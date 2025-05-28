import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch
from asgiref.sync import sync_to_async
from app.services.optimizer import LLMBasedOptimizer
from app.services.llm_provider import OpenAIProvider
from core.models import SystemPrompt, EvaluationSnapshot, Email, UserFeedback, Draft


@pytest.fixture
def mock_llm():
    return OpenAIProvider("test-api-key")

@pytest.fixture
def optimizer(mock_llm):
    return LLMBasedOptimizer(mock_llm)

@pytest_asyncio.fixture
async def current_prompt():
    prompt, created = await sync_to_async(SystemPrompt.objects.get_or_create)(
        version=1,
        defaults={
            'content': "You are a helpful email assistant.",
            'is_active': True
        }
    )
    return prompt

@pytest_asyncio.fixture
async def test_email():
    return await sync_to_async(Email.objects.create)(
        subject="Test Email",
        body="Test body",
        sender="test@example.com",
        scenario_type="professional"
    )


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_optimize_prompt_interface(optimizer, current_prompt, mock_llm):
    """Test that optimize_prompt method exists"""
    # Mock the LLM provider's optimize_prompt method
    mock_response = "You are an improved email assistant that considers user feedback."
    
    with patch.object(mock_llm, 'optimize_prompt', return_value=mock_response):
        result = await optimizer.optimize_prompt(current_prompt, [], [])
        
        assert isinstance(result, SystemPrompt)
        assert result.content == mock_response
        assert result.version == 2  # Should increment version


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_evaluate_prompt_interface(optimizer, test_email):
    """Test that evaluate_prompt method exists"""
    # Create test evaluation snapshot
    eval_snapshot = await sync_to_async(EvaluationSnapshot.objects.create)(
        email=test_email,
        expected_outcome="Professional response",
        prompt_version=1,
        performance_score=0.8
    )
    
    result = await optimizer.evaluate_prompt(current_prompt, [eval_snapshot])
    
    assert isinstance(result, float)
    assert 0.0 <= result <= 1.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_optimize_prompt_returns_new_prompt(optimizer, current_prompt, mock_llm):
    """Test that optimization returns improved prompt"""
    # Mock the LLM provider
    mock_improved_content = "You are an enhanced email assistant that learns from user feedback and adapts to preferences."
    
    with patch.object(mock_llm, 'optimize_prompt', return_value=mock_improved_content):
        result = await optimizer.optimize_prompt(current_prompt, [], [])
        
        assert isinstance(result, SystemPrompt)
        assert result.content == mock_improved_content
        assert result.version > current_prompt.version
        assert result.is_active == False  # New prompts start as inactive


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_evaluate_prompt_returns_score(optimizer, current_prompt, test_email):
    """Test that evaluation returns numeric score"""
    # Create test evaluation snapshots
    eval_snapshot1 = await sync_to_async(EvaluationSnapshot.objects.create)(
        email=test_email,
        expected_outcome="Professional response",
        prompt_version=1,
        performance_score=0.8
    )
    
    eval_snapshot2 = await sync_to_async(EvaluationSnapshot.objects.create)(
        email=test_email,
        expected_outcome="Friendly response",
        prompt_version=1,
        performance_score=0.9
    )
    
    result = await optimizer.evaluate_prompt(current_prompt, [eval_snapshot1, eval_snapshot2])
    
    assert isinstance(result, float)
    assert abs(result - 0.85) < 0.001  # Average of 0.8 and 0.9 (with floating point tolerance)