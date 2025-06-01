from rest_framework import serializers
from .models import (
    PromptLab, SystemPrompt, UserPreference, Email, DraftReason, Draft, 
    UserFeedback, ReasonRating, EvaluationSnapshot, OptimizationRun
)


class PromptLabSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptLab
        fields = [
            'id', 'name', 'description', 'created_at', 'updated_at', 'is_active',
            'optimization_iterations', 'total_emails_processed', 'total_feedback_collected'
        ]


class DraftReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = DraftReason
        fields = ['id', 'text', 'confidence', 'created_at']


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = ['id', 'subject', 'body', 'sender', 'scenario_type', 'is_synthetic', 'created_at']


class DraftSerializer(serializers.ModelSerializer):
    reasons = DraftReasonSerializer(many=True, read_only=True)
    email = EmailSerializer(read_only=True)
    
    class Meta:
        model = Draft
        fields = ['id', 'content', 'reasons', 'email', 'system_prompt', 'created_at']


class ReasonRatingSerializer(serializers.ModelSerializer):
    reason = DraftReasonSerializer(read_only=True)
    
    class Meta:
        model = ReasonRating
        fields = ['id', 'reason', 'liked', 'created_at']


class UserFeedbackSerializer(serializers.ModelSerializer):
    reason_ratings = ReasonRatingSerializer(many=True, read_only=True)
    draft = DraftSerializer(read_only=True)
    
    class Meta:
        model = UserFeedback
        fields = ['id', 'draft', 'action', 'reason', 'edited_content', 'reason_ratings', 'created_at']


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ['id', 'key', 'value', 'description', 'created_at', 'updated_at', 'is_active']


class SystemPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemPrompt
        fields = ['id', 'content', 'version', 'created_at', 'is_active', 'performance_score', 'parameters']


class EvaluationSnapshotSerializer(serializers.ModelSerializer):
    email = EmailSerializer(read_only=True)
    
    class Meta:
        model = EvaluationSnapshot
        fields = ['id', 'email', 'expected_outcome', 'prompt_version', 'performance_score', 'created_at', 'metadata']


class OptimizationRunSerializer(serializers.ModelSerializer):
    old_prompt = SystemPromptSerializer(read_only=True)
    new_prompt = SystemPromptSerializer(read_only=True)
    
    class Meta:
        model = OptimizationRun
        fields = [
            'id', 'old_prompt', 'new_prompt', 'status', 'feedback_count', 
            'performance_improvement', 'error_message', 'started_at', 'completed_at'
        ]


# Input serializers for API endpoints
class GenerateEmailRequestSerializer(serializers.Serializer):
    scenario_type = serializers.ChoiceField(choices=Email.SCENARIO_CHOICES, default='random')


class GenerateDraftsRequestSerializer(serializers.Serializer):
    email_id = serializers.IntegerField()


class SubmitFeedbackRequestSerializer(serializers.Serializer):
    draft_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=UserFeedback.ACTION_CHOICES)
    reason = serializers.CharField(required=False, allow_blank=True)
    edited_content = serializers.CharField(required=False, allow_blank=True)
    reason_ratings = serializers.DictField(
        child=serializers.BooleanField(),
        required=False,
        help_text="Dictionary mapping reason IDs to like/dislike (true/false)"
    )