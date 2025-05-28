from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from django.db import models
from core.models import Email, SystemPrompt, Draft, UserFeedback
from .prompt_rewriter import PromptRewriter, RewriteContext, RewriteCandidate, LLMBasedPromptRewriter
from .reward_aggregator import RewardFunctionAggregator
from .meta_prompt_manager import MetaPromptManager
from dataclasses import dataclass
from asgiref.sync import sync_to_async
import asyncio


@dataclass
class LLMConfiguration:
    """Configuration for LLM providers"""
    provider_type: str  # "openai", "anthropic", "local", etc.
    model_name: str
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    max_tokens: int = 1024
    temperature: float = 0.7
    timeout: int = 30


@dataclass
class DraftGenerationRequest:
    """Request for draft generation"""
    email: Email
    prompt: SystemPrompt
    user_preferences: List[Dict[str, Any]]
    constraints: Optional[Dict[str, Any]] = None


@dataclass
class DraftGenerationResult:
    """Result of draft generation process"""
    drafts: List[Draft]
    prompt_used: SystemPrompt
    original_prompt: SystemPrompt
    rewrite_applied: bool
    rewrite_reasoning: Optional[str] = None
    performance_metrics: Optional[Dict[str, float]] = None


class TaskLLMProvider(ABC):
    """Abstract interface for task LLM providers"""
    
    @abstractmethod
    async def generate_drafts(
        self,
        email: Email,
        system_prompt: SystemPrompt,
        user_preferences: List[Dict[str, Any]],
        num_drafts: int = 2
    ) -> List[Draft]:
        """Generate draft responses using the task LLM"""
        pass
    
    @abstractmethod
    async def evaluate_response_quality(
        self,
        email: Email,
        response: str,
        criteria: Dict[str, Any]
    ) -> Dict[str, float]:
        """Evaluate quality of generated response"""
        pass


class OpenAITaskLLM(TaskLLMProvider):
    """OpenAI implementation of task LLM provider"""
    
    def __init__(self, config: LLMConfiguration, llm_provider):
        self.config = config
        self.llm_provider = llm_provider  # Existing OpenAIProvider
    
    async def generate_drafts(
        self,
        email: Email,
        system_prompt: SystemPrompt,
        user_preferences: List[Dict[str, Any]],
        num_drafts: int = 2
    ) -> List[Draft]:
        """Generate drafts using existing OpenAI provider"""
        
        # Convert user_preferences dict to UserPreference objects for compatibility
        from core.models import UserPreference
        
        # This is a temporary conversion - in real implementation,
        # we'd properly handle the preference format
        pref_objects = []
        for pref_dict in user_preferences:
            pref_obj = type('TempPref', (), {
                'key': pref_dict.get('key', 'tone'),
                'value': pref_dict.get('value', 'professional'),
                'is_active': pref_dict.get('is_active', True)
            })()
            pref_objects.append(pref_obj)
        
        # Use existing LLM provider
        drafts = await self.llm_provider.generate_drafts(
            email, 
            system_prompt, 
            pref_objects
        )
        
        return drafts
    
    async def evaluate_response_quality(
        self,
        email: Email,
        response: str,
        criteria: Dict[str, Any]
    ) -> Dict[str, float]:
        """Evaluate response quality using the task LLM"""
        
        evaluation_prompt = f"""
Evaluate the following email response based on these criteria: {criteria}

Original Email:
Subject: {email.subject}
From: {email.sender}
Body: {email.body}

Response:
{response}

Rate each criterion on a scale of 0.0 to 1.0 and provide scores in JSON format:
{{"relevance": 0.0, "clarity": 0.0, "professionalism": 0.0, "completeness": 0.0}}
"""
        
        try:
            # Use the LLM to evaluate the response
            evaluation_result = await self.llm_provider.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": evaluation_prompt}],
                temperature=0.1,  # Low temperature for consistent evaluation
                max_tokens=200
            )
            
            import json
            import re
            
            content = evaluation_result.choices[0].message.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                scores = json.loads(json_match.group())
                return scores
            else:
                # Fallback scores
                return {"relevance": 0.7, "clarity": 0.7, "professionalism": 0.7, "completeness": 0.7}
                
        except Exception as e:
            print(f"Error evaluating response quality: {e}")
            return {"relevance": 0.5, "clarity": 0.5, "professionalism": 0.5, "completeness": 0.5}


class DualLLMCoordinator:
    """Coordinates between prompt rewriter LLM and task LLM"""
    
    def __init__(
        self,
        prompt_rewriter: PromptRewriter,
        task_llm: TaskLLMProvider,
        reward_aggregator: RewardFunctionAggregator,
        meta_prompt_manager: MetaPromptManager,
        auto_rewrite: bool = True,
        rewrite_threshold: float = 0.6
    ):
        self.prompt_rewriter = prompt_rewriter
        self.task_llm = task_llm
        self.reward_aggregator = reward_aggregator
        self.meta_prompt_manager = meta_prompt_manager
        self.auto_rewrite = auto_rewrite
        self.rewrite_threshold = rewrite_threshold
        self.performance_history = {}
    
    async def generate_drafts_with_optimization(
        self,
        request: DraftGenerationRequest
    ) -> DraftGenerationResult:
        """Generate drafts with optional prompt optimization"""
        
        original_prompt = request.prompt
        prompt_to_use = original_prompt
        rewrite_applied = False
        rewrite_reasoning = None
        
        # Determine if prompt rewriting should be applied
        should_rewrite = await self._should_rewrite_prompt(request)
        
        if should_rewrite and self.auto_rewrite:
            # Perform prompt rewriting
            rewrite_result = await self._rewrite_prompt_for_request(request)
            if rewrite_result:
                prompt_to_use = rewrite_result['prompt']
                rewrite_applied = True
                rewrite_reasoning = rewrite_result['reasoning']
        
        # Generate drafts using the (possibly rewritten) prompt
        drafts = await self.task_llm.generate_drafts(
            request.email,
            prompt_to_use,
            request.user_preferences,
            num_drafts=2
        )
        
        # Evaluate performance
        performance_metrics = await self._evaluate_generation_performance(
            request.email,
            drafts,
            prompt_to_use
        )
        
        # Store performance for future rewrite decisions
        self._update_performance_history(
            request.email.scenario_type,
            original_prompt.id,
            performance_metrics,
            rewrite_applied
        )
        
        return DraftGenerationResult(
            drafts=drafts,
            prompt_used=prompt_to_use,
            original_prompt=original_prompt,
            rewrite_applied=rewrite_applied,
            rewrite_reasoning=rewrite_reasoning,
            performance_metrics=performance_metrics
        )
    
    async def _should_rewrite_prompt(self, request: DraftGenerationRequest) -> bool:
        """Determine if prompt should be rewritten based on performance history"""
        
        scenario = request.email.scenario_type
        prompt_id = request.prompt.id
        
        # Check recent performance for this prompt/scenario combination
        key = f"{scenario}_{prompt_id}"
        
        if key in self.performance_history:
            recent_performance = self.performance_history[key]
            avg_performance = sum(recent_performance[-5:]) / min(len(recent_performance), 5)
            
            # Rewrite if performance is below threshold
            return avg_performance < self.rewrite_threshold
        
        # Default to rewriting for new prompt/scenario combinations
        return True
    
    async def _rewrite_prompt_for_request(
        self,
        request: DraftGenerationRequest
    ) -> Optional[Dict[str, Any]]:
        """Rewrite prompt for the given request"""
        
        try:
            # Build rewrite context
            context = RewriteContext(
                email_scenario=request.email.scenario_type,
                current_prompt=request.prompt,
                recent_feedback=[],  # TODO: Get recent feedback for this prompt
                performance_history=self.performance_history.get(
                    f"{request.email.scenario_type}_{request.prompt.id}", []
                ),
                constraints=request.constraints or {}
            )
            
            # Generate rewrite candidates
            candidates = await self.prompt_rewriter.rewrite_prompt(
                context,
                mode="conservative"  # Use conservative mode for production
            )
            
            if not candidates:
                return None
            
            # Select best candidate
            evaluation_context = {
                'email_scenario': request.email.scenario_type,
                'original_prompt': request.prompt.content,
                'expected_output': '',  # Would be set based on email content analysis
                'constraints': request.constraints or {}
            }
            
            best_candidate = await self.prompt_rewriter.select_best_candidate(
                candidates,
                evaluation_context
            )
            
            # Create new SystemPrompt object
            from core.models import SystemPrompt
            from asgiref.sync import sync_to_async
            
            # Find next available version number
            latest_version = await sync_to_async(
                lambda: SystemPrompt.objects.aggregate(
                    max_version=models.Max('version')
                )['max_version'] or 0
            )()
            
            rewritten_prompt = await sync_to_async(SystemPrompt.objects.create)(
                content=best_candidate.content,
                version=latest_version + 1,
                is_active=False,  # Don't activate automatically
                performance_score=None
            )
            
            return {
                'prompt': rewritten_prompt,
                'reasoning': best_candidate.reasoning,
                'confidence': best_candidate.confidence
            }
            
        except Exception as e:
            print(f"Error rewriting prompt: {e}")
            return None
    
    async def _evaluate_generation_performance(
        self,
        email: Email,
        drafts: List[Draft],
        prompt: SystemPrompt
    ) -> Dict[str, float]:
        """Evaluate the performance of draft generation"""
        
        if not drafts:
            return {"overall_quality": 0.0}
        
        # Evaluate each draft
        draft_scores = []
        
        for draft in drafts:
            scores = await self.task_llm.evaluate_response_quality(
                email,
                draft.content,
                {
                    "relevance": "How relevant is the response to the email?",
                    "clarity": "How clear and well-written is the response?",
                    "professionalism": "How professional is the tone?",
                    "completeness": "How complete is the response?"
                }
            )
            
            # Calculate overall score for this draft
            overall = sum(scores.values()) / len(scores)
            draft_scores.append(overall)
        
        # Calculate aggregate metrics
        performance_metrics = {
            "overall_quality": sum(draft_scores) / len(draft_scores),
            "best_draft_quality": max(draft_scores),
            "consistency": 1.0 - (max(draft_scores) - min(draft_scores)),  # Higher is better
            "num_drafts": len(drafts)
        }
        
        return performance_metrics
    
    def _update_performance_history(
        self,
        scenario: str,
        prompt_id: int,
        performance_metrics: Dict[str, float],
        rewrite_applied: bool
    ):
        """Update performance history for future rewrite decisions"""
        
        key = f"{scenario}_{prompt_id}"
        
        if key not in self.performance_history:
            self.performance_history[key] = []
        
        # Store overall quality score
        overall_quality = performance_metrics.get("overall_quality", 0.0)
        self.performance_history[key].append(overall_quality)
        
        # Keep only recent history (last 20 entries)
        self.performance_history[key] = self.performance_history[key][-20:]
    
    async def process_user_feedback(
        self,
        original_prompt: SystemPrompt,
        rewritten_prompt: Optional[SystemPrompt],
        user_feedback: UserFeedback,
        generation_result: DraftGenerationResult
    ):
        """Process user feedback to improve future rewriting"""
        
        if not rewritten_prompt:
            return
        
        # Convert feedback to reward signal
        task_performance = generation_result.performance_metrics or {}
        
        # Update prompt rewriter with feedback
        await self.prompt_rewriter.update_from_feedback(
            original_prompt,
            rewritten_prompt.content,
            user_feedback,
            task_performance
        )
        
        # Update reward aggregator weights if needed
        scenario = generation_result.drafts[0].email.scenario_type if generation_result.drafts else "general"
        
        # Update meta-prompt effectiveness
        await self.meta_prompt_manager.optimize_template_selection({
            scenario: task_performance.get("overall_quality", 0.5)
        })
    
    async def get_coordination_metrics(self) -> Dict[str, Any]:
        """Get metrics about the coordination between LLMs"""
        
        total_scenarios = len(self.performance_history)
        
        if total_scenarios == 0:
            return {"total_scenarios": 0, "average_performance": 0.0}
        
        # Calculate overall performance metrics
        all_scores = []
        for scores in self.performance_history.values():
            all_scores.extend(scores)
        
        avg_performance = sum(all_scores) / len(all_scores) if all_scores else 0.0
        
        # Count scenarios that might benefit from rewriting
        scenarios_needing_improvement = sum(
            1 for scores in self.performance_history.values()
            if scores and (sum(scores[-3:]) / min(len(scores), 3)) < self.rewrite_threshold
        )
        
        return {
            "total_scenarios": total_scenarios,
            "average_performance": avg_performance,
            "scenarios_needing_improvement": scenarios_needing_improvement,
            "rewrite_threshold": self.rewrite_threshold,
            "auto_rewrite_enabled": self.auto_rewrite,
            "performance_history_size": len(all_scores)
        }
    
    def configure_rewriting(
        self,
        auto_rewrite: bool,
        rewrite_threshold: float
    ):
        """Configure rewriting behavior"""
        self.auto_rewrite = auto_rewrite
        self.rewrite_threshold = max(0.0, min(1.0, rewrite_threshold))