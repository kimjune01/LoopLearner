from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from core.models import SystemPrompt, Email
from dataclasses import dataclass
import asyncio


@dataclass
class MetaPromptTemplate:
    """Template for guiding prompt rewriting"""
    id: str
    name: str
    description: str
    template: str
    scenario_types: List[str]
    constraints: Dict[str, Any]
    version: int
    effectiveness_score: float = 0.0


class MetaPromptManager:
    """Manages meta-prompts that guide the prompt rewriting process"""
    
    def __init__(self):
        self.templates: Dict[str, MetaPromptTemplate] = {}
        self.scenario_mappings: Dict[str, str] = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default meta-prompt templates for different scenarios"""
        
        # General rewriting template
        general_template = MetaPromptTemplate(
            id="general_rewrite",
            name="General Prompt Rewriting",
            description="General purpose prompt improvement",
            template="""You are an expert prompt engineer. Your task is to rewrite the given prompt to make it more effective while preserving its core intent and functionality.

Guidelines for rewriting:
1. Make the prompt more specific and actionable
2. Add relevant context that improves task performance
3. Maintain clarity and readability
4. Preserve the original intent and scope
5. Consider the target audience and use case

Focus on improving:
- Clarity of instructions
- Specificity of requirements
- Context relevance
- Task alignment""",
            scenario_types=["general"],
            constraints={},
            version=1
        )
        
        # Professional email template
        professional_template = MetaPromptTemplate(
            id="professional_email_rewrite",
            name="Professional Email Optimization",
            description="Optimizes prompts for professional email responses",
            template="""You are a business communication expert. Rewrite the given prompt to generate more effective professional email responses.

Professional Email Guidelines:
1. Ensure appropriate business tone and formality
2. Include clear call-to-action guidance
3. Emphasize conciseness and clarity
4. Consider business etiquette and best practices
5. Account for different professional contexts (internal, external, client-facing)

Key improvements to focus on:
- Professional language and tone instructions
- Response structure guidance (greeting, body, closing)
- Appropriate level of detail for business context
- Time-sensitive communication handling
- Stakeholder consideration""",
            scenario_types=["professional", "business"],
            constraints={"tone": "professional", "max_length": 200},
            version=1
        )
        
        # Casual email template
        casual_template = MetaPromptTemplate(
            id="casual_email_rewrite",
            name="Casual Email Optimization",
            description="Optimizes prompts for casual/personal email responses",
            template="""You are a communication expert specializing in casual, friendly correspondence. Rewrite the prompt to generate more natural and engaging casual email responses.

Casual Email Guidelines:
1. Encourage friendly, approachable tone
2. Allow for personal expression and warmth
3. Focus on relationship building
4. Include conversational elements
5. Balance casualness with respect

Key improvements to focus on:
- Natural, conversational language instructions
- Flexibility in response structure
- Personal touch and warmth guidance
- Appropriate informality level
- Relationship context consideration""",
            scenario_types=["casual", "personal", "friendly"],
            constraints={"tone": "casual", "formality": "low"},
            version=1
        )
        
        # Complaint handling template
        complaint_template = MetaPromptTemplate(
            id="complaint_handling_rewrite",
            name="Complaint Response Optimization",
            description="Optimizes prompts for handling complaints and difficult situations",
            template="""You are a customer service expert. Rewrite the prompt to generate more effective responses to complaints and difficult situations.

Complaint Handling Guidelines:
1. Emphasize empathy and understanding
2. Include acknowledgment of concerns
3. Focus on solution-oriented responses
4. Maintain professionalism under pressure
5. De-escalation techniques

Key improvements to focus on:
- Empathetic language instructions
- Problem-solving approach guidance
- Appropriate apology frameworks
- Next steps and resolution focus
- Professional boundary maintenance""",
            scenario_types=["complaint", "difficult", "customer_service"],
            constraints={"tone": "empathetic", "solution_focused": True},
            version=1
        )
        
        # Inquiry response template
        inquiry_template = MetaPromptTemplate(
            id="inquiry_response_rewrite",
            name="Inquiry Response Optimization",
            description="Optimizes prompts for responding to inquiries and requests for information",
            template="""You are an information specialist. Rewrite the prompt to generate more helpful and comprehensive responses to inquiries and information requests.

Inquiry Response Guidelines:
1. Ensure complete information coverage
2. Organize information logically
3. Anticipate follow-up questions
4. Provide actionable next steps
5. Include relevant resources or contacts

Key improvements to focus on:
- Comprehensive information gathering instructions
- Logical structure and organization guidance
- Proactive information provision
- Resource and contact inclusion
- Follow-up facilitation""",
            scenario_types=["inquiry", "information", "request"],
            constraints={"completeness": "high", "structure": "organized"},
            version=1
        )
        
        # Store templates
        for template in [general_template, professional_template, casual_template, 
                        complaint_template, inquiry_template]:
            self.templates[template.id] = template
            for scenario in template.scenario_types:
                self.scenario_mappings[scenario] = template.id
    
    async def get_meta_prompt(
        self,
        scenario_type: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get appropriate meta-prompt for scenario and constraints"""
        
        # Find template for scenario
        template_id = self.scenario_mappings.get(scenario_type, "general_rewrite")
        template = self.templates.get(template_id)
        
        if not template:
            template = self.templates["general_rewrite"]
        
        # Apply constraints if provided
        if constraints:
            return self._apply_constraints(template, constraints)
        
        return template.template
    
    def _apply_constraints(
        self,
        template: MetaPromptTemplate,
        constraints: Dict[str, Any]
    ) -> str:
        """Apply runtime constraints to meta-prompt template"""
        
        base_template = template.template
        
        # Add constraint-specific instructions
        constraint_additions = []
        
        if "max_length" in constraints:
            constraint_additions.append(
                f"- Keep responses under {constraints['max_length']} words"
            )
        
        if "tone" in constraints:
            constraint_additions.append(
                f"- Maintain {constraints['tone']} tone throughout"
            )
        
        if "urgency" in constraints:
            urgency = constraints["urgency"]
            if urgency == "high":
                constraint_additions.append(
                    "- Prioritize immediate action and clear next steps"
                )
            elif urgency == "low":
                constraint_additions.append(
                    "- Allow for thoughtful, detailed responses"
                )
        
        if "audience" in constraints:
            audience = constraints["audience"]
            constraint_additions.append(
                f"- Tailor language and content for {audience} audience"
            )
        
        # Append constraints to template
        if constraint_additions:
            additional_constraints = "\n\nAdditional Constraints:\n" + "\n".join(constraint_additions)
            return base_template + additional_constraints
        
        return base_template
    
    async def create_custom_template(
        self,
        template_id: str,
        name: str,
        description: str,
        template_content: str,
        scenario_types: List[str],
        constraints: Optional[Dict[str, Any]] = None
    ) -> MetaPromptTemplate:
        """Create a new custom meta-prompt template"""
        
        template = MetaPromptTemplate(
            id=template_id,
            name=name,
            description=description,
            template=template_content,
            scenario_types=scenario_types,
            constraints=constraints or {},
            version=1
        )
        
        self.templates[template_id] = template
        
        # Update scenario mappings
        for scenario in scenario_types:
            self.scenario_mappings[scenario] = template_id
        
        return template
    
    async def update_template_effectiveness(
        self,
        template_id: str,
        effectiveness_score: float
    ):
        """Update template effectiveness based on performance metrics"""
        
        if template_id in self.templates:
            self.templates[template_id].effectiveness_score = effectiveness_score
    
    async def get_best_template_for_scenario(
        self,
        scenario_type: str
    ) -> Optional[MetaPromptTemplate]:
        """Get the most effective template for a given scenario"""
        
        # Find all templates that handle this scenario
        candidate_templates = [
            template for template in self.templates.values()
            if scenario_type in template.scenario_types
        ]
        
        if not candidate_templates:
            return self.templates.get("general_rewrite")
        
        # Return template with highest effectiveness score
        return max(candidate_templates, key=lambda t: t.effectiveness_score)
    
    async def get_template_performance_report(self) -> Dict[str, Any]:
        """Generate performance report for all templates"""
        
        report = {
            "total_templates": len(self.templates),
            "scenario_coverage": len(self.scenario_mappings),
            "templates": []
        }
        
        for template in self.templates.values():
            template_info = {
                "id": template.id,
                "name": template.name,
                "scenario_types": template.scenario_types,
                "effectiveness_score": template.effectiveness_score,
                "version": template.version
            }
            report["templates"].append(template_info)
        
        return report
    
    async def optimize_template_selection(
        self,
        scenario_performance_data: Dict[str, float]
    ):
        """Optimize template selection based on performance data"""
        
        for scenario, performance in scenario_performance_data.items():
            if scenario in self.scenario_mappings:
                template_id = self.scenario_mappings[scenario]
                await self.update_template_effectiveness(template_id, performance)
    
    def get_template_by_id(self, template_id: str) -> Optional[MetaPromptTemplate]:
        """Get template by its ID"""
        return self.templates.get(template_id)
    
    def list_available_templates(self) -> List[MetaPromptTemplate]:
        """List all available templates"""
        return list(self.templates.values())
    
    def get_scenarios_for_template(self, template_id: str) -> List[str]:
        """Get all scenarios that use a specific template"""
        template = self.templates.get(template_id)
        return template.scenario_types if template else []