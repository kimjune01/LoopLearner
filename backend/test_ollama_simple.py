#!/usr/bin/env python3
"""
Simple standalone test for Ollama without Django dependencies
"""

import asyncio
import ollama


async def test_ollama_simple():
    """Test basic Ollama functionality without framework dependencies"""
    
    print("🚀 Testing Ollama Simple Integration...")
    
    try:
        client = ollama.Client(host="http://localhost:11434")
        
        # Test 1: Health check
        print("\n1. Health Check:")
        response = await asyncio.to_thread(
            client.chat,
            model="llama3.2:3b",
            messages=[{"role": "user", "content": "Hello! Say hi back."}],
            options={"num_predict": 20}
        )
        
        print(f"   ✅ Model response: {response['message']['content']}")
        
        # Test 2: Email draft generation
        print("\n2. Email Draft Generation:")
        
        email_prompt = """
        Generate a professional email response to this message:
        
        "Hi, I'd like to schedule a meeting to discuss the project timeline. When would be good for you?"
        
        Structure your response as:
        DRAFT:
        [Your email response]
        
        REASONING:
        1. [First reason]
        2. [Second reason]
        3. [Third reason]
        """
        
        draft_response = await asyncio.to_thread(
            client.chat,
            model="llama3.2:3b",
            messages=[
                {"role": "system", "content": "You are a professional email assistant."},
                {"role": "user", "content": email_prompt}
            ],
            options={"temperature": 0.7, "num_predict": 300}
        )
        
        print(f"   📧 Generated draft:")
        print(f"   {draft_response['message']['content']}")
        
        print("\n✅ Ollama integration working perfectly!")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_ollama_simple())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")