from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from asgiref.sync import sync_to_async
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Email, Draft, UserFeedback, ReasonRating, DraftReason, SystemPrompt, UserPreference
from .serializers import (
    EmailSerializer, DraftSerializer, UserFeedbackSerializer,
    GenerateEmailRequestSerializer, GenerateDraftsRequestSerializer,
    SubmitFeedbackRequestSerializer
)
from app.services.email_generator import SyntheticEmailGenerator
from app.services.llm_provider import OpenAIProvider
import os


# Initialize services
email_generator = SyntheticEmailGenerator()

# Get OpenAI API key from environment
openai_api_key = os.getenv('OPENAI_API_KEY', 'dummy-key-for-testing')
llm_provider = OpenAIProvider(openai_api_key)


@api_view(['POST'])
def generate_fake_email(request):
    """Generate a synthetic email for testing"""
    serializer = GenerateEmailRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    scenario_type = serializer.validated_data.get('scenario_type', 'random')
    
    try:
        # Use async generator but call it synchronously in Django view
        import asyncio
        email = asyncio.run(email_generator.generate_synthetic_email(scenario_type))
        
        serializer = EmailSerializer(email)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {'error': f'Failed to generate email: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def generate_drafts(request, email_id):
    """Generate draft responses for an email"""
    try:
        email = get_object_or_404(Email, id=email_id)
        
        # Get active system prompt
        system_prompt = SystemPrompt.objects.filter(is_active=True).first()
        if not system_prompt:
            return Response(
                {'error': 'No active system prompt found'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Get active user preferences
        user_preferences = list(UserPreference.objects.filter(is_active=True))
        
        # Generate drafts using LLM provider
        import asyncio
        drafts = asyncio.run(llm_provider.generate_drafts(email, system_prompt, user_preferences))
        
        serializer = DraftSerializer(drafts, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    except Email.DoesNotExist:
        return Response(
            {'error': 'Email not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to generate drafts: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def submit_feedback(request, email_id):
    """Submit user feedback for a draft"""
    serializer = SubmitFeedbackRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        draft_id = serializer.validated_data['draft_id']
        draft = get_object_or_404(Draft, id=draft_id, email_id=email_id)
        
        with transaction.atomic():
            # Create user feedback
            feedback = UserFeedback.objects.create(
                draft=draft,
                action=serializer.validated_data['action'],
                reason=serializer.validated_data.get('reason', ''),
                edited_content=serializer.validated_data.get('edited_content', '')
            )
            
            # Create reason ratings
            reason_ratings = serializer.validated_data.get('reason_ratings', {})
            for reason_id, liked in reason_ratings.items():
                try:
                    reason = DraftReason.objects.get(id=reason_id)
                    ReasonRating.objects.create(
                        feedback=feedback,
                        reason=reason,
                        liked=liked
                    )
                except DraftReason.DoesNotExist:
                    continue  # Skip invalid reason IDs
        
        feedback_serializer = UserFeedbackSerializer(feedback)
        return Response(feedback_serializer.data, status=status.HTTP_201_CREATED)
    
    except Draft.DoesNotExist:
        return Response(
            {'error': 'Draft not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to submit feedback: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def optimization_status(request):
    """Get current optimization status"""
    return Response({
        'status': 'idle',
        'message': 'No optimization currently running'
    })


@api_view(['GET'])
def list_emails(request):
    """List all emails"""
    emails = Email.objects.all().order_by('-created_at')
    serializer = EmailSerializer(emails, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_email_drafts(request, email_id):
    """Get all drafts for an email"""
    try:
        email = get_object_or_404(Email, id=email_id)
        drafts = email.drafts.all()
        serializer = DraftSerializer(drafts, many=True)
        return Response(serializer.data)
    except Email.DoesNotExist:
        return Response(
            {'error': 'Email not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )