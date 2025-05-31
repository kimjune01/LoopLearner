"""
Session Import Service

Handles importing session data from exported JSON files.
Supports conflict resolution and data validation.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db import transaction

from core.models import (
    Session, SystemPrompt, UserPreference, Email, Draft, DraftReason,
    UserFeedback, SessionConfidence, ExtractedPreference
)

logger = logging.getLogger(__name__)


class ImportValidationError(Exception):
    """Raised when import data validation fails"""
    pass


class SessionImporter:
    """Service for importing session data from export files"""
    
    SUPPORTED_VERSIONS = ['1.0']
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def import_session(
        self, 
        export_data: Dict[str, Any], 
        handle_conflicts: str = 'rename'
    ) -> Session:
        """
        Import a session from exported data
        
        Args:
            export_data: The exported session data
            handle_conflicts: How to handle name conflicts ('rename', 'error', 'replace')
            
        Returns:
            The imported Session object
            
        Raises:
            ImportValidationError: If the data is invalid
        """
        # Validate the export data
        self._validate_export_data(export_data)
        
        with transaction.atomic():
            # Create the session
            session = self._create_session(export_data['session'], handle_conflicts)
            
            # Import prompts
            if 'prompts' in export_data:
                self._import_prompts(session, export_data['prompts'])
            
            # Import preferences  
            if 'preferences' in export_data:
                self._import_preferences(session, export_data['preferences'])
            
            # Import emails
            if 'emails' in export_data:
                self._import_emails(session, export_data['emails'])
            
            self.logger.info(f"Successfully imported session '{session.name}' (ID: {session.id})")
            return session
    
    def _validate_export_data(self, data: Dict[str, Any]) -> None:
        """Validate that export data has the correct structure and required fields"""
        if not data:
            raise ImportValidationError("Import data is empty or None")
        
        # Check version
        version = data.get('version')
        if not version:
            raise ImportValidationError("Export data missing version field")
        
        if version not in self.SUPPORTED_VERSIONS:
            raise ImportValidationError(f"Unsupported export format version: {version}")
        
        # Check required session data
        if 'session' not in data:
            raise ImportValidationError("Export data missing session information")
        
        session_data = data['session']
        if not isinstance(session_data, dict):
            raise ImportValidationError("Session data must be a dictionary")
        
        if 'name' not in session_data:
            raise ImportValidationError("Session data missing required 'name' field")
        
        # Validate prompts if present
        if 'prompts' in data:
            self._validate_prompts_data(data['prompts'])
        
        # Validate preferences if present
        if 'preferences' in data:
            self._validate_preferences_data(data['preferences'])
        
        # Validate emails if present
        if 'emails' in data:
            self._validate_emails_data(data['emails'])
    
    def _validate_prompts_data(self, prompts: List[Dict[str, Any]]) -> None:
        """Validate prompts data structure"""
        if not isinstance(prompts, list):
            raise ImportValidationError("Prompts data must be a list")
        
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, dict):
                raise ImportValidationError(f"Prompt {i} must be a dictionary")
            
            if 'version' not in prompt:
                raise ImportValidationError(f"Prompt {i} missing 'version' field")
            
            if 'content' not in prompt:
                raise ImportValidationError(f"Prompt {i} missing 'content' field")
            
            # Validate data types
            try:
                int(prompt['version'])
            except (ValueError, TypeError):
                raise ImportValidationError(f"Prompt {i} version must be an integer")
            
            if not isinstance(prompt['content'], str):
                raise ImportValidationError(f"Prompt {i} content must be a string")
    
    def _validate_preferences_data(self, preferences: List[Dict[str, Any]]) -> None:
        """Validate preferences data structure"""
        if not isinstance(preferences, list):
            raise ImportValidationError("Preferences data must be a list")
        
        for i, pref in enumerate(preferences):
            if not isinstance(pref, dict):
                raise ImportValidationError(f"Preference {i} must be a dictionary")
            
            if 'key' not in pref:
                raise ImportValidationError(f"Preference {i} missing 'key' field")
            
            if 'value' not in pref:
                raise ImportValidationError(f"Preference {i} missing 'value' field")
    
    def _validate_emails_data(self, emails: List[Dict[str, Any]]) -> None:
        """Validate emails data structure"""
        if not isinstance(emails, list):
            raise ImportValidationError("Emails data must be a list")
        
        for i, email in enumerate(emails):
            if not isinstance(email, dict):
                raise ImportValidationError(f"Email {i} must be a dictionary")
            
            if 'subject' not in email:
                raise ImportValidationError(f"Email {i} missing 'subject' field")
            
            if 'body' not in email:
                raise ImportValidationError(f"Email {i} missing 'body' field")
    
    def _create_session(self, session_data: Dict[str, Any], handle_conflicts: str) -> Session:
        """Create the session, handling name conflicts"""
        name = session_data['name']
        description = session_data.get('description', '')
        
        # Check for existing session with same name
        if Session.objects.filter(name=name, is_active=True).exists():
            if handle_conflicts == 'error':
                raise ImportValidationError(f"Session with name '{name}' already exists")
            elif handle_conflicts == 'rename':
                name = self._generate_unique_name(name)
            elif handle_conflicts == 'replace':
                # Deactivate existing session
                Session.objects.filter(name=name, is_active=True).update(is_active=False)
        
        # Create the new session
        session = Session.objects.create(
            name=name,
            description=description,
            optimization_iterations=session_data.get('optimization_iterations', 0),
            total_emails_processed=session_data.get('total_emails_processed', 0),
            total_feedback_collected=session_data.get('total_feedback_collected', 0)
        )
        
        return session
    
    def _generate_unique_name(self, base_name: str) -> str:
        """Generate a unique session name by appending a number"""
        counter = 1
        new_name = f"{base_name} (Import {counter})"
        
        while Session.objects.filter(name=new_name, is_active=True).exists():
            counter += 1
            new_name = f"{base_name} (Import {counter})"
        
        return new_name
    
    def _import_prompts(self, session: Session, prompts_data: List[Dict[str, Any]]) -> None:
        """Import system prompts for the session"""
        for prompt_data in prompts_data:
            SystemPrompt.objects.create(
                session=session,
                content=prompt_data['content'],
                version=prompt_data['version'],
                is_active=prompt_data.get('is_active', False),
                performance_score=prompt_data.get('performance_score', 0.0)
            )
        
        self.logger.info(f"Imported {len(prompts_data)} prompts for session {session.name}")
    
    def _import_preferences(self, session: Session, preferences_data: List[Dict[str, Any]]) -> None:
        """Import user preferences for the session"""
        for pref_data in preferences_data:
            UserPreference.objects.create(
                session=session,
                key=pref_data['key'],
                value=pref_data['value'],
                description=pref_data.get('description', ''),
                is_active=pref_data.get('is_active', True)
            )
        
        self.logger.info(f"Imported {len(preferences_data)} preferences for session {session.name}")
    
    def _import_emails(self, session: Session, emails_data: List[Dict[str, Any]]) -> None:
        """Import emails for the session"""
        for email_data in emails_data:
            Email.objects.create(
                session=session,
                subject=email_data['subject'],
                body=email_data['body'],
                sender=email_data.get('sender', 'unknown@example.com'),
                scenario_type=email_data.get('scenario_type', 'general'),
                is_synthetic=email_data.get('is_synthetic', True)
            )
        
        self.logger.info(f"Imported {len(emails_data)} emails for session {session.name}")
    
    def get_import_summary(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of what would be imported without actually importing"""
        self._validate_export_data(export_data)
        
        summary = {
            'session_name': export_data['session']['name'],
            'session_description': export_data['session'].get('description', ''),
            'prompts_count': len(export_data.get('prompts', [])),
            'preferences_count': len(export_data.get('preferences', [])),
            'emails_count': len(export_data.get('emails', [])),
            'export_version': export_data.get('version'),
            'export_timestamp': export_data.get('export_timestamp')
        }
        
        # Check for potential conflicts
        name = export_data['session']['name']
        if Session.objects.filter(name=name, is_active=True).exists():
            summary['has_name_conflict'] = True
            summary['suggested_name'] = self._generate_unique_name(name)
        else:
            summary['has_name_conflict'] = False
        
        return summary


class SystemImporter:
    """Service for importing complete system state including multiple sessions"""
    
    def __init__(self):
        self.session_importer = SessionImporter()
        self.logger = logging.getLogger(__name__)
    
    def import_system_state(
        self, 
        system_data: Dict[str, Any], 
        preserve_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Import complete system state including multiple sessions
        
        Args:
            system_data: The exported system data
            preserve_existing: Whether to preserve existing data or replace it
            
        Returns:
            Dict with import results summary
        """
        results = {
            'imported_sessions': 0,
            'imported_global_preferences': 0,
            'errors': [],
            'warnings': []
        }
        
        with transaction.atomic():
            # Clear existing data if not preserving
            if not preserve_existing:
                self._clear_existing_data()
                results['warnings'].append('Existing data was cleared before import')
            
            # Import global preferences
            if 'global_preferences' in system_data:
                count = self._import_global_preferences(system_data['global_preferences'])
                results['imported_global_preferences'] = count
            
            # Import sessions
            if 'sessions' in system_data:
                for session_data in system_data['sessions']:
                    try:
                        # Format session data for SessionImporter
                        formatted_data = {
                            'session': session_data,
                            'prompts': session_data.get('prompts', []),
                            'preferences': session_data.get('preferences', []),
                            'emails': session_data.get('emails', []),
                            'version': system_data.get('version', '1.0')
                        }
                        
                        self.session_importer.import_session(
                            formatted_data, 
                            handle_conflicts='rename'
                        )
                        results['imported_sessions'] += 1
                        
                    except Exception as e:
                        error_msg = f"Failed to import session '{session_data.get('name', 'unknown')}': {str(e)}"
                        results['errors'].append(error_msg)
                        self.logger.error(error_msg)
        
        self.logger.info(f"System import completed: {results}")
        return results
    
    def _clear_existing_data(self) -> None:
        """Clear existing system data"""
        Session.objects.filter(is_active=True).update(is_active=False)
        UserPreference.objects.filter(session__isnull=True).delete()
    
    def _import_global_preferences(self, preferences_data: List[Dict[str, Any]]) -> int:
        """Import global (session-independent) preferences"""
        count = 0
        for pref_data in preferences_data:
            UserPreference.objects.update_or_create(
                session=None,  # Global preference
                key=pref_data['key'],
                defaults={
                    'value': pref_data['value'],
                    'description': pref_data.get('description', ''),
                    'is_active': pref_data.get('is_active', True)
                }
            )
            count += 1
        
        return count