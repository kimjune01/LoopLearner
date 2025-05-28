from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from core.models import SystemPrompt, Email, UserFeedback
from dataclasses import dataclass
import asyncio
import logging
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


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


@dataclass
class FeedbackPattern:
    """Pattern extracted from historical feedback"""
    scenario_type: str
    successful_prompt: str
    feedback_summary: str
    performance_score: float
    usage_count: int


@dataclass
class SimilarityMatch:
    """Result from similarity matching"""
    prompt: SystemPrompt
    similarity_score: float
    feedback_pattern: str
    success_rate: float


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


class LLMBasedPromptRewriter(PromptRewriter):
    """LLM-based prompt rewriter with similarity matching and feedback learning"""
    
    def __init__(
        self, 
        rewriter_llm_provider,
        similarity_llm_provider,
        reward_function_aggregator,
        meta_prompt_manager
    ):
        self.rewriter_llm = rewriter_llm_provider
        self.similarity_llm = similarity_llm_provider
        self.reward_aggregator = reward_function_aggregator
        self.meta_prompt_manager = meta_prompt_manager
        self.feedback_patterns = []  # Cache for performance
    
    async def rewrite_prompt(
        self, 
        context: RewriteContext,
        mode: str = "conservative"
    ) -> List[RewriteCandidate]:
        """Generate prompt rewrites using LLM with similarity matching"""
        
        # Step 1: Find similar successful prompts from database
        similar_patterns = await self._find_similar_successful_prompts(context)
        
        # Step 2: Get meta-prompt template
        meta_prompt = await self.meta_prompt_manager.get_meta_prompt(
            context.email_scenario,
            context.constraints
        )
        
        # Step 3: Build comprehensive rewriting instruction
        rewrite_instruction = await self._build_llm_rewrite_instruction(
            context, 
            meta_prompt, 
            similar_patterns
        )
        
        # Step 4: Generate candidates based on mode
        if mode == "conservative":
            candidates = await self._generate_conservative_rewrites(rewrite_instruction)
        elif mode == "exploratory":
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
        """Update feedback patterns based on user feedback and task performance"""
        
        # Convert feedback to reward signal
        reward = await self.reward_aggregator.compute_reward(
            original_prompt,
            rewritten_prompt,
            user_feedback,
            task_performance
        )
        
        # Store successful patterns in database (feedback is already stored by Django)
        if user_feedback.action in ['accept', 'edit'] and reward > 0.7:
            await self._store_successful_pattern(
                original_prompt,
                rewritten_prompt,
                user_feedback,
                reward
            )
        
        # Update cached patterns
        await self._refresh_feedback_patterns()
        
        logger.info(f"Updated feedback patterns. Reward: {reward:.3f}, Action: {user_feedback.action}")
    
    async def _find_similar_successful_prompts(self, context: RewriteContext) -> List[SimilarityMatch]:
        """Find similar successful prompts from database using LLM similarity matching"""
        
        # Get successful prompts from recent feedback
        successful_prompts = await self._get_successful_prompts_from_db(context.email_scenario)
        
        if not successful_prompts:
            return []
        
        # Use LLM to find similar prompts
        similarity_instruction = f"""
        Compare the current prompt with these successful prompts and rate similarity (0-1):
        
        Current Prompt: "{context.current_prompt.content}"
        Current Scenario: {context.email_scenario}
        
        Successful Prompts:
        {self._format_successful_prompts(successful_prompts)}
        
        Return JSON format: [{{"prompt_id": 1, "similarity": 0.8, "reason": "both focus on professional tone"}}]
        """
        
        try:
            similarity_response = await self.similarity_llm.generate(
                similarity_instruction,
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse similarity scores (simplified - in production use proper JSON parsing)
            matches = []
            for prompt_data in successful_prompts[:3]:  # Top 3 matches
                matches.append(SimilarityMatch(
                    prompt=prompt_data['prompt'],
                    similarity_score=0.7,  # Placeholder - would parse from LLM response
                    feedback_pattern=prompt_data['feedback_summary'],
                    success_rate=prompt_data['success_rate']
                ))
            
            return matches
            
        except Exception as e:
            logger.warning(f"Similarity matching failed: {e}")
            return []
    
    async def _build_llm_rewrite_instruction(
        self, 
        context: RewriteContext, 
        meta_prompt: str, 
        similar_patterns: List[SimilarityMatch]
    ) -> str:
        """Build comprehensive instruction for LLM-based rewriting"""
        
        similar_prompts_text = ""
        if similar_patterns:
            similar_prompts_text = "\n\nSimilar Successful Prompts:\n"
            for i, match in enumerate(similar_patterns[:2]):  # Top 2
                similar_prompts_text += f"{i+1}. {match.prompt.content} (Success rate: {match.success_rate:.1%})\n"
        
        return f"""
{meta_prompt}

CURRENT PROMPT TO IMPROVE:
{context.current_prompt.content}

CONTEXT:
- Email Scenario: {context.email_scenario}
- Recent Performance: {context.performance_history}
- User Feedback Summary: {self._summarize_feedback(context.recent_feedback)}
{similar_prompts_text}

TASK: Rewrite the current prompt to improve performance based on:
1. User feedback patterns
2. Similar successful prompts 
3. Scenario-specific requirements

Generate an improved prompt that maintains clarity while addressing the identified issues:
"""
    
    async def _generate_conservative_rewrites(self, instruction: str) -> List[RewriteCandidate]:
        """Generate single high-confidence rewrite"""
        response = await self.rewriter_llm.generate(
            instruction,
            temperature=0.1,  # Very low temperature for consistency
            max_tokens=300
        )
        
        return [RewriteCandidate(
            content=response.strip(),
            confidence=0.9,
            temperature=0.1,
            reasoning="Conservative rewrite based on successful patterns"
        )]
    
    async def _generate_exploratory_rewrites(self, instruction: str) -> List[RewriteCandidate]:
        """Generate multiple diverse candidate rewrites"""
        candidates = []
        
        for i in range(3):  # Generate 3 diverse candidates
            enhanced_instruction = f"{instruction}\n\nVariation {i+1}: Focus on {'clarity' if i==0 else 'engagement' if i==1 else 'efficiency'}:"
            
            response = await self.rewriter_llm.generate(
                enhanced_instruction,
                temperature=0.7,  # Higher temperature for diversity
                max_tokens=300
            )
            
            candidates.append(RewriteCandidate(
                content=response.strip(),
                confidence=0.6,
                temperature=0.7,
                reasoning=f"Exploratory rewrite focusing on {'clarity' if i==0 else 'engagement' if i==1 else 'efficiency'}"
            ))
        
        return candidates
    
    async def _generate_hybrid_rewrites(self, instruction: str) -> List[RewriteCandidate]:
        """Generate mix of conservative and exploratory candidates"""
        conservative = await self._generate_conservative_rewrites(instruction)
        exploratory = await self._generate_exploratory_rewrites(instruction)
        
        # Return conservative + top 2 exploratory
        return conservative + exploratory[:2]
    
    def _summarize_feedback(self, feedback_list: List[UserFeedback]) -> str:
        """Summarize recent user feedback for context"""
        if not feedback_list:
            return "No recent feedback"
        
        actions = [f.action for f in feedback_list[-5:]]  # Last 5 feedback items
        action_counts = {action: actions.count(action) for action in set(actions)}
        
        return f"Recent actions: {action_counts}"
    
    async def _get_successful_prompts_from_db(self, scenario_type: str) -> List[Dict]:
        """Query database for successful prompts in similar scenarios"""
        try:
            # Get prompts with positive feedback in the last 30 days
            recent_date = timezone.now() - timedelta(days=30)
            
            # Query successful feedback patterns using async ORM
            successful_feedback = [
                feedback async for feedback in UserFeedback.objects.filter(
                    action__in=['accept', 'edit'],
                    created_at__gte=recent_date,
                    draft__email__scenario_type=scenario_type
                ).select_related('draft__system_prompt')
            ]
            
            prompt_performance = {}
            for feedback in successful_feedback:
                prompt_id = feedback.draft.system_prompt.id
                if prompt_id not in prompt_performance:
                    prompt_performance[prompt_id] = {
                        'prompt': feedback.draft.system_prompt,
                        'accepts': 0,
                        'edits': 0,
                        'total': 0
                    }
                
                prompt_performance[prompt_id][feedback.action + 's'] += 1
                prompt_performance[prompt_id]['total'] += 1
            
            # Calculate success rates and return top performers
            successful_prompts = []
            for prompt_id, data in prompt_performance.items():
                if data['total'] >= 3:  # Minimum feedback count
                    success_rate = (data['accepts'] + data['edits']) / data['total']
                    if success_rate >= 0.6:  # 60% success threshold
                        successful_prompts.append({
                            'prompt': data['prompt'],
                            'success_rate': success_rate,
                            'feedback_summary': f"Accepts: {data['accepts']}, Edits: {data['edits']}"
                        })
            
            # Sort by success rate
            successful_prompts.sort(key=lambda x: x['success_rate'], reverse=True)
            return successful_prompts[:5]  # Top 5
            
        except Exception as e:
            logger.error(f"Failed to query successful prompts: {e}")
            return []
    
    def _format_successful_prompts(self, prompts: List[Dict]) -> str:
        """Format successful prompts for LLM similarity comparison"""
        formatted = ""
        for i, prompt_data in enumerate(prompts):
            formatted += f"{i+1}. \"{prompt_data['prompt'].content}\" (Success: {prompt_data['success_rate']:.1%})\n"
        return formatted
    
    async def _store_successful_pattern(
        self, 
        original_prompt: SystemPrompt, 
        rewritten_prompt: str, 
        feedback: UserFeedback, 
        reward: float
    ):
        """Store successful rewriting pattern for future reference"""
        try:
            # Create new system prompt for the successful rewrite
            if feedback.action == 'edit' and feedback.edited_content:
                content = feedback.edited_content
            else:
                content = rewritten_prompt
            
            new_prompt = await SystemPrompt.objects.acreate(
                content=content,
                scenario_type=original_prompt.scenario_type,
                version=original_prompt.version + 1,
                is_active=False,  # Don't activate automatically
                performance_score=reward
            )
            
            logger.info(f"Stored successful pattern: v{new_prompt.version} (reward: {reward:.3f})")
            
        except Exception as e:
            logger.error(f"Failed to store successful pattern: {e}")
    
    async def _refresh_feedback_patterns(self):
        """Refresh cached feedback patterns from database"""
        try:
            # Update cache with recent successful patterns
            self.feedback_patterns = await self._get_successful_prompts_from_db("all")
            logger.debug(f"Refreshed {len(self.feedback_patterns)} feedback patterns")
        except Exception as e:
            logger.error(f"Failed to refresh feedback patterns: {e}")