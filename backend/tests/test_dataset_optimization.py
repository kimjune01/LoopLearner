"""
Tests for dataset-based prompt optimization functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List

from app.services.dataset_optimization_service import DatasetOptimizationService
from core.models import (
    EvaluationDataset, EvaluationCase, PromptLab, SystemPrompt
)


class TestDatasetOptimizationService:
    """Test suite for DatasetOptimizationService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = DatasetOptimizationService()
        
        # Create mock prompt lab
        self.prompt_lab = Mock(spec=PromptLab)
        self.prompt_lab.id = "test-prompt-lab-id"
        self.prompt_lab.name = "Test Prompt Lab"
        self.prompt_lab.active_prompt = Mock(spec=SystemPrompt)
        self.prompt_lab.active_prompt.parameters = ["topic", "tone"]
        
        # Create mock datasets
        self.dataset1 = Mock(spec=EvaluationDataset)
        self.dataset1.id = 1
        self.dataset1.name = "High Quality Dataset"
        self.dataset1.prompt_lab_id = self.prompt_lab.id
        self.dataset1.parameters = ["topic", "tone"]
        self.dataset1.case_count = 10
        self.dataset1.quality_score = 0.9
        self.dataset1.human_reviewed_count = 8
        
        self.dataset2 = Mock(spec=EvaluationDataset)
        self.dataset2.id = 2
        self.dataset2.name = "Medium Quality Dataset"
        self.dataset2.prompt_lab_id = self.prompt_lab.id
        self.dataset2.parameters = ["topic"]
        self.dataset2.case_count = 5
        self.dataset2.quality_score = 0.5
        self.dataset2.human_reviewed_count = 2
        
        self.dataset3 = Mock(spec=EvaluationDataset)
        self.dataset3.id = 3
        self.dataset3.name = "Low Quality Dataset"
        self.dataset3.prompt_lab_id = self.prompt_lab.id
        self.dataset3.parameters = ["unrelated_param"]
        self.dataset3.case_count = 3
        self.dataset3.quality_score = 0.3
        self.dataset3.human_reviewed_count = 0
    
    def test_select_datasets_for_optimization_filters_by_parameters(self):
        """Test that dataset selection filters by matching parameters"""
        # Mock database query
        with patch.object(self.service, '_get_datasets_for_prompt_lab') as mock_get:
            mock_get.return_value = [self.dataset1, self.dataset2, self.dataset3]
            
            # Select datasets
            selected = self.service.select_datasets_for_optimization(
                prompt_lab_id=self.prompt_lab.id,
                parameters=["topic", "tone"]
            )
            
            # Should select datasets that have matching parameters
            assert len(selected) == 2
            assert self.dataset1 in selected  # Has both parameters
            assert self.dataset2 in selected  # Has one parameter
            assert self.dataset3 not in selected  # Has unrelated parameter
    
    def test_select_datasets_prioritizes_quality_score(self):
        """Test that datasets are sorted by quality score"""
        with patch.object(self.service, '_get_datasets_for_prompt_lab') as mock_get:
            mock_get.return_value = [self.dataset2, self.dataset1, self.dataset3]
            
            selected = self.service.select_datasets_for_optimization(
                prompt_lab_id=self.prompt_lab.id,
                parameters=["topic"]
            )
            
            # Should be sorted by quality score (descending)
            assert selected[0] == self.dataset1  # quality_score = 0.9
            assert selected[1] == self.dataset2  # quality_score = 0.5
    
    def test_select_datasets_respects_limit(self):
        """Test that dataset selection respects the limit parameter"""
        with patch.object(self.service, '_get_datasets_for_prompt_lab') as mock_get:
            mock_get.return_value = [self.dataset1, self.dataset2]
            
            selected = self.service.select_datasets_for_optimization(
                prompt_lab_id=self.prompt_lab.id,
                parameters=["topic"],
                limit=1
            )
            
            assert len(selected) == 1
            assert selected[0] == self.dataset1  # Highest quality
    
    def test_load_evaluation_cases_from_single_dataset(self):
        """Test loading evaluation cases from a single dataset"""
        # Create mock cases
        case1 = Mock(spec=EvaluationCase)
        case1.id = 1
        case1.dataset_id = 1
        case1.input_text = "AI Safety topic"
        case1.expected_output = "Expected output 1"
        case1.context = {"is_human_reviewed": True}
        
        case2 = Mock(spec=EvaluationCase)
        case2.id = 2
        case2.dataset_id = 1
        case2.input_text = "Climate Change topic"
        case2.expected_output = "Expected output 2"
        case2.context = {"is_human_reviewed": False}
        
        with patch.object(self.service, '_get_cases_for_datasets') as mock_get:
            mock_get.return_value = [case1, case2]
            
            cases = self.service.load_evaluation_cases(dataset_ids=[1])
            
            assert len(cases) == 2
            assert cases[0] == case1  # Human reviewed cases first
            assert cases[1] == case2
    
    def test_load_evaluation_cases_prioritizes_human_reviewed(self):
        """Test that human-reviewed cases are prioritized"""
        # Create mix of human-reviewed and generated cases
        human_case = Mock(spec=EvaluationCase, id=1)
        human_case.context = {"is_human_reviewed": True}
        generated_case = Mock(spec=EvaluationCase, id=2)
        generated_case.context = {"is_human_reviewed": False}
        
        with patch.object(self.service, '_get_cases_for_datasets') as mock_get:
            mock_get.return_value = [generated_case, human_case]
            
            cases = self.service.load_evaluation_cases(dataset_ids=[1])
            
            # Human reviewed should come first
            assert cases[0] == human_case
            assert cases[1] == generated_case
    
    def test_load_evaluation_cases_respects_limit(self):
        """Test that case loading respects the limit parameter"""
        cases = [Mock(spec=EvaluationCase, id=i) for i in range(10)]
        
        with patch.object(self.service, '_get_cases_for_datasets') as mock_get:
            mock_get.return_value = cases
            
            loaded = self.service.load_evaluation_cases(dataset_ids=[1, 2], limit=5)
            
            assert len(loaded) == 5
    
    def test_track_dataset_usage_creates_record(self):
        """Test that dataset usage is properly tracked"""
        optimization_run_id = "opt-run-123"
        dataset_ids = [1, 2]
        results = {
            "improvement": 0.15,
            "best_candidate_id": "prompt-v2",
            "evaluation_metrics": {
                "f1_score": 0.85,
                "perplexity": 12.5
            }
        }
        
        with patch.object(self.service, '_save_dataset_usage') as mock_save:
            with patch.object(self.service, '_update_dataset_quality_scores') as mock_update:
                self.service.track_dataset_usage(
                    optimization_run_id=optimization_run_id,
                    dataset_ids=dataset_ids,
                    results=results
                )
                
                # Verify tracking was called with correct parameters
                mock_save.assert_called_once()
                call_args = mock_save.call_args[1]
                assert call_args['optimization_run_id'] == optimization_run_id
                assert call_args['dataset_ids'] == dataset_ids
                assert call_args['improvement'] == 0.15
                
                # Verify quality scores were updated
                mock_update.assert_called_once_with(
                    dataset_ids=dataset_ids,
                    improvement=0.15
                )
    
    def test_track_dataset_usage_updates_quality_scores(self):
        """Test that dataset quality scores are updated based on optimization results"""
        # High improvement should increase quality scores
        results = {"improvement": 0.25}  # 25% improvement
        
        with patch.object(self.service, '_update_dataset_quality_scores') as mock_update:
            self.service.track_dataset_usage(
                optimization_run_id="opt-123",
                dataset_ids=[1, 2],
                results=results
            )
            
            # Should update quality scores positively
            mock_update.assert_called_once_with(
                dataset_ids=[1, 2],
                improvement=0.25
            )
    
    def test_convert_case_to_test_format(self):
        """Test conversion of evaluation case to test case format"""
        eval_case = Mock(spec=EvaluationCase)
        eval_case.id = 1
        eval_case.input_text = "AI topic with professional tone"
        eval_case.expected_output = "Expected AI response"
        eval_case.context = {
            "parameters": {
                "topic": "AI",
                "tone": "professional"
            },
            "is_human_reviewed": True
        }
        
        test_case = self.service._convert_to_test_case(eval_case)
        
        assert test_case['input_data']['text'] == eval_case.input_text
        assert test_case['expected_output'] == eval_case.expected_output
        assert test_case['parameters'] == {
            "topic": "AI",
            "tone": "professional"
        }
        assert test_case['is_human_reviewed'] is True
        assert test_case['case_id'] == 1
    
    def test_empty_dataset_ids_returns_empty_cases(self):
        """Test that empty dataset IDs returns empty case list"""
        cases = self.service.load_evaluation_cases(dataset_ids=[])
        assert cases == []
    
    def test_no_matching_datasets_returns_empty_list(self):
        """Test that no matching datasets returns empty list"""
        with patch.object(self.service, '_get_datasets_for_prompt_lab') as mock_get:
            mock_get.return_value = []
            
            selected = self.service.select_datasets_for_optimization(
                prompt_lab_id="non-existent",
                parameters=["any"]
            )
            
            assert selected == []