"""
Unified LLM Provider System
Supports multiple backends: Ollama (local), OpenAI, Anthropic, etc.
Configurable via environment variables for easy switching
"""

import asyncio
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import json


@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: str  # "ollama", "openai", "anthropic", "mock"
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 500


@dataclass
class EmailDraft:
    """Standardized email draft response"""
    content: str
    reasoning: List[str]
    confidence: float
    draft_id: int
    metadata: Dict[str, Any] = None


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate text response"""
        pass
    
    @abstractmethod
    async def generate_drafts(
        self, 
        email_content: str, 
        system_prompt: str,
        user_preferences: List[Dict[str, Any]] = None,
        constraints: Dict[str, Any] = None,
        num_drafts: int = 3
    ) -> List[EmailDraft]:
        """Generate multiple email draft responses"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health and availability"""
        pass
    
    @abstractmethod
    async def get_log_probabilities(
        self,
        text: str,
        context: Optional[str] = None
    ) -> List[float]:
        """Get log probabilities for each token in the text"""
        pass


class OllamaProvider(BaseLLMProvider):
    """Ollama local model provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        import ollama
        base_url = config.base_url or "localhost:11434"
        self.client = ollama.Client(host=f"http://{base_url}")
    
    async def generate(
        self, 
        prompt: str, 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate text using Ollama"""
        
        temp = temperature or self.config.temperature
        tokens = max_tokens or self.config.max_tokens
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await asyncio.to_thread(
                self.client.chat,
                model=self.config.model,
                messages=messages,
                options={"temperature": temp, "num_predict": tokens}
            )
            return response['message']['content'].strip()
        except Exception as e:
            return f"Ollama Error: {str(e)}"
    
    async def generate_drafts(
        self, 
        email_content: str, 
        system_prompt: str,
        user_preferences: List[Dict[str, Any]] = None,
        constraints: Dict[str, Any] = None,
        num_drafts: int = 3
    ) -> List[EmailDraft]:
        """Generate email drafts using Ollama"""
        
        drafts = []
        for i in range(num_drafts):
            temperature = 0.3 + (i * 0.3)  # Vary temperature for diversity
            
            prompt = self._build_draft_prompt(
                email_content, user_preferences, constraints, i+1
            )
            
            response = await self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=800
            )
            
            draft = self._parse_draft_response(response, i+1)
            drafts.append(draft)
        
        return drafts
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama health"""
        try:
            response = await asyncio.to_thread(
                self.client.chat,
                model=self.config.model,
                messages=[{"role": "user", "content": "Hello"}],
                options={"num_predict": 5}
            )
            return {
                "status": "healthy",
                "provider": "ollama",
                "model": self.config.model,
                "response_sample": response['message']['content'][:30]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "ollama", 
                "model": self.config.model,
                "error": str(e)
            }
    
    async def get_log_probabilities(
        self,
        text: str,
        context: Optional[str] = None
    ) -> List[float]:
        """Get log probabilities for each token in the text"""
        try:
            # Ollama doesn't directly support logprobs, so use LLM-based estimation
            if context:
                eval_prompt = f"""
Given this context: "{context}"

Rate the likelihood of each word in this continuation on a scale where:
- Very likely/common words: 0.9-1.0
- Moderately likely words: 0.6-0.8  
- Unlikely/uncommon words: 0.3-0.5
- Very unlikely words: 0.1-0.2

Text to evaluate: "{text}"

Provide likelihood scores for each word as a JSON list: [0.8, 0.6, 0.9, ...]
"""
            else:
                eval_prompt = f"""
Rate the likelihood of each word in this text on a scale where:
- Very common words (the, and, is): 0.9-1.0
- Common words: 0.6-0.8
- Uncommon words: 0.3-0.5  
- Very rare words: 0.1-0.2

Text: "{text}"

Provide likelihood scores for each word as a JSON list: [0.8, 0.6, 0.9, ...]
"""
            
            response = await self.generate(eval_prompt, temperature=0.1, max_tokens=200)
            
            # Try to extract JSON array from response
            import json
            import re
            
            json_match = re.search(r'\[[\d\.\,\s]+\]', response)
            if json_match:
                likelihood_scores = json.loads(json_match.group())
                # Convert likelihood scores to log probabilities
                import math
                log_probs = [math.log(max(score, 0.001)) for score in likelihood_scores]
                return log_probs
            else:
                return self._estimate_log_probabilities(text)
                
        except Exception as e:
            return self._estimate_log_probabilities(text)
    
    def _estimate_log_probabilities(self, text: str) -> List[float]:
        """Estimate log probabilities based on text characteristics"""
        import re
        import math
        
        words = text.split()
        log_probs = []
        
        for word in words:
            if len(word) <= 3:
                likelihood = 0.8
            elif word.lower() in ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that', 'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'at']:
                likelihood = 0.9
            elif re.match(r'^[A-Z][a-z]+$', word):
                likelihood = 0.3
            elif word.isdigit():
                likelihood = 0.4
            else:
                likelihood = 0.6
            
            log_prob = math.log(max(likelihood, 0.001))
            log_probs.append(log_prob)
        
        return log_probs
    
    def _build_draft_prompt(self, email_content: str, user_preferences: List[Dict] = None, 
                          constraints: Dict = None, draft_num: int = 1) -> str:
        """Build structured prompt for draft generation"""
        
        parts = [
            f"Generate professional email response (Draft #{draft_num}):",
            f"\n--- INCOMING EMAIL ---\n{email_content}\n--- END EMAIL ---\n"
        ]
        
        if user_preferences:
            parts.append("USER PREFERENCES:")
            for pref in user_preferences:
                if pref.get('is_active', True):
                    parts.append(f"- {pref['key']}: {pref['value']}")
            parts.append("")
        
        if constraints:
            parts.append("CONSTRAINTS:")
            for key, value in constraints.items():
                parts.append(f"- {key}: {value}")
            parts.append("")
        
        # Style variation by draft number
        styles = {
            1: "STYLE: Formal and professional",
            2: "STYLE: Friendly and conversational", 
            3: "STYLE: Concise and direct"
        }
        parts.append(styles.get(draft_num, "STYLE: Professional"))
        
        parts.extend([
            "",
            "FORMAT YOUR RESPONSE EXACTLY AS:",
            "DRAFT:",
            "[Your email response here]",
            "",
            "REASONING:",
            "1. [First reasoning factor]",
            "2. [Second reasoning factor]",
            "3. [Third reasoning factor]"
        ])
        
        return "\n".join(parts)
    
    def _parse_draft_response(self, response: str, draft_id: int) -> EmailDraft:
        """Parse LLM response into structured EmailDraft"""
        
        try:
            # Extract draft content
            if "REASONING:" in response:
                draft_content = response.split("REASONING:")[0].replace("DRAFT:", "").strip()
                reasoning_text = response.split("REASONING:")[1].strip()
            else:
                draft_content = response.replace("DRAFT:", "").strip()
                reasoning_text = ""
            
            # Extract reasoning factors
            reasoning = []
            for line in reasoning_text.split('\n'):
                line = line.strip()
                if any(line.startswith(p) for p in ['1.', '2.', '3.', '-', '•']):
                    clean = line
                    for prefix in ['1.', '2.', '3.', '-', '•']:
                        clean = clean.replace(prefix, '', 1).strip()
                    if clean:
                        reasoning.append(clean)
            
            # Fallback reasoning if none found
            if not reasoning:
                reasoning = [
                    "Professional tone maintained",
                    "Addresses key points from original email",
                    "Appropriate length and structure"
                ]
            
            # Calculate confidence
            confidence = self._calculate_confidence(draft_content, reasoning)
            
            return EmailDraft(
                content=draft_content,
                reasoning=reasoning[:3],
                confidence=confidence,
                draft_id=draft_id,
                metadata={"provider": "ollama", "model": self.config.model}
            )
            
        except Exception as e:
            return EmailDraft(
                content=response[:300] + "..." if len(response) > 300 else response,
                reasoning=["Error parsing response", "Content may need review"],
                confidence=0.3,
                draft_id=draft_id,
                metadata={"error": str(e)}
            )
    
    def _calculate_confidence(self, content: str, reasoning: List[str]) -> float:
        """Calculate confidence score based on response quality"""
        confidence = 0.6  # Base
        
        if 30 <= len(content) <= 800: confidence += 0.1
        if len(reasoning) >= 3: confidence += 0.1
        if any(word in content.lower() for word in ['thank', 'please', 'regards']): confidence += 0.1
        if not any(word in content.lower() for word in ['error', 'fail', 'issue']): confidence += 0.1
        
        return min(1.0, confidence)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        import openai
        self.client = openai.AsyncOpenAI(api_key=config.api_key)
    
    async def generate(
        self, 
        prompt: str, 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate text using OpenAI API"""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"OpenAI Error: {str(e)}"
    
    async def generate_drafts(
        self, 
        email_content: str, 
        system_prompt: str,
        user_preferences: List[Dict[str, Any]] = None,
        constraints: Dict[str, Any] = None,
        num_drafts: int = 3
    ) -> List[EmailDraft]:
        """Generate email drafts using OpenAI"""
        # Similar implementation to Ollama but using OpenAI API
        # Implementation would be similar to OllamaProvider.generate_drafts()
        # but using self.client.chat.completions.create()
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI API health"""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return {
                "status": "healthy",
                "provider": "openai",
                "model": self.config.model,
                "response_sample": response.choices[0].message.content[:30]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "openai",
                "model": self.config.model,
                "error": str(e)
            }
    
    async def get_log_probabilities(
        self,
        text: str,
        context: Optional[str] = None
    ) -> List[float]:
        """Get log probabilities for each token in the text using echo technique"""
        try:
            # Use the "echo" technique: provide the text as assistant message and ask model to echo it
            messages = []
            if context:
                messages.append({"role": "user", "content": context})
                messages.append({"role": "assistant", "content": text})
                messages.append({"role": "user", "content": "Please repeat exactly what you just said."})
            else:
                messages.append({"role": "user", "content": f"Please repeat this exactly: {text}"})
            
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=0.0,  # Deterministic for probability calculation
                max_tokens=len(text.split()) + 20,  # Enough tokens to echo the text
                logprobs=True,
                top_logprobs=1
            )
            
            # Extract log probabilities from response
            if response.choices[0].logprobs and response.choices[0].logprobs.content:
                log_probs = []
                for token_data in response.choices[0].logprobs.content:
                    if token_data.logprob is not None:
                        log_probs.append(token_data.logprob)
                return log_probs
            else:
                return self._estimate_log_probabilities(text)
                
        except Exception as e:
            return self._estimate_log_probabilities(text)
    
    def _estimate_log_probabilities(self, text: str) -> List[float]:
        """Estimate log probabilities based on text characteristics"""
        import re
        
        words = text.split()
        log_probs = []
        
        for word in words:
            if len(word) <= 3:
                log_prob = -2.0
            elif word.lower() in ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that', 'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'at']:
                log_prob = -1.5
            elif re.match(r'^[A-Z][a-z]+$', word):
                log_prob = -4.0
            elif word.isdigit():
                log_prob = -3.5
            else:
                log_prob = -3.0
            
            log_probs.append(log_prob)
        
        return log_probs


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(
                api_key=config.api_key,
                base_url=config.base_url
            )
        except ImportError:
            raise ImportError("anthropic package required for Anthropic provider. Install with: pip install anthropic")
    
    async def generate(
        self, 
        prompt: str, 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate text using Claude"""
        try:
            temp = temperature if temperature is not None else self.config.temperature
            tokens = max_tokens if max_tokens is not None else self.config.max_tokens
            
            # Claude uses messages format
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": self.config.model,
                "messages": messages,
                "temperature": temp,
                "max_tokens": tokens
            }
            
            # Add system prompt if provided
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = await self.client.messages.create(**kwargs)
            
            # Extract text from response
            if response.content and len(response.content) > 0:
                return response.content[0].text
            else:
                return ""
                
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    async def generate_drafts(
        self, 
        email_content: str, 
        system_prompt: str, 
        num_drafts: int = 3,
        **kwargs
    ) -> List[EmailDraft]:
        """Generate email drafts using Claude"""
        try:
            prompt = f"""Please generate {num_drafts} different email draft responses to the following email:

Email: {email_content}

For each draft, provide:
1. The email response content
2. 3 reasoning factors explaining your approach
3. A confidence score (0.0-1.0)

Format your response as JSON with this structure:
{{
  "drafts": [
    {{
      "content": "email response text",
      "reasoning": ["reason 1", "reason 2", "reason 3"],
      "confidence": 0.85
    }}
  ]
}}"""

            response_text = await self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1000)
            )
            
            # Parse JSON response
            import json
            try:
                data = json.loads(response_text)
                drafts = []
                
                for i, draft_data in enumerate(data.get('drafts', [])):
                    draft = EmailDraft(
                        content=draft_data.get('content', f'Draft {i+1} content'),
                        reasoning=draft_data.get('reasoning', [f'Reasoning {i+1}']),
                        confidence=draft_data.get('confidence', 0.7),
                        draft_id=i+1,
                        metadata={"provider": "anthropic", "model": self.config.model}
                    )
                    drafts.append(draft)
                
                return drafts
                
            except json.JSONDecodeError:
                # Fallback: create basic drafts from text response
                return [
                    EmailDraft(
                        content=response_text[:500],
                        reasoning=["AI-generated response", "Professional tone", "Contextually appropriate"],
                        confidence=0.7,
                        draft_id=1,
                        metadata={"provider": "anthropic", "model": self.config.model}
                    )
                ]
                
        except Exception as e:
            # Return error draft
            return [
                EmailDraft(
                    content=f"Error generating draft: {str(e)}",
                    reasoning=["Error occurred", "Fallback response", "Manual review needed"],
                    confidence=0.1,
                    draft_id=1,
                    metadata={"provider": "anthropic", "error": str(e)}
                )
            ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Anthropic API health"""
        try:
            response = await self.client.messages.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return {
                "status": "healthy",
                "provider": "anthropic",
                "model": self.config.model,
                "response_sample": response.content[0].text[:30] if response.content else ""
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "anthropic",
                "model": self.config.model,
                "error": str(e)
            }
    
    async def get_log_probabilities(
        self,
        text: str,
        context: Optional[str] = None
    ) -> List[float]:
        """
        Anthropic doesn't provide log probabilities directly.
        Use estimated probabilities based on text characteristics.
        """
        return self._estimate_log_probabilities(text)
    
    def _estimate_log_probabilities(self, text: str) -> List[float]:
        """Estimate log probabilities based on text characteristics"""
        import re
        import math
        
        words = text.split()
        log_probs = []
        
        for word in words:
            # Estimate likelihood based on word characteristics
            if len(word) <= 3:
                likelihood = 0.8  # Short words are common
            elif word.lower() in ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that', 'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'at']:
                likelihood = 0.9  # Common words
            elif re.match(r'^[A-Z][a-z]+$', word):
                likelihood = 0.3  # Proper nouns are less predictable
            elif word.isdigit():
                likelihood = 0.4  # Numbers are somewhat predictable
            else:
                likelihood = 0.6  # Default likelihood
            
            # Convert to log probability
            log_prob = math.log(max(likelihood, 0.001))
            log_probs.append(log_prob)
        
        return log_probs


class MockProvider(BaseLLMProvider):
    """Mock provider for testing"""
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        # Generate more realistic responses for evaluation testing
        if system_prompt and "email assistant" in system_prompt.lower():
            return self._generate_mock_email_response(prompt, system_prompt)
        elif "email" in prompt.lower() or "subject:" in prompt.lower():
            return self._generate_mock_email_response(prompt, system_prompt)
        else:
            return f"Mock response to: {prompt[:50]}..."
    
    def _generate_mock_email_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a realistic mock email response"""
        import random
        
        # Extract key information from the prompt
        prompt_lower = prompt.lower()
        
        # Determine email type and generate appropriate response
        if "shipping" in prompt_lower or "address" in prompt_lower:
            responses = [
                """<improved_email>
Subject: Re: Update Shipping Address for Recent Order

Dear Lisa Wang,

Thank you for reaching out regarding your recent order. I'd be happy to help you update your shipping address.

To process this change, I'll need your order number and the new shipping address. Please note that if your order has already been shipped, we may need to contact our carrier to redirect the package.

Could you please provide:
- Your order number
- The updated shipping address
- Your preferred delivery date if you have one

I'll process this update immediately once I receive this information.

Best regards,
Customer Service Team
</improved_email>""",
                """<improved_email>
Subject: Shipping Address Update Confirmation

Dear Lisa Wang,

Thank you for contacting us about updating your shipping address for your recent order.

I've successfully updated your shipping address in our system. Your order will now be delivered to the new address you provided.

You can expect delivery within 3-5 business days. You'll receive a tracking confirmation email once your order ships.

If you have any other questions, please don't hesitate to reach out.

Warm regards,
Customer Support
</improved_email>"""
            ]
        elif "meeting" in prompt_lower or "schedule" in prompt_lower:
            responses = [
                """<improved_email>
Subject: Re: Meeting Request

Thank you for your email. I'd be happy to schedule a meeting with you.

I have availability on the following dates and times:
- Tuesday, June 4th at 2:00 PM
- Wednesday, June 5th at 10:00 AM  
- Friday, June 7th at 3:30 PM

Please let me know which time works best for you, and I'll send a calendar invitation.

Best regards,
[Your Name]
</improved_email>""",
                """<improved_email>
Subject: Meeting Confirmation

Thank you for scheduling our meeting. I'm looking forward to our discussion.

Meeting Details:
- Date: Wednesday, June 5th
- Time: 10:00 AM - 11:00 AM
- Location: Conference Room B / Zoom (link to follow)

I'll prepare an agenda and send it to you by tomorrow.

Best regards,
[Your Name]
</improved_email>"""
            ]
        elif "project" in prompt_lower or "status" in prompt_lower or "update" in prompt_lower:
            responses = [
                """<improved_email>
Subject: Project Status Update

Thank you for requesting an update on the project status.

Here's the current progress:
- Phase 1: Completed (100%)
- Phase 2: In progress (75% complete)
- Phase 3: Scheduled to begin next week

We're on track to meet our deadline of June 15th. I'll continue to provide weekly updates as we progress.

Please let me know if you need any additional details.

Best regards,
[Your Name]
</improved_email>""",
                """<improved_email>
Subject: Re: Project Status Update Required

Dear [Name],

Thank you for your inquiry about the project status. I'm pleased to provide you with the latest update.

Current Status:
✓ Requirements gathering: Complete
✓ Design phase: Complete  
• Development: 80% complete
• Testing: Scheduled for next week
• Deployment: On schedule for June 20th

We're meeting all major milestones and remain on budget. I'll have a more detailed report ready for tomorrow's stakeholder meeting.

Best regards,
Project Manager
</improved_email>"""
            ]
        elif "thank" in prompt_lower or "follow" in prompt_lower:
            responses = [
                """<improved_email>
Subject: Thank You

Thank you for your email and for taking the time to reach out.

I appreciate your interest and will review your request carefully. I'll get back to you within 24 hours with a detailed response.

In the meantime, please don't hesitate to contact me if you have any urgent questions.

Best regards,
[Your Name]
</improved_email>""",
                """<improved_email>
Subject: Following Up

Thank you for our conversation yesterday. I wanted to follow up on the points we discussed.

As promised, I've attached the documents you requested. Please review them at your convenience and let me know if you have any questions.

I look forward to hearing your thoughts and moving forward with our collaboration.

Best regards,
[Your Name]
</improved_email>"""
            ]
        else:
            # Generic professional email response
            responses = [
                """<improved_email>
Subject: Re: Your Inquiry

Thank you for your email. I've received your message and wanted to acknowledge it promptly.

I'll review the details you've provided and get back to you with a comprehensive response within 24 hours.

If you have any urgent questions in the meantime, please don't hesitate to contact me directly.

Best regards,
[Your Name]
</improved_email>""",
                """<improved_email>
Subject: Response to Your Request

Dear [Name],

Thank you for reaching out. I appreciate you taking the time to contact us.

I've noted your request and will ensure it receives proper attention. You can expect a detailed response from our team shortly.

Please let me know if there's anything else I can assist you with.

Warm regards,
Customer Service Team
</improved_email>"""
            ]
        
        # Return a random response for variety
        return random.choice(responses)
    
    async def generate_drafts(self, email_content: str, system_prompt: str, **kwargs) -> List[EmailDraft]:
        return [
            EmailDraft(
                content=f"Mock draft response to email about: {email_content[:30]}...",
                reasoning=["Mock reasoning 1", "Mock reasoning 2", "Mock reasoning 3"],
                confidence=0.8,
                draft_id=i+1,
                metadata={"provider": "mock"}
            ) for i in range(kwargs.get('num_drafts', 3))
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "provider": "mock", "model": "mock-model"}
    
    async def get_log_probabilities(
        self,
        text: str,
        context: Optional[str] = None
    ) -> List[float]:
        """Mock log probabilities for testing"""
        import re
        import math
        
        words = text.split()
        log_probs = []
        
        for word in words:
            if len(word) <= 3:
                likelihood = 0.8
            elif word.lower() in ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that']:
                likelihood = 0.9
            elif re.match(r'^[A-Z][a-z]+$', word):
                likelihood = 0.3
            else:
                likelihood = 0.6
            
            log_prob = math.log(max(likelihood, 0.001))
            log_probs.append(log_prob)
        
        return log_probs


class LLMProviderFactory:
    """Factory for creating LLM providers based on configuration"""
    
    @staticmethod
    def create_provider(config: LLMConfig) -> BaseLLMProvider:
        """Create appropriate provider based on config"""
        
        providers = {
            "ollama": OllamaProvider,
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "claude": AnthropicProvider,  # Alias for anthropic
            "mock": MockProvider
        }
        
        provider_class = providers.get(config.provider.lower())
        if not provider_class:
            raise ValueError(f"Unsupported provider: {config.provider}")
        
        return provider_class(config)
    
    @staticmethod
    def from_environment() -> BaseLLMProvider:
        """Create provider from environment variables"""
        
        provider = os.getenv("LLM_PROVIDER", "ollama")
        
        # Set default model based on provider
        default_models = {
            "ollama": "llama3.2:3b",
            "openai": "gpt-3.5-turbo",
            "anthropic": "claude-3-haiku-20240307",
            "claude": "claude-3-haiku-20240307",
            "mock": "mock-model"
        }
        
        default_model = default_models.get(provider.lower(), "llama3.2:3b")
        
        config = LLMConfig(
            provider=provider,
            model=os.getenv("LLM_MODEL", default_model),
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "500"))
        )
        
        return LLMProviderFactory.create_provider(config)


# Convenience function for easy access
def get_llm_provider() -> BaseLLMProvider:
    """Get configured LLM provider instance"""
    return LLMProviderFactory.from_environment()