"""
TDD Tests for Session Detail with Reasoning Factor Support
Following TDD principles: Write failing tests first that define expected behavior
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from core.models import Session, SystemPrompt, Email, Draft, DraftReason, UserFeedback, ReasonRating


class TestSessionDetailWithReasoningFactors(TestCase):
    """Test session detail includes reasoning factor information - TDD approach"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test session
        self.session = Session.objects.create(
            name="Test Session with Reasoning",
            description="Test session for reasoning detail API"
        )
        
        self.prompt = SystemPrompt.objects.create(
            session=self.session,
            content="Test prompt",
            version=1,
            is_active=True
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
        
        # Add reasons to draft
        self.draft.reasons.add(self.reason1, self.reason2, self.reason3)
        
        # Create feedback with ratings
        self.feedback = UserFeedback.objects.create(
            draft=self.draft,
            action='accept',
            reason='Good response overall'
        )
        
        # Create reason ratings
        ReasonRating.objects.create(
            feedback=self.feedback,
            reason=self.reason1,
            liked=True
        )
        ReasonRating.objects.create(
            feedback=self.feedback,
            reason=self.reason2,
            liked=True
        )
        ReasonRating.objects.create(
            feedback=self.feedback,
            reason=self.reason3,
            liked=False
        )
    
    def test_session_detail_includes_reasoning_summary(self):
        """Test that session detail includes reasoning factor summary"""
        # This test will FAIL initially - endpoint doesn't include reasoning data yet
        
        response = self.client.get(
            reverse('session-detail', kwargs={'session_id': self.session.id})
        )
        
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        
        # Check that reasoning summary is included
        self.assertIn('reasoning_summary', response_data)
        
        reasoning_summary = response_data['reasoning_summary']
        self.assertIn('total_reasons_generated', reasoning_summary)
        self.assertIn('total_reason_ratings', reasoning_summary)
        self.assertIn('reason_rating_breakdown', reasoning_summary)
        self.assertIn('most_liked_reasons', reasoning_summary)
        self.assertIn('least_liked_reasons', reasoning_summary)
    
    def test_session_detail_reasoning_summary_calculations(self):
        """Test that reasoning summary calculations are correct"""
        response = self.client.get(
            reverse('session-detail', kwargs={'session_id': self.session.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        reasoning_summary = response_data['reasoning_summary']
        
        # Should have 3 total reasons
        self.assertEqual(reasoning_summary['total_reasons_generated'], 3)
        
        # Should have 3 total ratings
        self.assertEqual(reasoning_summary['total_reason_ratings'], 3)
        
        # Rating breakdown should show 2 liked, 1 disliked
        breakdown = reasoning_summary['reason_rating_breakdown']
        self.assertEqual(breakdown['liked'], 2)
        self.assertEqual(breakdown['disliked'], 1)
        self.assertEqual(breakdown['total'], 3)
    
    def test_session_detail_most_liked_reasons(self):
        """Test that most liked reasons are correctly identified"""
        response = self.client.get(
            reverse('session-detail', kwargs={'session_id': self.session.id})
        )
        
        response_data = response.json()
        reasoning_summary = response_data['reasoning_summary']
        
        most_liked = reasoning_summary['most_liked_reasons']
        
        # Should return top 3 most liked reasons
        self.assertEqual(len(most_liked), 2)  # Only 2 are liked
        
        # Should include reason text and like count
        first_reason = most_liked[0]
        self.assertIn('text', first_reason)
        self.assertIn('like_count', first_reason)
        self.assertIn('dislike_count', first_reason)
        self.assertIn('confidence', first_reason)
        
        # Verify the liked reasons are included
        liked_texts = [reason['text'] for reason in most_liked]
        self.assertIn("Professional tone maintained", liked_texts)
        self.assertIn("Clear and concise structure", liked_texts)
    
    def test_session_detail_least_liked_reasons(self):
        """Test that least liked reasons are correctly identified"""
        response = self.client.get(
            reverse('session-detail', kwargs={'session_id': self.session.id})
        )
        
        response_data = response.json()
        reasoning_summary = response_data['reasoning_summary']
        
        least_liked = reasoning_summary['least_liked_reasons']
        
        # Should return reasons with dislikes
        self.assertEqual(len(least_liked), 1)  # Only 1 is disliked
        
        disliked_reason = least_liked[0]
        self.assertEqual(disliked_reason['text'], "Addressed all key points")
        self.assertEqual(disliked_reason['dislike_count'], 1)
        self.assertEqual(disliked_reason['like_count'], 0)
    
    def test_session_detail_empty_reasoning_data(self):
        """Test session detail with no reasoning data"""
        # Create a session with no drafts/reasoning
        empty_session = Session.objects.create(
            name="Empty Session",
            description="Session with no reasoning data"
        )
        
        SystemPrompt.objects.create(
            session=empty_session,
            content="Empty prompt",
            version=1,
            is_active=True
        )
        
        response = self.client.get(
            reverse('session-detail', kwargs={'session_id': empty_session.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Should still include reasoning summary with zero values
        reasoning_summary = response_data['reasoning_summary']
        self.assertEqual(reasoning_summary['total_reasons_generated'], 0)
        self.assertEqual(reasoning_summary['total_reason_ratings'], 0)
        self.assertEqual(reasoning_summary['most_liked_reasons'], [])
        self.assertEqual(reasoning_summary['least_liked_reasons'], [])
    
    def test_session_detail_with_multiple_drafts_and_reasons(self):
        """Test reasoning summary across multiple drafts and emails"""
        # Create another email and draft with different reasons
        email2 = Email.objects.create(
            session=self.session,
            subject="Second Test Email",
            body="Second email body",
            sender="test2@example.com"
        )
        
        draft2 = Draft.objects.create(
            email=email2,
            content="Second draft response",
            system_prompt=self.prompt
        )
        
        # Create different reasons for second draft
        reason4 = DraftReason.objects.create(
            text="Empathetic communication",
            confidence=0.80
        )
        reason5 = DraftReason.objects.create(
            text="Action-oriented response",
            confidence=0.95
        )
        
        draft2.reasons.add(reason4, reason5)
        
        # Create feedback for second draft
        feedback2 = UserFeedback.objects.create(
            draft=draft2,
            action='edit',
            reason='Mostly good but needs tweaks'
        )
        
        ReasonRating.objects.create(
            feedback=feedback2,
            reason=reason4,
            liked=True
        )
        ReasonRating.objects.create(
            feedback=feedback2,
            reason=reason5,
            liked=True
        )
        
        response = self.client.get(
            reverse('session-detail', kwargs={'session_id': self.session.id})
        )
        
        response_data = response.json()
        reasoning_summary = response_data['reasoning_summary']
        
        # Should aggregate across all drafts in session
        self.assertEqual(reasoning_summary['total_reasons_generated'], 5)  # 3 + 2
        self.assertEqual(reasoning_summary['total_reason_ratings'], 5)  # 3 + 2
        
        # Rating breakdown should show 4 liked, 1 disliked
        breakdown = reasoning_summary['reason_rating_breakdown']
        self.assertEqual(breakdown['liked'], 4)
        self.assertEqual(breakdown['disliked'], 1)


class TestDraftReasoningDetailEndpoint(TestCase):
    """Test dedicated endpoint for getting reasoning factors for a specific draft"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.session = Session.objects.create(
            name="Draft Reasoning Test",
            description="Test draft reasoning endpoint"
        )
        
        self.prompt = SystemPrompt.objects.create(
            session=self.session,
            content="Test prompt",
            version=1,
            is_active=True
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
        
        # Create reasons
        self.reason1 = DraftReason.objects.create(
            text="Professional tone",
            confidence=0.85
        )
        self.reason2 = DraftReason.objects.create(
            text="Clear structure",
            confidence=0.90
        )
        
        self.draft.reasons.add(self.reason1, self.reason2)
    
    def test_draft_reasoning_endpoint_exists(self):
        """Test that draft reasoning endpoint can be accessed"""
        # This will FAIL initially - endpoint doesn't exist yet
        
        response = self.client.get(
            reverse('draft-reasoning-factors', kwargs={
                'session_id': self.session.id,
                'draft_id': self.draft.id
            })
        )
        
        self.assertEqual(response.status_code, 200)
    
    def test_draft_reasoning_returns_factors(self):
        """Test that endpoint returns reasoning factors for draft"""
        response = self.client.get(
            reverse('draft-reasoning-factors', kwargs={
                'session_id': self.session.id,
                'draft_id': self.draft.id
            })
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        self.assertIn('draft_id', response_data)
        self.assertIn('reasoning_factors', response_data)
        
        factors = response_data['reasoning_factors']
        self.assertEqual(len(factors), 2)
        
        # Check factor structure
        factor = factors[0]
        self.assertIn('id', factor)
        self.assertIn('text', factor)
        self.assertIn('confidence', factor)
        self.assertIn('rating_stats', factor)
    
    def test_draft_reasoning_includes_rating_stats(self):
        """Test that reasoning factors include rating statistics"""
        # Create some ratings
        feedback = UserFeedback.objects.create(
            draft=self.draft,
            action='accept'
        )
        
        ReasonRating.objects.create(
            feedback=feedback,
            reason=self.reason1,
            liked=True
        )
        
        response = self.client.get(
            reverse('draft-reasoning-factors', kwargs={
                'session_id': self.session.id,
                'draft_id': self.draft.id
            })
        )
        
        response_data = response.json()
        factors = response_data['reasoning_factors']
        
        # Find the rated factor
        rated_factor = next(f for f in factors if f['id'] == self.reason1.id)
        
        rating_stats = rated_factor['rating_stats']
        self.assertEqual(rating_stats['likes'], 1)
        self.assertEqual(rating_stats['dislikes'], 0)
        self.assertEqual(rating_stats['total_ratings'], 1)
    
    def test_draft_reasoning_nonexistent_draft(self):
        """Test error handling for nonexistent draft"""
        response = self.client.get(
            reverse('draft-reasoning-factors', kwargs={
                'session_id': self.session.id,
                'draft_id': 99999
            })
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_draft_reasoning_wrong_session(self):
        """Test error handling when draft doesn't belong to session"""
        # Create draft in different session
        other_session = Session.objects.create(name="Other Session")
        other_email = Email.objects.create(
            session=other_session,
            subject="Other Email",
            body="Other body",
            sender="other@example.com"
        )
        other_prompt = SystemPrompt.objects.create(
            session=other_session,
            content="Other prompt",
            version=1
        )
        other_draft = Draft.objects.create(
            email=other_email,
            content="Other draft",
            system_prompt=other_prompt
        )
        
        response = self.client.get(
            reverse('draft-reasoning-factors', kwargs={
                'session_id': self.session.id,
                'draft_id': other_draft.id
            })
        )
        
        self.assertEqual(response.status_code, 404)