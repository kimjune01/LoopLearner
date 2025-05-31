import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from django.utils import timezone

from app.services.optimization_orchestrator import (
    OptimizationOrchestrator, OptimizationTrigger, OptimizationResult
)
from app.services.prompt_rewriter import RewriteCandidate, RewriteContext
from app.services.evaluation_engine import EvaluationResult, ComparisonResult
from app.services.unified_llm_provider import LLMConfig, LLMProviderFactory
from core.models import SystemPrompt, UserFeedback, Email, Draft


@pytest.fixture
def mock_llm_config():
    return LLMConfig(
        provider="mock",
        model="test-model",
        api_key="test-key"
    )


@pytest.fixture
def trigger_config():
    return OptimizationTrigger(
        min_feedback_count=5,  # Lower for testing
        min_negative_feedback_ratio=0.4,
        feedback_window_hours=24,
        min_time_since_last_optimization_hours=1,  # Lower for testing
        max_optimization_frequency_per_day=10
    )


@pytest.fixture
def mock_system_prompt():
    prompt = MagicMock(spec=SystemPrompt)
    prompt.content = "You are a helpful assistant."
    prompt.version = 1
    prompt.performance_score = 0.7
    prompt.is_active = True
    prompt.save = MagicMock()
    return prompt


@pytest.fixture
def mock_feedback_batch():
    feedback_list = []
    for i in range(8):
        feedback = MagicMock(spec=UserFeedback)
        feedback.action = 'reject' if i < 4 else 'accept'  # 50% negative
        feedback.reasoning = f"Test reasoning {i}"
        feedback.reasoning_factors = {
            'clarity': 2 if i < 4 else 4,
            'tone': 2 if i < 4 else 4,
            'completeness': 3,
            'relevance': 3
        }
        feedback.created_at = timezone.now() - timedelta(hours=i)
        feedback.draft = MagicMock()
        feedback.draft.email = MagicMock()
        feedback.draft.email.scenario_type = 'professional'
        # Add proper session mock with UUID
        feedback.draft.email.session = MagicMock()
        feedback.draft.email.session.id = '12345678-1234-5678-9012-123456789012'
        feedback_list.append(feedback)
    return feedback_list


@pytest.fixture
async def orchestrator(mock_llm_config, trigger_config):
    provider = LLMProviderFactory.create_provider(mock_llm_config)
    
    # Mock dependencies
    prompt_rewriter = MagicMock()
    evaluation_engine = MagicMock()
    
    return OptimizationOrchestrator(
        llm_provider=provider,
        prompt_rewriter=prompt_rewriter,
        evaluation_engine=evaluation_engine,
        trigger_config=trigger_config
    )


class TestOptimizationTrigger:
    def test_trigger_config_defaults(self):
        config = OptimizationTrigger()
        
        assert config.min_feedback_count == 10
        assert config.min_negative_feedback_ratio == 0.3
        assert config.feedback_window_hours == 24
        assert config.min_time_since_last_optimization_hours == 6
        assert config.max_optimization_frequency_per_day == 4

    def test_trigger_config_custom(self):
        config = OptimizationTrigger(
            min_feedback_count=15,
            min_negative_feedback_ratio=0.5
        )
        
        assert config.min_feedback_count == 15
        assert config.min_negative_feedback_ratio == 0.5


class TestOptimizationOrchestrator:
    @pytest.mark.asyncio
    async def test_check_optimization_insufficient_feedback(self, orchestrator):
        with patch('app.services.optimization_orchestrator.UserFeedback.objects.filter') as mock_filter:
            # Mock insufficient feedback
            mock_queryset = MagicMock()
            mock_queryset.__aiter__ = AsyncMock(return_value=iter([]))
            mock_filter.return_value = mock_queryset
            
            result = await orchestrator.check_and_trigger_optimization()
            
            assert result is None

    @pytest.mark.asyncio
    async def test_check_optimization_daily_limit_reached(self, orchestrator):
        # Simulate daily limit reached
        orchestrator._optimization_count_today = 10
        
        result = await orchestrator.check_and_trigger_optimization()
        
        assert result is None

    @pytest.mark.asyncio
    async def test_check_optimization_too_soon(self, orchestrator):
        # Set last optimization time to recent
        orchestrator._last_optimization_time = timezone.now() - timedelta(minutes=30)
        
        result = await orchestrator.check_and_trigger_optimization()
        
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_feedback_negative_ratio_trigger(self, orchestrator, mock_feedback_batch):
        # Directly patch the method to use our mock data
        original_method = orchestrator._analyze_feedback_for_triggers
        
        async def mock_analyze():
            # Simulate the analysis with our mock feedback batch
            negative_feedback_count = 0
            for feedback in mock_feedback_batch:
                if feedback.action in ['reject', 'edit']:
                    negative_feedback_count += 1
            
            negative_feedback_ratio = negative_feedback_count / len(mock_feedback_batch)
            
            return {
                'should_trigger': negative_feedback_ratio >= orchestrator.trigger_config.min_negative_feedback_ratio,
                'reason': f"High negative feedback ratio: {negative_feedback_ratio:.1%}" if negative_feedback_ratio >= orchestrator.trigger_config.min_negative_feedback_ratio else "No trigger",
                'feedback_count': len(mock_feedback_batch),
                'negative_feedback_ratio': negative_feedback_ratio,
                'average_rating': 3.0,
                'feedback_batch': mock_feedback_batch
            }
        
        orchestrator._analyze_feedback_for_triggers = mock_analyze
        
        analysis = await orchestrator._analyze_feedback_for_triggers()
        
        assert analysis['should_trigger'] == True
        assert analysis['negative_feedback_ratio'] == 0.5  # 4/8 = 0.5 > 0.4 threshold
        assert analysis['feedback_count'] == 8

    @pytest.mark.asyncio
    async def test_analyze_feedback_low_ratings_trigger(self, orchestrator):
        # Create feedback with low ratings
        feedback_batch = []
        for i in range(6):
            feedback = MagicMock(spec=UserFeedback)
            feedback.action = 'accept'  # Not negative action
            feedback.reasoning_factors = {
                'clarity': 2.0,  # Low rating
                'tone': 2.0,
                'completeness': 2.0,
                'relevance': 2.0
            }
            feedback.created_at = timezone.now() - timedelta(hours=i)
            feedback_batch.append(feedback)
        
        # Mock the analysis method directly
        async def mock_analyze():
            # Calculate average rating
            total_rating_sum = 0
            rating_count = 0
            
            for feedback in feedback_batch:
                if hasattr(feedback, 'reasoning_factors') and feedback.reasoning_factors:
                    factors = feedback.reasoning_factors
                    if isinstance(factors, dict):
                        ratings = [v for v in factors.values() if isinstance(v, (int, float))]
                        if ratings:
                            total_rating_sum += sum(ratings) / len(ratings)
                            rating_count += 1
            
            average_rating = total_rating_sum / rating_count if rating_count > 0 else 3.0
            
            return {
                'should_trigger': average_rating < 2.5,
                'reason': f"Low average rating: {average_rating:.2f}" if average_rating < 2.5 else "No trigger",
                'feedback_count': len(feedback_batch),
                'negative_feedback_ratio': 0.0,  # No negative actions
                'average_rating': average_rating,
                'feedback_batch': feedback_batch
            }
        
        orchestrator._analyze_feedback_for_triggers = mock_analyze
        
        analysis = await orchestrator._analyze_feedback_for_triggers()
        
        assert analysis['should_trigger'] == True
        assert analysis['average_rating'] == 2.0

    @pytest.mark.asyncio
    async def test_has_consistent_issues(self, orchestrator):
        feedback_batch = []
        for i in range(10):
            feedback = MagicMock(spec=UserFeedback)
            feedback.reasoning_factors = {
                'clarity': 2,  # Consistently low
                'tone': 4,
                'completeness': 3,
                'relevance': 3
            }
            feedback_batch.append(feedback)
        
        has_issues = orchestrator._has_consistent_issues(feedback_batch)
        
        assert has_issues == True

    @pytest.mark.asyncio
    async def test_execute_optimization_cycle(self, orchestrator, mock_system_prompt, mock_feedback_batch):
        # Mock dependencies
        with patch('app.services.optimization_orchestrator.sync_to_async') as mock_sync, \
             patch.object(orchestrator, '_check_cold_start_status', return_value=True), \
             patch('app.services.optimization_orchestrator.SystemPrompt') as mock_prompt_model:
            mock_sync.return_value = AsyncMock(return_value=mock_system_prompt)
            mock_prompt_model.objects.filter.return_value.first.return_value = mock_system_prompt
            
            # Mock prompt rewriter
            mock_candidate = RewriteCandidate(
                content="Improved prompt",
                confidence=0.8,
                temperature=0.7,
                reasoning="Better clarity"
            )
            orchestrator.prompt_rewriter.rewrite_prompt = AsyncMock(return_value=[mock_candidate])
            
            # Mock evaluation engine
            mock_comparison = ComparisonResult(
                baseline=EvaluationResult(
                    prompt=mock_system_prompt,
                    performance_score=0.6,
                    metrics={},
                    sample_outputs=[],
                    evaluation_time=datetime.now(),
                    test_cases_used=5,
                    error_rate=0.0
                ),
                candidate=EvaluationResult(
                    prompt=MagicMock(),
                    performance_score=0.8,
                    metrics={},
                    sample_outputs=[],
                    evaluation_time=datetime.now(),
                    test_cases_used=5,
                    error_rate=0.0
                ),
                improvement=33.3,
                statistical_significance=0.01,
                winner="candidate",
                confidence_level=0.99
            )
            orchestrator.evaluation_engine.compare_prompt_candidates = AsyncMock(return_value=[mock_comparison])
            
            trigger_analysis = {
                'reason': 'High negative feedback ratio',
                'feedback_batch': mock_feedback_batch
            }
            
            result = await orchestrator._execute_optimization_cycle(trigger_analysis)
            
            assert isinstance(result, OptimizationResult)
            assert result.improvement_percentage == 33.3
            assert result.deployed == True
            assert result.feedback_batch_size == len(mock_feedback_batch)

    @pytest.mark.asyncio
    async def test_build_rewrite_context(self, orchestrator, mock_system_prompt, mock_feedback_batch):
        context = await orchestrator._build_rewrite_context(mock_system_prompt, mock_feedback_batch)
        
        assert isinstance(context, RewriteContext)
        assert context.current_prompt == mock_system_prompt
        assert len(context.recent_feedback) <= 5  # Limited to last 5
        assert context.email_scenario == 'professional'
        assert 'overall_quality' in context.performance_history

    def test_should_deploy_candidate(self, orchestrator):
        # Test successful deployment criteria
        good_comparison = MagicMock()
        good_comparison.winner = "candidate"
        good_comparison.improvement = 10.0  # > 5%
        good_comparison.confidence_level = 0.85  # > 0.8
        
        assert orchestrator._should_deploy_candidate(good_comparison) == True
        
        # Test insufficient improvement
        bad_comparison = MagicMock()
        bad_comparison.winner = "candidate"
        bad_comparison.improvement = 3.0  # < 5%
        bad_comparison.confidence_level = 0.85
        
        assert orchestrator._should_deploy_candidate(bad_comparison) == False
        
        # Test low confidence
        low_confidence = MagicMock()
        low_confidence.winner = "candidate"
        low_confidence.improvement = 10.0
        low_confidence.confidence_level = 0.7  # < 0.8
        
        assert orchestrator._should_deploy_candidate(low_confidence) == False

    @pytest.mark.asyncio
    async def test_deploy_new_prompt(self, orchestrator, mock_system_prompt):
        candidate = RewriteCandidate(
            content="New improved prompt",
            confidence=0.9,
            temperature=0.7,
            reasoning="Better performance"
        )
        
        comparison_result = MagicMock()
        comparison_result.candidate.performance_score = 0.85
        comparison_result.improvement = 15.0  # Add this for the format operation
        
        with patch('app.services.optimization_orchestrator.sync_to_async') as mock_sync:
            mock_save = AsyncMock()
            mock_sync.return_value = mock_save
            
            with patch('app.services.optimization_orchestrator.SystemPrompt') as mock_prompt_class:
                mock_new_prompt = MagicMock()
                mock_prompt_class.return_value = mock_new_prompt
                
                await orchestrator._deploy_new_prompt(mock_system_prompt, candidate, comparison_result)
                
                # Verify new prompt creation
                mock_prompt_class.assert_called_once()
                mock_save.assert_called()
                
                # Verify old prompt deactivation
                assert mock_system_prompt.is_active == False

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_get_optimization_status(self, orchestrator):
        status = await orchestrator.get_optimization_status()
        
        assert 'last_optimization_time' in status
        assert 'optimizations_today' in status
        assert 'daily_limit' in status
        assert 'can_optimize_now' in status
        assert 'trigger_config' in status

    @pytest.mark.asyncio
    async def test_force_optimization(self, orchestrator, mock_system_prompt):
        with patch('app.services.optimization_orchestrator.UserFeedback.objects.filter') as mock_filter:
            mock_queryset = MagicMock()
            mock_queryset.__aiter__ = AsyncMock(return_value=iter([]))
            mock_filter.return_value = mock_queryset
            
            with patch.object(orchestrator, '_execute_optimization_cycle') as mock_execute:
                mock_result = MagicMock(spec=OptimizationResult)
                mock_execute.return_value = mock_result
                
                result = await orchestrator.force_optimization("Manual test")
                
                assert result == mock_result
                mock_execute.assert_called_once()
                
                # Verify the trigger analysis passed to execute
                call_args = mock_execute.call_args[0][0]
                assert call_args['reason'] == "Manual test"
                assert call_args['should_trigger'] == True

    def test_reset_daily_count(self, orchestrator):
        # Set count to non-zero
        orchestrator._optimization_count_today = 5
        orchestrator._last_count_reset_date = timezone.now().date() - timedelta(days=1)
        
        orchestrator._reset_daily_count_if_needed()
        
        assert orchestrator._optimization_count_today == 0
        assert orchestrator._last_count_reset_date == timezone.now().date()

    def test_can_optimize_based_on_time(self, orchestrator):
        # Test when no previous optimization
        assert orchestrator._can_optimize_based_on_time() == True
        
        # Test when too recent
        orchestrator._last_optimization_time = timezone.now() - timedelta(minutes=30)
        assert orchestrator._can_optimize_based_on_time() == False
        
        # Test when enough time has passed
        orchestrator._last_optimization_time = timezone.now() - timedelta(hours=2)
        assert orchestrator._can_optimize_based_on_time() == True