from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils import timezone
from django.db import models
import logging
import uuid

from core.models import PromptLab, SystemPrompt, UserPreference, Email, Draft, DraftReason, ReasonRating, UserFeedback, PromptLabConfidence, ExtractedPreference
from core.serializers import PromptLabSerializer

logger = logging.getLogger(__name__)


class PromptLabAPIView(APIView):
    """Base class for prompt lab-related API views"""
    
    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            return Response({'error': 'PromptLab not found'}, status=status.HTTP_404_NOT_FOUND)
        logger.error(f"PromptLab API Error: {str(exc)}")
        return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PromptLabListView(PromptLabAPIView):
    """List all prompt labs and create new prompt labs"""
    
    def get(self, request):
        """Get all prompt labs with optional filtering and sorting"""
        # Get query parameters
        search = request.query_params.get('search', '')
        sort_by = request.query_params.get('sort_by', 'updated_at')
        order = request.query_params.get('order', 'desc')
        status_filter = request.query_params.get('status', '')
        
        # Start with all active prompt labs
        prompt_labs = PromptLab.objects.filter(is_active=True)
        
        # Apply search filter
        if search:
            prompt_labs = prompt_labs.filter(
                models.Q(name__icontains=search) | 
                models.Q(description__icontains=search)
            )
        
        # Apply status filter (if needed in future)
        if status_filter:
            # For now, we only have is_active, but could add optimization_status later
            pass
        
        # Apply sorting
        if sort_by in ['created_at', 'updated_at', 'name']:
            order_prefix = '-' if order == 'desc' else ''
            prompt_labs = prompt_labs.order_by(f'{order_prefix}{sort_by}')
        
        # Serialize and return
        serializer = PromptLabSerializer(prompt_labs, many=True)
        return Response({
            'prompt_labs': serializer.data,
            'count': prompt_labs.count()
        })
    
    def post(self, request):
        """Create a new prompt lab"""
        data = request.data
        
        # Validate required fields
        name = data.get('name', '').strip()
        if not name:
            return Response(
                {'error': 'PromptLab name is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        description = data.get('description', '').strip()
        
        try:
            # Create the prompt lab
            prompt_lab = PromptLab.objects.create(
                name=name,
                description=description
            )
            
            # Create initial system prompt for the prompt lab
            initial_prompt_content = data.get('initial_prompt', 
                "You are a helpful email assistant that generates professional and appropriate email responses.")
            
            SystemPrompt.objects.create(
                prompt_lab=prompt_lab,
                content=initial_prompt_content,
                version=1,
                is_active=True
            )
            
            # Serialize and return the created prompt lab
            serializer = PromptLabSerializer(prompt_lab)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating prompt lab: {str(e)}")
            return Response(
                {'error': 'Failed to create prompt lab'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromptLabDetailView(PromptLabAPIView):
    """Get, update, or delete a specific prompt lab"""
    
    def get(self, request, prompt_lab_id):
        """Get prompt lab details with related data"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        # Get additional prompt lab statistics
        active_prompt = prompt_lab.prompts.filter(is_active=True).first()
        recent_emails = prompt_lab.emails.order_by('-created_at')[:5]
        
        serializer = PromptLabSerializer(prompt_lab)
        prompt_lab_data = serializer.data
        
        # Add additional context
        prompt_lab_data['active_prompt'] = {
            'id': active_prompt.id if active_prompt else None,
            'version': active_prompt.version if active_prompt else None,
            'content': active_prompt.content if active_prompt else None,
            'parameters': active_prompt.parameters if active_prompt else [],
        }
        prompt_lab_data['recent_emails'] = [
            {
                'id': email.id,
                'subject': email.subject,
                'created_at': email.created_at,
                'scenario_type': email.scenario_type
            } for email in recent_emails
        ]
        
        # Add reasoning summary
        prompt_lab_data['reasoning_summary'] = self._calculate_reasoning_summary(prompt_lab)
        
        # Add confidence metrics
        prompt_lab_data['confidence_metrics'] = self._get_confidence_metrics(prompt_lab)
        
        return Response(prompt_lab_data)
    
    def _calculate_reasoning_summary(self, prompt_lab):
        """Calculate reasoning factor summary for prompt lab"""
        # Get all drafts in this prompt lab
        drafts = Draft.objects.filter(email__prompt_lab=prompt_lab)
        
        # Get all reasons associated with these drafts
        all_reasons = DraftReason.objects.filter(drafts__in=drafts).distinct()
        total_reasons_generated = all_reasons.count()
        
        # Get all reason ratings for these drafts
        all_ratings = ReasonRating.objects.filter(
            feedback__draft__in=drafts
        )
        total_reason_ratings = all_ratings.count()
        
        # Calculate rating breakdown
        liked_count = all_ratings.filter(liked=True).count()
        disliked_count = all_ratings.filter(liked=False).count()
        
        # Get most and least liked reasons with aggregated stats
        reason_stats = {}
        for rating in all_ratings:
            reason_id = rating.reason.id
            if reason_id not in reason_stats:
                reason_stats[reason_id] = {
                    'reason': rating.reason,
                    'likes': 0,
                    'dislikes': 0
                }
            
            if rating.liked:
                reason_stats[reason_id]['likes'] += 1
            else:
                reason_stats[reason_id]['dislikes'] += 1
        
        # Sort by likes for most liked
        most_liked_reasons = sorted(
            [
                {
                    'text': stats['reason'].text,
                    'confidence': stats['reason'].confidence,
                    'like_count': stats['likes'],
                    'dislike_count': stats['dislikes']
                }
                for stats in reason_stats.values()
                if stats['likes'] > 0
            ],
            key=lambda x: x['like_count'],
            reverse=True
        )
        
        # Sort by dislikes for least liked
        least_liked_reasons = sorted(
            [
                {
                    'text': stats['reason'].text,
                    'confidence': stats['reason'].confidence,
                    'like_count': stats['likes'],
                    'dislike_count': stats['dislikes']
                }
                for stats in reason_stats.values()
                if stats['dislikes'] > 0
            ],
            key=lambda x: x['dislike_count'],
            reverse=True
        )
        
        return {
            'total_reasons_generated': total_reasons_generated,
            'total_reason_ratings': total_reason_ratings,
            'reason_rating_breakdown': {
                'liked': liked_count,
                'disliked': disliked_count,
                'total': total_reason_ratings
            },
            'most_liked_reasons': most_liked_reasons,
            'least_liked_reasons': least_liked_reasons
        }
    
    def _get_confidence_metrics(self, prompt_lab):
        """Get confidence metrics for prompt lab detail"""
        try:
            from app.services.confidence_calculator import ConfidenceCalculator
            
            calculator = ConfidenceCalculator()
            
            # Get or update confidence tracker
            confidence_tracker = calculator.update_session_confidence(prompt_lab)
            
            return {
                'user_confidence': confidence_tracker.user_confidence,
                'system_confidence': confidence_tracker.system_confidence,
                'is_learning_sufficient': confidence_tracker.is_learning_sufficient(),
                'should_continue_learning': confidence_tracker.should_continue_learning(),
                'is_cold_start_complete': calculator.is_cold_start_complete(prompt_lab),
                'confidence_trend': confidence_tracker.confidence_trend,
                'feedback_count': confidence_tracker.total_feedback_count,
                'consistency_streak': confidence_tracker.consistent_feedback_streak,
                'last_updated': confidence_tracker.last_calculated.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting confidence metrics for prompt lab {prompt_lab.id}: {str(e)}")
            # Return default values if calculation fails
            return {
                'user_confidence': 0.0,
                'system_confidence': 0.0,
                'is_learning_sufficient': False,
                'should_continue_learning': True,
                'is_cold_start_complete': False,
                'confidence_trend': 0.0,
                'feedback_count': 0,
                'consistency_streak': 0,
                'last_updated': None
            }
    
    def put(self, request, prompt_lab_id):
        """Update prompt lab details"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        data = request.data
        
        # Update fields if provided
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return Response(
                    {'error': 'PromptLab name cannot be empty'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            prompt_lab.name = name
        
        if 'description' in data:
            prompt_lab.description = data['description'].strip()
        
        # Handle initial_prompt updates
        if 'initial_prompt' in data:
            prompt_content = data['initial_prompt'].strip()
            if prompt_content:
                # Get or create active prompt for this prompt lab
                active_prompt = prompt_lab.prompts.filter(is_active=True).first()
                
                if active_prompt:
                    # Update existing active prompt
                    active_prompt.content = prompt_content
                    active_prompt.save()
                else:
                    # Create new prompt as version 1
                    SystemPrompt.objects.create(
                        prompt_lab=prompt_lab,
                        content=prompt_content,
                        version=1,
                        is_active=True
                    )
                    
            else:
                # If empty prompt, deactivate current active prompt
                active_prompt = prompt_lab.prompts.filter(is_active=True).first()
                if active_prompt:
                    active_prompt.is_active = False
                    active_prompt.save()
        
        try:
            prompt_lab.save()
            serializer = PromptLabSerializer(prompt_lab)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error updating prompt lab {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to update prompt lab'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, prompt_lab_id):
        """Soft delete a prompt lab"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            # Soft delete by setting is_active to False
            prompt_lab.is_active = False
            prompt_lab.save()
            
            return Response(
                {'message': 'PromptLab deleted successfully'}, 
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error deleting prompt lab {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to delete prompt lab'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromptLabExportView(PromptLabAPIView):
    """Export prompt lab data"""
    
    def get(self, request, prompt_lab_id):
        """Export complete prompt lab state"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            # Get all prompt lab-related data
            prompts = prompt_lab.prompts.all().order_by('version')
            preferences = prompt_lab.preferences.filter(is_active=True)
            emails = prompt_lab.emails.all().order_by('created_at')
            
            # Build export data structure
            export_data = {
                'prompt_lab': {
                    'id': str(prompt_lab.id),
                    'name': prompt_lab.name,
                    'description': prompt_lab.description,
                    'created_at': prompt_lab.created_at.isoformat(),
                    'updated_at': prompt_lab.updated_at.isoformat(),
                    'optimization_iterations': prompt_lab.optimization_iterations,
                    'total_emails_processed': prompt_lab.total_emails_processed,
                    'total_feedback_collected': prompt_lab.total_feedback_collected,
                },
                'prompts': [
                    {
                        'version': prompt.version,
                        'content': prompt.content,
                        'is_active': prompt.is_active,
                        'performance_score': prompt.performance_score,
                        'created_at': prompt.created_at.isoformat(),
                    } for prompt in prompts
                ],
                'preferences': [
                    {
                        'key': pref.key,
                        'value': pref.value,
                        'description': pref.description,
                        'created_at': pref.created_at.isoformat(),
                        'updated_at': pref.updated_at.isoformat(),
                    } for pref in preferences
                ],
                'emails': [
                    {
                        'id': email.id,
                        'subject': email.subject,
                        'body': email.body,
                        'sender': email.sender,
                        'scenario_type': email.scenario_type,
                        'is_synthetic': email.is_synthetic,
                        'created_at': email.created_at.isoformat(),
                    } for email in emails
                ],
                'export_timestamp': timezone.now().isoformat(),
                'version': '1.0'
            }
            
            return Response(export_data)
            
        except Exception as e:
            logger.error(f"Error exporting prompt lab {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to export prompt lab data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromptLabDuplicateView(PromptLabAPIView):
    """Duplicate an existing prompt lab"""
    
    def post(self, request, prompt_lab_id):
        """Create a copy of an existing prompt lab"""
        source_prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        data = request.data
        new_name = data.get('name', f"{source_prompt_lab.name} (Copy)")
        new_description = data.get('description', source_prompt_lab.description)
        
        try:
            # Create new prompt lab
            new_prompt_lab = PromptLab.objects.create(
                name=new_name,
                description=new_description
            )
            
            # Copy system prompts
            for prompt in source_prompt_lab.prompts.all():
                SystemPrompt.objects.create(
                    prompt_lab=new_prompt_lab,
                    content=prompt.content,
                    version=prompt.version,
                    is_active=prompt.is_active,
                    performance_score=prompt.performance_score
                )
            
            # Copy user preferences
            for pref in source_prompt_lab.preferences.filter(is_active=True):
                UserPreference.objects.create(
                    prompt_lab=new_prompt_lab,
                    key=pref.key,
                    value=pref.value,
                    description=pref.description
                )
            
            # Optionally copy emails if requested
            copy_emails = data.get('copy_emails', False)
            if copy_emails:
                for email in source_prompt_lab.emails.all():
                    Email.objects.create(
                        prompt_lab=new_prompt_lab,
                        subject=email.subject,
                        body=email.body,
                        sender=email.sender,
                        scenario_type=email.scenario_type,
                        is_synthetic=email.is_synthetic
                    )
            
            serializer = PromptLabSerializer(new_prompt_lab)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error duplicating prompt lab {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to duplicate prompt lab'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromptLabStatsView(PromptLabAPIView):
    """Get prompt lab statistics and metrics"""
    
    def get(self, request, prompt_lab_id):
        """Get detailed prompt lab statistics"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            # Calculate various statistics
            prompts_count = prompt_lab.prompts.count()
            active_prompt = prompt_lab.prompts.filter(is_active=True).first()
            
            emails_count = prompt_lab.emails.count()
            synthetic_emails_count = prompt_lab.emails.filter(is_synthetic=True).count()
            
            # Get draft and feedback statistics
            total_drafts = 0
            total_feedback = 0
            feedback_by_action = {'accept': 0, 'reject': 0, 'edit': 0, 'ignore': 0}
            
            for email in prompt_lab.emails.all():
                drafts = email.drafts.all()
                total_drafts += drafts.count()
                
                for draft in drafts:
                    feedback_items = draft.feedback.all()
                    total_feedback += feedback_items.count()
                    
                    for feedback in feedback_items:
                        feedback_by_action[feedback.action] += 1
            
            stats = {
                'prompt_lab_id': str(prompt_lab.id),
                'prompt_lab_name': prompt_lab.name,
                'created_at': prompt_lab.created_at.isoformat(),
                'updated_at': prompt_lab.updated_at.isoformat(),
                'optimization_iterations': prompt_lab.optimization_iterations,
                'prompts': {
                    'total_versions': prompts_count,
                    'current_version': active_prompt.version if active_prompt else 0,
                    'current_performance_score': active_prompt.performance_score if active_prompt else None,
                },
                'emails': {
                    'total_processed': emails_count,
                    'synthetic_generated': synthetic_emails_count,
                    'real_emails': emails_count - synthetic_emails_count,
                },
                'drafts': {
                    'total_generated': total_drafts,
                    'average_per_email': total_drafts / emails_count if emails_count > 0 else 0,
                },
                'feedback': {
                    'total_collected': total_feedback,
                    'by_action': feedback_by_action,
                    'feedback_rate': total_feedback / total_drafts if total_drafts > 0 else 0,
                },
                'preferences_count': prompt_lab.preferences.filter(is_active=True).count(),
            }
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"Error getting prompt lab stats {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to get prompt lab statistics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DraftReasoningFactorsView(PromptLabAPIView):
    """Get reasoning factors for a specific draft"""
    
    def get(self, request, prompt_lab_id, draft_id):
        """Get reasoning factors and their rating stats for a draft"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            # Get draft and ensure it belongs to this prompt lab
            draft = Draft.objects.get(
                id=draft_id,
                email__prompt_lab=prompt_lab
            )
        except Draft.DoesNotExist:
            return Response(
                {'error': 'Draft not found in this prompt lab'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Get all reasoning factors for this draft
            reasons = draft.reasons.all()
            
            # Build response with rating statistics
            reasoning_factors = []
            for reason in reasons:
                # Get rating stats for this reason
                ratings = ReasonRating.objects.filter(reason=reason)
                likes = ratings.filter(liked=True).count()
                dislikes = ratings.filter(liked=False).count()
                
                reasoning_factors.append({
                    'id': reason.id,
                    'text': reason.text,
                    'confidence': reason.confidence,
                    'rating_stats': {
                        'likes': likes,
                        'dislikes': dislikes,
                        'total_ratings': likes + dislikes
                    }
                })
            
            return Response({
                'draft_id': draft.id,
                'reasoning_factors': reasoning_factors
            })
            
        except Exception as e:
            logger.error(f"Error getting draft reasoning factors {draft_id}: {str(e)}")
            return Response(
                {'error': 'Failed to get reasoning factors'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkAcceptReasonsView(PromptLabAPIView):
    """Bulk accept all reasoning factors for a draft"""
    
    def post(self, request, prompt_lab_id, draft_id):
        """Create feedback with all reasoning factors liked"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            # Get draft and ensure it belongs to this prompt lab
            draft = Draft.objects.get(
                id=draft_id,
                email__prompt_lab=prompt_lab
            )
        except Draft.DoesNotExist:
            return Response(
                {'error': 'Draft not found in this prompt lab'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            data = request.data
            reason = data.get('reason', 'Bulk accept all reasoning factors')
            
            # Create feedback
            feedback = UserFeedback.objects.create(
                draft=draft,
                action='accept',
                reason=reason
            )
            
            # Get all reasons for this draft and rate them as liked
            reasons = draft.reasons.all()
            reasons_rated = 0
            
            for reason_obj in reasons:
                ReasonRating.objects.create(
                    feedback=feedback,
                    reason=reason_obj,
                    liked=True
                )
                reasons_rated += 1
            
            return Response({
                'feedback_id': feedback.id,
                'action': 'bulk_accept',
                'reasons_rated': reasons_rated,
                'draft_id': draft.id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error in bulk accept reasons {draft_id}: {str(e)}")
            return Response(
                {'error': 'Failed to bulk accept reasons'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkRejectReasonsView(PromptLabAPIView):
    """Bulk reject all reasoning factors for a draft"""
    
    def post(self, request, prompt_lab_id, draft_id):
        """Create feedback with all reasoning factors disliked"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            # Get draft and ensure it belongs to this prompt lab
            draft = Draft.objects.get(
                id=draft_id,
                email__prompt_lab=prompt_lab
            )
        except Draft.DoesNotExist:
            return Response(
                {'error': 'Draft not found in this prompt lab'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            data = request.data
            reason = data.get('reason', 'Bulk reject all reasoning factors')
            
            # Create feedback
            feedback = UserFeedback.objects.create(
                draft=draft,
                action='reject',
                reason=reason
            )
            
            # Get all reasons for this draft and rate them as disliked
            reasons = draft.reasons.all()
            reasons_rated = 0
            
            for reason_obj in reasons:
                ReasonRating.objects.create(
                    feedback=feedback,
                    reason=reason_obj,
                    liked=False
                )
                reasons_rated += 1
            
            return Response({
                'feedback_id': feedback.id,
                'action': 'bulk_reject',
                'reasons_rated': reasons_rated,
                'draft_id': draft.id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error in bulk reject reasons {draft_id}: {str(e)}")
            return Response(
                {'error': 'Failed to bulk reject reasons'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkRateReasonsView(PromptLabAPIView):
    """Bulk rate selected reasoning factors for a draft"""
    
    def post(self, request, prompt_lab_id, draft_id):
        """Create feedback with specific reason ratings"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            # Get draft and ensure it belongs to this prompt lab
            draft = Draft.objects.get(
                id=draft_id,
                email__prompt_lab=prompt_lab
            )
        except Draft.DoesNotExist:
            return Response(
                {'error': 'Draft not found in this prompt lab'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            data = request.data
            action = data.get('action', 'accept')
            reason = data.get('reason', 'Bulk rating of selected reasoning factors')
            reason_ratings = data.get('reason_ratings', {})
            
            # Validate action
            if action not in ['accept', 'reject', 'edit', 'ignore']:
                return Response(
                    {'error': 'Invalid action'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create feedback
            feedback = UserFeedback.objects.create(
                draft=draft,
                action=action,
                reason=reason,
                edited_content=data.get('edited_content', '')
            )
            
            # Create ratings for selected reasons
            reasons_rated = 0
            for reason_id_str, liked in reason_ratings.items():
                try:
                    reason_id = int(reason_id_str)
                    reason_obj = DraftReason.objects.get(id=reason_id)
                    
                    # Verify this reason belongs to this draft
                    if reason_obj in draft.reasons.all():
                        ReasonRating.objects.create(
                            feedback=feedback,
                            reason=reason_obj,
                            liked=bool(liked)
                        )
                        reasons_rated += 1
                except (ValueError, DraftReason.DoesNotExist):
                    # Ignore invalid reason IDs
                    continue
            
            return Response({
                'feedback_id': feedback.id,
                'action': 'bulk_rate',
                'reasons_rated': reasons_rated,
                'draft_id': draft.id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error in bulk rate reasons {draft_id}: {str(e)}")
            return Response(
                {'error': 'Failed to bulk rate reasons'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuickRateReasonView(PromptLabAPIView):
    """Quick thumbs up/down rating for individual reasoning factors"""
    
    def post(self, request, prompt_lab_id, reason_id):
        """Quick rate a single reasoning factor"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            # Get the reason
            try:
                reason = DraftReason.objects.get(id=reason_id)
            except DraftReason.DoesNotExist:
                return Response(
                    {'error': 'Reason not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            data = request.data
            rating = data.get('rating')  # 'thumbs_up' or 'thumbs_down'
            draft_id = data.get('draft_id')
            
            # Validate rating
            if rating not in ['thumbs_up', 'thumbs_down']:
                return Response(
                    {'error': 'Invalid rating. Must be thumbs_up or thumbs_down'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the draft and validate it belongs to prompt lab
            try:
                draft = Draft.objects.get(
                    id=draft_id,
                    email__prompt_lab=prompt_lab
                )
            except Draft.DoesNotExist:
                return Response(
                    {'error': 'Draft not found in this prompt lab'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verify reason belongs to this draft
            if reason not in draft.reasons.all():
                return Response(
                    {'error': 'Reason does not belong to this draft'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create feedback for this draft
            feedback, created = UserFeedback.objects.get_or_create(
                draft=draft,
                action='accept',  # Default action for quick ratings
                defaults={'reason': 'Quick rating feedback'}
            )
            
            # Create or update the rating
            rating_obj, rating_created = ReasonRating.objects.get_or_create(
                feedback=feedback,
                reason=reason,
                defaults={'liked': rating == 'thumbs_up'}
            )
            
            if not rating_created:
                # Update existing rating
                rating_obj.liked = rating == 'thumbs_up'
                rating_obj.save()
            
            return Response({
                'feedback_id': feedback.id,
                'reason_id': reason.id,
                'rating': rating,
                'liked': rating == 'thumbs_up',
                'created': rating_created
            }, status=status.HTTP_201_CREATED if rating_created else status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in quick rate reason {reason_id}: {str(e)}")
            return Response(
                {'error': 'Failed to rate reason'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromptLabConfidenceView(PromptLabAPIView):
    """Get confidence metrics for a prompt lab"""
    
    def get(self, request, prompt_lab_id):
        """Get current confidence metrics for prompt lab"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            from app.services.confidence_calculator import ConfidenceCalculator
            
            calculator = ConfidenceCalculator()
            
            # Get or create confidence tracker
            confidence_tracker = calculator.update_session_confidence(prompt_lab)
            
            # Calculate current metrics
            user_confidence = calculator.calculate_user_confidence(prompt_lab)
            system_confidence = calculator.calculate_system_confidence(prompt_lab)
            
            # Check threshold status
            is_learning_sufficient = confidence_tracker.is_learning_sufficient()
            should_continue_learning = confidence_tracker.should_continue_learning()
            
            response_data = {
                'prompt_lab_id': str(prompt_lab.id),
                'user_confidence': user_confidence,
                'system_confidence': system_confidence,
                'confidence_trend': confidence_tracker.confidence_trend,
                'is_learning_sufficient': is_learning_sufficient,
                'should_continue_learning': should_continue_learning,
                'confidence_breakdown': {
                    'feedback_consistency_score': confidence_tracker.feedback_consistency_score,
                    'reasoning_alignment_score': confidence_tracker.reasoning_alignment_score,
                    'total_feedback_count': confidence_tracker.total_feedback_count,
                    'consistent_feedback_streak': confidence_tracker.consistent_feedback_streak
                },
                'thresholds': {
                    'user_confidence_threshold': PromptLabConfidence.USER_CONFIDENCE_THRESHOLD,
                    'system_confidence_threshold': PromptLabConfidence.SYSTEM_CONFIDENCE_THRESHOLD,
                    'combined_confidence_threshold': PromptLabConfidence.COMBINED_CONFIDENCE_THRESHOLD
                },
                'last_calculated': confidence_tracker.last_calculated.isoformat()
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error getting prompt lab confidence {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to get confidence metrics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecalculateConfidenceView(PromptLabAPIView):
    """Manually trigger confidence recalculation"""
    
    def post(self, request, prompt_lab_id):
        """Recalculate confidence metrics for prompt lab"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            from app.services.confidence_calculator import ConfidenceCalculator
            
            calculator = ConfidenceCalculator()
            confidence_tracker = calculator.update_session_confidence(prompt_lab)
            
            response_data = {
                'prompt_lab_id': str(prompt_lab.id),
                'user_confidence': confidence_tracker.user_confidence,
                'system_confidence': confidence_tracker.system_confidence,
                'confidence_trend': confidence_tracker.confidence_trend,
                'calculation_timestamp': confidence_tracker.last_calculated.isoformat(),
                'is_learning_sufficient': confidence_tracker.is_learning_sufficient(),
                'should_continue_learning': confidence_tracker.should_continue_learning()
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error recalculating confidence {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to recalculate confidence'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConfidenceHistoryView(PromptLabAPIView):
    """Get confidence tracking history for a prompt lab"""
    
    def get(self, request, prompt_lab_id):
        """Get historical confidence data"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            # For now, return current snapshot as history
            # In future, could track historical confidence changes
            confidence_tracker = PromptLabConfidence.objects.filter(prompt_lab=prompt_lab).first()
            
            if not confidence_tracker:
                # No confidence data yet
                history = []
            else:
                history = [{
                    'timestamp': confidence_tracker.last_calculated.isoformat(),
                    'user_confidence': confidence_tracker.user_confidence,
                    'system_confidence': confidence_tracker.system_confidence,
                    'feedback_count': confidence_tracker.total_feedback_count
                }]
            
            return Response({
                'prompt_lab_id': str(prompt_lab.id),
                'confidence_history': history
            })
            
        except Exception as e:
            logger.error(f"Error getting confidence history {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to get confidence history'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConfidenceThresholdsView(PromptLabAPIView):
    """Get and update confidence thresholds"""
    
    def get(self, request, prompt_lab_id):
        """Get current confidence thresholds"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        return Response({
            'prompt_lab_id': str(prompt_lab.id),
            'user_confidence_threshold': PromptLabConfidence.USER_CONFIDENCE_THRESHOLD,
            'system_confidence_threshold': PromptLabConfidence.SYSTEM_CONFIDENCE_THRESHOLD,
            'combined_confidence_threshold': PromptLabConfidence.COMBINED_CONFIDENCE_THRESHOLD
        })
    
    def post(self, request, prompt_lab_id):
        """Update confidence thresholds (for future customization)"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        data = request.data
        
        # Validate threshold values
        user_threshold = data.get('user_confidence_threshold')
        system_threshold = data.get('system_confidence_threshold')
        
        if user_threshold is not None and (user_threshold < 0 or user_threshold > 1):
            return Response(
                {'error': 'user_confidence_threshold must be between 0 and 1'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if system_threshold is not None and (system_threshold < 0 or system_threshold > 1):
            return Response(
                {'error': 'system_confidence_threshold must be between 0 and 1'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # For now, just return the current values as this is a future feature
        # In future, could store per-prompt lab custom thresholds
        return Response({
            'prompt_lab_id': str(prompt_lab.id),
            'user_confidence_threshold': PromptLabConfidence.USER_CONFIDENCE_THRESHOLD,
            'system_confidence_threshold': PromptLabConfidence.SYSTEM_CONFIDENCE_THRESHOLD,
            'combined_confidence_threshold': PromptLabConfidence.COMBINED_CONFIDENCE_THRESHOLD,
            'message': 'Custom thresholds will be supported in future version'
        }, status=status.HTTP_200_OK)


class ExtractPreferencesView(PromptLabAPIView):
    """Extract user preferences from feedback patterns"""
    
    def post(self, request, prompt_lab_id):
        """Trigger preference extraction for a prompt lab"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            from app.services.preference_extractor import PreferenceExtractor
            
            extractor = PreferenceExtractor()
            
            # Extract preferences from all sources
            extracted_preferences = extractor.extract_all_preferences(prompt_lab)
            
            # Save high-confidence preferences to database
            saved_count = 0
            high_confidence_count = 0
            categories_discovered = set()
            
            for pref in extracted_preferences:
                categories_discovered.add(pref['category'])
                
                if pref['confidence'] >= 0.7:
                    high_confidence_count += 1
                
                # Save to database if confidence is reasonable
                if pref['confidence'] >= 0.5:
                    # Check if similar preference already exists
                    existing = ExtractedPreference.objects.filter(
                        prompt_lab=prompt_lab,
                        preference_category=pref['category'],
                        is_active=True
                    ).first()
                    
                    if existing:
                        # Update if new confidence is higher
                        if pref['confidence'] > existing.confidence_score:
                            existing.preference_text = pref['text']
                            existing.confidence_score = pref['confidence']
                            existing.supporting_evidence = pref.get('evidence', '')
                            existing.save()
                    else:
                        # Create new extracted preference
                        ExtractedPreference.objects.create(
                            prompt_lab=prompt_lab,
                            source_feedback_ids=pref.get('sources', []),
                            preference_category=pref['category'],
                            preference_text=pref['text'],
                            confidence_score=pref['confidence'],
                            extraction_method='multi_source_analysis',
                            supporting_evidence=pref.get('evidence', 'Extracted from feedback analysis')
                        )
                        saved_count += 1
            
            return Response({
                'prompt_lab_id': str(prompt_lab.id),
                'extracted_preferences': extracted_preferences,
                'extraction_summary': {
                    'total_preferences_found': len(extracted_preferences),
                    'high_confidence_count': high_confidence_count,
                    'preferences_saved': saved_count,
                    'categories_discovered': list(categories_discovered)
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error extracting preferences for prompt lab {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to extract preferences'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromptLabPreferencesView(PromptLabAPIView):
    """Get all preferences for a prompt lab"""
    
    def get(self, request, prompt_lab_id):
        """Get manual and extracted preferences for prompt lab"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            # Get manual preferences
            manual_prefs = UserPreference.objects.filter(
                prompt_lab=prompt_lab,
                is_active=True
            ).order_by('-updated_at')
            
            # Get extracted preferences
            extracted_prefs = ExtractedPreference.objects.filter(
                prompt_lab=prompt_lab,
                is_active=True
            ).order_by('-confidence_score')
            
            manual_preferences_data = [
                {
                    'id': pref.id,
                    'key': pref.key,
                    'value': pref.value,
                    'description': pref.description,
                    'created_at': pref.created_at.isoformat(),
                    'updated_at': pref.updated_at.isoformat()
                } for pref in manual_prefs
            ]
            
            extracted_preferences_data = [
                {
                    'id': pref.id,
                    'category': pref.preference_category,
                    'text': pref.preference_text,
                    'confidence_score': pref.confidence_score,
                    'extraction_method': pref.extraction_method,
                    'supporting_evidence': pref.supporting_evidence,
                    'auto_extracted': pref.auto_extracted,
                    'created_at': pref.created_at.isoformat(),
                    'updated_at': pref.updated_at.isoformat()
                } for pref in extracted_prefs
            ]
            
            return Response({
                'prompt_lab_id': str(prompt_lab.id),
                'manual_preferences': manual_preferences_data,
                'extracted_preferences': extracted_preferences_data
            })
            
        except Exception as e:
            logger.error(f"Error getting prompt lab preferences {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to get prompt lab preferences'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdatePromptLabPreferenceView(PromptLabAPIView):
    """Add or update a manual preference for a prompt lab"""
    
    def post(self, request, prompt_lab_id):
        """Create or update a manual preference"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        data = request.data
        
        # Validate required fields
        key = data.get('key', '').strip()
        value = data.get('value', '').strip()
        
        if not key:
            return Response(
                {'error': 'Preference key is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not value:
            return Response(
                {'error': 'Preference value is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            description = data.get('description', '').strip()
            
            # Get or create preference
            preference, created = UserPreference.objects.get_or_create(
                prompt_lab=prompt_lab,
                key=key,
                defaults={
                    'value': value,
                    'description': description
                }
            )
            
            if not created:
                # Update existing preference
                preference.value = value
                preference.description = description
                preference.is_active = True
                preference.save()
            
            return Response({
                'preference_id': preference.id,
                'key': preference.key,
                'value': preference.value,
                'description': preference.description,
                'created': created,
                'updated_at': preference.updated_at.isoformat()
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating prompt lab preference {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to update preference'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConvergenceAssessmentView(PromptLabAPIView):
    """Get convergence assessment for a prompt lab"""
    
    def get(self, request, prompt_lab_id):
        """Get comprehensive convergence assessment"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            from app.services.convergence_detector import ConvergenceDetector
            
            detector = ConvergenceDetector()
            
            # Get convergence assessment
            assessment = detector.assess_convergence(prompt_lab)
            
            # Get optimization history for context
            optimization_history = self._get_optimization_history(prompt_lab)
            performance_trend = self._get_performance_trend(prompt_lab)
            
            response_data = {
                'prompt_lab_id': str(prompt_lab.id),
                'convergence_assessment': assessment,
                'optimization_history': optimization_history,
                'performance_trend': performance_trend,
                'prompt_lab_stats': {
                    'optimization_iterations': prompt_lab.optimization_iterations,
                    'total_feedback_collected': prompt_lab.total_feedback_collected,
                    'created_at': prompt_lab.created_at.isoformat(),
                    'updated_at': prompt_lab.updated_at.isoformat()
                }
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error getting convergence assessment for prompt lab {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to get convergence assessment'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_optimization_history(self, prompt_lab):
        """Get optimization iteration history"""
        try:
            prompts = SystemPrompt.objects.filter(
                session=prompt_lab
            ).order_by('version')
            
            return [
                {
                    'version': prompt.version,
                    'performance_score': prompt.performance_score,
                    'created_at': prompt.created_at.isoformat(),
                    'is_active': prompt.is_active
                } for prompt in prompts
            ]
        except Exception:
            return []
    
    def _get_performance_trend(self, prompt_lab):
        """Calculate performance trend over time"""
        try:
            prompts_with_scores = SystemPrompt.objects.filter(
                prompt_lab=prompt_lab,
                performance_score__isnull=False
            ).order_by('version')
            
            if prompts_with_scores.count() < 2:
                return {'trend': 'insufficient_data'}
            
            scores = [p.performance_score for p in prompts_with_scores]
            
            # Simple trend calculation
            first_half = scores[:len(scores)//2]
            second_half = scores[len(scores)//2:]
            
            if first_half and second_half:
                avg_first = sum(first_half) / len(first_half)
                avg_second = sum(second_half) / len(second_half)
                trend_value = avg_second - avg_first
                
                if trend_value > 0.05:
                    trend = 'improving'
                elif trend_value < -0.05:
                    trend = 'declining'
                else:
                    trend = 'stable'
                
                return {
                    'trend': trend,
                    'trend_value': round(trend_value, 3),
                    'first_half_avg': round(avg_first, 3),
                    'second_half_avg': round(avg_second, 3)
                }
            
            return {'trend': 'insufficient_data'}
            
        except Exception:
            return {'trend': 'error'}


class ForceConvergenceView(PromptLabAPIView):
    """Force convergence for a prompt lab"""
    
    def post(self, request, prompt_lab_id):
        """Manually force convergence"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        data = request.data
        
        # Validate required fields
        reason = data.get('reason', '').strip()
        if not reason:
            return Response(
                {'error': 'Reason for forcing convergence is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        override_confidence = data.get('override_confidence_check', False)
        if not isinstance(override_confidence, bool):
            return Response(
                {'error': 'override_confidence_check must be a boolean'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from app.services.convergence_detector import ConvergenceDetector
            
            detector = ConvergenceDetector()
            result = detector.force_convergence(prompt_lab, reason, override_confidence)
            
            if result.get('success'):
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': result.get('error', 'Failed to force convergence')}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Exception as e:
            logger.error(f"Error forcing convergence for prompt lab {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to force convergence'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConvergenceHistoryView(PromptLabAPIView):
    """Get convergence assessment history for a prompt lab"""
    
    def get(self, request, prompt_lab_id):
        """Get historical convergence assessments"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            from app.services.convergence_detector import ConvergenceDetector
            
            detector = ConvergenceDetector()
            
            # Get convergence history
            history = detector.get_convergence_history(prompt_lab)
            
            # Create assessment timeline
            timeline = []
            for assessment in history:
                timeline.append({
                    'timestamp': assessment.get('timestamp'),
                    'converged': assessment.get('converged'),
                    'confidence_score': assessment.get('confidence_score'),
                    'key_factors_met': sum(1 for v in assessment.get('factors', {}).values() if v)
                })
            
            response_data = {
                'prompt_lab_id': str(prompt_lab.id),
                'convergence_history': history,
                'assessment_timeline': timeline,
                'summary': {
                    'total_assessments': len(history),
                    'ever_converged': any(a.get('converged', False) for a in history),
                    'latest_convergence_state': history[0].get('converged', False) if history else False
                }
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error getting convergence history for prompt lab {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to get convergence history'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromptLabImportView(PromptLabAPIView):
    """Import prompt lab data from exported JSON"""
    
    def post(self, request):
        """Import a prompt lab from exported data"""
        try:
            data = request.data
            options = data.get('options', {})
            
            # Extract import options
            conflict_resolution = options.get('conflict_resolution', 'rename')
            
            # Import the prompt lab
            from app.services.promptlab_importer import PromptLabImporter, ImportValidationError
            importer = PromptLabImporter()
            
            prompt_lab = importer.import_session(data, handle_conflicts=conflict_resolution)
            
            # Get summary of what was imported
            summary = {
                'prompt_lab_id': str(prompt_lab.id),
                'prompt_lab_name': prompt_lab.name,
                'imported_items': []
            }
            
            # Check what was imported
            if prompt_lab.prompts.exists():
                summary['imported_items'].append('prompts')
                summary['prompts_count'] = prompt_lab.prompts.count()
            
            if prompt_lab.preferences.exists():
                summary['imported_items'].append('preferences')
                summary['preferences_count'] = prompt_lab.preferences.count()
            
            if prompt_lab.emails.exists():
                summary['imported_items'].append('emails')
                summary['emails_count'] = prompt_lab.emails.count()
            
            return Response(summary, status=status.HTTP_201_CREATED)
            
        except ImportValidationError as e:
            return Response(
                {'error': f'Import validation failed: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error importing prompt lab: {str(e)}")
            return Response(
                {'error': 'Failed to import prompt lab data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """Preview what would be imported from the provided data"""
        try:
            data = request.query_params.get('data')
            if not data:
                return Response(
                    {'error': 'No data provided for preview'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            import json
            try:
                import_data = json.loads(data)
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Invalid JSON data'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from app.services.promptlab_importer import PromptLabImporter, ImportValidationError
            importer = PromptLabImporter()
            
            summary = importer.get_import_summary(import_data)
            return Response(summary)
            
        except ImportValidationError as e:
            return Response(
                {'error': f'Preview validation failed: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error previewing import: {str(e)}")
            return Response(
                {'error': 'Failed to preview import data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromptLabColdStartView(PromptLabAPIView):
    """Manage cold start for prompt labs"""
    
    def post(self, request, prompt_lab_id):
        """Trigger cold start initialization for a prompt lab"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            from app.services.cold_start_manager import ColdStartManager
            manager = ColdStartManager()
            
            # Initialize cold start
            result = manager.initialize_cold_start(prompt_lab)
            
            if result.success:
                # Get current status
                status_info = manager.get_cold_start_status(prompt_lab)
                
                return Response({
                    'status': 'success',
                    'emails_generated': result.emails_generated,
                    'cold_start_active': status_info['is_cold_start_active'],
                    'progress_percentage': status_info['progress_percentage']
                })
            else:
                return Response({
                    'status': 'failed',
                    'error': result.error_message
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error initializing cold start for prompt lab {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to initialize cold start'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request, prompt_lab_id):
        """Get cold start status for a prompt lab"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            from app.services.cold_start_manager import ColdStartManager
            manager = ColdStartManager()
            
            status_info = manager.get_cold_start_status(prompt_lab)
            
            return Response(status_info)
            
        except Exception as e:
            logger.error(f"Error getting cold start status for prompt lab {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to get cold start status'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromptLabApplyPreferencesView(PromptLabAPIView):
    """Apply learned preferences from cold start"""
    
    def post(self, request, prompt_lab_id):
        """Analyze cold start feedback and apply learned preferences"""
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id, is_active=True)
        
        try:
            from app.services.cold_start_manager import ColdStartManager
            manager = ColdStartManager()
            
            # Analyze feedback to learn preferences
            preferences = manager.analyze_cold_start_feedback(prompt_lab)
            
            if not preferences:
                return Response({
                    'status': 'no_preferences',
                    'message': 'No clear preferences identified yet'
                })
            
            # Apply learned preferences
            new_prompt = manager.apply_learned_preferences(prompt_lab, preferences)
            
            if new_prompt:
                return Response({
                    'status': 'success',
                    'preferences_applied': preferences,
                    'new_prompt_version': new_prompt.version,
                    'new_prompt_content': new_prompt.content
                })
            else:
                return Response({
                    'status': 'failed',
                    'error': 'Failed to apply preferences'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error applying preferences for prompt lab {prompt_lab_id}: {str(e)}")
            return Response(
                {'error': 'Failed to apply learned preferences'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
