"""
Cold Start Manager Service

Manages the cold start phase for new sessions by:
1. Generating strategic synthetic emails to probe preferences
2. Learning from initial feedback
3. Bootstrapping the system prompt with discovered preferences
4. Managing confidence thresholds before allowing optimization
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from django.db.models import Count, Q

from core.models import (
    PromptLab, SystemPrompt, UserPreference, Email, Draft, 
    UserFeedback, PromptLabConfidence, ExtractedPreference
)
from .email_generator import SyntheticEmailGenerator
from .confidence_calculator import ConfidenceCalculator
from .preference_extractor import PreferenceExtractor
from .meta_prompt_manager import MetaPromptManager

logger = logging.getLogger(__name__)


@dataclass
class ColdStartResult:
    """Result of cold start initialization"""
    success: bool
    emails_generated: int
    error_message: Optional[str] = None


class ColdStartManager:
    """Manages confidence-based cold start for new sessions"""
    
    # Preference dimensions to probe during cold start
    PREFERENCE_DIMENSIONS = {
        'tone': ['professional', 'casual', 'friendly', 'formal'],
        'style': ['concise', 'detailed', 'conversational', 'direct'],
        'length': ['brief', 'moderate', 'comprehensive'],
        'formality': ['very_formal', 'formal', 'neutral', 'informal'],
        'approach': ['diplomatic', 'straightforward', 'empathetic']
    }
    
    # Minimum feedback required before optimization
    MIN_FEEDBACK_FOR_OPTIMIZATION = 10
    MIN_CONFIDENCE_FOR_OPTIMIZATION = 0.4
    
    def __init__(self):
        self.email_generator = SyntheticEmailGenerator()
        self.confidence_calculator = ConfidenceCalculator()
        self.preference_extractor = PreferenceExtractor()
        self.meta_prompt_manager = MetaPromptManager()
        self.logger = logging.getLogger(__name__)
    
    def initialize_cold_start(self, prompt_lab: PromptLab) -> ColdStartResult:
        """
        Initialize cold start process for a new session
        
        Args:
            session: The prompt_lab to initialize
            
        Returns:
            ColdStartResult with status and email count
        """
        try:
            # Generate strategic synthetic emails
            email_specs = self.generate_strategic_emails(prompt_lab)
            
            # Create the emails in the database
            emails_created = 0
            for spec in email_specs:
                email = self.email_generator.generate_email(
                    prompt_lab=prompt_lab,
                    scenario_type=spec['scenario_type'],
                    complexity=spec.get('complexity', 'medium'),
                    metadata=spec.get('metadata', {})
                )
                
                # Email created successfully
                # Note: We can't store metadata on the Email model directly
                # The cold start information is implicit in the synthetic emails
                
                emails_created += 1
            
            self.logger.info(f"Cold start initialized for prompt_lab {prompt_lab.id} with {emails_created} emails")
            
            return ColdStartResult(
                success=True,
                emails_generated=emails_created
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cold start for prompt_lab {prompt_lab.id}: {str(e)}")
            return ColdStartResult(
                success=False,
                emails_generated=0,
                error_message=str(e)
            )
    
    def generate_strategic_emails(self, prompt_lab: PromptLab) -> List[Dict[str, Any]]:
        """
        Generate strategic email specifications to probe different preferences
        
        Returns:
            List of email specifications with scenario types and preference probes
        """
        email_specs = []
        
        # 1. Professional vs Casual tone probe
        email_specs.append({
            'scenario_type': 'professional',
            'probes': ['tone', 'formality'],
            'complexity': 'medium'
        })
        
        email_specs.append({
            'scenario_type': 'casual',
            'probes': ['tone', 'formality'],
            'complexity': 'simple'
        })
        
        # 2. Inquiry and complaint emails
        email_specs.append({
            'scenario_type': 'inquiry',
            'probes': ['style', 'length'],
            'complexity': 'medium'
        })
        
        email_specs.append({
            'scenario_type': 'complaint',
            'probes': ['approach', 'tone'],
            'complexity': 'complex'
        })
        
        # 3. Mix of different scenarios to probe preferences
        email_specs.append({
            'scenario_type': 'professional',
            'probes': ['style', 'approach'],
            'complexity': 'high'
        })
        
        # Add more variety
        email_specs.append({
            'scenario_type': 'inquiry',
            'probes': ['formality', 'length'],
            'complexity': 'simple'
        })
        
        email_specs.append({
            'scenario_type': 'casual',
            'probes': ['style', 'approach'],
            'complexity': 'medium'
        })
        
        return email_specs
    
    def analyze_cold_start_feedback(self, prompt_lab: PromptLab) -> Dict[str, str]:
        """
        Analyze feedback from cold start emails to learn preferences
        
        Returns:
            Dictionary of learned preferences
        """
        # Get feedback on cold start emails
        # We consider the first synthetic emails as cold start emails
        cold_start_emails = Email.objects.filter(
            prompt_lab=prompt_lab,
            is_synthetic=True
        ).order_by('created_at')[:10]  # First 10 synthetic emails
        
        cold_start_feedback = UserFeedback.objects.filter(
            draft__email__in=cold_start_emails
        ).select_related('draft__email')
        
        if not cold_start_feedback.exists():
            return {}
        
        preferences = {}
        
        # Analyze acceptance patterns
        accepted_emails = []
        rejected_emails = []
        
        for feedback in cold_start_feedback:
            email = feedback.draft.email
            if feedback.action == 'accept':
                accepted_emails.append(email)
            elif feedback.action == 'reject':
                rejected_emails.append(email)
        
        # Determine tone preference
        tone_scores = {}
        for tone in self.PREFERENCE_DIMENSIONS['tone']:
            accepted_count = sum(1 for e in accepted_emails if e.scenario_type == tone)
            rejected_count = sum(1 for e in rejected_emails if e.scenario_type == tone)
            
            if accepted_count + rejected_count > 0:
                tone_scores[tone] = accepted_count / (accepted_count + rejected_count)
        
        if tone_scores:
            preferred_tone = max(tone_scores, key=tone_scores.get)
            if tone_scores[preferred_tone] > 0.6:  # Strong preference
                preferences['tone'] = preferred_tone
        
        # Analyze feedback reasons for style preferences
        feedback_with_reasons = cold_start_feedback.exclude(reason='')
        
        for feedback in feedback_with_reasons:
            reason_lower = feedback.reason.lower()
            
            # Check for length preferences
            if any(word in reason_lower for word in ['brief', 'short', 'concise', 'too long']):
                preferences['style'] = 'concise'
            elif any(word in reason_lower for word in ['detailed', 'comprehensive', 'thorough', 'too short']):
                preferences['style'] = 'detailed'
            
            # Check for formality preferences
            if any(word in reason_lower for word in ['formal', 'professional']):
                preferences['formality'] = 'formal'
            elif any(word in reason_lower for word in ['casual', 'friendly', 'relaxed']):
                preferences['formality'] = 'casual'
        
        # Use preference extractor for additional insights
        extracted = self.preference_extractor.extract_all_preferences(prompt_lab)
        
        for pref in extracted:
            if pref.get('confidence', 0) > 0.7:  # High confidence preferences
                if pref.get('category') and pref.get('text'):
                    preferences[pref['category']] = pref['text']
        
        self.logger.info(f"Learned preferences for prompt_lab {prompt_lab.id}: {preferences}")
        return preferences
    
    def apply_learned_preferences(self, prompt_lab: PromptLab, preferences: Dict[str, str]) -> Optional[SystemPrompt]:
        """
        Apply learned preferences to create an improved system prompt
        
        Returns:
            New SystemPrompt if created, None otherwise
        """
        if not preferences:
            return None
        
        # Get current active prompt
        current_prompt = SystemPrompt.objects.filter(
            prompt_lab=prompt_lab,
            is_active=True
        ).first()
        
        if not current_prompt:
            return None
        
        # Build preference instructions
        preference_instructions = []
        
        if 'tone' in preferences:
            preference_instructions.append(f"Use a {preferences['tone']} tone")
        
        if 'style' in preferences:
            if preferences['style'] == 'concise':
                preference_instructions.append("Keep responses brief and to the point")
            elif preferences['style'] == 'detailed':
                preference_instructions.append("Provide comprehensive and detailed responses")
        
        if 'formality' in preferences:
            if preferences['formality'] == 'formal':
                preference_instructions.append("Maintain a formal and professional demeanor")
            elif preferences['formality'] == 'casual':
                preference_instructions.append("Use a casual and friendly approach")
        
        if 'approach' in preferences:
            preference_instructions.append(f"Take a {preferences['approach']} approach in responses")
        
        # Create enhanced prompt
        enhanced_content = f"{current_prompt.content}\n\nUser Preferences:\n"
        enhanced_content += "\n".join(f"- {instruction}" for instruction in preference_instructions)
        
        # If we have preference placeholders, add them
        if '{{' in current_prompt.content:
            # Update the template with learned values
            enhanced_content = current_prompt.content
            for key, value in preferences.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in enhanced_content:
                    enhanced_content = enhanced_content.replace(placeholder, value)
        
        # Create new prompt version
        new_prompt = SystemPrompt.objects.create(
            prompt_lab=prompt_lab,
            content=enhanced_content,
            version=current_prompt.version + 1,
            is_active=True,
            performance_score=(current_prompt.performance_score or 0.5) * 1.1  # Slight boost for preferences
        )
        
        # Deactivate old prompt
        current_prompt.is_active = False
        current_prompt.save()
        
        # Store preferences
        for key, value in preferences.items():
            UserPreference.objects.update_or_create(
                prompt_lab=prompt_lab,
                key=key,
                defaults={
                    'value': value,
                    'description': f'Learned during cold start: {key}',
                    'is_active': True
                }
            )
        
        self.logger.info(f"Applied learned preferences to create prompt v{new_prompt.version} for prompt_lab {prompt_lab.id}")
        return new_prompt
    
    def should_allow_optimization(self, prompt_lab: PromptLab) -> bool:
        """
        Check if optimization should be allowed based on cold start status
        
        Returns:
            True if optimization can proceed, False if still in cold start
        """
        # Check if cold start is complete
        if not self.is_cold_start_complete(prompt_lab):
            return False
        
        # Check confidence levels
        confidence = PromptLabConfidence.objects.filter(
            prompt_lab=prompt_lab
        ).order_by('-created_at').first()
        
        if not confidence:
            # Calculate current confidence
            user_conf = self.confidence_calculator.calculate_user_confidence(prompt_lab)
            system_conf = self.confidence_calculator.calculate_system_confidence(prompt_lab)
            
            if user_conf < self.MIN_CONFIDENCE_FOR_OPTIMIZATION or system_conf < self.MIN_CONFIDENCE_FOR_OPTIMIZATION:
                return False
        else:
            if confidence.user_confidence < self.MIN_CONFIDENCE_FOR_OPTIMIZATION or \
               confidence.system_confidence < self.MIN_CONFIDENCE_FOR_OPTIMIZATION:
                return False
        
        return True
    
    def is_cold_start_complete(self, prompt_lab: PromptLab) -> bool:
        """
        Check if cold start phase is complete for a session
        
        Returns:
            True if cold start is complete, False otherwise
        """
        # Check feedback count
        feedback_count = UserFeedback.objects.filter(
            draft__email__prompt_lab=prompt_lab
        ).count()
        
        if feedback_count < self.MIN_FEEDBACK_FOR_OPTIMIZATION:
            return False
        
        # Check if we have feedback on cold start emails
        # Consider first synthetic emails as cold start
        cold_start_emails = Email.objects.filter(
            prompt_lab=prompt_lab,
            is_synthetic=True
        ).order_by('created_at')[:10]
        
        cold_start_feedback = UserFeedback.objects.filter(
            draft__email__in=cold_start_emails
        ).count()
        
        # Need at least 5 cold start email feedbacks
        if cold_start_feedback < 5:
            return False
        
        # Use confidence calculator's method
        return self.confidence_calculator.is_cold_start_complete(prompt_lab)
    
    def get_synthetic_email_ratio(self, prompt_lab: PromptLab) -> float:
        """
        Get recommended ratio of synthetic to real emails based on cold start progress
        
        Returns:
            Float between 0 and 1 representing synthetic email ratio
        """
        # During cold start, high ratio of synthetic
        if not self.is_cold_start_complete(prompt_lab):
            return 0.7
        
        # Get feedback counts
        total_feedback = UserFeedback.objects.filter(
            draft__email__prompt_lab=prompt_lab
        ).count()
        
        real_email_feedback = UserFeedback.objects.filter(
            draft__email__prompt_lab=prompt_lab,
            draft__email__is_synthetic=False
        ).count()
        
        # Gradually reduce synthetic ratio
        if total_feedback < 20:
            return 0.5
        elif total_feedback < 50:
            return 0.3
        elif real_email_feedback > 20:
            return 0.1  # Minimal synthetic emails
        else:
            return 0.2
    
    def get_cold_start_status(self, prompt_lab: PromptLab) -> Dict[str, Any]:
        """
        Get comprehensive cold start status for a session
        
        Returns:
            Dictionary with cold start metrics and status
        """
        feedback_count = UserFeedback.objects.filter(
            draft__email__prompt_lab=prompt_lab
        ).count()
        
        # Consider first synthetic emails as cold start
        cold_start_emails = Email.objects.filter(
            prompt_lab=prompt_lab,
            is_synthetic=True
        ).order_by('created_at')[:10]
        
        cold_start_feedback = UserFeedback.objects.filter(
            draft__email__in=cold_start_emails
        ).count()
        
        user_conf = self.confidence_calculator.calculate_user_confidence(prompt_lab)
        system_conf = self.confidence_calculator.calculate_system_confidence(prompt_lab)
        
        return {
            'is_cold_start_active': not self.is_cold_start_complete(prompt_lab),
            'is_cold_start_complete': self.is_cold_start_complete(prompt_lab),
            'synthetic_email_ratio': self.get_synthetic_email_ratio(prompt_lab),
            'optimization_allowed': self.should_allow_optimization(prompt_lab),
            'feedback_collected': feedback_count,
            'cold_start_feedback': cold_start_feedback,
            'confidence_levels': {
                'user': user_conf,
                'system': system_conf,
                'combined': (user_conf + system_conf) / 2
            },
            'progress_percentage': min(100, (feedback_count / self.MIN_FEEDBACK_FOR_OPTIMIZATION) * 100)
        }