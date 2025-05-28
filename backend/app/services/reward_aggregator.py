from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from core.models import SystemPrompt, UserFeedback, Draft, Email
from dataclasses import dataclass
from asgiref.sync import sync_to_async
import asyncio
import math


@dataclass
class RewardComponents:
    """Individual reward components for aggregation"""
    exact_match: float = 0.0
    f1_score: float = 0.0
    perplexity: float = 0.0
    human_feedback: float = 0.0
    length_appropriateness: float = 0.0
    semantic_similarity: float = 0.0


@dataclass
class RewardWeights:
    """Weights for different reward components"""
    exact_match: float = 0.1
    f1_score: float = 0.3
    perplexity: float = 0.2
    human_feedback: float = 0.3
    length_appropriateness: float = 0.05
    semantic_similarity: float = 0.05


class RewardFunction(ABC):
    """Abstract interface for individual reward functions"""
    
    @abstractmethod
    async def compute_reward(
        self,
        original_prompt: str,
        rewritten_prompt: str,
        context: Dict[str, Any]
    ) -> float:
        """Compute reward for a specific metric"""
        pass


class ExactMatchReward(RewardFunction):
    """Exact match reward for precision requirements"""
    
    async def compute_reward(
        self,
        original_prompt: str,
        rewritten_prompt: str,
        context: Dict[str, Any]
    ) -> float:
        """Compute exact match score between expected and actual output"""
        expected = context.get('expected_output', '')
        actual = context.get('actual_output', '')
        
        if not expected or not actual:
            return 0.0
        
        return 1.0 if expected.strip().lower() == actual.strip().lower() else 0.0


class F1ScoreReward(RewardFunction):
    """F1 score combining precision and recall"""
    
    async def compute_reward(
        self,
        original_prompt: str,
        rewritten_prompt: str,
        context: Dict[str, Any]
    ) -> float:
        """Compute F1 score for response quality"""
        expected = context.get('expected_output', '').split()
        actual = context.get('actual_output', '').split()
        
        # Handle empty inputs consistently
        expected_set = set(expected)
        actual_set = set(actual)
        
        # Both empty is perfect match
        if not expected_set and not actual_set:
            return 1.0
        
        # One empty, one non-empty is zero match
        if not expected_set or not actual_set:
            return 0.0
        
        intersection = expected_set.intersection(actual_set)
        precision = len(intersection) / len(actual_set)
        recall = len(intersection) / len(expected_set)
        
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)


class PerplexityReward(RewardFunction):
    """Perplexity-based reward for response predictability"""
    
    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
    
    async def compute_reward(
        self,
        original_prompt: str,
        rewritten_prompt: str,
        context: Dict[str, Any]
    ) -> float:
        """Compute perplexity-based reward (lower perplexity = higher reward)"""
        output = context.get('actual_output', '')
        
        if not output:
            return 0.0
        
        try:
            # Get log probabilities from LLM
            log_probs = await self.llm_provider.get_log_probabilities(output)
            
            if not log_probs:
                return 0.5  # Neutral score if can't compute
            
            # Calculate perplexity
            avg_log_prob = sum(log_probs) / len(log_probs)
            perplexity = math.exp(-avg_log_prob)
            
            # Convert to reward (inverse relationship)
            # Normalize to 0-1 range assuming reasonable perplexity bounds
            max_perplexity = 100.0  # Configurable threshold
            reward = max(0.0, 1.0 - (perplexity / max_perplexity))
            
            return min(1.0, reward)
            
        except Exception as e:
            print(f"Error computing perplexity reward: {e}")
            return 0.5


class HumanFeedbackReward(RewardFunction):
    """Human feedback-based reward"""
    
    async def compute_reward(
        self,
        original_prompt: str,
        rewritten_prompt: str,
        context: Dict[str, Any]
    ) -> float:
        """Convert human feedback to numerical reward"""
        user_feedback = context.get('user_feedback')
        
        if not user_feedback:
            return 0.5  # Neutral when no feedback
        
        # Convert feedback action to reward
        action_rewards = {
            'accept': 1.0,
            'edit': 0.6,   # Partial success
            'reject': 0.0,
            'ignore': 0.3  # Slight negative signal
        }
        
        base_reward = action_rewards.get(user_feedback.action, 0.5)
        
        # Adjust based on reason ratings if available
        try:
            if hasattr(user_feedback, 'reason_ratings') and user_feedback.reason_ratings:
                # For mock objects, reason_ratings.all() should work directly
                ratings = [r.liked for r in user_feedback.reason_ratings.all()]
                if ratings:
                    rating_bonus = sum(ratings) / len(ratings) * 0.2  # Up to 20% bonus
                    base_reward += rating_bonus
        except Exception:
            # For real Django querysets, use sync_to_async
            try:
                if hasattr(user_feedback, 'reason_ratings') and user_feedback.reason_ratings:
                    ratings = await sync_to_async(list)(user_feedback.reason_ratings.all())
                    if ratings:
                        rating_bonus = sum(r.liked for r in ratings) / len(ratings) * 0.2
                        base_reward += rating_bonus
            except Exception:
                pass
        
        return min(1.2, base_reward)  # Allow bonuses up to 1.2


class LengthAppropriatenessReward(RewardFunction):
    """Reward for appropriate response length"""
    
    async def compute_reward(
        self,
        original_prompt: str,
        rewritten_prompt: str,
        context: Dict[str, Any]
    ) -> float:
        """Compute reward based on response length appropriateness"""
        expected_length = context.get('expected_length', 0)
        actual_length = len(context.get('actual_output', '').split())
        
        if expected_length == 0:
            return 1.0  # No constraint
        
        # Calculate length ratio
        ratio = actual_length / expected_length if expected_length > 0 else 0
        
        # Reward function: highest at ratio=1, decreases with distance
        if 0.8 <= ratio <= 1.2:
            return 1.0  # Perfect range
        elif 0.5 <= ratio <= 2.0:
            return 1.0 - abs(ratio - 1.0) * 0.5  # Gradual decrease
        else:
            return 0.1  # Very poor length match


class RewardFunctionAggregator:
    """Aggregates multiple reward functions with configurable weights"""
    
    def __init__(
        self,
        llm_provider,
        weights: Optional[RewardWeights] = None,
        scenario_specific_weights: Optional[Dict[str, RewardWeights]] = None
    ):
        self.weights = weights or RewardWeights()
        self.scenario_weights = scenario_specific_weights or {}
        
        # Initialize reward functions
        self.reward_functions = {
            'exact_match': ExactMatchReward(),
            'f1_score': F1ScoreReward(),
            'perplexity': PerplexityReward(llm_provider),
            'human_feedback': HumanFeedbackReward(),
            'length_appropriateness': LengthAppropriatenessReward(),
        }
    
    async def compute_reward(
        self,
        original_prompt: SystemPrompt,
        rewritten_prompt: str,
        user_feedback: UserFeedback,
        task_performance: Dict[str, float],
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Compute aggregated reward from all components"""
        
        if context is None:
            context = {}
        
        # Add feedback and performance to context
        context['user_feedback'] = user_feedback
        context.update(task_performance)
        
        # Get scenario-specific weights if available
        scenario = context.get('email_scenario', 'default')
        weights = self.scenario_weights.get(scenario, self.weights)
        
        # Compute individual reward components
        components = RewardComponents()
        
        try:
            components.exact_match = await self.reward_functions['exact_match'].compute_reward(
                original_prompt.content, rewritten_prompt, context
            )
            components.f1_score = await self.reward_functions['f1_score'].compute_reward(
                original_prompt.content, rewritten_prompt, context
            )
            components.perplexity = await self.reward_functions['perplexity'].compute_reward(
                original_prompt.content, rewritten_prompt, context
            )
            components.human_feedback = await self.reward_functions['human_feedback'].compute_reward(
                original_prompt.content, rewritten_prompt, context
            )
            components.length_appropriateness = await self.reward_functions['length_appropriateness'].compute_reward(
                original_prompt.content, rewritten_prompt, context
            )
        except Exception as e:
            print(f"Error computing reward components: {e}")
            return 0.5  # Neutral reward on error
        
        # Compute weighted aggregation
        total_reward = (
            components.exact_match * weights.exact_match +
            components.f1_score * weights.f1_score +
            components.perplexity * weights.perplexity +
            components.human_feedback * weights.human_feedback +
            components.length_appropriateness * weights.length_appropriateness +
            components.semantic_similarity * weights.semantic_similarity
        )
        
        # Store components for analysis
        context['reward_components'] = components
        
        return max(0.0, min(1.0, total_reward))
    
    async def evaluate_candidate(
        self,
        candidate,  # RewriteCandidate
        evaluation_context: Dict[str, Any]
    ) -> float:
        """Evaluate a rewrite candidate for selection"""
        
        # Simulate task performance with candidate prompt
        # In real implementation, this would run the task LLM
        simulated_performance = {
            'accuracy': 0.8,  # Placeholder
            'actual_output': f"Response using: {candidate.content[:50]}...",
            'expected_output': evaluation_context.get('expected_output', '')
        }
        
        # Create dummy feedback for evaluation
        from core.models import UserFeedback
        dummy_feedback = type('DummyFeedback', (), {
            'action': 'accept',
            'reason': '',
            'reason_ratings': []
        })()
        
        # Create dummy prompt
        dummy_prompt = type('DummyPrompt', (), {
            'content': evaluation_context.get('original_prompt', '')
        })()
        
        reward = await self.compute_reward(
            dummy_prompt,
            candidate.content,
            dummy_feedback,
            simulated_performance,
            evaluation_context
        )
        
        # Adjust by candidate confidence
        return reward * candidate.confidence
    
    def update_weights(
        self,
        scenario: str,
        new_weights: RewardWeights
    ):
        """Update weights for specific scenario based on performance"""
        self.scenario_weights[scenario] = new_weights
    
    def get_reward_breakdown(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Get detailed breakdown of reward components"""
        components = context.get('reward_components')
        if not components:
            return {}
        
        return {
            'exact_match': components.exact_match,
            'f1_score': components.f1_score,
            'perplexity': components.perplexity,
            'human_feedback': components.human_feedback,
            'length_appropriateness': components.length_appropriateness,
            'semantic_similarity': components.semantic_similarity
        }