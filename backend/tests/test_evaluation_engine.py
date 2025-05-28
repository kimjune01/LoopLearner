import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime

from app.services.evaluation_engine import (
    EvaluationEngine, BatchPromptEvaluator, ABTestingEngine, 
    EvaluationTestSuite, EvaluationResult, ComparisonResult, EvaluationTestCase
)
from app.services.unified_llm_provider import LLMProviderFactory, LLMConfig
from app.services.reward_aggregator import RewardFunctionAggregator
from core.models import SystemPrompt, Email


@pytest.fixture
def mock_llm_config():
    return LLMConfig(
        provider="mock",
        model="test-model",
        api_key="test-key"
    )


@pytest.fixture
def mock_system_prompt():
    prompt = MagicMock(spec=SystemPrompt)
    prompt.content = "You are a helpful assistant."
    prompt.version = 1
    prompt.performance_score = 0.0
    prompt.save = MagicMock()
    return prompt


@pytest.fixture
def mock_email():
    email = MagicMock(spec=Email)
    email.subject = "Test Subject"
    email.body = "Test email body"
    email.sender = "test@example.com"
    email.scenario_type = "professional"
    return email


@pytest.fixture
def test_cases(mock_email):
    return [
        EvaluationTestCase(
            email=mock_email,
            expected_qualities={"f1_score": 0.7, "semantic_similarity": 0.8},
            scenario_type="professional",
            difficulty_level="medium"
        )
    ]


@pytest.fixture
async def batch_evaluator(mock_llm_config):
    provider = LLMProviderFactory.create_provider(mock_llm_config)
    reward_aggregator = MagicMock(spec=RewardFunctionAggregator)
    reward_aggregator.compute_reward = AsyncMock(return_value=0.75)
    return BatchPromptEvaluator(reward_aggregator)


@pytest.fixture
def ab_testing_engine(batch_evaluator):
    return ABTestingEngine(batch_evaluator)


@pytest.fixture
def evaluation_test_suite():
    return EvaluationTestSuite()


@pytest.fixture
async def evaluation_engine(mock_llm_config):
    provider = LLMProviderFactory.create_provider(mock_llm_config)
    reward_aggregator = MagicMock(spec=RewardFunctionAggregator)
    reward_aggregator.compute_reward = AsyncMock(return_value=0.75)
    return EvaluationEngine(provider, reward_aggregator)


class TestBatchPromptEvaluator:
    @pytest.mark.asyncio
    async def test_evaluate_prompt_success(self, batch_evaluator, mock_system_prompt, test_cases, mock_llm_config):
        provider = LLMProviderFactory.create_provider(mock_llm_config)
        provider.generate = AsyncMock(return_value="Test response")
        provider.get_log_probabilities = AsyncMock(return_value=[-0.5, -0.3, -0.7])
        
        result = await batch_evaluator.evaluate_prompt(mock_system_prompt, test_cases, provider)
        
        assert isinstance(result, EvaluationResult)
        assert result.prompt == mock_system_prompt
        assert 0.0 <= result.performance_score <= 1.0
        assert result.test_cases_used == len(test_cases)
        assert result.error_rate == 0.0

    @pytest.mark.asyncio
    async def test_evaluate_prompt_empty_test_cases(self, batch_evaluator, mock_system_prompt, mock_llm_config):
        provider = LLMProviderFactory.create_provider(mock_llm_config)
        
        with pytest.raises(ValueError, match="No successful evaluations completed"):
            await batch_evaluator.evaluate_prompt(mock_system_prompt, [], provider)

    @pytest.mark.asyncio
    async def test_evaluate_prompt_handles_errors(self, batch_evaluator, mock_system_prompt, test_cases, mock_llm_config):
        provider = LLMProviderFactory.create_provider(mock_llm_config)
        provider.generate = AsyncMock(side_effect=Exception("LLM error"))
        
        with pytest.raises(ValueError, match="No successful evaluations completed"):
            await batch_evaluator.evaluate_prompt(mock_system_prompt, test_cases, provider)


class TestABTestingEngine:
    @pytest.mark.asyncio
    async def test_compare_prompts(self, ab_testing_engine, mock_llm_config):
        baseline = MagicMock(spec=SystemPrompt)
        baseline.version = 1
        candidate = MagicMock(spec=SystemPrompt)
        candidate.version = 2
        
        provider = LLMProviderFactory.create_provider(mock_llm_config)
        
        # Mock evaluator to return different scores
        ab_testing_engine.evaluator.evaluate_prompt = AsyncMock()
        ab_testing_engine.evaluator.evaluate_prompt.side_effect = [
            EvaluationResult(
                prompt=baseline,
                performance_score=0.6,
                metrics={},
                sample_outputs=[],
                evaluation_time=datetime.now(),
                test_cases_used=5,
                error_rate=0.0
            ),
            EvaluationResult(
                prompt=candidate,
                performance_score=0.8,
                metrics={},
                sample_outputs=[],
                evaluation_time=datetime.now(),
                test_cases_used=5,
                error_rate=0.0
            )
        ]
        
        result = await ab_testing_engine.compare_prompts(baseline, candidate, [], provider)
        
        assert isinstance(result, ComparisonResult)
        assert result.baseline.prompt == baseline
        assert result.candidate.prompt == candidate
        assert result.improvement > 0  # Candidate performed better
        assert result.winner in ["candidate", "baseline", "tie"]

    def test_determine_winner_candidate_wins(self, ab_testing_engine):
        baseline = EvaluationResult(
            prompt=MagicMock(),
            performance_score=0.6,
            metrics={},
            sample_outputs=[],
            evaluation_time=datetime.now(),
            test_cases_used=5,
            error_rate=0.0
        )
        candidate = EvaluationResult(
            prompt=MagicMock(),
            performance_score=0.8,
            metrics={},
            sample_outputs=[],
            evaluation_time=datetime.now(),
            test_cases_used=5,
            error_rate=0.0
        )
        
        winner = ab_testing_engine._determine_winner(baseline, candidate, 0.01)  # Significant p-value
        assert winner == "candidate"

    def test_determine_winner_not_significant(self, ab_testing_engine):
        baseline = EvaluationResult(
            prompt=MagicMock(),
            performance_score=0.7,
            metrics={},
            sample_outputs=[],
            evaluation_time=datetime.now(),
            test_cases_used=5,
            error_rate=0.0
        )
        candidate = EvaluationResult(
            prompt=MagicMock(),
            performance_score=0.72,
            metrics={},
            sample_outputs=[],
            evaluation_time=datetime.now(),
            test_cases_used=5,
            error_rate=0.0
        )
        
        winner = ab_testing_engine._determine_winner(baseline, candidate, 0.8)  # Not significant
        assert winner == "tie"


class TestEvaluationTestSuite:
    @pytest.mark.asyncio
    async def test_generate_test_cases_with_synthetic_data(self, evaluation_test_suite):
        with patch('app.services.evaluation_engine.Email.objects.all') as mock_query:
            # Mock empty queryset
            mock_query.return_value.__aiter__ = AsyncMock(return_value=iter([]))
            
            test_cases = await evaluation_test_suite.generate_test_cases(['professional'], ['medium'], 2)
            
            assert len(test_cases) >= 1  # Should generate synthetic cases
            for test_case in test_cases:
                assert isinstance(test_case, EvaluationTestCase)
                assert test_case.email is not None
                assert test_case.scenario_type in ['professional', 'casual', 'technical', 'urgent']

    @pytest.mark.asyncio 
    async def test_generate_synthetic_test_cases(self, evaluation_test_suite):
        test_cases = await evaluation_test_suite._generate_synthetic_test_cases(['professional'], ['medium'], 2)
        
        assert len(test_cases) >= 1
        for test_case in test_cases:
            assert isinstance(test_case, EvaluationTestCase)
            assert test_case.email.subject
            assert test_case.email.body
            assert test_case.scenario_type


class TestEvaluationEngine:
    @pytest.mark.asyncio
    async def test_evaluate_prompt_performance(self, evaluation_engine, mock_system_prompt):
        with patch('app.services.evaluation_engine.sync_to_async') as mock_sync_to_async:
            mock_sync_to_async.return_value = AsyncMock()
            
            evaluation_engine.test_suite.generate_test_cases = AsyncMock(return_value=[
                EvaluationTestCase(
                    email=MagicMock(),
                    expected_qualities={},
                    scenario_type="professional",
                    difficulty_level="medium"
                )
            ])
            
            evaluation_engine.evaluator.evaluate_prompt = AsyncMock(return_value=EvaluationResult(
                prompt=mock_system_prompt,
                performance_score=0.75,
                metrics={},
                sample_outputs=[],
                evaluation_time=datetime.now(),
                test_cases_used=1,
                error_rate=0.0
            ))
            
            result = await evaluation_engine.evaluate_prompt_performance(mock_system_prompt, 5)
            
            assert isinstance(result, EvaluationResult)
            assert result.prompt == mock_system_prompt
            assert result.performance_score == 0.75

    @pytest.mark.asyncio
    async def test_compare_prompt_candidates(self, evaluation_engine, mock_system_prompt):
        baseline = mock_system_prompt
        candidates = [MagicMock(spec=SystemPrompt), MagicMock(spec=SystemPrompt)]
        
        evaluation_engine.test_suite.generate_test_cases = AsyncMock(return_value=[
            EvaluationTestCase(
                email=MagicMock(),
                expected_qualities={},
                scenario_type="professional", 
                difficulty_level="medium"
            )
        ])
        
        evaluation_engine.ab_testing.compare_prompts = AsyncMock(return_value=ComparisonResult(
            baseline=EvaluationResult(
                prompt=baseline,
                performance_score=0.6,
                metrics={},
                sample_outputs=[],
                evaluation_time=datetime.now(),
                test_cases_used=1,
                error_rate=0.0
            ),
            candidate=EvaluationResult(
                prompt=candidates[0],
                performance_score=0.8,
                metrics={},
                sample_outputs=[],
                evaluation_time=datetime.now(),
                test_cases_used=1,
                error_rate=0.0
            ),
            improvement=33.3,
            statistical_significance=0.01,
            winner="candidate",
            confidence_level=0.99
        ))
        
        results = await evaluation_engine.compare_prompt_candidates(baseline, candidates, 5)
        
        assert len(results) == len(candidates)
        for result in results:
            assert isinstance(result, ComparisonResult)

    @pytest.mark.asyncio
    async def test_find_best_prompt_single_candidate(self, evaluation_engine, mock_system_prompt):
        candidates = [mock_system_prompt]
        
        with patch('app.services.evaluation_engine.sync_to_async') as mock_sync_to_async:
            mock_sync_to_async.return_value = AsyncMock()
            
            evaluation_engine.evaluate_prompt_performance = AsyncMock(return_value=EvaluationResult(
                prompt=mock_system_prompt,
                performance_score=0.75,
                metrics={},
                sample_outputs=[],
                evaluation_time=datetime.now(),
                test_cases_used=1,
                error_rate=0.0
            ))
            
            best_prompt, best_result = await evaluation_engine.find_best_prompt(candidates, 5)
            
            assert best_prompt == mock_system_prompt
            assert isinstance(best_result, EvaluationResult)

    @pytest.mark.asyncio
    async def test_find_best_prompt_no_candidates(self, evaluation_engine):
        with pytest.raises(ValueError, match="No candidates provided"):
            await evaluation_engine.find_best_prompt([], 5)

    @pytest.mark.asyncio
    async def test_find_best_prompt_multiple_candidates(self, evaluation_engine):
        candidates = [MagicMock(spec=SystemPrompt) for _ in range(3)]
        for i, candidate in enumerate(candidates):
            candidate.version = i + 1
            candidate.save = MagicMock()
        
        with patch('app.services.evaluation_engine.sync_to_async') as mock_sync_to_async:
            mock_sync_to_async.return_value = AsyncMock()
            
            evaluation_engine.test_suite.generate_test_cases = AsyncMock(return_value=[
                EvaluationTestCase(
                    email=MagicMock(),
                    expected_qualities={},
                    scenario_type="professional",
                    difficulty_level="medium"
                )
            ])
            
            # Mock different scores for each candidate
            evaluation_engine.evaluator.evaluate_prompt = AsyncMock()
            evaluation_engine.evaluator.evaluate_prompt.side_effect = [
                EvaluationResult(
                    prompt=candidates[i],
                    performance_score=0.6 + i * 0.1,  # Increasing scores
                    metrics={},
                    sample_outputs=[],
                    evaluation_time=datetime.now(),
                    test_cases_used=1,
                    error_rate=0.0
                ) for i in range(3)
            ]
            
            best_prompt, best_result = await evaluation_engine.find_best_prompt(candidates, 5)
            
            assert best_prompt == candidates[2]  # Highest score
            assert best_result.performance_score == 0.8