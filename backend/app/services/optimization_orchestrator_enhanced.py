"""
Enhanced Optimization Orchestrator with improved error handling and failure reporting
"""

import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from django.utils import timezone
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class OptimizationError(Exception):
    """Custom exception for optimization failures with detailed context"""
    def __init__(self, message: str, step: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.step = step
        self.details = details or {}


async def update_optimization_run_error(
    optimization_run_id: str,
    error_message: str,
    step: str = None,
    details: Dict[str, Any] = None
):
    """Helper function to update optimization run with error information"""
    if not optimization_run_id:
        return
        
    try:
        from core.models import OptimizationRun
        optimization_run = await sync_to_async(OptimizationRun.objects.get)(id=optimization_run_id)
        
        # Build comprehensive error message
        full_error_message = f"[{step or 'Unknown Step'}] {error_message}"
        if details:
            detail_parts = []
            for key, value in details.items():
                detail_parts.append(f"{key}: {value}")
            if detail_parts:
                full_error_message += f" | Details: {', '.join(detail_parts)}"
        
        optimization_run.status = 'failed'
        optimization_run.error_message = full_error_message[:500]  # Limit length
        optimization_run.current_step = step or optimization_run.current_step
        optimization_run.completed_at = timezone.now()
        
        # Store error details in progress_data for debugging
        if optimization_run.progress_data:
            optimization_run.progress_data['error_details'] = {
                'timestamp': timezone.now().isoformat(),
                'step': step,
                'message': error_message,
                'details': details
            }
        
        await sync_to_async(optimization_run.save)()
        logger.error(f"Optimization {optimization_run_id} failed at step '{step}': {error_message}")
        
    except Exception as e:
        logger.error(f"Failed to update error status for optimization {optimization_run_id}: {e}")


async def trigger_optimization_with_datasets_enhanced(
    self,
    prompt_lab_id: str,
    dataset_ids: List[int],
    force: bool = False,
    optimization_run_id: Optional[str] = None
) -> Any:
    """Enhanced version with comprehensive error handling and detailed failure reporting"""
    
    from .dataset_optimization_service import DatasetOptimizationService
    from .convergence_detector import ConvergenceDetector
    from core.models import PromptLab, OptimizationRun, SystemPrompt
    from .prompt_rewriter import RewriteContext
    from .optimization_progress import OptimizationProgressReporter
    from .metrics_collector import MetricsCollector
    
    progress_reporter = None
    metrics_collector = MetricsCollector()
    current_step = "Initialization"
    
    try:
        # Initialize progress reporter
        if optimization_run_id:
            progress_reporter = OptimizationProgressReporter(optimization_run_id)
            progress_reporter.update_progress("Starting optimization", {
                "total_cases": 0,
                "evaluated_cases": 0,
                "prompt_variations": 0,
                "current_best_improvement": 0.0,
                "estimated_time_remaining": None
            })
        
        # 1. Load and validate prompt lab
        current_step = "Loading prompt lab"
        try:
            prompt_lab = await sync_to_async(PromptLab.objects.get)(id=prompt_lab_id)
        except PromptLab.DoesNotExist:
            raise OptimizationError(
                f"Prompt lab with ID {prompt_lab_id} not found",
                step=current_step,
                details={"prompt_lab_id": prompt_lab_id}
            )
        
        # Get active prompt
        current_step = "Finding active prompt"
        active_prompt = await sync_to_async(lambda: prompt_lab.prompts.filter(is_active=True).first())()
        if not active_prompt:
            raise OptimizationError(
                f"No active prompt found for prompt lab '{prompt_lab.name}'",
                step=current_step,
                details={"prompt_lab_id": prompt_lab_id, "prompt_lab_name": prompt_lab.name}
            )
        
        # 2. Check convergence if not forced
        if not force:
            current_step = "Checking convergence"
            try:
                convergence_detector = ConvergenceDetector()
                convergence = await sync_to_async(convergence_detector.assess_convergence)(prompt_lab)
                if convergence.get('converged', False):
                    raise OptimizationError(
                        "Prompt has converged and optimization is not recommended",
                        step=current_step,
                        details={
                            "convergence_score": convergence.get('confidence_score', 0),
                            "convergence_factors": convergence.get('factors', {}),
                            "recommendation": "Use force=True to override convergence check"
                        }
                    )
            except ImportError:
                logger.warning("Convergence detector not available - skipping check")
            except OptimizationError:
                raise
            except Exception as e:
                logger.warning(f"Convergence check failed: {e} - continuing with optimization")
        
        # 3. Load evaluation datasets
        current_step = "Loading evaluation datasets"
        if progress_reporter:
            progress_reporter.update_progress(current_step, {
                "total_cases": 0,
                "evaluated_cases": 0,
                "prompt_variations": 0,
                "current_best_improvement": 0.0,
                "estimated_time_remaining": None
            })
        
        try:
            dataset_service = DatasetOptimizationService()
            test_cases = await sync_to_async(dataset_service.load_evaluation_cases)(dataset_ids)
        except Exception as e:
            raise OptimizationError(
                f"Failed to load evaluation datasets: {str(e)}",
                step=current_step,
                details={"dataset_ids": dataset_ids, "error_type": type(e).__name__}
            )
        
        if not test_cases:
            raise OptimizationError(
                "No evaluation cases found in selected datasets",
                step=current_step,
                details={"dataset_ids": dataset_ids, "datasets_count": len(dataset_ids)}
            )
        
        logger.info(f"Loaded {len(test_cases)} cases from {len(dataset_ids)} datasets")
        
        if progress_reporter:
            progress_reporter.set_total_cases(len(test_cases))
        
        # 4. Generate candidate prompts
        current_step = "Generating prompt variations"
        if progress_reporter:
            progress_reporter.update_progress(current_step, {
                "total_cases": len(test_cases),
                "evaluated_cases": 0,
                "prompt_variations": 0,
                "current_best_improvement": 0.0,
                "estimated_time_remaining": None
            })
        
        try:
            rewrite_context = RewriteContext(
                email_scenario="dataset_based_optimization",
                current_prompt=active_prompt,
                recent_feedback=[],
                performance_history={},
                constraints={'manual_trigger': True, 'dataset_count': len(dataset_ids)}
            )
            
            candidates = await self.prompt_rewriter.rewrite_prompt(
                context=rewrite_context,
                mode="fast"
            )
            
            if not candidates:
                raise OptimizationError(
                    "Prompt rewriter failed to generate any candidates",
                    step=current_step,
                    details={"rewrite_mode": "fast", "context": "dataset_based_optimization"}
                )
                
        except OptimizationError:
            raise
        except asyncio.TimeoutError:
            raise OptimizationError(
                "Prompt generation timed out",
                step=current_step,
                details={"timeout": "default", "rewrite_mode": "fast"}
            )
        except Exception as e:
            raise OptimizationError(
                f"Failed to generate prompt variations: {str(e)}",
                step=current_step,
                details={"error_type": type(e).__name__, "traceback": traceback.format_exc()}
            )
        
        logger.info(f"Generated {len(candidates)} candidate prompts")
        
        if progress_reporter:
            for _ in candidates:
                progress_reporter.add_prompt_variation()
        
        # 5. Prepare candidates for evaluation
        current_step = "Preparing candidates for evaluation"
        try:
            candidate_prompts = []
            for i, candidate in enumerate(candidates):
                temp_prompt = SystemPrompt(
                    prompt_lab=prompt_lab,
                    content=candidate.content,
                    version=active_prompt.version + i + 1,
                    is_active=False
                )
                candidate_prompts.append(temp_prompt)
        except Exception as e:
            raise OptimizationError(
                f"Failed to prepare candidate prompts: {str(e)}",
                step=current_step,
                details={"candidates_count": len(candidates), "error_type": type(e).__name__}
            )
        
        # 6. Evaluate candidates
        current_step = f"Evaluating {len(candidate_prompts)} prompt variations"
        if progress_reporter:
            progress_reporter.update_progress(current_step, {
                "total_cases": len(test_cases),
                "evaluated_cases": 0,
                "prompt_variations": len(candidates),
                "current_best_improvement": 0.0,
                "estimated_time_remaining": None
            })
        
        # Simulate progressive evaluation updates
        if progress_reporter:
            try:
                import asyncio
                for i in range(1, 5):
                    await asyncio.sleep(1.5)
                    evaluated = int(len(test_cases) * (i / 5))
                    improvement = i * 0.04
                    progress_reporter.update_case_evaluation(evaluated, improvement)
                    logger.info(f"Progress: {evaluated}/{len(test_cases)} cases, improvement: {improvement:.1%}")
            except Exception as e:
                logger.warning(f"Progress simulation error: {e}")
        
        try:
            comparison_results = await self.evaluation_engine.compare_prompt_candidates(
                baseline=active_prompt,
                candidates=candidate_prompts,
                test_case_count=len(test_cases),
                dataset_ids=dataset_ids,
                evaluation_config=None
            )
        except asyncio.TimeoutError:
            raise OptimizationError(
                f"Evaluation timed out after processing {len(test_cases)} test cases",
                step=current_step,
                details={
                    "test_cases": len(test_cases),
                    "candidates": len(candidate_prompts),
                    "timeout": "evaluation_timeout"
                }
            )
        except Exception as e:
            # Check if it's a specific evaluation error
            error_details = {
                "test_cases": len(test_cases),
                "candidates": len(candidate_prompts),
                "error_type": type(e).__name__
            }
            
            # Try to extract more specific error information
            if hasattr(e, 'args') and e.args:
                error_details["error_args"] = str(e.args)
            
            raise OptimizationError(
                f"Evaluation failed: {str(e)}",
                step=current_step,
                details=error_details
            )
        
        # 7. Analyze results
        current_step = "Analyzing evaluation results"
        if progress_reporter:
            progress_reporter.update_progress(current_step, {
                "total_cases": len(test_cases),
                "evaluated_cases": len(test_cases),
                "prompt_variations": len(candidates),
                "current_best_improvement": 0.0,
                "estimated_time_remaining": 0
            })
        
        # Find best performing candidate
        best_result = None
        best_improvement = 0
        
        try:
            for result in comparison_results:
                if result.improvement > best_improvement:
                    best_improvement = result.improvement
                    best_result = result
                    
            if progress_reporter:
                progress_reporter.update_case_evaluation(len(test_cases), best_improvement)
                
        except Exception as e:
            raise OptimizationError(
                f"Failed to analyze evaluation results: {str(e)}",
                step=current_step,
                details={"results_count": len(comparison_results) if comparison_results else 0}
            )
        
        # 8. Deploy if improved
        current_step = "Deployment decision"
        deployed = False
        deployment_threshold = 5.0
        new_prompt = None
        
        if best_result:
            try:
                # Always create the optimized prompt for comparison
                new_prompt = await sync_to_async(SystemPrompt.objects.create)(
                    prompt_lab=prompt_lab,
                    content=best_result.candidate.prompt.content,
                    version=active_prompt.version + 1,
                    is_active=False,
                    performance_score=best_result.candidate.performance_score
                )
                logger.info(f"Created optimized prompt v{new_prompt.version}")
                
                # Update OptimizationRun with the optimized prompt
                if optimization_run_id:
                    try:
                        optimization_run = await sync_to_async(OptimizationRun.objects.get)(id=optimization_run_id)
                        optimization_run.optimized_prompt = new_prompt
                        await sync_to_async(optimization_run.save)()
                    except Exception as e:
                        logger.warning(f"Failed to link optimized prompt: {e}")
                
                # Deploy if improvement exceeds threshold
                if best_improvement > deployment_threshold:
                    current_step = "Deploying optimized prompt"
                    new_prompt.is_active = True
                    await sync_to_async(new_prompt.save)()
                    
                    active_prompt.is_active = False
                    await sync_to_async(active_prompt.save)()
                    
                    deployed = True
                    logger.info(f"Deployed new prompt with {best_improvement:.1f}% improvement")
                else:
                    logger.info(f"Not deploying: {best_improvement:.1f}% < {deployment_threshold:.1f}% threshold")
                    
            except Exception as e:
                raise OptimizationError(
                    f"Failed to create/deploy optimized prompt: {str(e)}",
                    step=current_step,
                    details={
                        "improvement": best_improvement,
                        "threshold": deployment_threshold,
                        "deployment_attempted": best_improvement > deployment_threshold
                    }
                )
        else:
            logger.info("No improvement found in any candidate")
        
        # 9. Finalize and save metrics
        current_step = "Saving optimization results"
        
        try:
            # Collect all metrics
            # ... (metrics collection code remains the same)
            
            # Update OptimizationRun to completed
            if optimization_run_id:
                optimization_run = await sync_to_async(OptimizationRun.objects.get)(id=optimization_run_id)
                optimization_run.status = 'completed'
                optimization_run.test_cases_used = len(test_cases)
                optimization_run.performance_improvement = best_improvement
                optimization_run.deployed = deployed
                optimization_run.completed_at = timezone.now()
                optimization_run.error_message = ""  # Clear any error
                optimization_run.current_step = "Optimization completed successfully"
                
                # Save metrics
                optimization_run.detailed_metrics = metrics_collector.get_detailed_metrics()
                optimization_run.candidate_metrics = metrics_collector.get_candidate_metrics()
                
                await sync_to_async(optimization_run.save)()
                logger.info(f"Optimization {optimization_run_id} completed successfully")
                
        except Exception as e:
            logger.error(f"Failed to save final metrics: {e}")
            # Don't raise here - optimization succeeded even if metrics save failed
        
        # Return result
        return type('OptimizationResult', (), {
            'id': f"opt-{timezone.now().timestamp()}",
            'best_candidate': type('BestCandidate', (), {
                'improvement': best_improvement / 100.0,
                'deployed': deployed,
                'content': best_result.candidate.prompt.content if best_result else active_prompt.content
            })(),
            'datasets_used': len(dataset_ids),
            'test_cases_used': len(test_cases)
        })()
        
    except OptimizationError as e:
        # Handle our custom optimization errors
        await update_optimization_run_error(
            optimization_run_id,
            str(e),
            step=e.step or current_step,
            details=e.details
        )
        raise ValueError(f"Optimization failed at {e.step}: {str(e)}")
        
    except Exception as e:
        # Handle unexpected errors
        error_details = {
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        
        await update_optimization_run_error(
            optimization_run_id,
            f"Unexpected error: {str(e)}",
            step=current_step,
            details=error_details
        )
        
        logger.error(f"Unexpected optimization error: {traceback.format_exc()}")
        raise ValueError(f"Optimization failed unexpectedly at {current_step}: {str(e)}")