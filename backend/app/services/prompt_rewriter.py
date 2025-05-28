from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from core.models import SystemPrompt, Email, UserFeedback
from dataclasses import dataclass
import asyncio


@dataclass
class RewriteCandidate:
    """Represents a candidate prompt rewrite with metadata"""
    content: str
    confidence: float
    temperature: float
    reasoning: Optional[str] = None


@dataclass
class RewriteContext:
    """Context for prompt rewriting including email scenario and constraints"""
    email_scenario: str
    current_prompt: SystemPrompt
    recent_feedback: List[UserFeedback]
    performance_history: Dict[str, float]
    constraints: Dict[str, Any]


class PromptRewriter(ABC):
    """Abstract interface for prompt rewriting using RL-based optimization"""
    
    @abstractmethod
    async def rewrite_prompt(
        self, 
        context: RewriteContext,
        mode: str = "conservative"  # "conservative" | "exploratory" | "hybrid"
    ) -> List[RewriteCandidate]:
        """Generate prompt rewrite candidates based on context"""
        pass
    
    @abstractmethod
    async def select_best_candidate(
        self,
        candidates: List[RewriteCandidate],
        evaluation_context: Dict[str, Any]
    ) -> RewriteCandidate:
        """Select the best candidate from generated rewrites"""
        pass


class PPOPromptRewriter(PromptRewriter):
    """PPO-based prompt rewriter implementing PRewrite methodology"""
    
    def __init__(
        self, 
        rewriter_llm_provider,
        reward_function_aggregator,
        meta_prompt_manager,
        kl_penalty: float = 0.02
    ):
        self.rewriter_llm = rewriter_llm_provider
        self.reward_aggregator = reward_function_aggregator
        self.meta_prompt_manager = meta_prompt_manager
        self.kl_penalty = kl_penalty
        self.training_history = []
    
    async def rewrite_prompt(
        self, 
        context: RewriteContext,
        mode: str = "conservative"
    ) -> List[RewriteCandidate]:
        """Generate prompt rewrites using PPO-trained rewriter LLM"""
        
        # Get appropriate meta-prompt for scenario
        meta_prompt = await self.meta_prompt_manager.get_meta_prompt(
            context.email_scenario,
            context.constraints
        )
        
        # Prepare rewriting instruction
        rewrite_instruction = self._build_rewrite_instruction(context, meta_prompt)
        
        if mode == "conservative":
            # PRewrite-I: Greedy decoding (temperature = 0)
            candidates = await self._generate_conservative_rewrites(rewrite_instruction)
        elif mode == "exploratory":
            # PRewrite-S: Multiple candidates (temperature = 1)
            candidates = await self._generate_exploratory_rewrites(rewrite_instruction)
        else:  # hybrid
            candidates = await self._generate_hybrid_rewrites(rewrite_instruction)
        
        return candidates
    
    async def select_best_candidate(
        self,
        candidates: List[RewriteCandidate],
        evaluation_context: Dict[str, Any]
    ) -> RewriteCandidate:
        """Select best candidate using reward function evaluation"""
        
        best_candidate = None
        best_score = float('-inf')
        
        for candidate in candidates:
            # Evaluate candidate using reward aggregator
            score = await self.reward_aggregator.evaluate_candidate(
                candidate, 
                evaluation_context
            )
            
            if score > best_score:
                best_score = score
                best_candidate = candidate
        
        return best_candidate
    
    async def update_from_feedback(
        self,
        original_prompt: SystemPrompt,
        rewritten_prompt: str,
        user_feedback: UserFeedback,
        task_performance: Dict[str, float]
    ):
        """Update PPO model based on user feedback and task performance"""
        
        # Convert feedback to reward signal
        reward = await self.reward_aggregator.compute_reward(
            original_prompt,
            rewritten_prompt,
            user_feedback,
            task_performance
        )
        
        # Store training example
        training_example = {
            'original_prompt': original_prompt.content,
            'rewritten_prompt': rewritten_prompt,
            'reward': reward,
            'feedback': user_feedback,
            'timestamp': user_feedback.created_at
        }
        
        self.training_history.append(training_example)
        
        # Trigger batch training if enough examples accumulated
        if len(self.training_history) >= 10:  # Configurable batch size
            await self._run_ppo_training_step()
            # Clear training history after batch training
            self.training_history = []
    
    def _build_rewrite_instruction(self, context: RewriteContext, meta_prompt: str) -> str:
        """Build instruction for the rewriter LLM"""
        return f"""
{meta_prompt}

Current Prompt:
{context.current_prompt.content}

Email Scenario: {context.email_scenario}
Recent Performance: {context.performance_history}
User Feedback Summary: {self._summarize_feedback(context.recent_feedback)}

Please rewrite the prompt to improve performance while maintaining clarity and intent.
Rewritten Prompt:"""
    
    async def _generate_conservative_rewrites(self, instruction: str) -> List[RewriteCandidate]:
        """Generate single high-confidence rewrite (PRewrite-I)"""
        response = await self.rewriter_llm.generate(
            instruction,
            temperature=0.0,
            max_tokens=200
        )
        
        return [RewriteCandidate(
            content=response.strip(),
            confidence=0.9,  # High confidence for greedy decoding
            temperature=0.0,
            reasoning="Conservative rewrite using greedy decoding"
        )]
    
    async def _generate_exploratory_rewrites(self, instruction: str) -> List[RewriteCandidate]:
        """Generate multiple candidate rewrites (PRewrite-S)"""
        candidates = []
        
        for i in range(5):  # Generate 5 candidates
            response = await self.rewriter_llm.generate(
                instruction,
                temperature=1.0,
                max_tokens=200
            )
            
            candidates.append(RewriteCandidate(
                content=response.strip(),
                confidence=0.7,  # Lower confidence due to sampling
                temperature=1.0,
                reasoning=f"Exploratory candidate {i+1}"
            ))
        
        return candidates
    
    async def _generate_hybrid_rewrites(self, instruction: str) -> List[RewriteCandidate]:
        """Generate mix of conservative and exploratory candidates"""
        conservative = await self._generate_conservative_rewrites(instruction)
        exploratory = await self._generate_exploratory_rewrites(instruction)
        
        # Take top 3 exploratory + 1 conservative
        return conservative + exploratory[:3]
    
    def _summarize_feedback(self, feedback_list: List[UserFeedback]) -> str:
        """Summarize recent user feedback for context"""
        if not feedback_list:
            return "No recent feedback"
        
        actions = [f.action for f in feedback_list[-5:]]  # Last 5 feedback items
        action_counts = {action: actions.count(action) for action in set(actions)}
        
        return f"Recent actions: {action_counts}"
    
    async def _run_ppo_training_step(self):
        """Run PPO training step on accumulated examples"""
        # TODO: Implement actual PPO training logic
        # This would involve:
        # 1. Computing advantages using GAE
        # 2. Policy gradient updates with clipping
        # 3. KL penalty application
        # 4. Value function updates
        
        print(f"PPO training step with {len(self.training_history)} examples")
        
        # Note: Training history is cleared in update_from_feedback after this method