"""
Ollama LLM Provider for local model integration
Implements the LLMProvider interface using Ollama local models
"""

import ollama
import asyncio
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import json


class OllamaProvider(LLMProvider):
    """LLM Provider using Ollama for local model execution"""
    
    def __init__(self, model_name: str = "llama3.2:3b", host: str = "localhost:11434"):
        self.model_name = model_name
        self.host = host
        self.client = ollama.Client(host=f"http://{host}")
    
    async def generate(
        self, 
        prompt: str, 
        temperature: float = 0.7, 
        max_tokens: int = 500,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate text using Ollama model"""
        
        try:
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user", 
                "content": prompt
            })
            
            # Run in thread pool to avoid blocking
            response = await asyncio.to_thread(
                self.client.chat,
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )
            
            return response['message']['content'].strip()
            
        except Exception as e:
            print(f"Ollama generation error: {e}")
            return f"Error generating response: {str(e)}"
    
    async def generate_drafts(
        self, 
        email_content: str, 
        system_prompt: str,
        user_preferences: List[Dict[str, Any]] = None,
        constraints: Dict[str, Any] = None,
        num_drafts: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate multiple email draft responses with reasoning"""
        
        drafts = []
        
        for i in range(num_drafts):
            # Create variation in each draft
            temperature = 0.3 + (i * 0.3)  # 0.3, 0.6, 0.9
            
            # Build comprehensive prompt
            prompt = self._build_draft_prompt(
                email_content, 
                user_preferences, 
                constraints,
                draft_number=i+1
            )
            
            try:
                response = await self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=800
                )
                
                # Parse response to extract draft and reasoning
                draft_data = self._parse_draft_response(response, i+1)
                drafts.append(draft_data)
                
            except Exception as e:
                print(f"Error generating draft {i+1}: {e}")
                # Add fallback draft
                drafts.append({
                    "content": f"I apologize, but I encountered an error generating this draft response. Please try again.",
                    "reasoning": [
                        "Technical error occurred during generation",
                        "Fallback response provided for continuity"
                    ],
                    "confidence": 0.1,
                    "draft_id": i+1
                })
        
        return drafts
    
    def _build_draft_prompt(
        self, 
        email_content: str, 
        user_preferences: List[Dict[str, Any]] = None,
        constraints: Dict[str, Any] = None,
        draft_number: int = 1
    ) -> str:
        """Build a comprehensive prompt for draft generation"""
        
        prompt_parts = [
            f"Generate a professional email response (Draft #{draft_number}) to the following email:",
            f"\n--- INCOMING EMAIL ---\n{email_content}\n--- END EMAIL ---\n",
        ]
        
        # Add user preferences
        if user_preferences:
            active_prefs = [p for p in user_preferences if p.get('is_active', True)]
            if active_prefs:
                prompt_parts.append("USER PREFERENCES:")
                for pref in active_prefs:
                    prompt_parts.append(f"- {pref['key']}: {pref['value']}")
                prompt_parts.append("")
        
        # Add constraints
        if constraints:
            prompt_parts.append("CONSTRAINTS:")
            for key, value in constraints.items():
                prompt_parts.append(f"- {key}: {value}")
            prompt_parts.append("")
        
        # Add specific instructions based on draft number
        if draft_number == 1:
            prompt_parts.append("STYLE: Create a formal, professional response.")
        elif draft_number == 2:
            prompt_parts.append("STYLE: Create a more conversational, friendly response.")
        else:
            prompt_parts.append("STYLE: Create a concise, direct response.")
        
        prompt_parts.extend([
            "",
            "IMPORTANT: Structure your response as follows:",
            "DRAFT:",
            "[Your email response here]",
            "",
            "REASONING:",
            "1. [First reasoning factor]",
            "2. [Second reasoning factor]", 
            "3. [Third reasoning factor]",
            "",
            "Provide exactly 3 clear reasoning factors that explain your drafting decisions."
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_draft_response(self, response: str, draft_id: int) -> Dict[str, Any]:
        """Parse the LLM response to extract draft content and reasoning"""
        
        try:
            # Split response into draft and reasoning sections
            if "REASONING:" in response:
                parts = response.split("REASONING:")
                draft_part = parts[0].replace("DRAFT:", "").strip()
                reasoning_part = parts[1].strip()
            else:
                # Fallback parsing
                lines = response.split('\n')
                draft_lines = []
                reasoning_lines = []
                in_reasoning = False
                
                for line in lines:
                    if line.strip().lower().startswith(('reasoning', 'reasons:', '1.', '2.', '3.')):
                        in_reasoning = True
                    
                    if in_reasoning:
                        reasoning_lines.append(line)
                    else:
                        draft_lines.append(line)
                
                draft_part = '\n'.join(draft_lines).replace("DRAFT:", "").strip()
                reasoning_part = '\n'.join(reasoning_lines)
            
            # Extract reasoning factors
            reasoning_factors = []
            reasoning_lines = reasoning_part.split('\n')
            
            for line in reasoning_lines:
                line = line.strip()
                # Look for numbered items or bullet points
                if any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '-', '•']):
                    # Clean up the reasoning factor
                    clean_reason = line
                    for prefix in ['1.', '2.', '3.', '-', '•']:
                        clean_reason = clean_reason.replace(prefix, '', 1).strip()
                    
                    if clean_reason:
                        reasoning_factors.append(clean_reason)
            
            # Ensure we have at least some reasoning
            if not reasoning_factors:
                reasoning_factors = [
                    "Professional tone maintained throughout response",
                    "Addresses all key points from original email", 
                    "Structured for clarity and appropriate length"
                ]
            
            # Calculate confidence based on response quality
            confidence = self._calculate_confidence(draft_part, reasoning_factors)
            
            return {
                "content": draft_part,
                "reasoning": reasoning_factors[:3],  # Limit to 3 factors
                "confidence": confidence,
                "draft_id": draft_id
            }
            
        except Exception as e:
            print(f"Error parsing draft response: {e}")
            return {
                "content": response[:500] + "..." if len(response) > 500 else response,
                "reasoning": [
                    "Response generated but parsing encountered issues",
                    "Content may need manual review",
                    "System working to improve parsing accuracy"
                ],
                "confidence": 0.5,
                "draft_id": draft_id
            }
    
    def _calculate_confidence(self, draft_content: str, reasoning_factors: List[str]) -> float:
        """Calculate confidence score based on response quality indicators"""
        
        confidence = 0.7  # Base confidence
        
        # Check length appropriateness
        if 50 <= len(draft_content) <= 1000:
            confidence += 0.1
        
        # Check if reasoning is substantive
        if len(reasoning_factors) >= 3:
            confidence += 0.1
        
        # Check for common email elements
        email_indicators = ['thank', 'regards', 'sincerely', 'please', 'appreciate']
        if any(indicator in draft_content.lower() for indicator in email_indicators):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    async def evaluate_response_quality(
        self, 
        original_email: str, 
        generated_response: str,
        criteria: List[str] = None
    ) -> Dict[str, float]:
        """Evaluate the quality of a generated response"""
        
        if not criteria:
            criteria = ["relevance", "clarity", "professionalism", "completeness"]
        
        evaluation_prompt = f"""
        Evaluate the following email response on a scale of 0.0 to 1.0 for each criterion:
        
        ORIGINAL EMAIL:
        {original_email}
        
        GENERATED RESPONSE:
        {generated_response}
        
        CRITERIA TO EVALUATE:
        {', '.join(criteria)}
        
        Provide your evaluation in this exact format:
        relevance: 0.X
        clarity: 0.X
        professionalism: 0.X
        completeness: 0.X
        
        Only include the numerical scores, one per line.
        """
        
        try:
            evaluation = await self.generate(
                prompt=evaluation_prompt,
                temperature=0.1,  # Low temperature for consistent evaluation
                max_tokens=200
            )
            
            # Parse evaluation scores
            scores = {}
            for line in evaluation.split('\n'):
                line = line.strip()
                if ':' in line:
                    criterion, score_str = line.split(':', 1)
                    criterion = criterion.strip().lower()
                    try:
                        score = float(score_str.strip())
                        scores[criterion] = max(0.0, min(1.0, score))  # Clamp to [0,1]
                    except ValueError:
                        scores[criterion] = 0.7  # Default score
            
            # Ensure all criteria have scores
            for criterion in criteria:
                if criterion not in scores:
                    scores[criterion] = 0.7
            
            return scores
            
        except Exception as e:
            print(f"Error in response evaluation: {e}")
            # Return default scores
            return {criterion: 0.7 for criterion in criteria}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Ollama is healthy and model is available"""
        
        try:
            # Test model availability
            response = await asyncio.to_thread(
                self.client.chat,
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                options={"num_predict": 10}
            )
            
            return {
                "status": "healthy",
                "model": self.model_name,
                "host": self.host,
                "test_response": response['message']['content'][:50]
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self.model_name,
                "host": self.host,
                "error": str(e)
            }