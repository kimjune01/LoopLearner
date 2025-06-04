"""
Progress tracking for optimization runs
"""

import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from core.models import OptimizationRun

logger = logging.getLogger(__name__)


class OptimizationProgressReporter:
    """Reports progress during optimization runs"""
    
    def __init__(self, optimization_run_id: str):
        self.run_id = optimization_run_id
        self._start_time = timezone.now()
        self._total_cases = 0
        self._evaluated_cases = 0
        self._prompt_variations = 0
        self._current_best_improvement = 0.0
        
    def set_total_cases(self, total: int):
        """Set the total number of test cases to evaluate"""
        self._total_cases = total
        self.update_progress(
            current_step="Loading evaluation datasets",
            progress_data={
                "total_cases": total,
                "evaluated_cases": 0,
                "prompt_variations": 0,
                "current_best_improvement": 0.0,
                "estimated_time_remaining": None
            }
        )
        
    def update_case_evaluation(self, evaluated: int, current_improvement: float):
        """Update progress after evaluating test cases"""
        self._evaluated_cases = evaluated
        self._current_best_improvement = max(self._current_best_improvement, current_improvement)
        
        # Estimate time remaining
        elapsed = (timezone.now() - self._start_time).total_seconds()
        if evaluated > 0:
            avg_time_per_case = elapsed / evaluated
            remaining_cases = self._total_cases - evaluated
            estimated_remaining = int(avg_time_per_case * remaining_cases)
        else:
            estimated_remaining = None
            
        self.update_progress(
            current_step=f"Evaluating test cases ({evaluated}/{self._total_cases})",
            progress_data={
                "total_cases": self._total_cases,
                "evaluated_cases": evaluated,
                "prompt_variations": self._prompt_variations,
                "current_best_improvement": self._current_best_improvement,
                "estimated_time_remaining": estimated_remaining
            }
        )
        
    def add_prompt_variation(self):
        """Increment the count of prompt variations tested"""
        self._prompt_variations += 1
        self.update_progress(
            current_step=f"Testing prompt variation #{self._prompt_variations}",
            progress_data={
                "total_cases": self._total_cases,
                "evaluated_cases": self._evaluated_cases,
                "prompt_variations": self._prompt_variations,
                "current_best_improvement": self._current_best_improvement,
                "estimated_time_remaining": None
            }
        )
        
    def update_progress(self, current_step: str, progress_data: Dict[str, Any]):
        """Update the optimization run with current progress"""
        try:
            import asyncio
            from asgiref.sync import sync_to_async
            from django.db import transaction
            
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in async context - use sync_to_async
                self._update_progress_async(current_step, progress_data)
            except RuntimeError:
                # We're in sync context - use regular sync methods
                with transaction.atomic():
                    optimization_run = OptimizationRun.objects.get(id=self.run_id)
                    optimization_run.current_step = current_step
                    optimization_run.progress_data = progress_data
                    optimization_run.save(update_fields=['current_step', 'progress_data'])
                
                logger.info(f"Progress updated for run {self.run_id}: {current_step}")
                logger.debug(f"Progress data: {progress_data}")
                
        except OptimizationRun.DoesNotExist:
            logger.error(f"Optimization run {self.run_id} not found")
        except Exception as e:
            logger.error(f"Error updating progress: {e}", exc_info=True)
    
    def _update_progress_async(self, current_step: str, progress_data: Dict[str, Any]):
        """Helper method to update progress from async context"""
        import asyncio
        from asgiref.sync import sync_to_async
        
        async def _do_update():
            try:
                # Use sync_to_async for database operations
                optimization_run = await sync_to_async(OptimizationRun.objects.get)(id=self.run_id)
                optimization_run.current_step = current_step
                optimization_run.progress_data = progress_data
                await sync_to_async(optimization_run.save)(update_fields=['current_step', 'progress_data'])
                
                logger.info(f"Progress updated for run {self.run_id}: {current_step}")
                logger.debug(f"Progress data: {progress_data}")
            except Exception as e:
                logger.error(f"Error in async progress update: {e}", exc_info=True)
        
        # Schedule the update to run in the current event loop
        asyncio.create_task(_do_update())
            
    def report_completion(self, improvement: float):
        """Report that optimization is complete"""
        self.update_progress(
            current_step="Optimization complete",
            progress_data={
                "total_cases": self._total_cases,
                "evaluated_cases": self._total_cases,
                "prompt_variations": self._prompt_variations,
                "current_best_improvement": improvement,
                "estimated_time_remaining": 0
            }
        )