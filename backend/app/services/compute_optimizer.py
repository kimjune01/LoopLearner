"""
Compute Optimization Service
Prevents excessive LLM spend through intelligent convergence and caching
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from core.models import PromptLab, SystemPrompt, UserFeedback

logger = logging.getLogger(__name__)


class ComputeOptimizer:
    """Service for optimizing compute spend on LLM operations"""
    
    # Progressive thresholds match convergence detector
    CONVERGENCE_STAGES = {
        'exploration': {
            'min_iterations': 2,
            'min_feedback': 5,
            'performance_threshold': 0.10,  # 10% improvement required
            'confidence_required': 0.6
        },
        'refinement': {
            'min_iterations': 5,
            'min_feedback': 20,
            'performance_threshold': 0.05,  # 5% improvement required
            'confidence_required': 0.75
        },
        'optimization': {
            'min_iterations': 10,
            'min_feedback': 50,
            'performance_threshold': 0.02,  # 2% improvement required
            'confidence_required': 0.85
        },
        'diminishing_returns': {
            'min_iterations': 15,
            'min_feedback': 100,
            'performance_threshold': 0.01,  # 1% improvement required
            'confidence_required': 0.95
        }
    }
    
    # Cost controls (sensible defaults)
    MAX_ITERATIONS_PER_PROMPT_LAB = 20  # Hard stop to prevent runaway costs
    MAX_DAILY_ITERATIONS_PER_USER = 100  # Rate limiting per user
    CACHE_DURATION_SECONDS = 3600  # 1 hour cache for expensive operations
    
    # Cost estimates (adjust based on your LLM provider)
    COST_PER_OPTIMIZATION = 0.15  # ~$0.15 per optimization iteration
    COST_PER_EVALUATION = 0.05   # ~$0.05 per evaluation run
    
    def __init__(self):
        self.logger = logger
    
    def should_continue_optimization(self, prompt_lab: PromptLab) -> Dict[str, Any]:
        """Determine if optimization should continue based on ROI"""
        try:
            # Check hard limits first
            if prompt_lab.optimization_iterations >= self.MAX_ITERATIONS_PER_PROMPT_LAB:
                return {
                    'continue': False,
                    'reason': 'max_iterations_reached',
                    'recommendation': 'Prompt lab has reached maximum optimization limit',
                    'compute_saved': True
                }
            
            # Determine current stage
            stage = self._determine_optimization_stage(prompt_lab)
            thresholds = self.CONVERGENCE_STAGES[stage]
            
            # Check if we meet minimum requirements for current stage
            if prompt_lab.optimization_iterations < thresholds['min_iterations']:
                return {
                    'continue': True,
                    'reason': 'insufficient_iterations',
                    'stage': stage,
                    'iterations_needed': thresholds['min_iterations'] - prompt_lab.optimization_iterations
                }
            
            # Calculate ROI metrics
            roi_metrics = self._calculate_optimization_roi(prompt_lab)
            
            # Progressive convergence based on stage
            improvement_rate = roi_metrics['recent_improvement_rate']
            if improvement_rate < thresholds['performance_threshold']:
                return {
                    'continue': False,
                    'reason': 'low_roi',
                    'stage': stage,
                    'improvement_rate': improvement_rate,
                    'threshold': thresholds['performance_threshold'],
                    'recommendation': f'Improvement rate ({improvement_rate:.1%}) below threshold for {stage} stage',
                    'compute_saved': True
                }
            
            # Check confidence vs compute cost
            compute_cost_ratio = self._estimate_compute_cost_ratio(prompt_lab)
            if compute_cost_ratio > 2.0:  # Costs outweigh benefits
                return {
                    'continue': False,
                    'reason': 'high_compute_cost',
                    'cost_ratio': compute_cost_ratio,
                    'recommendation': 'Compute costs exceed expected benefits',
                    'compute_saved': True
                }
            
            return {
                'continue': True,
                'reason': 'optimization_beneficial',
                'stage': stage,
                'improvement_rate': improvement_rate,
                'cost_ratio': compute_cost_ratio
            }
            
        except Exception as e:
            self.logger.error(f"Error in optimization decision: {str(e)}")
            # Fail safe - don't spend compute on errors
            return {
                'continue': False,
                'reason': 'error',
                'error': str(e),
                'compute_saved': True
            }
    
    def get_cached_optimization_result(self, prompt_lab: PromptLab, prompt_hash: str) -> Optional[Dict]:
        """Check if we already have optimization results for similar prompts"""
        cache_key = f"opt_result_{prompt_lab.id}_{prompt_hash}"
        return cache.get(cache_key)
    
    def cache_optimization_result(self, prompt_lab: PromptLab, prompt_hash: str, result: Dict):
        """Cache optimization results to avoid recomputation"""
        cache_key = f"opt_result_{prompt_lab.id}_{prompt_hash}"
        cache.set(cache_key, result, self.CACHE_DURATION_SECONDS)
    
    def estimate_optimization_cost(self, prompt_lab: PromptLab) -> Dict[str, float]:
        """Estimate compute costs for next optimization iteration"""
        try:
            # Base costs (example values - adjust based on your LLM pricing)
            BASE_OPTIMIZATION_COST = 0.10  # $0.10 per optimization run
            BASE_EVALUATION_COST = 0.05    # $0.05 per evaluation
            
            # Scale costs based on complexity
            complexity_multiplier = self._calculate_complexity_multiplier(prompt_lab)
            
            # Estimate tokens based on prompt length
            active_prompt = prompt_lab.prompts.filter(is_active=True).first()
            if active_prompt:
                prompt_tokens = len(active_prompt.content.split()) * 1.5  # Rough estimate
                token_cost = (prompt_tokens / 1000) * 0.002  # Example pricing
            else:
                token_cost = 0.02  # Default
            
            optimization_cost = BASE_OPTIMIZATION_COST * complexity_multiplier + token_cost
            evaluation_cost = BASE_EVALUATION_COST * prompt_lab.emails.count() * 0.1  # Sample evaluation
            
            total_cost = optimization_cost + evaluation_cost
            
            return {
                'optimization_cost': round(optimization_cost, 3),
                'evaluation_cost': round(evaluation_cost, 3),
                'total_cost': round(total_cost, 3),
                'complexity_multiplier': complexity_multiplier,
                'estimated_tokens': int(prompt_tokens) if active_prompt else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error estimating costs: {str(e)}")
            return {
                'optimization_cost': 0.15,  # Conservative estimate
                'evaluation_cost': 0.10,
                'total_cost': 0.25,
                'error': str(e)
            }
    
    def get_compute_budget_status(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Check compute budget and usage"""
        try:
            # Daily budget tracking
            today = timezone.now().date()
            cache_key = f"compute_usage_{user_id}_{today}" if user_id else f"compute_usage_global_{today}"
            
            current_usage = cache.get(cache_key, 0)
            daily_limit = self.MAX_DAILY_ITERATIONS_PER_USER
            
            return {
                'daily_iterations_used': current_usage,
                'daily_iterations_limit': daily_limit,
                'budget_remaining': daily_limit - current_usage,
                'percentage_used': (current_usage / daily_limit * 100) if daily_limit > 0 else 0,
                'reset_time': (timezone.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            }
            
        except Exception as e:
            self.logger.error(f"Error checking budget: {str(e)}")
            return {
                'error': str(e),
                'budget_remaining': 0  # Fail safe
            }
    
    def increment_usage_counter(self, user_id: Optional[str] = None):
        """Increment compute usage counter"""
        today = timezone.now().date()
        cache_key = f"compute_usage_{user_id}_{today}" if user_id else f"compute_usage_global_{today}"
        
        try:
            cache.incr(cache_key)
        except ValueError:
            # Key doesn't exist, initialize it
            cache.set(cache_key, 1, 86400)  # 24 hour expiration
    
    def _determine_optimization_stage(self, prompt_lab: PromptLab) -> str:
        """Determine which optimization stage the prompt lab is in"""
        iterations = prompt_lab.optimization_iterations
        feedback_count = prompt_lab.total_feedback_collected
        
        if iterations >= 15 or feedback_count >= 100:
            return 'diminishing_returns'
        elif iterations >= 10 or feedback_count >= 50:
            return 'optimization'
        elif iterations >= 5 or feedback_count >= 20:
            return 'refinement'
        else:
            return 'exploration'
    
    def _calculate_optimization_roi(self, prompt_lab: PromptLab) -> Dict[str, float]:
        """Calculate return on investment metrics"""
        try:
            # Get recent performance history
            recent_prompts = SystemPrompt.objects.filter(
                session=session,
                performance_score__isnull=False
            ).order_by('-version')[:5]
            
            if recent_prompts.count() < 2:
                return {'recent_improvement_rate': 1.0}  # Assume high ROI early
            
            scores = [p.performance_score for p in recent_prompts]
            
            # Calculate improvement rate
            if len(scores) >= 2:
                recent_improvement = scores[0] - scores[1]  # Latest - previous
                improvement_rate = recent_improvement / scores[1] if scores[1] > 0 else 0
            else:
                improvement_rate = 0
            
            # Calculate trend
            if len(scores) >= 3:
                recent_trend = (scores[0] + scores[1]) / 2 - (scores[2] + scores[3] if len(scores) > 3 else scores[2]) / 2
            else:
                recent_trend = improvement_rate
            
            return {
                'recent_improvement_rate': improvement_rate,
                'improvement_trend': recent_trend,
                'latest_score': scores[0] if scores else 0,
                'average_score': sum(scores) / len(scores) if scores else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating ROI: {str(e)}")
            return {'recent_improvement_rate': 0}
    
    def _estimate_compute_cost_ratio(self, prompt_lab: PromptLab) -> float:
        """Estimate ratio of compute cost to expected benefit"""
        try:
            # Get ROI metrics
            roi = self._calculate_optimization_roi(prompt_lab)
            improvement_rate = roi['recent_improvement_rate']
            
            # Estimate cost of next iteration
            cost_estimate = self.estimate_optimization_cost(prompt_lab)
            iteration_cost = cost_estimate['total_cost']
            
            # Estimate value of improvement (example: $1 per 1% improvement)
            improvement_value = improvement_rate * 100 * 1.0
            
            # Calculate ratio (higher = worse)
            if improvement_value > 0:
                ratio = iteration_cost / improvement_value
            else:
                ratio = float('inf')  # No improvement = infinite cost ratio
            
            return min(ratio, 10.0)  # Cap at 10 for practical purposes
            
        except Exception as e:
            self.logger.error(f"Error calculating cost ratio: {str(e)}")
            return 5.0  # Conservative estimate
    
    def _calculate_complexity_multiplier(self, prompt_lab: PromptLab) -> float:
        """Calculate complexity multiplier based on session characteristics"""
        try:
            multiplier = 1.0
            
            # More emails = more complex evaluation
            email_count = prompt_lab.emails.count()
            if email_count > 50:
                multiplier *= 1.5
            elif email_count > 20:
                multiplier *= 1.2
            
            # Longer prompts = more tokens
            active_prompt = prompt_lab.prompts.filter(is_active=True).first()
            if active_prompt and len(active_prompt.content) > 1000:
                multiplier *= 1.3
            
            # More preferences = more complex optimization
            preference_count = prompt_lab.preferences.filter(is_active=True).count()
            if preference_count > 10:
                multiplier *= 1.2
            
            return round(multiplier, 2)
            
        except Exception as e:
            self.logger.error(f"Error calculating complexity: {str(e)}")
            return 1.5  # Conservative estimate