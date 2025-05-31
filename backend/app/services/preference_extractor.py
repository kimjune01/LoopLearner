"""
Preference Extractor Service
Extracts user preferences from feedback patterns and text analysis
"""
import logging
import re
from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict
from django.db.models import Count, Q
from core.models import Session, UserFeedback, ReasonRating, DraftReason, UserPreference, ExtractedPreference

logger = logging.getLogger(__name__)


class PreferenceExtractor:
    """Service for extracting user preferences from feedback patterns"""
    
    # Preference categories and their keywords
    PREFERENCE_CATEGORIES = {
        'tone': ['professional', 'casual', 'friendly', 'formal', 'warm', 'direct', 'polite', 'respectful'],
        'length': ['concise', 'brief', 'short', 'detailed', 'comprehensive', 'lengthy', 'verbose', 'terse'],
        'structure': ['bullet points', 'numbered', 'paragraphs', 'sections', 'organized', 'structured'],
        'vocabulary': ['technical', 'simple', 'jargon', 'plain language', 'complex', 'accessible'],
        'style': ['personal', 'business', 'academic', 'conversational', 'authoritative'],
        'content': ['examples', 'details', 'context', 'background', 'specifics', 'general']
    }
    
    # Common preference patterns
    PREFERENCE_PATTERNS = [
        (r'(?:i prefer|i like|i want|i need)\s+([^.!?]+)', 'positive'),
        (r'(?:too|overly)\s+(\w+)', 'negative'),
        (r'(?:not enough|need more|should have more)\s+([^.!?]+)', 'more_of'),
        (r'(?:don\'t|do not|avoid|stop)\s+([^.!?]+)', 'avoid'),
        (r'(?:should be|needs to be|must be)\s+([^.!?]+)', 'requirement'),
    ]
    
    def __init__(self):
        self.logger = logger
    
    def extract_from_feedback_text(self, session: Session) -> List[Dict[str, Any]]:
        """Extract preferences from user feedback reason text"""
        try:
            # Get all feedback with reasons for this session
            feedbacks = UserFeedback.objects.filter(
                draft__email__session=session
            ).exclude(reason='').exclude(reason__isnull=True)
            
            extracted_preferences = []
            
            for feedback in feedbacks:
                preferences = self._analyze_feedback_text(feedback.reason, feedback.id)
                extracted_preferences.extend(preferences)
            
            # Consolidate similar preferences
            consolidated = self._consolidate_text_preferences(extracted_preferences)
            
            return consolidated
            
        except Exception as e:
            self.logger.error(f"Error extracting preferences from feedback text: {str(e)}")
            return []
    
    def extract_from_reasoning_patterns(self, session: Session) -> List[Dict[str, Any]]:
        """Extract preferences from reasoning factor rating patterns"""
        try:
            # Get all reason ratings for this session
            ratings = ReasonRating.objects.filter(
                feedback__draft__email__session=session
            ).select_related('reason')
            
            if not ratings.exists():
                return []
            
            # Analyze patterns in liked vs disliked reasoning factors
            liked_reasons = defaultdict(int)
            disliked_reasons = defaultdict(int)
            total_ratings = defaultdict(int)
            
            for rating in ratings:
                reason_text = rating.reason.text.lower()
                total_ratings[reason_text] += 1
                
                if rating.liked:
                    liked_reasons[reason_text] += 1
                else:
                    disliked_reasons[reason_text] += 1
            
            preferences = []
            
            # Extract preferences from consistently liked reasoning factors
            for reason_text, like_count in liked_reasons.items():
                total = total_ratings[reason_text]
                like_ratio = like_count / total if total > 0 else 0
                
                if like_ratio >= 0.7 and total >= 2:  # At least 70% like rate, minimum 2 ratings
                    preference = self._extract_preference_from_reasoning(
                        reason_text, like_ratio, like_count, total, 'liked'
                    )
                    if preference:
                        preferences.append(preference)
            
            # Extract preferences from consistently disliked reasoning factors
            for reason_text, dislike_count in disliked_reasons.items():
                total = total_ratings[reason_text]
                dislike_ratio = dislike_count / total if total > 0 else 0
                
                if dislike_ratio >= 0.7 and total >= 2:  # At least 70% dislike rate
                    preference = self._extract_preference_from_reasoning(
                        reason_text, dislike_ratio, dislike_count, total, 'disliked'
                    )
                    if preference:
                        preferences.append(preference)
            
            return preferences
            
        except Exception as e:
            self.logger.error(f"Error extracting preferences from reasoning patterns: {str(e)}")
            return []
    
    def extract_from_action_patterns(self, session: Session) -> List[Dict[str, Any]]:
        """Extract preferences from user action patterns"""
        try:
            feedbacks = UserFeedback.objects.filter(
                draft__email__session=session
            )
            
            if feedbacks.count() < 3:
                return []  # Need minimum feedback to detect patterns
            
            # Analyze action patterns
            action_counts = feedbacks.values('action').annotate(count=Count('action'))
            total_feedback = feedbacks.count()
            
            preferences = []
            
            # High acceptance rate pattern
            accept_count = feedbacks.filter(action='accept').count()
            accept_rate = accept_count / total_feedback
            
            if accept_rate >= 0.8:
                preferences.append({
                    'category': 'general',
                    'text': 'User generally approves of the current response style and approach',
                    'confidence': min(0.9, accept_rate),
                    'sources': ['action_pattern_analysis'],
                    'evidence': f'{accept_rate:.1%} acceptance rate ({accept_count}/{total_feedback} responses accepted)'
                })
            
            # High rejection rate pattern
            reject_count = feedbacks.filter(action='reject').count()
            reject_rate = reject_count / total_feedback
            
            if reject_rate >= 0.6:
                preferences.append({
                    'category': 'general',
                    'text': 'User frequently rejects responses, indicating need for significant style changes',
                    'confidence': min(0.8, reject_rate),
                    'sources': ['action_pattern_analysis'],
                    'evidence': f'{reject_rate:.1%} rejection rate ({reject_count}/{total_feedback} responses rejected)'
                })
            
            # High edit rate pattern
            edit_count = feedbacks.filter(action='edit').count()
            edit_rate = edit_count / total_feedback
            
            if edit_rate >= 0.5:
                preferences.append({
                    'category': 'general',
                    'text': 'User frequently edits responses, indicating preferences for modified approach',
                    'confidence': min(0.7, edit_rate),
                    'sources': ['action_pattern_analysis'],
                    'evidence': f'{edit_rate:.1%} edit rate ({edit_count}/{total_feedback} responses edited)'
                })
            
            return preferences
            
        except Exception as e:
            self.logger.error(f"Error extracting preferences from action patterns: {str(e)}")
            return []
    
    def extract_all_preferences(self, session: Session) -> List[Dict[str, Any]]:
        """Extract and consolidate preferences from all sources"""
        try:
            all_preferences = []
            
            # Extract from different sources
            text_prefs = self.extract_from_feedback_text(session)
            reasoning_prefs = self.extract_from_reasoning_patterns(session)
            action_prefs = self.extract_from_action_patterns(session)
            
            all_preferences.extend(text_prefs)
            all_preferences.extend(reasoning_prefs)
            all_preferences.extend(action_prefs)
            
            # Consolidate and rank preferences
            consolidated = self._consolidate_all_preferences(all_preferences)
            
            # Sort by confidence score
            consolidated.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            return consolidated
            
        except Exception as e:
            self.logger.error(f"Error extracting all preferences: {str(e)}")
            return []
    
    def classify_preference_category(self, preference_text: str) -> str:
        """Classify a preference into a category based on keywords"""
        text_lower = preference_text.lower()
        
        category_scores = {}
        
        for category, keywords in self.PREFERENCE_CATEGORIES.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            # Return category with highest score
            return max(category_scores.items(), key=lambda x: x[1])[0]
        else:
            return 'general'  # Default category
    
    def enhance_prompt_with_preferences(self, base_prompt: str, session: Session) -> str:
        """Enhance a system prompt with user preferences"""
        try:
            # Get manual preferences
            manual_prefs = UserPreference.objects.filter(
                session=session,
                is_active=True
            )
            
            # Get high-confidence extracted preferences
            extracted_prefs = ExtractedPreference.objects.filter(
                session=session,
                is_active=True,
                confidence_score__gte=0.7
            ).order_by('-confidence_score')[:5]  # Top 5 most confident
            
            if not manual_prefs.exists() and not extracted_prefs.exists():
                return base_prompt
            
            # Build preference section
            preference_text = "\n\nUser Preferences:"
            
            # Add manual preferences
            for pref in manual_prefs:
                preference_text += f"\n- {pref.key.replace('_', ' ').title()}: {pref.value}"
            
            # Add extracted preferences
            for pref in extracted_prefs:
                preference_text += f"\n- {pref.preference_category.title()}: {pref.preference_text}"
            
            preference_text += "\n\nPlease ensure your responses align with these preferences."
            
            return base_prompt + preference_text
            
        except Exception as e:
            self.logger.error(f"Error enhancing prompt with preferences: {str(e)}")
            return base_prompt
    
    def detect_preference_changes(self, session: Session) -> bool:
        """Detect if user preferences have changed based on recent feedback"""
        try:
            # Simple implementation: check if recent feedback patterns differ from historical
            recent_feedbacks = UserFeedback.objects.filter(
                draft__email__session=session
            ).order_by('-created_at')[:10]
            
            if recent_feedbacks.count() < 5:
                return False
            
            # Extract preferences from recent feedback
            recent_prefs = []
            for feedback in recent_feedbacks:
                if feedback.reason:
                    prefs = self._analyze_feedback_text(feedback.reason, feedback.id)
                    recent_prefs.extend(prefs)
            
            # Simple heuristic: if we found new preference statements, consider it a change
            return len(recent_prefs) > 0
            
        except Exception as e:
            self.logger.error(f"Error detecting preference changes: {str(e)}")
            return False
    
    def _analyze_feedback_text(self, feedback_text: str, feedback_id: int) -> List[Dict[str, Any]]:
        """Analyze individual feedback text for preference statements"""
        preferences = []
        text_lower = feedback_text.lower()
        
        for pattern, sentiment in self.PREFERENCE_PATTERNS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            
            for match in matches:
                preference_content = match.group(1).strip()
                
                if len(preference_content) > 5:  # Filter out very short matches
                    category = self.classify_preference_category(preference_content)
                    
                    # Build preference text based on sentiment
                    if sentiment == 'positive':
                        pref_text = f"User prefers {preference_content}"
                    elif sentiment == 'negative':
                        pref_text = f"User finds responses {preference_content} (should avoid)"
                    elif sentiment == 'more_of':
                        pref_text = f"User wants more {preference_content}"
                    elif sentiment == 'avoid':
                        pref_text = f"User wants to avoid {preference_content}"
                    elif sentiment == 'requirement':
                        pref_text = f"Responses should be {preference_content}"
                    else:
                        pref_text = preference_content
                    
                    preferences.append({
                        'category': category,
                        'text': pref_text,
                        'confidence': 0.6,  # Medium confidence for text analysis
                        'sources': [f'feedback_text_{feedback_id}'],
                        'evidence': f'Extracted from feedback: "{feedback_text[:100]}..."'
                    })
        
        return preferences
    
    def _extract_preference_from_reasoning(self, reason_text: str, ratio: float, count: int, total: int, sentiment: str) -> Dict[str, Any]:
        """Extract preference from reasoning factor patterns"""
        category = self.classify_preference_category(reason_text)
        
        if sentiment == 'liked':
            pref_text = f"User appreciates {reason_text}"
        else:
            pref_text = f"User dislikes {reason_text} (should avoid)"
        
        confidence = min(0.9, ratio * 0.8 + (count / 10) * 0.2)  # Scale confidence
        
        return {
            'category': category,
            'text': pref_text,
            'confidence': confidence,
            'sources': ['reasoning_pattern_analysis'],
            'evidence': f'{ratio:.1%} {sentiment} rate for "{reason_text}" ({count}/{total} ratings)'
        }
    
    def _consolidate_text_preferences(self, preferences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Consolidate similar text-based preferences"""
        # Group by category
        by_category = defaultdict(list)
        for pref in preferences:
            by_category[pref['category']].append(pref)
        
        consolidated = []
        
        for category, prefs in by_category.items():
            if len(prefs) == 1:
                consolidated.append(prefs[0])
            else:
                # Merge similar preferences in same category
                merged = {
                    'category': category,
                    'text': f"User has {len(prefs)} preferences about {category}",
                    'confidence': sum(p['confidence'] for p in prefs) / len(prefs),
                    'sources': [source for p in prefs for source in p['sources']],
                    'evidence': f"Consolidated from {len(prefs)} feedback statements"
                }
                consolidated.append(merged)
        
        return consolidated
    
    def _consolidate_all_preferences(self, preferences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Consolidate preferences from all sources"""
        # Group by category
        by_category = defaultdict(list)
        for pref in preferences:
            by_category[pref['category']].append(pref)
        
        consolidated = []
        
        for category, prefs in by_category.items():
            if len(prefs) == 1:
                consolidated.append(prefs[0])
            else:
                # Calculate average confidence, combine sources
                avg_confidence = sum(p['confidence'] for p in prefs) / len(prefs)
                all_sources = []
                for p in prefs:
                    all_sources.extend(p.get('sources', []))
                
                # Create consolidated preference
                merged = {
                    'category': category,
                    'text': self._merge_preference_texts(prefs),
                    'confidence': avg_confidence,
                    'sources': list(set(all_sources)),  # Remove duplicates
                    'evidence': f"Consolidated from {len(prefs)} sources across multiple analysis methods"
                }
                consolidated.append(merged)
        
        return consolidated
    
    def _merge_preference_texts(self, preferences: List[Dict[str, Any]]) -> str:
        """Merge multiple preference texts into a coherent statement"""
        # Simple implementation: take the highest confidence preference text
        # In a more sophisticated version, could use NLP to merge semantically
        
        if not preferences:
            return ""
        
        # Sort by confidence and take the best one
        best_pref = max(preferences, key=lambda x: x.get('confidence', 0))
        return best_pref['text']