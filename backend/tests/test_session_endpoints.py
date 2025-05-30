import pytest
import json
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from core.models import Session, SystemPrompt, UserPreference, Email, Draft, DraftReason


class SessionEndpointsTestCase(TestCase):
    """Test cases for session management endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test sessions
        self.session1 = Session.objects.create(
            name="Test Session 1",
            description="First test session"
        )
        
        self.session2 = Session.objects.create(
            name="Test Session 2", 
            description="Second test session"
        )
        
        # Create system prompts for sessions
        self.prompt1 = SystemPrompt.objects.create(
            session=self.session1,
            content="Test prompt for session 1",
            version=1,
            is_active=True
        )
        
        self.prompt2 = SystemPrompt.objects.create(
            session=self.session2,
            content="Test prompt for session 2",
            version=1,
            is_active=True
        )
        
        # Create test preferences
        UserPreference.objects.create(
            session=self.session1,
            key="tone",
            value="professional",
            description="Professional tone preference"
        )
        
        # Create test emails
        self.email1 = Email.objects.create(
            session=self.session1,
            subject="Test Email 1",
            body="This is a test email",
            sender="test@example.com",
            scenario_type="professional"
        )
    
    def test_session_list_get(self):
        """Test GET /api/sessions/ - list all sessions"""
        response = self.client.get('/api/sessions/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('sessions', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['sessions']), 2)
        
        # Check session data structure
        session_data = data['sessions'][0]
        required_fields = ['id', 'name', 'description', 'created_at', 'updated_at', 
                          'optimization_iterations', 'total_emails_processed', 'total_feedback_collected']
        for field in required_fields:
            self.assertIn(field, session_data)
    
    def test_session_list_with_search(self):
        """Test session list with search parameter"""
        response = self.client.get('/api/sessions/?search=Test Session 1')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['sessions'][0]['name'], 'Test Session 1')
    
    def test_session_list_with_sorting(self):
        """Test session list with sorting"""
        response = self.client.get('/api/sessions/?sort_by=name&order=asc')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should be sorted by name ascending
        session_names = [s['name'] for s in data['sessions']]
        self.assertEqual(session_names, sorted(session_names))
    
    def test_session_create_post(self):
        """Test POST /api/sessions/ - create new session"""
        session_data = {
            'name': 'New Test Session',
            'description': 'A newly created session',
            'initial_prompt': 'Custom initial prompt'
        }
        
        response = self.client.post(
            '/api/sessions/',
            data=json.dumps(session_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        # Check response data
        self.assertEqual(data['name'], session_data['name'])
        self.assertEqual(data['description'], session_data['description'])
        
        # Verify session was created in database
        session = Session.objects.get(id=data['id'])
        self.assertEqual(session.name, session_data['name'])
        
        # Verify initial prompt was created
        initial_prompt = session.prompts.filter(version=1, is_active=True).first()
        self.assertIsNotNone(initial_prompt)
        self.assertEqual(initial_prompt.content, session_data['initial_prompt'])
    
    def test_session_create_missing_name(self):
        """Test session creation with missing name"""
        session_data = {
            'description': 'Missing name'
        }
        
        response = self.client.post(
            '/api/sessions/',
            data=json.dumps(session_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
    
    def test_session_detail_get(self):
        """Test GET /api/sessions/{id}/ - get session details"""
        response = self.client.get(f'/api/sessions/{self.session1.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['name'], self.session1.name)
        self.assertEqual(data['description'], self.session1.description)
        
        # Check additional context
        self.assertIn('active_prompt', data)
        self.assertIn('recent_emails', data)
        
        self.assertEqual(data['active_prompt']['version'], 1)
        self.assertEqual(len(data['recent_emails']), 1)
    
    def test_session_detail_not_found(self):
        """Test session detail with non-existent ID"""
        fake_id = uuid.uuid4()
        response = self.client.get(f'/api/sessions/{fake_id}/')
        
        self.assertEqual(response.status_code, 404)
    
    def test_session_update_put(self):
        """Test PUT /api/sessions/{id}/ - update session"""
        update_data = {
            'name': 'Updated Session Name',
            'description': 'Updated description'
        }
        
        response = self.client.put(
            f'/api/sessions/{self.session1.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['name'], update_data['name'])
        self.assertEqual(data['description'], update_data['description'])
        
        # Verify database was updated
        self.session1.refresh_from_db()
        self.assertEqual(self.session1.name, update_data['name'])
    
    def test_session_update_empty_name(self):
        """Test session update with empty name"""
        update_data = {'name': ''}
        
        response = self.client.put(
            f'/api/sessions/{self.session1.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_session_delete(self):
        """Test DELETE /api/sessions/{id}/ - soft delete session"""
        response = self.client.delete(f'/api/sessions/{self.session1.id}/')
        
        self.assertEqual(response.status_code, 200)
        
        # Verify soft delete (is_active = False)
        self.session1.refresh_from_db()
        self.assertFalse(self.session1.is_active)
        
        # Verify session no longer appears in list
        list_response = self.client.get('/api/sessions/')
        data = list_response.json()
        session_ids = [s['id'] for s in data['sessions']]
        self.assertNotIn(str(self.session1.id), session_ids)
    
    def test_session_export(self):
        """Test GET /api/sessions/{id}/export/ - export session data"""
        response = self.client.get(f'/api/sessions/{self.session1.id}/export/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check export structure
        required_sections = ['session', 'prompts', 'preferences', 'emails', 
                           'export_timestamp', 'version']
        for section in required_sections:
            self.assertIn(section, data)
        
        # Check session data
        self.assertEqual(data['session']['name'], self.session1.name)
        
        # Check prompts
        self.assertEqual(len(data['prompts']), 1)
        self.assertEqual(data['prompts'][0]['version'], 1)
        
        # Check preferences
        self.assertEqual(len(data['preferences']), 1)
        self.assertEqual(data['preferences'][0]['key'], 'tone')
        
        # Check emails
        self.assertEqual(len(data['emails']), 1)
        self.assertEqual(data['emails'][0]['subject'], 'Test Email 1')
    
    def test_session_duplicate(self):
        """Test POST /api/sessions/{id}/duplicate/ - duplicate session"""
        duplicate_data = {
            'name': 'Duplicated Session',
            'description': 'Copy of original session',
            'copy_emails': True
        }
        
        response = self.client.post(
            f'/api/sessions/{self.session1.id}/duplicate/',
            data=json.dumps(duplicate_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        # Verify new session was created
        new_session = Session.objects.get(id=data['id'])
        self.assertEqual(new_session.name, duplicate_data['name'])
        
        # Verify prompts were copied
        self.assertEqual(new_session.prompts.count(), self.session1.prompts.count())
        
        # Verify preferences were copied
        self.assertEqual(new_session.preferences.count(), self.session1.preferences.count())
        
        # Verify emails were copied (since copy_emails=True)
        self.assertEqual(new_session.emails.count(), self.session1.emails.count())
    
    def test_session_duplicate_without_emails(self):
        """Test session duplication without copying emails"""
        duplicate_data = {
            'name': 'Duplicated Session No Emails',
            'copy_emails': False
        }
        
        response = self.client.post(
            f'/api/sessions/{self.session1.id}/duplicate/',
            data=json.dumps(duplicate_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        new_session = Session.objects.get(id=data['id'])
        
        # Emails should not be copied
        self.assertEqual(new_session.emails.count(), 0)
        
        # But prompts and preferences should still be copied
        self.assertEqual(new_session.prompts.count(), self.session1.prompts.count())
        self.assertEqual(new_session.preferences.count(), self.session1.preferences.count())
    
    def test_session_stats(self):
        """Test GET /api/sessions/{id}/stats/ - get session statistics"""
        response = self.client.get(f'/api/sessions/{self.session1.id}/stats/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check stats structure
        required_stats = ['session_id', 'session_name', 'created_at', 'updated_at',
                         'optimization_iterations', 'prompts', 'emails', 'drafts', 
                         'feedback', 'preferences_count']
        for stat in required_stats:
            self.assertIn(stat, data)
        
        # Check specific values
        self.assertEqual(data['session_name'], self.session1.name)
        self.assertEqual(data['prompts']['total_versions'], 1)
        self.assertEqual(data['prompts']['current_version'], 1)
        self.assertEqual(data['emails']['total_processed'], 1)
        self.assertEqual(data['preferences_count'], 1)
    
    def test_session_scoped_email_generation(self):
        """Test session-scoped synthetic email generation"""
        request_data = {
            'scenario_type': 'professional'
        }
        
        response = self.client.post(
            f'/api/sessions/{self.session1.id}/generate-synthetic-email/',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        # Check response includes session_id
        self.assertEqual(data['session_id'], str(self.session1.id))
        self.assertEqual(data['scenario_type'], 'professional')
        
        # Verify email was created in correct session
        email = Email.objects.get(id=data['email_id'])
        self.assertEqual(email.session_id, self.session1.id)
    
    def test_session_scoped_draft_generation(self):
        """Test session-scoped draft generation"""
        response = self.client.post(
            f'/api/sessions/{self.session1.id}/emails/{self.email1.id}/generate-drafts/',
            data=json.dumps({'num_drafts': 2}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify drafts were created for the email in the correct session
        self.assertIn('drafts', data)
        
        # Verify email belongs to the session
        email = Email.objects.get(id=self.email1.id)
        self.assertEqual(email.session_id, self.session1.id)
    
    def test_session_scoped_draft_generation_wrong_session(self):
        """Test draft generation with email from wrong session"""
        # Try to generate drafts for session1's email via session2's endpoint
        response = self.client.post(
            f'/api/sessions/{self.session2.id}/emails/{self.email1.id}/generate-drafts/',
            data=json.dumps({'num_drafts': 1}),
            content_type='application/json'
        )
        
        # Should return 404 since email doesn't belong to session2
        self.assertEqual(response.status_code, 404)
    
    def test_legacy_endpoint_compatibility(self):
        """Test that legacy endpoints still work for backward compatibility"""
        # Test legacy email generation
        response = self.client.post(
            '/api/generate-synthetic-email/',
            data=json.dumps({'scenario_type': 'casual'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        # Should create email in default session or create new default session
        self.assertIn('session_id', data)
        self.assertEqual(data['scenario_type'], 'casual')


class SessionModelTestCase(TestCase):
    """Test cases for Session model functionality"""
    
    def test_session_creation(self):
        """Test basic session creation"""
        session = Session.objects.create(
            name="Test Model Session",
            description="Testing session model"
        )
        
        self.assertEqual(session.name, "Test Model Session")
        self.assertTrue(session.is_active)
        self.assertEqual(session.optimization_iterations, 0)
        self.assertEqual(session.total_emails_processed, 0)
        self.assertEqual(session.total_feedback_collected, 0)
    
    def test_session_uuid_generation(self):
        """Test that sessions get unique UUIDs"""
        session1 = Session.objects.create(name="Session 1")
        session2 = Session.objects.create(name="Session 2")
        
        self.assertNotEqual(session1.id, session2.id)
        self.assertIsInstance(session1.id, uuid.UUID)
        self.assertIsInstance(session2.id, uuid.UUID)
    
    def test_session_str_representation(self):
        """Test session string representation"""
        session = Session.objects.create(
            name="Test Session",
            description="Test description"
        )
        
        expected_str = f"Test Session ({session.created_at.strftime('%Y-%m-%d')})"
        self.assertEqual(str(session), expected_str)
    
    def test_session_ordering(self):
        """Test session ordering by updated_at desc"""
        session1 = Session.objects.create(name="First")
        session2 = Session.objects.create(name="Second")
        
        # Update session1 to be more recent
        session1.name = "Updated First"
        session1.save()
        
        sessions = list(Session.objects.all())
        self.assertEqual(sessions[0], session1)  # Most recently updated first
        self.assertEqual(sessions[1], session2)


class SessionPromptRelationshipTestCase(TestCase):
    """Test session-prompt relationships"""
    
    def setUp(self):
        self.session = Session.objects.create(
            name="Prompt Test Session"
        )
    
    def test_session_prompt_creation(self):
        """Test creating prompts for a session"""
        prompt = SystemPrompt.objects.create(
            session=self.session,
            content="Test prompt content",
            version=1,
            is_active=True
        )
        
        self.assertEqual(prompt.session, self.session)
        self.assertEqual(self.session.prompts.count(), 1)
    
    def test_session_prompt_version_uniqueness(self):
        """Test that prompt versions are unique per session"""
        SystemPrompt.objects.create(
            session=self.session,
            content="Version 1",
            version=1
        )
        
        # Should be able to create same version in different session
        session2 = Session.objects.create(name="Session 2")
        SystemPrompt.objects.create(
            session=session2,
            content="Version 1",
            version=1
        )
        
        # Should not be able to create duplicate version in same session
        with self.assertRaises(Exception):
            SystemPrompt.objects.create(
                session=self.session,
                content="Another version 1",
                version=1
            )
    
    def test_session_deletion_cascade(self):
        """Test that deleting session cascades to related objects"""
        # Create related objects
        prompt = SystemPrompt.objects.create(
            session=self.session,
            content="Test prompt",
            version=1
        )
        
        preference = UserPreference.objects.create(
            session=self.session,
            key="test_key",
            value="test_value"
        )
        
        email = Email.objects.create(
            session=self.session,
            subject="Test Email",
            body="Test body",
            sender="test@example.com"
        )
        
        session_id = self.session.id
        
        # Delete session
        self.session.delete()
        
        # Verify related objects were deleted
        self.assertFalse(SystemPrompt.objects.filter(id=prompt.id).exists())
        self.assertFalse(UserPreference.objects.filter(id=preference.id).exists())
        self.assertFalse(Email.objects.filter(id=email.id).exists())
        self.assertFalse(Session.objects.filter(id=session_id).exists())


if __name__ == '__main__':
    pytest.main([__file__])