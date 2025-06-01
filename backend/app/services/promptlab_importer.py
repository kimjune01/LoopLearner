"""
PromptLab Import Service

Handles importing prompt lab data from exported JSON files.
Supports conflict resolution and data validation.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db import transaction

from core.models import (
    PromptLab, SystemPrompt, UserPreference, Email, Draft, DraftReason,
    UserFeedback, PromptLabConfidence, ExtractedPreference
)

logger = logging.getLogger(__name__)


class ImportValidationError(Exception):
    """Raised when import data validation fails"""
    pass


class PromptLabImporter:
    """Service for importing prompt lab data from export files"""
    
    SUPPORTED_VERSIONS = ['1.0']
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def import_session(
        self, 
        export_data: Dict[str, Any], 
        handle_conflicts: str = 'rename'
    ) -> PromptLab:
        """
        Import a prompt lab from exported data
        
        Args:
            export_data: The exported prompt lab data
            handle_conflicts: How to handle name conflicts ('rename', 'error', 'replace')
            
        Returns:
            The imported PromptLab object
            
        Raises:
            ImportValidationError: If the data is invalid
        """
        # Validate the export data
        self._validate_export_data(export_data)
        
        with transaction.atomic():
            # Create the prompt lab
            prompt_lab = self._create_prompt_lab(export_data['session'], handle_conflicts)
            
            # Import prompts
            if 'prompts' in export_data:
                self._import_prompts(prompt_lab, export_data['prompts'])
            
            # Import preferences  
            if 'preferences' in export_data:
                self._import_preferences(prompt_lab, export_data['preferences'])
            
            # Import emails
            if 'emails' in export_data:
                self._import_emails(prompt_lab, export_data['emails'])
            
            self.logger.info(f"Successfully imported prompt lab '{prompt_lab.name}' (ID: {prompt_lab.id})")
            return prompt_lab
    
    def _validate_export_data(self, data: Dict[str, Any]) -> None:
        """Validate the export data structure and content"""
        # Check version
        version = data.get('version')
        if version not in self.SUPPORTED_VERSIONS:
            raise ImportValidationError(f"Unsupported export version: {version}")
        
        # Check required top-level fields
        if 'session' not in data:
            raise ImportValidationError("Export data missing required 'session' field")
        
        # Validate session data
        session_data = data['session']
        if not isinstance(session_data, dict):
            raise ImportValidationError("PromptLab data must be a dictionary")
        
        if 'name' not in session_data:
            raise ImportValidationError("PromptLab data missing required 'name' field")
        
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
        """Validate prompt data structure"""
        if not isinstance(prompts, list):
            raise ImportValidationError("Prompts must be a list")
        
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, dict):
                raise ImportValidationError(f"Prompt {i} must be a dictionary")
            
            # Check required fields
            if 'content' not in prompt:
                raise ImportValidationError(f"Prompt {i} missing 'content' field")
            
            if 'version' not in prompt:
                raise ImportValidationError(f"Prompt {i} missing 'version' field")
    
    def _validate_preferences_data(self, preferences: List[Dict[str, Any]]) -> None:
        """Validate preference data structure"""
        if not isinstance(preferences, list):
            raise ImportValidationError("Preferences must be a list")
        
        for i, pref in enumerate(preferences):
            if not isinstance(pref, dict):
                raise ImportValidationError(f"Preference {i} must be a dictionary")
            
            # Check required fields
            if 'key' not in pref:
                raise ImportValidationError(f"Preference {i} missing 'key' field")
            
            if 'value' not in pref:
                raise ImportValidationError(f"Preference {i} missing 'value' field")
    
    def _validate_emails_data(self, emails: List[Dict[str, Any]]) -> None:
        """Validate email data structure"""
        if not isinstance(emails, list):
            raise ImportValidationError("Emails must be a list")
        
        for i, email in enumerate(emails):
            if not isinstance(email, dict):
                raise ImportValidationError(f"Email {i} must be a dictionary")
            
            if 'subject' not in email:
                raise ImportValidationError(f"Email {i} missing 'subject' field")
            
            if 'body' not in email:
                raise ImportValidationError(f"Email {i} missing 'body' field")
    
    def _create_prompt_lab(self, session_data: Dict[str, Any], handle_conflicts: str) -> PromptLab:
        """Create the prompt lab, handling name conflicts"""
        name = session_data['name']
        description = session_data.get('description', '')
        
        # Check for existing prompt lab with same name
        if PromptLab.objects.filter(name=name, is_active=True).exists():
            if handle_conflicts == 'error':
                raise ImportValidationError(f"PromptLab with name '{name}' already exists")
            elif handle_conflicts == 'rename':
                name = self._generate_unique_name(name)
            elif handle_conflicts == 'replace':
                # Deactivate existing prompt lab
                PromptLab.objects.filter(name=name, is_active=True).update(is_active=False)
        
        # Create the new prompt lab
        prompt_lab = PromptLab.objects.create(
            name=name,
            description=description,
            optimization_iterations=session_data.get('optimization_iterations', 0),
            total_emails_processed=session_data.get('total_emails_processed', 0),
            total_feedback_collected=session_data.get('total_feedback_collected', 0)
        )
        
        return prompt_lab
    
    def _generate_unique_name(self, base_name: str) -> str:
        """Generate a unique prompt lab name by appending a number"""
        counter = 1
        new_name = f"{base_name} (Import {counter})"
        
        while PromptLab.objects.filter(name=new_name, is_active=True).exists():
            counter += 1
            new_name = f"{base_name} (Import {counter})"
        
        return new_name
    
    def _import_prompts(self, prompt_lab: PromptLab, prompts_data: List[Dict[str, Any]]) -> None:
        """Import system prompts for the prompt lab"""
        for prompt_data in prompts_data:
            SystemPrompt.objects.create(
                prompt_lab=prompt_lab,
                content=prompt_data['content'],
                version=prompt_data['version'],
                is_active=prompt_data.get('is_active', False),
                performance_score=prompt_data.get('performance_score', 0.0)
            )
        
        self.logger.info(f"Imported {len(prompts_data)} prompts for prompt lab {prompt_lab.name}")
    
    def _import_preferences(self, prompt_lab: PromptLab, preferences_data: List[Dict[str, Any]]) -> None:
        """Import user preferences for the prompt lab"""
        for pref_data in preferences_data:
            UserPreference.objects.create(
                prompt_lab=prompt_lab,
                key=pref_data['key'],
                value=pref_data['value'],
                description=pref_data.get('description', ''),
                is_active=pref_data.get('is_active', True)
            )
        
        self.logger.info(f"Imported {len(preferences_data)} preferences for prompt lab {prompt_lab.name}")
    
    def _import_emails(self, prompt_lab: PromptLab, emails_data: List[Dict[str, Any]]) -> None:
        """Import emails for the prompt lab"""
        for email_data in emails_data:
            Email.objects.create(
                prompt_lab=prompt_lab,
                subject=email_data['subject'],
                body=email_data['body'],
                sender=email_data.get('sender', 'unknown@example.com'),
                scenario_type=email_data.get('scenario_type', 'general'),
                is_synthetic=email_data.get('is_synthetic', True)
            )
        
        self.logger.info(f"Imported {len(emails_data)} emails for prompt lab {prompt_lab.name}")
    
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
        if PromptLab.objects.filter(name=name, is_active=True).exists():
            summary['has_name_conflict'] = True
            summary['suggested_name'] = self._generate_unique_name(name)
        else:
            summary['has_name_conflict'] = False
        
        return summary


class SystemImporter:
    """Service for importing complete system state including multiple prompt labs"""
    
    def __init__(self):
        self.promptlab_importer = PromptLabImporter()
        self.logger = logging.getLogger(__name__)
    
    def import_system_state(
        self, 
        system_data: Dict[str, Any], 
        preserve_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Import complete system state including multiple prompt labs
        
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
            
            # Import prompt labs
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
                        
                        self.promptlab_importer.import_session(
                            formatted_data, 
                            handle_conflicts='rename'
                        )
                        results['imported_sessions'] += 1
                        
                    except Exception as e:
                        error_msg = f"Failed to import prompt lab '{session_data.get('name', 'unknown')}': {str(e)}"
                        results['errors'].append(error_msg)
                        self.logger.error(error_msg)
        
        self.logger.info(f"System import completed: {results}")
        return results
    
    def _clear_existing_data(self) -> None:
        """Clear existing system data"""
        PromptLab.objects.filter(is_active=True).update(is_active=False)
        UserPreference.objects.filter(prompt_lab__isnull=True).delete()
    
    def _import_global_preferences(self, preferences_data: List[Dict[str, Any]]) -> int:
        """Import global (prompt lab-independent) preferences"""
        count = 0
        for pref_data in preferences_data:
            UserPreference.objects.update_or_create(
                prompt_lab=None,  # Global preference
                key=pref_data['key'],
                defaults={
                    'value': pref_data['value'],
                    'description': pref_data.get('description', ''),
                    'is_active': pref_data.get('is_active', True)
                }
            )
            count += 1
        
        return count