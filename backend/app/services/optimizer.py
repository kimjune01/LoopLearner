from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..models.email import UserFeedback
from ..models.state import SystemPrompt, EvaluationSnapshot


class PromptOptimizer(ABC):
    """Abstract interface for prompt optimization"""
    
    @abstractmethod
    async def optimize_prompt(
        self,
        current_prompt: SystemPrompt,
        feedback_history: List[UserFeedback],
        evaluation_snapshots: List[EvaluationSnapshot]
    ) -> SystemPrompt:
        """Optimize prompt based on feedback and evaluations"""
        pass
    
    @abstractmethod
    async def evaluate_prompt(
        self,
        prompt: SystemPrompt,
        test_scenarios: List[EvaluationSnapshot]
    ) -> float:
        """Evaluate prompt performance against test scenarios"""
        pass


class LLMBasedOptimizer(PromptOptimizer):
    """LLM-based prompt optimization implementation"""
    
    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
    
    async def optimize_prompt(
        self,
        current_prompt: SystemPrompt,
        feedback_history: List[UserFeedback],
        evaluation_snapshots: List[EvaluationSnapshot]
    ) -> SystemPrompt:
        # TODO: Implement LLM-based optimization
        raise NotImplementedError("Prompt optimization not implemented")
    
    async def evaluate_prompt(
        self,
        prompt: SystemPrompt,
        test_scenarios: List[EvaluationSnapshot]
    ) -> float:
        # TODO: Implement prompt evaluation
        raise NotImplementedError("Prompt evaluation not implemented")