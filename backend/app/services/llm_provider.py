from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..models.email import EmailMessage, EmailDraft


class LLMProvider(ABC):
    """Abstract interface for LLM providers"""
    
    @abstractmethod
    async def generate_drafts(
        self, 
        email: EmailMessage, 
        system_prompt: str,
        user_preferences: Dict[str, str]
    ) -> List[EmailDraft]:
        """Generate multiple draft responses for an email"""
        pass
    
    @abstractmethod
    async def optimize_prompt(
        self,
        current_prompt: str,
        feedback_data: List[Dict[str, Any]],
        evaluation_snapshots: List[Dict[str, Any]]
    ) -> str:
        """Optimize system prompt based on feedback"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of LLM provider"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def generate_drafts(
        self, 
        email: EmailMessage, 
        system_prompt: str,
        user_preferences: Dict[str, str]
    ) -> List[EmailDraft]:
        # TODO: Implement OpenAI API call
        raise NotImplementedError("OpenAI draft generation not implemented")
    
    async def optimize_prompt(
        self,
        current_prompt: str,
        feedback_data: List[Dict[str, Any]],
        evaluation_snapshots: List[Dict[str, Any]]
    ) -> str:
        # TODO: Implement prompt optimization
        raise NotImplementedError("Prompt optimization not implemented")