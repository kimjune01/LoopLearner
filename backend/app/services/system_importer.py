"""
System Import Service

Enhanced system-wide import functionality that can handle multiple sessions
and global preferences in a single import operation.
"""
import logging
from typing import Dict, Any, List
from django.db import transaction

from core.models import Session, UserPreference
from .session_importer import SessionImporter

logger = logging.getLogger(__name__)


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
            
            # Legacy support: import current_prompt and user_preferences as global
            if 'current_prompt' in system_data or 'user_preferences' in system_data:
                count = self._import_legacy_system_data(system_data)
                results['imported_global_preferences'] += count
            
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
    
    def _import_legacy_system_data(self, system_data: Dict[str, Any]) -> int:
        """Import legacy system export format (current_prompt + user_preferences)"""
        count = 0
        
        # Import legacy user_preferences as global preferences
        if 'user_preferences' in system_data:
            for pref_data in system_data['user_preferences']:
                UserPreference.objects.update_or_create(
                    session=None,
                    key=pref_data['key'],
                    defaults={
                        'value': pref_data['value'],
                        'is_active': pref_data.get('is_active', True)
                    }
                )
                count += 1
        
        # Legacy current_prompt handling could create a default session
        if 'current_prompt' in system_data:
            # Create a default session with the legacy prompt
            from core.models import SystemPrompt
            
            default_session, created = Session.objects.get_or_create(
                name="Imported Legacy Session",
                defaults={'description': 'Session created from legacy system import'}
            )
            
            prompt_data = system_data['current_prompt']
            SystemPrompt.objects.update_or_create(
                session=default_session,
                version=prompt_data.get('version', 1),
                defaults={
                    'content': prompt_data.get('content', 'You are a helpful assistant.'),
                    'is_active': True
                }
            )
        
        return count