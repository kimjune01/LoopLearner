import pytest
import json
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from core.models import PromptLab, SystemPrompt, UserPreference, Email, Draft, DraftReason


class PromptLabEndpointsTestCase(TestCase):
    """Test cases for prompt lab management endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test prompt labs
        self.prompt_lab1 = PromptLab.objects.create(
            name="Test PromptLab 1",
            description="First test prompt lab"
        )
        
        self.prompt_lab2 = PromptLab.objects.create(
            name="Test PromptLab 2", 
            description="Second test prompt lab"
        )
        
        # Create system prompts for prompt labs
        self.prompt1 = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab1,
            content="Test prompt for prompt lab 1",
            version=1,
            is_active=True
        )
        
        self.prompt2 = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab2,
            content="Test prompt for prompt lab 2",
            version=1,
            is_active=True
        )
        
        # Create test preferences
        UserPreference.objects.create(
            prompt_lab=self.prompt_lab1,
            key="tone",
            value="professional",
            description="Professional tone preference"
        )
        
        # Create test emails
        self.email1 = Email.objects.create(
            prompt_lab=self.prompt_lab1,
            subject="Test Email 1",
            body="This is a test email",
            sender="test@example.com",
            scenario_type="professional"
        )
    
    def test_prompt_lab_list_get(self):
        """Test GET /api/prompt-labs/ - list all prompt labs"""
        response = self.client.get('/api/prompt-labs/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('prompt_labs', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['prompt_labs']), 2)
        
        # Check prompt lab data structure
        prompt_lab_data = data['prompt_labs'][0]
        required_fields = ['id', 'name', 'description', 'created_at', 'updated_at', 
                          'optimization_iterations', 'total_emails_processed', 'total_feedback_collected']
        for field in required_fields:
            self.assertIn(field, prompt_lab_data)
    
    def test_prompt_lab_list_with_search(self):
        """Test session list with search parameter"""
        response = self.client.get('/api/prompt-labs/?search=Test PromptLab 1')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['prompt_labs'][0]['name'], 'Test PromptLab 1')
    
    def test_prompt_lab_list_with_sorting(self):
        """Test prompt lab list with sorting"""
        response = self.client.get('/api/prompt-labs/?sort_by=name&order=asc')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should be sorted by name ascending
        prompt_lab_names = [s['name'] for s in data['prompt_labs']]
        self.assertEqual(prompt_lab_names, sorted(prompt_lab_names))
    
    def test_prompt_lab_create_post(self):
        """Test POST /api/prompt-labs/ - create new prompt lab"""
        prompt_lab_data = {
            'name': 'New Test PromptLab',
            'description': 'A newly created prompt lab',
            'initial_prompt': 'Custom initial prompt'
        }
        
        response = self.client.post(
            '/api/prompt-labs/',
            data=json.dumps(prompt_lab_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        # Check response data
        self.assertEqual(data['name'], prompt_lab_data['name'])
        self.assertEqual(data['description'], prompt_lab_data['description'])
        
        # Verify prompt lab was created in database
        prompt_lab = PromptLab.objects.get(id=data['id'])
        self.assertEqual(prompt_lab.name, prompt_lab_data['name'])
        
        # Verify initial prompt was created
        initial_prompt = prompt_lab.prompts.filter(version=1, is_active=True).first()
        self.assertIsNotNone(initial_prompt)
        self.assertEqual(initial_prompt.content, prompt_lab_data['initial_prompt'])
    
    def test_prompt_lab_create_missing_name(self):
        """Test prompt lab creation with missing name"""
        prompt_lab_data = {
            'description': 'Missing name'
        }
        
        response = self.client.post(
            '/api/prompt-labs/',
            data=json.dumps(prompt_lab_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
    
    def test_prompt_lab_detail_get(self):
        """Test GET /api/prompt-labs/{id}/ - get prompt lab details"""
        response = self.client.get(f'/api/prompt-labs/{self.prompt_lab1.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['name'], self.prompt_lab1.name)
        self.assertEqual(data['description'], self.prompt_lab1.description)
        
        # Check additional context
        self.assertIn('active_prompt', data)
        self.assertIn('recent_emails', data)
        
        self.assertEqual(data['active_prompt']['version'], 1)
        self.assertEqual(len(data['recent_emails']), 1)
    
    def test_prompt_lab_detail_not_found(self):
        """Test prompt lab detail with non-existent ID"""
        fake_id = uuid.uuid4()
        response = self.client.get(f'/api/prompt-labs/{fake_id}/')
        
        self.assertEqual(response.status_code, 404)
    
    def test_prompt_lab_update_put(self):
        """Test PUT /api/prompt-labs/{id}/ - update prompt lab"""
        update_data = {
            'name': 'Updated PromptLab Name',
            'description': 'Updated description'
        }
        
        response = self.client.put(
            f'/api/prompt-labs/{self.prompt_lab1.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['name'], update_data['name'])
        self.assertEqual(data['description'], update_data['description'])
        
        # Verify database was updated
        self.prompt_lab1.refresh_from_db()
        self.assertEqual(self.prompt_lab1.name, update_data['name'])
    
    def test_prompt_lab_update_empty_name(self):
        """Test prompt lab update with empty name"""
        update_data = {'name': ''}
        
        response = self.client.put(
            f'/api/prompt-labs/{self.prompt_lab1.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_prompt_lab_delete(self):
        """Test DELETE /api/prompt-labs/{id}/ - soft delete prompt lab"""
        response = self.client.delete(f'/api/prompt-labs/{self.prompt_lab1.id}/')
        
        self.assertEqual(response.status_code, 200)
        
        # Verify soft delete (is_active = False)
        self.prompt_lab1.refresh_from_db()
        self.assertFalse(self.prompt_lab1.is_active)
        
        # Verify prompt lab no longer appears in list
        list_response = self.client.get('/api/prompt-labs/')
        data = list_response.json()
        prompt_lab_ids = [s['id'] for s in data['prompt_labs']]
        self.assertNotIn(str(self.prompt_lab1.id), prompt_lab_ids)
    
    def test_prompt_lab_export(self):
        """Test GET /api/prompt-labs/{id}/export/ - export prompt lab data"""
        response = self.client.get(f'/api/prompt-labs/{self.prompt_lab1.id}/export/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check export structure
        required_sections = ['prompt_lab', 'prompts', 'preferences', 'emails', 
                           'export_timestamp', 'version']
        for section in required_sections:
            self.assertIn(section, data)
        
        # Check prompt lab data
        self.assertEqual(data['prompt_lab']['name'], self.prompt_lab1.name)
        
        # Check prompts
        self.assertEqual(len(data['prompts']), 1)
        self.assertEqual(data['prompts'][0]['version'], 1)
        
        # Check preferences
        self.assertEqual(len(data['preferences']), 1)
        self.assertEqual(data['preferences'][0]['key'], 'tone')
        
        # Check emails
        self.assertEqual(len(data['emails']), 1)
        self.assertEqual(data['emails'][0]['subject'], 'Test Email 1')
    
    def test_prompt_lab_duplicate(self):
        """Test POST /api/prompt-labs/{id}/duplicate/ - duplicate prompt lab"""
        duplicate_data = {
            'name': 'Duplicated PromptLab',
            'description': 'Copy of original prompt lab',
            'copy_emails': True
        }
        
        response = self.client.post(
            f'/api/prompt-labs/{self.prompt_lab1.id}/duplicate/',
            data=json.dumps(duplicate_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        # Verify new prompt lab was created
        new_prompt_lab = PromptLab.objects.get(id=data['id'])
        self.assertEqual(new_prompt_lab.name, duplicate_data['name'])
        
        # Verify prompts were copied
        self.assertEqual(new_prompt_lab.prompts.count(), self.prompt_lab1.prompts.count())
        
        # Verify preferences were copied
        self.assertEqual(new_prompt_lab.preferences.count(), self.prompt_lab1.preferences.count())
        
        # Verify emails were copied (since copy_emails=True)
        self.assertEqual(new_prompt_lab.emails.count(), self.prompt_lab1.emails.count())
    
    def test_prompt_lab_duplicate_without_emails(self):
        """Test prompt lab duplication without copying emails"""
        duplicate_data = {
            'name': 'Duplicated PromptLab No Emails',
            'copy_emails': False
        }
        
        response = self.client.post(
            f'/api/prompt-labs/{self.prompt_lab1.id}/duplicate/',
            data=json.dumps(duplicate_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        new_prompt_lab = PromptLab.objects.get(id=data['id'])
        
        # Emails should not be copied
        self.assertEqual(new_prompt_lab.emails.count(), 0)
        
        # But prompts and preferences should still be copied
        self.assertEqual(new_prompt_lab.prompts.count(), self.prompt_lab1.prompts.count())
        self.assertEqual(new_prompt_lab.preferences.count(), self.prompt_lab1.preferences.count())
    
    def test_prompt_lab_stats(self):
        """Test GET /api/prompt-labs/{id}/stats/ - get prompt lab statistics"""
        response = self.client.get(f'/api/prompt-labs/{self.prompt_lab1.id}/stats/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check stats structure
        required_stats = ['prompt_lab_id', 'prompt_lab_name', 'created_at', 'updated_at',
                         'optimization_iterations', 'prompts', 'emails', 'drafts', 
                         'feedback', 'preferences_count']
        for stat in required_stats:
            self.assertIn(stat, data)
        
        # Check specific values
        self.assertEqual(data['prompt_lab_name'], self.prompt_lab1.name)
        self.assertEqual(data['prompts']['total_versions'], 1)
        self.assertEqual(data['prompts']['current_version'], 1)
        self.assertEqual(data['emails']['total_processed'], 1)
        self.assertEqual(data['preferences_count'], 1)
    
    def test_prompt_lab_scoped_email_generation(self):
        """Test prompt lab-scoped synthetic email generation"""
        request_data = {
            'scenario_type': 'professional'
        }
        
        response = self.client.post(
            f'/api/prompt-labs/{self.prompt_lab1.id}/generate-synthetic-email/',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        # Check response includes prompt_lab_id
        self.assertEqual(data['prompt_lab_id'], str(self.prompt_lab1.id))
        self.assertEqual(data['scenario_type'], 'professional')
        
        # Verify email was created in correct prompt lab
        email = Email.objects.get(id=data['email_id'])
        self.assertEqual(email.prompt_lab_id, self.prompt_lab1.id)
    
    def test_prompt_lab_scoped_draft_generation(self):
        """Test prompt lab-scoped draft generation"""
        response = self.client.post(
            f'/api/prompt-labs/{self.prompt_lab1.id}/emails/{self.email1.id}/generate-drafts/',
            data=json.dumps({'num_drafts': 2}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        # Verify drafts were created for the email in the correct prompt lab
        self.assertIn('drafts', data)
        
        # Verify email belongs to the prompt lab
        email = Email.objects.get(id=self.email1.id)
        self.assertEqual(email.prompt_lab_id, self.prompt_lab1.id)
    
    def test_prompt_lab_scoped_draft_generation_wrong_session(self):
        """Test draft generation with email from wrong prompt lab"""
        # Try to generate drafts for prompt_lab1's email via prompt_lab2's endpoint
        response = self.client.post(
            f'/api/prompt-labs/{self.prompt_lab2.id}/emails/{self.email1.id}/generate-drafts/',
            data=json.dumps({'num_drafts': 1}),
            content_type='application/json'
        )
        
        # Should return 404 since email doesn't belong to prompt_lab2
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
        
        # Should create email in default prompt lab or create new default prompt lab
        self.assertIn('prompt_lab_id', data)
        self.assertEqual(data['scenario_type'], 'casual')


class PromptLabModelTestCase(TestCase):
    """Test cases for PromptLab model functionality"""
    
    def test_prompt_lab_creation(self):
        """Test basic prompt lab creation"""
        prompt_lab = PromptLab.objects.create(
            name="Test Model PromptLab",
            description="Testing prompt lab model"
        )
        
        self.assertEqual(prompt_lab.name, "Test Model PromptLab")
        self.assertTrue(prompt_lab.is_active)
        self.assertEqual(prompt_lab.optimization_iterations, 0)
        self.assertEqual(prompt_lab.total_emails_processed, 0)
        self.assertEqual(prompt_lab.total_feedback_collected, 0)
    
    def test_prompt_lab_uuid_generation(self):
        """Test that prompt labs get unique UUIDs"""
        prompt_lab1 = PromptLab.objects.create(name="PromptLab 1")
        prompt_lab2 = PromptLab.objects.create(name="PromptLab 2")
        
        self.assertNotEqual(prompt_lab1.id, prompt_lab2.id)
        self.assertIsInstance(prompt_lab1.id, uuid.UUID)
        self.assertIsInstance(prompt_lab2.id, uuid.UUID)
    
    def test_prompt_lab_str_representation(self):
        """Test prompt lab string representation"""
        prompt_lab = PromptLab.objects.create(
            name="Test PromptLab",
            description="Test description"
        )
        
        expected_str = f"Test PromptLab ({prompt_lab.created_at.strftime('%Y-%m-%d')})"
        self.assertEqual(str(prompt_lab), expected_str)
    
    def test_prompt_lab_ordering(self):
        """Test prompt lab ordering by updated_at desc"""
        prompt_lab1 = PromptLab.objects.create(name="First")
        prompt_lab2 = PromptLab.objects.create(name="Second")
        
        # Update prompt_lab1 to be more recent
        prompt_lab1.name = "Updated First"
        prompt_lab1.save()
        
        prompt_labs = list(PromptLab.objects.all())
        self.assertEqual(prompt_labs[0], prompt_lab1)  # Most recently updated first
        self.assertEqual(prompt_labs[1], prompt_lab2)


class PromptLabPromptRelationshipTestCase(TestCase):
    """Test prompt lab-prompt relationships"""
    
    def setUp(self):
        self.prompt_lab = PromptLab.objects.create(
            name="Prompt Test PromptLab"
        )
    
    def test_prompt_lab_prompt_creation(self):
        """Test creating prompts for a prompt lab"""
        prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="Test prompt content",
            version=1,
            is_active=True
        )
        
        self.assertEqual(prompt.prompt_lab, self.prompt_lab)
        self.assertEqual(self.prompt_lab.prompts.count(), 1)
    
    def test_prompt_lab_prompt_version_uniqueness(self):
        """Test that prompt versions are unique per prompt lab"""
        SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="Version 1",
            version=1
        )
        
        # Should be able to create same version in different prompt lab
        prompt_lab2 = PromptLab.objects.create(name="PromptLab 2")
        SystemPrompt.objects.create(
            prompt_lab=prompt_lab2,
            content="Version 1",
            version=1
        )
        
        # Should not be able to create duplicate version in same prompt lab
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            SystemPrompt.objects.create(
                prompt_lab=self.prompt_lab,
                content="Another version 1",
                version=1
            )
    
    def test_prompt_lab_deletion_cascade(self):
        """Test that deleting prompt lab cascades to related objects"""
        # Create related objects
        prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="Test prompt",
            version=1
        )
        
        preference = UserPreference.objects.create(
            prompt_lab=self.prompt_lab,
            key="test_key",
            value="test_value"
        )
        
        email = Email.objects.create(
            prompt_lab=self.prompt_lab,
            subject="Test Email",
            body="Test body",
            sender="test@example.com"
        )
        
        prompt_lab_id = self.prompt_lab.id
        
        # Delete prompt lab
        self.prompt_lab.delete()
        
        # Verify related objects were deleted
        self.assertFalse(SystemPrompt.objects.filter(id=prompt.id).exists())
        self.assertFalse(UserPreference.objects.filter(id=preference.id).exists())
        self.assertFalse(Email.objects.filter(id=email.id).exists())
        self.assertFalse(PromptLab.objects.filter(id=prompt_lab_id).exists())


class PromptLabPromptUpdateTestCase(TestCase):
    """Test cases for prompt lab prompt update functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test prompt lab with initial prompt
        self.session_with_prompt = PromptLab.objects.create(
            name="PromptLab with Prompt",
            description="PromptLab that has an initial prompt"
        )
        
        # Create system prompt for this prompt lab
        self.system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.session_with_prompt,
            content="Initial test prompt",
            version=1,
            is_active=True
        )
        
        # Create test prompt lab without prompt
        self.session_without_prompt = PromptLab.objects.create(
            name="PromptLab without Prompt",
            description="PromptLab that has no initial prompt"
        )
    
    def test_update_existing_prompt_success(self):
        """Test successfully updating an existing prompt"""
        new_prompt_content = "Updated prompt content for testing"
        
        response = self.client.put(
            f'/api/prompt-labs/{self.session_with_prompt.id}/',
            data=json.dumps({'initial_prompt': new_prompt_content}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify prompt lab exists (no initial_prompt field to check)
        updated_prompt_lab = PromptLab.objects.get(id=self.session_with_prompt.id)
        
        # Verify system prompt was updated
        updated_system_prompt = SystemPrompt.objects.get(
            prompt_lab=self.session_with_prompt, 
            is_active=True
        )
        self.assertEqual(updated_system_prompt.content, new_prompt_content)
        self.assertEqual(updated_system_prompt.version, 1)  # Should still be version 1
        self.assertTrue(updated_system_prompt.is_active)
    
    def test_create_new_prompt_for_prompt_lab_without_prompt(self):
        """Test creating a new prompt for a prompt lab that doesn't have one"""
        new_prompt_content = "New prompt for prompt lab without prompt"
        
        response = self.client.put(
            f'/api/prompt-labs/{self.session_without_prompt.id}/',
            data=json.dumps({'initial_prompt': new_prompt_content}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify prompt lab exists (no initial_prompt field to check)
        updated_prompt_lab = PromptLab.objects.get(id=self.session_without_prompt.id)
        
        # Verify system prompt was created
        new_system_prompt = SystemPrompt.objects.get(
            prompt_lab=self.session_without_prompt,
            is_active=True
        )
        self.assertEqual(new_system_prompt.content, new_prompt_content)
        self.assertEqual(new_system_prompt.version, 1)
        self.assertTrue(new_system_prompt.is_active)
    
    def test_clear_existing_prompt(self):
        """Test clearing an existing prompt by setting it to empty string"""
        response = self.client.put(
            f'/api/prompt-labs/{self.session_with_prompt.id}/',
            data=json.dumps({'initial_prompt': ''}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify prompt lab exists (no initial_prompt field to check)
        updated_prompt_lab = PromptLab.objects.get(id=self.session_with_prompt.id)
        
        # Verify system prompt was deactivated
        deactivated_prompt = SystemPrompt.objects.get(id=self.system_prompt.id)
        self.assertFalse(deactivated_prompt.is_active)
        
        # Verify no active prompts exist for this prompt lab
        active_prompts = SystemPrompt.objects.filter(
            prompt_lab=self.session_with_prompt,
            is_active=True
        )
        self.assertEqual(active_prompts.count(), 0)
    
    def test_clear_prompt_with_whitespace(self):
        """Test clearing prompt with whitespace-only content"""
        response = self.client.put(
            f'/api/prompt-labs/{self.session_with_prompt.id}/',
            data=json.dumps({'initial_prompt': '   \n\t   '}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify prompt lab exists (no initial_prompt field to check)
        updated_prompt_lab = PromptLab.objects.get(id=self.session_with_prompt.id)
        
        # Verify system prompt was deactivated
        deactivated_prompt = SystemPrompt.objects.get(id=self.system_prompt.id)
        self.assertFalse(deactivated_prompt.is_active)
    
    def test_update_prompt_with_other_fields(self):
        """Test updating prompt along with other prompt lab fields"""
        new_prompt_content = "Updated prompt with other fields"
        new_name = "Updated PromptLab Name"
        new_description = "Updated prompt lab description"
        
        response = self.client.put(
            f'/api/prompt-labs/{self.session_with_prompt.id}/',
            data=json.dumps({
                'name': new_name,
                'description': new_description,
                'initial_prompt': new_prompt_content
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify all fields were updated
        updated_prompt_lab = PromptLab.objects.get(id=self.session_with_prompt.id)
        self.assertEqual(updated_prompt_lab.name, new_name)
        self.assertEqual(updated_prompt_lab.description, new_description)
        
        # Verify system prompt was updated
        updated_system_prompt = SystemPrompt.objects.get(
            prompt_lab=self.session_with_prompt,
            is_active=True
        )
        self.assertEqual(updated_system_prompt.content, new_prompt_content)
    
    def test_update_prompt_nonexistent_session(self):
        """Test updating prompt for a non-existent prompt lab"""
        fake_prompt_lab_id = uuid.uuid4()
        
        response = self.client.put(
            f'/api/prompt-labs/{fake_prompt_lab_id}/',
            data=json.dumps({'initial_prompt': 'Test prompt'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_prompt_lab_detail_includes_active_prompt(self):
        """Test that prompt lab detail endpoint includes active prompt information"""
        response = self.client.get(f'/api/prompt-labs/{self.session_with_prompt.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify active_prompt information is included
        self.assertIn('active_prompt', data)
        active_prompt = data['active_prompt']
        
        self.assertEqual(active_prompt['content'], self.system_prompt.content)
        self.assertEqual(active_prompt['version'], self.system_prompt.version)
        self.assertIsNotNone(active_prompt['id'])
    
    def test_prompt_lab_detail_no_active_prompt(self):
        """Test prompt lab detail endpoint for prompt lab without active prompt"""
        response = self.client.get(f'/api/prompt-labs/{self.session_without_prompt.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify active_prompt information shows null values
        self.assertIn('active_prompt', data)
        active_prompt = data['active_prompt']
        
        self.assertIsNone(active_prompt['content'])
        self.assertIsNone(active_prompt['version'])
        self.assertIsNone(active_prompt['id'])
    
    def test_prompt_update_preserves_related_data(self):
        """Test that updating prompt doesn't affect other prompt lab data"""
        # Create related data
        email = Email.objects.create(
            prompt_lab=self.session_with_prompt,
            subject="Test Email",
            body="Test email body",
            sender="test@example.com"
        )
        
        preference = UserPreference.objects.create(
            prompt_lab=self.session_with_prompt,
            key="test_key", 
            value="test_value"
        )
        
        # Update prompt
        new_prompt_content = "Updated prompt - should not affect related data"
        response = self.client.put(
            f'/api/prompt-labs/{self.session_with_prompt.id}/',
            data=json.dumps({'initial_prompt': new_prompt_content}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify related data is preserved
        self.assertTrue(Email.objects.filter(id=email.id).exists())
        self.assertTrue(UserPreference.objects.filter(id=preference.id).exists())
        
        # Verify prompt was updated
        updated_prompt_lab = PromptLab.objects.get(id=self.session_with_prompt.id)
        updated_system_prompt = SystemPrompt.objects.get(
            prompt_lab=self.session_with_prompt,
            is_active=True
        )
        self.assertEqual(updated_system_prompt.content, new_prompt_content)


if __name__ == '__main__':
    pytest.main([__file__])