"""
Test comprehensive import functionality for  and system state.
This implements missing import capabilities to match export functionality.
"""
import json
import uuid
from datetime import datetime
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone

from core.models import (
    PromptLab, SystemPrompt, UserPreference, Email, Draft, DraftReason, 
    UserFeedback, PromptLabConfidence, ExtractedPreference
)


class PromptLabImportTests(TestCase):
    """Test session import functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test  to export and then import
        self.prompt_lab = PromptLab.objects.create(
            name="Original PromptLab",
            description="Original test session"
        )
        
        # Create system prompt
        self.system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="You are a helpful assistant. {{preferences}}",
            version=1,
            is_active=True
        )
        
        # Create preferences
        self.preference = UserPreference.objects.create(
            prompt_lab=self.prompt_lab,
            key="tone",
            value="professional",
            description="Writing tone preference",
            is_active=True
        )
        
        # Create email
        self.email = Email.objects.create(
            prompt_lab=self.prompt_lab,
            subject="Test Subject",
            body="Test email body",
            sender="test@example.com",
            is_synthetic=True
        )
        
        # Create draft
        self.draft = Draft.objects.create(
            email=self.email,
            content="Test draft response",
            system_prompt=self.system_prompt
        )
        
        # Create feedback
        self.feedback = UserFeedback.objects.create(
            draft=self.draft,
            action="accept",
            reason="",
            edited_content=""
        )
    
    def test_import_session_from_export_data(self):
        """Test importing a  from exported JSON data"""
        from app.services.promptlab_importer import PromptLabImporter
        
        # First export the prompt_lab
        export_data = {
            'session': {
                'name': 'Imported PromptLab',
                'description': 'This is an imported session',
                'optimization_iterations': 3,
                'total_emails_processed': 5,
                'total_feedback_collected': 8,
            },
            'prompts': [
                {
                    'version': 1,
                    'content': 'You are a helpful assistant.',
                    'is_active': False,
                    'performance_score': 0.75,
                },
                {
                    'version': 2,
                    'content': 'You are an expert assistant. {{preferences}}',
                    'is_active': True,
                    'performance_score': 0.85,
                }
            ],
            'preferences': [
                {
                    'key': 'tone',
                    'value': 'friendly',
                    'description': 'Communication tone',
                },
                {
                    'key': 'length',
                    'value': 'concise',
                    'description': 'Response length preference',
                }
            ],
            'emails': [
                {
                    'subject': 'Project Update',
                    'body': 'Can you provide a status update?',
                    'sender': 'manager@company.com',
                    'scenario_type': 'professional',
                    'is_synthetic': False,
                }
            ],
            'export_timestamp': timezone.now().isoformat(),
            'version': '1.0'
        }
        
        # Import the 
        importer = PromptLabImporter()
        imported_session = importer.import_session(export_data)
        
        # Verify  was created
        self.assertIsInstance(imported_session, PromptLab)
        self.assertEqual(imported_session.name, 'Imported PromptLab')
        self.assertEqual(imported_session.description, 'This is an imported session')
        self.assertEqual(imported_session.optimization_iterations, 3)
        self.assertEqual(imported_session.total_emails_processed, 5)
        self.assertEqual(imported_session.total_feedback_collected, 8)
        
        # Verify prompts were imported
        prompts = imported_session.prompts.all().order_by('version')
        self.assertEqual(prompts.count(), 2)
        
        # Check first prompt
        prompt1 = prompts[0]
        self.assertEqual(prompt1.version, 1)
        self.assertEqual(prompt1.content, 'You are a helpful assistant.')
        self.assertFalse(prompt1.is_active)
        self.assertEqual(prompt1.performance_score, 0.75)
        
        # Check second prompt
        prompt2 = prompts[1]
        self.assertEqual(prompt2.version, 2)
        self.assertEqual(prompt2.content, 'You are an expert assistant. {{preferences}}')
        self.assertTrue(prompt2.is_active)
        self.assertEqual(prompt2.performance_score, 0.85)
        
        # Verify preferences were imported
        preferences = imported_session.preferences.all()
        self.assertEqual(preferences.count(), 2)
        
        tone_pref = preferences.filter(key='tone').first()
        self.assertIsNotNone(tone_pref)
        self.assertEqual(tone_pref.value, 'friendly')
        self.assertEqual(tone_pref.description, 'Communication tone')
        
        # Verify emails were imported
        emails = imported_session.emails.all()
        self.assertEqual(emails.count(), 1)
        
        email = emails.first()
        self.assertEqual(email.subject, 'Project Update')
        self.assertEqual(email.body, 'Can you provide a status update?')
        self.assertEqual(email.sender, 'manager@company.com')
        self.assertEqual(email.scenario_type, 'professional')
        self.assertFalse(email.is_synthetic)
    
    def test_import_session_handles_conflicts(self):
        """Test that prompt_lab import handles conflicts appropriately"""
        from app.services.promptlab_importer import PromptLabImporter
        
        # Create conflicting prompt_lab with same name
        PromptLab.objects.create(name="Conflict PromptLab", description="Existing prompt_lab")
        
        export_data = {
            'session': {
                'name': 'Conflict PromptLab',
                'description': 'Imported prompt_lab with same name',
            },
            'prompts': [],
            'preferences': [],
            'emails': [],
            'export_timestamp': timezone.now().isoformat(),
            'version': '1.0'
        }
        
        importer = PromptLabImporter()
        imported_session = importer.import_session(export_data, handle_conflicts='rename')
        
        # Should create prompt_lab with modified name
        self.assertTrue(imported_session.name.startswith('Conflict PromptLab'))
        self.assertNotEqual(imported_session.name, 'Conflict PromptLab')
    
    def test_import_session_validates_data(self):
        """Test that prompt_lab import validates input data"""
        from app.services.promptlab_importer import PromptLabImporter, ImportValidationError
        
        importer = PromptLabImporter()
        
        # Test missing required fields
        with self.assertRaises(ImportValidationError):
            importer.import_session({})
        
        # Test invalid version
        with self.assertRaises(ImportValidationError):
            importer.import_session({
                'session': {'name': 'Test'},
                'version': '2.0'  # Unsupported version
            })
        
        # Test invalid prompt data
        with self.assertRaises(ImportValidationError):
            importer.import_session({
                'session': {'name': 'Test'},
                'prompts': [
                    {'content': 'test'}  # Missing version
                ],
                'preferences': [],
                'emails': [],
                'version': '1.0'
            })
    
    def test_import_preserves_relationships(self):
        """Test that import preserves all relationships between entities"""
        from app.services.promptlab_importer import PromptLabImporter
        
        # Complex export data with relationships
        export_data = {
            'prompt_lab': {
                'name': 'Complex PromptLab',
                'description': 'Session with all relationships',
            },
            'prompts': [
                {
                    'version': 1,
                    'content': 'You are a helpful assistant.',
                    'is_active': True,
                    'performance_score': 0.8,
                }
            ],
            'preferences': [
                {
                    'key': 'style',
                    'value': 'formal',
                    'description': 'Writing style',
                }
            ],
            'emails': [
                {
                    'subject': 'Meeting Request',
                    'body': 'Can we schedule a meeting?',
                    'sender': 'colleague@company.com',
                    'scenario_type': 'professional',
                    'is_synthetic': False,
                }
            ],
            'export_timestamp': timezone.now().isoformat(),
            'version': '1.0'
        }
        
        importer = PromptLabImporter()
        imported_prompt_lab = importer.import_session(export_data)
        
        # Verify all entities are connected to the prompt_lab
        prompt = imported_prompt_lab.prompts.first()
        self.assertEqual(prompt.prompt_lab, imported_prompt_lab)
        
        preference = imported_prompt_lab.preferences.first()
        self.assertEqual(preference.prompt_lab, imported_prompt_lab)
        
        email = imported_prompt_lab.emails.first()
        self.assertEqual(email.prompt_lab, imported_prompt_lab)


class PromptLabImportAPITests(APITestCase):
    """Test session import API endpoints"""
    
    def test_prompt_lab_import_api_success(self):
        """Test successful  import via API"""
        url = reverse('prompt-lab-import')
        
        import_data = {
            'session': {
                'name': 'API Import Test',
                'description': 'Session imported via API',
            },
            'prompts': [
                {
                    'version': 1,
                    'content': 'You are a helpful assistant.',
                    'is_active': True,
                    'performance_score': 0.75,
                }
            ],
            'preferences': [],
            'emails': [],
            'export_timestamp': timezone.now().isoformat(),
            'version': '1.0'
        }
        
        response = self.client.post(url, import_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        self.assertIn('prompt_lab_id', data)
        self.assertIn('imported_items', data)
        self.assertEqual(data['prompt_lab_name'], 'API Import Test')
        
        # Verify  was actually created
        session_id = data['prompt_lab_id']
        session = PromptLab.objects.get(id=session_id)
        self.assertEqual(session.name, 'API Import Test')
    
    def test_prompt_lab_import_api_validation_error(self):
        """Test API validation for invalid import data"""
        url = reverse('prompt_lab-import')
        
        # Invalid data - missing prompt_lab info
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid version
        response = self.client.post(url, {
            '': {'name': 'Test'},
            'version': '2.0'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_prompt_lab_import_api_conflict_handling(self):
        """Test API conflict handling options"""
        # Create existing 
        PromptLab.objects.create(name="Conflict Test", description="Existing")
        
        url = reverse('prompt-lab-import')
        import_data = {
            'session': {
                'name': 'Conflict Test',
                'description': 'Imported prompt_lab',
            },
            'prompts': [],
            'preferences': [],
            'emails': [],
            'version': '1.0',
            'options': {
                'conflict_resolution': 'rename'
            }
        }
        
        response = self.client.post(url, import_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Should have created with different name
        data = response.json()
        self.assertNotEqual(data['prompt_lab_name'], 'Conflict Test')


class EnhancedSystemImportTests(TestCase):
    """Test enhanced system-wide import functionality"""
    
    def test_import_system_state_with_sessions(self):
        """Test importing system state that includes multiple """
        from app.services.system_importer import SystemImporter
        
        system_data = {
            'global_preferences': [
                {
                    'key': 'default_tone',
                    'value': 'professional',
                    'description': 'Default communication tone'
                }
            ],
            'prompt_labs': [
                {
                    'name': 'Session 1',
                    'description': 'First prompt_lab',
                    'prompts': [
                        {
                            'version': 1,
                            'content': 'You are assistant 1.',
                            'is_active': True,
                            'performance_score': 0.8,
                        }
                    ],
                    'preferences': [],
                    'emails': []
                },
                {
                    'name': 'Session 2', 
                    'description': 'Second prompt_lab',
                    'prompts': [
                        {
                            'version': 1,
                            'content': 'You are assistant 2.',
                            'is_active': True,
                            'performance_score': 0.75,
                        }
                    ],
                    'preferences': [],
                    'emails': []
                }
            ],
            'export_timestamp': timezone.now().isoformat(),
            'version': '1.0'
        }
        
        importer = SystemImporter()
        result = importer.import_system_state(system_data)
        
        # Verify both prompt_labs were imported
        self.assertEqual(result['imported_prompt_labs'], 2)
        self.assertEqual(result['imported_global_preferences'], 1)
        
        # Check prompt_labs exist
        prompt_lab1 = PromptLab.objects.filter(name='Session 1').first()
        prompt_lab2 = PromptLab.objects.filter(name=' 2').first()
        
        self.assertIsNotNone(prompt_lab1)
        self.assertIsNotNone(prompt_lab2)
        
        # Check global preferences
        global_pref = UserPreference.objects.filter(prompt_lab__isnull=True, key='default_tone').first()
        self.assertIsNotNone(global_pref)
        self.assertEqual(global_pref.value, 'professional')
    
    def test_import_preserves_existing_data_option(self):
        """Test that import can preserve existing data when requested"""
        from app.services.system_importer import SystemImporter
        
        # Create existing 
        existing_session = PromptLab.objects.create(name="Existing", description="Keep me")
        
        system_data = {
            'prompt_labs': [
                {
                    'name': 'New PromptLab',
                    'description': 'Import me',
                    'prompts': [],
                    'preferences': [],
                    'emails': []
                }
            ],
            'version': '1.0'
        }
        
        importer = SystemImporter()
        result = importer.import_system_state(system_data, preserve_existing=True)
        
        # Both  should exist
        self.assertEqual(PromptLab.objects.count(), 2)
        self.assertTrue(PromptLab.objects.filter(name="Existing").exists())
        self.assertTrue(PromptLab.objects.filter(name="New PromptLab").exists())
    
    def test_import_replaces_existing_data_option(self):
        """Test that import can replace existing data when requested"""
        from app.services.system_importer import SystemImporter
        
        # Create existing 
        PromptLab.objects.create(name="Existing", description="Replace me")
        
        system_data = {
            'prompt_labs': [
                {
                    'name': 'New PromptLab',
                    'description': 'Import me',
                    'prompts': [],
                    'preferences': [],
                    'emails': []
                }
            ],
            'version': '1.0'
        }
        
        importer = SystemImporter()
        result = importer.import_system_state(system_data, preserve_existing=False)
        
        # Only new  should be active
        self.assertEqual(PromptLab.objects.filter(is_active=True).count(), 1)
        self.assertFalse(PromptLab.objects.filter(name="Existing", is_active=True).exists())
        self.assertTrue(PromptLab.objects.filter(name="New PromptLab", is_active=True).exists())


class ImportValidationTests(TestCase):
    """Test import data validation and error handling"""
    
    def test_validates_export_format_version(self):
        """Test that import validates export format version"""
        from app.services.promptlab_importer import PromptLabImporter, ImportValidationError
        
        importer = PromptLabImporter()
        
        # Test unsupported version
        with self.assertRaises(ImportValidationError) as cm:
            importer.import_session({'version': '99.0'})
        
        self.assertIn('Unsupported export format version', str(cm.exception))
    
    def test_validates_required_fields(self):
        """Test validation of required fields in import data"""
        from app.services.promptlab_importer import PromptLabImporter, ImportValidationError
        
        importer = PromptLabImporter()
        
        # Test missing prompt_lab data
        with self.assertRaises(ImportValidationError) as cm:
            importer.import_session({'version': '1.0'})
        
        self.assertIn('prompt_lab', str(cm.exception))
        
        # Test missing prompt_lab name
        with self.assertRaises(ImportValidationError) as cm:
            importer.import_session({
                '': {'description': 'No name'},
                'version': '1.0'
            })
        
        self.assertIn('name', str(cm.exception))
    
    def test_validates_data_types(self):
        """Test validation of data types in import data"""
        from app.services.promptlab_importer import PromptLabImporter, ImportValidationError
        
        importer = PromptLabImporter()
        
        # Test invalid prompt data
        with self.assertRaises(ImportValidationError):
            importer.import_session({
                '': {'name': 'Test'},
                'prompts': [
                    {
                        'version': 'not_a_number',  # Should be int
                        'content': 'test',
                        'is_active': True
                    }
                ],
                'preferences': [],
                'emails': [],
                'version': '1.0'
            })
    
    def test_handles_corrupted_data(self):
        """Test handling of corrupted or malformed import data"""
        from app.services.promptlab_importer import PromptLabImporter, ImportValidationError
        
        importer = PromptLabImporter()
        
        # Test None data
        with self.assertRaises(ImportValidationError):
            importer.import_session(None)
        
        # Test empty data
        with self.assertRaises(ImportValidationError):
            importer.import_session({})
        
        # Test data with wrong structure
        with self.assertRaises(ImportValidationError):
            importer.import_session({
                'wrong_key': 'wrong_value'
            })