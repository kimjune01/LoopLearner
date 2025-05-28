import pytest
from unittest.mock import MagicMock, patch
from django.test import TestCase
from asgiref.sync import sync_to_async
from app.services.optimizer import LLMBasedOptimizer
from app.services.llm_provider import OpenAIProvider
from core.models import SystemPrompt, EvaluationSnapshot, Email, UserFeedback, Draft


@pytest.mark.django_db
@pytest.mark.asyncio
class TestPromptOptimizer:
    """Test cases for prompt optimizer interface"""
    
    async def setup_method(self):
        # Create mock LLM provider
        self.mock_llm = OpenAIProvider("test-api-key")
        self.optimizer = LLMBasedOptimizer(self.mock_llm)
        
        # Create test data
        self.current_prompt = await sync_to_async(SystemPrompt.objects.create)(
            content="You are a helpful email assistant.",
            version=1,
            is_active=True
        )
        
        self.test_email = await sync_to_async(Email.objects.create)(
            subject="Test Email",
            body="Test body",
            sender="test@example.com",
            scenario_type="professional"
        )
    
    async def test_optimize_prompt_interface(self):
        """Test that optimize_prompt method exists"""
        # Mock the LLM provider's optimize_prompt method
        mock_response = "You are an improved email assistant that considers user feedback."
        
        with patch.object(self.mock_llm, 'optimize_prompt', return_value=mock_response):
            result = await self.optimizer.optimize_prompt(self.current_prompt, [], [])
            
            assert isinstance(result, SystemPrompt)
            assert result.version > self.current_prompt.version
            assert result.content != self.current_prompt.content
    
    async def test_evaluate_prompt_interface(self):
        """Test that evaluate_prompt method exists"""
        # Create test evaluation snapshot
        eval_snapshot = await sync_to_async(EvaluationSnapshot.objects.create)(
            email=self.test_email,
            expected_outcome="Professional response",
            prompt_version=1,
            performance_score=0.8
        )
        
        score = await self.optimizer.evaluate_prompt(self.current_prompt, [eval_snapshot])
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    async def test_optimize_prompt_returns_new_prompt(self):
        """Test that optimization returns improved prompt"""
        # Mock the LLM provider
        mock_improved_content = "You are an enhanced email assistant that learns from user feedback and adapts to preferences."
        
        with patch.object(self.mock_llm, 'optimize_prompt', return_value=mock_improved_content):
            result = await self.optimizer.optimize_prompt(
                self.current_prompt, 
                [], 
                []
            )
            
            assert isinstance(result, SystemPrompt)
            assert result.version > self.current_prompt.version
            assert result.content == mock_improved_content
            assert result.content != self.current_prompt.content
    
    async def test_evaluate_prompt_returns_score(self):
        """Test that evaluation returns numeric score"""
        # Create test evaluation snapshots
        eval_snapshot1 = await sync_to_async(EvaluationSnapshot.objects.create)(
            email=self.test_email,
            expected_outcome="Professional response",
            prompt_version=1,
            performance_score=0.8
        )
        
        eval_snapshot2 = await sync_to_async(EvaluationSnapshot.objects.create)(
            email=self.test_email,
            expected_outcome="Helpful response",
            prompt_version=1,
            performance_score=0.9
        )
        
        test_scenarios = [eval_snapshot1, eval_snapshot2]
        
        score = await self.optimizer.evaluate_prompt(self.current_prompt, test_scenarios)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # Should return average of the scores (0.8 + 0.9) / 2 = 0.85
        assert score == 0.85