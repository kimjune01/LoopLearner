"""
Integration tests for dataset-based optimization triggering
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import asyncio

from app.services.optimization_orchestrator import OptimizationOrchestrator
from app.services.dataset_optimization_service import DatasetOptimizationService
from core.models import (
    PromptLab, SystemPrompt, EvaluationDataset, EvaluationCase
)


class TestOptimizationOrchestratorDatasetIntegration:
    """Test OptimizationOrchestrator with dataset-based optimization"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create mock prompt lab
        self.prompt_lab = Mock(spec=PromptLab)
        self.prompt_lab.id = "test-lab-id"
        self.prompt_lab.name = "Test Lab"
        
        # Create mock active prompt
        self.active_prompt = Mock(spec=SystemPrompt)
        self.active_prompt.id = 1
        self.active_prompt.content = "You are a helpful assistant with {{tone}} tone."
        self.active_prompt.parameters = ["tone"]
        self.active_prompt.version = 1
        self.prompt_lab.active_prompt = self.active_prompt
        
        # Create mock dependencies
        mock_llm_provider = Mock()
        mock_prompt_rewriter = Mock()
        mock_evaluation_engine = AsyncMock()
        
        # Create orchestrator with mocked dependencies
        self.orchestrator = OptimizationOrchestrator(
            llm_provider=mock_llm_provider,
            prompt_rewriter=mock_prompt_rewriter,
            evaluation_engine=mock_evaluation_engine
        )
        
        # Add additional mocks
        self.orchestrator.convergence_detector = Mock()
        self.orchestrator.config = Mock()
        self.orchestrator.config.deployment_threshold = 0.1
        self.orchestrator.config.evaluation = Mock()
    
    @pytest.mark.asyncio
    async def test_trigger_optimization_with_datasets_basic_flow(self):
        """Test basic flow of triggering optimization with specific datasets"""
        dataset_ids = [1, 2]
        
        # Mock convergence check
        convergence_result = Mock()
        convergence_result.has_converged = False
        self.orchestrator.convergence_detector.check_convergence = AsyncMock(
            return_value=convergence_result
        )
        
        # Mock Django ORM for prompt lab loading
        self.prompt_lab.prompts = Mock()
        self.prompt_lab.prompts.filter.return_value.first.return_value = self.active_prompt
        
        mock_get = AsyncMock(return_value=self.prompt_lab)
        mock_prompts_query = AsyncMock(return_value=self.active_prompt)
        
        with patch('app.services.optimization_orchestrator.sync_to_async') as mock_sync:
            # Configure sync_to_async to return our mocked functions
            def mock_sync_to_async(func):
                if 'get' in str(func):
                    return mock_get
                else:
                    return mock_prompts_query
            mock_sync.side_effect = mock_sync_to_async
            
            # Mock convergence detector import
            with patch('app.services.optimization_orchestrator.ConvergenceDetector') as mock_conv_class:
                mock_conv_class.return_value = self.orchestrator.convergence_detector
                
                # Mock dataset service
                with patch('app.services.dataset_optimization_service.DatasetOptimizationService') as mock_service_class:
                    mock_service = Mock()
                    mock_service_class.return_value = mock_service
                    
                    # Mock test cases
                test_cases = [
                    {"id": 1, "input_text": "Test 1", "expected_output": "Output 1"},
                    {"id": 2, "input_text": "Test 2", "expected_output": "Output 2"}
                ]
                mock_service.load_evaluation_cases.return_value = test_cases
                mock_service.track_dataset_usage = Mock()
                
                # No need to mock context building since we build it inline
                
                # Mock candidate generation
                candidate_prompts = [Mock(id=2, content="Improved prompt", version=2)]
                self.orchestrator.prompt_rewriter.generate_candidates = AsyncMock(
                    return_value=candidate_prompts
                )
                
                # Mock evaluation result
                best_candidate = Mock()
                best_candidate.improvement = 0.15
                best_candidate.prompt = candidate_prompts[0]
                evaluation_result = Mock()
                evaluation_result.best_candidate = best_candidate
                evaluation_result.id = "eval-123"
                evaluation_result.to_dict = Mock(return_value={"improvement": 0.15})
                self.orchestrator.evaluation_engine.compare_prompt_candidates.return_value = evaluation_result
                
                # Mock deployment
                with patch.object(self.orchestrator, '_deploy_new_prompt', new=AsyncMock()):
                    # Execute
                    result = await self.orchestrator.trigger_optimization_with_datasets(
                        prompt_lab_id=self.prompt_lab.id,
                        dataset_ids=dataset_ids,
                        force=False
                    )
                    
                    # Verify dataset loading
                    mock_service.load_evaluation_cases.assert_called_once_with(dataset_ids)
                    
                    # Verify context includes dataset info
                    context_call = self.orchestrator.prompt_rewriter.generate_candidates.call_args[1]['context']
                    assert context_call['dataset_ids'] == dataset_ids
                    assert context_call['manual_trigger'] is True
                    
                    # Verify evaluation called with datasets
                    eval_call = self.orchestrator.evaluation_engine.compare_prompt_candidates.call_args
                    assert eval_call[1]['dataset_ids'] == dataset_ids
                    
                    # Verify deployment was called (improvement > threshold)
                    self.orchestrator._deploy_new_prompt.assert_called_once()
                    
                    # Verify dataset usage tracking
                    mock_service.track_dataset_usage.assert_called_once()
                    
                    # Verify result
                    assert result == evaluation_result
    
    @pytest.mark.asyncio
    async def test_trigger_optimization_respects_convergence(self):
        """Test that optimization respects convergence unless forced"""
        # Mock convergence check - has converged
        convergence_result = Mock()
        convergence_result.has_converged = True
        self.orchestrator.convergence_detector.check_convergence = AsyncMock(
            return_value=convergence_result
        )
        
        with patch.object(self.orchestrator, '_get_prompt_lab', new=AsyncMock(return_value=self.prompt_lab)):
            # Should raise error when not forced
            with pytest.raises(ValueError, match="Prompt has converged"):
                await self.orchestrator.trigger_optimization_with_datasets(
                    prompt_lab_id=self.prompt_lab.id,
                    dataset_ids=[1],
                    force=False
                )
    
    @pytest.mark.asyncio
    async def test_trigger_optimization_force_ignores_convergence(self):
        """Test that force=True ignores convergence"""
        # Mock convergence check - has converged
        convergence_result = Mock()
        convergence_result.has_converged = True
        self.orchestrator.convergence_detector.check_convergence = AsyncMock(
            return_value=convergence_result
        )
        
        with patch.object(self.orchestrator, '_get_prompt_lab', new=AsyncMock(return_value=self.prompt_lab)):
            with patch('app.services.optimization_orchestrator.DatasetOptimizationService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service
                mock_service.load_evaluation_cases.return_value = [{"id": 1}]
                
                # Set up other mocks
                with patch.object(self.orchestrator, '_build_optimization_context', new=AsyncMock(return_value={})):
                    self.orchestrator.prompt_rewriter.generate_candidates = AsyncMock(return_value=[Mock()])
                    evaluation_result = Mock()
                    evaluation_result.best_candidate = Mock(improvement=0.05)  # Below threshold
                    evaluation_result.id = "eval-456"
                    evaluation_result.to_dict = Mock(return_value={})
                    self.orchestrator.evaluation_engine.compare_prompt_candidates.return_value = evaluation_result
                    
                    # Should not raise error with force=True
                    result = await self.orchestrator.trigger_optimization_with_datasets(
                        prompt_lab_id=self.prompt_lab.id,
                        dataset_ids=[1],
                        force=True
                    )
                    
                    assert result == evaluation_result
    
    @pytest.mark.asyncio
    async def test_trigger_optimization_no_cases_raises_error(self):
        """Test that optimization fails if no cases found in datasets"""
        with patch.object(self.orchestrator, '_get_prompt_lab', new=AsyncMock(return_value=self.prompt_lab)):
            with patch('app.services.optimization_orchestrator.DatasetOptimizationService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service
                # No cases returned
                mock_service.load_evaluation_cases.return_value = []
                
                with pytest.raises(ValueError, match="No evaluation cases found"):
                    await self.orchestrator.trigger_optimization_with_datasets(
                        prompt_lab_id=self.prompt_lab.id,
                        dataset_ids=[1],
                        force=True
                    )
    
    @pytest.mark.asyncio
    async def test_trigger_optimization_no_deployment_if_below_threshold(self):
        """Test that prompt is not deployed if improvement is below threshold"""
        with patch.object(self.orchestrator, '_get_prompt_lab', new=AsyncMock(return_value=self.prompt_lab)):
            with patch('app.services.optimization_orchestrator.DatasetOptimizationService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service
                mock_service.load_evaluation_cases.return_value = [{"id": 1}]
                mock_service.track_dataset_usage = Mock()
                
                with patch.object(self.orchestrator, '_build_optimization_context', new=AsyncMock(return_value={})):
                    self.orchestrator.prompt_rewriter.generate_candidates = AsyncMock(return_value=[Mock()])
                    
                    # Low improvement
                    evaluation_result = Mock()
                    evaluation_result.best_candidate = Mock(improvement=0.05)  # Below 0.1 threshold
                    evaluation_result.id = "eval-789"
                    evaluation_result.to_dict = Mock(return_value={})
                    self.orchestrator.evaluation_engine.compare_prompt_candidates.return_value = evaluation_result
                    
                    with patch.object(self.orchestrator, '_deploy_prompt', new=AsyncMock()) as mock_deploy:
                        result = await self.orchestrator.trigger_optimization_with_datasets(
                            prompt_lab_id=self.prompt_lab.id,
                            dataset_ids=[1],
                            force=True
                        )
                        
                        # Should not deploy
                        mock_deploy.assert_not_called()
                        
                        # Should still track usage
                        mock_service.track_dataset_usage.assert_called_once()