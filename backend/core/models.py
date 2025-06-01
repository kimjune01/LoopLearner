from django.db import models
from django.utils import timezone
import json
import uuid


class PromptLab(models.Model):
    """Prompt optimization laboratories with isolated state and evolution tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # PromptLab metadata
    optimization_iterations = models.IntegerField(default=0)
    total_emails_processed = models.IntegerField(default=0)
    total_feedback_collected = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} ({self.created_at.strftime('%Y-%m-%d')})"


class SystemPrompt(models.Model):
    """System prompt versions with evolution tracking"""
    prompt_lab = models.ForeignKey(PromptLab, on_delete=models.CASCADE, related_name='prompts', null=True, blank=True)
    content = models.TextField()
    version = models.IntegerField()  # PromptLab-scoped version (global when prompt_lab is null)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=False)
    performance_score = models.FloatField(null=True, blank=True)
    parameters = models.JSONField(default=list, blank=True)  # List of parameter names found in content
    
    class Meta:
        ordering = ['-version']
        unique_together = [['prompt_lab', 'version']]
    
    def extract_parameters(self):
        """Extract parameter names from content and update the parameters field"""
        import re
        if not self.content:
            self.parameters = []
            return []
        
        # Find all parameters in exactly double curly braces (not triple or more)
        # Use negative lookbehind and lookahead to avoid matching nested braces
        parameter_regex = r'(?<!\{)\{\{([^{}]+)\}\}(?!\})'
        matches = re.findall(parameter_regex, self.content)
        
        # Clean up parameter names and remove duplicates
        parameters = []
        for match in matches:
            param = match.strip()
            if param and param not in parameters:
                parameters.append(param)
        
        self.parameters = parameters
        return parameters
    
    def save(self, *args, **kwargs):
        """Override save to automatically extract parameters"""
        self.extract_parameters()
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.prompt_lab:
            return f"{self.prompt_lab.name} Prompt v{self.version}"
        return f"Global Prompt v{self.version}"


class UserPreference(models.Model):
    """User preferences in natural language"""
    prompt_lab = models.ForeignKey(PromptLab, on_delete=models.CASCADE, related_name='preferences', null=True, blank=True)
    key = models.CharField(max_length=100)
    value = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        pass  # Remove unique constraint for now
    
    def __str__(self):
        if self.prompt_lab:
            return f"{self.prompt_lab.name} - {self.key}: {self.value[:50]}"
        return f"Global - {self.key}: {self.value[:50]}"


class Email(models.Model):
    """Synthetic and real emails for draft generation"""
    SCENARIO_CHOICES = [
        ('random', 'Random'),
        ('professional', 'Professional'),
        ('casual', 'Casual'),
        ('complaint', 'Complaint'),
        ('inquiry', 'Inquiry'),
    ]
    
    prompt_lab = models.ForeignKey(PromptLab, on_delete=models.CASCADE, related_name='emails', null=True, blank=True)
    subject = models.CharField(max_length=500)
    body = models.TextField()
    sender = models.EmailField()
    scenario_type = models.CharField(max_length=20, choices=SCENARIO_CHOICES, default='random')
    is_synthetic = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        if self.prompt_lab:
            return f"{self.prompt_lab.name} - {self.subject[:50]} ({self.scenario_type})"
        return f"Global - {self.subject[:50]} ({self.scenario_type})"


class DraftReason(models.Model):
    """Reasoning factors for draft suggestions"""
    text = models.TextField()
    confidence = models.FloatField()
    created_at = models.DateTimeField(default=timezone.now)
    
    def clean(self):
        """Validate confidence is between 0 and 1"""
        from django.core.exceptions import ValidationError
        if self.confidence is not None:
            if self.confidence < 0 or self.confidence > 1:
                raise ValidationError('Confidence must be between 0 and 1')
    
    def __str__(self):
        return f"{self.text[:50]} ({self.confidence})"


class Draft(models.Model):
    """Generated draft responses for emails"""
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='drafts')
    content = models.TextField()
    reasons = models.ManyToManyField(DraftReason, related_name='drafts')
    system_prompt = models.ForeignKey(SystemPrompt, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Draft for: {self.email.subject[:30]}"


class UserFeedback(models.Model):
    """User feedback on draft suggestions"""
    ACTION_CHOICES = [
        ('accept', 'Accept'),
        ('reject', 'Reject'),
        ('edit', 'Edit'),
        ('ignore', 'Ignore'),
    ]
    
    draft = models.ForeignKey(Draft, on_delete=models.CASCADE, related_name='feedback')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    reason = models.TextField(blank=True)
    edited_content = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.action} - {self.draft.email.subject[:30]}"


class ReasonRating(models.Model):
    """User ratings for individual reasoning factors"""
    feedback = models.ForeignKey(UserFeedback, on_delete=models.CASCADE, related_name='reason_ratings')
    reason = models.ForeignKey(DraftReason, on_delete=models.CASCADE)
    liked = models.BooleanField()  # True for like, False for dislike
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('feedback', 'reason')
    
    def __str__(self):
        sentiment = "👍" if self.liked else "👎"
        return f"{sentiment} {self.reason.text[:30]}"


class EvaluationSnapshot(models.Model):
    """Snapshots for evaluating prompt performance"""
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    expected_outcome = models.TextField()
    prompt_version = models.IntegerField()
    performance_score = models.FloatField()
    created_at = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)  # Additional context
    
    def __str__(self):
        return f"Eval: {self.email.subject[:30]} (v{self.prompt_version})"


class OptimizationRun(models.Model):
    """Track prompt optimization attempts"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    old_prompt = models.ForeignKey(SystemPrompt, on_delete=models.CASCADE, related_name='optimization_runs_old')
    new_prompt = models.ForeignKey(SystemPrompt, on_delete=models.CASCADE, related_name='optimization_runs_new', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    feedback_count = models.IntegerField(default=0)  # Number of feedback items used
    performance_improvement = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Optimization: v{self.old_prompt.version} -> v{getattr(self.new_prompt, 'version', '?')} ({self.status})"


class EvaluationDataset(models.Model):
    """Simple evaluation dataset - just name and description for now"""
    prompt_lab = models.ForeignKey(PromptLab, on_delete=models.CASCADE, related_name='evaluation_datasets', null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=list, blank=True)  # List of parameter names
    parameter_descriptions = models.JSONField(default=dict, blank=True)  # Parameter descriptions
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.prompt_lab.name if self.prompt_lab else 'Global'})"


class EvaluationCase(models.Model):
    """Individual test case - input, expected output, that's it"""
    dataset = models.ForeignKey(EvaluationDataset, on_delete=models.CASCADE, related_name='cases')
    input_text = models.TextField()  # The input to test against the prompt
    expected_output = models.TextField()  # What we expect the prompt to generate
    context = models.JSONField(default=dict, blank=True)  # Optional extra data
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Case {self.id}: {self.input_text[:50]}..."


class EvaluationRun(models.Model):
    """Track when we run evaluations"""
    dataset = models.ForeignKey(EvaluationDataset, on_delete=models.CASCADE)
    prompt = models.ForeignKey(SystemPrompt, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='pending')  # pending, running, completed, failed
    overall_score = models.FloatField(null=True, blank=True)  # 0.0 to 1.0
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Eval {self.id}: {self.prompt} on {self.dataset}"


class EvaluationResult(models.Model):
    """Results for individual test cases"""
    run = models.ForeignKey(EvaluationRun, on_delete=models.CASCADE, related_name='results')
    case = models.ForeignKey(EvaluationCase, on_delete=models.CASCADE)
    generated_output = models.TextField()  # What the prompt actually generated
    similarity_score = models.FloatField()  # 0.0 to 1.0
    passed = models.BooleanField()  # True if score above threshold
    details = models.JSONField(default=dict, blank=True)  # Extra debugging info
    
    def __str__(self):
        return f"Result {self.id}: {self.similarity_score:.2f} ({'PASS' if self.passed else 'FAIL'})"


class PromptLabConfidence(models.Model):
    """Track confidence metrics for prompt labs"""
    
    # Threshold constants for determining when learning is sufficient
    USER_CONFIDENCE_THRESHOLD = 0.75
    SYSTEM_CONFIDENCE_THRESHOLD = 0.75  
    COMBINED_CONFIDENCE_THRESHOLD = 0.80
    
    prompt_lab = models.OneToOneField(PromptLab, on_delete=models.CASCADE, related_name='confidence_tracker')
    
    # Core confidence metrics (0.0 to 1.0)
    user_confidence = models.FloatField(default=0.0)  # How confident user is in their feedback
    system_confidence = models.FloatField(default=0.0)  # How confident system is in understanding user
    confidence_trend = models.FloatField(default=0.0)  # Rate of confidence change
    
    # Detailed breakdown metrics
    feedback_consistency_score = models.FloatField(default=0.0)  # Consistency of user feedback patterns
    reasoning_alignment_score = models.FloatField(default=0.0)  # How well reasoning aligns with user preferences
    total_feedback_count = models.IntegerField(default=0)  # Total feedback received
    consistent_feedback_streak = models.IntegerField(default=0)  # Current streak of consistent feedback
    
    # Tracking metadata
    last_calculated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-last_calculated']
    
    def clean(self):
        """Validate confidence values are between 0 and 1"""
        from django.core.exceptions import ValidationError
        
        fields_to_validate = [
            ('user_confidence', self.user_confidence),
            ('system_confidence', self.system_confidence), 
            ('feedback_consistency_score', self.feedback_consistency_score),
            ('reasoning_alignment_score', self.reasoning_alignment_score)
        ]
        
        for field_name, value in fields_to_validate:
            if value is not None:
                if value < 0 or value > 1:
                    raise ValidationError(f'{field_name} must be between 0 and 1')
    
    def save(self, *args, **kwargs):
        """Override save to validate confidence values"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_user_confidence_sufficient(self):
        """Check if user confidence meets threshold"""
        return self.user_confidence >= self.USER_CONFIDENCE_THRESHOLD
    
    def is_system_confidence_sufficient(self):
        """Check if system confidence meets threshold"""
        return self.system_confidence >= self.SYSTEM_CONFIDENCE_THRESHOLD
    
    def is_learning_sufficient(self):
        """Check if both confidence metrics meet thresholds"""
        combined_confidence = (self.user_confidence + self.system_confidence) / 2
        return (self.is_user_confidence_sufficient() and 
                self.is_system_confidence_sufficient() and
                combined_confidence >= self.COMBINED_CONFIDENCE_THRESHOLD)
    
    def should_continue_learning(self):
        """Determine if system should continue learning"""
        return not self.is_learning_sufficient()
    
    def __str__(self):
        return f"{self.prompt_lab.name} - U:{self.user_confidence:.2f} S:{self.system_confidence:.2f}"


class ExtractedPreference(models.Model):
    """Automatically extracted user preferences from feedback patterns"""
    
    prompt_lab = models.ForeignKey(PromptLab, on_delete=models.CASCADE, related_name='extracted_preferences')
    
    # Source tracking
    source_feedback_ids = models.JSONField(default=list)  # List of feedback IDs that led to this preference
    
    # Preference details
    preference_category = models.CharField(max_length=100)  # e.g., 'tone', 'structure', 'length', 'vocabulary'
    preference_text = models.TextField()  # Natural language description of the preference
    confidence_score = models.FloatField()  # 0.0 to 1.0 - how confident we are in this preference
    
    # Extraction metadata
    extraction_method = models.CharField(max_length=100)  # e.g., 'reasoning_pattern_analysis', 'feedback_text_analysis'
    supporting_evidence = models.TextField()  # Description of evidence that supports this preference
    
    # Management fields
    is_active = models.BooleanField(default=True)
    auto_extracted = models.BooleanField(default=True)  # True if automatically extracted, False if manually verified
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-confidence_score', '-updated_at']
        indexes = [
            models.Index(fields=['prompt_lab', 'preference_category']),
            models.Index(fields=['confidence_score']),
        ]
    
    def clean(self):
        """Validate confidence score is between 0 and 1"""
        from django.core.exceptions import ValidationError
        
        if self.confidence_score is not None:
            if self.confidence_score < 0 or self.confidence_score > 1:
                raise ValidationError('confidence_score must be between 0 and 1')
    
    def save(self, *args, **kwargs):
        """Override save to validate confidence score"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.prompt_lab.name} - {self.preference_category}: {self.preference_text[:50]}... ({self.confidence_score:.2f})"