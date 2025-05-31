"""
TDD Tests for Reasoning Models
Following TDD principles: Write failing tests first that define expected behavior
"""
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from core.models import Session, SystemPrompt, Email, Draft, UserFeedback


class TestDraftReasonModel(TestCase):
    """Test DraftReason model behavior - these tests will fail initially"""
    
    def setUp(self):
        """Set up test data"""
        self.session = Session.objects.create(
            name="Test Session",
            description="Test session for reasoning"
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
    
    def test_draft_reason_model_exists(self):
        """Test that DraftReason model can be imported"""
        # This will FAIL until we create the model
        from core.models import DraftReason
        self.assertTrue(DraftReason)
    
    def test_draft_reason_has_required_fields(self):
        """Test that DraftReason has all required fields"""
        from core.models import DraftReason
        
        # Create a reason (without draft - M2M relationship)
        reason = DraftReason(
            text="Used professional tone",
            confidence=0.85
        )
        reason.save()
        
        # Add to draft through M2M
        self.draft.reasons.add(reason)
        
        # Test field existence
        self.assertEqual(reason.text, "Used professional tone")
        self.assertEqual(reason.confidence, 0.85)
        self.assertIn(reason, self.draft.reasons.all())
    
    def test_draft_reason_string_representation(self):
        """Test the string representation of DraftReason"""
        from core.models import DraftReason
        
        reason = DraftReason(
            text="Used professional tone for business context",
            confidence=0.85
        )
        
        # Current implementation shows more characters
        expected = "Used professional tone for business context (0.85)"
        self.assertEqual(str(reason), expected)
    
    def test_draft_can_have_multiple_reasons(self):
        """Test that a draft can have multiple reasoning factors"""
        from core.models import DraftReason
        
        # Create multiple reasons
        reason1 = DraftReason.objects.create(
            text="Professional tone",
            confidence=0.85
        )
        
        reason2 = DraftReason.objects.create(
            text="Clear structure",
            confidence=0.90
        )
        
        reason3 = DraftReason.objects.create(
            text="Addressed all points",
            confidence=0.75
        )
        
        # Add to draft through M2M
        self.draft.reasons.add(reason1, reason2, reason3)
        
        # Test relationship
        self.assertEqual(self.draft.reasons.count(), 3)
        
        # DraftReason doesn't have ordering defined, so we can't test order
        # But we can verify all exist
        confidences = set(self.draft.reasons.values_list('confidence', flat=True))
        self.assertEqual(confidences, {0.75, 0.85, 0.90})
    
    def test_draft_reason_confidence_validation(self):
        """Test that confidence must be between 0 and 1"""
        from core.models import DraftReason
        
        # Test valid confidence
        valid_reason = DraftReason(
            text="Valid reason",
            confidence=0.5
        )
        valid_reason.full_clean()  # Should not raise
        
        # Test invalid confidence > 1
        with self.assertRaises(ValidationError):
            invalid_reason = DraftReason(
                text="Invalid reason",
                confidence=1.5
            )
            invalid_reason.full_clean()
        
        # Test invalid confidence < 0
        with self.assertRaises(ValidationError):
            invalid_reason = DraftReason(
                text="Invalid reason",
                confidence=-0.5
            )
            invalid_reason.full_clean()
    
    def test_draft_reason_cascade_delete(self):
        """Test that M2M relationship handles draft deletion properly"""
        from core.models import DraftReason
        
        # Create reason and add to draft
        reason = DraftReason.objects.create(
            text="Reason 1",
            confidence=0.8
        )
        self.draft.reasons.add(reason)
        
        reason_count_before = DraftReason.objects.count()
        self.assertEqual(reason_count_before, 1)
        
        # Delete draft
        self.draft.delete()
        
        # With M2M, reasons are NOT deleted, just the relationship
        reason_count_after = DraftReason.objects.count()
        self.assertEqual(reason_count_after, 1)  # Reason still exists


class TestReasonRatingModel(TestCase):
    """Test ReasonRating model behavior - these tests will fail initially"""
    
    def setUp(self):
        """Set up test data"""
        self.session = Session.objects.create(
            name="Test Session",
            description="Test session for ratings"
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
        
        # Create draft reason and add to draft via M2M
        from core.models import DraftReason
        self.reason = DraftReason.objects.create(
            text="Professional tone",
            confidence=0.85
        )
        self.draft.reasons.add(self.reason)
        
        self.feedback = UserFeedback.objects.create(
            draft=self.draft,
            action='accept'
        )
    
    def test_reason_rating_model_exists(self):
        """Test that ReasonRating model can be imported"""
        # This will FAIL until we create the model
        from core.models import ReasonRating
        self.assertTrue(ReasonRating)
    
    def test_reason_rating_has_required_fields(self):
        """Test that ReasonRating has all required fields"""
        from core.models import ReasonRating
        
        # Create a rating
        rating = ReasonRating(
            feedback=self.feedback,
            reason=self.reason,
            liked=True
        )
        
        # Test field existence
        self.assertEqual(rating.feedback, self.feedback)
        self.assertEqual(rating.reason, self.reason)
        self.assertTrue(rating.liked)
    
    def test_reason_rating_string_representation(self):
        """Test the string representation of ReasonRating"""
        from core.models import ReasonRating
        
        # Test liked rating
        liked_rating = ReasonRating(
            feedback=self.feedback,
            reason=self.reason,
            liked=True
        )
        self.assertEqual(str(liked_rating), "👍 Professional tone")
        
        # Test disliked rating
        disliked_rating = ReasonRating(
            feedback=self.feedback,
            reason=self.reason,
            liked=False
        )
        self.assertEqual(str(disliked_rating), "👎 Professional tone")
    
    def test_unique_constraint_per_feedback_reason_pair(self):
        """Test that each feedback can only rate each reason once"""
        from core.models import ReasonRating
        
        # Create first rating
        ReasonRating.objects.create(
            feedback=self.feedback,
            reason=self.reason,
            liked=True
        )
        
        # Try to create duplicate - should fail
        with self.assertRaises(Exception):  # IntegrityError
            ReasonRating.objects.create(
                feedback=self.feedback,
                reason=self.reason,
                liked=False  # Even with different value
            )
    
    def test_feedback_can_rate_multiple_reasons(self):
        """Test that one feedback can rate multiple reasons"""
        from core.models import DraftReason, ReasonRating
        
        # Create additional reasons
        reason2 = DraftReason.objects.create(
            text="Clear structure",
            confidence=0.90
        )
        
        reason3 = DraftReason.objects.create(
            text="Good examples",
            confidence=0.80
        )
        
        # Add to draft
        self.draft.reasons.add(reason2, reason3)
        
        # Rate all reasons
        ReasonRating.objects.create(
            feedback=self.feedback,
            reason=self.reason,
            liked=True
        )
        
        ReasonRating.objects.create(
            feedback=self.feedback,
            reason=reason2,
            liked=True
        )
        
        ReasonRating.objects.create(
            feedback=self.feedback,
            reason=reason3,
            liked=False
        )
        
        # Check counts
        self.assertEqual(self.feedback.reason_ratings.count(), 3)
        self.assertEqual(self.feedback.reason_ratings.filter(liked=True).count(), 2)
        self.assertEqual(self.feedback.reason_ratings.filter(liked=False).count(), 1)
    
    def test_reason_rating_cascade_delete(self):
        """Test cascade behavior when related objects are deleted"""
        from core.models import ReasonRating
        
        # Create rating
        rating = ReasonRating.objects.create(
            feedback=self.feedback,
            reason=self.reason,
            liked=True
        )
        
        # Delete feedback - rating should be deleted
        self.feedback.delete()
        self.assertEqual(ReasonRating.objects.filter(id=rating.id).count(), 0)
    
    def test_get_liked_reasons_for_feedback(self):
        """Test getting all liked reasons for a feedback"""
        from core.models import DraftReason, ReasonRating
        
        # Create more reasons and ratings
        reason2 = DraftReason.objects.create(
            text="Clear structure",
            confidence=0.90
        )
        self.draft.reasons.add(reason2)
        
        ReasonRating.objects.create(
            feedback=self.feedback,
            reason=self.reason,
            liked=True
        )
        
        ReasonRating.objects.create(
            feedback=self.feedback,
            reason=reason2,
            liked=False
        )
        
        # Get liked reasons through feedback
        liked_reasons = self.feedback.reason_ratings.filter(liked=True)
        self.assertEqual(liked_reasons.count(), 1)
        self.assertEqual(liked_reasons.first().reason.text, "Professional tone")