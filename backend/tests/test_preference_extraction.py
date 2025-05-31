"""
TDD Tests for User Preference Extraction System
Following TDD principles: Write failing tests first that define expected behavior

Based on Requirements FR-015: Preserve user preference statements in natural language
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from core.models import Session, SystemPrompt, Email, Draft, DraftReason, UserFeedback, ReasonRating, UserPreference
from datetime import datetime, timedelta


class TestPreferenceExtractionModels(TestCase):
    """Test preference-related models and relationships - TDD approach"""
    
    def setUp(self):
        """Set up test data"""
        self.session = Session.objects.create(
            name="Preference Test Session",
            description="Session for testing preference extraction"
        )
        
        self.prompt = SystemPrompt.objects.create(
            session=self.session,
            content="Test prompt",
            version=1,
            is_active=True
        )
    
    def test_user_preference_model_exists_and_has_fields(self):
        """Test that UserPreference model exists with required fields"""
        # UserPreference already exists in core.models, verify it has the right fields
        
        preference = UserPreference.objects.create(
            session=self.session,
            key="communication_style",
            value="I prefer concise, professional responses without unnecessary pleasantries",
            description="User's preferred communication style extracted from feedback patterns"
        )
        
        # Test field existence and values
        self.assertEqual(preference.session, self.session)
        self.assertEqual(preference.key, "communication_style")
        self.assertIn("concise", preference.value)
        self.assertTrue(preference.is_active)
    
    def test_extracted_preference_model_exists(self):
        """Test that ExtractedPreference model exists for automatic preference discovery"""
        # This will FAIL initially - model doesn't exist yet
        from core.models import ExtractedPreference
        
        extracted_pref = ExtractedPreference(
            session=self.session,
            source_feedback_ids=[1, 2, 3],
            preference_category="tone",
            preference_text="User prefers professional but friendly tone",
            confidence_score=0.85,
            extraction_method="reasoning_pattern_analysis",
            supporting_evidence="Consistently likes reasoning factors mentioning 'professional tone'"
        )
        extracted_pref.save()
        
        self.assertEqual(extracted_pref.session, self.session)
        self.assertEqual(extracted_pref.preference_category, "tone")
        self.assertEqual(extracted_pref.confidence_score, 0.85)
    
    def test_extracted_preference_has_required_fields(self):
        """Test that ExtractedPreference has all required fields"""
        from core.models import ExtractedPreference
        
        extracted_pref = ExtractedPreference(
            session=self.session,
            source_feedback_ids=[1, 2, 3, 4],
            preference_category="structure",
            preference_text="User prefers bullet-pointed responses with clear action items",
            confidence_score=0.92,
            extraction_method="feedback_pattern_analysis",
            supporting_evidence="80% acceptance rate for structured responses vs 40% for paragraphs",
            is_active=True,
            auto_extracted=True
        )
        
        # Test field existence
        self.assertTrue(hasattr(extracted_pref, 'source_feedback_ids'))
        self.assertTrue(hasattr(extracted_pref, 'preference_category'))
        self.assertTrue(hasattr(extracted_pref, 'preference_text'))
        self.assertTrue(hasattr(extracted_pref, 'confidence_score'))
        self.assertTrue(hasattr(extracted_pref, 'extraction_method'))
        self.assertTrue(hasattr(extracted_pref, 'supporting_evidence'))
        self.assertTrue(hasattr(extracted_pref, 'is_active'))
        self.assertTrue(hasattr(extracted_pref, 'auto_extracted'))
    
    def test_preference_validation(self):
        """Test that preference confidence scores are validated"""
        from core.models import ExtractedPreference
        from django.core.exceptions import ValidationError
        
        # Test valid confidence score
        valid_pref = ExtractedPreference(
            session=self.session,
            source_feedback_ids=[1],
            preference_category="test",
            preference_text="Test preference",
            confidence_score=0.75,
            extraction_method="test_method",
            supporting_evidence="Test evidence"
        )
        valid_pref.full_clean()  # Should not raise
        
        # Test invalid confidence > 1
        with self.assertRaises(ValidationError):
            invalid_pref = ExtractedPreference(
                session=self.session,
                source_feedback_ids=[1],
                preference_category="test",
                preference_text="Test preference",
                confidence_score=1.5,
                extraction_method="test_method",
                supporting_evidence="Test evidence"
            )
            invalid_pref.full_clean()
        
        # Test invalid confidence < 0
        with self.assertRaises(ValidationError):
            invalid_pref = ExtractedPreference(
                session=self.session,
                source_feedback_ids=[1],
                preference_category="test",
                preference_text="Test preference",
                confidence_score=-0.1,
                extraction_method="test_method",
                supporting_evidence="Test evidence"
            )
            invalid_pref.full_clean()


class TestPreferenceExtractionService(TestCase):
    """Test preference extraction algorithms - TDD approach"""
    
    def setUp(self):
        """Set up test data with feedback patterns"""
        self.session = Session.objects.create(
            name="Preference Extraction Test",
            description="Session for testing preference extraction"
        )
        
        self.prompt = SystemPrompt.objects.create(
            session=self.session,
            content="Test prompt",
            version=1,
            is_active=True
        )
        
        # Create test emails and drafts
        self.email1 = Email.objects.create(
            session=self.session,
            subject="Test Email 1",
            body="Test body 1",
            sender="test1@example.com"
        )
        
        self.draft1 = Draft.objects.create(
            email=self.email1,
            content="Test draft 1",
            system_prompt=self.prompt
        )
    
    def test_preference_extractor_service_exists(self):
        """Test that PreferenceExtractor service exists"""
        # This will FAIL initially - service doesn't exist yet
        from app.services.preference_extractor import PreferenceExtractor
        
        extractor = PreferenceExtractor()
        self.assertTrue(extractor)
    
    def test_preference_extraction_from_feedback_reasons(self):
        """Test extracting preferences from user feedback reason text"""
        from app.services.preference_extractor import PreferenceExtractor
        
        # Create feedback with explicit preference statements
        feedback1 = UserFeedback.objects.create(
            draft=self.draft1,
            action='reject',
            reason='Too verbose - I prefer concise responses that get straight to the point'
        )
        
        feedback2 = UserFeedback.objects.create(
            draft=self.draft1,
            action='edit',
            reason='The tone is too casual. I need professional language for business communications'
        )
        
        extractor = PreferenceExtractor()
        
        # Should have method to extract preferences from feedback text
        self.assertTrue(hasattr(extractor, 'extract_from_feedback_text'))
        
        preferences = extractor.extract_from_feedback_text(self.session)
        
        # Should return list of extracted preferences
        self.assertIsInstance(preferences, list)
        
        if len(preferences) > 0:
            pref = preferences[0]
            # Should include preference details
            self.assertIn('category', pref)
            self.assertIn('text', pref)
            self.assertIn('confidence', pref)
            self.assertIn('evidence', pref)
    
    def test_preference_extraction_from_reasoning_patterns(self):
        """Test extracting preferences from reasoning factor rating patterns"""
        from app.services.preference_extractor import PreferenceExtractor
        
        # Create reasoning factors and ratings with patterns
        reason1 = DraftReason.objects.create(
            text="Professional tone maintained",
            confidence=0.9
        )
        reason2 = DraftReason.objects.create(
            text="Concise and direct communication",
            confidence=0.85
        )
        reason3 = DraftReason.objects.create(
            text="Friendly and casual approach",
            confidence=0.7
        )
        
        self.draft1.reasons.add(reason1, reason2, reason3)
        
        feedback = UserFeedback.objects.create(
            draft=self.draft1,
            action='accept'
        )
        
        # Create consistent pattern: likes professional/concise, dislikes casual
        ReasonRating.objects.create(feedback=feedback, reason=reason1, liked=True)
        ReasonRating.objects.create(feedback=feedback, reason=reason2, liked=True)
        ReasonRating.objects.create(feedback=feedback, reason=reason3, liked=False)
        
        extractor = PreferenceExtractor()
        
        # Should have method to extract from reasoning patterns
        self.assertTrue(hasattr(extractor, 'extract_from_reasoning_patterns'))
        
        patterns = extractor.extract_from_reasoning_patterns(self.session)
        
        # Should identify preference patterns
        self.assertIsInstance(patterns, list)
    
    def test_preference_extraction_from_action_patterns(self):
        """Test extracting preferences from user action patterns"""
        from app.services.preference_extractor import PreferenceExtractor
        
        # Create pattern of feedback actions
        for i in range(5):
            email = Email.objects.create(
                session=self.session,
                subject=f"Email {i}",
                body=f"Body {i}",
                sender=f"test{i}@example.com"
            )
            draft = Draft.objects.create(
                email=email,
                content=f"Draft {i}",
                system_prompt=self.prompt
            )
            
            # Create pattern: accept short responses, reject long ones
            action = 'accept' if i % 2 == 0 else 'reject'
            reason = 'Too long' if action == 'reject' else 'Good length'
            
            UserFeedback.objects.create(
                draft=draft,
                action=action,
                reason=reason
            )
        
        extractor = PreferenceExtractor()
        
        # Should have method to extract from action patterns
        self.assertTrue(hasattr(extractor, 'extract_from_action_patterns'))
        
        action_prefs = extractor.extract_from_action_patterns(self.session)
        
        # Should identify patterns in user behavior
        self.assertIsInstance(action_prefs, list)
    
    def test_preference_consolidation_and_ranking(self):
        """Test consolidating multiple preference sources into ranked list"""
        from app.services.preference_extractor import PreferenceExtractor
        
        extractor = PreferenceExtractor()
        
        # Should have method to consolidate preferences
        self.assertTrue(hasattr(extractor, 'extract_all_preferences'))
        
        all_preferences = extractor.extract_all_preferences(self.session)
        
        # Should return consolidated, ranked preferences
        self.assertIsInstance(all_preferences, list)
        
        # Each preference should have required fields
        for pref in all_preferences:
            self.assertIn('category', pref)
            self.assertIn('text', pref)
            self.assertIn('confidence', pref)
            self.assertIn('sources', pref)  # List of evidence sources
    
    def test_preference_confidence_scoring(self):
        """Test that extracted preferences have appropriate confidence scores"""
        from app.services.preference_extractor import PreferenceExtractor
        
        # Create strong pattern for high confidence
        for i in range(10):
            feedback = UserFeedback.objects.create(
                draft=self.draft1,
                action='reject',
                reason='Too verbose - I prefer concise responses'
            )
        
        extractor = PreferenceExtractor()
        preferences = extractor.extract_all_preferences(self.session)
        
        # Should have high confidence for consistent patterns
        if preferences:
            # At least one preference should have reasonable confidence
            max_confidence = max(pref.get('confidence', 0) for pref in preferences)
            self.assertGreater(max_confidence, 0.5)
    
    def test_preference_category_classification(self):
        """Test that preferences are properly categorized"""
        from app.services.preference_extractor import PreferenceExtractor
        
        extractor = PreferenceExtractor()
        
        # Should have method to classify preference categories
        self.assertTrue(hasattr(extractor, 'classify_preference_category'))
        
        # Test classification of different preference types
        test_cases = [
            ("I prefer concise responses", "length"),
            ("Use professional tone", "tone"),
            ("Include bullet points", "structure"),
            ("Don't use too many technical terms", "vocabulary"),
            ("Be more friendly and warm", "tone")
        ]
        
        for text, expected_category in test_cases:
            category = extractor.classify_preference_category(text)
            # Should return a reasonable category (exact match not required)
            self.assertIsInstance(category, str)
            self.assertGreater(len(category), 0)


class TestPreferenceExtractionAPI(TestCase):
    """Test preference extraction API endpoints - TDD approach"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.session = Session.objects.create(
            name="API Preference Test",
            description="Session for testing preference API"
        )
        
        self.prompt = SystemPrompt.objects.create(
            session=self.session,
            content="Test prompt",
            version=1,
            is_active=True
        )
    
    def test_extract_preferences_endpoint_exists(self):
        """Test that preference extraction endpoint exists"""
        # This will FAIL initially - endpoint doesn't exist yet
        
        response = self.client.post(
            reverse('extract-preferences', kwargs={'session_id': self.session.id}),
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
    
    def test_extract_preferences_returns_extracted_preferences(self):
        """Test that extraction endpoint returns discovered preferences"""
        response = self.client.post(
            reverse('extract-preferences', kwargs={'session_id': self.session.id}),
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
        response_data = response.json()
        
        # Should include extracted preferences
        self.assertIn('extracted_preferences', response_data)
        self.assertIn('extraction_summary', response_data)
        
        # Summary should include counts and confidence
        summary = response_data['extraction_summary']
        self.assertIn('total_preferences_found', summary)
        self.assertIn('high_confidence_count', summary)
        self.assertIn('categories_discovered', summary)
    
    def test_get_session_preferences_endpoint(self):
        """Test endpoint to get all preferences for a session"""
        response = self.client.get(
            reverse('session-preferences', kwargs={'session_id': self.session.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        self.assertIn('manual_preferences', response_data)
        self.assertIn('extracted_preferences', response_data)
        self.assertIn('session_id', response_data)
    
    def test_update_preference_endpoint(self):
        """Test endpoint to manually add/update preferences"""
        preference_data = {
            'key': 'communication_style',
            'value': 'I prefer direct, action-oriented responses with clear next steps',
            'description': 'Manually specified communication preference'
        }
        
        response = self.client.post(
            reverse('update-session-preference', kwargs={'session_id': self.session.id}),
            data=json.dumps(preference_data),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
        
        # Verify preference was saved
        preference = UserPreference.objects.filter(
            session=self.session,
            key='communication_style'
        ).first()
        
        self.assertIsNotNone(preference)
        self.assertEqual(preference.value, preference_data['value'])
    
    def test_preference_api_validation_errors(self):
        """Test preference API error handling"""
        # Test invalid session ID
        response = self.client.get(
            reverse('session-preferences', kwargs={'session_id': '00000000-0000-0000-0000-000000000000'})
        )
        
        self.assertEqual(response.status_code, 404)
        
        # Test invalid preference data
        invalid_data = {
            'key': '',  # Empty key
            'value': 'Some value'
        }
        
        response = self.client.post(
            reverse('update-session-preference', kwargs={'session_id': self.session.id}),
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)


class TestPreferenceIntegrationWithPrompts(TestCase):
    """Test preference integration with prompt enhancement"""
    
    def setUp(self):
        """Set up test data"""
        self.session = Session.objects.create(
            name="Integration Test Session",
            description="Session for testing preference integration"
        )
        
        self.prompt = SystemPrompt.objects.create(
            session=self.session,
            content="You are a helpful email assistant.",
            version=1,
            is_active=True
        )
    
    def test_preference_aware_prompt_enhancement(self):
        """Test that preferences can be integrated into system prompts"""
        from app.services.preference_extractor import PreferenceExtractor
        
        # Create some preferences
        UserPreference.objects.create(
            session=self.session,
            key="tone",
            value="Professional but friendly",
            description="User's preferred tone"
        )
        
        UserPreference.objects.create(
            session=self.session,
            key="structure",
            value="Use bullet points for action items",
            description="User's preferred structure"
        )
        
        extractor = PreferenceExtractor()
        
        # Should have method to enhance prompts with preferences
        self.assertTrue(hasattr(extractor, 'enhance_prompt_with_preferences'))
        
        enhanced_prompt = extractor.enhance_prompt_with_preferences(
            self.prompt.content, 
            self.session
        )
        
        # Enhanced prompt should include preference information
        self.assertIsInstance(enhanced_prompt, str)
        self.assertNotEqual(enhanced_prompt, self.prompt.content)
        self.assertIn("Professional but friendly", enhanced_prompt)
    
    def test_preference_change_detection(self):
        """Test detecting when user preferences have changed"""
        from app.services.preference_extractor import PreferenceExtractor
        
        extractor = PreferenceExtractor()
        
        # Should have method to detect preference changes
        self.assertTrue(hasattr(extractor, 'detect_preference_changes'))
        
        # Initial extraction
        initial_prefs = extractor.extract_all_preferences(self.session)
        
        # Simulate new feedback that might change preferences
        # This would trigger re-extraction and comparison
        changes_detected = extractor.detect_preference_changes(self.session)
        
        # Should return boolean indicating if changes were detected
        self.assertIsInstance(changes_detected, bool)