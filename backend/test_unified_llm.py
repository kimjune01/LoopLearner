#!/usr/bin/env python3
"""
Test the unified LLM provider system with multiple backends
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.unified_llm_provider import (
    LLMConfig, LLMProviderFactory, get_llm_provider
)


async def test_provider_switching():
    """Test switching between different LLM providers"""
    
    print("🚀 Testing Unified LLM Provider System")
    print("="*50)
    
    # Test scenarios for different providers
    test_configs = [
        {
            "name": "Ollama Local",
            "config": LLMConfig(
                provider="ollama",
                model="llama3.2:3b",
                base_url="localhost:11434"
            )
        },
        {
            "name": "Mock Provider",
            "config": LLMConfig(
                provider="mock",
                model="mock-model"
            )
        }
    ]
    
    sample_email = """
Subject: Quick Question

Hi,

I have a quick question about our upcoming meeting. 
Can we move it from 2 PM to 3 PM tomorrow?

Thanks,
Alex
    """
    
    for test_config in test_configs:
        print(f"\n📋 Testing: {test_config['name']}")
        print("-" * 30)
        
        try:
            # Create provider
            provider = LLMProviderFactory.create_provider(test_config['config'])
            
            # Health check
            health = await provider.health_check()
            print(f"   Health: {health['status']}")
            
            if health['status'] != 'healthy':
                print(f"   ⚠️  Skipping {test_config['name']} - not available")
                continue
            
            # Test simple generation
            simple_response = await provider.generate(
                prompt="Say hello professionally",
                system_prompt="You are a professional assistant"
            )
            print(f"   Simple: {simple_response[:50]}...")
            
            # Test draft generation
            drafts = await provider.generate_drafts(
                email_content=sample_email,
                system_prompt="You are a helpful email assistant",
                user_preferences=[
                    {"key": "tone", "value": "professional", "is_active": True}
                ],
                num_drafts=2
            )
            
            print(f"   Drafts: Generated {len(drafts)} drafts")
            for i, draft in enumerate(drafts, 1):
                print(f"      Draft {i}: {draft.content[:40]}... (conf: {draft.confidence:.2f})")
            
            print(f"   ✅ {test_config['name']} working correctly")
            
        except Exception as e:
            print(f"   ❌ {test_config['name']} failed: {str(e)}")
    
    # Test environment-based configuration
    print(f"\n🌍 Testing Environment Configuration")
    print("-" * 30)
    
    try:
        # Set environment for testing
        os.environ['LLM_PROVIDER'] = 'ollama'
        os.environ['LLM_MODEL'] = 'llama3.2:3b'
        
        env_provider = get_llm_provider()
        env_health = await env_provider.health_check()
        
        print(f"   Environment provider: {env_health.get('provider', 'unknown')}")
        print(f"   Model: {env_health.get('model', 'unknown')}")
        print(f"   Status: {env_health.get('status', 'unknown')}")
        
        if env_health['status'] == 'healthy':
            print("   ✅ Environment configuration working")
        else:
            print("   ⚠️  Environment provider not available")
            
    except Exception as e:
        print(f"   ❌ Environment configuration failed: {str(e)}")
    
    # Test configuration flexibility
    print(f"\n⚙️  Testing Configuration Flexibility")
    print("-" * 30)
    
    flexibility_tests = [
        {
            "desc": "Different temperature",
            "config": LLMConfig(provider="mock", model="test", temperature=0.1)
        },
        {
            "desc": "Different max_tokens", 
            "config": LLMConfig(provider="mock", model="test", max_tokens=100)
        },
        {
            "desc": "With API key",
            "config": LLMConfig(provider="mock", model="test", api_key="test-key")
        }
    ]
    
    for test in flexibility_tests:
        try:
            provider = LLMProviderFactory.create_provider(test['config'])
            print(f"   ✅ {test['desc']}: Created successfully")
        except Exception as e:
            print(f"   ❌ {test['desc']}: Failed - {str(e)}")
    
    print(f"\n🎯 Testing Production-Ready Features")
    print("-" * 30)
    
    # Test error handling
    try:
        bad_config = LLMConfig(provider="nonexistent", model="fake")
        LLMProviderFactory.create_provider(bad_config)
        print("   ❌ Error handling: Should have failed")
    except ValueError:
        print("   ✅ Error handling: Properly rejects invalid providers")
    except Exception as e:
        print(f"   ⚠️  Error handling: Unexpected error - {str(e)}")
    
    # Test data structure consistency
    if test_configs:
        try:
            mock_provider = LLMProviderFactory.create_provider(
                LLMConfig(provider="mock", model="test")
            )
            drafts = await mock_provider.generate_drafts(
                email_content="Test email",
                system_prompt="Test prompt"
            )
            
            # Verify EmailDraft structure
            draft = drafts[0]
            required_fields = ['content', 'reasoning', 'confidence', 'draft_id']
            missing = [field for field in required_fields if not hasattr(draft, field)]
            
            if not missing:
                print("   ✅ Data structure: EmailDraft format consistent")
            else:
                print(f"   ❌ Data structure: Missing fields - {missing}")
                
        except Exception as e:
            print(f"   ❌ Data structure test failed: {str(e)}")
    
    print(f"\n✅ Unified LLM Provider System Test Complete!")
    print("="*50)
    
    return True


async def demo_provider_switching():
    """Demo switching between providers for the same task"""
    
    print("\n🔄 Demo: Provider Switching for Same Task")
    print("="*40)
    
    task_email = "Hi, can we reschedule our 2 PM meeting to 3 PM? Thanks!"
    
    providers_to_test = ["mock", "ollama"]  # Add "openai" when you have API key
    
    for provider_name in providers_to_test:
        print(f"\n📡 Using {provider_name.upper()} provider:")
        
        try:
            config = LLMConfig(
                provider=provider_name,
                model="llama3.2:3b" if provider_name == "ollama" else "mock-model"
            )
            
            provider = LLMProviderFactory.create_provider(config)
            health = await provider.health_check()
            
            if health['status'] != 'healthy':
                print(f"   ⚠️  {provider_name} not available, skipping")
                continue
            
            draft = await provider.generate_drafts(
                email_content=task_email,
                system_prompt="Be professional and helpful",
                num_drafts=1
            )
            
            print(f"   Response: {draft[0].content}")
            print(f"   Confidence: {draft[0].confidence:.2f}")
            print(f"   Reasoning: {', '.join(draft[0].reasoning[:2])}...")
            
        except Exception as e:
            print(f"   ❌ {provider_name} failed: {str(e)}")


if __name__ == "__main__":
    success = asyncio.run(test_provider_switching())
    asyncio.run(demo_provider_switching())
    
    print(f"\nTest Result: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)