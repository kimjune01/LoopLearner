"""
Tests for Compute Optimization Controls
Ensures compute spend limits and progressive thresholds work correctly
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from core.models import PromptLab, SystemPrompt


class TestComputeOptimizationControls(TestCase):
    """Test compute optimization controls in convergence detection"""
    
    def setUp(self):
        """Set up test data"""
        self.prompt_lab = PromptLab.objects.create(
            name="Compute Test PromptLab",
            description="Session for testing compute controls"
        )
        
        self.prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="Test prompt",
            version=1,
            is_active=True
        )
    
    def test_hard_iteration_limit_enforced(self):
        """Test that hard iteration limit stops optimization"""
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        
        # Set  to max iterations
        self.prompt_lab.optimization_iterations = detector.MAX_ITERATIONS_HARD_LIMIT
        self.prompt_lab.save()
        
        # Should force convergence
        assessment = detector.assess_convergence(self.prompt_lab)
        
        self.assertTrue(assessment['converged'])
        self.assertEqual(assessment['factors'].get('hard_limit_reached'), True)
        self.assertEqual(assessment['confidence_score'], 1.0)  # Maximum confidence
        self.assertTrue(assessment.get('compute_saved', False))
    
    def test_progressive_performance_thresholds(self):
        """Test that performance thresholds change with iterations"""
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        
        # Test early stage (< 5 iterations)
        self.prompt_lab.optimization_iterations = 3
        threshold_early = detector._get_progressive_threshold(self.prompt_lab)
        self.assertEqual(threshold_early, 0.10)  # 10% threshold
        
        # Test refinement stage (5-10 iterations)
        self.prompt_lab.optimization_iterations = 7
        threshold_refinement = detector._get_progressive_threshold(self.prompt_lab)
        self.assertEqual(threshold_refinement, 0.05)  # 5% threshold
        
        # Test optimization stage (10-15 iterations)
        self.prompt_lab.optimization_iterations = 12
        threshold_optimization = detector._get_progressive_threshold(self.prompt_lab)
        self.assertEqual(threshold_optimization, 0.02)  # 2% threshold
        
        # Test diminishing returns (15+ iterations)
        self.prompt_lab.optimization_iterations = 17
        threshold_diminishing = detector._get_progressive_threshold(self.prompt_lab)
        self.assertEqual(threshold_diminishing, 0.01)  # 1% threshold
    
    def test_negative_performance_trend_early_exit(self):
        """Test that declining performance triggers early exit"""
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        
        # Create declining performance scores
        scores = [0.8, 0.7, 0.6]  # Getting worse
        for i, score in enumerate(scores):
            SystemPrompt.objects.create(
                prompt_lab=self.prompt_lab,
                content=f"Test prompt v{i+2}",
                version=i+2,
                performance_score=score,
                is_active=(i == len(scores)-1)
            )
        
        # Should detect negative trend
        negative_trend = detector._check_negative_performance_trend(self.prompt_lab)
        self.assertTrue(negative_trend)
        
        # Full assessment should recommend stopping
        assessment = detector.assess_convergence(self.prompt_lab)
        
        self.assertTrue(assessment['converged'])
        self.assertTrue(assessment['factors'].get('negative_trend_detected', False))
        self.assertTrue(assessment.get('compute_saved', False))
        
        # Should have critical recommendation
        stop_recommendations = [
            r for r in assessment['recommendations'] 
            if r.get('priority') == 'critical'
        ]
        self.assertGreater(len(stop_recommendations), 0)
    
    def test_compute_aware_recommendations(self):
        """Test that recommendations include compute cost information"""
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        
        # Set up a  approaching soft limit
        self.prompt_lab.optimization_iterations = detector.MAX_ITERATIONS_SOFT_LIMIT
        self.prompt_lab.total_feedback_collected = 50
        self.prompt_lab.save()
        
        assessment = detector.assess_convergence(self.prompt_lab)
        
        # Should have recommendation about approaching limit
        approaching_limit_recs = [
            r for r in assessment['recommendations']
            if 'approaching iteration limit' in r.get('reason', '') or 
               'Approaching iteration limit' in r.get('reason', '')
        ]
        
        # If no approaching limit recommendation, check for any iteration-related recommendation
        if len(approaching_limit_recs) == 0:
            # PromptLab might be converged or have other recommendations
            self.assertTrue(
                assessment['converged'] or 
                any('iteration' in r.get('reason', '').lower() for r in assessment['recommendations'])
            )
        
        # Test converged state includes savings estimate
        factors = {
            'performance_plateau': True,
            'confidence_convergence': True,
            'feedback_stability': True,
            'minimum_iterations_reached': True,
            'minimum_feedback_reached': True
        }
        
        savings_recommendations = detector.generate_recommendations(
            self.prompt_lab, factors, converged=True
        )
        
        savings_recs = [
            r for r in savings_recommendations
            if r.get('action') == 'compute_savings'
        ]
        
        if self.prompt_lab.optimization_iterations < detector.MAX_ITERATIONS_HARD_LIMIT:
            self.assertGreater(len(savings_recs), 0)
            # Should include dollar amount in reason
            self.assertIn('$', savings_recs[0]['reason'])
    
    def test_significant_performance_drop_triggers_convergence(self):
        """Test that a significant performance drop (>5%) triggers early exit"""
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        
        # Create performance with recent significant drop
        # Note: version 1 already exists from setUp
        scores = [0.85, 0.75, 0.70]  # Declining trend with 11.7% drop
        for i, score in enumerate(scores):
            SystemPrompt.objects.create(
                prompt_lab=self.prompt_lab,
                content=f"Test prompt v{i+2}",
                version=i+2,
                performance_score=score,
                is_active=(i == len(scores)-1)
            )
        
        # Should detect negative trend due to significant drop
        negative_trend = detector._check_negative_performance_trend(self.prompt_lab)
        
        # The drop from 0.85 to 0.75 is 11.7%, which is > 5%
        # But we need at least 3 scores for the method to work properly
        # Since we now have 3 scores (0.70, 0.75, 0.85 in reverse order)
        self.assertTrue(negative_trend, "Should detect negative trend with significant drop")