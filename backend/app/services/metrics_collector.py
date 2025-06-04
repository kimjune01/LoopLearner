"""
Comprehensive metrics collection for optimization runs
Collects detailed performance data including component scores, statistical analysis, and cost breakdown
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class ComponentMetrics:
    """Individual component scores from reward aggregator"""
    f1_score: float
    human_feedback_score: float
    perplexity_score: float
    exact_match_score: float
    length_appropriateness_score: float
    semantic_similarity_score: float
    weighted_total: float


@dataclass
class CandidateMetrics:
    """Complete metrics for a single candidate prompt"""
    candidate_id: str
    prompt_content: str
    performance_score: float
    component_metrics: ComponentMetrics
    test_cases_passed: int
    test_cases_failed: int
    error_rate: float
    generation_time_ms: float
    sample_outputs: List[str]


@dataclass
class StatisticalAnalysis:
    """Statistical significance and confidence data"""
    improvement_percentage: float
    confidence_level: float
    p_value: float
    statistical_significance: str  # "significant", "not_significant", "marginal"
    sample_size: int
    variance: float
    standard_deviation: float


@dataclass
class ThresholdAnalysis:
    """Analysis of deployment decision thresholds"""
    strategy_used: str
    min_improvement_threshold: float
    min_confidence_threshold: float
    improvement_met: bool
    confidence_met: bool
    deployment_decision: str  # "deployed", "not_deployed", "insufficient_improvement"
    deployment_reason: str


@dataclass
class CostAnalysis:
    """Cost and ROI analysis for the optimization"""
    total_cost_usd: float
    cost_per_iteration: float
    cost_per_evaluation: float
    iterations_performed: int
    evaluations_performed: int
    estimated_benefit_usd: float
    roi_percentage: float
    cost_efficiency_score: float


class MetricsCollector:
    """Collects and structures comprehensive optimization metrics"""
    
    def __init__(self):
        self.candidates: List[CandidateMetrics] = []
        self.baseline_metrics: Optional[CandidateMetrics] = None
        self.statistical_analysis: Optional[StatisticalAnalysis] = None
        self.threshold_analysis: Optional[ThresholdAnalysis] = None
        self.cost_analysis: Optional[CostAnalysis] = None
        self._start_time = timezone.now()
        
    def add_candidate_metrics(
        self,
        candidate_id: str,
        prompt_content: str,
        performance_score: float,
        component_scores: Dict[str, float],
        test_results: Dict[str, Any],
        generation_time_ms: float,
        sample_outputs: List[str] = None
    ):
        """Add metrics for a candidate prompt"""
        
        # Structure component metrics
        component_metrics = ComponentMetrics(
            f1_score=component_scores.get('f1_score', 0.0),
            human_feedback_score=component_scores.get('human_feedback_score', 0.0),
            perplexity_score=component_scores.get('perplexity_score', 0.0),
            exact_match_score=component_scores.get('exact_match_score', 0.0),
            length_appropriateness_score=component_scores.get('length_appropriateness_score', 0.0),
            semantic_similarity_score=component_scores.get('semantic_similarity_score', 0.0),
            weighted_total=performance_score
        )
        
        # Calculate test metrics
        passed = test_results.get('passed', 0)
        failed = test_results.get('failed', 0)
        total_tests = passed + failed
        error_rate = failed / total_tests if total_tests > 0 else 0.0
        
        candidate_metrics = CandidateMetrics(
            candidate_id=candidate_id,
            prompt_content=prompt_content[:500],  # Truncate for storage
            performance_score=performance_score,
            component_metrics=component_metrics,
            test_cases_passed=passed,
            test_cases_failed=failed,
            error_rate=error_rate,
            generation_time_ms=generation_time_ms,
            sample_outputs=sample_outputs[:3] if sample_outputs else []  # Store top 3 samples
        )
        
        if candidate_id == "baseline":
            self.baseline_metrics = candidate_metrics
        else:
            self.candidates.append(candidate_metrics)
            
        logger.info(f"Added metrics for candidate {candidate_id}: score={performance_score:.3f}")
    
    def set_statistical_analysis(
        self,
        improvement_percentage: float,
        confidence_level: float,
        p_value: float,
        sample_size: int,
        variance: float = 0.0
    ):
        """Set statistical analysis results"""
        
        # Determine significance level
        if p_value < 0.01:
            significance = "significant"
        elif p_value < 0.05:
            significance = "marginal"
        else:
            significance = "not_significant"
            
        self.statistical_analysis = StatisticalAnalysis(
            improvement_percentage=improvement_percentage,
            confidence_level=confidence_level,
            p_value=p_value,
            statistical_significance=significance,
            sample_size=sample_size,
            variance=variance,
            standard_deviation=variance ** 0.5 if variance >= 0 else 0.0
        )
        
        logger.info(f"Statistical analysis: {improvement_percentage:.1f}% improvement, p={p_value:.3f}")
    
    def set_threshold_analysis(
        self,
        strategy_used: str,
        min_improvement_threshold: float,
        min_confidence_threshold: float,
        actual_improvement: float,
        actual_confidence: float,
        deployed: bool,
        deployment_reason: str
    ):
        """Set threshold analysis results"""
        
        improvement_met = actual_improvement >= min_improvement_threshold
        confidence_met = actual_confidence >= min_confidence_threshold
        
        if deployed:
            decision = "deployed"
        elif not improvement_met:
            decision = "insufficient_improvement"
        else:
            decision = "not_deployed"
            
        self.threshold_analysis = ThresholdAnalysis(
            strategy_used=strategy_used,
            min_improvement_threshold=min_improvement_threshold,
            min_confidence_threshold=min_confidence_threshold,
            improvement_met=improvement_met,
            confidence_met=confidence_met,
            deployment_decision=decision,
            deployment_reason=deployment_reason
        )
        
        logger.info(f"Threshold analysis: strategy={strategy_used}, deployed={deployed}")
    
    def set_cost_analysis(
        self,
        total_cost_usd: float,
        iterations_performed: int,
        evaluations_performed: int,
        estimated_benefit_usd: float = 0.0
    ):
        """Set cost and ROI analysis"""
        
        cost_per_iteration = total_cost_usd / iterations_performed if iterations_performed > 0 else 0.0
        cost_per_evaluation = total_cost_usd / evaluations_performed if evaluations_performed > 0 else 0.0
        
        # Calculate ROI
        roi_percentage = 0.0
        if total_cost_usd > 0 and estimated_benefit_usd > 0:
            roi_percentage = ((estimated_benefit_usd - total_cost_usd) / total_cost_usd) * 100
        
        # Cost efficiency score (0-1 scale)
        cost_efficiency_score = min(1.0, estimated_benefit_usd / total_cost_usd) if total_cost_usd > 0 else 1.0
        
        self.cost_analysis = CostAnalysis(
            total_cost_usd=total_cost_usd,
            cost_per_iteration=cost_per_iteration,
            cost_per_evaluation=cost_per_evaluation,
            iterations_performed=iterations_performed,
            evaluations_performed=evaluations_performed,
            estimated_benefit_usd=estimated_benefit_usd,
            roi_percentage=roi_percentage,
            cost_efficiency_score=cost_efficiency_score
        )
        
        logger.info(f"Cost analysis: ${total_cost_usd:.2f} total, ROI={roi_percentage:.1f}%")
    
    def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics breakdown for database storage"""
        
        best_candidate = None
        if self.candidates:
            best_candidate = max(self.candidates, key=lambda c: c.performance_score)
        
        total_time = (timezone.now() - self._start_time).total_seconds()
        
        return {
            "summary": {
                "total_candidates_tested": len(self.candidates),
                "best_performance_score": best_candidate.performance_score if best_candidate else 0.0,
                "baseline_performance_score": self.baseline_metrics.performance_score if self.baseline_metrics else 0.0,
                "optimization_time_seconds": total_time,
                "timestamp": timezone.now().isoformat()
            },
            "baseline_metrics": asdict(self.baseline_metrics) if self.baseline_metrics else None,
            "best_candidate_metrics": asdict(best_candidate) if best_candidate else None,
            "component_scores_comparison": self._get_component_comparison(),
            "performance_distribution": self._get_performance_distribution()
        }
    
    def get_candidate_metrics(self) -> List[Dict[str, Any]]:
        """Get all candidate metrics for database storage"""
        result = []
        
        if self.baseline_metrics:
            result.append(asdict(self.baseline_metrics))
            
        for candidate in self.candidates:
            result.append(asdict(candidate))
            
        return result
    
    def get_statistical_analysis(self) -> Dict[str, Any]:
        """Get statistical analysis for database storage"""
        if self.statistical_analysis:
            return asdict(self.statistical_analysis)
        return {}
    
    def get_threshold_analysis(self) -> Dict[str, Any]:
        """Get threshold analysis for database storage"""
        if self.threshold_analysis:
            return asdict(self.threshold_analysis)
        return {}
    
    def get_cost_analysis(self) -> Dict[str, Any]:
        """Get cost analysis for database storage"""
        if self.cost_analysis:
            return asdict(self.cost_analysis)
        return {}
    
    def _get_component_comparison(self) -> Dict[str, Any]:
        """Compare component scores between baseline and best candidate"""
        if not self.baseline_metrics or not self.candidates:
            return {}
            
        best_candidate = max(self.candidates, key=lambda c: c.performance_score)
        baseline_components = self.baseline_metrics.component_metrics
        candidate_components = best_candidate.component_metrics
        
        return {
            "f1_improvement": candidate_components.f1_score - baseline_components.f1_score,
            "human_feedback_improvement": candidate_components.human_feedback_score - baseline_components.human_feedback_score,
            "perplexity_improvement": candidate_components.perplexity_score - baseline_components.perplexity_score,
            "exact_match_improvement": candidate_components.exact_match_score - baseline_components.exact_match_score,
            "length_improvement": candidate_components.length_appropriateness_score - baseline_components.length_appropriateness_score,
            "semantic_improvement": candidate_components.semantic_similarity_score - baseline_components.semantic_similarity_score
        }
    
    def _get_performance_distribution(self) -> Dict[str, Any]:
        """Get distribution statistics for all candidates"""
        if not self.candidates:
            return {}
            
        scores = [c.performance_score for c in self.candidates]
        
        return {
            "min_score": min(scores),
            "max_score": max(scores),
            "mean_score": sum(scores) / len(scores),
            "score_range": max(scores) - min(scores),
            "candidates_above_baseline": sum(1 for s in scores if s > (self.baseline_metrics.performance_score if self.baseline_metrics else 0)),
            "improvement_rates": [
                (s - (self.baseline_metrics.performance_score if self.baseline_metrics else 0)) / (self.baseline_metrics.performance_score if self.baseline_metrics else 1) * 100
                for s in scores
            ]
        }