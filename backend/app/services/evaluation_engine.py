"""
Evaluation Engine for automated prompt performance testing and comparison
Implements A/B testing and batch evaluation for prompt optimization
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from core.models import SystemPrompt, Email, Draft, UserFeedback
from .reward_aggregator import RewardFunctionAggregator
from .unified_llm_provider import BaseLLMProvider
from asgiref.sync import sync_to_async
import asyncio
import statistics
import logging
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of evaluating a single prompt"""
    prompt: SystemPrompt
    performance_score: float
    metrics: Dict[str, float]
    sample_outputs: List[str]
    evaluation_time: datetime
    test_cases_used: int
    error_rate: float


@dataclass
class ComparisonResult:
    """Result of comparing two prompts"""
    baseline: EvaluationResult
    candidate: EvaluationResult
    improvement: float  # Percentage improvement (positive = better)
    statistical_significance: float  # p-value
    winner: str  # "baseline", "candidate", or "tie"
    confidence_level: float


@dataclass
class EvaluationTestCase:
    """Test case for prompt evaluation"""
    email: Email
    expected_qualities: Dict[str, float]  # Expected performance metrics
    scenario_type: str
    difficulty_level: str  # "easy", "medium", "hard"


class PromptEvaluator(ABC):
    """Abstract interface for prompt evaluation strategies"""
    
    @abstractmethod
    async def evaluate_prompt(
        self,
        prompt: SystemPrompt,
        test_cases: List[EvaluationTestCase],
        llm_provider: BaseLLMProvider
    ) -> EvaluationResult:
        """Evaluate a prompt against test cases"""
        pass


class BatchPromptEvaluator(PromptEvaluator):
    """Evaluates prompts by running them against a batch of test cases"""
    
    def __init__(self, reward_aggregator: RewardFunctionAggregator):
        self.reward_aggregator = reward_aggregator
    
    async def evaluate_prompt(
        self,
        prompt: SystemPrompt,
        test_cases: List[EvaluationTestCase],
        llm_provider: BaseLLMProvider
    ) -> EvaluationResult:
        """Evaluate prompt performance across multiple test cases"""
        
        start_time = timezone.now()
        all_scores = []
        all_metrics = []
        sample_outputs = []
        errors = 0
        
        logger.info(f"Evaluating prompt v{prompt.version} against {len(test_cases)} test cases")
        
        # Run evaluation across all test cases
        for i, test_case in enumerate(test_cases):
            try:
                # Generate response using the prompt
                draft_response = await self._generate_response_with_prompt(
                    prompt, test_case.email, llm_provider
                )
                
                # Calculate performance metrics
                metrics = await self._calculate_metrics(
                    prompt, draft_response, test_case, llm_provider
                )
                
                all_scores.append(metrics['overall_score'])
                all_metrics.append(metrics)
                
                # Store sample outputs for analysis
                if i < 3:  # Keep first 3 as samples
                    sample_outputs.append(draft_response)
                    
            except Exception as e:
                logger.error(f"Error evaluating test case {i}: {e}")
                errors += 1
                continue
        
        if not all_scores:
            raise ValueError("No successful evaluations completed")
        
        # Aggregate results
        overall_performance = statistics.mean(all_scores)
        aggregated_metrics = self._aggregate_metrics(all_metrics)
        error_rate = errors / len(test_cases)
        
        return EvaluationResult(
            prompt=prompt,
            performance_score=overall_performance,
            metrics=aggregated_metrics,
            sample_outputs=sample_outputs,
            evaluation_time=start_time,
            test_cases_used=len(test_cases) - errors,
            error_rate=error_rate
        )
    
    async def _generate_response_with_prompt(
        self,
        prompt: SystemPrompt,
        email: Email,
        llm_provider: BaseLLMProvider
    ) -> str:
        """Generate response using the given prompt"""
        
        # Build email context
        email_content = f"""
Subject: {email.subject}
From: {email.sender}
Body: {email.body}
"""
        
        # Generate response using the prompt
        response = await llm_provider.generate(
            prompt=f"Please respond to this email:\n{email_content}",
            system_prompt=prompt.content,
            temperature=0.7,
            max_tokens=300
        )
        
        return response.strip()
    
    async def _calculate_metrics(
        self,
        prompt: SystemPrompt,
        response: str,
        test_case: EvaluationTestCase,
        llm_provider: BaseLLMProvider
    ) -> Dict[str, float]:
        """Calculate performance metrics for a response"""
        
        # Create mock feedback for reward calculation
        mock_feedback = type('MockFeedback', (), {
            'action': 'accept',  # Assume positive for evaluation
            'reasoning_factors': {
                'clarity': 4,
                'tone': 4,
                'completeness': 4,
                'relevance': 4
            }
        })()
        
        # Calculate reward using existing system
        overall_score = await self.reward_aggregator.compute_reward(
            prompt,
            response,
            mock_feedback,
            {
                'actual_output': response,
                'expected_output': '',  # We don't have ground truth
                'f1_score': test_case.expected_qualities.get('f1_score', 0.7),
                'semantic_similarity': test_case.expected_qualities.get('semantic_similarity', 0.7)
            }
        )
        
        # Calculate additional metrics
        perplexity_score = await self._calculate_perplexity_score(response, llm_provider)
        length_score = self._calculate_length_appropriateness(response, test_case)
        
        return {
            'overall_score': overall_score,
            'perplexity_score': perplexity_score,
            'length_score': length_score,
            'response_length': len(response),
            'word_count': len(response.split())
        }
    
    async def _calculate_perplexity_score(self, text: str, llm_provider: BaseLLMProvider) -> float:
        """Calculate perplexity-based score for text quality"""
        try:
            log_probs = await llm_provider.get_log_probabilities(text)
            if not log_probs:
                return 0.5
            
            import math
            mean_log_prob = sum(log_probs) / len(log_probs)
            perplexity = math.exp(-mean_log_prob)
            
            # Convert to 0-1 score (lower perplexity = higher score)
            return max(0.0, 1.0 - (perplexity / 50.0))  # Normalize by max expected perplexity
        except Exception:
            return 0.5
    
    def _calculate_length_appropriateness(self, response: str, test_case: EvaluationTestCase) -> float:
        """Calculate how appropriate the response length is"""
        word_count = len(response.split())
        
        # Define ideal ranges based on scenario type
        ideal_ranges = {
            'professional': (50, 200),
            'casual': (20, 150),
            'technical': (100, 300),
            'urgent': (10, 100)
        }
        
        min_ideal, max_ideal = ideal_ranges.get(test_case.scenario_type, (50, 200))
        
        if min_ideal <= word_count <= max_ideal:
            return 1.0
        elif word_count < min_ideal:
            return max(0.0, word_count / min_ideal)
        else:
            return max(0.0, 1.0 - (word_count - max_ideal) / max_ideal)
    
    def _aggregate_metrics(self, metrics_list: List[Dict[str, float]]) -> Dict[str, float]:
        """Aggregate metrics across multiple test cases"""
        if not metrics_list:
            return {}
        
        aggregated = {}
        
        # Get all metric keys
        all_keys = set()
        for metrics in metrics_list:
            all_keys.update(metrics.keys())
        
        # Calculate mean for each metric
        for key in all_keys:
            values = [m.get(key, 0.0) for m in metrics_list]
            aggregated[f"{key}_mean"] = statistics.mean(values)
            aggregated[f"{key}_std"] = statistics.stdev(values) if len(values) > 1 else 0.0
        
        return aggregated


class ABTestingEngine:
    """Engine for running A/B tests between prompt versions"""
    
    def __init__(self, evaluator: PromptEvaluator):
        self.evaluator = evaluator
    
    async def compare_prompts(
        self,
        baseline: SystemPrompt,
        candidate: SystemPrompt,
        test_cases: List[EvaluationTestCase],
        llm_provider: BaseLLMProvider
    ) -> ComparisonResult:
        """Compare two prompts using A/B testing methodology"""
        
        logger.info(f"Running A/B test: baseline v{baseline.version} vs candidate v{candidate.version}")
        
        # Evaluate both prompts in parallel
        baseline_task = self.evaluator.evaluate_prompt(baseline, test_cases, llm_provider)
        candidate_task = self.evaluator.evaluate_prompt(candidate, test_cases, llm_provider)
        
        baseline_result, candidate_result = await asyncio.gather(baseline_task, candidate_task)
        
        # Calculate improvement
        improvement = ((candidate_result.performance_score - baseline_result.performance_score) 
                      / baseline_result.performance_score * 100)
        
        # Calculate statistical significance (simplified)
        statistical_significance = self._calculate_statistical_significance(
            baseline_result, candidate_result
        )
        
        # Determine winner
        winner = self._determine_winner(baseline_result, candidate_result, statistical_significance)
        
        # Calculate confidence level
        confidence_level = max(0.0, 1.0 - statistical_significance)
        
        return ComparisonResult(
            baseline=baseline_result,
            candidate=candidate_result,
            improvement=improvement,
            statistical_significance=statistical_significance,
            winner=winner,
            confidence_level=confidence_level
        )
    
    def _calculate_statistical_significance(
        self, 
        baseline: EvaluationResult, 
        candidate: EvaluationResult
    ) -> float:
        """Calculate statistical significance (simplified p-value estimation)"""
        
        # This is a simplified implementation
        # In production, you'd want proper statistical testing
        
        baseline_score = baseline.performance_score
        candidate_score = candidate.performance_score
        
        # Simple heuristic based on difference and sample size
        score_diff = abs(candidate_score - baseline_score)
        min_sample_size = min(baseline.test_cases_used, candidate.test_cases_used)
        
        # Rough p-value estimation
        if score_diff < 0.05:
            return 0.8  # High p-value (not significant)
        elif score_diff < 0.1:
            return 0.3
        elif score_diff < 0.2:
            return 0.1
        else:
            return 0.01  # Low p-value (significant)
    
    def _determine_winner(
        self, 
        baseline: EvaluationResult, 
        candidate: EvaluationResult, 
        p_value: float
    ) -> str:
        """Determine the winner of the A/B test"""
        
        # Require statistical significance (p < 0.05) and meaningful improvement
        if p_value > 0.05:
            return "tie"  # Not statistically significant
        
        score_diff = candidate.performance_score - baseline.performance_score
        
        if score_diff > 0.02:  # At least 2% improvement
            return "candidate"
        elif score_diff < -0.02:  # At least 2% degradation
            return "baseline"
        else:
            return "tie"


class EvaluationTestSuite:
    """Manages test cases for prompt evaluation"""
    
    def __init__(self):
        self.test_cases = []
    
    async def generate_test_cases(
        self, 
        scenario_types: List[str] = None,
        difficulty_levels: List[str] = None,
        count_per_scenario: int = 5
    ) -> List[EvaluationTestCase]:
        """Generate test cases for evaluation"""
        
        if scenario_types is None:
            scenario_types = ['professional', 'casual', 'technical', 'urgent']
        
        if difficulty_levels is None:
            difficulty_levels = ['easy', 'medium', 'hard']
        
        test_cases = []
        
        # Get existing emails from database for test cases
        existing_emails = [
            email async for email in Email.objects.all()[:20]  # Limit to recent emails
        ]
        
        if not existing_emails:
            # Generate synthetic test cases if no emails exist
            test_cases = await self._generate_synthetic_test_cases(
                scenario_types, difficulty_levels, count_per_scenario
            )
        else:
            # Use existing emails as test cases
            for email in existing_emails:
                test_case = EvaluationTestCase(
                    email=email,
                    expected_qualities={
                        'f1_score': 0.7,
                        'semantic_similarity': 0.7,
                        'clarity': 0.8,
                        'professionalism': 0.8
                    },
                    scenario_type=email.scenario_type or 'professional',
                    difficulty_level='medium'  # Default difficulty
                )
                test_cases.append(test_case)
        
        logger.info(f"Generated {len(test_cases)} test cases for evaluation")
        return test_cases
    
    async def _generate_synthetic_test_cases(
        self, 
        scenario_types: List[str],
        difficulty_levels: List[str], 
        count_per_scenario: int
    ) -> List[EvaluationTestCase]:
        """Generate synthetic test cases when no real emails are available"""
        
        synthetic_emails = [
            {
                'subject': 'Project Status Update Required',
                'body': 'Could you please provide an update on the current project status? We need this for the stakeholder meeting.',
                'sender': 'manager@company.com',
                'scenario_type': 'professional'
            },
            {
                'subject': 'Quick Question',
                'body': 'Hey! Just wondering if you\'re still available for coffee tomorrow?',
                'sender': 'friend@email.com',
                'scenario_type': 'casual'
            },
            {
                'subject': 'System Integration Issues',
                'body': 'We\'re experiencing API timeout errors with the new microservice. Can you investigate the connection pooling configuration?',
                'sender': 'tech@company.com',
                'scenario_type': 'technical'
            },
            {
                'subject': 'URGENT: Server Down',
                'body': 'Production server is down. Need immediate assistance!',
                'sender': 'ops@company.com',
                'scenario_type': 'urgent'
            }
        ]
        
        test_cases = []
        
        for email_template in synthetic_emails:
            # Create email object (don't save to database)
            email = Email(
                subject=email_template['subject'],
                body=email_template['body'],
                sender=email_template['sender'],
                scenario_type=email_template['scenario_type']
            )
            
            test_case = EvaluationTestCase(
                email=email,
                expected_qualities={
                    'f1_score': 0.7,
                    'semantic_similarity': 0.7,
                    'clarity': 0.8,
                    'professionalism': 0.8 if email_template['scenario_type'] == 'professional' else 0.6
                },
                scenario_type=email_template['scenario_type'],
                difficulty_level='medium'
            )
            test_cases.append(test_case)
        
        return test_cases


class EvaluationEngine:
    """Main evaluation engine coordinating all evaluation components"""
    
    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        reward_aggregator: RewardFunctionAggregator
    ):
        self.llm_provider = llm_provider
        self.evaluator = BatchPromptEvaluator(reward_aggregator)
        self.ab_testing = ABTestingEngine(self.evaluator)
        self.test_suite = EvaluationTestSuite()
    
    async def evaluate_prompt_performance(
        self,
        prompt: SystemPrompt,
        test_case_count: int = 10
    ) -> EvaluationResult:
        """Evaluate a single prompt's performance"""
        
        # Generate test cases
        test_cases = await self.test_suite.generate_test_cases()
        if len(test_cases) > test_case_count:
            test_cases = test_cases[:test_case_count]
        
        # Run evaluation
        result = await self.evaluator.evaluate_prompt(prompt, test_cases, self.llm_provider)
        
        # Update prompt's performance score in database
        prompt.performance_score = result.performance_score
        await sync_to_async(prompt.save)()
        
        logger.info(f"Evaluated prompt v{prompt.version}: score = {result.performance_score:.3f}")
        
        return result
    
    async def compare_prompt_candidates(
        self,
        baseline: SystemPrompt,
        candidates: List[SystemPrompt],
        test_case_count: int = 10
    ) -> List[ComparisonResult]:
        """Compare multiple prompt candidates against a baseline"""
        
        # Generate test cases
        test_cases = await self.test_suite.generate_test_cases()
        if len(test_cases) > test_case_count:
            test_cases = test_cases[:test_case_count]
        
        # Run A/B tests for each candidate
        comparison_tasks = [
            self.ab_testing.compare_prompts(baseline, candidate, test_cases, self.llm_provider)
            for candidate in candidates
        ]
        
        results = await asyncio.gather(*comparison_tasks)
        
        # Log results
        for result in results:
            logger.info(
                f"A/B Test: baseline v{baseline.version} vs candidate v{result.candidate.prompt.version} "
                f"- Winner: {result.winner}, Improvement: {result.improvement:.1f}%, "
                f"Confidence: {result.confidence_level:.1%}"
            )
        
        return results
    
    async def find_best_prompt(
        self,
        candidates: List[SystemPrompt],
        test_case_count: int = 10
    ) -> Tuple[SystemPrompt, EvaluationResult]:
        """Find the best performing prompt from a list of candidates"""
        
        if not candidates:
            raise ValueError("No candidates provided")
        
        if len(candidates) == 1:
            result = await self.evaluate_prompt_performance(candidates[0], test_case_count)
            return candidates[0], result
        
        # Evaluate all candidates
        test_cases = await self.test_suite.generate_test_cases()
        if len(test_cases) > test_case_count:
            test_cases = test_cases[:test_case_count]
        
        evaluation_tasks = [
            self.evaluator.evaluate_prompt(candidate, test_cases, self.llm_provider)
            for candidate in candidates
        ]
        
        results = await asyncio.gather(*evaluation_tasks)
        
        # Find best performer
        best_idx = 0
        best_score = results[0].performance_score
        
        for i, result in enumerate(results[1:], 1):
            if result.performance_score > best_score:
                best_score = result.performance_score
                best_idx = i
        
        best_prompt = candidates[best_idx]
        best_result = results[best_idx]
        
        # Update database with performance scores
        for candidate, result in zip(candidates, results):
            candidate.performance_score = result.performance_score
            await sync_to_async(candidate.save)()
        
        logger.info(f"Best prompt: v{best_prompt.version} with score {best_score:.3f}")
        
        return best_prompt, best_result