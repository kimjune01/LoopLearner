from abc import ABC, abstractmethod
from typing import List, Dict, Any
from core.models import UserFeedback, SystemPrompt, EvaluationSnapshot
from asgiref.sync import sync_to_async


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
        """Optimize prompt based on feedback and evaluations"""
        
        # Prepare feedback data for the LLM
        feedback_data = []
        for feedback in feedback_history:
            feedback_item = {
                'action': feedback.action,
                'reason': feedback.reason,
                'edited_content': feedback.edited_content,
                'reason_ratings': {}
            }
            
            # Get reason ratings
            for rating in await sync_to_async(list)(feedback.reason_ratings.all()):
                feedback_item['reason_ratings'][rating.reason.text] = rating.liked
                
            feedback_data.append(feedback_item)
        
        # Prepare evaluation data
        eval_data = []
        for snapshot in evaluation_snapshots:
            eval_data.append({
                'email_subject': snapshot.email.subject,
                'expected_outcome': snapshot.expected_outcome,
                'performance_score': snapshot.performance_score,
                'metadata': snapshot.metadata
            })
        
        # Use LLM provider to optimize the prompt
        improved_content = await self.llm_provider.optimize_prompt(
            current_prompt,
            feedback_data,
            eval_data
        )
        
        # Create new SystemPrompt with incremented version
        new_version = current_prompt.version + 1
        
        # Create new prompt
        new_prompt = await sync_to_async(SystemPrompt.objects.create)(
            content=improved_content,
            version=new_version,
            is_active=False  # Not active until manually approved
        )
        
        return new_prompt
    
    async def evaluate_prompt(
        self,
        prompt: SystemPrompt,
        test_scenarios: List[EvaluationSnapshot]
    ) -> float:
        """Evaluate prompt performance against test scenarios"""
        
        if not test_scenarios:
            return 0.0
        
        # Calculate average performance score from evaluation snapshots
        total_score = sum(scenario.performance_score for scenario in test_scenarios)
        average_score = total_score / len(test_scenarios)
        
        return float(average_score)