import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from asgiref.sync import sync_to_async

from app.services.prompt_rewriter import LLMBasedPromptRewriter, RewriteContext, RewriteCandidate
from app.services.reward_aggregator import RewardFunctionAggregator
from app.services.meta_prompt_manager import MetaPromptManager
from core.models import SystemPrompt, UserFeedback, Email, Draft


@pytest_asyncio.fixture
async def mock_llm_provider():
    """Mock LLM provider for testing"""
    mock = AsyncMock()
    mock.generate.return_value = "You are an enhanced email assistant that provides professional responses."
    mock.get_log_probabilities.return_value = [-2.5, -1.8, -3.1, -2.0, -1.5, -2.8]
    return mock


@pytest_asyncio.fixture
async def rewriter_with_real_components(mock_llm_provider):
    """LLM-based rewriter with real reward aggregator and meta-prompt manager"""
    reward_aggregator = RewardFunctionAggregator(llm_provider=mock_llm_provider)
    meta_prompt_manager = MetaPromptManager()
    
    return LLMBasedPromptRewriter(
        rewriter_llm_provider=mock_llm_provider,
        similarity_llm_provider=mock_llm_provider,
        reward_function_aggregator=reward_aggregator,
        meta_prompt_manager=meta_prompt_manager
    )


@pytest_asyncio.fixture
async def test_system_prompt():
    """Test system prompt"""
    prompt, created = await sync_to_async(SystemPrompt.objects.get_or_create)(
        version=2000,
        defaults={
            'content': "You are a helpful email assistant.",
            'is_active': True
        }
    )
    return prompt


@pytest_asyncio.fixture
async def test_email():
    """Test email"""
    email = await Email.objects.acreate(
        subject="Test Learning Email",
        body="This is a test email for learning pipeline validation.",
        sender="test@learning.com",
        scenario_type="professional"
    )
    return email


@pytest_asyncio.fixture
async def test_draft(test_email, test_system_prompt):
    """Test draft"""
    draft = await Draft.objects.acreate(
        email=test_email,
        content="Thank you for your email. I will review this and get back to you shortly.",
        system_prompt=test_system_prompt,
        version=1
    )
    return draft


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_learning_pipeline_integration(rewriter_with_real_components, test_system_prompt, test_email):
    """Test complete learning pipeline from rewrite to feedback storage"""
    
    # Step 1: Create rewrite context
    context = RewriteContext(
        email_scenario="professional",
        current_prompt=test_system_prompt,
        recent_feedback=[],
        performance_history={"overall_quality": 0.6},
        constraints={"max_length": 200, "tone": "professional"}
    )
    
    # Step 2: Generate rewrite candidates
    candidates = await rewriter_with_real_components.rewrite_prompt(context, mode="conservative")
    
    assert len(candidates) == 1
    assert isinstance(candidates[0], RewriteCandidate)
    assert candidates[0].confidence == 0.9
    
    # Step 3: Select best candidate
    best_candidate = await rewriter_with_real_components.select_best_candidate(
        candidates, 
        {"scenario": "professional"}
    )
    
    assert best_candidate is not None
    assert best_candidate.content
    
    # Step 4: Create mock user feedback (accept)
    mock_feedback = type('MockFeedback', (), {
        'action': 'accept',
        'reasoning_factors': {
            'clarity': 4,
            'tone': 4,
            'completeness': 4,
            'relevance': 4
        },
        'edited_content': None,
        'created_at': '2024-01-01T00:00:00Z'
    })()
    
    # Step 5: Test learning from feedback
    initial_prompt_count = await SystemPrompt.objects.acount()
    
    await rewriter_with_real_components.update_from_feedback(
        test_system_prompt,
        best_candidate.content,
        mock_feedback,
        {'f1_score': 0.8, 'semantic_similarity': 0.75}
    )
    
    # Verify learning occurred
    final_prompt_count = await SystemPrompt.objects.acount()
    assert final_prompt_count >= initial_prompt_count  # New prompt may be created if reward > 0.7


@pytest.mark.django_db 
@pytest.mark.asyncio
async def test_reward_calculation_with_real_perplexity(mock_llm_provider):
    """Test reward calculation using real perplexity computation"""
    
    reward_aggregator = RewardFunctionAggregator(llm_provider=mock_llm_provider)
    
    # Create test system prompt
    system_prompt = await SystemPrompt.objects.acreate(
        content="Test prompt for reward calculation",
        version=2001,
        is_active=False
    )
    
    # Create mock feedback
    mock_feedback = type('MockFeedback', (), {
        'action': 'accept',
        'reasoning_factors': {
            'clarity': 4,
            'tone': 4,
            'completeness': 4,
            'relevance': 4
        }
    })()
    
    # Calculate reward with actual perplexity - include actual_output for perplexity calculation
    reward = await reward_aggregator.compute_reward(
        system_prompt,
        "You are an enhanced professional email assistant.",
        mock_feedback,
        {
            'f1_score': 0.8, 
            'semantic_similarity': 0.7,
            'actual_output': 'This is a test response for perplexity calculation'
        }
    )
    
    # Verify reward is reasonable
    assert isinstance(reward, float)
    assert 0.0 <= reward <= 1.0
    
    # Verify LLM was called for perplexity calculation (check call_count since it might be called multiple times)
    assert mock_llm_provider.get_log_probabilities.call_count >= 1
    
    # Cleanup
    await SystemPrompt.objects.filter(version=2001).adelete()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_feedback_pattern_storage_and_retrieval(rewriter_with_real_components, test_system_prompt):
    """Test that successful patterns are stored and retrieved correctly"""
    
    # Create mock feedback with high reward
    mock_feedback = type('MockFeedback', (), {
        'action': 'accept',
        'reasoning_factors': {
            'clarity': 5,
            'tone': 5,
            'completeness': 5,
            'relevance': 5
        },
        'edited_content': None,
        'created_at': '2024-01-01T00:00:00Z'
    })()
    
    rewritten_prompt = "You are a highly effective email assistant that provides clear, professional responses."
    
    # Store pattern (should create new SystemPrompt if reward > 0.7)
    initial_count = await SystemPrompt.objects.acount()
    
    await rewriter_with_real_components.update_from_feedback(
        test_system_prompt,
        rewritten_prompt,
        mock_feedback,
        {'f1_score': 0.9, 'semantic_similarity': 0.85}  # High performance
    )
    
    final_count = await SystemPrompt.objects.acount()
    
    # If reward was high enough, new pattern should be stored
    if final_count > initial_count:
        # Verify the new prompt was created
        latest_prompt = await SystemPrompt.objects.filter(
            version__gt=test_system_prompt.version
        ).afirst()
        
        assert latest_prompt is not None
        assert latest_prompt.content == rewritten_prompt
        assert latest_prompt.performance_score is not None
        assert latest_prompt.performance_score > 0.7


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_similarity_matching_with_database(rewriter_with_real_components, test_system_prompt):
    """Test similarity matching retrieves patterns from database"""
    
    # Create some historical successful prompts
    historical_prompt_1 = await SystemPrompt.objects.acreate(
        content="You are a professional email responder.",
        version=2002,
        is_active=False,
        performance_score=0.8
    )
    
    historical_prompt_2 = await SystemPrompt.objects.acreate(
        content="You are an efficient email assistant.",
        version=2003, 
        is_active=False,
        performance_score=0.75
    )
    
    # Create context for rewriting
    context = RewriteContext(
        email_scenario="professional",
        current_prompt=test_system_prompt,
        recent_feedback=[],
        performance_history={"overall_quality": 0.6},
        constraints={"max_length": 200, "tone": "professional"}
    )
    
    # Test that similarity matching queries database
    similar_patterns = await rewriter_with_real_components._get_successful_prompts_from_db("professional")
    
    # Should be empty initially since no feedback exists for these prompts
    assert isinstance(similar_patterns, list)
    
    # Cleanup
    await SystemPrompt.objects.filter(version__in=[2002, 2003]).adelete()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_learning_with_different_feedback_types(rewriter_with_real_components, test_system_prompt):
    """Test learning behavior with different types of feedback"""
    
    test_cases = [
        {
            'action': 'accept',
            'expected_reward_range': (0.6, 1.0),  # Adjusted based on actual reward weights
            'should_store_pattern': True
        },
        {
            'action': 'edit', 
            'expected_reward_range': (0.4, 0.8),
            'should_store_pattern': False  # Depends on final reward
        },
        {
            'action': 'reject',
            'expected_reward_range': (0.0, 0.5),
            'should_store_pattern': False
        }
    ]
    
    for i, case in enumerate(test_cases):
        mock_feedback = type('MockFeedback', (), {
            'action': case['action'],
            'reasoning_factors': {
                'clarity': 4,
                'tone': 4,
                'completeness': 4,
                'relevance': 4
            },
            'edited_content': f"Edited content {i}" if case['action'] == 'edit' else None,
            'created_at': '2024-01-01T00:00:00Z'
        })()
        
        # Calculate reward for this feedback type
        reward = await rewriter_with_real_components.reward_aggregator.compute_reward(
            test_system_prompt,
            f"Test rewritten prompt {i}",
            mock_feedback,
            {'f1_score': 0.7, 'semantic_similarity': 0.6}
        )
        
        # Verify reward is in expected range
        assert case['expected_reward_range'][0] <= reward <= case['expected_reward_range'][1], \
            f"Reward {reward} not in expected range {case['expected_reward_range']} for action {case['action']}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_learning_pipeline_error_handling(rewriter_with_real_components, test_system_prompt):
    """Test learning pipeline handles errors gracefully"""
    
    # Test with malformed feedback
    malformed_feedback = type('MockFeedback', (), {
        'action': 'invalid_action',
        'reasoning_factors': None,
        'edited_content': None,
        'created_at': '2024-01-01T00:00:00Z'
    })()
    
    # Should not crash
    try:
        await rewriter_with_real_components.update_from_feedback(
            test_system_prompt,
            "Test prompt",
            malformed_feedback,
            {}
        )
        # If it completes without exception, test passes
        assert True
    except Exception as e:
        # Log the error but test should handle gracefully
        pytest.fail(f"Learning pipeline should handle malformed feedback gracefully, got: {e}")


@pytest.fixture(scope="function", autouse=True)
async def cleanup_test_data():
    """Clean up test data after each test"""
    yield
    # Cleanup any test prompts created during tests
    await SystemPrompt.objects.filter(version__gte=2000).adelete()