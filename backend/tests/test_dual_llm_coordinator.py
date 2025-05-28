import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from asgiref.sync import sync_to_async
from app.services.dual_llm_coordinator import (
    DualLLMCoordinator,
    LLMConfiguration,
    DraftGenerationRequest,
    DraftGenerationResult,
    OpenAITaskLLM,
    TaskLLMProvider
)
from core.models import SystemPrompt, Email, Draft


@pytest_asyncio.fixture
async def mock_prompt_rewriter():
    """Mock prompt rewriter"""
    mock_rewriter = AsyncMock()
    mock_rewriter.rewrite_prompt = AsyncMock()
    mock_rewriter.select_best_candidate = AsyncMock()
    mock_rewriter.update_from_feedback = AsyncMock()
    return mock_rewriter


@pytest_asyncio.fixture
async def mock_task_llm():
    """Mock task LLM provider"""
    mock_llm = AsyncMock()
    mock_llm.generate_drafts = AsyncMock()
    mock_llm.evaluate_response_quality = AsyncMock()
    return mock_llm


@pytest_asyncio.fixture
async def mock_reward_aggregator():
    """Mock reward aggregator"""
    mock_aggregator = AsyncMock()
    mock_aggregator.compute_reward = AsyncMock(return_value=0.8)
    return mock_aggregator


@pytest_asyncio.fixture
async def mock_meta_prompt_manager():
    """Mock meta-prompt manager"""
    mock_manager = AsyncMock()
    mock_manager.optimize_template_selection = AsyncMock()
    return mock_manager


@pytest_asyncio.fixture
async def system_prompt():
    """Test system prompt"""
    prompt, created = await sync_to_async(SystemPrompt.objects.get_or_create)(
        version=30,  # Use different version to avoid conflicts
        defaults={
            'content': "You are a helpful coordinator test assistant.",
            'is_active': True
        }
    )
    return prompt


@pytest_asyncio.fixture
async def test_email():
    """Test email for draft generation"""
    return await sync_to_async(Email.objects.create)(
        subject="Coordinator Test Email",
        body="This is a test email for the dual-LLM coordinator.",
        sender="coordinator@test.com",
        scenario_type="professional"
    )


@pytest_asyncio.fixture
async def test_draft(test_email, system_prompt):
    """Test draft for evaluation"""
    return await sync_to_async(Draft.objects.create)(
        email=test_email,
        content="This is a test draft response.",
        system_prompt=system_prompt
    )


@pytest_asyncio.fixture
def llm_config():
    """Test LLM configuration"""
    return LLMConfiguration(
        provider_type="openai",
        model_name="gpt-4",
        api_key="test-key",
        max_tokens=1024,
        temperature=0.7
    )


@pytest_asyncio.fixture
def draft_request(test_email, system_prompt):
    """Test draft generation request"""
    return DraftGenerationRequest(
        email=test_email,
        prompt=system_prompt,
        user_preferences=[
            {"key": "tone", "value": "professional", "is_active": True}
        ],
        constraints={"max_length": 200}
    )


@pytest_asyncio.fixture
def coordinator(mock_prompt_rewriter, mock_task_llm, mock_reward_aggregator, mock_meta_prompt_manager):
    """Dual-LLM coordinator instance"""
    return DualLLMCoordinator(
        prompt_rewriter=mock_prompt_rewriter,
        task_llm=mock_task_llm,
        reward_aggregator=mock_reward_aggregator,
        meta_prompt_manager=mock_meta_prompt_manager,
        auto_rewrite=True,
        rewrite_threshold=0.6
    )


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_llm_configuration_dataclass(llm_config):
    """Test LLM configuration dataclass"""
    assert llm_config.provider_type == "openai"
    assert llm_config.model_name == "gpt-4"
    assert llm_config.api_key == "test-key"
    assert llm_config.max_tokens == 1024
    assert llm_config.temperature == 0.7
    assert llm_config.timeout == 30  # Default value


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_draft_generation_request_dataclass(draft_request, test_email, system_prompt):
    """Test draft generation request dataclass"""
    assert draft_request.email == test_email
    assert draft_request.prompt == system_prompt
    assert len(draft_request.user_preferences) == 1
    assert draft_request.user_preferences[0]["key"] == "tone"
    assert draft_request.constraints["max_length"] == 200


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_openai_task_llm_implements_interface():
    """Test that OpenAITaskLLM implements TaskLLMProvider interface"""
    config = LLMConfiguration(provider_type="openai", model_name="gpt-4")
    mock_llm_provider = MagicMock()
    
    task_llm = OpenAITaskLLM(config, mock_llm_provider)
    
    assert isinstance(task_llm, TaskLLMProvider)
    assert hasattr(task_llm, 'generate_drafts')
    assert hasattr(task_llm, 'evaluate_response_quality')


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_openai_task_llm_generate_drafts(test_email, system_prompt):
    """Test OpenAI task LLM draft generation"""
    mock_llm_provider = AsyncMock()
    mock_llm_provider.generate_drafts = AsyncMock(return_value=[])
    
    config = LLMConfiguration(provider_type="openai", model_name="gpt-4")
    task_llm = OpenAITaskLLM(config, mock_llm_provider)
    
    user_preferences = [{"key": "tone", "value": "professional", "is_active": True}]
    
    drafts = await task_llm.generate_drafts(
        test_email, 
        system_prompt, 
        user_preferences, 
        num_drafts=3
    )
    
    # Verify LLM provider was called
    mock_llm_provider.generate_drafts.assert_called_once()
    
    # Verify preference conversion
    call_args = mock_llm_provider.generate_drafts.call_args[0]
    assert call_args[0] == test_email
    assert call_args[1] == system_prompt
    # Third argument should be converted preference objects
    pref_objects = call_args[2]
    assert len(pref_objects) == 1
    assert pref_objects[0].key == "tone"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_openai_task_llm_evaluate_quality(test_email, llm_config):
    """Test OpenAI task LLM response quality evaluation"""
    mock_llm_provider = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"relevance": 0.8, "clarity": 0.9, "professionalism": 0.7, "completeness": 0.8}'
    
    mock_llm_provider.client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    task_llm = OpenAITaskLLM(llm_config, mock_llm_provider)
    
    scores = await task_llm.evaluate_response_quality(
        test_email,
        "Test response content",
        {"relevance": "How relevant?", "clarity": "How clear?"}
    )
    
    assert "relevance" in scores
    assert "clarity" in scores
    assert "professionalism" in scores
    assert "completeness" in scores
    assert 0.0 <= scores["relevance"] <= 1.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_coordinator_initialization(coordinator):
    """Test dual-LLM coordinator initialization"""
    assert coordinator.auto_rewrite is True
    assert coordinator.rewrite_threshold == 0.6
    assert coordinator.performance_history == {}
    assert coordinator.prompt_rewriter is not None
    assert coordinator.task_llm is not None


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_generate_drafts_without_rewrite(coordinator, draft_request, test_draft):
    """Test draft generation without prompt rewriting"""
    # Setup mocks
    coordinator.task_llm.generate_drafts.return_value = [test_draft]
    coordinator.task_llm.evaluate_response_quality.return_value = {
        "relevance": 0.8, "clarity": 0.9, "professionalism": 0.7, "completeness": 0.8
    }
    
    # Disable auto-rewrite
    coordinator.auto_rewrite = False
    
    result = await coordinator.generate_drafts_with_optimization(draft_request)
    
    # Verify result
    assert isinstance(result, DraftGenerationResult)
    assert result.drafts == [test_draft]
    assert result.prompt_used == draft_request.prompt
    assert result.original_prompt == draft_request.prompt
    assert result.rewrite_applied is False
    assert result.rewrite_reasoning is None
    assert result.performance_metrics is not None


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_generate_drafts_with_rewrite(coordinator, draft_request, test_draft, system_prompt):
    """Test draft generation with prompt rewriting"""
    # Setup rewrite mocks
    mock_candidate = type('MockCandidate', (), {
        'content': 'Rewritten prompt content',
        'confidence': 0.9,
        'reasoning': 'Improved for better performance'
    })()
    
    coordinator.prompt_rewriter.rewrite_prompt.return_value = [mock_candidate]
    coordinator.prompt_rewriter.select_best_candidate.return_value = mock_candidate
    
    # Setup new prompt creation mock
    with patch('app.services.dual_llm_coordinator.sync_to_async') as mock_sync_to_async:
        # Mock the SystemPrompt.objects.create call
        mock_create_prompt = AsyncMock(return_value=system_prompt)
        mock_sync_to_async.return_value = mock_create_prompt
        
        # Mock other sync_to_async calls
        mock_sync_to_async.side_effect = [
            mock_create_prompt,  # For SystemPrompt.objects.create
            AsyncMock(return_value={"max_version": 30})  # For aggregate query
        ]
        
        coordinator.task_llm.generate_drafts.return_value = [test_draft]
        coordinator.task_llm.evaluate_response_quality.return_value = {
            "relevance": 0.8, "clarity": 0.9, "professionalism": 0.7, "completeness": 0.8
        }
        
        # Force rewrite by setting low performance history
        coordinator.performance_history[f"{draft_request.email.scenario_type}_{draft_request.prompt.id}"] = [0.3, 0.4, 0.5]
        
        result = await coordinator.generate_drafts_with_optimization(draft_request)
        
        # Verify rewrite was attempted
        coordinator.prompt_rewriter.rewrite_prompt.assert_called_once()
        assert result.rewrite_applied is True
        assert result.rewrite_reasoning == 'Improved for better performance'


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_should_rewrite_prompt_new_scenario(coordinator, draft_request):
    """Test rewrite decision for new scenario/prompt combination"""
    # No performance history - should rewrite
    should_rewrite = await coordinator._should_rewrite_prompt(draft_request)
    assert should_rewrite is True


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_should_rewrite_prompt_poor_performance(coordinator, draft_request):
    """Test rewrite decision for poor performing prompt"""
    # Add poor performance history
    key = f"{draft_request.email.scenario_type}_{draft_request.prompt.id}"
    coordinator.performance_history[key] = [0.3, 0.4, 0.5, 0.4, 0.3]
    
    should_rewrite = await coordinator._should_rewrite_prompt(draft_request)
    assert should_rewrite is True  # Average 0.38 < threshold 0.6


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_should_rewrite_prompt_good_performance(coordinator, draft_request):
    """Test rewrite decision for well-performing prompt"""
    # Add good performance history
    key = f"{draft_request.email.scenario_type}_{draft_request.prompt.id}"
    coordinator.performance_history[key] = [0.8, 0.9, 0.85, 0.9, 0.8]
    
    should_rewrite = await coordinator._should_rewrite_prompt(draft_request)
    assert should_rewrite is False  # Average 0.85 > threshold 0.6


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_evaluate_generation_performance(coordinator, test_email, test_draft, system_prompt):
    """Test evaluation of draft generation performance"""
    coordinator.task_llm.evaluate_response_quality.return_value = {
        "relevance": 0.8,
        "clarity": 0.9,
        "professionalism": 0.7,
        "completeness": 0.8
    }
    
    metrics = await coordinator._evaluate_generation_performance(
        test_email,
        [test_draft],
        system_prompt
    )
    
    assert "overall_quality" in metrics
    assert "best_draft_quality" in metrics
    assert "consistency" in metrics
    assert "num_drafts" in metrics
    
    assert metrics["num_drafts"] == 1
    assert 0.0 <= metrics["overall_quality"] <= 1.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_update_performance_history(coordinator):
    """Test updating performance history"""
    scenario = "professional"
    prompt_id = 123
    metrics = {"overall_quality": 0.85}
    
    coordinator._update_performance_history(scenario, prompt_id, metrics, False)
    
    key = f"{scenario}_{prompt_id}"
    assert key in coordinator.performance_history
    assert coordinator.performance_history[key] == [0.85]


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_performance_history_size_limit(coordinator):
    """Test that performance history is limited in size"""
    scenario = "professional"
    prompt_id = 123
    
    # Add 25 entries (should keep only last 20)
    for i in range(25):
        metrics = {"overall_quality": i / 25.0}
        coordinator._update_performance_history(scenario, prompt_id, metrics, False)
    
    key = f"{scenario}_{prompt_id}"
    assert len(coordinator.performance_history[key]) == 20
    # Should keep the most recent entries
    assert coordinator.performance_history[key][-1] == 24 / 25.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_process_user_feedback(coordinator, system_prompt, test_draft):
    """Test processing user feedback for improvement"""
    # Create mock feedback
    mock_feedback = type('MockFeedback', (), {
        'action': 'accept',
        'reason': 'Good response'
    })()
    
    # Create mock generation result
    mock_result = DraftGenerationResult(
        drafts=[test_draft],
        prompt_used=system_prompt,
        original_prompt=system_prompt,
        rewrite_applied=True,
        performance_metrics={"overall_quality": 0.8}
    )
    
    await coordinator.process_user_feedback(
        system_prompt,
        system_prompt,  # Rewritten prompt (same for test)
        mock_feedback,
        mock_result
    )
    
    # Verify feedback was processed
    coordinator.prompt_rewriter.update_from_feedback.assert_called_once()
    coordinator.meta_prompt_manager.optimize_template_selection.assert_called_once()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_get_coordination_metrics_empty(coordinator):
    """Test coordination metrics with no data"""
    metrics = await coordinator.get_coordination_metrics()
    
    assert metrics["total_scenarios"] == 0
    assert metrics["average_performance"] == 0.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_get_coordination_metrics_with_data(coordinator):
    """Test coordination metrics with performance data"""
    # Add performance history
    coordinator.performance_history = {
        "professional_1": [0.8, 0.9, 0.7],
        "casual_2": [0.6, 0.5, 0.4],  # Below threshold
        "complaint_3": [0.9, 0.8, 0.85]
    }
    
    metrics = await coordinator.get_coordination_metrics()
    
    assert metrics["total_scenarios"] == 3
    assert 0.0 <= metrics["average_performance"] <= 1.0
    assert metrics["scenarios_needing_improvement"] == 1  # casual_2
    assert metrics["rewrite_threshold"] == 0.6
    assert metrics["auto_rewrite_enabled"] is True


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_configure_rewriting(coordinator):
    """Test configuring rewriting behavior"""
    coordinator.configure_rewriting(auto_rewrite=False, rewrite_threshold=0.8)
    
    assert coordinator.auto_rewrite is False
    assert coordinator.rewrite_threshold == 0.8


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_configure_rewriting_bounds_checking(coordinator):
    """Test rewriting configuration bounds checking"""
    # Test threshold bounds
    coordinator.configure_rewriting(auto_rewrite=True, rewrite_threshold=-0.5)
    assert coordinator.rewrite_threshold == 0.0  # Bounded to 0.0
    
    coordinator.configure_rewriting(auto_rewrite=True, rewrite_threshold=1.5)
    assert coordinator.rewrite_threshold == 1.0  # Bounded to 1.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_draft_generation_result_dataclass(test_draft, system_prompt):
    """Test DraftGenerationResult dataclass"""
    result = DraftGenerationResult(
        drafts=[test_draft],
        prompt_used=system_prompt,
        original_prompt=system_prompt,
        rewrite_applied=True,
        rewrite_reasoning="Improved performance",
        performance_metrics={"quality": 0.8}
    )
    
    assert result.drafts == [test_draft]
    assert result.prompt_used == system_prompt
    assert result.original_prompt == system_prompt
    assert result.rewrite_applied is True
    assert result.rewrite_reasoning == "Improved performance"
    assert result.performance_metrics["quality"] == 0.8


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_error_handling_in_rewrite_process(coordinator, draft_request, test_draft):
    """Test error handling during rewrite process"""
    # Make rewriter fail
    coordinator.prompt_rewriter.rewrite_prompt.side_effect = Exception("Rewrite failed")
    
    coordinator.task_llm.generate_drafts.return_value = [test_draft]
    coordinator.task_llm.evaluate_response_quality.return_value = {"overall": 0.7}
    
    # Should still complete without rewriting
    result = await coordinator.generate_drafts_with_optimization(draft_request)
    
    assert result.rewrite_applied is False
    assert result.prompt_used == draft_request.prompt  # Original prompt used
    assert len(result.drafts) == 1