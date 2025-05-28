# LLM Provider Configuration Guide

## Overview

The Loop Learner system supports multiple LLM providers through a unified interface, allowing seamless switching between local and remote models for different development and production scenarios.

## Supported Providers

### 1. Ollama (Local Development) ✅ 
- **Best for**: Fast local development, no API costs, privacy
- **Model**: `llama3.2:3b` (recommended for development)
- **Setup**: Requires Ollama installed locally
- **Pros**: Fast, free, private, no rate limits
- **Cons**: Requires local resources, limited to local models

### 2. OpenAI (Production Ready) 🚀
- **Best for**: Production deployments, highest quality responses
- **Models**: `gpt-4`, `gpt-3.5-turbo`, `gpt-4-turbo`
- **Setup**: Requires OpenAI API key
- **Pros**: Excellent quality, reliable, scalable
- **Cons**: API costs, rate limits, requires internet

### 3. Anthropic (Alternative Production) 🎯
- **Best for**: Production alternative, excellent reasoning
- **Models**: `claude-3-sonnet-20240229`, `claude-3-haiku-20240307`
- **Setup**: Requires Anthropic API key
- **Pros**: Strong reasoning, safety-focused, reliable
- **Cons**: API costs, rate limits, requires internet

### 4. Mock (Testing) 🧪
- **Best for**: Unit tests, CI/CD, development without dependencies
- **Setup**: No setup required
- **Pros**: Always available, predictable, fast
- **Cons**: Not real responses, limited testing value

## Configuration

### Environment Variables

```bash
# Provider Selection
LLM_PROVIDER=ollama          # ollama, openai, anthropic, mock

# Model Configuration  
LLM_MODEL=llama3.2:3b        # Provider-specific model name
LLM_BASE_URL=localhost:11434  # For Ollama or custom endpoints
LLM_API_KEY=your-key-here     # For remote providers

# Generation Parameters
LLM_TEMPERATURE=0.7           # 0.0-1.0, creativity vs consistency
LLM_MAX_TOKENS=500           # Maximum response length
```

### Quick Setup Examples

#### Local Development (Ollama)
```bash
# .env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:3b
LLM_BASE_URL=localhost:11434
LLM_TEMPERATURE=0.7
```

#### Production (OpenAI)
```bash
# .env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_API_KEY=sk-your-openai-key
LLM_TEMPERATURE=0.5
LLM_MAX_TOKENS=800
```

#### Testing (Mock)
```bash
# .env
LLM_PROVIDER=mock
LLM_MODEL=mock-model
```

## Usage in Code

### Basic Usage
```python
from app.services.unified_llm_provider import get_llm_provider

# Get configured provider from environment
provider = get_llm_provider()

# Generate text
response = await provider.generate(
    prompt="Write a professional email response",
    system_prompt="You are a helpful assistant"
)

# Generate email drafts
drafts = await provider.generate_drafts(
    email_content="Hi, can we meet tomorrow?",
    system_prompt="You are professional and helpful",
    num_drafts=3
)
```

### Advanced Configuration
```python
from app.services.unified_llm_provider import LLMConfig, LLMProviderFactory

# Custom configuration
config = LLMConfig(
    provider="openai",
    model="gpt-4",
    api_key="your-key",
    temperature=0.3,
    max_tokens=1000
)

provider = LLMProviderFactory.create_provider(config)
```

## Performance Characteristics

| Provider | Latency | Quality | Cost | Setup |
|----------|---------|---------|------|-------|
| Ollama   | ~2-5s   | Good    | Free | Medium |
| OpenAI   | ~1-3s   | Excellent | $$$ | Easy |
| Anthropic| ~1-4s   | Excellent | $$$ | Easy |
| Mock     | ~0.1s   | N/A     | Free | None |

## Recommended Workflows

### Development Flow
1. **Start with Ollama** for rapid iteration
2. **Test with Mock** for unit tests
3. **Validate with OpenAI** before production

### Production Flow
1. **OpenAI for primary** (best quality)
2. **Anthropic as backup** (redundancy)
3. **Ollama for fallback** (self-hosted reliability)

### Testing Flow
1. **Mock for unit tests** (fast, predictable)
2. **Ollama for integration tests** (real LLM behavior)
3. **Remote providers for E2E tests** (production simulation)

## Switching Providers

### Runtime Switching
```python
# Switch provider by changing environment
import os
os.environ['LLM_PROVIDER'] = 'openai'
provider = get_llm_provider()  # Now uses OpenAI
```

### Configuration-Based Switching
```python
# Development config
dev_config = LLMConfig(provider="ollama", model="llama3.2:3b")

# Production config  
prod_config = LLMConfig(provider="openai", model="gpt-4", api_key="...")

# Use appropriate config based on environment
provider = LLMProviderFactory.create_provider(
    prod_config if IS_PRODUCTION else dev_config
)
```

## Best Practices

### Security
- **Never commit API keys** to version control
- **Use environment variables** for sensitive configuration
- **Rotate API keys regularly** in production
- **Monitor API usage** to detect anomalies

### Performance
- **Use appropriate models** for your use case
- **Set reasonable timeouts** for API calls
- **Implement retry logic** for remote providers
- **Cache responses** when appropriate

### Cost Management
- **Start with smaller models** for development
- **Monitor token usage** in production
- **Use local models** for high-volume testing
- **Implement rate limiting** to control costs

### Reliability
- **Health check providers** before use
- **Implement fallback chains** (primary → backup → local)
- **Handle errors gracefully** with meaningful messages
- **Log provider performance** for monitoring

## Troubleshooting

### Ollama Issues
```bash
# Check if Ollama is running
ollama list

# Pull model if missing
ollama pull llama3.2:3b

# Restart Ollama service
brew services restart ollama
```

### API Key Issues
```bash
# Verify API key format
echo $LLM_API_KEY | grep -E "^sk-"  # OpenAI format

# Test API connectivity
curl -H "Authorization: Bearer $LLM_API_KEY" \
     https://api.openai.com/v1/models
```

### Common Errors
- **Provider not found**: Check `LLM_PROVIDER` spelling
- **Model not available**: Verify model name for provider
- **API key invalid**: Check key format and permissions
- **Connection refused**: Verify Ollama is running (local)
- **Rate limited**: Implement exponential backoff

## Migration Guide

### From Mock to Ollama
1. Install Ollama: `brew install ollama`
2. Pull model: `ollama pull llama3.2:3b`
3. Update environment: `LLM_PROVIDER=ollama`

### From Ollama to OpenAI
1. Get OpenAI API key from platform.openai.com
2. Update environment: `LLM_PROVIDER=openai`, `LLM_API_KEY=sk-...`
3. Choose appropriate model: `LLM_MODEL=gpt-4`

### From Development to Production
1. **Review model selection** (smaller → larger)
2. **Add API monitoring** and error handling
3. **Implement rate limiting** and retry logic
4. **Set up fallback providers** for reliability
5. **Configure proper logging** and alerting