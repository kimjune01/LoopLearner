from abc import ABC, abstractmethod
from typing import List, Dict, Any
from core.models import Email, Draft, DraftReason, SystemPrompt, UserPreference
import openai
import json
import re
from asgiref.sync import sync_to_async


class LLMProvider(ABC):
    """Abstract interface for LLM providers"""
    
    @abstractmethod
    async def generate_drafts(
        self, 
        email: Email, 
        system_prompt: SystemPrompt,
        user_preferences: List[UserPreference]
    ) -> List[Draft]:
        """Generate multiple draft responses for an email"""
        pass
    
    @abstractmethod
    async def optimize_prompt(
        self,
        current_prompt: SystemPrompt,
        feedback_data: List[Dict[str, Any]],
        evaluation_snapshots: List[Dict[str, Any]]
    ) -> str:
        """Optimize system prompt based on feedback"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of LLM provider"""
    
    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def generate_drafts(
        self, 
        email: Email, 
        system_prompt: SystemPrompt,
        user_preferences: List[UserPreference]
    ) -> List[Draft]:
        """Generate multiple draft responses for an email"""
        # Build user preferences string
        preferences_text = "\n".join([
            f"- {pref.key}: {pref.value}" 
            for pref in user_preferences if pref.is_active
        ])
        
        # Create the full system prompt
        full_prompt = f"""
{system_prompt.content}

User Preferences:
{preferences_text}

IMPORTANT: You must generate exactly 2 different draft responses. 
For each draft, also provide 2-3 reasoning factors that explain why you chose that approach.

Format your response as JSON:
{{
    "drafts": [
        {{
            "content": "Your draft response here",
            "reasons": [
                {{"text": "Reason 1", "confidence": 0.8}},
                {{"text": "Reason 2", "confidence": 0.9}}
            ]
        }},
        {{
            "content": "Your second draft response here", 
            "reasons": [
                {{"text": "Reason 1", "confidence": 0.7}},
                {{"text": "Reason 2", "confidence": 0.85}}
            ]
        }}
    ]
}}
"""
        
        user_message = f"""
Original Email:
Subject: {email.subject}
From: {email.sender}
Body: {email.body}

Please generate 2 draft responses to this email.
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": full_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            # Try to extract JSON from the response
            try:
                # Look for JSON block in the response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    data = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            except (json.JSONDecodeError, ValueError):
                # Fallback: create simple drafts from the text response
                data = {
                    "drafts": [
                        {
                            "content": content[:len(content)//2],
                            "reasons": [
                                {"text": "Generated from LLM response", "confidence": 0.7}
                            ]
                        },
                        {
                            "content": content[len(content)//2:],
                            "reasons": [
                                {"text": "Generated from LLM response", "confidence": 0.7}
                            ]
                        }
                    ]
                }
            
            # Create Draft objects with reasons
            drafts = []
            for draft_data in data.get("drafts", []):
                # Create draft
                draft = await sync_to_async(Draft.objects.create)(
                    email=email,
                    content=draft_data["content"],
                    system_prompt=system_prompt
                )
                
                # Create and associate reasons
                for reason_data in draft_data.get("reasons", []):
                    reason = await sync_to_async(DraftReason.objects.create)(
                        text=reason_data["text"],
                        confidence=reason_data.get("confidence", 0.5)
                    )
                    await sync_to_async(draft.reasons.add)(reason)
                
                drafts.append(draft)
            
            return drafts
            
        except Exception as e:
            # TODO: Add proper logging
            raise NotImplementedError(f"OpenAI draft generation failed: {str(e)}")
    
    async def optimize_prompt(
        self,
        current_prompt: SystemPrompt,
        feedback_data: List[Dict[str, Any]],
        evaluation_snapshots: List[Dict[str, Any]]
    ) -> str:
        """Optimize system prompt based on feedback"""
        
        # Prepare feedback summary
        feedback_summary = self._summarize_feedback(feedback_data)
        
        optimization_prompt = f"""
You are an expert at optimizing system prompts for email response generation based on human feedback.

Current System Prompt:
{current_prompt.content}

User Feedback Summary:
{feedback_summary}

Evaluation Data:
{json.dumps(evaluation_snapshots[:5], indent=2)}  # Limit to recent snapshots

Please analyze the feedback and create an improved version of the system prompt that:
1. Addresses the issues identified in user feedback
2. Maintains the core functionality
3. Incorporates lessons learned from the evaluation data
4. Is clear and actionable for an AI assistant

Return only the improved system prompt, without explanations.
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": optimization_prompt}
                ],
                temperature=0.3  # Lower temperature for more consistent optimization
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise NotImplementedError(f"Prompt optimization failed: {str(e)}")
    
    def _summarize_feedback(self, feedback_data: List[Dict[str, Any]]) -> str:
        """Create a summary of user feedback for prompt optimization"""
        if not feedback_data:
            return "No feedback available."
        
        summary_parts = []
        
        # Count actions
        actions = {}
        for feedback in feedback_data:
            action = feedback.get('action', 'unknown')
            actions[action] = actions.get(action, 0) + 1
        
        summary_parts.append(f"Action Distribution: {actions}")
        
        # Collect reasons for rejections and edits
        negative_feedback = []
        for feedback in feedback_data:
            if feedback.get('action') in ['reject', 'edit'] and feedback.get('reason'):
                negative_feedback.append(feedback['reason'])
        
        if negative_feedback:
            summary_parts.append(f"Common Issues: {'; '.join(negative_feedback[:5])}")
        
        # Collect reason ratings patterns
        liked_reasons = []
        disliked_reasons = []
        
        for feedback in feedback_data:
            for reason_id, liked in feedback.get('reason_ratings', {}).items():
                reason_text = reason_id  # Simplified - in real implementation, look up reason text
                if liked:
                    liked_reasons.append(reason_text)
                else:
                    disliked_reasons.append(reason_text)
        
        if liked_reasons:
            summary_parts.append(f"Appreciated Reasoning: {'; '.join(liked_reasons[:3])}")
        if disliked_reasons:
            summary_parts.append(f"Problematic Reasoning: {'; '.join(disliked_reasons[:3])}")
        
        return "\n".join(summary_parts)