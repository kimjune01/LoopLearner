"""
Quick test to verify PromptLab API is working
"""
import pytest
from django.test import TestCase, Client
from core.models import PromptLab


class PromptLabAPITest(TestCase):
    """Simple test to verify PromptLab API functionality"""
    
    def setUp(self):
        self.client = Client()
        self.prompt_lab = PromptLab.objects.create(
            name="Test PromptLab API",
            description="Testing API functionality"
        )
    
    def test_prompt_lab_list_api(self):
        """Test that the PromptLab list API works"""
        response = self.client.get('/api/prompt-labs/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('prompt_labs', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 1)
        
    def test_prompt_lab_detail_api(self):
        """Test that PromptLab detail API works"""
        response = self.client.get(f'/api/prompt-labs/{self.prompt_lab.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], "Test PromptLab API")
        self.assertEqual(data['description'], "Testing API functionality")
    
    def test_prompt_lab_creation_api(self):
        """Test creating a new PromptLab via API"""
        data = {
            'name': 'New PromptLab',
            'description': 'Created via API'
        }
        response = self.client.post('/api/prompt-labs/', data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        result = response.json()
        self.assertEqual(result['name'], 'New PromptLab')
        
        # Verify it was created in database
        self.assertEqual(PromptLab.objects.count(), 2)