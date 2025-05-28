"""
Complete Demonstration Workflow for Loop Learner
Showcases adaptive learning in action with automated scenarios and guided interactions
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from django.utils import timezone
from asgiref.sync import sync_to_async

from core.models import SystemPrompt, Email, Draft, UserFeedback, OptimizationRun
from .unified_llm_provider import LLMProviderFactory, LLMConfig
from .email_generator import SyntheticEmailGenerator
from .optimization_orchestrator import OptimizationOrchestrator, OptimizationTrigger
from .background_scheduler import OptimizationScheduler
from .evaluation_engine import EvaluationEngine
from .reward_aggregator import RewardFunctionAggregator
from .prompt_rewriter import LLMBasedPromptRewriter, RewriteContext

logger = logging.getLogger(__name__)


@dataclass
class DemoScenario:
    """Represents a complete demo scenario with expected outcomes"""
    name: str
    description: str
    email_scenarios: List[str]
    feedback_patterns: List[Dict[str, Any]]
    expected_improvement: float
    learning_objectives: List[str]


@dataclass
class DemoStep:
    """Individual step in the demonstration workflow"""
    step_number: int
    title: str
    description: str
    action_type: str  # "generate", "feedback", "optimize", "evaluate"
    expected_duration: int  # seconds
    success_criteria: Dict[str, Any]


@dataclass
class DemoResults:
    """Results from running a complete demo workflow"""
    scenario_name: str
    total_emails_processed: int
    total_feedback_collected: int
    optimizations_triggered: int
    final_performance_improvement: float
    learning_objectives_met: List[str]
    execution_time: timedelta
    detailed_metrics: Dict[str, Any]


class DemoWorkflowOrchestrator:
    """Orchestrates complete demonstration workflows showing adaptive learning"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.llm_provider = LLMProviderFactory.create_provider(llm_config)
        self.email_generator = SyntheticEmailGenerator()
        
        # Initialize core components
        self.reward_aggregator = RewardFunctionAggregator(self.llm_provider)
        self.evaluation_engine = EvaluationEngine(self.llm_provider, self.reward_aggregator)
        
        # Demo-specific configuration for faster iterations
        self.demo_trigger_config = OptimizationTrigger(
            min_feedback_count=5,  # Lower threshold for demo
            min_negative_feedback_ratio=0.4,
            feedback_window_hours=1,  # Shorter window for demo
            min_time_since_last_optimization_hours=0.1,  # Very short for demo
            max_optimization_frequency_per_day=20  # Higher limit for demo
        )
        
        self.orchestrator = None
        self.demo_scenarios = self._create_demo_scenarios()
    
    def _create_demo_scenarios(self) -> List[DemoScenario]:
        """Create predefined demo scenarios for different learning objectives"""
        
        return [
            DemoScenario(
                name="Professional Email Optimization",
                description="Improve professional email responses through feedback",
                email_scenarios=["professional", "business_inquiry", "project_update"],
                feedback_patterns=[
                    {"action": "reject", "reasoning": "Too informal", "factors": {"tone": 2, "professionalism": 2}},
                    {"action": "edit", "reasoning": "Good start but needs more detail", "factors": {"completeness": 2}},
                    {"action": "accept", "reasoning": "Perfect professional tone", "factors": {"tone": 5, "professionalism": 5}},
                ],
                expected_improvement=15.0,
                learning_objectives=["Improve professional tone", "Increase completeness", "Maintain clarity"]
            ),
            
            DemoScenario(
                name="Customer Service Excellence",
                description="Optimize customer service responses for empathy and helpfulness",
                email_scenarios=["complaint", "inquiry", "urgent"],
                feedback_patterns=[
                    {"action": "reject", "reasoning": "Not empathetic enough", "factors": {"empathy": 2, "tone": 3}},
                    {"action": "edit", "reasoning": "Good empathy but needs solution", "factors": {"completeness": 2, "helpfulness": 3}},
                    {"action": "accept", "reasoning": "Excellent customer service", "factors": {"empathy": 5, "helpfulness": 5}},
                ],
                expected_improvement=20.0,
                learning_objectives=["Increase empathy", "Improve solution-oriented responses", "Enhance helpfulness"]
            ),
            
            DemoScenario(
                name="Technical Communication",
                description="Learn to balance technical accuracy with accessibility",
                email_scenarios=["technical", "support", "explanation"],
                feedback_patterns=[
                    {"action": "reject", "reasoning": "Too technical for audience", "factors": {"clarity": 2, "accessibility": 2}},
                    {"action": "edit", "reasoning": "Good accuracy but simplify", "factors": {"clarity": 3, "accessibility": 3}},
                    {"action": "accept", "reasoning": "Perfect balance", "factors": {"accuracy": 5, "clarity": 5}},
                ],
                expected_improvement=18.0,
                learning_objectives=["Balance technical accuracy", "Improve accessibility", "Enhance clarity"]
            )
        ]
    
    async def run_complete_demo(self, scenario_name: str = "Professional Email Optimization") -> DemoResults:
        """Run a complete demonstration workflow from start to finish"""
        
        scenario = next((s for s in self.demo_scenarios if s.name == scenario_name), self.demo_scenarios[0])
        start_time = timezone.now()
        
        logger.info(f"Starting complete demo workflow: {scenario.name}")
        
        try:
            # Step 1: Initialize system with baseline prompt
            await self._initialize_demo_system()
            
            # Step 2: Generate and process emails with feedback
            emails_processed, feedback_collected = await self._process_demo_emails(scenario)
            
            # Step 3: Trigger and monitor optimization
            optimizations_triggered = await self._trigger_demo_optimization()
            
            # Step 4: Evaluate final performance
            final_improvement, objectives_met = await self._evaluate_demo_results(scenario)
            
            # Step 5: Generate comprehensive metrics
            detailed_metrics = await self._generate_demo_metrics()
            
            execution_time = timezone.now() - start_time
            
            results = DemoResults(
                scenario_name=scenario.name,
                total_emails_processed=emails_processed,
                total_feedback_collected=feedback_collected,
                optimizations_triggered=optimizations_triggered,
                final_performance_improvement=final_improvement,
                learning_objectives_met=objectives_met,
                execution_time=execution_time,
                detailed_metrics=detailed_metrics
            )
            
            logger.info(f"Demo completed successfully: {final_improvement:.1f}% improvement")
            return results
            
        except Exception as e:
            logger.error(f"Demo workflow failed: {e}")
            raise
    
    async def _initialize_demo_system(self):
        """Initialize the system with a baseline prompt for demonstration"""
        
        # Create baseline system prompt
        baseline_prompt = SystemPrompt(
            content="You are an email assistant. Respond to emails professionally and helpfully.",
            version=1,
            is_active=True,
            performance_score=0.6,  # Starting baseline
        )
        await sync_to_async(baseline_prompt.save)()
        
        # Initialize orchestrator with demo configuration
        prompt_rewriter = LLMBasedPromptRewriter(
            rewriter_llm_provider=self.llm_provider,
            similarity_llm_provider=self.llm_provider,
            reward_function_aggregator=self.reward_aggregator,
            meta_prompt_manager=None  # Simplified for demo
        )
        
        self.orchestrator = OptimizationOrchestrator(
            llm_provider=self.llm_provider,
            prompt_rewriter=prompt_rewriter,
            evaluation_engine=self.evaluation_engine,
            trigger_config=self.demo_trigger_config
        )
        
        logger.info("Demo system initialized with baseline prompt")
    
    async def _process_demo_emails(self, scenario: DemoScenario) -> Tuple[int, int]:
        """Process emails and collect feedback according to scenario patterns"""
        
        emails_processed = 0
        feedback_collected = 0
        
        # Generate emails for each scenario type
        for scenario_type in scenario.email_scenarios:
            for i in range(4):  # Process 4 emails per scenario type
                try:
                    # Generate synthetic email
                    email = await self.email_generator.generate_synthetic_email(scenario_type)
                    
                    # Generate draft response
                    active_prompt = await sync_to_async(
                        SystemPrompt.objects.filter(is_active=True).first
                    )()
                    
                    if active_prompt:
                        draft_content = await self.llm_provider.generate(
                            prompt=f"Please respond to this email:\n\nSubject: {email.subject}\nFrom: {email.sender}\nBody: {email.body}",
                            system_prompt=active_prompt.content,
                            temperature=0.7,
                            max_tokens=200
                        )
                        
                        draft = Draft(
                            email=email,
                            content=draft_content,
                            system_prompt=active_prompt
                        )
                        await sync_to_async(draft.save)()
                        
                        # Simulate feedback based on scenario patterns
                        feedback_pattern = scenario.feedback_patterns[i % len(scenario.feedback_patterns)]
                        
                        feedback = UserFeedback(
                            draft=draft,
                            action=feedback_pattern['action'],
                            reason=feedback_pattern['reasoning'],
                            edited_content=draft_content + " [Edited for demo]" if feedback_pattern['action'] == 'edit' else ""
                        )
                        await sync_to_async(feedback.save)()
                        
                        emails_processed += 1
                        feedback_collected += 1
                        
                        # Small delay for realistic demonstration
                        await asyncio.sleep(0.1)
                
                except Exception as e:
                    logger.error(f"Error processing demo email: {e}")
                    continue
        
        logger.info(f"Processed {emails_processed} emails with {feedback_collected} feedback instances")
        return emails_processed, feedback_collected
    
    async def _trigger_demo_optimization(self) -> int:
        """Trigger optimization and wait for completion"""
        
        optimizations_count = 0
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                # Force optimization trigger
                result = await self.orchestrator.force_optimization(f"Demo optimization attempt {attempt + 1}")
                
                if result and result.deployed:
                    optimizations_count += 1
                    logger.info(f"Demo optimization {optimizations_count} completed: {result.improvement_percentage:.1f}% improvement")
                    
                    # Create optimization run record
                    optimization_run = OptimizationRun(
                        old_prompt=result.baseline_prompt,
                        new_prompt=await sync_to_async(SystemPrompt.objects.filter(is_active=True).first)(),
                        status='completed',
                        feedback_count=result.feedback_batch_size,
                        performance_improvement=result.improvement_percentage,
                        completed_at=timezone.now()
                    )
                    await sync_to_async(optimization_run.save)()
                
                # Short delay between optimization attempts
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Demo optimization attempt {attempt + 1} failed: {e}")
                continue
        
        return optimizations_count
    
    async def _evaluate_demo_results(self, scenario: DemoScenario) -> Tuple[float, List[str]]:
        """Evaluate final demo performance and check learning objectives"""
        
        # Get initial and final prompts
        all_prompts = [
            prompt async for prompt in SystemPrompt.objects.all().order_by('version')
        ]
        
        if len(all_prompts) < 2:
            return 0.0, []
        
        initial_prompt = all_prompts[0]
        final_prompt = all_prompts[-1]
        
        # Calculate improvement
        initial_score = initial_prompt.performance_score or 0.6
        final_score = final_prompt.performance_score or initial_score
        improvement = ((final_score - initial_score) / initial_score * 100) if initial_score > 0 else 0.0
        
        # Check learning objectives (simplified for demo)
        objectives_met = []
        if improvement > 5.0:
            objectives_met.append("Achieved measurable improvement")
        if improvement > 10.0:
            objectives_met.append("Exceeded performance targets")
        if len(all_prompts) > 2:
            objectives_met.append("Demonstrated iterative learning")
        
        return improvement, objectives_met
    
    async def _generate_demo_metrics(self) -> Dict[str, Any]:
        """Generate comprehensive metrics for demo results"""
        
        # Count various entities
        total_emails = await Email.objects.filter(is_synthetic=True).acount()
        total_drafts = await Draft.objects.acount()
        total_feedback = await UserFeedback.objects.acount()
        total_optimizations = await OptimizationRun.objects.acount()
        
        # Get prompt evolution
        prompt_versions = []
        async for prompt in SystemPrompt.objects.all().order_by('version'):
            prompt_versions.append({
                'version': prompt.version,
                'performance_score': prompt.performance_score,
                'is_active': prompt.is_active,
                'created_at': prompt.created_at.isoformat()
            })
        
        # Calculate feedback distribution
        feedback_distribution = {}
        async for feedback in UserFeedback.objects.all():
            action = feedback.action
            feedback_distribution[action] = feedback_distribution.get(action, 0) + 1
        
        return {
            'total_emails': total_emails,
            'total_drafts': total_drafts,
            'total_feedback': total_feedback,
            'total_optimizations': total_optimizations,
            'prompt_evolution': prompt_versions,
            'feedback_distribution': feedback_distribution,
            'system_health': {
                'learning_active': total_optimizations > 0,
                'feedback_diversity': len(feedback_distribution),
                'optimization_success': total_optimizations > 0
            }
        }
    
    async def run_guided_demo_steps(self, scenario_name: str = "Professional Email Optimization") -> List[DemoStep]:
        """Generate step-by-step guided demo instructions"""
        
        scenario = next((s for s in self.demo_scenarios if s.name == scenario_name), self.demo_scenarios[0])
        
        steps = [
            DemoStep(
                step_number=1,
                title="Initialize Baseline System",
                description=f"Set up the system with a basic prompt for {scenario.name}",
                action_type="generate",
                expected_duration=5,
                success_criteria={"baseline_prompt_created": True, "system_ready": True}
            ),
            
            DemoStep(
                step_number=2,
                title="Generate Test Emails",
                description=f"Create {len(scenario.email_scenarios)} different email scenarios",
                action_type="generate",
                expected_duration=10,
                success_criteria={"emails_generated": len(scenario.email_scenarios) * 4}
            ),
            
            DemoStep(
                step_number=3,
                title="Collect Human Feedback",
                description="Provide feedback on AI responses using Accept/Reject/Edit actions",
                action_type="feedback",
                expected_duration=30,
                success_criteria={"feedback_collected": 12, "negative_feedback_ratio": 0.4}
            ),
            
            DemoStep(
                step_number=4,
                title="Trigger Optimization",
                description="Watch the system automatically optimize based on feedback patterns",
                action_type="optimize",
                expected_duration=15,
                success_criteria={"optimization_triggered": True, "new_prompt_deployed": True}
            ),
            
            DemoStep(
                step_number=5,
                title="Evaluate Improvement",
                description="Review performance metrics and learning progress in dashboard",
                action_type="evaluate",
                expected_duration=10,
                success_criteria={"improvement_measured": True, "objectives_met": True}
            )
        ]
        
        return steps
    
    async def create_demo_report(self, results: DemoResults) -> Dict[str, Any]:
        """Create a comprehensive demo report for presentation"""
        
        return {
            'executive_summary': {
                'scenario': results.scenario_name,
                'total_improvement': f"{results.final_performance_improvement:.1f}%",
                'execution_time': str(results.execution_time),
                'success_status': 'Completed Successfully' if results.final_performance_improvement > 5 else 'Partial Success'
            },
            'learning_metrics': {
                'emails_processed': results.total_emails_processed,
                'feedback_collected': results.total_feedback_collected,
                'optimizations_triggered': results.optimizations_triggered,
                'objectives_achieved': len(results.learning_objectives_met),
                'learning_efficiency': results.total_feedback_collected / max(results.optimizations_triggered, 1)
            },
            'system_performance': {
                'baseline_to_final_improvement': results.final_performance_improvement,
                'objectives_met': results.learning_objectives_met,
                'detailed_metrics': results.detailed_metrics
            },
            'demonstration_highlights': [
                f"Processed {results.total_emails_processed} emails across multiple scenarios",
                f"Collected {results.total_feedback_collected} human feedback instances",
                f"Triggered {results.optimizations_triggered} automatic optimizations",
                f"Achieved {results.final_performance_improvement:.1f}% performance improvement",
                f"Completed in {results.execution_time}",
                "Demonstrated end-to-end adaptive learning capability"
            ],
            'next_steps': [
                "Deploy in production environment",
                "Scale to additional email scenarios", 
                "Integrate with real email systems",
                "Add advanced analytics and reporting",
                "Implement A/B testing for prompt candidates"
            ]
        }


async def run_quick_demo(llm_config: LLMConfig = None) -> Dict[str, Any]:
    """Run a quick demonstration of the complete system"""
    
    if llm_config is None:
        llm_config = LLMConfig(
            provider="mock",
            model="demo-model",
            api_key="demo-key"
        )
    
    demo_orchestrator = DemoWorkflowOrchestrator(llm_config)
    
    try:
        # Run complete demo
        results = await demo_orchestrator.run_complete_demo("Professional Email Optimization")
        
        # Generate report
        report = await demo_orchestrator.create_demo_report(results)
        
        return {
            'success': True,
            'demo_results': results,
            'demo_report': report,
            'message': 'Complete demonstration workflow executed successfully'
        }
        
    except Exception as e:
        logger.error(f"Quick demo failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Demo workflow encountered an error'
        }