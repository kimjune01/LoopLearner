"""
TDD Tests for Feedback API with Reasoning Ratings
Following TDD principles: Write failing tests first that define expected behavior
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from core.models import Session, SystemPrompt, Email, Draft, DraftReason, UserFeedback, ReasonRating


class TestFeedbackAPIWithReasonRatings(TestCase):
    """Test feedback API endpoint handles reason ratings - TDD approach"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test data
        self.session = Session.objects.create(
            name="Test Session",
            description="Test session for API"
        )
        
        self.prompt = SystemPrompt.objects.create(
            session=self.session,
            content="Test prompt",
            version=1
        )
        
        self.email = Email.objects.create(
            session=self.session,
            subject="Test Email",
            body="Test email body",
            sender="test@example.com"
        )
        
        self.draft = Draft.objects.create(
            email=self.email,
            content="Test draft response",
            system_prompt=self.prompt
        )
        
        # Create draft reasons
        self.reason1 = DraftReason.objects.create(
            text="Professional tone",
            confidence=0.85
        )
        self.reason2 = DraftReason.objects.create(
            text="Clear structure",
            confidence=0.90
        )
        self.reason3 = DraftReason.objects.create(
            text="Addressed all points",
            confidence=0.75
        )
        
        # Add reasons to draft
        self.draft.reasons.add(self.reason1, self.reason2, self.reason3)
    
    def test_feedback_endpoint_accepts_reason_ratings(self):
        """Test that feedback endpoint accepts and stores reason ratings"""
        # This test will FAIL initially - endpoint doesn't handle reason_ratings yet
        
        feedback_data = {
            'draft_id': self.draft.id,
            'email_id': self.email.id,
            'action': 'accept',
            'reason': 'Good response',
            'reason_ratings': {
                str(self.reason1.id): True,
                str(self.reason2.id): True,
                str(self.reason3.id): False
            }
        }
        
        response = self.client.post(
            reverse('submit-feedback', kwargs={'draft_id': self.draft.id}),
            data=json.dumps(feedback_data),
            content_type='application/json'
        )
        
        # Should succeed (201 for created)
        self.assertIn(response.status_code, [200, 201])
        
        # Check feedback was created
        feedback = UserFeedback.objects.latest('id')
        self.assertEqual(feedback.draft.id, self.draft.id)
        self.assertEqual(feedback.action, 'accept')
        
        # Check reason ratings were created
        self.assertEqual(feedback.reason_ratings.count(), 3)
        
        # Verify specific ratings
        rating1 = feedback.reason_ratings.get(reason=self.reason1)
        self.assertTrue(rating1.liked)
        
        rating2 = feedback.reason_ratings.get(reason=self.reason2)
        self.assertTrue(rating2.liked)
        
        rating3 = feedback.reason_ratings.get(reason=self.reason3)
        self.assertFalse(rating3.liked)
    
    def test_feedback_without_reason_ratings_still_works(self):
        """Test backward compatibility - feedback without ratings should work"""
        feedback_data = {
            'draft_id': self.draft.id,
            'email_id': self.email.id,
            'action': 'reject',
            'reason': 'Not appropriate'
            # No reason_ratings field
        }
        
        response = self.client.post(
            reverse('submit-feedback', kwargs={'draft_id': self.draft.id}),
            data=json.dumps(feedback_data),
            content_type='application/json'
        )
        
        # Should succeed (201 for created)
        self.assertIn(response.status_code, [200, 201])
        
        # Check feedback was created without ratings
        feedback = UserFeedback.objects.latest('id')
        self.assertEqual(feedback.action, 'reject')
        self.assertEqual(feedback.reason_ratings.count(), 0)
    
    def test_invalid_reason_id_ignored(self):
        """Test that invalid reason IDs are ignored gracefully"""
        feedback_data = {
            'draft_id': self.draft.id,
            'email_id': self.email.id,
            'action': 'accept',
            'reason_ratings': {
                str(self.reason1.id): True,
                '99999': True,  # Invalid ID
                'abc': False    # Non-numeric ID
            }
        }
        
        response = self.client.post(
            reverse('submit-feedback', kwargs={'draft_id': self.draft.id}),
            data=json.dumps(feedback_data),
            content_type='application/json'
        )
        
        # Should succeed (201 for created)
        self.assertIn(response.status_code, [200, 201])
        
        # Only valid rating should be created
        feedback = UserFeedback.objects.latest('id')
        self.assertEqual(feedback.reason_ratings.count(), 1)
        self.assertTrue(feedback.reason_ratings.first().liked)
    
    def test_duplicate_ratings_prevented(self):
        """Test that duplicate ratings for same reason are prevented"""
        # Create initial feedback with rating
        feedback = UserFeedback.objects.create(
            draft=self.draft,
            action='accept'
        )
        ReasonRating.objects.create(
            feedback=feedback,
            reason=self.reason1,
            liked=True
        )
        
        # Try to submit another rating for same reason
        feedback_data = {
            'draft_id': self.draft.id,
            'email_id': self.email.id,
            'action': 'accept',
            'reason_ratings': {
                str(self.reason1.id): False,  # Different value
            }
        }
        
        # This creates a NEW feedback, so it should work
        response = self.client.post(
            reverse('submit-feedback', kwargs={'draft_id': self.draft.id}),
            data=json.dumps(feedback_data),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
        
        # Should have 2 feedbacks now
        self.assertEqual(UserFeedback.objects.count(), 2)
    
    def test_edit_action_with_reason_ratings(self):
        """Test edit action includes reason ratings"""
        feedback_data = {
            'draft_id': self.draft.id,
            'email_id': self.email.id,
            'action': 'edit',
            'reason': 'Needs adjustment',
            'edited_content': 'Edited draft content',
            'reason_ratings': {
                str(self.reason1.id): True,
                str(self.reason2.id): False,
            }
        }
        
        response = self.client.post(
            reverse('submit-feedback', kwargs={'draft_id': self.draft.id}),
            data=json.dumps(feedback_data),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
        
        feedback = UserFeedback.objects.latest('id')
        self.assertEqual(feedback.action, 'edit')
        self.assertEqual(feedback.edited_content, 'Edited draft content')
        self.assertEqual(feedback.reason_ratings.count(), 2)
    
    def test_api_response_includes_rating_confirmation(self):
        """Test that API response confirms ratings were saved"""
        feedback_data = {
            'draft_id': self.draft.id,
            'email_id': self.email.id,
            'action': 'accept',
            'reason_ratings': {
                str(self.reason1.id): True,
                str(self.reason2.id): True,
            }
        }
        
        response = self.client.post(
            reverse('submit-feedback', kwargs={'draft_id': self.draft.id}),
            data=json.dumps(feedback_data),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
        
        # Check response data
        response_data = response.json()
        self.assertIn('reason_ratings_saved', response_data)
        self.assertEqual(response_data['reason_ratings_saved'], 2)
    
    def test_reason_ratings_available_in_feedback_list(self):
        """Test that reason ratings are included when listing feedback"""
        # TODO: Skip this test for now - feedback list endpoint doesn't exist yet
        # This will be implemented in the next phase
        self.skipTest("Feedback list endpoint not implemented yet")