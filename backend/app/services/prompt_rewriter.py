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
    """Modern LLM-based prompt rewriter with OPRO-inspired techniques and fast optimization"""
    
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
        
        # Modern optimization settings
        self.optimization_modes = {
            'fast': {'max_iterations': 1, 'candidates': 1, 'timeout': 5},
            'balanced': {'max_iterations': 2, 'candidates': 3, 'timeout': 15},
            'thorough': {'max_iterations': 3, 'candidates': 5, 'timeout': 30}
        }
        
        # Research-backed meta-prompt template
        self.static_metaprompt = """
Take a deep breath and work on this problem step by step.

You are an expert prompt engineer specializing in optimizing prompts for AI assistants. Your task is to improve the given prompt to make it more effective at generating high-quality responses.

Current prompt:
\"\"\"{current_prompt}\"\"\"

Context: This prompt is used for {task_context}

Performance feedback:
{performance_feedback}

Optimization guidelines:
1. **Clarity**: Make instructions specific and unambiguous
2. **Structure**: Use clear step-by-step format when helpful
3. **Context**: Include relevant background and constraints
4. **Examples**: Add concrete examples if they would help
5. **Format**: Specify desired output format and style
6. **Tone**: Ensure appropriate tone for the task

Common effective prompt elements:
- "Think step by step"
- "Be specific and detailed"
- "Consider the context carefully"
- Clear role definition ("You are a...")
- Explicit constraints and requirements
- Example inputs and outputs

Focus on the biggest weakness in the current prompt and make targeted improvements. Keep the core purpose intact while making it more likely to produce high-quality responses.

Generate ONLY the improved prompt without any explanations:
"""
    
    async def rewrite_prompt(
        self, 
        context: RewriteContext,
        mode: str = "fast"  # Changed default to fast
    ) -> List[RewriteCandidate]:
        """Generate prompt rewrites using modern optimization techniques"""
        
        # Select optimization strategy based on mode
        if mode in ['fast', 'cached']:
            return await self._fast_optimization(context)
        elif mode == 'single_shot':
            return await self._single_shot_optimization(context)
        elif mode == 'mini_opro':
            return await self._mini_opro_optimization(context)
        else:
            # Legacy mode for backward compatibility
            return await self._legacy_optimization(context, mode)
    
    async def _fast_optimization(self, context: RewriteContext) -> List[RewriteCandidate]:
        """Ultra-fast optimization using cached patterns and rule-based improvements"""
        
        # First try cached pattern matching (sub-second)
        cached_candidate = await self._try_cached_pattern_optimization(context)
        if cached_candidate:
            return [cached_candidate]
        
        # Fallback to rule-based direct optimization (1-3 seconds)
        return await self._direct_instruction_optimization(context)
    
    async def _single_shot_optimization(self, context: RewriteContext) -> List[RewriteCandidate]:
        """Single LLM call optimization (5-10 seconds)"""
        
        # Build focused optimization prompt
        task_context = self._build_task_context(context)
        performance_feedback = self._format_performance_feedback(context)
        main_issue = self._identify_primary_issue(context)
        
        optimization_prompt = f"""
Improve this prompt to make it more effective:

\"\"\"{context.current_prompt.content}\"\"\"

Main issue to fix: {main_issue}
Context: {task_context}

Make the prompt more specific and actionable while keeping it clear.

Improved prompt:
"""
        
        try:
            response = await self.rewriter_llm.generate(
                optimization_prompt,
                temperature=0.3,
                max_tokens=200,
                timeout=10
            )
            
            return [RewriteCandidate(
                content=response.strip(),
                confidence=0.8,
                temperature=0.3,
                reasoning=f"Single-shot optimization targeting: {main_issue}"
            )]
            
        except Exception as e:
            logger.warning(f"Single-shot optimization failed: {e}")
            return await self._fast_optimization(context)  # Fallback
    
    async def _mini_opro_optimization(self, context: RewriteContext) -> List[RewriteCandidate]:
        """Lightweight OPRO implementation (15-30 seconds)"""
        
        # Build mini meta-prompt with optimization trajectory
        recent_history = await self._get_recent_optimization_history(context, limit=3)
        
        task_context = self._build_task_context(context)
        performance_feedback = self._format_performance_feedback(context)
        
        mini_metaprompt = self.static_metaprompt.format(
            current_prompt=context.current_prompt.content,
            task_context=task_context,
            performance_feedback=performance_feedback
        )
        
        # Add optimization trajectory if available
        if recent_history:
            mini_metaprompt += f"\n\nRecent optimization attempts and results:\n{self._format_optimization_history(recent_history)}"
        
        mini_metaprompt += "\n\nGenerate 3 improved versions focusing on the main weakness:\n"
        
        try:
            # Generate 3 candidates in parallel if possible
            candidates = []
            for i in range(3):
                response = await self.rewriter_llm.generate(
                    mini_metaprompt + f"\nVersion {i+1}:",
                    temperature=0.4 + (i * 0.1),  # Slight temperature variation
                    max_tokens=200,
                    timeout=10
                )
                
                candidates.append(RewriteCandidate(
                    content=response.strip(),
                    confidence=0.7 + (0.1 if i == 0 else 0),  # First candidate slightly higher confidence
                    temperature=0.4 + (i * 0.1),
                    reasoning=f"Mini-OPRO candidate {i+1} with slight variation"
                ))
            
            return candidates
            
        except Exception as e:
            logger.warning(f"Mini-OPRO optimization failed: {e}")
            return await self._single_shot_optimization(context)  # Fallback
    
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
    
    async def _try_cached_pattern_optimization(self, context: RewriteContext) -> Optional[RewriteCandidate]:
        """Try to optimize using cached successful patterns (sub-second)"""
        
        try:
            # Quick pattern matching based on scenario and feedback
            cached_patterns = self._get_cached_patterns(context.email_scenario)
            
            if not cached_patterns:
                return None
            
            # Apply best matching pattern using template substitution
            best_pattern = self._select_best_cached_pattern(context, cached_patterns)
            
            if best_pattern:
                optimized_content = self._apply_cached_pattern(context.current_prompt.content, best_pattern)
                
                return RewriteCandidate(
                    content=optimized_content,
                    confidence=0.6,
                    temperature=0.0,  # Deterministic
                    reasoning=f"Applied cached pattern: {best_pattern['trigger']}"
                )
            
            return None
            
        except Exception as e:
            logger.debug(f"Cached pattern optimization failed: {e}")
            return None
    
    async def _direct_instruction_optimization(self, context: RewriteContext) -> List[RewriteCandidate]:
        """Rule-based direct optimization (1-3 seconds)"""
        
        improvements = []
        current_content = context.current_prompt.content
        
        # Analyze feedback for common issues
        feedback_analysis = self._analyze_feedback_patterns(context.recent_feedback)
        
        # Apply rule-based improvements
        if feedback_analysis.get('clarity_score', 0) < 0.7:
            improvements.append(self._add_clarity_improvements(current_content))
        
        if feedback_analysis.get('structure_score', 0) < 0.6:
            improvements.append(self._add_structure_improvements(current_content))
        
        if feedback_analysis.get('specificity_score', 0) < 0.6:
            improvements.append(self._add_specificity_improvements(current_content))
        
        # Apply best improvement or combine multiple
        if improvements:
            optimized_content = self._apply_rule_based_improvements(current_content, improvements)
        else:
            # Default improvement: add "Think step by step" if not present
            optimized_content = self._add_default_improvements(current_content)
        
        return [RewriteCandidate(
            content=optimized_content,
            confidence=0.7,
            temperature=0.0,
            reasoning="Rule-based direct optimization with template improvements"
        )]
    
    def _build_task_context(self, context: RewriteContext) -> str:
        """Build concise task context description"""
        return f"an AI email assistant that helps with {context.email_scenario} emails"
    
    def _format_performance_feedback(self, context: RewriteContext) -> str:
        """Format performance feedback concisely"""
        if not context.recent_feedback:
            return "No specific feedback available yet."
        
        # Analyze recent feedback for main issues
        issues = []
        
        # Check performance history
        if context.performance_history.get('f1_score', 1.0) < 0.7:
            issues.append("Low accuracy in responses")
        if context.performance_history.get('user_rating', 5) < 3:
            issues.append("Poor user satisfaction")
        
        # Check recent feedback actions
        recent_actions = [f.action for f in context.recent_feedback[-5:]]
        reject_rate = recent_actions.count('reject') / len(recent_actions) if recent_actions else 0
        
        if reject_rate > 0.4:
            issues.append("High rejection rate")
        
        return f"Main issues: {', '.join(issues) if issues else 'Generally good performance, looking for incremental improvements'}"
    
    def _identify_primary_issue(self, context: RewriteContext) -> str:
        """Identify the primary issue to focus optimization on"""
        
        # Analyze feedback patterns
        if not context.recent_feedback:
            return "lack of specific user feedback"
        
        # Count feedback types
        actions = [f.action for f in context.recent_feedback[-10:]]
        
        if actions.count('reject') > len(actions) * 0.4:
            return "high rejection rate - prompt may be unclear or inappropriate"
        
        if actions.count('edit') > len(actions) * 0.3:
            return "frequent edits needed - prompt lacks specificity"
        
        # Check performance metrics
        if context.performance_history.get('f1_score', 1.0) < 0.6:
            return "low accuracy - prompt may not provide clear enough guidance"
        
        return "general refinement needed for better performance"
    
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
    
    # New helper methods for modern optimization techniques
    
    def _get_cached_patterns(self, scenario_type: str) -> List[Dict]:
        """Get cached optimization patterns for scenario type"""
        
        # Pre-computed patterns based on research
        pattern_library = {
            'customer_service': [
                {
                    'trigger': 'low_politeness',
                    'fix': 'add_courtesy_phrases',
                    'template': 'Please be polite and courteous. Start responses with appropriate greetings and end with helpful closures.'
                },
                {
                    'trigger': 'unclear_intent', 
                    'fix': 'explicit_purpose_statement',
                    'template': 'Begin by clearly acknowledging the customer\'s request and state your intent to help.'
                }
            ],
            'technical_support': [
                {
                    'trigger': 'vague_steps',
                    'fix': 'numbered_instructions', 
                    'template': 'Provide step-by-step numbered instructions. Be specific about each action the user should take.'
                },
                {
                    'trigger': 'no_examples',
                    'fix': 'concrete_example_addition',
                    'template': 'Include concrete examples to illustrate your points and make instructions clearer.'
                }
            ],
            'general': [
                {
                    'trigger': 'missing_structure',
                    'fix': 'add_step_by_step',
                    'template': 'Think step by step and organize your response clearly.'
                },
                {
                    'trigger': 'lack_specificity',
                    'fix': 'add_detail_requirement',
                    'template': 'Be specific and detailed in your response. Provide concrete information rather than general statements.'
                }
            ]
        }
        
        return pattern_library.get(scenario_type, pattern_library['general'])
    
    def _select_best_cached_pattern(self, context: RewriteContext, patterns: List[Dict]) -> Optional[Dict]:
        """Select best matching cached pattern based on context"""
        
        # Simple heuristic-based selection
        feedback_analysis = self._analyze_feedback_patterns(context.recent_feedback)
        
        # Match patterns to issues
        if feedback_analysis.get('politeness_score', 1.0) < 0.6:
            return next((p for p in patterns if p['trigger'] == 'low_politeness'), None)
        
        if feedback_analysis.get('clarity_score', 1.0) < 0.6:
            return next((p for p in patterns if p['trigger'] == 'unclear_intent'), None)
        
        if feedback_analysis.get('structure_score', 1.0) < 0.6:
            return next((p for p in patterns if p['trigger'] == 'missing_structure'), None)
        
        # Default to first pattern if no specific match
        return patterns[0] if patterns else None
    
    def _apply_cached_pattern(self, current_prompt: str, pattern: Dict) -> str:
        """Apply cached pattern to current prompt"""
        
        # Simple template-based improvement
        if pattern['fix'] == 'add_courtesy_phrases':
            if 'please' not in current_prompt.lower():
                return f"{current_prompt}\n\n{pattern['template']}"
        
        elif pattern['fix'] == 'add_step_by_step':
            if 'step by step' not in current_prompt.lower():
                return f"Think step by step.\n\n{current_prompt}"
        
        elif pattern['fix'] == 'add_detail_requirement':
            if 'specific' not in current_prompt.lower() and 'detailed' not in current_prompt.lower():
                return f"{current_prompt}\n\n{pattern['template']}"
        
        # Default: prepend template guidance
        return f"{pattern['template']}\n\n{current_prompt}"
    
    def _analyze_feedback_patterns(self, feedback_list: List[UserFeedback]) -> Dict[str, float]:
        """Analyze feedback patterns to identify issues"""
        
        if not feedback_list:
            return {'clarity_score': 0.8, 'structure_score': 0.8, 'specificity_score': 0.8, 'politeness_score': 0.8}
        
        # Simple heuristic analysis
        recent_feedback = feedback_list[-10:]  # Last 10 items
        total_feedback = len(recent_feedback)
        
        # Calculate scores based on action types
        accepts = sum(1 for f in recent_feedback if f.action == 'accept')
        rejects = sum(1 for f in recent_feedback if f.action == 'reject')
        edits = sum(1 for f in recent_feedback if f.action == 'edit')
        
        # Basic scoring heuristics
        clarity_score = max(0.3, (accepts + edits * 0.5) / total_feedback) if total_feedback > 0 else 0.8
        structure_score = max(0.3, accepts / total_feedback) if total_feedback > 0 else 0.8
        specificity_score = max(0.3, (total_feedback - rejects) / total_feedback) if total_feedback > 0 else 0.8
        politeness_score = max(0.3, (total_feedback - rejects * 0.8) / total_feedback) if total_feedback > 0 else 0.8
        
        return {
            'clarity_score': clarity_score,
            'structure_score': structure_score, 
            'specificity_score': specificity_score,
            'politeness_score': politeness_score
        }
    
    def _add_clarity_improvements(self, content: str) -> str:
        """Add clarity improvements to prompt"""
        clarity_additions = [
            "Be clear and specific in your response.",
            "Ensure your answer directly addresses the question.",
            "Use simple, understandable language."
        ]
        
        # Add if not already present
        for addition in clarity_additions:
            if addition.lower() not in content.lower():
                return f"{content}\n\n{addition}"
        
        return content
    
    def _add_structure_improvements(self, content: str) -> str:
        """Add structure improvements to prompt"""
        if 'step by step' not in content.lower():
            return f"Think step by step and organize your response clearly.\n\n{content}"
        return content
    
    def _add_specificity_improvements(self, content: str) -> str:
        """Add specificity improvements to prompt"""
        if 'specific' not in content.lower() and 'detailed' not in content.lower():
            return f"{content}\n\nBe specific and detailed in your response. Provide concrete examples when helpful."
        return content
    
    def _apply_rule_based_improvements(self, content: str, improvements: List[str]) -> str:
        """Apply the best rule-based improvement"""
        # For now, just apply the first improvement
        # In practice, you might want more sophisticated combination logic
        return improvements[0] if improvements else content
    
    def _add_default_improvements(self, content: str) -> str:
        """Add default improvements when no specific issues identified"""
        
        # Add "Think step by step" if not present - research shows this is effective
        if 'step by step' not in content.lower():
            return f"Take a deep breath and think step by step.\n\n{content}"
        
        # Add specificity requirement if not present
        if 'specific' not in content.lower():
            return f"{content}\n\nBe specific and detailed in your response."
        
        return content
    
    async def _get_recent_optimization_history(self, context: RewriteContext, limit: int = 3) -> List[Dict]:
        """Get recent optimization history for OPRO-style trajectory"""
        
        try:
            # Query recent system prompts with performance data
            recent_prompts = []
            
            # This would query recent prompts and their performance in a real implementation
            # For now, return empty to avoid database complexity
            return recent_prompts
            
        except Exception as e:
            logger.debug(f"Failed to get optimization history: {e}")
            return []
    
    def _format_optimization_history(self, history: List[Dict]) -> str:
        """Format optimization history for meta-prompt"""
        
        if not history:
            return "No recent optimization history available."
        
        formatted = ""
        for i, item in enumerate(history):
            formatted += f"{i+1}. Prompt: \"{item.get('prompt', 'Unknown')}\" - Score: {item.get('score', 0.0):.2f}\n"
        
        return formatted
    
    async def _legacy_optimization(self, context: RewriteContext, mode: str) -> List[RewriteCandidate]:
        """Legacy optimization method for backward compatibility"""
        
        # Step 1: Find similar successful prompts from database
        similar_patterns = await self._find_similar_successful_prompts(context)
        
        # Step 2: Get meta-prompt template (fallback to static if manager fails)
        try:
            meta_prompt = await self.meta_prompt_manager.get_meta_prompt(
                context.email_scenario,
                context.constraints
            )
        except:
            meta_prompt = self.static_metaprompt.format(
                current_prompt=context.current_prompt.content,
                task_context=self._build_task_context(context),
                performance_feedback=self._format_performance_feedback(context)
            )
        
        # Step 3: Build comprehensive rewriting instruction
        rewrite_instruction = await self._build_legacy_rewrite_instruction(
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
    
    async def _build_legacy_rewrite_instruction(
        self, 
        context: RewriteContext, 
        meta_prompt: str, 
        similar_patterns: List[SimilarityMatch]
    ) -> str:
        """Build comprehensive instruction for legacy LLM-based rewriting"""
        
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