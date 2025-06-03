"""
Convergence Detector Service
Detects when optimization loops have converged and should stop learning
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Q
from core.models import PromptLab, SystemPrompt, UserFeedback

logger = logging.getLogger(__name__)


class ConvergenceDetector:
    """Service for detecting when optimization has converged"""
    
    # Convergence detection thresholds
    PERFORMANCE_PLATEAU_THRESHOLD = 0.02  # 2% improvement threshold
    PERFORMANCE_WINDOW_SIZE = 5  # Look at last 5 prompts
    MINIMUM_ITERATIONS = 3  # Minimum optimization iterations before convergence
    MINIMUM_FEEDBACK_COUNT = 10  # Minimum feedback before convergence
    FEEDBACK_STABILITY_WINDOW = 15  # Look at last 15 feedback items
    FEEDBACK_STABILITY_THRESHOLD = 0.8  # 80% consistency required
    
    # Compute optimization limits (sensible defaults)
    MAX_ITERATIONS_HARD_LIMIT = 20  # Absolute maximum to prevent runaway
    MAX_ITERATIONS_SOFT_LIMIT = 15  # Soft limit where we get more strict
    COST_BENEFIT_RATIO_LIMIT = 2.0  # Stop if costs > 2x benefits
    
    def __init__(self):
        self.logger = logger
    
    def assess_convergence(self, prompt_lab: PromptLab) -> Dict[str, Any]:
        """Comprehensive convergence assessment combining all factors"""
        try:
            # Import compute optimizer for cost-aware decisions
            from app.services.compute_optimizer import ComputeOptimizer
            compute_optimizer = ComputeOptimizer()
            
            # Check hard iteration limit first (failsafe)
            if prompt_lab.optimization_iterations >= self.MAX_ITERATIONS_HARD_LIMIT:
                return {
                    'converged': True,
                    'confidence_score': 1.0,
                    'factors': {
                        'hard_limit_reached': True,
                        'iterations': prompt_lab.optimization_iterations,
                        'limit': self.MAX_ITERATIONS_HARD_LIMIT
                    },
                    'recommendations': [{
                        'action': 'stop_optimization',
                        'reason': f'Maximum iteration limit ({self.MAX_ITERATIONS_HARD_LIMIT}) reached',
                        'priority': 'critical'
                    }],
                    'compute_saved': True,
                    'assessment_timestamp': timezone.now().isoformat()
                }
            
            # Check if we should even run convergence check (save compute)
            optimization_decision = compute_optimizer.should_continue_optimization(prompt_lab)
            if not optimization_decision.get('continue', True):
                # Force convergence if compute costs too high
                return {
                    'converged': True,
                    'confidence_score': 0.95,
                    'factors': {
                        'compute_limit_reached': True,
                        'reason': optimization_decision.get('reason', 'compute_optimization')
                    },
                    'recommendations': [{
                        'action': 'stop_optimization',
                        'reason': optimization_decision.get('recommendation', 'Compute limits reached'),
                        'priority': 'high'
                    }],
                    'compute_saved': True,
                    'assessment_timestamp': timezone.now().isoformat()
                }
            
            # Check all convergence factors
            performance_plateau = self.detect_performance_plateau(prompt_lab)
            confidence_convergence = self.check_confidence_convergence(prompt_lab)
            feedback_stability = self.detect_feedback_stability(prompt_lab)
            minimum_iterations = self._check_minimum_iterations(prompt_lab)
            minimum_feedback = self._check_minimum_feedback(prompt_lab)
            
            # Check for negative trends (early exit if performance declining)
            negative_trend = self._check_negative_performance_trend(prompt_lab)
            if negative_trend:
                return {
                    'converged': True,
                    'confidence_score': 0.9,
                    'factors': {
                        'negative_trend_detected': True,
                        'reason': 'Performance declining for multiple iterations'
                    },
                    'recommendations': [{
                        'action': 'stop_optimization',
                        'reason': 'Performance is declining - optimization may be harmful',
                        'priority': 'critical'
                    }, {
                        'action': 'review_feedback',
                        'reason': 'Check recent feedback to understand performance decline',
                        'priority': 'high'
                    }],
                    'compute_saved': True,
                    'assessment_timestamp': timezone.now().isoformat()
                }
            
            # Calculate overall convergence score
            factors = {
                'performance_plateau': performance_plateau,
                'confidence_convergence': confidence_convergence,
                'feedback_stability': feedback_stability,
                'minimum_iterations_reached': minimum_iterations,
                'minimum_feedback_reached': minimum_feedback
            }
            
            # Convergence requires all key factors to be met
            key_factors_met = performance_plateau and confidence_convergence and feedback_stability
            prerequisites_met = minimum_iterations and minimum_feedback
            
            converged = key_factors_met and prerequisites_met
            confidence_score = self.calculate_convergence_confidence(prompt_lab)
            
            # Generate recommendations based on current state
            recommendations = self.generate_recommendations(prompt_lab, factors, converged)
            
            return {
                'converged': converged,
                'confidence_score': confidence_score,
                'factors': factors,
                'recommendations': recommendations,
                'assessment_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing convergence for prompt lab {prompt_lab.id}: {str(e)}")
            return {
                'converged': False,
                'confidence_score': 0.0,
                'factors': {},
                'recommendations': [],
                'error': str(e)
            }
    
    def detect_performance_plateau(self, prompt_lab: PromptLab) -> bool:
        """Detect if performance has plateaued (no significant improvement)"""
        try:
            # Get recent prompt performance scores
            recent_prompts = SystemPrompt.objects.filter(
                prompt_lab=prompt_lab,
                performance_score__isnull=False
            ).order_by('-version')[:self.PERFORMANCE_WINDOW_SIZE]
            
            if recent_prompts.count() < self.PERFORMANCE_WINDOW_SIZE:
                return False  # Not enough data to detect plateau
            
            scores = [prompt.performance_score for prompt in recent_prompts]
            
            if not scores:
                return False
            
            # Use progressive thresholds based on iteration count
            threshold = self._get_progressive_threshold(prompt_lab)
            
            # Check if performance improvement is minimal
            max_score = max(scores)
            min_score = min(scores)
            performance_range = max_score - min_score
            
            # Also check trend: is the latest score significantly better than earlier ones?
            latest_score = scores[0]  # Most recent (first in reverse order)
            earliest_score = scores[-1]  # Oldest in this window
            improvement = latest_score - earliest_score
            
            # Plateau detected if both range and improvement are below threshold
            plateau_detected = (
                performance_range < threshold and
                improvement < threshold
            )
            
            self.logger.info(f"Performance plateau check for prompt lab {prompt_lab.id}: "
                           f"range={performance_range:.3f}, improvement={improvement:.3f}, "
                           f"threshold={threshold:.3f}, plateau={plateau_detected}")
            
            return plateau_detected
            
        except Exception as e:
            self.logger.error(f"Error detecting performance plateau: {str(e)}")
            return False
    
    def _get_progressive_threshold(self, prompt_lab: PromptLab) -> float:
        """Get performance threshold based on optimization stage"""
        iterations = prompt_lab.optimization_iterations
        
        if iterations < 5:
            # Early stage: allow 10% improvement
            return 0.10
        elif iterations < 10:
            # Refinement: require 5% improvement
            return 0.05
        elif iterations < self.MAX_ITERATIONS_SOFT_LIMIT:
            # Optimization: require 2% improvement
            return 0.02
        else:
            # Diminishing returns: require only 1% improvement
            return 0.01
    
    def check_confidence_convergence(self, prompt_lab: PromptLab) -> bool:
        """Check if confidence metrics indicate convergence"""
        try:
            # For now, return False since PromptLabConfidence model doesn't exist yet
            # This can be implemented later when confidence tracking is added
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking confidence convergence: {str(e)}")
            return False
    
    def detect_feedback_stability(self, prompt_lab: PromptLab) -> bool:
        """Detect if user feedback patterns have stabilized"""
        try:
            # Get recent feedback
            recent_feedback = UserFeedback.objects.filter(
                draft__email__prompt_lab=prompt_lab
            ).order_by('-created_at')[:self.FEEDBACK_STABILITY_WINDOW]
            
            if recent_feedback.count() < self.FEEDBACK_STABILITY_WINDOW:
                return False  # Not enough feedback to assess stability
            
            # Analyze action patterns
            actions = [f.action for f in recent_feedback]
            
            # Calculate consistency: most common action should dominate
            from collections import Counter
            action_counts = Counter(actions)
            most_common_action, most_common_count = action_counts.most_common(1)[0]
            
            consistency_ratio = most_common_count / len(actions)
            
            # Check for acceptance pattern specifically (indicates satisfaction)
            accept_ratio = action_counts.get('accept', 0) / len(actions)
            
            # Stability detected if either:
            # 1. High consistency in any action, OR
            # 2. High acceptance rate (user is satisfied)
            stability_detected = (
                consistency_ratio >= self.FEEDBACK_STABILITY_THRESHOLD or
                accept_ratio >= 0.7  # 70% acceptance rate
            )
            
            self.logger.info(f"Feedback stability check for prompt lab {prompt_lab.id}: "
                           f"consistency={consistency_ratio:.3f}, acceptance={accept_ratio:.3f}, "
                           f"stable={stability_detected}")
            
            return stability_detected
            
        except Exception as e:
            self.logger.error(f"Error detecting feedback stability: {str(e)}")
            return False
    
    def check_early_stopping_criteria(self, prompt_lab: PromptLab) -> bool:
        """Check if early stopping conditions are met (shouldn't stop early)"""
        try:
            # Early stopping should NOT happen if:
            # 1. Not enough iterations
            # 2. Not enough feedback
            # 3. Recent negative trend
            
            insufficient_iterations = prompt_lab.optimization_iterations < self.MINIMUM_ITERATIONS
            insufficient_feedback = prompt_lab.total_feedback_collected < self.MINIMUM_FEEDBACK_COUNT
            
            # Check for recent negative performance trend
            recent_prompts = SystemPrompt.objects.filter(
                prompt_lab=prompt_lab,
                performance_score__isnull=False
            ).order_by('-version')[:3]
            
            negative_trend = False
            if recent_prompts.count() >= 3:
                scores = [p.performance_score for p in recent_prompts]
                # Check if performance is declining
                if scores[0] < scores[-1]:  # Latest < oldest
                    negative_trend = True
            
            # Should NOT stop early if any of these conditions are true
            should_not_stop = insufficient_iterations or insufficient_feedback or negative_trend
            
            return not should_not_stop  # Return True if early stopping is appropriate
            
        except Exception as e:
            self.logger.error(f"Error checking early stopping criteria: {str(e)}")
            return False
    
    def calculate_convergence_confidence(self, prompt_lab: PromptLab) -> float:
        """Calculate confidence score for convergence decision"""
        try:
            confidence_factors = []
            
            # Factor 1: Performance stability
            if self.detect_performance_plateau(prompt_lab):
                confidence_factors.append(0.3)  # 30% weight
            else:
                confidence_factors.append(0.0)
            
            # Factor 2: Confidence metrics
            if self.check_confidence_convergence(prompt_lab):
                confidence_factors.append(0.3)  # 30% weight
            else:
                confidence_factors.append(0.0)
            
            # Factor 3: Feedback stability
            if self.detect_feedback_stability(prompt_lab):
                confidence_factors.append(0.25)  # 25% weight
            else:
                confidence_factors.append(0.0)
            
            # Factor 4: Data sufficiency
            iterations_factor = min(1.0, prompt_lab.optimization_iterations / (self.MINIMUM_ITERATIONS * 2))
            feedback_factor = min(1.0, prompt_lab.total_feedback_collected / (self.MINIMUM_FEEDBACK_COUNT * 2))
            data_sufficiency = (iterations_factor + feedback_factor) / 2
            confidence_factors.append(data_sufficiency * 0.15)  # 15% weight
            
            # Sum all factors for total confidence
            total_confidence = sum(confidence_factors)
            
            return round(total_confidence, 3)
            
        except Exception as e:
            self.logger.error(f"Error calculating convergence confidence: {str(e)}")
            return 0.0
    
    def generate_recommendations(self, prompt_lab: PromptLab, factors: Dict[str, bool], converged: bool) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on convergence state"""
        try:
            recommendations = []
            
            # Add compute-aware recommendations
            iterations = prompt_lab.optimization_iterations
            
            if converged:
                recommendations.append({
                    'action': 'stop_optimization',
                    'reason': 'All convergence criteria met - optimization can be stopped',
                    'priority': 'high'
                })
                
                # Calculate estimated savings
                remaining_iterations = self.MAX_ITERATIONS_HARD_LIMIT - iterations
                estimated_savings = remaining_iterations * 0.15  # ~$0.15 per iteration
                
                if estimated_savings > 0:
                    recommendations.append({
                        'action': 'compute_savings',
                        'reason': f'Stopping now saves ~${estimated_savings:.2f} in compute costs',
                        'priority': 'high'
                    })
                
                recommendations.append({
                    'action': 'archive_prompt_lab',
                    'reason': 'Session has reached optimal performance, consider archiving',
                    'priority': 'medium'
                })
                
            else:
                # Check if approaching limits
                if iterations >= self.MAX_ITERATIONS_SOFT_LIMIT:
                    recommendations.append({
                        'action': 'consider_stopping',
                        'reason': f'Approaching iteration limit ({iterations}/{self.MAX_ITERATIONS_HARD_LIMIT})',
                        'priority': 'high'
                    })
                
                # Provide specific recommendations based on missing factors
                if not factors.get('minimum_iterations_reached', False):
                    recommendations.append({
                        'action': 'continue_optimization',
                        'reason': f'Need at least {self.MINIMUM_ITERATIONS} optimization iterations',
                        'priority': 'high'
                    })
                
                if not factors.get('minimum_feedback_reached', False):
                    recommendations.append({
                        'action': 'collect_more_feedback',
                        'reason': f'Need at least {self.MINIMUM_FEEDBACK_COUNT} feedback items',
                        'priority': 'high'
                    })
                
                if not factors.get('performance_plateau', False):
                    # Include current threshold in recommendation
                    threshold = self._get_progressive_threshold(prompt_lab)
                    recommendations.append({
                        'action': 'monitor_performance',
                        'reason': f'Performance still improving - continue optimization (current threshold: {threshold:.1%})',
                        'priority': 'medium'
                    })
                
                if not factors.get('confidence_convergence', False):
                    recommendations.append({
                        'action': 'build_confidence',
                        'reason': 'Confidence levels not yet sufficient for convergence',
                        'priority': 'medium'
                    })
                
                if not factors.get('feedback_stability', False):
                    recommendations.append({
                        'action': 'analyze_feedback_patterns',
                        'reason': 'User feedback patterns not yet stable',
                        'priority': 'low'
                    })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def should_check_convergence(self, prompt_lab: PromptLab) -> bool:
        """Determine if convergence should be checked now"""
        try:
            # Check convergence if:
            # 1. Minimum time has passed since last check
            # 2. Sufficient new feedback has been collected
            # 3. New optimization iteration has completed
            
            # For now, simple implementation: check every optimization iteration
            # In production, could add more sophisticated timing logic
            
            return prompt_lab.optimization_iterations >= self.MINIMUM_ITERATIONS
            
        except Exception as e:
            self.logger.error(f"Error determining convergence check timing: {str(e)}")
            return False
    
    def get_convergence_history(self, prompt_lab: PromptLab) -> List[Dict[str, Any]]:
        """Get historical convergence assessments for a prompt lab"""
        try:
            # For now, return current assessment as history
            # In production, could store historical assessments in database
            
            current_assessment = self.assess_convergence(prompt_lab)
            
            return [{
                'timestamp': current_assessment.get('assessment_timestamp'),
                'converged': current_assessment.get('converged', False),
                'confidence_score': current_assessment.get('confidence_score', 0.0),
                'factors': current_assessment.get('factors', {})
            }]
            
        except Exception as e:
            self.logger.error(f"Error getting convergence history: {str(e)}")
            return []
    
    def force_convergence(self, prompt_lab: PromptLab, reason: str, override_confidence: bool = False) -> Dict[str, Any]:
        """Manually force convergence for a prompt lab"""
        try:
            # Validate that forced convergence is appropriate
            if not override_confidence:
                current_assessment = self.assess_convergence(prompt_lab)
                if current_assessment.get('confidence_score', 0) < 0.5:
                    return {
                        'success': False,
                        'error': 'Convergence confidence too low for manual override without force flag'
                    }
            
            # Mark prompt lab as manually converged
            # This could update a prompt lab field or create a convergence record
            
            return {
                'success': True,
                'convergence_forced': True,
                'reason': reason,
                'timestamp': timezone.now().isoformat(),
                'prompt_lab_id': str(prompt_lab.id)
            }
            
        except Exception as e:
            self.logger.error(f"Error forcing convergence: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _check_minimum_iterations(self, prompt_lab: PromptLab) -> bool:
        """Check if minimum optimization iterations have been reached"""
        return prompt_lab.optimization_iterations >= self.MINIMUM_ITERATIONS
    
    def _check_minimum_feedback(self, prompt_lab: PromptLab) -> bool:
        """Check if minimum feedback count has been reached"""
        return prompt_lab.total_feedback_collected >= self.MINIMUM_FEEDBACK_COUNT
    
    def _check_negative_performance_trend(self, prompt_lab: PromptLab) -> bool:
        """Check if performance is declining (early exit condition)"""
        try:
            # Need at least 3 data points to detect trend
            recent_prompts = SystemPrompt.objects.filter(
                prompt_lab=prompt_lab,
                performance_score__isnull=False
            ).order_by('-version')[:3]
            
            if recent_prompts.count() < 3:
                return False
            
            scores = [p.performance_score for p in recent_prompts]
            
            # Check if performance is consistently declining
            # scores[0] is most recent, scores[2] is oldest
            declining = scores[0] < scores[1] < scores[2]
            
            # Also check if recent drop is significant (>5%)
            if len(scores) >= 2:
                # scores[0] is most recent, scores[1] is previous
                # If recent is lower than previous, it's a drop
                if scores[0] < scores[1]:
                    drop_percentage = (scores[1] - scores[0]) / scores[1] if scores[1] > 0 else 0
                    significant_drop = drop_percentage > 0.05
                else:
                    significant_drop = False
                
                return declining or significant_drop
            
            return declining
            
        except Exception as e:
            self.logger.error(f"Error checking negative trend: {str(e)}")
            return False