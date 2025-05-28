#!/usr/bin/env python3
"""
Test comprehensive draft generation functionality with Ollama
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.simple_llm_provider import SimpleOllamaProvider


async def test_draft_generation():
    """Test comprehensive draft generation functionality"""
    
    print("🚀 Testing Comprehensive Draft Generation...")
    
    # Initialize provider
    ollama = SimpleOllamaProvider()
    
    # Test health check first
    print("\n1. Health Check:")
    health = await ollama.health_check()
    print(f"   Status: {health['status']}")
    
    if health['status'] != 'healthy':
        print(f"   ❌ Error: {health.get('error', 'Unknown error')}")
        return False
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Professional Meeting Request",
            "email": """
Subject: Project Timeline Discussion

Hi there,

I hope this email finds you well. I wanted to reach out regarding the upcoming product launch timeline we discussed last week. 

There have been some changes to our development schedule, and I think it would be beneficial for us to meet and realign our expectations. Would you be available for a 30-minute call this Thursday or Friday afternoon?

Please let me know what works best for your schedule.

Best regards,
Sarah Johnson
Product Manager
            """,
            "system_prompt": "You are a professional email assistant. Generate helpful, courteous responses.",
            "preferences": [
                {"key": "tone", "value": "professional", "is_active": True},
                {"key": "length", "value": "concise", "is_active": True}
            ],
            "constraints": {
                "max_length": 200,
                "include_signature": True
            }
        },
        {
            "name": "Customer Support Inquiry",
            "email": """
Subject: Issue with Recent Order

Hello,

I placed an order last week (Order #12345) and haven't received a tracking number yet. The estimated delivery was supposed to be today, but I haven't heard anything.

Can you please check on the status of my order and let me know when I can expect to receive it?

Thanks,
Mike Chen
            """,
            "system_prompt": "You are a helpful customer service representative. Be empathetic and solution-focused.",
            "preferences": [
                {"key": "tone", "value": "helpful", "is_active": True},
                {"key": "empathy", "value": "high", "is_active": True}
            ],
            "constraints": {
                "max_length": 150,
                "include_next_steps": True
            }
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i+1}. Testing Scenario: {scenario['name']}")
        print("="*50)
        
        # Generate drafts
        drafts = await ollama.generate_drafts(
            email_content=scenario['email'],
            system_prompt=scenario['system_prompt'],
            user_preferences=scenario['preferences'],
            constraints=scenario['constraints'],
            num_drafts=3
        )
        
        # Display results
        for j, draft in enumerate(drafts, 1):
            print(f"\n   Draft {j} (Confidence: {draft['confidence']:.2f}):")
            print(f"   Content: {draft['content']}")
            print(f"   Reasoning:")
            for k, reason in enumerate(draft['reasoning'], 1):
                print(f"      {k}. {reason}")
            print()
    
    # Test error handling
    print(f"\n{len(test_scenarios)+2}. Testing Error Handling:")
    print("="*50)
    
    try:
        # Test with empty email
        drafts = await ollama.generate_drafts(
            email_content="",
            system_prompt="You are helpful.",
            num_drafts=1
        )
        print(f"   ✅ Handled empty email gracefully")
        print(f"   Response: {drafts[0]['content'][:100]}...")
    except Exception as e:
        print(f"   ❌ Error handling failed: {e}")
    
    # Performance test
    print(f"\n{len(test_scenarios)+3}. Performance Test:")
    print("="*50)
    
    import time
    start_time = time.time()
    
    quick_drafts = await ollama.generate_drafts(
        email_content="Hi, thanks for your email. Can we schedule a quick call?",
        system_prompt="Be brief and professional.",
        num_drafts=2
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"   ⏱️  Generated 2 drafts in {duration:.2f} seconds")
    print(f"   📊 Average per draft: {duration/2:.2f} seconds")
    
    if duration > 30:  # More than 30 seconds total
        print(f"   ⚠️  Performance slower than expected")
    else:
        print(f"   ✅ Performance within acceptable range")
    
    print("\n✅ Draft generation test completed successfully!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_draft_generation())
    print(f"\nOverall Test Result: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)