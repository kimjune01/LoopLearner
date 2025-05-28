import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from django.utils import timezone

from app.services.demo_workflow import (
    DemoWorkflowOrchestrator, DemoScenario, DemoStep, DemoResults, run_quick_demo
)
from app.services.unified_llm_provider import LLMConfig, LLMProviderFactory
from core.models import SystemPrompt, Email, Draft, UserFeedback, OptimizationRun


@pytest.fixture
def mock_llm_config():
    return LLMConfig(
        provider="mock",
        model="demo-model",
        api_key="demo-key"
    )


@pytest.fixture
def demo_orchestrator(mock_llm_config):
    return DemoWorkflowOrchestrator(mock_llm_config)


@pytest.fixture
def mock_scenario():
    return DemoScenario(
        name="Test Scenario",
        description="Test description",
        email_scenarios=["professional", "casual"],
        feedback_patterns=[
            {"action": "reject", "reasoning": "Too informal", "factors": {"tone": 2}},
            {"action": "accept", "reasoning": "Perfect", "factors": {"tone": 5}},
        ],
        expected_improvement=10.0,
        learning_objectives=["Improve tone", "Enhance clarity"]
    )


class TestDemoScenario:
    def test_demo_scenario_creation(self, mock_scenario):
        assert mock_scenario.name == "Test Scenario"
        assert len(mock_scenario.email_scenarios) == 2
        assert len(mock_scenario.feedback_patterns) == 2
        assert mock_scenario.expected_improvement == 10.0
        assert len(mock_scenario.learning_objectives) == 2


class TestDemoWorkflowOrchestrator:
    def test_orchestrator_initialization(self, demo_orchestrator):
        assert demo_orchestrator.llm_provider is not None
        assert demo_orchestrator.email_generator is not None
        assert len(demo_orchestrator.demo_scenarios) == 3  # Default scenarios
        assert demo_orchestrator.demo_trigger_config.min_feedback_count == 5  # Demo-specific config

    def test_demo_scenarios_creation(self, demo_orchestrator):
        scenarios = demo_orchestrator.demo_scenarios
        
        # Check we have the expected scenarios
        scenario_names = [s.name for s in scenarios]
        assert "Professional Email Optimization" in scenario_names
        assert "Customer Service Excellence" in scenario_names
        assert "Technical Communication" in scenario_names
        
        # Check scenario structure
        for scenario in scenarios:
            assert isinstance(scenario, DemoScenario)
            assert scenario.name
            assert scenario.description
            assert len(scenario.email_scenarios) > 0
            assert len(scenario.feedback_patterns) > 0
            assert scenario.expected_improvement > 0
            assert len(scenario.learning_objectives) > 0

    @pytest.mark.asyncio
    async def test_initialize_demo_system(self, demo_orchestrator):
        with patch('app.services.demo_workflow.sync_to_async') as mock_sync:
            mock_save = AsyncMock()
            mock_sync.return_value = mock_save
            
            with patch('app.services.demo_workflow.SystemPrompt') as mock_prompt_class:
                mock_prompt = MagicMock()
                mock_prompt_class.return_value = mock_prompt
                
                await demo_orchestrator._initialize_demo_system()
                
                # Verify prompt creation
                mock_prompt_class.assert_called_once()
                mock_save.assert_called()
                
                # Verify orchestrator initialization
                assert demo_orchestrator.orchestrator is not None

    @pytest.mark.asyncio
    async def test_process_demo_emails(self, demo_orchestrator, mock_scenario):
        with patch('app.services.demo_workflow.sync_to_async') as mock_sync:
            mock_save = AsyncMock()
            mock_sync.side_effect = [
                mock_save,  # email.save()
                AsyncMock(return_value=MagicMock()),  # get active prompt
                mock_save,  # draft.save()
                mock_save,  # feedback.save()
            ] * 8  # 4 emails per scenario type (2 types)
            
            # Mock LLM provider
            demo_orchestrator.llm_provider.generate = AsyncMock(return_value="Test response")
            
            # Mock Django models
            with patch('app.services.demo_workflow.Email') as mock_email_class:
                with patch('app.services.demo_workflow.Draft') as mock_draft_class:
                    with patch('app.services.demo_workflow.UserFeedback') as mock_feedback_class:
                        
                        # Mock email generator to return real-looking email
                        mock_email = MagicMock()
                        mock_email.subject = 'Test Subject'
                        mock_email.body = 'Test Body'
                        mock_email.sender = 'test@example.com'
                        demo_orchestrator.email_generator.generate_synthetic_email = AsyncMock(
                            return_value=mock_email
                        )
                        
                        emails_processed, feedback_collected = await demo_orchestrator._process_demo_emails(mock_scenario)
                        
                        assert emails_processed == 8  # 4 emails per scenario type * 2 types
                        assert feedback_collected == 8

    @pytest.mark.asyncio
    async def test_trigger_demo_optimization(self, demo_orchestrator):
        # Mock orchestrator
        demo_orchestrator.orchestrator = MagicMock()
        
        # Mock optimization result
        mock_result = MagicMock()
        mock_result.deployed = True
        mock_result.improvement_percentage = 15.0
        mock_result.baseline_prompt = MagicMock()
        mock_result.feedback_batch_size = 10
        
        demo_orchestrator.orchestrator.force_optimization = AsyncMock(return_value=mock_result)
        
        with patch('app.services.demo_workflow.sync_to_async') as mock_sync:
            mock_save = AsyncMock()
            mock_sync.side_effect = [
                AsyncMock(return_value=MagicMock()),  # get active prompt
                mock_save,  # save optimization run
            ] * 3  # max_attempts
            
            optimizations_count = await demo_orchestrator._trigger_demo_optimization()
            
            assert optimizations_count == 3  # All attempts successful

    @pytest.mark.asyncio
    async def test_evaluate_demo_results(self, demo_orchestrator, mock_scenario):
        # Mock prompt evolution
        mock_prompts = [
            MagicMock(version=1, performance_score=0.6),
            MagicMock(version=2, performance_score=0.7),
            MagicMock(version=3, performance_score=0.8),
        ]
        
        async def mock_aiter(self):
            for prompt in mock_prompts:
                yield prompt
        
        with patch('app.services.demo_workflow.SystemPrompt.objects.all') as mock_query:
            mock_queryset = MagicMock()
            mock_queryset.order_by.return_value = mock_queryset
            mock_queryset.__aiter__ = mock_aiter
            mock_query.return_value = mock_queryset
            
            improvement, objectives_met = await demo_orchestrator._evaluate_demo_results(mock_scenario)
            
            # Should show improvement from 0.6 to 0.8 = 33.3%
            assert improvement > 30
            assert len(objectives_met) > 0

    @pytest.mark.asyncio
    async def test_generate_demo_metrics(self, demo_orchestrator):
        with patch('app.services.demo_workflow.Email.objects.filter') as mock_email_filter:
            mock_email_query = MagicMock()
            mock_email_query.acount = AsyncMock(return_value=10)
            mock_email_filter.return_value = mock_email_query
            
            with patch('app.services.demo_workflow.Draft.objects.acount', new_callable=AsyncMock, return_value=15):
                with patch('app.services.demo_workflow.UserFeedback.objects.acount', new_callable=AsyncMock, return_value=12):
                    with patch('app.services.demo_workflow.OptimizationRun.objects.acount', new_callable=AsyncMock, return_value=3):
                        # Mock prompt evolution
                        mock_prompts = [MagicMock(version=1, performance_score=0.6, is_active=False, created_at=timezone.now())]
                        
                        async def mock_prompt_aiter(self):
                            for prompt in mock_prompts:
                                yield prompt
                        
                        with patch('app.services.demo_workflow.SystemPrompt.objects.all') as mock_prompt_query:
                            mock_prompt_queryset = MagicMock()
                            mock_prompt_queryset.order_by.return_value = mock_prompt_queryset
                            mock_prompt_queryset.__aiter__ = mock_prompt_aiter
                            mock_prompt_query.return_value = mock_prompt_queryset
                            
                            # Mock feedback iteration
                            mock_feedback = [MagicMock(action='accept'), MagicMock(action='reject')]
                            
                            async def mock_feedback_aiter(self):
                                for feedback in mock_feedback:
                                    yield feedback
                            
                            with patch('app.services.demo_workflow.UserFeedback.objects.all') as mock_feedback_query:
                                mock_feedback_queryset = MagicMock()
                                mock_feedback_queryset.__aiter__ = mock_feedback_aiter
                                mock_feedback_query.return_value = mock_feedback_queryset
                                
                                metrics = await demo_orchestrator._generate_demo_metrics()
                                
                                assert 'total_emails' in metrics
                                assert 'total_drafts' in metrics
                                assert 'total_feedback' in metrics
                                assert 'total_optimizations' in metrics
                                assert 'prompt_evolution' in metrics
                                assert 'feedback_distribution' in metrics
                                assert 'system_health' in metrics

    @pytest.mark.asyncio
    async def test_run_guided_demo_steps(self, demo_orchestrator):
        steps = await demo_orchestrator.run_guided_demo_steps("Professional Email Optimization")
        
        assert len(steps) == 5  # Expected number of demo steps
        
        for i, step in enumerate(steps):
            assert isinstance(step, DemoStep)
            assert step.step_number == i + 1
            assert step.title
            assert step.description
            assert step.action_type in ['generate', 'feedback', 'optimize', 'evaluate']
            assert step.expected_duration > 0
            assert isinstance(step.success_criteria, dict)

    @pytest.mark.asyncio
    async def test_create_demo_report(self, demo_orchestrator):
        # Create mock demo results
        mock_results = DemoResults(
            scenario_name="Test Scenario",
            total_emails_processed=10,
            total_feedback_collected=8,
            optimizations_triggered=2,
            final_performance_improvement=15.5,
            learning_objectives_met=["Objective 1", "Objective 2"],
            execution_time=timedelta(minutes=2),
            detailed_metrics={'test': 'metrics'}
        )
        
        report = await demo_orchestrator.create_demo_report(mock_results)
        
        assert 'executive_summary' in report
        assert 'learning_metrics' in report
        assert 'system_performance' in report
        assert 'demonstration_highlights' in report
        assert 'next_steps' in report
        
        # Check executive summary
        assert report['executive_summary']['scenario'] == "Test Scenario"
        assert report['executive_summary']['total_improvement'] == "15.5%"
        assert 'Success' in report['executive_summary']['success_status']
        
        # Check learning metrics
        assert report['learning_metrics']['emails_processed'] == 10
        assert report['learning_metrics']['feedback_collected'] == 8
        assert report['learning_metrics']['optimizations_triggered'] == 2
        
        # Check highlights and next steps
        assert len(report['demonstration_highlights']) > 0
        assert len(report['next_steps']) > 0

    @pytest.mark.asyncio
    async def test_run_complete_demo_integration(self, demo_orchestrator):
        # Mock all the sub-methods
        with patch.object(demo_orchestrator, '_initialize_demo_system') as mock_init:
            with patch.object(demo_orchestrator, '_process_demo_emails') as mock_process:
                with patch.object(demo_orchestrator, '_trigger_demo_optimization') as mock_trigger:
                    with patch.object(demo_orchestrator, '_evaluate_demo_results') as mock_evaluate:
                        with patch.object(demo_orchestrator, '_generate_demo_metrics') as mock_metrics:
                            
                            # Setup return values
                            mock_init.return_value = None
                            mock_process.return_value = (10, 8)
                            mock_trigger.return_value = 2
                            mock_evaluate.return_value = (15.5, ["Objective 1"])
                            mock_metrics.return_value = {'test': 'metrics'}
                            
                            results = await demo_orchestrator.run_complete_demo()
                            
                            # Verify all methods were called
                            mock_init.assert_called_once()
                            mock_process.assert_called_once()
                            mock_trigger.assert_called_once()
                            mock_evaluate.assert_called_once()
                            mock_metrics.assert_called_once()
                            
                            # Check results
                            assert isinstance(results, DemoResults)
                            assert results.total_emails_processed == 10
                            assert results.total_feedback_collected == 8
                            assert results.optimizations_triggered == 2
                            assert results.final_performance_improvement == 15.5


class TestQuickDemo:
    @pytest.mark.asyncio
    async def test_run_quick_demo_success(self, mock_llm_config):
        with patch('app.services.demo_workflow.DemoWorkflowOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = MagicMock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Mock demo results
            mock_results = MagicMock()
            mock_results.scenario_name = "Test"
            mock_results.final_performance_improvement = 10.0
            
            mock_report = {'executive_summary': {'success_status': 'Success'}}
            
            mock_orchestrator.run_complete_demo = AsyncMock(return_value=mock_results)
            mock_orchestrator.create_demo_report = AsyncMock(return_value=mock_report)
            
            result = await run_quick_demo(mock_llm_config)
            
            assert result['success'] is True
            assert 'demo_results' in result
            assert 'demo_report' in result
            assert result['message'] == 'Complete demonstration workflow executed successfully'

    @pytest.mark.asyncio
    async def test_run_quick_demo_failure(self, mock_llm_config):
        with patch('app.services.demo_workflow.DemoWorkflowOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = MagicMock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Mock failure
            mock_orchestrator.run_complete_demo = AsyncMock(side_effect=Exception("Demo failed"))
            
            result = await run_quick_demo(mock_llm_config)
            
            assert result['success'] is False
            assert 'error' in result
            assert result['message'] == 'Demo workflow encountered an error'

    @pytest.mark.asyncio
    async def test_run_quick_demo_default_config(self):
        with patch('app.services.demo_workflow.DemoWorkflowOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = MagicMock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            mock_results = MagicMock()
            mock_report = {}
            
            mock_orchestrator.run_complete_demo = AsyncMock(return_value=mock_results)
            mock_orchestrator.create_demo_report = AsyncMock(return_value=mock_report)
            
            result = await run_quick_demo()  # No config provided
            
            # Should use default mock config
            mock_orchestrator_class.assert_called_once()
            call_args = mock_orchestrator_class.call_args[0][0]
            assert call_args.provider == "mock"
            assert call_args.model == "demo-model"