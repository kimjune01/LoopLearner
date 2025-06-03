"""
Service for handling dataset-based prompt optimization
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from django.db import transaction
from django.utils import timezone

from core.models import (
    EvaluationDataset, EvaluationCase, PromptLab
)

logger = logging.getLogger(__name__)


class DatasetOptimizationService:
    """Handles dataset selection and management for prompt optimization"""
    
    def __init__(self):
        """Initialize the service"""
        pass
    
    def select_datasets_for_optimization(
        self,
        prompt_lab_id: str,
        parameters: List[str],
        limit: int = 5
    ) -> List[EvaluationDataset]:
        """
        Select relevant datasets based on prompt parameters and quality scores
        
        Args:
            prompt_lab_id: ID of the prompt lab
            parameters: List of parameter names from the prompt
            limit: Maximum number of datasets to return
            
        Returns:
            List of selected datasets sorted by quality score
        """
        # Get all datasets for the prompt lab
        datasets = self._get_datasets_for_prompt_lab(prompt_lab_id)
        
        # Filter datasets that have at least one matching parameter
        matching_datasets = []
        for dataset in datasets:
            if dataset.parameters:
                # Check if any dataset parameter matches prompt parameters
                if any(param in parameters for param in dataset.parameters):
                    matching_datasets.append(dataset)
        
        # Sort by quality score (descending)
        matching_datasets.sort(
            key=lambda d: getattr(d, 'quality_score', 0.5),
            reverse=True
        )
        
        # Return top N datasets
        return matching_datasets[:limit]
    
    def load_evaluation_cases(
        self,
        dataset_ids: List[int],
        limit: int = 50
    ) -> List[EvaluationCase]:
        """
        Load evaluation cases from selected datasets
        
        Args:
            dataset_ids: List of dataset IDs to load cases from
            limit: Maximum number of cases to return
            
        Returns:
            List of evaluation cases prioritized by human review status
        """
        if not dataset_ids:
            return []
        
        # Get cases from all specified datasets
        cases = self._get_cases_for_datasets(dataset_ids)
        
        # Sort cases: human-reviewed first, then by ID for stability
        cases.sort(
            key=lambda c: (
                not (c.context.get('is_human_reviewed', False) if hasattr(c, 'context') and isinstance(c.context, dict) else False),  # True values first
                c.id
            )
        )
        
        # Return limited number of cases
        return cases[:limit]
    
    def track_dataset_usage(
        self,
        optimization_run_id: str,
        dataset_ids: List[int],
        results: Dict[str, Any]
    ) -> None:
        """
        Record which datasets were used in an optimization run
        
        Args:
            optimization_run_id: ID of the optimization run
            dataset_ids: List of dataset IDs that were used
            results: Optimization results including improvement metrics
        """
        # Extract improvement from results
        improvement = results.get('improvement', 0.0)
        
        # Save usage record
        self._save_dataset_usage(
            optimization_run_id=optimization_run_id,
            dataset_ids=dataset_ids,
            improvement=improvement,
            timestamp=timezone.now()
        )
        
        # Update dataset quality scores based on improvement
        self._update_dataset_quality_scores(
            dataset_ids=dataset_ids,
            improvement=improvement
        )
        
        logger.info(
            f"Tracked usage of {len(dataset_ids)} datasets "
            f"for optimization {optimization_run_id} "
            f"with {improvement:.1%} improvement"
        )
    
    def _convert_to_test_case(self, evaluation_case: EvaluationCase) -> Dict[str, Any]:
        """
        Convert an evaluation case to test case format
        
        Args:
            evaluation_case: The evaluation case to convert
            
        Returns:
            Dictionary in test case format
        """
        # Extract parameters from context if available
        parameters = {}
        if hasattr(evaluation_case, 'context') and isinstance(evaluation_case.context, dict):
            parameters = evaluation_case.context.get('parameters', {})
        
        return {
            'input_data': {
                'text': evaluation_case.input_text,
                'context': getattr(evaluation_case, 'context', {})
            },
            'expected_output': evaluation_case.expected_output,
            'parameters': parameters,
            'case_id': evaluation_case.id,
            'is_human_reviewed': evaluation_case.context.get('is_human_reviewed', False) if hasattr(evaluation_case, 'context') else False
        }
    
    # Database interaction methods (to be implemented with actual DB queries)
    
    def _get_datasets_for_prompt_lab(self, prompt_lab_id: str) -> List[EvaluationDataset]:
        """Get all datasets for a prompt lab from database"""
        return list(EvaluationDataset.objects.filter(
            prompt_lab_id=prompt_lab_id,
            case_count__gt=0
        ))
    
    def _get_cases_for_datasets(self, dataset_ids: List[int]) -> List[EvaluationCase]:
        """Get all cases for the specified dataset IDs"""
        return list(EvaluationCase.objects.filter(
            dataset_id__in=dataset_ids
        ))
    
    def _save_dataset_usage(
        self,
        optimization_run_id: str,
        dataset_ids: List[int],
        improvement: float,
        timestamp: datetime
    ) -> None:
        """Save dataset usage record to database"""
        # This would save to a DatasetUsage table (to be created)
        # For now, we'll just log it
        logger.info(
            f"Dataset usage: optimization={optimization_run_id}, "
            f"datasets={dataset_ids}, improvement={improvement:.2%}"
        )
    
    def _update_dataset_quality_scores(
        self,
        dataset_ids: List[int],
        improvement: float
    ) -> None:
        """Update dataset quality scores based on optimization results"""
        # Simple quality score update based on improvement
        # Positive improvement increases score, negative decreases
        score_delta = improvement * 0.1  # 10% of improvement
        
        with transaction.atomic():
            for dataset_id in dataset_ids:
                try:
                    dataset = EvaluationDataset.objects.get(id=dataset_id)
                    if hasattr(dataset, 'quality_score'):
                        current_score = getattr(dataset, 'quality_score', 0.5)
                        new_score = max(0.0, min(1.0, current_score + score_delta))
                        dataset.quality_score = new_score
                        dataset.save()
                except EvaluationDataset.DoesNotExist:
                    logger.warning(f"Dataset {dataset_id} not found for quality score update")