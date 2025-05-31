"""
Test comprehensive import functionality for sessions and system state.
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
    Session, SystemPrompt, UserPreference, Email, Draft, DraftReason, 
    UserFeedback, SessionConfidence, ExtractedPreference
)


class SessionImportTests(TestCase):
    """Test session import functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test session to export and then import
        self.session = Session.objects.create(
            name="Original Session",
            description="Original test session"
        )
        
        # Create system prompt
        self.system_prompt = SystemPrompt.objects.create(
            session=self.session,
            content="You are a helpful assistant. {{preferences}}",
            version=1,
            is_active=True
        )
        
        # Create preferences
        self.preference = UserPreference.objects.create(
            session=self.session,
            key="tone",
            value="professional",
            description="Writing tone preference",
            is_active=True
        )
        
        # Create email
        self.email = Email.objects.create(
            session=self.session,
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
        """Test importing a session from exported JSON data"""
        from app.services.session_importer import SessionImporter
        
        # First export the session
        export_data = {
            'session': {
                'name': 'Imported Session',
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
        
        # Import the session
        importer = SessionImporter()
        imported_session = importer.import_session(export_data)
        
        # Verify session was created
        self.assertIsInstance(imported_session, Session)
        self.assertEqual(imported_session.name, 'Imported Session')
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
        """Test that session import handles conflicts appropriately"""
        from app.services.session_importer import SessionImporter
        
        # Create conflicting session with same name
        Session.objects.create(name="Conflict Session", description="Existing session")
        
        export_data = {
            'session': {
                'name': 'Conflict Session',
                'description': 'Imported session with same name',
            },
            'prompts': [],
            'preferences': [],
            'emails': [],
            'export_timestamp': timezone.now().isoformat(),
            'version': '1.0'
        }
        
        importer = SessionImporter()
        imported_session = importer.import_session(export_data, handle_conflicts='rename')
        
        # Should create session with modified name
        self.assertTrue(imported_session.name.startswith('Conflict Session'))
        self.assertNotEqual(imported_session.name, 'Conflict Session')
    
    def test_import_session_validates_data(self):
        """Test that session import validates input data"""
        from app.services.session_importer import SessionImporter, ImportValidationError
        
        importer = SessionImporter()
        
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
        from app.services.session_importer import SessionImporter
        
        # Complex export data with relationships
        export_data = {
            'session': {
                'name': 'Complex Session',
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
        
        importer = SessionImporter()
        imported_session = importer.import_session(export_data)
        
        # Verify all entities are connected to the session
        prompt = imported_session.prompts.first()
        self.assertEqual(prompt.session, imported_session)
        
        preference = imported_session.preferences.first()
        self.assertEqual(preference.session, imported_session)
        
        email = imported_session.emails.first()
        self.assertEqual(email.session, imported_session)


class SessionImportAPITests(APITestCase):
    """Test session import API endpoints"""
    
    def test_session_import_api_success(self):
        """Test successful session import via API"""
        url = reverse('session-import')
        
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
        
        self.assertIn('session_id', data)
        self.assertIn('imported_items', data)
        self.assertEqual(data['session_name'], 'API Import Test')
        
        # Verify session was actually created
        session_id = data['session_id']
        session = Session.objects.get(id=session_id)
        self.assertEqual(session.name, 'API Import Test')
    
    def test_session_import_api_validation_error(self):
        """Test API validation for invalid import data"""
        url = reverse('session-import')
        
        # Invalid data - missing session info
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid version
        response = self.client.post(url, {
            'session': {'name': 'Test'},
            'version': '2.0'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_session_import_api_conflict_handling(self):
        """Test API conflict handling options"""
        # Create existing session
        Session.objects.create(name="Conflict Test", description="Existing")
        
        url = reverse('session-import')
        import_data = {
            'session': {
                'name': 'Conflict Test',
                'description': 'Imported session',
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
        self.assertNotEqual(data['session_name'], 'Conflict Test')


class EnhancedSystemImportTests(TestCase):
    """Test enhanced system-wide import functionality"""
    
    def test_import_system_state_with_sessions(self):
        """Test importing system state that includes multiple sessions"""
        from app.services.system_importer import SystemImporter
        
        system_data = {
            'global_preferences': [
                {
                    'key': 'default_tone',
                    'value': 'professional',
                    'description': 'Default communication tone'
                }
            ],
            'sessions': [
                {
                    'name': 'Session 1',
                    'description': 'First session',
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
                    'description': 'Second session',
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
        
        # Verify both sessions were imported
        self.assertEqual(result['imported_sessions'], 2)
        self.assertEqual(result['imported_global_preferences'], 1)
        
        # Check sessions exist
        session1 = Session.objects.filter(name='Session 1').first()
        session2 = Session.objects.filter(name='Session 2').first()
        
        self.assertIsNotNone(session1)
        self.assertIsNotNone(session2)
        
        # Check global preferences
        global_pref = UserPreference.objects.filter(session__isnull=True, key='default_tone').first()
        self.assertIsNotNone(global_pref)
        self.assertEqual(global_pref.value, 'professional')
    
    def test_import_preserves_existing_data_option(self):
        """Test that import can preserve existing data when requested"""
        from app.services.system_importer import SystemImporter
        
        # Create existing session
        existing_session = Session.objects.create(name="Existing", description="Keep me")
        
        system_data = {
            'sessions': [
                {
                    'name': 'New Session',
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
        
        # Both sessions should exist
        self.assertEqual(Session.objects.count(), 2)
        self.assertTrue(Session.objects.filter(name="Existing").exists())
        self.assertTrue(Session.objects.filter(name="New Session").exists())
    
    def test_import_replaces_existing_data_option(self):
        """Test that import can replace existing data when requested"""
        from app.services.system_importer import SystemImporter
        
        # Create existing session
        Session.objects.create(name="Existing", description="Replace me")
        
        system_data = {
            'sessions': [
                {
                    'name': 'New Session',
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
        
        # Only new session should be active
        self.assertEqual(Session.objects.filter(is_active=True).count(), 1)
        self.assertFalse(Session.objects.filter(name="Existing", is_active=True).exists())
        self.assertTrue(Session.objects.filter(name="New Session", is_active=True).exists())


class ImportValidationTests(TestCase):
    """Test import data validation and error handling"""
    
    def test_validates_export_format_version(self):
        """Test that import validates export format version"""
        from app.services.session_importer import SessionImporter, ImportValidationError
        
        importer = SessionImporter()
        
        # Test unsupported version
        with self.assertRaises(ImportValidationError) as cm:
            importer.import_session({'version': '99.0'})
        
        self.assertIn('Unsupported export format version', str(cm.exception))
    
    def test_validates_required_fields(self):
        """Test validation of required fields in import data"""
        from app.services.session_importer import SessionImporter, ImportValidationError
        
        importer = SessionImporter()
        
        # Test missing session data
        with self.assertRaises(ImportValidationError) as cm:
            importer.import_session({'version': '1.0'})
        
        self.assertIn('session', str(cm.exception))
        
        # Test missing session name
        with self.assertRaises(ImportValidationError) as cm:
            importer.import_session({
                'session': {'description': 'No name'},
                'version': '1.0'
            })
        
        self.assertIn('name', str(cm.exception))
    
    def test_validates_data_types(self):
        """Test validation of data types in import data"""
        from app.services.session_importer import SessionImporter, ImportValidationError
        
        importer = SessionImporter()
        
        # Test invalid prompt data
        with self.assertRaises(ImportValidationError):
            importer.import_session({
                'session': {'name': 'Test'},
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
        from app.services.session_importer import SessionImporter, ImportValidationError
        
        importer = SessionImporter()
        
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