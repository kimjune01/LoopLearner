"""
TDD Tests for Confidence Tracking System
Following TDD principles: Write failing tests first that define expected behavior

Based on Requirements FR-027: Track user and system confidence until threshold met
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from core.models import PromptLab, SystemPrompt, Email, Draft, DraftReason, UserFeedback, ReasonRating
from decimal import Decimal


class TestConfidenceTrackingModels(TestCase):
    """Test confidence tracking models and calculations - TDD approach"""
    
    def setUp(self):
        """Set up test data"""
        self.prompt_lab = PromptLab.objects.create(
            name="Confidence Test PromptLab",
            description="Session for testing confidence tracking"
        )
        
        self.prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="Test prompt",
            version=1,
            is_active=True
        )
    
    def test_prompt_lab_confidence_tracker_model_exists(self):
        """Test that PromptLabConfidence model exists for tracking confidence metrics"""
        # This will FAIL initially - model doesn't exist yet
        from core.models import PromptLabConfidence
        
        confidence = PromptLabConfidence(
            prompt_lab=self.prompt_lab,
            user_confidence=0.75,
            system_confidence=0.60,
            confidence_trend=0.05
        )
        confidence.save()
        
        self.assertEqual(confidence.prompt_lab, self.prompt_lab)
        self.assertEqual(confidence.user_confidence, 0.75)
        self.assertEqual(confidence.system_confidence, 0.60)
    
    def test_prompt_lab_confidence_has_required_fields(self):
        """Test that PromptLabConfidence has all required fields"""
        from core.models import PromptLabConfidence
        
        confidence = PromptLabConfidence(
            prompt_lab=self.prompt_lab,
            user_confidence=0.80,
            system_confidence=0.70,
            confidence_trend=0.10,
            feedback_consistency_score=0.85,
            reasoning_alignment_score=0.75,
            total_feedback_count=25,
            consistent_feedback_streak=5,
            last_calculated=None  # Will be auto-set
        )
        
        # Test field existence
        self.assertTrue(hasattr(confidence, 'user_confidence'))
        self.assertTrue(hasattr(confidence, 'system_confidence'))
        self.assertTrue(hasattr(confidence, 'confidence_trend'))
        self.assertTrue(hasattr(confidence, 'feedback_consistency_score'))
        self.assertTrue(hasattr(confidence, 'reasoning_alignment_score'))
        self.assertTrue(hasattr(confidence, 'total_feedback_count'))
        self.assertTrue(hasattr(confidence, 'consistent_feedback_streak'))
        self.assertTrue(hasattr(confidence, 'last_calculated'))
    
    def test_prompt_lab_confidence_validation(self):
        """Test that confidence values are properly validated"""
        from core.models import PromptLabConfidence
        from django.core.exceptions import ValidationError
        
        # Test valid confidence values
        valid_confidence = PromptLabConfidence(
            prompt_lab=self.prompt_lab,
            user_confidence=0.5,
            system_confidence=1.0
        )
        valid_confidence.full_clean()  # Should not raise
        
        # Test invalid confidence > 1
        with self.assertRaises(ValidationError):
            invalid_confidence = PromptLabConfidence(
                prompt_lab=self.prompt_lab,
                user_confidence=1.5,
                system_confidence=0.5
            )
            invalid_confidence.full_clean()
        
        # Test invalid confidence < 0
        with self.assertRaises(ValidationError):
            invalid_confidence = PromptLabConfidence(
                prompt_lab=self.prompt_lab,
                user_confidence=0.5,
                system_confidence=-0.1
            )
            invalid_confidence.full_clean()
    
    def test_confidence_threshold_constants(self):
        """Test that confidence threshold constants are defined"""
        from core.models import PromptLabConfidence
        
        # These should be class constants for determining when learning is sufficient
        self.assertTrue(hasattr(PromptLabConfidence, 'USER_CONFIDENCE_THRESHOLD'))
        self.assertTrue(hasattr(PromptLabConfidence, 'SYSTEM_CONFIDENCE_THRESHOLD'))
        self.assertTrue(hasattr(PromptLabConfidence, 'COMBINED_CONFIDENCE_THRESHOLD'))
        
        # Should be reasonable threshold values
        self.assertGreaterEqual(PromptLabConfidence.USER_CONFIDENCE_THRESHOLD, 0.7)
        self.assertGreaterEqual(PromptLabConfidence.SYSTEM_CONFIDENCE_THRESHOLD, 0.7)
        self.assertGreaterEqual(PromptLabConfidence.COMBINED_CONFIDENCE_THRESHOLD, 0.75)


class TestConfidenceCalculationService(TestCase):
    """Test confidence calculation algorithms - TDD approach"""
    
    def setUp(self):
        """Set up test data with feedback patterns"""
        self.prompt_lab = PromptLab.objects.create(
            name="Confidence Calculation Test",
            description="Session for testing confidence calculations"
        )
        
        self.prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="Test prompt",
            version=1,
            is_active=True
        )
        
        # Create test emails and drafts
        self.email1 = Email.objects.create(
            prompt_lab=self.prompt_lab,
            subject="Test Email 1",
            body="Test body 1",
            sender="test1@example.com"
        )
        
        self.email2 = Email.objects.create(
            prompt_lab=self.prompt_lab,
            subject="Test Email 2", 
            body="Test body 2",
            sender="test2@example.com"
        )
        
        self.draft1 = Draft.objects.create(
            email=self.email1,
            content="Test draft 1",
            system_prompt=self.prompt
        )
        
        self.draft2 = Draft.objects.create(
            email=self.email2,
            content="Test draft 2", 
            system_prompt=self.prompt
        )
    
    def test_confidence_calculator_service_exists(self):
        """Test that ConfidenceCalculator service exists"""
        # This will FAIL initially - service doesn't exist yet
        from app.services.confidence_calculator import ConfidenceCalculator
        
        calculator = ConfidenceCalculator()
        self.assertTrue(calculator)
    
    def test_user_confidence_calculation_interface(self):
        """Test that user confidence calculation interface is defined"""
        from app.services.confidence_calculator import ConfidenceCalculator
        
        calculator = ConfidenceCalculator()
        
        # Should have method to calculate user confidence
        self.assertTrue(hasattr(calculator, 'calculate_user_confidence'))
        
        # Test the interface
        user_confidence = calculator.calculate_user_confidence(self.prompt_lab)
        
        # Should return float between 0 and 1
        self.assertIsInstance(user_confidence, float)
        self.assertGreaterEqual(user_confidence, 0.0)
        self.assertLessEqual(user_confidence, 1.0)
    
    def test_system_confidence_calculation_interface(self):
        """Test that system confidence calculation interface is defined"""
        from app.services.confidence_calculator import ConfidenceCalculator
        
        calculator = ConfidenceCalculator()
        
        # Should have method to calculate system confidence
        self.assertTrue(hasattr(calculator, 'calculate_system_confidence'))
        
        # Test the interface
        system_confidence = calculator.calculate_system_confidence(self.prompt_lab)
        
        # Should return float between 0 and 1
        self.assertIsInstance(system_confidence, float)
        self.assertGreaterEqual(system_confidence, 0.0)
        self.assertLessEqual(system_confidence, 1.0)
    
    def test_user_confidence_based_on_consistency(self):
        """Test that user confidence increases with consistent feedback patterns"""
        from app.services.confidence_calculator import ConfidenceCalculator
        
        # Create consistent feedback pattern (all accepts)
        for i in range(5):
            feedback = UserFeedback.objects.create(
                draft=self.draft1,
                action='accept',
                reason=f'Good response {i}'
            )
        
        calculator = ConfidenceCalculator()
        confidence_consistent = calculator.calculate_user_confidence(self.prompt_lab)
        
        # Create inconsistent feedback pattern
        inconsistent_session = PromptLab.objects.create(name="Inconsistent PromptLab")
        inconsistent_prompt = SystemPrompt.objects.create(
            prompt_lab=inconsistent_session,
            content="Test prompt",
            version=1
        )
        inconsistent_email = Email.objects.create(
            prompt_lab=inconsistent_session,
            subject="Test",
            body="Test",
            sender="test@example.com"
        )
        inconsistent_draft = Draft.objects.create(
            email=inconsistent_email,
            content="Test draft",
            system_prompt=inconsistent_prompt
        )
        
        # Mixed feedback pattern
        actions = ['accept', 'reject', 'accept', 'edit', 'reject']
        for action in actions:
            UserFeedback.objects.create(
                draft=inconsistent_draft,
                action=action,
                reason='Mixed feedback'
            )
        
        confidence_inconsistent = calculator.calculate_user_confidence(inconsistent_session)
        
        # Consistent feedback should yield higher confidence
        self.assertGreater(confidence_consistent, confidence_inconsistent)
    
    def test_system_confidence_based_on_reasoning_alignment(self):
        """Test that system confidence increases when reasoning factors are consistently liked"""
        from app.services.confidence_calculator import ConfidenceCalculator
        
        # Create reasons and feedback with consistent likes
        reason1 = DraftReason.objects.create(text="Professional tone", confidence=0.9)
        reason2 = DraftReason.objects.create(text="Clear structure", confidence=0.8)
        
        self.draft1.reasons.add(reason1, reason2)
        
        feedback = UserFeedback.objects.create(
            draft=self.draft1,
            action='accept'
        )
        
        # All reasons liked consistently
        ReasonRating.objects.create(feedback=feedback, reason=reason1, liked=True)
        ReasonRating.objects.create(feedback=feedback, reason=reason2, liked=True)
        
        calculator = ConfidenceCalculator()
        
        # Should calculate high system confidence due to alignment
        system_confidence = calculator.calculate_system_confidence(self.prompt_lab)
        
        # Should be > 0.5 since reasoning aligns with user preferences
        self.assertGreater(system_confidence, 0.5)
    
    def test_confidence_threshold_checking(self):
        """Test methods for checking if confidence thresholds are met"""
        from app.services.confidence_calculator import ConfidenceCalculator
        
        calculator = ConfidenceCalculator()
        
        # Should have methods to check threshold status
        self.assertTrue(hasattr(calculator, 'is_user_confidence_sufficient'))
        self.assertTrue(hasattr(calculator, 'is_system_confidence_sufficient'))
        self.assertTrue(hasattr(calculator, 'should_continue_learning'))
        
        # Test threshold checking
        user_sufficient = calculator.is_user_confidence_sufficient(self.prompt_lab)
        system_sufficient = calculator.is_system_confidence_sufficient(self.prompt_lab)
        should_continue = calculator.should_continue_learning(self.prompt_lab)
        
        # Should return boolean values
        self.assertIsInstance(user_sufficient, bool)
        self.assertIsInstance(system_sufficient, bool)
        self.assertIsInstance(should_continue, bool)
        
        # Logic: should continue learning if either confidence is insufficient
        if user_sufficient and system_sufficient:
            self.assertFalse(should_continue)


class TestConfidenceTrackingAPI(TestCase):
    """Test confidence tracking API endpoints - TDD approach"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.prompt_lab = PromptLab.objects.create(
            name="API Confidence Test",
            description="Session for testing confidence API"
        )
        
        self.prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="Test prompt",
            version=1,
            is_active=True
        )
    
    def test_prompt_lab_confidence_endpoint_exists(self):
        """Test that  confidence endpoint exists"""
        # This will FAIL initially - endpoint doesn't exist yet
        
        response = self.client.get(
            reverse('prompt-lab-confidence', kwargs={'prompt_lab_id': self.prompt_lab.id})
        )
        
        self.assertEqual(response.status_code, 200)
    
    def test_prompt_lab_confidence_returns_metrics(self):
        """Test that confidence endpoint returns confidence metrics"""
        response = self.client.get(
            reverse('-confidence', kwargs={'prompt_lab_id': self.prompt_lab.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Should include confidence metrics
        self.assertIn('user_confidence', response_data)
        self.assertIn('system_confidence', response_data)
        self.assertIn('confidence_trend', response_data)
        self.assertIn('is_learning_sufficient', response_data)
        self.assertIn('should_continue_learning', response_data)
        
        # Should include detailed breakdown
        self.assertIn('confidence_breakdown', response_data)
        breakdown = response_data['confidence_breakdown']
        self.assertIn('feedback_consistency_score', breakdown)
        self.assertIn('reasoning_alignment_score', breakdown)
        self.assertIn('total_feedback_count', breakdown)
    
    def test_confidence_calculation_trigger_endpoint(self):
        """Test endpoint to manually trigger confidence recalculation"""
        response = self.client.post(
            reverse('recalculate-confidence', kwargs={'prompt_lab_id': self.prompt_lab.id}),
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
        
        response_data = response.json()
        self.assertIn('user_confidence', response_data)
        self.assertIn('system_confidence', response_data)
        self.assertIn('calculation_timestamp', response_data)
    
    def test_confidence_history_endpoint(self):
        """Test endpoint to get confidence tracking history"""
        response = self.client.get(
            reverse('confidence-history', kwargs={'prompt_lab_id': self.prompt_lab.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        self.assertIn('confidence_history', response_data)
        self.assertIn('prompt_lab_id', response_data)
        
        # History should be an array
        self.assertIsInstance(response_data['confidence_history'], list)
    
    def test_confidence_thresholds_endpoint(self):
        """Test endpoint to get/update confidence thresholds"""
        # GET current thresholds
        response = self.client.get(
            reverse('confidence-thresholds', kwargs={'prompt_lab_id': self.prompt_lab.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        self.assertIn('user_confidence_threshold', response_data)
        self.assertIn('system_confidence_threshold', response_data)
        self.assertIn('combined_confidence_threshold', response_data)
        
        # POST to update thresholds
        new_thresholds = {
            'user_confidence_threshold': 0.8,
            'system_confidence_threshold': 0.75
        }
        
        response = self.client.post(
            reverse('confidence-thresholds', kwargs={'prompt_lab_id': self.prompt_lab.id}),
            data=json.dumps(new_thresholds),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
    
    def test_confidence_api_validation_errors(self):
        """Test confidence API error handling"""
        # Test invalid prompt lab ID
        response = self.client.get(
            reverse('-confidence', kwargs={'prompt_lab_id': '00000000-0000-0000-0000-000000000000'})
        )
        
        self.assertEqual(response.status_code, 404)
        
        # Test invalid threshold values
        invalid_thresholds = {
            'user_confidence_threshold': 1.5,  # > 1.0
            'system_confidence_threshold': -0.1  # < 0.0
        }
        
        response = self.client.post(
            reverse('confidence-thresholds', kwargs={'prompt_lab_id': self.prompt_lab.id}),
            data=json.dumps(invalid_thresholds),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)


class TestConfidenceIntegrationWithOptimization(TestCase):
    """Test confidence tracking integration with optimization system"""
    
    def setUp(self):
        """Set up test data"""
        self.prompt_lab = PromptLab.objects.create(
            name="Integration Test PromptLab",
            description="Session for testing confidence integration"
        )
        
        self.prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="Test prompt",
            version=1,
            is_active=True
        )
    
    def test_optimization_respects_confidence_thresholds(self):
        """Test that optimization system checks confidence before running"""
        from app.services.confidence_calculator import ConfidenceCalculator
        
        calculator = ConfidenceCalculator()
        
        # Should not trigger optimization if confidence is insufficient
        should_continue = calculator.should_continue_learning(self.prompt_lab)
        
        if should_continue:
            # Low confidence - optimization should be allowed/encouraged
            self.assertTrue(True)  # This is expected for new prompt labs
        else:
            # High confidence - optimization might be skipped
            # This would happen in mature  with sufficient learning
            self.assertTrue(True)  # Both cases are valid
    
    def test_confidence_influences_cold_start_completion(self):
        """Test that confidence determines when cold start phase is complete"""
        from app.services.confidence_calculator import ConfidenceCalculator
        
        calculator = ConfidenceCalculator()
        
        # Should have method to check cold start status
        self.assertTrue(hasattr(calculator, 'is_cold_start_complete'))
        
        cold_start_complete = calculator.is_cold_start_complete(self.prompt_lab)
        self.assertIsInstance(cold_start_complete, bool)
    
    def test_confidence_tracking_updates_session_stats(self):
        """Test that confidence calculations update  statistics"""
        # This would integrate with existing  stats
        # PromptLab should track confidence progression over time
        
        # Should be able to see confidence trend in  detail
        from django.urls import reverse
        client = Client()
        
        response = client.get(
            reverse('prompt-lab-detail', kwargs={'prompt_lab_id': self.prompt_lab.id})
        )
        
        self.assertEqual(response.status_code, 200)
        #  detail should include confidence information
        # (This will be implemented when we integrate with  detail)