#!/usr/bin/env python3
"""
Quick test script to verify Ollama integration works
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ollama_provider import OllamaProvider


async def test_ollama_integration():
    """Test basic Ollama functionality"""
    
    print("🚀 Testing Ollama Integration...")
    
    # Initialize provider
    ollama = OllamaProvider()
    
    # Test 1: Health check
    print("\n1. Health Check:")
    health = await ollama.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Model: {health['model']}")
    
    if health['status'] != 'healthy':
        print(f"   ❌ Error: {health.get('error', 'Unknown error')}")
        return False
    
    # Test 2: Simple generation
    print("\n2. Simple Generation:")
    response = await ollama.generate(
        prompt="Write a brief professional greeting.",
        temperature=0.7,
        max_tokens=50
    )
    print(f"   Response: {response}")
    
    # Test 3: Draft generation
    print("\n3. Draft Generation:")
    sample_email = """
    Subject: Meeting Request
    
    Hi,
    
    I'd like to schedule a meeting to discuss the upcoming project timeline.
    When would be a good time for you this week?
    
    Best regards,
    John
    """
    
    system_prompt = "You are a helpful email assistant. Generate professional, concise responses."
    
    drafts = await ollama.generate_drafts(
        email_content=sample_email,
        system_prompt=system_prompt,
        num_drafts=2
    )
    
    for i, draft in enumerate(drafts, 1):
        print(f"\n   Draft {i}:")
        print(f"   Content: {draft['content'][:100]}...")
        print(f"   Reasoning: {draft['reasoning']}")
        print(f"   Confidence: {draft['confidence']}")
    
    # Test 4: Response evaluation
    print("\n4. Response Evaluation:")
    evaluation = await ollama.evaluate_response_quality(
        original_email=sample_email,
        generated_response=drafts[0]['content']
    )
    
    for criterion, score in evaluation.items():
        print(f"   {criterion}: {score:.2f}")
    
    print("\n✅ Ollama integration test completed successfully!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_ollama_integration())
    sys.exit(0 if success else 1)