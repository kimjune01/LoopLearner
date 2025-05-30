from django.db import models
from django.utils import timezone
import json
import uuid


class Session(models.Model):
    """Learning sessions with isolated state and prompt evolution"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Session metadata
    optimization_iterations = models.IntegerField(default=0)
    total_emails_processed = models.IntegerField(default=0)
    total_feedback_collected = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} ({self.created_at.strftime('%Y-%m-%d')})"


class SystemPrompt(models.Model):
    """System prompt versions with evolution tracking"""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='prompts', null=True, blank=True)
    content = models.TextField()
    version = models.IntegerField()  # Session-scoped version (global when session is null)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=False)
    performance_score = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['-version']
    
    def __str__(self):
        if self.session:
            return f"{self.session.name} Prompt v{self.version}"
        return f"Global Prompt v{self.version}"


class UserPreference(models.Model):
    """User preferences in natural language"""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='preferences', null=True, blank=True)
    key = models.CharField(max_length=100)
    value = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        pass  # Remove unique constraint for now
    
    def __str__(self):
        if self.session:
            return f"{self.session.name} - {self.key}: {self.value[:50]}"
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
    
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='emails', null=True, blank=True)
    subject = models.CharField(max_length=500)
    body = models.TextField()
    sender = models.EmailField()
    scenario_type = models.CharField(max_length=20, choices=SCENARIO_CHOICES, default='random')
    is_synthetic = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        if self.session:
            return f"{self.session.name} - {self.subject[:50]} ({self.scenario_type})"
        return f"Global - {self.subject[:50]} ({self.scenario_type})"


class DraftReason(models.Model):
    """Reasoning factors for draft suggestions"""
    text = models.TextField()
    confidence = models.FloatField()
    created_at = models.DateTimeField(default=timezone.now)
    
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