"""
Optimization Orchestrator for automated prompt improvement cycles
Triggers optimization based on batches of feedback rather than individual instances
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from django.utils import timezone
from asgiref.sync import sync_to_async

from core.models import SystemPrompt, UserFeedback, Email, Draft
from .prompt_rewriter import PromptRewriter, RewriteContext, RewriteCandidate
from .evaluation_engine import EvaluationEngine
from .reward_aggregator import RewardFunctionAggregator
from .unified_llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


@dataclass
class OptimizationTrigger:
    """Configuration for when to trigger optimization"""
    min_feedback_count: int = 10  # Minimum feedback instances to trigger
    min_negative_feedback_ratio: float = 0.3  # Trigger if 30%+ feedback is negative
    feedback_window_hours: int = 24  # Look at feedback from last N hours
    min_time_since_last_optimization_hours: int = 6  # Prevent too frequent optimizations
    max_optimization_frequency_per_day: int = 4  # Maximum optimizations per day


@dataclass
class OptimizationResult:
    """Result of an optimization cycle"""
    trigger_reason: str
    baseline_prompt: SystemPrompt
    candidate_prompts: List[RewriteCandidate]
    best_candidate: Optional[RewriteCandidate]
    evaluation_results: Dict[str, Any]
    deployed: bool
    improvement_percentage: float
    feedback_batch_size: int
    optimization_time: datetime


class OptimizationOrchestrator:
    """Orchestrates automated prompt optimization based on feedback batches"""
    
    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        prompt_rewriter: PromptRewriter,
        evaluation_engine: EvaluationEngine,
        trigger_config: OptimizationTrigger = None
    ):
        self.llm_provider = llm_provider
        self.prompt_rewriter = prompt_rewriter
        self.evaluation_engine = evaluation_engine
        self.trigger_config = trigger_config or OptimizationTrigger()
        self._optimization_lock = asyncio.Lock()
        self._last_optimization_time: Optional[datetime] = None
        self._optimization_count_today = 0
        self._last_count_reset_date = timezone.now().date()
    
    async def check_and_trigger_optimization(self) -> Optional[OptimizationResult]:
        """Check if optimization should be triggered and execute if conditions are met"""
        
        async with self._optimization_lock:
            # Reset daily count if needed
            self._reset_daily_count_if_needed()
            
            # Check if we've hit daily limit
            if self._optimization_count_today >= self.trigger_config.max_optimization_frequency_per_day:
                logger.info(f"Daily optimization limit reached ({self._optimization_count_today})")
                return None
            
            # Check minimum time since last optimization
            if not self._can_optimize_based_on_time():
                logger.info("Too soon since last optimization")
                return None
            
            # Analyze recent feedback to determine if optimization is needed
            trigger_analysis = await self._analyze_feedback_for_triggers()
            
            if not trigger_analysis['should_trigger']:
                logger.info(f"Optimization not triggered: {trigger_analysis['reason']}")
                return None
            
            logger.info(f"Triggering optimization: {trigger_analysis['reason']}")
            
            # Execute optimization cycle
            result = await self._execute_optimization_cycle(trigger_analysis)
            
            # Update tracking variables
            self._last_optimization_time = timezone.now()
            self._optimization_count_today += 1
            
            return result
    
    async def _analyze_feedback_for_triggers(self) -> Dict[str, Any]:
        """Analyze recent feedback to determine if optimization should be triggered"""
        
        # Get feedback from the configured time window
        cutoff_time = timezone.now() - timedelta(hours=self.trigger_config.feedback_window_hours)
        
        recent_feedback = [
            feedback async for feedback in UserFeedback.objects.filter(
                created_at__gte=cutoff_time
            ).select_related('draft__prompt')
        ]
        
        if len(recent_feedback) < self.trigger_config.min_feedback_count:
            return {
                'should_trigger': False,
                'reason': f'Insufficient feedback count: {len(recent_feedback)} < {self.trigger_config.min_feedback_count}',
                'feedback_count': len(recent_feedback),
                'feedback_batch': recent_feedback
            }
        
        # Analyze feedback sentiment and quality
        negative_feedback_count = 0
        total_rating_sum = 0
        rating_count = 0
        
        for feedback in recent_feedback:
            # Count negative actions
            if feedback.action in ['reject', 'edit']:
                negative_feedback_count += 1
            
            # Aggregate rating factors
            if hasattr(feedback, 'reasoning_factors') and feedback.reasoning_factors:
                factors = feedback.reasoning_factors
                if isinstance(factors, dict):
                    ratings = [v for v in factors.values() if isinstance(v, (int, float))]
                    if ratings:
                        total_rating_sum += sum(ratings) / len(ratings)
                        rating_count += 1
        
        negative_feedback_ratio = negative_feedback_count / len(recent_feedback)
        average_rating = total_rating_sum / rating_count if rating_count > 0 else 3.0  # Default neutral
        
        # Determine if we should trigger optimization
        should_trigger = False
        trigger_reason = ""
        
        if negative_feedback_ratio >= self.trigger_config.min_negative_feedback_ratio:
            should_trigger = True
            trigger_reason = f"High negative feedback ratio: {negative_feedback_ratio:.1%}"
        elif average_rating < 2.5:  # Below neutral on 1-5 scale
            should_trigger = True
            trigger_reason = f"Low average rating: {average_rating:.2f}"
        elif self._has_consistent_issues(recent_feedback):
            should_trigger = True
            trigger_reason = "Consistent quality issues detected"
        
        return {
            'should_trigger': should_trigger,
            'reason': trigger_reason,
            'feedback_count': len(recent_feedback),
            'negative_feedback_ratio': negative_feedback_ratio,
            'average_rating': average_rating,
            'feedback_batch': recent_feedback
        }
    
    def _has_consistent_issues(self, feedback_batch: List[UserFeedback]) -> bool:
        """Detect consistent issues across the feedback batch"""
        
        issue_counts = {}
        
        for feedback in feedback_batch:
            if hasattr(feedback, 'reasoning_factors') and feedback.reasoning_factors:
                factors = feedback.reasoning_factors
                if isinstance(factors, dict):
                    # Count low ratings for specific factors
                    for factor, rating in factors.items():
                        if isinstance(rating, (int, float)) and rating < 3:  # Below neutral
                            issue_counts[factor] = issue_counts.get(factor, 0) + 1
        
        # Check if any factor has issues in >40% of feedback
        threshold = len(feedback_batch) * 0.4
        return any(count >= threshold for count in issue_counts.values())
    
    def _can_optimize_based_on_time(self) -> bool:
        """Check if enough time has passed since last optimization"""
        if self._last_optimization_time is None:
            return True
        
        time_since_last = timezone.now() - self._last_optimization_time
        min_interval = timedelta(hours=self.trigger_config.min_time_since_last_optimization_hours)
        
        return time_since_last >= min_interval
    
    def _reset_daily_count_if_needed(self):
        """Reset daily optimization count if it's a new day"""
        today = timezone.now().date()
        if today != self._last_count_reset_date:
            self._optimization_count_today = 0
            self._last_count_reset_date = today
    
    async def _execute_optimization_cycle(self, trigger_analysis: Dict[str, Any]) -> OptimizationResult:
        """Execute a complete optimization cycle"""
        
        start_time = timezone.now()
        feedback_batch = trigger_analysis['feedback_batch']
        
        logger.info(f"Starting optimization cycle with {len(feedback_batch)} feedback instances")
        
        # Get current active prompt
        current_prompt = await sync_to_async(
            SystemPrompt.objects.filter(is_active=True).first
        )()
        
        if not current_prompt:
            raise ValueError("No active system prompt found")
        
        # Build rewrite context from feedback batch
        rewrite_context = await self._build_rewrite_context(current_prompt, feedback_batch)
        
        # Generate candidate prompts
        candidates = await self.prompt_rewriter.rewrite_prompt(
            rewrite_context, 
            mode="aggressive"  # Use aggressive mode for batch-triggered optimization
        )
        
        logger.info(f"Generated {len(candidates)} candidate prompts")
        
        # Evaluate candidates against current prompt
        evaluation_results = await self.evaluation_engine.compare_prompt_candidates(
            current_prompt,
            [SystemPrompt(content=c.content, version=current_prompt.version + 1) for c in candidates],
            test_case_count=15  # Use more test cases for batch optimization
        )
        
        # Find best candidate
        best_candidate = None
        best_improvement = 0.0
        best_comparison = None
        
        for i, comparison in enumerate(evaluation_results):
            if comparison.winner == "candidate" and comparison.improvement > best_improvement:
                best_improvement = comparison.improvement
                best_candidate = candidates[i]
                best_comparison = comparison
        
        # Decide whether to deploy
        should_deploy = self._should_deploy_candidate(best_comparison)
        
        if should_deploy and best_candidate:
            await self._deploy_new_prompt(current_prompt, best_candidate, best_comparison)
            logger.info(f"Deployed new prompt with {best_improvement:.1f}% improvement")
        else:
            logger.info("No significant improvement found, keeping current prompt")
        
        return OptimizationResult(
            trigger_reason=trigger_analysis['reason'],
            baseline_prompt=current_prompt,
            candidate_prompts=candidates,
            best_candidate=best_candidate,
            evaluation_results={
                'comparisons': evaluation_results,
                'best_improvement': best_improvement
            },
            deployed=should_deploy,
            improvement_percentage=best_improvement,
            feedback_batch_size=len(feedback_batch),
            optimization_time=start_time
        )
    
    async def _build_rewrite_context(
        self, 
        current_prompt: SystemPrompt, 
        feedback_batch: List[UserFeedback]
    ) -> RewriteContext:
        """Build rewrite context from batch of feedback"""
        
        # Aggregate feedback insights
        recent_feedback = []
        performance_history = {}
        
        # Process feedback batch
        negative_actions = 0
        total_feedback = len(feedback_batch)
        factor_ratings = {}
        
        for feedback in feedback_batch:
            recent_feedback.append({
                'action': feedback.action,
                'reasoning': getattr(feedback, 'reasoning', ''),
                'factors': getattr(feedback, 'reasoning_factors', {})
            })
            
            if feedback.action in ['reject', 'edit']:
                negative_actions += 1
            
            # Aggregate factor ratings
            if hasattr(feedback, 'reasoning_factors') and feedback.reasoning_factors:
                factors = feedback.reasoning_factors
                if isinstance(factors, dict):
                    for factor, rating in factors.items():
                        if isinstance(rating, (int, float)):
                            if factor not in factor_ratings:
                                factor_ratings[factor] = []
                            factor_ratings[factor].append(rating)
        
        # Calculate aggregated performance metrics
        performance_history['overall_quality'] = 1.0 - (negative_actions / total_feedback)
        
        for factor, ratings in factor_ratings.items():
            performance_history[f'{factor}_avg'] = sum(ratings) / len(ratings)
        
        # Determine scenario based on feedback patterns
        scenario_counts = {}
        for feedback in feedback_batch:
            if hasattr(feedback, 'draft') and feedback.draft and hasattr(feedback.draft, 'email'):
                email = feedback.draft.email
                scenario = getattr(email, 'scenario_type', 'professional')
                scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
        
        primary_scenario = max(scenario_counts.items(), key=lambda x: x[1])[0] if scenario_counts else 'professional'
        
        # Build constraints based on feedback patterns
        constraints = {
            'max_length': 300,  # Reasonable default
            'tone': primary_scenario,
            'focus_areas': [factor for factor, ratings in factor_ratings.items() 
                          if sum(ratings) / len(ratings) < 3.0]  # Areas needing improvement
        }
        
        return RewriteContext(
            email_scenario=primary_scenario,
            current_prompt=current_prompt,
            recent_feedback=recent_feedback[-5:],  # Last 5 for context
            performance_history=performance_history,
            constraints=constraints
        )
    
    def _should_deploy_candidate(self, comparison_result) -> bool:
        """Determine if a candidate should be deployed based on evaluation results"""
        
        if not comparison_result or comparison_result.winner != "candidate":
            return False
        
        # Require significant improvement and statistical confidence
        min_improvement = 5.0  # At least 5% improvement
        min_confidence = 0.8   # At least 80% confidence
        
        return (
            comparison_result.improvement >= min_improvement and
            comparison_result.confidence_level >= min_confidence
        )
    
    async def _deploy_new_prompt(
        self, 
        current_prompt: SystemPrompt, 
        new_candidate: RewriteCandidate,
        comparison_result
    ):
        """Deploy a new prompt and archive the current one"""
        
        # Create new prompt version
        new_prompt = SystemPrompt(
            content=new_candidate.content,
            version=current_prompt.version + 1,
            performance_score=comparison_result.candidate.performance_score,
            is_active=True
        )
        
        # Save new prompt and deactivate old one
        await sync_to_async(new_prompt.save)()
        
        current_prompt.is_active = False
        await sync_to_async(current_prompt.save)()
        
        logger.info(f"Deployed prompt v{new_prompt.version} replacing v{current_prompt.version}")
    
    async def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status and metrics"""
        
        return {
            'last_optimization_time': self._last_optimization_time,
            'optimizations_today': self._optimization_count_today,
            'daily_limit': self.trigger_config.max_optimization_frequency_per_day,
            'can_optimize_now': self._can_optimize_based_on_time(),
            'next_eligible_time': (
                self._last_optimization_time + 
                timedelta(hours=self.trigger_config.min_time_since_last_optimization_hours)
            ) if self._last_optimization_time else None,
            'trigger_config': {
                'min_feedback_count': self.trigger_config.min_feedback_count,
                'min_negative_feedback_ratio': self.trigger_config.min_negative_feedback_ratio,
                'feedback_window_hours': self.trigger_config.feedback_window_hours
            }
        }
    
    async def force_optimization(self, reason: str = "Manual trigger") -> OptimizationResult:
        """Force an optimization cycle regardless of normal triggers"""
        
        logger.info(f"Forcing optimization: {reason}")
        
        # Build fake trigger analysis for forced optimization
        trigger_analysis = {
            'should_trigger': True,
            'reason': reason,
            'feedback_count': 0,
            'feedback_batch': []
        }
        
        # If no recent feedback, use all feedback from last 7 days
        if not trigger_analysis['feedback_batch']:
            cutoff_time = timezone.now() - timedelta(days=7)
            recent_feedback = [
                feedback async for feedback in UserFeedback.objects.filter(
                    created_at__gte=cutoff_time
                ).select_related('draft__prompt')[:20]  # Limit to recent 20
            ]
            trigger_analysis['feedback_batch'] = recent_feedback
            trigger_analysis['feedback_count'] = len(recent_feedback)
        
        return await self._execute_optimization_cycle(trigger_analysis)