from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from core.models import UserFeedback, Draft, Email, SystemPrompt, ReasonRating
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from asgiref.sync import sync_to_async


@dataclass
class FeedbackSignal:
    """Processed feedback signal for RL training"""
    user_id: Optional[str]
    email_scenario: str
    action: str  # accept, reject, edit, ignore
    reward_value: float
    confidence: float
    reasoning: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UserPreferenceLearning:
    """Learning data about user preferences"""
    user_id: str
    preference_vector: Dict[str, float]
    confidence_scores: Dict[str, float]
    last_updated: datetime
    interaction_count: int


class FeedbackProcessor(ABC):
    """Abstract interface for processing different types of feedback"""
    
    @abstractmethod
    async def process_feedback(
        self,
        feedback: UserFeedback,
        context: Dict[str, Any]
    ) -> FeedbackSignal:
        """Process feedback into a standardized signal"""
        pass


class AcceptFeedbackProcessor(FeedbackProcessor):
    """Processes accept feedback signals"""
    
    async def process_feedback(
        self,
        feedback: UserFeedback,
        context: Dict[str, Any]
    ) -> FeedbackSignal:
        """Process accept feedback - strong positive signal"""
        
        # Base reward for acceptance
        base_reward = 1.0
        
        # Adjust based on reason ratings if available
        reason_ratings = []
        try:
            if hasattr(feedback, 'reason_ratings') and feedback.reason_ratings:
                # For mock objects, reason_ratings.all() should work directly
                reason_ratings = feedback.reason_ratings.all()
                if reason_ratings:
                    avg_rating = sum(1.0 if r.liked else 0.0 for r in reason_ratings) / len(reason_ratings)
                    # Boost reward if reasons were also liked
                    base_reward = min(1.2, base_reward + (avg_rating * 0.2))
        except Exception:
            # For real Django querysets, use sync_to_async
            try:
                if hasattr(feedback, 'reason_ratings') and feedback.reason_ratings:
                    reason_ratings = await sync_to_async(list)(feedback.reason_ratings.all())
                    if reason_ratings:
                        avg_rating = sum(1.0 if r.liked else 0.0 for r in reason_ratings) / len(reason_ratings)
                        base_reward = min(1.2, base_reward + (avg_rating * 0.2))
            except Exception:
                pass
        
        return FeedbackSignal(
            user_id=getattr(feedback, 'user_id', None),
            email_scenario=context.get('email_scenario', 'unknown'),
            action='accept',
            reward_value=base_reward,
            confidence=0.9,  # High confidence for explicit acceptance
            reasoning=feedback.reason,
            metadata={
                'draft_id': feedback.draft.id if feedback.draft else None,
                'reason_ratings_count': len(reason_ratings)
            }
        )


class RejectFeedbackProcessor(FeedbackProcessor):
    """Processes reject feedback signals"""
    
    async def process_feedback(
        self,
        feedback: UserFeedback,
        context: Dict[str, Any]
    ) -> FeedbackSignal:
        """Process reject feedback - strong negative signal"""
        
        # Base negative reward for rejection
        base_reward = 0.0
        
        # Extract learning from rejection reason
        reason_keywords = {
            'tone': ['tone', 'professional', 'casual', 'formal'],
            'length': ['long', 'short', 'brief', 'verbose', 'lengthy', 'concise'],
            'content': ['content', 'information', 'detail', 'complete'],
            'clarity': ['clear', 'confusing', 'unclear', 'ambiguous']
        }
        
        reason_categories = []
        if feedback.reason:
            reason_lower = feedback.reason.lower()
            for category, keywords in reason_keywords.items():
                if any(keyword in reason_lower for keyword in keywords):
                    reason_categories.append(category)
        
        return FeedbackSignal(
            user_id=getattr(feedback, 'user_id', None),
            email_scenario=context.get('email_scenario', 'unknown'),
            action='reject',
            reward_value=base_reward,
            confidence=0.95,  # Very high confidence for explicit rejection
            reasoning=feedback.reason,
            metadata={
                'draft_id': feedback.draft.id if feedback.draft else None,
                'reason_categories': reason_categories,
                'rejection_reason': feedback.reason
            }
        )


class EditFeedbackProcessor(FeedbackProcessor):
    """Processes edit feedback signals"""
    
    async def process_feedback(
        self,
        feedback: UserFeedback,
        context: Dict[str, Any]
    ) -> FeedbackSignal:
        """Process edit feedback - partial positive signal with learning opportunity"""
        
        # Base reward for edit (partial success)
        base_reward = 0.6
        
        # Analyze edit content to extract preferences
        edit_analysis = {}
        if feedback.edited_content and context.get('original_content'):
            edit_analysis = self._analyze_edit_changes(
                context['original_content'],
                feedback.edited_content
            )
            
            # Adjust reward based on edit magnitude
            if edit_analysis.get('edit_ratio', 1.0) < 0.3:
                # Small edit suggests mostly good content
                base_reward = 0.8
            elif edit_analysis.get('edit_ratio', 1.0) > 0.7:
                # Large edit suggests significant issues
                base_reward = 0.4
        
        return FeedbackSignal(
            user_id=getattr(feedback, 'user_id', None),
            email_scenario=context.get('email_scenario', 'unknown'),
            action='edit',
            reward_value=base_reward,
            confidence=0.7,  # Moderate confidence - need to learn from edit
            reasoning=feedback.reason,
            metadata={
                'draft_id': feedback.draft.id if feedback.draft else None,
                'edit_analysis': edit_analysis,
                'edited_content': feedback.edited_content
            }
        )
    
    def _analyze_edit_changes(self, original: str, edited: str) -> Dict[str, Any]:
        """Analyze what changed between original and edited content"""
        
        original_words = original.split()
        edited_words = edited.split()
        
        # Simple edit ratio calculation
        edit_ratio = 1.0 - (len(set(original_words) & set(edited_words)) / 
                           max(len(original_words), 1))
        
        length_change = len(edited_words) - len(original_words)
        
        return {
            'edit_ratio': edit_ratio,
            'length_change': length_change,
            'original_length': len(original_words),
            'edited_length': len(edited_words)
        }


class IgnoreFeedbackProcessor(FeedbackProcessor):
    """Processes ignore feedback signals"""
    
    async def process_feedback(
        self,
        feedback: UserFeedback,
        context: Dict[str, Any]
    ) -> FeedbackSignal:
        """Process ignore feedback - weak negative signal"""
        
        return FeedbackSignal(
            user_id=getattr(feedback, 'user_id', None),
            email_scenario=context.get('email_scenario', 'unknown'),
            action='ignore',
            reward_value=0.3,  # Slight negative signal
            confidence=0.4,   # Low confidence - could be various reasons
            reasoning=feedback.reason,
            metadata={
                'draft_id': feedback.draft.id if feedback.draft else None
            }
        )


class HumanFeedbackIntegrator:
    """Integrates human feedback into RL training signals and user preference learning"""
    
    def __init__(self):
        self.feedback_processors = {
            'accept': AcceptFeedbackProcessor(),
            'reject': RejectFeedbackProcessor(),
            'edit': EditFeedbackProcessor(),
            'ignore': IgnoreFeedbackProcessor()
        }
        
        self.user_preferences: Dict[str, UserPreferenceLearning] = {}
        self.feedback_history: List[FeedbackSignal] = []
        self.scenario_performance: Dict[str, List[float]] = {}
    
    async def process_user_feedback(
        self,
        feedback: UserFeedback,
        email: Email,
        draft: Optional[Draft] = None
    ) -> FeedbackSignal:
        """Process user feedback into RL training signal"""
        
        # Build context for feedback processing
        context = {
            'email_scenario': email.scenario_type,
            'email_id': email.id,
            'draft_id': draft.id if draft else None,
            'original_content': draft.content if draft else None
        }
        
        # Get appropriate processor
        processor = self.feedback_processors.get(
            feedback.action, 
            self.feedback_processors['ignore']
        )
        
        # Process feedback into signal
        signal = await processor.process_feedback(feedback, context)
        
        # Store signal for analysis
        self.feedback_history.append(signal)
        
        # Update user preferences if user identified
        if signal.user_id:
            await self._update_user_preferences(signal, feedback, email, draft)
        
        # Update scenario performance tracking
        self._update_scenario_performance(signal)
        
        return signal
    
    async def _update_user_preferences(
        self,
        signal: FeedbackSignal,
        feedback: UserFeedback,
        email: Email,
        draft: Optional[Draft]
    ):
        """Update learned user preferences based on feedback"""
        
        user_id = signal.user_id
        
        # Initialize user preferences if new user
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreferenceLearning(
                user_id=user_id,
                preference_vector={},
                confidence_scores={},
                last_updated=datetime.now(),
                interaction_count=0
            )
        
        user_prefs = self.user_preferences[user_id]
        user_prefs.interaction_count += 1
        user_prefs.last_updated = datetime.now()
        
        # Extract preferences from feedback
        if signal.action == 'accept':
            # Reinforce current prompt characteristics
            await self._reinforce_preferences(user_prefs, email, draft, 1.0)
        
        elif signal.action == 'reject':
            # Learn what to avoid
            await self._reinforce_preferences(user_prefs, email, draft, -0.5)
            
            # Extract specific dislikes from reason
            if feedback.reason:
                await self._extract_negative_preferences(user_prefs, feedback.reason)
        
        elif signal.action == 'edit':
            # Learn from the edit
            if feedback.edited_content and draft:
                await self._learn_from_edit(user_prefs, draft.content, feedback.edited_content)
    
    async def _reinforce_preferences(
        self,
        user_prefs: UserPreferenceLearning,
        email: Email,
        draft: Optional[Draft],
        strength: float
    ):
        """Reinforce or diminish preferences based on feedback"""
        
        # Extract features from email and draft
        features = self._extract_features(email, draft)
        
        learning_rate = 0.1
        
        for feature, value in features.items():
            current_pref = user_prefs.preference_vector.get(feature, 0.0)
            current_conf = user_prefs.confidence_scores.get(feature, 0.1)
            
            # Update preference
            new_pref = current_pref + (learning_rate * strength * value)
            user_prefs.preference_vector[feature] = max(-1.0, min(1.0, new_pref))
            
            # Update confidence
            user_prefs.confidence_scores[feature] = min(1.0, current_conf + 0.05)
    
    def _extract_features(
        self,
        email: Email,
        draft: Optional[Draft]
    ) -> Dict[str, float]:
        """Extract features from email and draft for preference learning"""
        
        features = {}
        
        # Email scenario feature
        features[f'scenario_{email.scenario_type}'] = 1.0
        
        if draft:
            # Length features
            word_count = len(draft.content.split())
            if word_count < 50:
                features['length_short'] = 1.0
            elif word_count > 150:
                features['length_long'] = 1.0
            else:
                features['length_medium'] = 1.0
            
            # Tone features (simple keyword-based)
            content_lower = draft.content.lower()
            
            if any(word in content_lower for word in ['please', 'thank you', 'appreciate']):
                features['tone_polite'] = 1.0
            
            if any(word in content_lower for word in ['immediately', 'urgent', 'asap']):
                features['tone_urgent'] = 1.0
            
            if any(word in content_lower for word in ['happy', 'glad', 'pleased']):
                features['tone_positive'] = 1.0
        
        return features
    
    async def _extract_negative_preferences(
        self,
        user_prefs: UserPreferenceLearning,
        reason: str
    ):
        """Extract negative preferences from rejection reason"""
        
        reason_lower = reason.lower()
        
        # Map reason keywords to preference features
        negative_mappings = {
            'too formal': ('tone_formal', -0.3),
            'too casual': ('tone_casual', -0.3),
            'too long': ('length_long', -0.4),
            'too short': ('length_short', -0.4),
            'unclear': ('clarity_low', -0.5),
            'inappropriate': ('appropriateness_low', -0.6)
        }
        
        for phrase, (feature, penalty) in negative_mappings.items():
            if phrase in reason_lower:
                current = user_prefs.preference_vector.get(feature, 0.0)
                user_prefs.preference_vector[feature] = max(-1.0, current + penalty)
    
    async def _learn_from_edit(
        self,
        user_prefs: UserPreferenceLearning,
        original_content: str,
        edited_content: str
    ):
        """Learn preferences from user edits"""
        
        # Analyze edit patterns
        original_words = original_content.split()
        edited_words = edited_content.split()
        
        length_change = len(edited_words) - len(original_words)
        
        # Learn length preferences
        if length_change > 5:
            # User prefers longer responses
            current = user_prefs.preference_vector.get('length_preference', 0.0)
            user_prefs.preference_vector['length_preference'] = min(1.0, current + 0.1)
        elif length_change < -5:
            # User prefers shorter responses
            current = user_prefs.preference_vector.get('length_preference', 0.0)
            user_prefs.preference_vector['length_preference'] = max(-1.0, current - 0.1)
    
    def _update_scenario_performance(self, signal: FeedbackSignal):
        """Update performance tracking for scenarios"""
        
        scenario = signal.email_scenario
        
        if scenario not in self.scenario_performance:
            self.scenario_performance[scenario] = []
        
        self.scenario_performance[scenario].append(signal.reward_value)
        
        # Keep only recent performance (last 50 signals)
        self.scenario_performance[scenario] = self.scenario_performance[scenario][-50:]
    
    async def get_user_preferences(
        self,
        user_id: str
    ) -> Optional[Dict[str, float]]:
        """Get learned preferences for a user"""
        
        if user_id not in self.user_preferences:
            return None
        
        return self.user_preferences[user_id].preference_vector.copy()
    
    async def get_feedback_batch_for_training(
        self,
        min_confidence: float = 0.5,
        max_age_hours: int = 24,
        max_signals: int = 100
    ) -> List[FeedbackSignal]:
        """Get batch of feedback signals for RL training"""
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Filter signals by confidence and recency
        filtered_signals = [
            signal for signal in self.feedback_history
            if signal.confidence >= min_confidence
        ]
        
        # Return most recent signals up to max_signals
        return filtered_signals[-max_signals:]
    
    async def get_scenario_performance_summary(self) -> Dict[str, Dict[str, float]]:
        """Get performance summary by scenario"""
        
        summary = {}
        
        for scenario, performances in self.scenario_performance.items():
            if not performances:
                continue
            
            summary[scenario] = {
                'average_reward': sum(performances) / len(performances),
                'recent_average': sum(performances[-10:]) / min(len(performances), 10),
                'total_feedback': len(performances),
                'trend': self._calculate_trend(performances)
            }
        
        return summary
    
    def _calculate_trend(self, performances: List[float]) -> str:
        """Calculate performance trend"""
        
        if len(performances) < 10:
            return 'insufficient_data'
        
        recent_avg = sum(performances[-5:]) / 5
        older_avg = sum(performances[-10:-5]) / 5
        
        if recent_avg > older_avg + 0.1:
            return 'improving'
        elif recent_avg < older_avg - 0.1:
            return 'declining'
        else:
            return 'stable'
    
    async def get_integration_metrics(self) -> Dict[str, Any]:
        """Get metrics about feedback integration"""
        
        total_signals = len(self.feedback_history)
        
        if total_signals == 0:
            return {"total_signals": 0}
        
        # Calculate signal distribution
        action_counts = {}
        confidence_sum = 0
        
        for signal in self.feedback_history:
            action_counts[signal.action] = action_counts.get(signal.action, 0) + 1
            confidence_sum += signal.confidence
        
        return {
            "total_signals": total_signals,
            "action_distribution": action_counts,
            "average_confidence": confidence_sum / total_signals,
            "unique_users": len(self.user_preferences),
            "scenarios_tracked": len(self.scenario_performance),
            "recent_signals_24h": len([
                s for s in self.feedback_history
                if hasattr(s, 'timestamp') and 
                s.timestamp > datetime.now() - timedelta(hours=24)
            ])
        }