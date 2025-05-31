"""
Confidence Calculator Service
Calculates user and system confidence metrics for learning sessions
"""
import logging
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Q
from core.models import Session, SessionConfidence, UserFeedback, ReasonRating, Draft

logger = logging.getLogger(__name__)


class ConfidenceCalculator:
    """Service for calculating confidence metrics"""
    
    def __init__(self):
        self.logger = logger
    
    def calculate_user_confidence(self, session: Session) -> float:
        """
        Calculate user confidence based on feedback consistency and patterns
        
        User confidence increases when:
        - Feedback patterns are consistent over time
        - User provides detailed reasoning
        - User's feedback aligns with their previous patterns
        """
        try:
            # Get all feedback for this session
            feedbacks = UserFeedback.objects.filter(
                draft__email__session=session
            ).order_by('created_at')
            
            if feedbacks.count() < 2:
                # Not enough data for confidence calculation
                return 0.1
            
            # Calculate consistency score
            consistency_score = self._calculate_feedback_consistency(feedbacks)
            
            # Calculate feedback depth score (how detailed feedback is)
            depth_score = self._calculate_feedback_depth(feedbacks)
            
            # Calculate pattern alignment score
            pattern_score = self._calculate_pattern_alignment(feedbacks)
            
            # Weight the scores
            user_confidence = (
                consistency_score * 0.4 +
                depth_score * 0.3 +
                pattern_score * 0.3
            )
            
            # Ensure within bounds
            return max(0.0, min(1.0, user_confidence))
            
        except Exception as e:
            self.logger.error(f"Error calculating user confidence for session {session.id}: {str(e)}")
            return 0.0
    
    def calculate_system_confidence(self, session: Session) -> float:
        """
        Calculate system confidence based on reasoning alignment and prediction accuracy
        
        System confidence increases when:
        - Reasoning factors are consistently rated positively
        - System can predict user preferences accurately
        - Feedback patterns are learnable/modelable
        """
        try:
            # Get all drafts and their reasoning ratings for this session
            drafts = Draft.objects.filter(email__session=session)
            
            if drafts.count() == 0:
                return 0.1
            
            # Calculate reasoning alignment score
            reasoning_score = self._calculate_reasoning_alignment(session)
            
            # Calculate prediction accuracy (how well system predicts user actions)
            prediction_score = self._calculate_prediction_accuracy(session)
            
            # Calculate learning velocity (how quickly system improves)
            velocity_score = self._calculate_learning_velocity(session)
            
            # Weight the scores
            system_confidence = (
                reasoning_score * 0.5 +
                prediction_score * 0.3 +
                velocity_score * 0.2
            )
            
            # Ensure within bounds
            return max(0.0, min(1.0, system_confidence))
            
        except Exception as e:
            self.logger.error(f"Error calculating system confidence for session {session.id}: {str(e)}")
            return 0.0
    
    def _calculate_feedback_consistency(self, feedbacks) -> float:
        """Calculate how consistent user feedback patterns are"""
        if feedbacks.count() < 3:
            return 0.3  # Low confidence with limited data
        
        # Group feedback by action type
        action_counts = feedbacks.values('action').annotate(count=Count('action'))
        total_feedback = feedbacks.count()
        
        # Calculate entropy-like measure of consistency
        # More consistent patterns = higher confidence
        action_distribution = []
        for action_count in action_counts:
            proportion = action_count['count'] / total_feedback
            action_distribution.append(proportion)
        
        # If one action dominates (>60%), high consistency
        max_proportion = max(action_distribution) if action_distribution else 0
        if max_proportion > 0.6:
            return 0.8
        elif max_proportion > 0.4:
            return 0.6
        else:
            return 0.3  # Very mixed feedback = lower confidence
    
    def _calculate_feedback_depth(self, feedbacks) -> float:
        """Calculate how detailed/thoughtful user feedback is"""
        if feedbacks.count() == 0:
            return 0.0
        
        # Count feedback with reasons
        with_reasons = feedbacks.exclude(reason='').exclude(reason__isnull=True).count()
        reason_ratio = with_reasons / feedbacks.count()
        
        # Count feedback with reasoning factor ratings
        with_ratings = feedbacks.filter(reason_ratings__isnull=False).distinct().count()
        rating_ratio = with_ratings / feedbacks.count() if feedbacks.count() > 0 else 0
        
        # Calculate average reason length for non-empty reasons
        non_empty_reasons = feedbacks.exclude(reason='').exclude(reason__isnull=True)
        if non_empty_reasons.count() > 0:
            avg_reason_length = sum(len(f.reason) for f in non_empty_reasons) / non_empty_reasons.count()
            length_score = min(1.0, avg_reason_length / 50)  # Normalize to 50 chars
        else:
            length_score = 0.0
        
        # Combine metrics
        depth_score = (reason_ratio * 0.4 + rating_ratio * 0.4 + length_score * 0.2)
        return max(0.0, min(1.0, depth_score))
    
    def _calculate_pattern_alignment(self, feedbacks) -> float:
        """Calculate how well user's recent feedback aligns with their historical patterns"""
        if feedbacks.count() < 5:
            return 0.5  # Neutral score with limited data
        
        # Split into historical (first 80%) and recent (last 20%)
        total_count = feedbacks.count()
        split_point = int(total_count * 0.8)
        
        historical = feedbacks[:split_point]
        recent = feedbacks[split_point:]
        
        if recent.count() == 0:
            return 0.5
        
        # Calculate action distribution in both periods
        historical_actions = set(historical.values_list('action', flat=True))
        recent_actions = set(recent.values_list('action', flat=True))
        
        # Calculate overlap
        action_overlap = len(historical_actions.intersection(recent_actions))
        total_unique_actions = len(historical_actions.union(recent_actions))
        
        if total_unique_actions == 0:
            return 0.5
        
        alignment_score = action_overlap / total_unique_actions
        return max(0.3, min(1.0, alignment_score))
    
    def _calculate_reasoning_alignment(self, session: Session) -> float:
        """Calculate how well reasoning factors align with user preferences"""
        # Get all reason ratings for this session
        reason_ratings = ReasonRating.objects.filter(
            feedback__draft__email__session=session
        )
        
        if reason_ratings.count() == 0:
            return 0.3  # Low confidence without rating data
        
        # Calculate percentage of liked vs disliked ratings
        liked_count = reason_ratings.filter(liked=True).count()
        total_count = reason_ratings.count()
        
        like_ratio = liked_count / total_count
        
        # Higher like ratio = better alignment = higher confidence
        # Transform ratio to confidence score
        if like_ratio > 0.7:
            return 0.9
        elif like_ratio > 0.5:
            return 0.7
        elif like_ratio > 0.3:
            return 0.5
        else:
            return 0.3
    
    def _calculate_prediction_accuracy(self, session: Session) -> float:
        """Calculate how accurately system can predict user actions"""
        # This is a placeholder for future ML model predictions
        # For now, use reasoning alignment as proxy
        return self._calculate_reasoning_alignment(session)
    
    def _calculate_learning_velocity(self, session: Session) -> float:
        """Calculate how quickly the system is improving"""
        # Get feedback over time and look for improvement trends
        feedbacks = UserFeedback.objects.filter(
            draft__email__session=session
        ).order_by('created_at')
        
        if feedbacks.count() < 5:
            return 0.4  # Moderate score with limited data
        
        # Look at acceptance rate over time
        total_count = feedbacks.count()
        first_half = feedbacks[:total_count//2]
        second_half = feedbacks[total_count//2:]
        
        first_accept_rate = first_half.filter(action='accept').count() / first_half.count()
        second_accept_rate = second_half.filter(action='accept').count() / second_half.count()
        
        improvement = second_accept_rate - first_accept_rate
        
        # Convert improvement to confidence score
        if improvement > 0.2:
            return 0.9  # Strong improvement
        elif improvement > 0.1:
            return 0.7  # Moderate improvement
        elif improvement > -0.1:
            return 0.5  # Stable
        else:
            return 0.3  # Declining
    
    def is_user_confidence_sufficient(self, session: Session) -> bool:
        """Check if user confidence meets threshold"""
        confidence = self.calculate_user_confidence(session)
        return confidence >= SessionConfidence.USER_CONFIDENCE_THRESHOLD
    
    def is_system_confidence_sufficient(self, session: Session) -> bool:
        """Check if system confidence meets threshold"""
        confidence = self.calculate_system_confidence(session)
        return confidence >= SessionConfidence.SYSTEM_CONFIDENCE_THRESHOLD
    
    def should_continue_learning(self, session: Session) -> bool:
        """Determine if system should continue learning"""
        user_sufficient = self.is_user_confidence_sufficient(session)
        system_sufficient = self.is_system_confidence_sufficient(session)
        
        # Continue learning if either confidence is insufficient
        return not (user_sufficient and system_sufficient)
    
    def is_cold_start_complete(self, session: Session) -> bool:
        """Check if cold start phase is complete"""
        # Cold start is complete when we have sufficient feedback and reasonable confidence
        feedbacks = UserFeedback.objects.filter(draft__email__session=session)
        
        # Need minimum amount of feedback
        if feedbacks.count() < 5:
            return False
        
        # Need at least basic confidence levels
        user_conf = self.calculate_user_confidence(session)
        system_conf = self.calculate_system_confidence(session)
        
        # Lower thresholds for cold start completion
        return user_conf >= 0.4 and system_conf >= 0.4
    
    def update_session_confidence(self, session: Session) -> SessionConfidence:
        """Calculate and update confidence metrics for a session"""
        try:
            # Calculate metrics
            user_confidence = self.calculate_user_confidence(session)
            system_confidence = self.calculate_system_confidence(session)
            
            # Get or create confidence tracker
            confidence_tracker, created = SessionConfidence.objects.get_or_create(
                session=session,
                defaults={
                    'user_confidence': user_confidence,
                    'system_confidence': system_confidence,
                }
            )
            
            if not created:
                # Calculate trend
                old_combined = (confidence_tracker.user_confidence + confidence_tracker.system_confidence) / 2
                new_combined = (user_confidence + system_confidence) / 2
                confidence_trend = new_combined - old_combined
                
                # Update values
                confidence_tracker.user_confidence = user_confidence
                confidence_tracker.system_confidence = system_confidence
                confidence_tracker.confidence_trend = confidence_trend
            
            # Update detailed breakdown
            feedbacks = UserFeedback.objects.filter(draft__email__session=session)
            confidence_tracker.feedback_consistency_score = self._calculate_feedback_consistency(feedbacks)
            confidence_tracker.reasoning_alignment_score = self._calculate_reasoning_alignment(session)
            confidence_tracker.total_feedback_count = feedbacks.count()
            confidence_tracker.consistent_feedback_streak = self._calculate_consistency_streak(feedbacks)
            
            confidence_tracker.save()
            return confidence_tracker
            
        except Exception as e:
            self.logger.error(f"Error updating session confidence for {session.id}: {str(e)}")
            # Return default values if calculation fails
            confidence_tracker, _ = SessionConfidence.objects.get_or_create(
                session=session,
                defaults={'user_confidence': 0.1, 'system_confidence': 0.1}
            )
            return confidence_tracker
    
    def _calculate_consistency_streak(self, feedbacks) -> int:
        """Calculate current streak of consistent feedback"""
        if feedbacks.count() == 0:
            return 0
        
        # Look at last 5 feedback items
        recent_feedbacks = list(feedbacks.order_by('-created_at')[:5])
        
        if len(recent_feedbacks) < 2:
            return 0
        
        # Check if recent actions are similar
        recent_actions = [f.action for f in recent_feedbacks]
        
        # Count streak of same action from most recent
        streak = 1
        current_action = recent_actions[0]
        
        for action in recent_actions[1:]:
            if action == current_action:
                streak += 1
            else:
                break
        
        return streak