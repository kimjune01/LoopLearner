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