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
from .optimization_progress import OptimizationProgressReporter
from .metrics_collector import MetricsCollector

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
    """Modern orchestrator with fast optimization modes and adaptive strategies"""
    
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
        
        # Modern optimization configuration
        self.optimization_strategies = {
            'emergency': {'mode': 'fast', 'timeout': 5, 'min_improvement': 3.0},
            'continuous': {'mode': 'single_shot', 'timeout': 10, 'min_improvement': 5.0},
            'batch': {'mode': 'mini_opro', 'timeout': 30, 'min_improvement': 8.0},
            'thorough': {'mode': 'legacy', 'timeout': 120, 'min_improvement': 10.0}
        }
    
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
            
            # Check convergence before proceeding with optimization
            convergence_blocked = await self._check_convergence_status(trigger_analysis.get('feedback_batch', []))
            if convergence_blocked:
                logger.info("Optimization blocked due to convergence detection")
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
            ).select_related('draft__system_prompt')
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
        
        # Get current active prompt for the session
        session = None
        if feedback_batch:
            # Extract session from feedback
            first_feedback = feedback_batch[0]
            if hasattr(first_feedback, 'draft') and hasattr(first_feedback.draft, 'email'):
                session = first_feedback.draft.email.session
        
        # Check cold start status if we have a session
        if session and not self._check_cold_start_status(session):
            logger.warning(f"Optimization blocked for session {session.id}: Cold start not complete")
            return OptimizationResult(
                trigger_reason="Cold start not complete",
                baseline_prompt=None,
                candidate_prompts=[],
                best_candidate=None,
                evaluation_results={},
                deployed=False,
                improvement_percentage=0.0,
                feedback_batch_size=len(feedback_batch),
                optimization_time=start_time
            )
        
        if session:
            current_prompt = await sync_to_async(
                SystemPrompt.objects.filter(session=session, is_active=True).first
            )()
        else:
            current_prompt = await sync_to_async(
                SystemPrompt.objects.filter(is_active=True).first
            )()
        
        if not current_prompt:
            raise ValueError("No active system prompt found")
        
        # Build rewrite context from feedback batch
        rewrite_context = await self._build_rewrite_context(current_prompt, feedback_batch)
        
        # Select optimization strategy based on context
        optimization_strategy = self._select_optimization_strategy(trigger_analysis, len(feedback_batch))
        
        logger.info(f"Using optimization strategy: {optimization_strategy['name']}")
        
        # Generate candidate prompts with timeout
        try:
            candidates = await asyncio.wait_for(
                self.prompt_rewriter.rewrite_prompt(
                    rewrite_context,
                    mode=optimization_strategy['mode']
                ),
                timeout=optimization_strategy['timeout']
            )
        except asyncio.TimeoutError:
            logger.warning(f"Optimization timed out after {optimization_strategy['timeout']}s, falling back to fast mode")
            candidates = await self.prompt_rewriter.rewrite_prompt(
                rewrite_context,
                mode="fast"
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
        
        # Decide whether to deploy using strategy-specific criteria
        should_deploy = self._should_deploy_candidate(best_comparison, optimization_strategy)
        
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
    
    def _should_deploy_candidate(self, comparison_result, optimization_strategy: Dict[str, Any] = None) -> bool:
        """Determine if a candidate should be deployed based on evaluation results and strategy"""
        
        if not comparison_result or comparison_result.winner != "candidate":
            return False
        
        # Default strategy for backward compatibility
        if optimization_strategy is None:
            optimization_strategy = {'min_improvement': 5.0, 'mode': 'continuous'}
        
        # Use strategy-specific improvement thresholds
        min_improvement = optimization_strategy.get('min_improvement', 5.0)
        min_confidence = 0.8   # Keep confidence requirement consistent
        
        # For fast strategies, be more lenient with confidence requirements
        if optimization_strategy.get('mode') in ['fast', 'single_shot']:
            min_confidence = 0.6
        
        has_sufficient_improvement = comparison_result.improvement >= min_improvement
        has_sufficient_confidence = getattr(comparison_result, 'confidence_level', 0.8) >= min_confidence
        
        return has_sufficient_improvement and has_sufficient_confidence
    
    async def _deploy_new_prompt(
        self, 
        current_prompt: SystemPrompt, 
        new_candidate: RewriteCandidate,
        comparison_result
    ):
        """Deploy a new prompt and archive the current one"""
        
        # Create new prompt version
        new_prompt = SystemPrompt(
            session=current_prompt.session,  # Preserve session
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
        
        # Get optimization recommendations
        recommendations = await self.get_optimization_recommendations()
        
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
            },
            'recommendations': recommendations,
            'available_strategies': self.optimization_strategies
        }
    
    def _check_cold_start_status(self, session) -> bool:
        """Check if optimization is allowed based on cold start status"""
        try:
            from app.services.cold_start_manager import ColdStartManager
            cold_start_manager = ColdStartManager()
            
            # Check if cold start allows optimization
            if not cold_start_manager.should_allow_optimization(session):
                logger.info(f"Optimization blocked for session {session.id}: Cold start not complete")
                return False
            
            return True
        except ImportError:
            # If cold start manager not available, allow optimization
            logger.warning("Cold start manager not available, allowing optimization")
            return True
        except Exception as e:
            logger.error(f"Error checking cold start status: {str(e)}")
            # On error, be conservative and block optimization
            return False
    
    def optimize_prompt(self, session, feedback_list):
        """Synchronous wrapper for manual optimization trigger"""
        import asyncio
        from dataclasses import dataclass
        
        @dataclass
        class SimpleOptimizationResult:
            success: bool
            new_prompt: Optional[SystemPrompt] = None
            improvement_percentage: float = 0.0
            optimization_reason: str = ""
            error_message: str = ""
        
        # Check cold start status first
        if not self._check_cold_start_status(session):
            return SimpleOptimizationResult(
                success=False,
                error_message="Optimization blocked: Cold start phase not complete"
            )
        
        try:
            # Run the async optimization in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Convert feedback list to the format expected by the orchestrator
            trigger_analysis = {
                'should_trigger': True,
                'reason': f"Manual trigger with {len(feedback_list)} feedback items",
                'feedback_count': len(feedback_list),
                'feedback_batch': feedback_list,
                'forced_strategy': 'continuous'
            }
            
            # Execute optimization
            result = loop.run_until_complete(self._execute_optimization_cycle(trigger_analysis))
            
            # Convert to simple result format
            if result.deployed and result.best_candidate:
                # Get the newly created prompt
                new_prompt = SystemPrompt.objects.filter(
                    session=session,
                    version=result.baseline_prompt.version + 1
                ).first()
                
                return SimpleOptimizationResult(
                    success=True,
                    new_prompt=new_prompt,
                    improvement_percentage=result.improvement_percentage,
                    optimization_reason=result.trigger_reason
                )
            else:
                return SimpleOptimizationResult(
                    success=False,
                    error_message="No improvement found",
                    optimization_reason=result.trigger_reason
                )
                
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
            return SimpleOptimizationResult(
                success=False,
                error_message=str(e)
            )
        finally:
            loop.close()
    
    async def force_optimization(self, reason: str = "Manual trigger", strategy: str = "continuous", override_convergence: bool = False) -> OptimizationResult:
        """Force an optimization cycle with specified strategy"""
        
        logger.info(f"Forcing optimization with {strategy} strategy: {reason}")
        
        # Build trigger analysis for forced optimization
        trigger_analysis = {
            'should_trigger': True,
            'reason': reason,
            'feedback_count': 0,
            'feedback_batch': [],
            'forced_strategy': strategy
        }
        
        # If no recent feedback, use all feedback from last 7 days
        if not trigger_analysis['feedback_batch']:
            cutoff_time = timezone.now() - timedelta(days=7)
            recent_feedback = [
                feedback async for feedback in UserFeedback.objects.filter(
                    created_at__gte=cutoff_time
                ).select_related('draft__system_prompt')[:20]  # Limit to recent 20
            ]
            trigger_analysis['feedback_batch'] = recent_feedback
            trigger_analysis['feedback_count'] = len(recent_feedback)
        
        # Check convergence unless explicitly overridden
        if not override_convergence:
            convergence_blocked = await self._check_convergence_status(trigger_analysis.get('feedback_batch', []))
            if convergence_blocked:
                logger.warning(f"Force optimization blocked by convergence detection - use override_convergence=True to force")
                return OptimizationResult(
                    trigger_reason=f"Force optimization blocked: {reason}",
                    baseline_prompt=None,
                    candidate_prompts=[],
                    best_candidate=None,
                    evaluation_results={},
                    deployed=False,
                    improvement_percentage=0.0,
                    feedback_batch_size=len(trigger_analysis['feedback_batch']),
                    optimization_time=timezone.now()
                )
        
        return await self._execute_optimization_cycle(trigger_analysis)
    
    async def fast_optimize(self, time_budget: int = 10, min_performance: float = 0.7) -> OptimizationResult:
        """Fast optimization mode for immediate improvements"""
        
        logger.info(f"Starting fast optimization with {time_budget}s budget")
        
        # Select appropriate fast strategy based on time budget
        if time_budget < 5:
            strategy = 'emergency'
        elif time_budget < 15:
            strategy = 'continuous'
        else:
            strategy = 'batch'
        
        return await self.force_optimization(
            reason=f"Fast optimization (budget: {time_budget}s)",
            strategy=strategy
        )
    
    async def trigger_optimization_with_datasets(
        self,
        prompt_lab_id: str,
        dataset_ids: List[int],
        force: bool = False,
        optimization_run_id: Optional[str] = None
    ) -> Any:
        """Manually trigger optimization using specific evaluation datasets
        
        Args:
            prompt_lab_id: ID of the prompt lab to optimize
            dataset_ids: List of evaluation dataset IDs to use
            force: Whether to force optimization even if converged
            optimization_run_id: Optional ID for tracking optimization progress
            
        Returns:
            Evaluation result with details of the optimization
            
        Raises:
            ValueError: If no cases found in datasets or other errors occur
        """
        from .dataset_optimization_service import DatasetOptimizationService
        from .convergence_detector import ConvergenceDetector
        from core.models import PromptLab, OptimizationRun
        
        # Initialize progress reporter and metrics collector
        progress_reporter = None
        metrics_collector = MetricsCollector()
        
        if optimization_run_id:
            progress_reporter = OptimizationProgressReporter(optimization_run_id)
        
        async def update_error_status(error_message: str, step: str = None):
            """Helper function to update optimization run with error information"""
            if optimization_run_id:
                try:
                    optimization_run = await sync_to_async(OptimizationRun.objects.get)(id=optimization_run_id)
                    optimization_run.status = 'failed'
                    optimization_run.error_message = f"[{step or 'Unknown'}] {error_message}" if step else error_message
                    optimization_run.current_step = step or optimization_run.current_step
                    optimization_run.completed_at = timezone.now()
                    await sync_to_async(optimization_run.save)()
                    logger.error(f"Optimization {optimization_run_id} failed at {step}: {error_message}")
                except Exception as e:
                    logger.error(f"Failed to update error status: {e}")
        
        # 1. Load prompt lab
        prompt_lab = await sync_to_async(PromptLab.objects.get)(id=prompt_lab_id)
        
        # Get active prompt
        active_prompt = await sync_to_async(lambda: prompt_lab.prompts.filter(is_active=True).first())()
        if not active_prompt:
            raise ValueError(f"No active prompt found for prompt lab {prompt_lab_id}")
        
        # 2. Check if optimization is allowed (using convergence detector if available)
        if not force and hasattr(self, 'convergence_detector'):
            convergence = await sync_to_async(self.convergence_detector.assess_convergence)(prompt_lab)
            if convergence.get('converged', False):
                raise ValueError("Prompt has converged. Use force=True to override.")
        elif not force:
            # Simple convergence check based on whether we have a convergence detector
            try:
                convergence_detector = ConvergenceDetector()
                convergence = await sync_to_async(convergence_detector.assess_convergence)(prompt_lab)
                if convergence.get('converged', False):
                    raise ValueError("Prompt has converged. Use force=True to override.")
            except Exception as e:
                logger.warning(f"Could not check convergence: {e}")
        
        # 3. Load dataset cases
        dataset_service = DatasetOptimizationService()
        test_cases = await sync_to_async(dataset_service.load_evaluation_cases)(dataset_ids)
        
        if not test_cases:
            raise ValueError("No evaluation cases found in selected datasets")
        
        logger.info(f"Loaded {len(test_cases)} cases from {len(dataset_ids)} datasets")
        
        # 4. Generate candidate prompts using rewriter
        from .prompt_rewriter import RewriteContext
        
        rewrite_context = RewriteContext(
            email_scenario="dataset_based_optimization",
            current_prompt=active_prompt,
            recent_feedback=[],  # No user feedback for dataset-based optimization
            performance_history={},
            constraints={'manual_trigger': True, 'dataset_count': len(dataset_ids)}
        )
        
        candidates = await self.prompt_rewriter.rewrite_prompt(
            context=rewrite_context,
            mode="fast"
        )
        
        logger.info(f"Generated {len(candidates)} candidate prompts")
        
        # 6. Convert candidates to SystemPrompt objects for evaluation
        candidate_prompts = []
        for i, candidate in enumerate(candidates):
            # Create temporary SystemPrompt objects for evaluation
            from core.models import SystemPrompt
            temp_prompt = SystemPrompt(
                prompt_lab=prompt_lab,
                content=candidate.content,
                version=active_prompt.version + i + 1,
                is_active=False
            )
            candidate_prompts.append(temp_prompt)
        
        # 7. Evaluate with datasets
        comparison_results = await self.evaluation_engine.compare_prompt_candidates(
            baseline=active_prompt,
            candidates=candidate_prompts,
            test_case_count=len(test_cases),
            dataset_ids=dataset_ids,
            evaluation_config=None
        )
        
        # 8. Find best performing candidate
        best_result = None
        best_improvement = 0
        
        for result in comparison_results:
            if result.improvement > best_improvement:
                best_improvement = result.improvement
                best_result = result
        
        # 9. Deploy if improved (simplified deployment)
        deployed = False
        deployment_threshold = 5.0  # 5% improvement threshold for manual optimization
        
        if best_result and best_improvement > deployment_threshold:
            # Create and save new prompt version
            try:
                new_prompt = await sync_to_async(SystemPrompt.objects.create)(
                    prompt_lab=prompt_lab,
                    content=best_result.candidate.prompt.content,
                    version=active_prompt.version + 1,
                    is_active=True,
                    performance_score=best_result.candidate.performance_score
                )
                
                # Deactivate old prompt
                active_prompt.is_active = False
                await sync_to_async(active_prompt.save)()
                
                deployed = True
                logger.info(f"Deployed new prompt with {best_improvement:.1f}% improvement")
            except Exception as e:
                logger.error(f"Failed to deploy prompt: {e}")
        else:
            logger.info(f"Not deploying: improvement {best_improvement:.1f}% below threshold {deployment_threshold:.1f}%")
        
        # 10. Track dataset usage
        optimization_id = f"opt-{timezone.now().timestamp()}"
        await sync_to_async(dataset_service.track_dataset_usage)(
            optimization_run_id=optimization_id,
            dataset_ids=dataset_ids,
            results={'improvement': best_improvement, 'deployed': deployed}
        )
        
        # 11. Return result
        result = type('OptimizationResult', (), {
            'id': optimization_id,
            'best_candidate': type('BestCandidate', (), {
                'improvement': best_improvement / 100.0,  # Convert to decimal for API
                'deployed': deployed,
                'content': best_result.candidate.prompt.content if best_result else active_prompt.content
            })(),
            'datasets_used': len(dataset_ids),
            'test_cases_used': len(test_cases)
        })()
        
        return result
    
    def _select_optimization_strategy(self, trigger_analysis: Dict[str, Any], feedback_count: int) -> Dict[str, Any]:
        """Select optimization strategy based on context"""
        
        # Check if strategy is forced
        if 'forced_strategy' in trigger_analysis:
            strategy_name = trigger_analysis['forced_strategy']
            if strategy_name in self.optimization_strategies:
                strategy = self.optimization_strategies[strategy_name].copy()
                strategy['name'] = strategy_name
                return strategy
        
        # Select strategy based on urgency and feedback volume
        negative_ratio = trigger_analysis.get('negative_feedback_ratio', 0.0)
        average_rating = trigger_analysis.get('average_rating', 3.0)
        
        # Emergency mode for critical issues
        if negative_ratio > 0.6 or average_rating < 2.0:
            strategy = self.optimization_strategies['emergency'].copy()
            strategy['name'] = 'emergency'
            return strategy
        
        # Batch mode for large feedback volumes
        elif feedback_count >= 20:
            strategy = self.optimization_strategies['batch'].copy()
            strategy['name'] = 'batch'
            return strategy
        
        # Continuous mode for regular optimization
        elif feedback_count >= 10:
            strategy = self.optimization_strategies['continuous'].copy()
            strategy['name'] = 'continuous'
            return strategy
        
        # Emergency mode for low feedback (quick iteration)
        else:
            strategy = self.optimization_strategies['emergency'].copy()
            strategy['name'] = 'emergency'
            return strategy
    
    async def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for optimization strategy"""
        
        # Analyze current feedback state
        trigger_analysis = await self._analyze_feedback_for_triggers()
        
        # Determine recommended strategy
        recommended_strategy = self._select_optimization_strategy(
            trigger_analysis, 
            trigger_analysis.get('feedback_count', 0)
        )
        
        return {
            'should_optimize': trigger_analysis['should_trigger'],
            'trigger_reason': trigger_analysis.get('reason', 'No trigger'),
            'recommended_strategy': recommended_strategy['name'],
            'estimated_time': recommended_strategy['timeout'],
            'expected_improvement': recommended_strategy['min_improvement'],
            'feedback_analysis': {
                'count': trigger_analysis.get('feedback_count', 0),
                'negative_ratio': trigger_analysis.get('negative_feedback_ratio', 0.0),
                'average_rating': trigger_analysis.get('average_rating', 3.0)
            },
            'available_strategies': list(self.optimization_strategies.keys())
        }
    
    async def _check_convergence_status(self, feedback_batch: List[UserFeedback]) -> bool:
        """Check if optimization should be blocked due to convergence"""
        try:
            from app.services.convergence_detector import ConvergenceDetector
            
            # Extract prompt lab from feedback if available
            prompt_lab = None
            if feedback_batch:
                first_feedback = feedback_batch[0]
                if hasattr(first_feedback, 'draft') and hasattr(first_feedback.draft, 'email'):
                    prompt_lab = first_feedback.draft.email.prompt_lab
            
            # If no prompt lab found from feedback, get the most recently updated prompt lab
            if not prompt_lab:
                from core.models import PromptLab
                prompt_lab = await sync_to_async(
                    PromptLab.objects.filter(is_active=True).order_by('-updated_at').first
                )()
            
            if not prompt_lab:
                logger.warning("No prompt lab found for convergence check - allowing optimization")
                return False
            
            # Initialize convergence detector
            detector = ConvergenceDetector()
            
            # Check if convergence assessment should be performed
            should_check = await sync_to_async(detector.should_check_convergence)(prompt_lab)
            if not should_check:
                logger.info(f"Convergence check not needed for prompt lab {prompt_lab.id}")
                return False
            
            # Perform convergence assessment
            assessment = await sync_to_async(detector.assess_convergence)(prompt_lab)
            
            if assessment.get('converged', False):
                confidence = assessment.get('confidence_score', 0.0)
                factors = assessment.get('factors', {})
                recommendations = assessment.get('recommendations', [])
                
                logger.info(f"PromptLab {prompt_lab.id} has converged (confidence: {confidence:.2f})")
                logger.info(f"Convergence factors: {factors}")
                
                # Log convergence recommendations
                for rec in recommendations:
                    if rec.get('action') == 'stop_optimization':
                        logger.info(f"Convergence recommendation: {rec.get('reason', 'Stop optimization')}")
                
                return True
            
            else:
                logger.info(f"PromptLab {prompt_lab.id} has not converged - optimization can proceed")
                return False
                
        except Exception as e:
            logger.error(f"Error checking convergence status: {str(e)}")
            # On error, allow optimization to proceed to avoid blocking the system
            return False