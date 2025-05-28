import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from django.test import TestCase
from asgiref.sync import sync_to_async
from app.services.llm_provider import OpenAIProvider
from core.models import Email, SystemPrompt, UserPreference, Draft, DraftReason


@pytest.mark.django_db
@pytest.mark.asyncio
class TestLLMProvider:
    """Test cases for LLM provider interface"""
    
    async def setup_method(self):
        # Create test data
        self.system_prompt = await sync_to_async(SystemPrompt.objects.create)(
            content="You are a helpful email assistant.",
            version=1,
            is_active=True
        )
        
        self.test_email = await sync_to_async(Email.objects.create)(
            subject="Test Subject",
            body="Test email body",
            sender="test@example.com",
            scenario_type="professional"
        )
        
        self.user_prefs = [
            await sync_to_async(UserPreference.objects.create)(
                key="tone",
                value="professional",
                description="Professional communication style"
            )
        ]
        
        self.provider = OpenAIProvider("test-api-key")
    
    async def test_generate_drafts_interface(self):
        """Test that generate_drafts method exists and has correct signature"""
        # Mock the OpenAI API call
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "drafts": [
                {
                    "content": "Thank you for your email. I will review and get back to you.",
                    "reasons": [
                        {"text": "Professional tone", "confidence": 0.9},
                        {"text": "Acknowledges receipt", "confidence": 0.8}
                    ]
                },
                {
                    "content": "I appreciate you reaching out. Let me look into this and respond soon.",
                    "reasons": [
                        {"text": "Friendly but professional", "confidence": 0.8}
                    ]
                }
            ]
        }
        '''
        
        with patch.object(self.provider.client.chat.completions, 'create', return_value=mock_response):
            result = await self.provider.generate_drafts(
                self.test_email, 
                self.system_prompt,
                self.user_prefs
            )
            
            assert isinstance(result, list)
            assert len(result) >= 2
            assert all(isinstance(draft, Draft) for draft in result)
    
    async def test_optimize_prompt_interface(self):
        """Test that optimize_prompt method exists and has correct signature"""
        # Mock the OpenAI API call
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Improved system prompt based on feedback."
        
        with patch.object(self.provider.client.chat.completions, 'create', return_value=mock_response):
            result = await self.provider.optimize_prompt(
                self.system_prompt,
                [],
                []
            )
            
            assert isinstance(result, str)
            assert len(result) > 0
    
    async def test_generate_drafts_returns_list(self):
        """Test that generate_drafts returns a list of Draft objects"""
        # Mock the OpenAI API call with valid JSON
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "drafts": [
                {
                    "content": "First draft response",
                    "reasons": [
                        {"text": "Clear and concise", "confidence": 0.9}
                    ]
                },
                {
                    "content": "Second draft response", 
                    "reasons": [
                        {"text": "Professional tone", "confidence": 0.8}
                    ]
                }
            ]
        }
        '''
        
        with patch.object(self.provider.client.chat.completions, 'create', return_value=mock_response):
            result = await self.provider.generate_drafts(
                self.test_email,
                self.system_prompt, 
                self.user_prefs
            )
            
            assert isinstance(result, list)
            assert len(result) >= 2
            
            # Check that Draft objects were created
            for draft in result:
                assert isinstance(draft, Draft)
                assert draft.email == self.test_email
                assert draft.system_prompt == self.system_prompt
                assert len(draft.content) > 0
    
    async def test_optimize_prompt_returns_string(self):
        """Test that optimize_prompt returns a string"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "You are an improved email assistant that incorporates user feedback."
        
        with patch.object(self.provider.client.chat.completions, 'create', return_value=mock_response):
            result = await self.provider.optimize_prompt(self.system_prompt, [], [])
            
            assert isinstance(result, str)
            assert len(result) > 0
            assert "improved" in result.lower()