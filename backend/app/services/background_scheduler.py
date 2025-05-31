"""
Background Scheduler for automated optimization triggers
Runs periodic checks for batch-based optimization triggers
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.utils import timezone

from .optimization_orchestrator import OptimizationOrchestrator, OptimizationTrigger
from .prompt_rewriter import PromptRewriter
from .evaluation_engine import EvaluationEngine
from .reward_aggregator import RewardFunctionAggregator
from .unified_llm_provider import LLMProviderFactory, LLMConfig

logger = logging.getLogger(__name__)


class BackgroundOptimizationScheduler:
    """Background scheduler for automated optimization based on feedback thresholds"""
    
    def __init__(self, trigger_config: OptimizationTrigger = None):
        self.trigger_config = trigger_config or OptimizationTrigger()
        self._last_optimization_time = None
        self._optimization_count_today = 0
        self._last_count_reset_date = None
    
    def check_and_trigger_optimization(self, session=None):
        """Check if optimization should be triggered and execute if needed"""
        from core.models import Session, SystemPrompt, UserFeedback
        
        # Reset daily count if needed
        self._reset_daily_count_if_needed()
        
        # Track if we're checking a specific session
        specific_session_check = session is not None
        
        # Check time-based constraints
        if not self._can_optimize_based_on_time():
            logger.info("Skipping optimization: too soon since last optimization")
            return False
        
        # Check daily limit
        if self._optimization_count_today >= self.trigger_config.max_optimization_frequency_per_day:
            logger.info("Skipping optimization: daily limit reached")
            return False
        
        # Get sessions to check
        if specific_session_check:
            sessions_to_check = [session]
        else:
            sessions_to_check = Session.objects.filter(is_active=True)
        
        optimization_triggered = False
        
        for current_session in sessions_to_check:
            # Check if session has active prompt
            if not SystemPrompt.objects.filter(session=current_session, is_active=True).exists():
                continue
            
            # Get recent feedback
            cutoff_time = timezone.now() - timedelta(hours=self.trigger_config.feedback_window_hours)
            recent_feedback = UserFeedback.objects.filter(
                draft__email__session=current_session,
                created_at__gte=cutoff_time
            ).select_related('draft', 'draft__email')
            
            feedback_count = recent_feedback.count()
            
            # Check minimum feedback count
            if feedback_count < self.trigger_config.min_feedback_count:
                logger.debug(f"Session {current_session.id}: Not enough feedback ({feedback_count} < {self.trigger_config.min_feedback_count})")
                continue
            
            # Calculate negative feedback ratio
            negative_feedback_count = recent_feedback.filter(
                action__in=['reject', 'edit']
            ).count()
            negative_ratio = negative_feedback_count / feedback_count if feedback_count > 0 else 0
            
            # Check negative feedback threshold
            if negative_ratio < self.trigger_config.min_negative_feedback_ratio:
                logger.debug(f"Session {current_session.id}: Negative ratio too low ({negative_ratio:.2f} < {self.trigger_config.min_negative_feedback_ratio})")
                continue
            
            # Trigger optimization
            logger.info(f"Triggering optimization for session {current_session.id}: {negative_ratio:.0%} negative feedback")
            result = self._execute_optimization(current_session, list(recent_feedback))
            
            if result.get('success'):
                self._last_optimization_time = timezone.now()
                self._optimization_count_today += 1
                optimization_triggered = True
                
                # If checking a specific session, return the result immediately
                if specific_session_check:
                    return True
        
        return optimization_triggered
    
    def _can_optimize_based_on_time(self):
        """Check if enough time has passed since last optimization"""
        if not self._last_optimization_time:
            return True
        
        time_since_last = timezone.now() - self._last_optimization_time
        min_interval = timedelta(hours=self.trigger_config.min_time_since_last_optimization_hours)
        
        return time_since_last >= min_interval
    
    def _reset_daily_count_if_needed(self):
        """Reset daily optimization count if it's a new day"""
        today = timezone.now().date()
        if self._last_count_reset_date != today:
            self._optimization_count_today = 0
            self._last_count_reset_date = today
    
    def _execute_optimization(self, session, feedback_list):
        """Execute the optimization"""
        from app.services.optimization_orchestrator import OptimizationOrchestrator
        
        try:
            orchestrator = OptimizationOrchestrator()
            result = orchestrator.optimize_prompt(session, feedback_list)
            
            if result.success:
                return {
                    'success': True,
                    'new_prompt_version': result.new_prompt.version,
                    'improvement_percentage': result.improvement_percentage
                }
            else:
                return {
                    'success': False,
                    'error': result.error_message
                }
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_all_sessions(self):
        """Check all active sessions for optimization triggers"""
        from core.models import Session, SystemPrompt, UserFeedback
        
        results = []
        sessions = Session.objects.filter(is_active=True)
        
        # Reset daily count if needed
        self._reset_daily_count_if_needed()
        
        # Check time constraints once for all sessions
        if not self._can_optimize_based_on_time():
            logger.info("Skipping all optimizations: too soon since last optimization")
            for session in sessions:
                results.append({
                    'session_id': session.id,
                    'session_name': session.name,
                    'triggered': False
                })
            return results
        
        # Check daily limit
        if self._optimization_count_today >= self.trigger_config.max_optimization_frequency_per_day:
            logger.info("Skipping all optimizations: daily limit reached")
            for session in sessions:
                results.append({
                    'session_id': session.id,
                    'session_name': session.name,
                    'triggered': False
                })
            return results
        
        # Now check each session without time constraints
        for session in sessions:
            triggered = False
            
            # Check if session has active prompt
            if not SystemPrompt.objects.filter(session=session, is_active=True).exists():
                results.append({
                    'session_id': session.id,
                    'session_name': session.name,
                    'triggered': False
                })
                continue
            
            # Get recent feedback
            cutoff_time = timezone.now() - timedelta(hours=self.trigger_config.feedback_window_hours)
            recent_feedback = UserFeedback.objects.filter(
                draft__email__session=session,
                created_at__gte=cutoff_time
            ).select_related('draft', 'draft__email')
            
            feedback_count = recent_feedback.count()
            
            # Check minimum feedback count
            if feedback_count < self.trigger_config.min_feedback_count:
                logger.debug(f"Session {session.id}: Not enough feedback ({feedback_count} < {self.trigger_config.min_feedback_count})")
                results.append({
                    'session_id': session.id,
                    'session_name': session.name,
                    'triggered': False
                })
                continue
            
            # Calculate negative feedback ratio
            negative_feedback_count = recent_feedback.filter(
                action__in=['reject', 'edit']
            ).count()
            negative_ratio = negative_feedback_count / feedback_count if feedback_count > 0 else 0
            
            # Check negative feedback threshold
            if negative_ratio < self.trigger_config.min_negative_feedback_ratio:
                logger.debug(f"Session {session.id}: Negative ratio too low ({negative_ratio:.2f} < {self.trigger_config.min_negative_feedback_ratio})")
                results.append({
                    'session_id': session.id,
                    'session_name': session.name,
                    'triggered': False
                })
                continue
            
            # Trigger optimization
            logger.info(f"Triggering optimization for session {session.id}: {negative_ratio:.0%} negative feedback")
            result = self._execute_optimization(session, list(recent_feedback))
            
            if result.get('success'):
                self._last_optimization_time = timezone.now()
                self._optimization_count_today += 1
                triggered = True
            
            results.append({
                'session_id': session.id,
                'session_name': session.name,
                'triggered': triggered
            })
        
        return results


class OptimizationScheduler:
    """Schedules and manages automated optimization checks"""
    
    def __init__(
        self,
        check_interval_minutes: int = 60,  # Check every hour by default
        trigger_config: OptimizationTrigger = None
    ):
        self.check_interval_minutes = check_interval_minutes
        self.trigger_config = trigger_config or OptimizationTrigger()
        self.orchestrator: Optional[OptimizationOrchestrator] = None
        self.scheduler_task: Optional[asyncio.Task] = None
        self.is_running = False
        self._last_check_time: Optional[datetime] = None
        self._check_count = 0
        self._optimization_count = 0
    
    async def initialize(self, llm_config: LLMConfig):
        """Initialize the scheduler with LLM configuration"""
        
        # Create LLM provider
        llm_provider = LLMProviderFactory.create_provider(llm_config)
        
        # Create reward aggregator
        reward_aggregator = RewardFunctionAggregator(llm_provider)
        
        # Create evaluation engine
        evaluation_engine = EvaluationEngine(llm_provider, reward_aggregator)
        
        # Create prompt rewriter
        prompt_rewriter = PromptRewriter(llm_provider, reward_aggregator)
        
        # Create orchestrator
        self.orchestrator = OptimizationOrchestrator(
            llm_provider=llm_provider,
            prompt_rewriter=prompt_rewriter,
            evaluation_engine=evaluation_engine,
            trigger_config=self.trigger_config
        )
        
        logger.info("Optimization scheduler initialized")
    
    async def start(self):
        """Start the background optimization scheduler"""
        
        if not self.orchestrator:
            raise ValueError("Scheduler not initialized. Call initialize() first.")
        
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info(f"Started optimization scheduler (check interval: {self.check_interval_minutes} minutes)")
    
    async def stop(self):
        """Stop the background scheduler"""
        
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped optimization scheduler")
    
    async def _scheduler_loop(self):
        """Main scheduler loop that runs optimization checks"""
        
        logger.info("Optimization scheduler loop started")
        
        while self.is_running:
            try:
                await self._run_optimization_check()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval_minutes * 60)
                
            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                # Continue running even if one check fails
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    async def _run_optimization_check(self):
        """Run a single optimization check"""
        
        self._last_check_time = timezone.now()
        self._check_count += 1
        
        logger.info(f"Running optimization check #{self._check_count}")
        
        try:
            # Check if optimization should be triggered
            result = await self.orchestrator.check_and_trigger_optimization()
            
            if result:
                self._optimization_count += 1
                logger.info(
                    f"Optimization #{self._optimization_count} completed: "
                    f"{result.trigger_reason}, "
                    f"improvement: {result.improvement_percentage:.1f}%, "
                    f"deployed: {result.deployed}"
                )
            else:
                logger.debug("No optimization triggered this check")
            
        except Exception as e:
            logger.error(f"Error during optimization check: {e}", exc_info=True)
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status and statistics"""
        
        orchestrator_status = {}
        if self.orchestrator:
            orchestrator_status = await self.orchestrator.get_optimization_status()
        
        return {
            'is_running': self.is_running,
            'check_interval_minutes': self.check_interval_minutes,
            'last_check_time': self._last_check_time,
            'total_checks': self._check_count,
            'total_optimizations': self._optimization_count,
            'next_check_time': (
                self._last_check_time + timedelta(minutes=self.check_interval_minutes)
            ) if self._last_check_time else None,
            'orchestrator_status': orchestrator_status
        }
    
    async def force_check(self) -> Optional[Dict[str, Any]]:
        """Force an immediate optimization check"""
        
        if not self.orchestrator:
            raise ValueError("Scheduler not initialized")
        
        logger.info("Forcing immediate optimization check")
        
        result = await self.orchestrator.check_and_trigger_optimization()
        
        if result:
            self._optimization_count += 1
            return {
                'triggered': True,
                'reason': result.trigger_reason,
                'improvement': result.improvement_percentage,
                'deployed': result.deployed,
                'feedback_batch_size': result.feedback_batch_size
            }
        else:
            return {
                'triggered': False,
                'reason': 'No optimization triggers met'
            }


# Global scheduler instance
_scheduler_instance: Optional[OptimizationScheduler] = None


async def get_scheduler() -> OptimizationScheduler:
    """Get the global scheduler instance"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = OptimizationScheduler()
    
    return _scheduler_instance


async def start_optimization_scheduler(llm_config: LLMConfig):
    """Start the global optimization scheduler"""
    scheduler = await get_scheduler()
    
    if not scheduler.orchestrator:
        await scheduler.initialize(llm_config)
    
    await scheduler.start()


async def stop_optimization_scheduler():
    """Stop the global optimization scheduler"""
    global _scheduler_instance
    
    if _scheduler_instance:
        await _scheduler_instance.stop()


async def get_optimization_status() -> Dict[str, Any]:
    """Get optimization scheduler status"""
    global _scheduler_instance
    
    if _scheduler_instance:
        return await _scheduler_instance.get_scheduler_status()
    else:
        return {
            'is_running': False,
            'scheduler_initialized': False
        }