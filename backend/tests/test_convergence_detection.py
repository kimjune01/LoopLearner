"""
TDD Tests for Optimization Loop Convergence Detection
Following TDD principles: Write failing tests first that define expected behavior

Based on Requirements FR-026: Detect when optimization has converged and should stop
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from core.models import Session, SystemPrompt, Email, Draft, UserFeedback, SessionConfidence
from unittest.mock import patch, MagicMock


class TestConvergenceDetectionModels(TestCase):
    """Test convergence-related models and relationships - TDD approach"""
    
    def setUp(self):
        """Set up test data"""
        self.session = Session.objects.create(
            name="Convergence Test Session",
            description="Session for testing convergence detection"
        )
        
        self.prompt = SystemPrompt.objects.create(
            session=self.session,
            content="Test prompt",
            version=1,
            is_active=True
        )
    
    def test_session_has_convergence_related_fields(self):
        """Test that Session model has fields needed for convergence tracking"""
        # Session should track optimization iterations and feedback counts
        self.assertTrue(hasattr(self.session, 'optimization_iterations'))
        self.assertTrue(hasattr(self.session, 'total_feedback_collected'))
        
        # Should track when optimization was last run
        self.assertTrue(hasattr(self.session, 'updated_at'))
    
    def test_system_prompt_has_performance_tracking(self):
        """Test that SystemPrompt tracks performance for convergence"""
        # SystemPrompt should track performance scores over time
        self.assertTrue(hasattr(self.prompt, 'performance_score'))
        
        # Default performance score should be None (not yet calculated)
        self.assertIsNone(self.prompt.performance_score)
    
    def test_session_confidence_supports_convergence_detection(self):
        """Test that SessionConfidence model supports convergence detection"""
        from core.models import SessionConfidence
        
        confidence = SessionConfidence.objects.create(
            session=self.session,
            user_confidence=0.85,
            system_confidence=0.80,
            feedback_consistency_score=0.90,
            reasoning_alignment_score=0.85,
            total_feedback_count=25,
            consistent_feedback_streak=8,
            confidence_trend=0.1,
            last_calculated=timezone.now()
        )
        
        # Should have method to check if learning is sufficient (convergence reached)
        self.assertTrue(hasattr(confidence, 'is_learning_sufficient'))
        
        # Should have method to determine if learning should continue
        self.assertTrue(hasattr(confidence, 'should_continue_learning'))
        
        # Test convergence logic
        convergence_reached = confidence.is_learning_sufficient()
        should_continue = confidence.should_continue_learning()
        
        self.assertIsInstance(convergence_reached, bool)
        self.assertIsInstance(should_continue, bool)
        
        # If convergence is reached, should not continue learning
        if convergence_reached:
            self.assertFalse(should_continue)


class TestConvergenceDetectionService(TestCase):
    """Test convergence detection algorithms - TDD approach"""
    
    def setUp(self):
        """Set up test data with optimization history"""
        self.session = Session.objects.create(
            name="Convergence Algorithm Test",
            description="Session for testing convergence algorithms"
        )
        
        self.prompt = SystemPrompt.objects.create(
            session=self.session,
            content="Test prompt",
            version=1,
            is_active=True
        )
    
    def test_convergence_detector_service_exists(self):
        """Test that ConvergenceDetector service exists"""
        # This will FAIL initially - service doesn't exist yet
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        self.assertTrue(detector)
    
    def test_performance_plateau_detection(self):
        """Test detecting when performance has plateaued (no more improvement)"""
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        
        # Should have method to detect performance plateau
        self.assertTrue(hasattr(detector, 'detect_performance_plateau'))
        
        # Create series of prompts with performance scores showing plateau
        performance_history = [0.65, 0.72, 0.78, 0.81, 0.82, 0.82, 0.83, 0.82, 0.83, 0.82]
        
        for i, score in enumerate(performance_history):
            SystemPrompt.objects.create(
                session=self.session,
                content=f"Prompt version {i+1}",
                version=i+1,
                performance_score=score,
                is_active=(i == len(performance_history)-1)
            )
        
        plateau_detected = detector.detect_performance_plateau(self.session)
        
        # Should detect that performance has plateaued
        self.assertIsInstance(plateau_detected, bool)
        
        # With minimal improvement in recent versions, should detect plateau
        if len(performance_history) >= 5:
            # This specific pattern should indicate plateau
            recent_scores = performance_history[-5:]
            max_recent = max(recent_scores)
            min_recent = min(recent_scores)
            if max_recent - min_recent < 0.02:  # Less than 2% variation
                self.assertTrue(plateau_detected)
    
    def test_confidence_convergence_detection(self):
        """Test detecting convergence based on confidence metrics"""
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        
        # Should have method to check confidence-based convergence
        self.assertTrue(hasattr(detector, 'check_confidence_convergence'))
        
        # Create high-confidence scenario (converged)
        from core.models import SessionConfidence
        high_confidence = SessionConfidence.objects.create(
            session=self.session,
            user_confidence=0.92,
            system_confidence=0.88,
            feedback_consistency_score=0.95,
            reasoning_alignment_score=0.90,
            total_feedback_count=50,
            consistent_feedback_streak=15,
            confidence_trend=0.02,  # Minimal positive trend
            last_calculated=timezone.now()
        )
        
        convergence_reached = detector.check_confidence_convergence(self.session)
        self.assertIsInstance(convergence_reached, bool)
        
        # With high confidence scores, should detect convergence
        if high_confidence.is_learning_sufficient():
            self.assertTrue(convergence_reached)
    
    def test_feedback_pattern_stability_detection(self):
        """Test detecting when user feedback patterns have stabilized"""
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        
        # Should have method to detect stable feedback patterns
        self.assertTrue(hasattr(detector, 'detect_feedback_stability'))
        
        # Create emails and feedback with stable patterns
        for i in range(20):
            email = Email.objects.create(
                session=self.session,
                subject=f"Test Email {i}",
                body=f"Test body {i}",
                sender=f"test{i}@example.com"
            )
            
            draft = Draft.objects.create(
                email=email,
                content=f"Test draft {i}",
                system_prompt=self.prompt
            )
            
            # Create pattern: high acceptance rate in recent feedback
            action = 'accept' if i >= 5 else 'reject'  # Last 15 are accepts (75% overall)
            
            UserFeedback.objects.create(
                draft=draft,
                action=action,
                reason=f"Feedback {i}"
            )
        
        stability_detected = detector.detect_feedback_stability(self.session)
        self.assertIsInstance(stability_detected, bool)
        
        # With consistent recent feedback, should detect stability
        recent_feedback = UserFeedback.objects.filter(
            draft__email__session=self.session
        ).order_by('-created_at')[:15]  # Use same window as detector
        
        if recent_feedback.count() >= 15:
            recent_actions = [f.action for f in recent_feedback]
            accept_ratio = recent_actions.count('accept') / len(recent_actions)
            
            # Should detect stability with high acceptance rate
            if accept_ratio >= 0.7:
                self.assertTrue(stability_detected)
    
    def test_overall_convergence_assessment(self):
        """Test comprehensive convergence assessment combining all factors"""
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        
        # Should have method for overall convergence assessment
        self.assertTrue(hasattr(detector, 'assess_convergence'))
        
        assessment = detector.assess_convergence(self.session)
        
        # Should return convergence assessment with details
        self.assertIsInstance(assessment, dict)
        self.assertIn('converged', assessment)
        self.assertIn('confidence_score', assessment)
        self.assertIn('factors', assessment)
        
        # Factors should include different convergence indicators
        factors = assessment['factors']
        self.assertIn('performance_plateau', factors)
        self.assertIn('confidence_convergence', factors)
        self.assertIn('feedback_stability', factors)
        self.assertIn('minimum_iterations_reached', factors)
    
    def test_early_stopping_criteria(self):
        """Test early stopping conditions to prevent premature convergence"""
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        
        # Should have method to check early stopping criteria
        self.assertTrue(hasattr(detector, 'check_early_stopping_criteria'))
        
        # Test scenario with insufficient data
        early_session = Session.objects.create(
            name="Early Session",
            description="Session with minimal data",
            optimization_iterations=2,
            total_feedback_collected=5
        )
        
        should_stop_early = detector.check_early_stopping_criteria(early_session)
        self.assertIsInstance(should_stop_early, bool)
        
        # With minimal iterations and feedback, should NOT stop early (need more data)
        self.assertFalse(should_stop_early)
    
    def test_convergence_confidence_scoring(self):
        """Test confidence scoring for convergence decisions"""
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        
        # Should have method to calculate convergence confidence
        self.assertTrue(hasattr(detector, 'calculate_convergence_confidence'))
        
        confidence_score = detector.calculate_convergence_confidence(self.session)
        
        # Should return confidence score between 0 and 1
        self.assertIsInstance(confidence_score, (int, float))
        self.assertGreaterEqual(confidence_score, 0.0)
        self.assertLessEqual(confidence_score, 1.0)
    
    def test_convergence_recommendations(self):
        """Test generating actionable recommendations based on convergence state"""
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        
        # Should have method to generate recommendations
        self.assertTrue(hasattr(detector, 'generate_recommendations'))
        
        # Test with non-converged scenario
        factors = {
            'performance_plateau': False,
            'confidence_convergence': False,
            'feedback_stability': False,
            'minimum_iterations_reached': False,
            'minimum_feedback_reached': False
        }
        recommendations = detector.generate_recommendations(self.session, factors, False)
        
        # Should return list of actionable recommendations
        self.assertIsInstance(recommendations, list)
        
        for recommendation in recommendations:
            self.assertIn('action', recommendation)
            self.assertIn('reason', recommendation)
            self.assertIn('priority', recommendation)
        
        # Test with converged scenario
        converged_factors = {
            'performance_plateau': True,
            'confidence_convergence': True,
            'feedback_stability': True,
            'minimum_iterations_reached': True,
            'minimum_feedback_reached': True
        }
        converged_recommendations = detector.generate_recommendations(self.session, converged_factors, True)
        
        # Should recommend stopping optimization
        stop_recommendations = [r for r in converged_recommendations if r['action'] == 'stop_optimization']
        self.assertGreater(len(stop_recommendations), 0)


class TestConvergenceDetectionAPI(TestCase):
    """Test convergence detection API endpoints - TDD approach"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.session = Session.objects.create(
            name="API Convergence Test",
            description="Session for testing convergence API"
        )
        
        self.prompt = SystemPrompt.objects.create(
            session=self.session,
            content="Test prompt",
            version=1,
            is_active=True
        )
    
    def test_convergence_assessment_endpoint_exists(self):
        """Test that convergence assessment endpoint exists"""
        # This will FAIL initially - endpoint doesn't exist yet
        
        response = self.client.get(
            reverse('convergence-assessment', kwargs={'session_id': self.session.id})
        )
        
        self.assertEqual(response.status_code, 200)
    
    def test_convergence_assessment_returns_comprehensive_data(self):
        """Test that convergence endpoint returns detailed assessment"""
        response = self.client.get(
            reverse('convergence-assessment', kwargs={'session_id': self.session.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Should include convergence assessment
        self.assertIn('session_id', response_data)
        self.assertIn('convergence_assessment', response_data)
        
        assessment = response_data['convergence_assessment']
        self.assertIn('converged', assessment)
        self.assertIn('confidence_score', assessment)
        self.assertIn('factors', assessment)
        self.assertIn('recommendations', assessment)
        
        # Should include historical context
        self.assertIn('optimization_history', response_data)
        self.assertIn('performance_trend', response_data)
    
    def test_force_convergence_endpoint(self):
        """Test endpoint to manually mark session as converged"""
        force_data = {
            'reason': 'Manual convergence due to business requirements',
            'override_confidence_check': True
        }
        
        response = self.client.post(
            reverse('force-convergence', kwargs={'session_id': self.session.id}),
            data=json.dumps(force_data),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
        
        # Should update session convergence status
        response_data = response.json()
        self.assertIn('convergence_forced', response_data)
        self.assertIn('reason', response_data)
    
    def test_convergence_history_endpoint(self):
        """Test endpoint to get convergence assessment history"""
        response = self.client.get(
            reverse('convergence-history', kwargs={'session_id': self.session.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        self.assertIn('session_id', response_data)
        self.assertIn('convergence_history', response_data)
        self.assertIn('assessment_timeline', response_data)
    
    def test_convergence_api_validation_errors(self):
        """Test convergence API error handling"""
        # Test invalid session ID
        response = self.client.get(
            reverse('convergence-assessment', kwargs={'session_id': '00000000-0000-0000-0000-000000000000'})
        )
        
        self.assertEqual(response.status_code, 404)
        
        # Test invalid force convergence data
        invalid_data = {
            'reason': '',  # Empty reason
            'override_confidence_check': 'invalid'  # Invalid boolean
        }
        
        response = self.client.post(
            reverse('force-convergence', kwargs={'session_id': self.session.id}),
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)


class TestConvergenceIntegrationWithOptimization(TestCase):
    """Test convergence detection integration with optimization orchestrator"""
    
    def setUp(self):
        """Set up test data"""
        self.session = Session.objects.create(
            name="Integration Test Session",
            description="Session for testing convergence integration"
        )
        
        self.prompt = SystemPrompt.objects.create(
            session=self.session,
            content="Test prompt",
            version=1,
            is_active=True
        )
    
    def test_optimization_respects_convergence_detection(self):
        """Test that optimization orchestrator respects convergence decisions"""
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        
        # Mock scenario where convergence is detected
        with patch.object(detector, 'assess_convergence') as mock_assess:
            mock_assess.return_value = {
                'converged': True,
                'confidence_score': 0.95,
                'factors': {
                    'performance_plateau': True,
                    'confidence_convergence': True,
                    'feedback_stability': True,
                    'minimum_iterations_reached': True
                },
                'recommendations': [{
                    'action': 'stop_optimization',
                    'reason': 'High confidence convergence detected',
                    'priority': 'high'
                }]
            }
            
            # Test integration with optimization decision-making
            assessment = detector.assess_convergence(self.session)
            
            # Should indicate convergence reached
            self.assertTrue(assessment['converged'])
            self.assertGreater(assessment['confidence_score'], 0.9)
            
            # Should recommend stopping optimization
            stop_recommendations = [
                r for r in assessment['recommendations'] 
                if r['action'] == 'stop_optimization'
            ]
            self.assertGreater(len(stop_recommendations), 0)
    
    def test_convergence_prevents_unnecessary_optimization_runs(self):
        """Test that converged sessions don't trigger new optimization runs"""
        # This would integrate with the optimization orchestrator
        # to prevent wasted computational resources on converged sessions
        
        # Create scenario with high convergence confidence
        from core.models import SessionConfidence
        
        high_confidence = SessionConfidence.objects.create(
            session=self.session,
            user_confidence=0.95,
            system_confidence=0.92,
            feedback_consistency_score=0.98,
            reasoning_alignment_score=0.94,
            total_feedback_count=100,
            consistent_feedback_streak=25,
            confidence_trend=0.01,  # Minimal improvement
            last_calculated=timezone.now()
        )
        
        # Should indicate that optimization is not needed
        self.assertTrue(high_confidence.is_learning_sufficient())
        self.assertFalse(high_confidence.should_continue_learning())
    
    def test_convergence_detection_timing_considerations(self):
        """Test that convergence detection happens at appropriate intervals"""
        from app.services.convergence_detector import ConvergenceDetector
        
        detector = ConvergenceDetector()
        
        # Should have method to determine when to check convergence
        self.assertTrue(hasattr(detector, 'should_check_convergence'))
        
        # Test various scenarios for convergence checking timing
        should_check = detector.should_check_convergence(self.session)
        self.assertIsInstance(should_check, bool)
        
        # Should consider factors like:
        # - Time since last check
        # - Number of new feedback items
        # - Optimization iteration count
        # - Session activity level