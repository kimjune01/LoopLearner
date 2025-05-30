from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils import timezone
from django.db import models
import logging
import uuid

from core.models import Session, SystemPrompt, UserPreference, Email
from core.serializers import SessionSerializer

logger = logging.getLogger(__name__)


class SessionAPIView(APIView):
    """Base class for session-related API views"""
    
    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
        logger.error(f"Session API Error: {str(exc)}")
        return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SessionListView(SessionAPIView):
    """List all sessions and create new sessions"""
    
    def get(self, request):
        """Get all sessions with optional filtering and sorting"""
        # Get query parameters
        search = request.query_params.get('search', '')
        sort_by = request.query_params.get('sort_by', 'updated_at')
        order = request.query_params.get('order', 'desc')
        status_filter = request.query_params.get('status', '')
        
        # Start with all active sessions
        sessions = Session.objects.filter(is_active=True)
        
        # Apply search filter
        if search:
            sessions = sessions.filter(
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
            sessions = sessions.order_by(f'{order_prefix}{sort_by}')
        
        # Serialize and return
        serializer = SessionSerializer(sessions, many=True)
        return Response({
            'sessions': serializer.data,
            'count': sessions.count()
        })
    
    def post(self, request):
        """Create a new session"""
        data = request.data
        
        # Validate required fields
        name = data.get('name', '').strip()
        if not name:
            return Response(
                {'error': 'Session name is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        description = data.get('description', '').strip()
        
        try:
            # Create the session
            session = Session.objects.create(
                name=name,
                description=description
            )
            
            # Create initial system prompt for the session
            initial_prompt_content = data.get('initial_prompt', 
                "You are a helpful email assistant that generates professional and appropriate email responses.")
            
            SystemPrompt.objects.create(
                session=session,
                content=initial_prompt_content,
                version=1,
                is_active=True
            )
            
            # Serialize and return the created session
            serializer = SessionSerializer(session)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return Response(
                {'error': 'Failed to create session'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SessionDetailView(SessionAPIView):
    """Get, update, or delete a specific session"""
    
    def get(self, request, session_id):
        """Get session details with related data"""
        session = get_object_or_404(Session, id=session_id, is_active=True)
        
        # Get additional session statistics
        active_prompt = session.prompts.filter(is_active=True).first()
        recent_emails = session.emails.order_by('-created_at')[:5]
        
        serializer = SessionSerializer(session)
        session_data = serializer.data
        
        # Add additional context
        session_data['active_prompt'] = {
            'id': active_prompt.id if active_prompt else None,
            'version': active_prompt.version if active_prompt else None,
            'content': active_prompt.content if active_prompt else None,
        }
        session_data['recent_emails'] = [
            {
                'id': email.id,
                'subject': email.subject,
                'created_at': email.created_at,
                'scenario_type': email.scenario_type
            } for email in recent_emails
        ]
        
        return Response(session_data)
    
    def put(self, request, session_id):
        """Update session details"""
        session = get_object_or_404(Session, id=session_id, is_active=True)
        
        data = request.data
        
        # Update fields if provided
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return Response(
                    {'error': 'Session name cannot be empty'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            session.name = name
        
        if 'description' in data:
            session.description = data['description'].strip()
        
        try:
            session.save()
            serializer = SessionSerializer(session)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {str(e)}")
            return Response(
                {'error': 'Failed to update session'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, session_id):
        """Soft delete a session"""
        session = get_object_or_404(Session, id=session_id, is_active=True)
        
        try:
            # Soft delete by setting is_active to False
            session.is_active = False
            session.save()
            
            return Response(
                {'message': 'Session deleted successfully'}, 
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return Response(
                {'error': 'Failed to delete session'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SessionExportView(SessionAPIView):
    """Export session data"""
    
    def get(self, request, session_id):
        """Export complete session state"""
        session = get_object_or_404(Session, id=session_id, is_active=True)
        
        try:
            # Get all session-related data
            prompts = session.prompts.all().order_by('version')
            preferences = session.preferences.filter(is_active=True)
            emails = session.emails.all().order_by('created_at')
            
            # Build export data structure
            export_data = {
                'session': {
                    'id': str(session.id),
                    'name': session.name,
                    'description': session.description,
                    'created_at': session.created_at.isoformat(),
                    'updated_at': session.updated_at.isoformat(),
                    'optimization_iterations': session.optimization_iterations,
                    'total_emails_processed': session.total_emails_processed,
                    'total_feedback_collected': session.total_feedback_collected,
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
            logger.error(f"Error exporting session {session_id}: {str(e)}")
            return Response(
                {'error': 'Failed to export session data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SessionDuplicateView(SessionAPIView):
    """Duplicate an existing session"""
    
    def post(self, request, session_id):
        """Create a copy of an existing session"""
        source_session = get_object_or_404(Session, id=session_id, is_active=True)
        
        data = request.data
        new_name = data.get('name', f"{source_session.name} (Copy)")
        new_description = data.get('description', source_session.description)
        
        try:
            # Create new session
            new_session = Session.objects.create(
                name=new_name,
                description=new_description
            )
            
            # Copy system prompts
            for prompt in source_session.prompts.all():
                SystemPrompt.objects.create(
                    session=new_session,
                    content=prompt.content,
                    version=prompt.version,
                    is_active=prompt.is_active,
                    performance_score=prompt.performance_score
                )
            
            # Copy user preferences
            for pref in source_session.preferences.filter(is_active=True):
                UserPreference.objects.create(
                    session=new_session,
                    key=pref.key,
                    value=pref.value,
                    description=pref.description
                )
            
            # Optionally copy emails if requested
            copy_emails = data.get('copy_emails', False)
            if copy_emails:
                for email in source_session.emails.all():
                    Email.objects.create(
                        session=new_session,
                        subject=email.subject,
                        body=email.body,
                        sender=email.sender,
                        scenario_type=email.scenario_type,
                        is_synthetic=email.is_synthetic
                    )
            
            serializer = SessionSerializer(new_session)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error duplicating session {session_id}: {str(e)}")
            return Response(
                {'error': 'Failed to duplicate session'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SessionStatsView(SessionAPIView):
    """Get session statistics and metrics"""
    
    def get(self, request, session_id):
        """Get detailed session statistics"""
        session = get_object_or_404(Session, id=session_id, is_active=True)
        
        try:
            # Calculate various statistics
            prompts_count = session.prompts.count()
            active_prompt = session.prompts.filter(is_active=True).first()
            
            emails_count = session.emails.count()
            synthetic_emails_count = session.emails.filter(is_synthetic=True).count()
            
            # Get draft and feedback statistics
            total_drafts = 0
            total_feedback = 0
            feedback_by_action = {'accept': 0, 'reject': 0, 'edit': 0, 'ignore': 0}
            
            for email in session.emails.all():
                drafts = email.drafts.all()
                total_drafts += drafts.count()
                
                for draft in drafts:
                    feedback_items = draft.feedback.all()
                    total_feedback += feedback_items.count()
                    
                    for feedback in feedback_items:
                        feedback_by_action[feedback.action] += 1
            
            stats = {
                'session_id': str(session.id),
                'session_name': session.name,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
                'optimization_iterations': session.optimization_iterations,
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
                'preferences_count': session.preferences.filter(is_active=True).count(),
            }
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"Error getting session stats {session_id}: {str(e)}")
            return Response(
                {'error': 'Failed to get session statistics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )