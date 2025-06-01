"""
TDD Tests for Reasoning Factor Quick Actions
Following TDD principles: Write failing tests first that define expected behavior
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from core.models import PromptLab, SystemPrompt, Email, Draft, DraftReason, UserFeedback, ReasonRating


class TestReasoningQuickActions(TestCase):
    """Test quick actions for reasoning factors - TDD approach"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test 
        self.prompt_lab = PromptLab.objects.create(
            name="Quick Actions Test PromptLab",
            description="Test session for quick actions"
        )
        
        self.prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="Test prompt",
            version=1,
            is_active=True
        )
        
        self.email = Email.objects.create(
            prompt_lab=self.prompt_lab,
            subject="Test Email",
            body="Test email body",
            sender="test@example.com"
        )
        
        self.draft = Draft.objects.create(
            email=self.email,
            content="Test draft response",
            system_prompt=self.prompt
        )
        
        # Create multiple draft reasons
        self.reason1 = DraftReason.objects.create(
            text="Professional tone maintained",
            confidence=0.85
        )
        self.reason2 = DraftReason.objects.create(
            text="Clear and concise structure",
            confidence=0.90
        )
        self.reason3 = DraftReason.objects.create(
            text="Addressed all key points",
            confidence=0.75
        )
        self.reason4 = DraftReason.objects.create(
            text="Appropriate level of detail",
            confidence=0.80
        )
        
        # Add reasons to draft
        self.draft.reasons.add(self.reason1, self.reason2, self.reason3, self.reason4)
    
    def test_bulk_accept_all_reasons_endpoint_exists(self):
        """Test that bulk accept all reasons endpoint exists"""
        # This will FAIL initially - endpoint doesn't exist yet
        
        response = self.client.post(
            reverse('bulk-accept-reasons', kwargs={
                'prompt_lab_id': self.prompt_lab.id,
                'draft_id': self.draft.id
            }),
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
    
    def test_bulk_accept_all_reasons_creates_feedback_and_ratings(self):
        """Test that bulk accept creates feedback with all reasons liked"""
        response = self.client.post(
            reverse('bulk-accept-reasons', kwargs={
                'prompt_lab_id': self.prompt_lab.id,
                'draft_id': self.draft.id
            }),
            data=json.dumps({
                'reason': 'All reasoning factors look good'
            }),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
        
        # Check that feedback was created
        feedback = UserFeedback.objects.filter(draft=self.draft).first()
        self.assertIsNotNone(feedback)
        self.assertEqual(feedback.action, 'accept')
        self.assertEqual(feedback.reason, 'All reasoning factors look good')
        
        # Check that all reasons were rated as liked
        ratings = feedback.reason_ratings.all()
        self.assertEqual(ratings.count(), 4)
        
        for rating in ratings:
            self.assertTrue(rating.liked)
        
        # Check response includes count
        response_data = response.json()
        self.assertEqual(response_data['reasons_rated'], 4)
        self.assertEqual(response_data['action'], 'bulk_accept')
    
    def test_bulk_reject_all_reasons_endpoint(self):
        """Test that bulk reject all reasons endpoint works"""
        response = self.client.post(
            reverse('bulk-reject-reasons', kwargs={
                'prompt_lab_id': self.prompt_lab.id,
                'draft_id': self.draft.id
            }),
            data=json.dumps({
                'reason': 'Reasoning approach needs improvement'
            }),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
        
        # Check that feedback was created with reject action
        feedback = UserFeedback.objects.filter(draft=self.draft).first()
        self.assertEqual(feedback.action, 'reject')
        
        # Check that all reasons were rated as disliked
        ratings = feedback.reason_ratings.all()
        self.assertEqual(ratings.count(), 4)
        
        for rating in ratings:
            self.assertFalse(rating.liked)
    
    def test_bulk_rate_selected_reasons(self):
        """Test bulk rating of specific selected reasons"""
        # This will FAIL initially - endpoint doesn't exist yet
        
        selected_reasons = {
            str(self.reason1.id): True,   # Like
            str(self.reason2.id): True,   # Like  
            str(self.reason3.id): False,  # Dislike
            # reason4 not included - should not be rated
        }
        
        response = self.client.post(
            reverse('bulk-rate-reasons', kwargs={
                'prompt_lab_id': self.prompt_lab.id,
                'draft_id': self.draft.id
            }),
            data=json.dumps({
                'action': 'accept',
                'reason': 'Mixed feedback on reasoning factors',
                'reason_ratings': selected_reasons
            }),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
        
        feedback = UserFeedback.objects.filter(draft=self.draft).first()
        self.assertEqual(feedback.action, 'accept')
        
        # Should have exactly 3 ratings (reason4 not included)
        ratings = feedback.reason_ratings.all()
        self.assertEqual(ratings.count(), 3)
        
        # Check specific ratings
        reason1_rating = ratings.get(reason=self.reason1)
        self.assertTrue(reason1_rating.liked)
        
        reason2_rating = ratings.get(reason=self.reason2)
        self.assertTrue(reason2_rating.liked)
        
        reason3_rating = ratings.get(reason=self.reason3)
        self.assertFalse(reason3_rating.liked)
        
        # reason4 should not have a rating
        reason4_ratings = ratings.filter(reason=self.reason4)
        self.assertEqual(reason4_ratings.count(), 0)
    
    def test_quick_thumbs_up_down_actions(self):
        """Test quick thumbs up/down for individual reasons"""
        # Test thumbs up
        response = self.client.post(
            reverse('quick-rate-reason', kwargs={
                'prompt_lab_id': self.prompt_lab.id,
                'reason_id': self.reason1.id
            }),
            data=json.dumps({
                'rating': 'thumbs_up',
                'draft_id': self.draft.id
            }),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
        
        # Should create or update feedback for this draft
        feedback = UserFeedback.objects.filter(draft=self.draft).first()
        self.assertIsNotNone(feedback)
        
        # Should have rating for this reason
        rating = feedback.reason_ratings.get(reason=self.reason1)
        self.assertTrue(rating.liked)
        
        # Test thumbs down on different reason
        response = self.client.post(
            reverse('quick-rate-reason', kwargs={
                'prompt_lab_id': self.prompt_lab.id,
                'reason_id': self.reason2.id
            }),
            data=json.dumps({
                'rating': 'thumbs_down',
                'draft_id': self.draft.id
            }),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
        
        # Should use same feedback and add another rating
        feedback.refresh_from_db()
        self.assertEqual(feedback.reason_ratings.count(), 2)
        
        reason2_rating = feedback.reason_ratings.get(reason=self.reason2)
        self.assertFalse(reason2_rating.liked)
    
    def test_quick_actions_validation_errors(self):
        """Test validation errors for quick actions"""
        # Test bulk accept with invalid draft
        response = self.client.post(
            reverse('bulk-accept-reasons', kwargs={
                'prompt_lab_id': self.prompt_lab.id,
                'draft_id': 99999
            }),
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        
        # Test quick rate with invalid reason
        response = self.client.post(
            reverse('quick-rate-reason', kwargs={
                'prompt_lab_id': self.prompt_lab.id,
                'reason_id': 99999
            }),
            data=json.dumps({
                'rating': 'thumbs_up',
                'draft_id': self.draft.id
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        
        # Test quick rate with invalid rating value
        response = self.client.post(
            reverse('quick-rate-reason', kwargs={
                'prompt_lab_id': self.prompt_lab.id,
                'reason_id': self.reason1.id
            }),
            data=json.dumps({
                'rating': 'invalid_rating',
                'draft_id': self.draft.id
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_quick_actions_cross_session_validation(self):
        """Test that quick actions validate  ownership"""
        # Create another  with different draft
        other_session = PromptLab.objects.create(name="Other PromptLab")
        other_email = Email.objects.create(
            prompt_lab=other_session,
            subject="Other Email",
            body="Other body",
            sender="other@example.com"
        )
        other_prompt = SystemPrompt.objects.create(
            prompt_lab=other_session,
            content="Other prompt",
            version=1
        )
        other_draft = Draft.objects.create(
            email=other_email,
            content="Other draft",
            system_prompt=other_prompt
        )
        
        # Try to bulk accept draft from different 
        response = self.client.post(
            reverse('bulk-accept-reasons', kwargs={
                'prompt_lab_id': self.prompt_lab.id,  # Wrong 
                'draft_id': other_draft.id
            }),
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_bulk_actions_preserve_existing_ratings(self):
        """Test that bulk actions work alongside existing individual ratings"""
        # Create some existing feedback with ratings
        existing_feedback = UserFeedback.objects.create(
            draft=self.draft,
            action='edit',
            reason='Initial feedback'
        )
        
        ReasonRating.objects.create(
            feedback=existing_feedback,
            reason=self.reason1,
            liked=True
        )
        
        # Now do bulk accept - should create new feedback, not modify existing
        response = self.client.post(
            reverse('bulk-accept-reasons', kwargs={
                'prompt_lab_id': self.prompt_lab.id,
                'draft_id': self.draft.id
            }),
            data=json.dumps({
                'reason': 'Bulk accept after individual rating'
            }),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
        
        # Should have 2 feedback items now
        feedbacks = UserFeedback.objects.filter(draft=self.draft)
        self.assertEqual(feedbacks.count(), 2)
        
        # Find the new bulk feedback
        bulk_feedback = feedbacks.get(action='accept')
        self.assertEqual(bulk_feedback.reason_ratings.count(), 4)
        
        # Original feedback should be unchanged
        existing_feedback.refresh_from_db()
        self.assertEqual(existing_feedback.reason_ratings.count(), 1)
    
    def test_bulk_actions_response_format(self):
        """Test that bulk actions return proper response format"""
        response = self.client.post(
            reverse('bulk-accept-reasons', kwargs={
                'prompt_lab_id': self.prompt_lab.id,
                'draft_id': self.draft.id
            }),
            data=json.dumps({
                'reason': 'Testing response format'
            }),
            content_type='application/json'
        )
        
        response_data = response.json()
        
        # Check required response fields
        self.assertIn('feedback_id', response_data)
        self.assertIn('action', response_data)
        self.assertIn('reasons_rated', response_data)
        self.assertIn('draft_id', response_data)
        
        self.assertEqual(response_data['action'], 'bulk_accept')
        self.assertEqual(response_data['reasons_rated'], 4)
        self.assertEqual(response_data['draft_id'], self.draft.id)