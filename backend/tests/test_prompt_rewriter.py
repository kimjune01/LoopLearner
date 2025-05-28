import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from asgiref.sync import sync_to_async
from app.services.prompt_rewriter import (
    LLMBasedPromptRewriter, 
    RewriteCandidate, 
    RewriteContext,
    PromptRewriter
)
from core.models import SystemPrompt, Email, UserFeedback


@pytest_asyncio.fixture
async def mock_rewriter_llm():
    """Mock LLM provider for prompt rewriting"""
    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock()
    return mock_llm


@pytest_asyncio.fixture
async def mock_reward_aggregator():
    """Mock reward function aggregator"""
    mock_aggregator = AsyncMock()
    mock_aggregator.evaluate_candidate = AsyncMock(return_value=0.8)
    mock_aggregator.compute_reward = AsyncMock(return_value=0.7)
    return mock_aggregator


@pytest_asyncio.fixture
async def mock_meta_prompt_manager():
    """Mock meta-prompt manager"""
    mock_manager = AsyncMock()
    mock_manager.get_meta_prompt = AsyncMock(return_value="Rewrite this prompt to be more effective:")
    return mock_manager


@pytest_asyncio.fixture
async def mock_similarity_llm():
    """Mock LLM provider for similarity matching"""
    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(return_value='[{"prompt_id": 1, "similarity": 0.8, "reason": "similar tone"}]')
    return mock_llm


@pytest_asyncio.fixture
async def system_prompt():
    """Test system prompt"""
    prompt, created = await sync_to_async(SystemPrompt.objects.get_or_create)(
        version=10,  # Use different version to avoid conflicts
        defaults={
            'content': "You are a helpful email assistant.",
            'is_active': True
        }
    )
    return prompt


@pytest_asyncio.fixture
async def test_email():
    """Test email for context"""
    return await sync_to_async(Email.objects.create)(
        subject="Test Email for Rewriting",
        body="This is a test email body for prompt rewriting tests.",
        sender="test@rewriter.com",
        scenario_type="professional"
    )


@pytest_asyncio.fixture
async def rewrite_context(system_prompt, test_email):
    """Test rewrite context"""
    return RewriteContext(
        email_scenario="professional",
        current_prompt=system_prompt,
        recent_feedback=[],
        performance_history={"overall_quality": 0.6},
        constraints={"max_length": 200, "tone": "professional"}
    )


@pytest_asyncio.fixture
def llm_rewriter(mock_rewriter_llm, mock_similarity_llm, mock_reward_aggregator, mock_meta_prompt_manager):
    """LLM-based prompt rewriter instance"""
    return LLMBasedPromptRewriter(
        rewriter_llm_provider=mock_rewriter_llm,
        similarity_llm_provider=mock_similarity_llm,
        reward_function_aggregator=mock_reward_aggregator,
        meta_prompt_manager=mock_meta_prompt_manager
    )


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_llm_prompt_rewriter_implements_interface(llm_rewriter):
    """Test that LLMBasedPromptRewriter implements PromptRewriter interface"""
    assert isinstance(llm_rewriter, PromptRewriter)
    assert hasattr(llm_rewriter, 'rewrite_prompt')
    assert hasattr(llm_rewriter, 'select_best_candidate')


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_rewrite_prompt_conservative_mode(llm_rewriter, rewrite_context):
    """Test prompt rewriting in conservative mode with similarity matching"""
    # Setup mock LLM response
    llm_rewriter.rewriter_llm.generate.return_value = "You are an enhanced email assistant that provides professional responses."
    
    # Test conservative rewriting
    candidates = await llm_rewriter.rewrite_prompt(rewrite_context, mode="conservative")
    
    # Verify results
    assert isinstance(candidates, list)
    assert len(candidates) == 1  # Conservative mode should return single candidate
    assert isinstance(candidates[0], RewriteCandidate)
    assert candidates[0].temperature == 0.1  # Low temperature for consistency
    assert candidates[0].confidence == 0.9   # High confidence
    assert "enhanced email assistant" in candidates[0].content


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_rewrite_prompt_exploratory_mode(llm_rewriter, rewrite_context):
    """Test prompt rewriting in exploratory mode (LLM-based)"""
    # Setup mock LLM to return different responses for multiple calls
    responses = [
        "Enhanced email assistant for professional communication.",
        "Advanced email helper with user preference learning.", 
        "Intelligent email responder with context awareness.",
        "Smart email assistant with adaptive responses.",
        "Professional email generator with feedback integration."
    ]
    llm_rewriter.rewriter_llm.generate.side_effect = responses
    
    # Test exploratory rewriting
    candidates = await llm_rewriter.rewrite_prompt(rewrite_context, mode="exploratory")
    
    # Verify results
    assert isinstance(candidates, list)
    assert len(candidates) == 3  # Should generate 3 candidates
    assert all(isinstance(c, RewriteCandidate) for c in candidates)
    
    # Verify LLM was called 3 times
    assert llm_rewriter.rewriter_llm.generate.call_count == 3


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_rewrite_prompt_hybrid_mode(llm_rewriter, rewrite_context):
    """Test prompt rewriting in hybrid mode"""
    # Setup mock responses
    conservative_response = "Conservative enhanced email assistant."
    exploratory_responses = [f"Exploratory assistant variant {i}" for i in range(1, 6)]
    
    llm_rewriter.rewriter_llm.generate.side_effect = [conservative_response] + exploratory_responses
    
    # Test hybrid rewriting
    candidates = await llm_rewriter.rewrite_prompt(rewrite_context, mode="hybrid")
    
    # Verify results
    assert isinstance(candidates, list)
    assert len(candidates) == 4  # 1 conservative + 3 exploratory
    
    # First candidate should be conservative
    assert candidates[0].temperature == 0.0
    assert candidates[0].confidence == 0.9
    
    # Remaining should be exploratory
    for candidate in candidates[1:]:
        assert candidate.temperature == 1.0
        assert candidate.confidence == 0.7


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_select_best_candidate(llm_rewriter):
    """Test selection of best candidate from list"""
    # Create test candidates
    candidates = [
        RewriteCandidate("Candidate 1", 0.7, 0.0, "First option"),
        RewriteCandidate("Candidate 2", 0.9, 1.0, "Second option"),
        RewriteCandidate("Candidate 3", 0.6, 0.5, "Third option")
    ]
    
    # Setup mock reward evaluations
    llm_rewriter.reward_aggregator.evaluate_candidate.side_effect = [0.6, 0.9, 0.5]
    
    evaluation_context = {"email_scenario": "professional"}
    
    # Test candidate selection
    best_candidate = await llm_rewriter.select_best_candidate(candidates, evaluation_context)
    
    # Verify best candidate is selected
    assert best_candidate == candidates[1]  # Highest reward (0.9)
    assert best_candidate.content == "Candidate 2"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_update_from_feedback(llm_rewriter, system_prompt):
    """Test updating LLM-based rewriter from user feedback"""
    # Create test feedback
    test_feedback = type('MockFeedback', (), {
        'action': 'accept',
        'reason': 'Good response',
        'created_at': '2024-01-01T00:00:00Z'
    })()
    
    task_performance = {
        'accuracy': 0.8,
        'relevance': 0.9,
        'overall_quality': 0.85
    }
    
    rewritten_prompt = "Enhanced prompt for better email responses."
    
    # Test feedback processing
    await llm_rewriter.update_from_feedback(
        system_prompt,
        rewritten_prompt,
        test_feedback,
        task_performance
    )
    
    # Verify reward computation was called
    llm_rewriter.reward_aggregator.compute_reward.assert_called_once()
    
    # Verify training example was stored
    assert len(llm_rewriter.training_history) == 1
    training_example = llm_rewriter.training_history[0]
    assert training_example['original_prompt'] == system_prompt.content
    assert training_example['rewritten_prompt'] == rewritten_prompt
    assert training_example['reward'] == 0.7  # Mock return value


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_batch_training_trigger(llm_rewriter, system_prompt):
    """Test that batch training triggers after enough examples"""
    # Mock the training step
    llm_rewriter._run_training_step = AsyncMock()
    
    # Add 9 training examples (below threshold)
    for i in range(9):
        test_feedback = type('MockFeedback', (), {
            'action': 'accept',
            'reason': f'Feedback {i}',
            'created_at': '2024-01-01T00:00:00Z'
        })()
        
        await llm_rewriter.update_from_feedback(
            system_prompt,
            f"Rewritten prompt {i}",
            test_feedback,
            {'quality': 0.8}
        )
    
    # Training should not have triggered yet
    llm_rewriter._run_training_step.assert_not_called()
    assert len(llm_rewriter.training_history) == 9
    
    # Add 10th example (triggers training)
    test_feedback = type('MockFeedback', (), {
        'action': 'accept',
        'reason': 'Final feedback',
        'created_at': '2024-01-01T00:00:00Z'
    })()
    
    await llm_rewriter.update_from_feedback(
        system_prompt,
        "Final rewritten prompt",
        test_feedback,
        {'quality': 0.8}
    )
    
    # Training should have triggered and history cleared
    llm_rewriter._run_training_step.assert_called_once()
    assert len(llm_rewriter.training_history) == 0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_meta_prompt_integration(llm_rewriter, rewrite_context):
    """Test integration with meta-prompt manager"""
    # Setup mock meta-prompt
    expected_meta_prompt = "Professional email rewriting instructions..."
    llm_rewriter.meta_prompt_manager.get_meta_prompt.return_value = expected_meta_prompt
    
    # Mock LLM response
    llm_rewriter.rewriter_llm.generate.return_value = "Rewritten prompt output"
    
    # Test rewriting
    await llm_rewriter.rewrite_prompt(rewrite_context, mode="conservative")
    
    # Verify meta-prompt manager was called with correct parameters
    llm_rewriter.meta_prompt_manager.get_meta_prompt.assert_called_once_with(
        rewrite_context.email_scenario,
        rewrite_context.constraints
    )


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_build_rewrite_instruction(llm_rewriter, rewrite_context):
    """Test building of rewrite instruction"""
    meta_prompt = "Rewrite this prompt effectively:"
    
    # Test instruction building
    instruction = llm_rewriter._build_rewrite_instruction(rewrite_context, meta_prompt)
    
    # Verify instruction contains expected components
    assert meta_prompt in instruction
    assert rewrite_context.current_prompt.content in instruction
    assert rewrite_context.email_scenario in instruction
    assert str(rewrite_context.performance_history) in instruction
    assert "Rewritten Prompt:" in instruction


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_feedback_summarization(llm_rewriter):
    """Test summarization of recent feedback"""
    # Test with empty feedback
    summary = llm_rewriter._summarize_feedback([])
    assert summary == "No recent feedback"
    
    # Test with feedback list
    mock_feedback = [
        type('MockFeedback', (), {'action': 'accept'})(),
        type('MockFeedback', (), {'action': 'reject'})(),
        type('MockFeedback', (), {'action': 'accept'})(),
        type('MockFeedback', (), {'action': 'edit'})()
    ]
    
    summary = llm_rewriter._summarize_feedback(mock_feedback)
    assert "accept" in summary
    assert "reject" in summary
    assert "edit" in summary


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_rewrite_candidate_dataclass():
    """Test RewriteCandidate dataclass functionality"""
    candidate = RewriteCandidate(
        content="Test rewritten prompt",
        confidence=0.85,
        temperature=0.5,
        reasoning="Test reasoning"
    )
    
    assert candidate.content == "Test rewritten prompt"
    assert candidate.confidence == 0.85
    assert candidate.temperature == 0.5
    assert candidate.reasoning == "Test reasoning"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_rewrite_context_dataclass(system_prompt, test_email):
    """Test RewriteContext dataclass functionality"""
    mock_feedback = [type('MockFeedback', (), {'action': 'accept'})()]
    
    context = RewriteContext(
        email_scenario="professional",
        current_prompt=system_prompt,
        recent_feedback=mock_feedback,
        performance_history={"quality": 0.7},
        constraints={"max_length": 150}
    )
    
    assert context.email_scenario == "professional"
    assert context.current_prompt == system_prompt
    assert len(context.recent_feedback) == 1
    assert context.performance_history["quality"] == 0.7
    assert context.constraints["max_length"] == 150


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_llm_rewriter_configuration_parameters(mock_rewriter_llm, mock_similarity_llm, mock_reward_aggregator, mock_meta_prompt_manager):
    """Test LLM-based rewriter configuration parameters"""
    
    rewriter = LLMBasedPromptRewriter(
        rewriter_llm_provider=mock_rewriter_llm,
        similarity_llm_provider=mock_similarity_llm,
        reward_function_aggregator=mock_reward_aggregator,
        meta_prompt_manager=mock_meta_prompt_manager
    )
    
    assert rewriter.rewriter_llm == mock_rewriter_llm
    assert rewriter.similarity_llm == mock_similarity_llm
    assert rewriter.reward_aggregator == mock_reward_aggregator
    assert rewriter.meta_prompt_manager == mock_meta_prompt_manager
    assert rewriter.feedback_patterns == []