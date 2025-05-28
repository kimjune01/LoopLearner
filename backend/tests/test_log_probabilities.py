import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.unified_llm_provider import LLMConfig, LLMProviderFactory, OpenAIProvider, OllamaProvider, MockProvider


@pytest_asyncio.fixture
async def openai_config():
    """OpenAI provider configuration"""
    return LLMConfig(
        provider="openai",
        model="gpt-4o-mini",
        api_key="test-key"
    )


@pytest_asyncio.fixture
async def ollama_config():
    """Ollama provider configuration"""
    return LLMConfig(
        provider="ollama",
        model="llama3.2:3b"
    )


@pytest_asyncio.fixture
async def mock_config():
    """Mock provider configuration"""
    return LLMConfig(
        provider="mock",
        model="test-model"
    )


@pytest.mark.asyncio
async def test_mock_provider_log_probabilities(mock_config):
    """Test mock provider log probabilities implementation"""
    provider = LLMProviderFactory.create_provider(mock_config)
    
    # Test basic functionality
    log_probs = await provider.get_log_probabilities("Hello world test")
    
    assert isinstance(log_probs, list)
    assert len(log_probs) == 3  # Three words
    assert all(isinstance(p, float) for p in log_probs)
    assert all(p < 0 for p in log_probs)  # Log probabilities should be negative
    
    # Test word characteristic recognition
    common_word_logprob = await provider.get_log_probabilities("the")
    technical_word_logprob = await provider.get_log_probabilities("TechnicalTerm")
    
    # Common words should have higher probability (less negative log prob)
    assert common_word_logprob[0] > technical_word_logprob[0]


@pytest.mark.asyncio
async def test_openai_provider_log_probabilities_with_mock(openai_config):
    """Test OpenAI provider log probabilities with mocked API"""
    
    # Mock the OpenAI client
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].logprobs = MagicMock()
    mock_response.choices[0].logprobs.content = [
        MagicMock(logprob=-1.5),
        MagicMock(logprob=-2.1),
        MagicMock(logprob=-3.0)
    ]
    mock_client.chat.completions.create.return_value = mock_response
    
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_openai.return_value = mock_client
        
        provider = OpenAIProvider(openai_config)
        log_probs = await provider.get_log_probabilities("Hello world test")
        
        assert log_probs == [-1.5, -2.1, -3.0]
        assert mock_client.chat.completions.create.called
        
        # Verify logprobs=True was passed
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['logprobs'] is True


@pytest.mark.asyncio
async def test_openai_provider_fallback_estimation(openai_config):
    """Test OpenAI provider fallback to estimation when API fails"""
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_openai.return_value = mock_client
        
        provider = OpenAIProvider(openai_config)
        log_probs = await provider.get_log_probabilities("Hello world")
        
        # Should fallback to estimation
        assert isinstance(log_probs, list)
        assert len(log_probs) == 2
        assert all(isinstance(p, float) for p in log_probs)


@pytest.mark.asyncio
async def test_ollama_provider_log_probabilities_with_mock(ollama_config):
    """Test Ollama provider log probabilities with mocked responses"""
    
    with patch('ollama.Client') as mock_ollama:
        provider = OllamaProvider(ollama_config)
        
        # Mock the generate method to return likelihood scores
        provider.generate = AsyncMock(return_value="[0.8, 0.6, 0.9]")
        
        log_probs = await provider.get_log_probabilities("Hello world test")
        
        assert isinstance(log_probs, list)
        assert len(log_probs) == 3
        
        # Verify conversion from likelihood to log probability
        import math
        expected_log_probs = [math.log(0.8), math.log(0.6), math.log(0.9)]
        assert log_probs == expected_log_probs


@pytest.mark.asyncio
async def test_ollama_provider_fallback_estimation(ollama_config):
    """Test Ollama provider fallback when LLM response parsing fails"""
    
    with patch('ollama.Client') as mock_ollama:
        provider = OllamaProvider(ollama_config)
        
        # Mock generate to return unparseable response
        provider.generate = AsyncMock(return_value="This is not JSON")
        
        log_probs = await provider.get_log_probabilities("Hello world")
        
        # Should fallback to estimation
        assert isinstance(log_probs, list)
        assert len(log_probs) == 2
        assert all(isinstance(p, float) for p in log_probs)


@pytest.mark.asyncio
async def test_log_probabilities_with_context():
    """Test log probabilities calculation with context"""
    provider = LLMProviderFactory.create_provider(LLMConfig(provider="mock", model="test"))
    
    # Test with context
    log_probs_with_context = await provider.get_log_probabilities(
        "professional response", 
        context="Please write a"
    )
    
    # Test without context
    log_probs_without_context = await provider.get_log_probabilities("professional response")
    
    assert isinstance(log_probs_with_context, list)
    assert isinstance(log_probs_without_context, list)
    assert len(log_probs_with_context) == len(log_probs_without_context)


@pytest.mark.asyncio
async def test_perplexity_calculation_from_log_probabilities():
    """Test perplexity calculation using log probabilities"""
    provider = LLMProviderFactory.create_provider(LLMConfig(provider="mock", model="test"))
    
    text = "This is a natural sentence"
    log_probs = await provider.get_log_probabilities(text)
    
    # Calculate perplexity
    import math
    mean_log_prob = sum(log_probs) / len(log_probs)
    perplexity = math.exp(-mean_log_prob)
    
    assert isinstance(perplexity, float)
    assert perplexity > 0
    
    # Perplexity should be reasonable (not extremely high or low)
    assert 1.0 < perplexity < 100.0


@pytest.mark.asyncio
async def test_log_probabilities_consistency():
    """Test that log probabilities are consistent across calls"""
    provider = LLMProviderFactory.create_provider(LLMConfig(provider="mock", model="test"))
    
    text = "Consistent test text"
    
    # Multiple calls should return same results for mock provider
    log_probs_1 = await provider.get_log_probabilities(text)
    log_probs_2 = await provider.get_log_probabilities(text)
    
    assert log_probs_1 == log_probs_2


@pytest.mark.asyncio
async def test_empty_text_handling():
    """Test handling of edge cases like empty text"""
    provider = LLMProviderFactory.create_provider(LLMConfig(provider="mock", model="test"))
    
    # Empty string
    log_probs = await provider.get_log_probabilities("")
    assert log_probs == []
    
    # Single word
    log_probs = await provider.get_log_probabilities("word")
    assert len(log_probs) == 1
    
    # Whitespace only
    log_probs = await provider.get_log_probabilities("   ")
    assert isinstance(log_probs, list)