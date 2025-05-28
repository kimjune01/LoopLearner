import pytest
from datetime import datetime
from app.services.llm_provider import OpenAIProvider
from app.models.email import EmailMessage


@pytest.mark.asyncio
class TestLLMProvider:
    """Test cases for LLM provider interface"""
    
    def setup_method(self):
        self.provider = OpenAIProvider("test-api-key")
        self.test_email = EmailMessage(
            id="test-email-1",
            subject="Test Subject",
            body="Test email body",
            sender="test@example.com",
            timestamp=datetime.now()
        )
    
    async def test_generate_drafts_interface(self):
        """Test that generate_drafts method exists and has correct signature"""
        with pytest.raises(NotImplementedError):
            await self.provider.generate_drafts(
                self.test_email, 
                "test system prompt",
                {"tone": "professional"}
            )
    
    async def test_optimize_prompt_interface(self):
        """Test that optimize_prompt method exists and has correct signature"""
        with pytest.raises(NotImplementedError):
            await self.provider.optimize_prompt(
                "current prompt",
                [],
                []
            )
    
    async def test_generate_drafts_returns_list(self):
        """Test that when implemented, generate_drafts returns a list"""
        # This test will fail until implementation is complete
        # It defines the expected interface
        try:
            result = await self.provider.generate_drafts(
                self.test_email,
                "test prompt", 
                {}
            )
            assert isinstance(result, list)
            assert len(result) >= 2  # Should generate 2+ drafts
        except NotImplementedError:
            pytest.fail("generate_drafts not implemented - this test should pass when implemented")
    
    async def test_optimize_prompt_returns_string(self):
        """Test that when implemented, optimize_prompt returns a string"""
        # This test will fail until implementation is complete
        try:
            result = await self.provider.optimize_prompt("test", [], [])
            assert isinstance(result, str)
            assert len(result) > 0
        except NotImplementedError:
            pytest.fail("optimize_prompt not implemented - this test should pass when implemented")