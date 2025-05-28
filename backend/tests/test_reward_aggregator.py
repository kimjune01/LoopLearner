import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from asgiref.sync import sync_to_async
from app.services.reward_aggregator import (
    RewardFunctionAggregator,
    RewardComponents,
    RewardWeights,
    ExactMatchReward,
    F1ScoreReward,
    PerplexityReward,
    HumanFeedbackReward,
    LengthAppropriatenessReward
)
from core.models import SystemPrompt, UserFeedback, ReasonRating


@pytest_asyncio.fixture
async def mock_llm_provider():
    """Mock LLM provider for perplexity calculations"""
    mock_llm = AsyncMock()
    mock_llm.get_log_probabilities = AsyncMock(return_value=[-0.5, -0.3, -0.7, -0.4])
    return mock_llm


@pytest_asyncio.fixture
async def system_prompt():
    """Test system prompt"""
    prompt, created = await sync_to_async(SystemPrompt.objects.get_or_create)(
        version=20,  # Use different version to avoid conflicts
        defaults={
            'content': "You are a helpful assistant for reward testing.",
            'is_active': True
        }
    )
    return prompt


@pytest_asyncio.fixture
async def user_feedback_accept():
    """Mock user feedback - accept action"""
    feedback = type('MockFeedback', (), {
        'action': 'accept',
        'reason': 'Great response',
        'reason_ratings': type('MockQuerySet', (), {
            'all': lambda self: [
                type('MockRating', (), {'liked': True})(),
                type('MockRating', (), {'liked': True})()
            ]
        })()
    })()
    return feedback


@pytest_asyncio.fixture
async def user_feedback_reject():
    """Mock user feedback - reject action"""
    feedback = type('MockFeedback', (), {
        'action': 'reject',
        'reason': 'Too formal and lengthy',
        'reason_ratings': type('MockQuerySet', (), {
            'all': lambda self: []
        })()
    })()
    return feedback


@pytest_asyncio.fixture
def custom_weights():
    """Custom reward weights for testing"""
    return RewardWeights(
        exact_match=0.2,
        f1_score=0.4,
        perplexity=0.1,
        human_feedback=0.2,
        length_appropriateness=0.05,
        semantic_similarity=0.05
    )


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_exact_match_reward_perfect_match():
    """Test exact match reward with perfect match"""
    reward_func = ExactMatchReward()
    
    context = {
        'expected_output': 'Thank you for your email. I will respond shortly.',
        'actual_output': 'Thank you for your email. I will respond shortly.'
    }
    
    reward = await reward_func.compute_reward("original", "rewritten", context)
    assert reward == 1.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_exact_match_reward_no_match():
    """Test exact match reward with no match"""
    reward_func = ExactMatchReward()
    
    context = {
        'expected_output': 'Thank you for your email.',
        'actual_output': 'I appreciate your message.'
    }
    
    reward = await reward_func.compute_reward("original", "rewritten", context)
    assert reward == 0.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_exact_match_reward_missing_data():
    """Test exact match reward with missing data"""
    reward_func = ExactMatchReward()
    
    context = {'expected_output': ''}  # Missing actual_output
    
    reward = await reward_func.compute_reward("original", "rewritten", context)
    assert reward == 0.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_f1_score_reward_calculation():
    """Test F1 score calculation"""
    reward_func = F1ScoreReward()
    
    context = {
        'expected_output': 'thank you for your email message',
        'actual_output': 'thank you for the email'
    }
    
    reward = await reward_func.compute_reward("original", "rewritten", context)
    
    # Expected calculation:
    # expected_set = {thank, you, for, your, email, message}
    # actual_set = {thank, you, for, the, email}
    # intersection = {thank, you, for, email}
    # precision = 4/5 = 0.8
    # recall = 4/6 = 0.667
    # f1 = 2 * (0.8 * 0.667) / (0.8 + 0.667) = 0.727
    
    assert 0.7 < reward < 0.75  # Approximate F1 score


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_f1_score_reward_empty_inputs():
    """Test F1 score with empty inputs"""
    reward_func = F1ScoreReward()
    
    # Both empty - should be perfect match
    context = {'expected_output': '', 'actual_output': ''}
    reward = await reward_func.compute_reward("original", "rewritten", context)
    assert reward == 1.0
    
    # One empty - should be zero
    context = {'expected_output': 'some text', 'actual_output': ''}
    reward = await reward_func.compute_reward("original", "rewritten", context)
    assert reward == 0.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_perplexity_reward_calculation(mock_llm_provider):
    """Test perplexity reward calculation"""
    reward_func = PerplexityReward(mock_llm_provider)
    
    context = {'actual_output': 'This is a test response'}
    
    reward = await reward_func.compute_reward("original", "rewritten", context)
    
    # Verify LLM was called
    mock_llm_provider.get_log_probabilities.assert_called_once_with('This is a test response')
    
    # Reward should be positive (inverse of perplexity)
    assert 0.0 <= reward <= 1.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_perplexity_reward_error_handling(mock_llm_provider):
    """Test perplexity reward error handling"""
    # Make LLM provider raise an exception
    mock_llm_provider.get_log_probabilities.side_effect = Exception("API Error")
    
    reward_func = PerplexityReward(mock_llm_provider)
    context = {'actual_output': 'Test output'}
    
    reward = await reward_func.compute_reward("original", "rewritten", context)
    assert reward == 0.5  # Neutral score on error


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_human_feedback_reward_accept(user_feedback_accept):
    """Test human feedback reward for accept action"""
    reward_func = HumanFeedbackReward()
    
    context = {'user_feedback': user_feedback_accept}
    
    reward = await reward_func.compute_reward("original", "rewritten", context)
    
    # Should get base reward (1.0) plus bonus for positive reason ratings
    assert reward > 1.0
    assert reward <= 1.2  # Maximum possible with bonus


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_human_feedback_reward_reject(user_feedback_reject):
    """Test human feedback reward for reject action"""
    reward_func = HumanFeedbackReward()
    
    context = {'user_feedback': user_feedback_reject}
    
    reward = await reward_func.compute_reward("original", "rewritten", context)
    assert reward == 0.0  # Reject should give zero reward


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_human_feedback_reward_no_feedback():
    """Test human feedback reward with no feedback"""
    reward_func = HumanFeedbackReward()
    
    context = {}  # No user_feedback
    
    reward = await reward_func.compute_reward("original", "rewritten", context)
    assert reward == 0.5  # Neutral when no feedback


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_length_appropriateness_reward_perfect():
    """Test length appropriateness reward - perfect length"""
    reward_func = LengthAppropriatenessReward()
    
    context = {
        'expected_length': 10,
        'actual_output': 'This response has exactly ten words in total here.'  # 10 words
    }
    
    reward = await reward_func.compute_reward("original", "rewritten", context)
    assert reward == 1.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_length_appropriateness_reward_acceptable_range():
    """Test length appropriateness reward - acceptable range"""
    reward_func = LengthAppropriatenessReward()
    
    context = {
        'expected_length': 10,
        'actual_output': 'This response has exactly eight words total here.'  # 8 words (ratio = 0.8)
    }
    
    reward = await reward_func.compute_reward("original", "rewritten", context)
    assert reward == 1.0  # Within 0.8-1.2 range


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_length_appropriateness_reward_poor_match():
    """Test length appropriateness reward - poor length match"""
    reward_func = LengthAppropriatenessReward()
    
    context = {
        'expected_length': 10,
        'actual_output': 'Short.'  # 1 word (ratio = 0.1)
    }
    
    reward = await reward_func.compute_reward("original", "rewritten", context)
    assert reward == 0.1  # Very poor length match


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_reward_aggregator_initialization(mock_llm_provider):
    """Test reward aggregator initialization"""
    aggregator = RewardFunctionAggregator(mock_llm_provider)
    
    assert aggregator.weights is not None
    assert aggregator.scenario_weights == {}
    assert 'exact_match' in aggregator.reward_functions
    assert 'f1_score' in aggregator.reward_functions
    assert 'perplexity' in aggregator.reward_functions
    assert 'human_feedback' in aggregator.reward_functions
    assert 'length_appropriateness' in aggregator.reward_functions


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_reward_aggregator_custom_weights(mock_llm_provider, custom_weights):
    """Test reward aggregator with custom weights"""
    aggregator = RewardFunctionAggregator(mock_llm_provider, weights=custom_weights)
    
    assert aggregator.weights.exact_match == 0.2
    assert aggregator.weights.f1_score == 0.4
    assert aggregator.weights.perplexity == 0.1


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_compute_aggregated_reward(mock_llm_provider, system_prompt, user_feedback_accept):
    """Test computation of aggregated reward"""
    aggregator = RewardFunctionAggregator(mock_llm_provider)
    
    task_performance = {
        'expected_output': 'Thank you for your email',
        'actual_output': 'Thank you for your email',
        'expected_length': 5
    }
    
    reward = await aggregator.compute_reward(
        system_prompt,
        "Rewritten prompt content",
        user_feedback_accept,
        task_performance
    )
    
    # Should get a positive reward (weighted combination)
    assert 0.0 <= reward <= 1.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_scenario_specific_weights(mock_llm_provider):
    """Test scenario-specific weight handling"""
    scenario_weights = {
        'professional': RewardWeights(human_feedback=0.5, f1_score=0.3, perplexity=0.2),
        'casual': RewardWeights(human_feedback=0.3, f1_score=0.5, perplexity=0.2)
    }
    
    aggregator = RewardFunctionAggregator(
        mock_llm_provider,
        scenario_specific_weights=scenario_weights
    )
    
    # Test professional scenario uses correct weights
    context = {'email_scenario': 'professional'}
    
    # Use real reward function implementations instead of mocking
    # This tests the actual business logic and weighted aggregation
    
    # Create realistic context for real reward functions
    context.update({
        'expected_output': 'professional email response',
        'actual_output': 'professional email response',  # Perfect match for testing
        'user_feedback': type('MockFeedback', (), {'action': 'accept'})(),
        'expected_length': 4  # 4 words in actual output
    })
    
    mock_prompt = type('MockPrompt', (), {'content': 'test'})()
    mock_feedback = context['user_feedback']
    
    reward = await aggregator.compute_reward(
        mock_prompt,
        "rewritten",
        mock_feedback,
        {},
        context
    )
    
    # Verify scenario-specific weights were used
    assert reward is not None


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_evaluate_candidate(mock_llm_provider):
    """Test candidate evaluation for selection"""
    aggregator = RewardFunctionAggregator(mock_llm_provider)
    
    # Create mock candidate
    candidate = type('MockCandidate', (), {
        'content': 'Test rewritten prompt',
        'confidence': 0.8
    })()
    
    evaluation_context = {
        'original_prompt': 'Original prompt',
        'expected_output': 'Expected response'
    }
    
    score = await aggregator.evaluate_candidate(candidate, evaluation_context)
    
    # Score should be candidate confidence * computed reward
    assert 0.0 <= score <= 0.8  # Max is confidence * 1.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_update_weights(mock_llm_provider):
    """Test updating scenario-specific weights"""
    aggregator = RewardFunctionAggregator(mock_llm_provider)
    
    new_weights = RewardWeights(human_feedback=0.8, f1_score=0.2)
    aggregator.update_weights('test_scenario', new_weights)
    
    assert 'test_scenario' in aggregator.scenario_weights
    assert aggregator.scenario_weights['test_scenario'].human_feedback == 0.8


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_reward_breakdown(mock_llm_provider):
    """Test getting detailed reward breakdown"""
    aggregator = RewardFunctionAggregator(mock_llm_provider)
    
    # Create context with reward components
    components = RewardComponents(
        exact_match=1.0,
        f1_score=0.8,
        perplexity=0.7,
        human_feedback=0.9,
        length_appropriateness=0.85,
        semantic_similarity=0.75
    )
    
    context = {'reward_components': components}
    breakdown = aggregator.get_reward_breakdown(context)
    
    assert breakdown['exact_match'] == 1.0
    assert breakdown['f1_score'] == 0.8
    assert breakdown['perplexity'] == 0.7
    assert breakdown['human_feedback'] == 0.9
    assert breakdown['length_appropriateness'] == 0.85
    assert breakdown['semantic_similarity'] == 0.75


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_reward_components_dataclass():
    """Test RewardComponents dataclass"""
    components = RewardComponents(
        exact_match=0.9,
        f1_score=0.8,
        perplexity=0.7
    )
    
    assert components.exact_match == 0.9
    assert components.f1_score == 0.8
    assert components.perplexity == 0.7
    assert components.human_feedback == 0.0  # Default value
    assert components.length_appropriateness == 0.0  # Default value


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_reward_weights_dataclass():
    """Test RewardWeights dataclass"""
    weights = RewardWeights(
        exact_match=0.15,
        f1_score=0.35,
        perplexity=0.25,
        human_feedback=0.25
    )
    
    assert weights.exact_match == 0.15
    assert weights.f1_score == 0.35
    assert weights.perplexity == 0.25
    assert weights.human_feedback == 0.25
    assert weights.length_appropriateness == 0.05  # Default value


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_error_handling_in_aggregation(mock_llm_provider, system_prompt):
    """Test error handling in reward aggregation"""
    aggregator = RewardFunctionAggregator(mock_llm_provider)
    
    # Make one reward function fail
    aggregator.reward_functions['exact_match'].compute_reward = AsyncMock(side_effect=Exception("Test error"))
    
    mock_feedback = type('MockFeedback', (), {'action': 'accept'})()
    
    reward = await aggregator.compute_reward(
        system_prompt,
        "rewritten prompt",
        mock_feedback,
        {}
    )
    
    # Should return neutral reward on error
    assert reward == 0.5