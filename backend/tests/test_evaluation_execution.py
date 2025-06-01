"""Test evaluation execution functionality."""
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from core.models import (
    PromptLab, SystemPrompt, EvaluationDataset, EvaluationCase, 
    EvaluationRun, EvaluationResult
)


class EvaluationExecutionTests(TestCase):
    """Test evaluation execution functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create  and prompt
        self.prompt_lab = PromptLab.objects.create(
            name="Test PromptLab",
            description="Test Description"
        )
        
        self.system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="You are a helpful assistant. Answer the question: {{question}}",
            version=1,
            is_active=True
        )
        
        # Create evaluation dataset
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset",
            description="Test evaluation dataset",
            parameters=["question"]
        )
        
        # Create evaluation cases
        self.cases = []
        for i in range(3):
            case = EvaluationCase.objects.create(
                dataset=self.dataset,
                input_text=f"What is 2 + {i}?",
                expected_output=f"2 + {i} = {2 + i}",
                context={"question": f"What is 2 + {i}?"}
            )
            self.cases.append(case)
    
    def test_create_evaluation_run(self):
        """Test creating an evaluation run."""
        from app.services.evaluation_engine import EvaluationEngine
        from app.services.unified_llm_provider import LLMProviderFactory, LLMConfig
        from app.services.reward_aggregator import RewardFunctionAggregator
        
        # Create LLM provider and reward aggregator
        llm_provider = LLMProviderFactory.create_provider(LLMConfig(
            provider="mock", model="test-model"
        ))
        reward_aggregator = RewardFunctionAggregator(llm_provider)
        
        engine = EvaluationEngine(llm_provider, reward_aggregator)
        run = engine.create_evaluation_run(self.dataset, self.system_prompt)
        
        self.assertIsInstance(run, EvaluationRun)
        self.assertEqual(run.dataset, self.dataset)
        self.assertEqual(run.prompt, self.system_prompt)
        self.assertEqual(run.status, 'pending')
        self.assertIsNone(run.overall_score)
    
    @patch('app.services.unified_llm_provider.LLMProviderFactory')
    def test_execute_evaluation_run(self, mock_provider_factory):
        """Test executing an evaluation run."""
        from app.services.evaluation_engine import EvaluationEngine
        from app.services.reward_aggregator import RewardFunctionAggregator
        
        # Mock LLM provider
        mock_provider = MagicMock()
        mock_provider.generate_text.return_value = "2 + 1 = 3"
        mock_provider_factory.create_provider.return_value = mock_provider
        
        reward_aggregator = RewardFunctionAggregator(mock_provider)
        engine = EvaluationEngine(mock_provider, reward_aggregator)
        run = engine.create_evaluation_run(self.dataset, self.system_prompt)
        
        # Execute the run
        results = engine.execute_evaluation_run(run)
        
        # Verify run was completed
        run.refresh_from_db()
        self.assertEqual(run.status, 'completed')
        self.assertIsNotNone(run.overall_score)
        self.assertIsNotNone(run.completed_at)
        
        # Verify results were created
        self.assertEqual(len(results), 3)
        self.assertEqual(EvaluationResult.objects.filter(run=run).count(), 3)
        
        # Verify LLM was called for each case
        self.assertEqual(mock_provider.generate_text.call_count, 3)
    
    @patch('app.services.unified_llm_provider.LLMProviderFactory')
    def test_evaluation_similarity_scoring(self, mock_provider_factory):
        """Test similarity scoring in evaluation results."""
        from app.services.evaluation_engine import EvaluationEngine
        from app.services.unified_llm_provider import LLMProviderFactory, LLMConfig
        from app.services.reward_aggregator import RewardFunctionAggregator
        
        # Mock LLM provider with different responses
        mock_provider = MagicMock()
        responses = [
            "2 + 0 = 2",    # Exact match
            "The answer is 3",  # Partial match
            "I don't know"  # Poor match
        ]
        mock_provider.generate_text.side_effect = responses
        mock_provider_factory.create_provider.return_value = mock_provider
        
        # Create LLM provider and reward aggregator
        llm_provider = LLMProviderFactory.create_provider(LLMConfig(
            provider="mock", model="test-model"
        ))
        reward_aggregator = RewardFunctionAggregator(llm_provider)
        
        engine = EvaluationEngine(llm_provider, reward_aggregator)
        run = engine.create_evaluation_run(self.dataset, self.system_prompt)
        results = engine.execute_evaluation_run(run)
        
        # Check similarity scores
        results_sorted = sorted(results, key=lambda r: r.case.input_text)
        
        # First result should have highest similarity (exact match)
        self.assertGreater(results_sorted[0].similarity_score, 0.8)
        self.assertTrue(results_sorted[0].passed)
        
        # Third result should have lowest similarity (poor match)
        self.assertLess(results_sorted[2].similarity_score, 0.5)
        self.assertFalse(results_sorted[2].passed)
    
    def test_evaluation_run_failure_handling(self):
        """Test handling of evaluation run failures."""
        from app.services.evaluation_engine import EvaluationEngine
        from app.services.unified_llm_provider import LLMProviderFactory, LLMConfig
        from app.services.reward_aggregator import RewardFunctionAggregator
        
        # Create LLM provider and reward aggregator
        llm_provider = LLMProviderFactory.create_provider(LLMConfig(
            provider="mock", model="test-model"
        ))
        reward_aggregator = RewardFunctionAggregator(llm_provider)
        
        engine = EvaluationEngine(llm_provider, reward_aggregator)
        run = engine.create_evaluation_run(self.dataset, self.system_prompt)
        
        # Simulate failure during execution
        with patch.object(engine, '_generate_response_for_case', side_effect=Exception("LLM error")):
            # The method should complete but create failed results
            results = engine.execute_evaluation_run(run)
        
        # Verify run completed with failed results
        run.refresh_from_db()
        self.assertEqual(run.status, 'completed')  # Should complete but with all failed results
        self.assertIsNotNone(run.completed_at)
        
        # All results should be failed
        for result in results:
            self.assertFalse(result.passed)
            self.assertEqual(result.similarity_score, 0.0)
            self.assertEqual(result.generated_output, "")
    
    def test_compare_prompt_versions(self):
        """Test comparing multiple prompt versions."""
        from app.services.evaluation_engine import EvaluationEngine
        from app.services.unified_llm_provider import LLMProviderFactory, LLMConfig
        from app.services.reward_aggregator import RewardFunctionAggregator
        
        # Create a second prompt version
        prompt_v2 = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="You are an expert math tutor. Solve: {{question}}",
            version=2,
            is_active=False
        )
        
        # Create LLM provider and reward aggregator
        llm_provider = LLMProviderFactory.create_provider(LLMConfig(
            provider="mock", model="test-model"
        ))
        reward_aggregator = RewardFunctionAggregator(llm_provider)
        
        engine = EvaluationEngine(llm_provider, reward_aggregator)
        
        with patch.object(engine, '_generate_response_for_case') as mock_generate:
            # Mock responses for comparison
            mock_generate.side_effect = [
                "2 + 0 = 2", "2 + 1 = 3", "2 + 2 = 4",  # v1 responses
                "2 + 0 equals 2", "2 + 1 equals 3", "2 + 2 equals 4"  # v2 responses
            ]
            
            comparison = engine.compare_prompts(self.dataset, [self.system_prompt, prompt_v2])
            
            self.assertIn('runs', comparison)
            self.assertIn('winner', comparison)
            self.assertIn('improvement', comparison)
            self.assertEqual(len(comparison['runs']), 2)
    
    def test_batch_evaluation_multiple_datasets(self):
        """Test evaluating a prompt against multiple datasets."""
        from app.services.evaluation_engine import EvaluationEngine
        from app.services.unified_llm_provider import LLMProviderFactory, LLMConfig
        from app.services.reward_aggregator import RewardFunctionAggregator
        
        # Create a second dataset
        dataset2 = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Math Dataset 2",
            description="More math problems",
            parameters=["question"]
        )
        
        EvaluationCase.objects.create(
            dataset=dataset2,
            input_text="What is 5 * 3?",
            expected_output="5 * 3 = 15",
            context={"question": "What is 5 * 3?"}
        )
        
        # Create LLM provider and reward aggregator
        llm_provider = LLMProviderFactory.create_provider(LLMConfig(
            provider="mock", model="test-model"
        ))
        reward_aggregator = RewardFunctionAggregator(llm_provider)
        
        engine = EvaluationEngine(llm_provider, reward_aggregator)
        
        with patch.object(engine, '_generate_response_for_case', return_value="Mock response"):
            runs = engine.evaluate_prompt_against_datasets(
                self.system_prompt, 
                [self.dataset, dataset2]
            )
            
            self.assertEqual(len(runs), 2)
            self.assertEqual(runs[0].dataset, self.dataset)
            self.assertEqual(runs[1].dataset, dataset2)


class EvaluationExecutionAPITests(APITestCase):
    """Test evaluation execution API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.prompt_lab = PromptLab.objects.create(
            name="Test PromptLab",
            description="Test Description"
        )
        
        self.system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="Answer: {{question}}",
            version=1,
            is_active=True
        )
        
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset",
            parameters=["question"]
        )
        
        for i in range(2):
            EvaluationCase.objects.create(
                dataset=self.dataset,
                input_text=f"Question {i}?",
                expected_output=f"Answer {i}",
                context={"question": f"Question {i}?"}
            )
    
    def test_trigger_evaluation_run_api(self):
        """Test API endpoint for triggering evaluation runs."""
        url = reverse('evaluation-run-trigger')
        data = {
            'dataset_id': self.dataset.id,
            'prompt_id': self.system_prompt.id
        }
        
        with patch('app.services.evaluation_engine.EvaluationEngine') as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine_class.return_value = mock_engine
            
            # Mock evaluation run
            from core.models import EvaluationRun
            from datetime import datetime
            from django.utils import timezone
            
            mock_run = MagicMock(spec=EvaluationRun)
            mock_run.id = 1
            mock_run.status = 'completed'
            mock_run.overall_score = 0.85
            mock_run.started_at = timezone.now()
            mock_run.completed_at = timezone.now()
            
            mock_engine.create_evaluation_run.return_value = mock_run
            mock_engine.execute_evaluation_run.return_value = []
            
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            data = response.json()
            self.assertEqual(data['run_id'], 1)
            self.assertEqual(data['status'], 'completed')
            self.assertEqual(data['overall_score'], 0.85)
    
    def test_get_evaluation_run_results_api(self):
        """Test API endpoint for getting evaluation run results."""
        # Create a real evaluation run
        run = EvaluationRun.objects.create(
            dataset=self.dataset,
            prompt=self.system_prompt,
            status='completed',
            overall_score=0.9
        )
        
        # Create some results
        case = self.dataset.cases.first()
        result = EvaluationResult.objects.create(
            run=run,
            case=case,
            generated_output="Generated answer",
            similarity_score=0.9,
            passed=True
        )
        
        url = reverse('evaluation-run-results', args=[run.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['run_id'], run.id)
        self.assertEqual(data['overall_score'], 0.9)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['similarity_score'], 0.9)
    
    def test_compare_prompts_api(self):
        """Test API endpoint for comparing multiple prompts."""
        # Create second prompt
        prompt2 = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="Respond to: {{question}}",
            version=2,
            is_active=False
        )
        
        url = reverse('evaluation-compare-prompts')
        data = {
            'dataset_id': self.dataset.id,
            'prompt_ids': [self.system_prompt.id, prompt2.id]
        }
        
        with patch('app.services.evaluation_engine.EvaluationEngine') as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine_class.return_value = mock_engine
            
            mock_comparison = {
                'winner': 'prompt_2',
                'improvement': 15.5,
                'runs': [
                    {'prompt_id': self.system_prompt.id, 'score': 0.75},
                    {'prompt_id': prompt2.id, 'score': 0.87}
                ]
            }
            mock_engine.compare_prompts.return_value = mock_comparison
            
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(data['winner'], 'prompt_2')
            self.assertEqual(data['improvement'], 15.5)
            self.assertEqual(len(data['runs']), 2)