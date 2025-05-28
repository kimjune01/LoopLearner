"""
Tests for system prompt viewing and export API endpoints
"""

import pytest
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import SystemPrompt
from datetime import datetime


class TestSystemPromptAPI(TestCase):
    """Test system prompt viewing and export endpoints"""

    def setUp(self):
        self.client = APIClient()
        
        # Clear any existing prompts
        SystemPrompt.objects.all().delete()
        
        # Create test system prompts with unique versions
        import time
        version_suffix = int(time.time() * 1000) % 10000  # Use timestamp for unique versions
        
        self.prompt1 = SystemPrompt.objects.create(
            version=version_suffix + 1,
            content="You are a helpful email assistant.",
            is_active=False
        )
        
        self.prompt2 = SystemPrompt.objects.create(
            version=version_suffix + 2,
            content="You are a professional email assistant who provides clear, concise, and helpful responses.",
            is_active=True
        )

    def test_get_system_prompt_returns_active_prompt(self):
        """Test that get system prompt returns the active prompt"""
        url = reverse('get-system-prompt')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return the active prompt (prompt2)
        self.assertEqual(data['id'], self.prompt2.id)
        self.assertEqual(data['version'], self.prompt2.version)
        self.assertEqual(data['content'], self.prompt2.content)
        self.assertTrue(data['is_active'])
        
        # Check metadata
        self.assertIn('metadata', data)
        self.assertEqual(data['metadata']['word_count'], len(self.prompt2.content.split()))
        self.assertEqual(data['metadata']['character_count'], len(self.prompt2.content))
        self.assertEqual(data['metadata']['line_count'], len(self.prompt2.content.splitlines()))

    def test_get_system_prompt_fallback_to_latest(self):
        """Test that get system prompt falls back to latest when no active prompt"""
        # Make all prompts inactive
        SystemPrompt.objects.all().update(is_active=False)
        
        url = reverse('get-system-prompt')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return the latest prompt (prompt2) even though it's not active
        self.assertEqual(data['version'], self.prompt2.version)
        self.assertFalse(data['is_active'])

    def test_get_system_prompt_no_prompts_exist(self):
        """Test get system prompt when no prompts exist"""
        SystemPrompt.objects.all().delete()
        
        url = reverse('get-system-prompt')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        self.assertIn('error', data)

    def test_export_system_prompt_json_format(self):
        """Test exporting system prompt in JSON format"""
        url = reverse('export-system-prompt')
        response = self.client.get(url, {'format': 'json', 'include_metadata': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn(f'system_prompt_v{self.prompt2.version}.json', response['Content-Disposition'])
        
        # Parse the JSON content
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['version'], self.prompt2.version)
        self.assertEqual(data['content'], self.prompt2.content)
        self.assertTrue(data['is_active'])
        self.assertIn('metadata', data)

    def test_export_system_prompt_txt_format(self):
        """Test exporting system prompt in TXT format"""
        url = reverse('export-system-prompt')
        response = self.client.get(url, {'format': 'txt', 'include_metadata': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn(f'system_prompt_v{self.prompt2.version}.txt', response['Content-Disposition'])
        
        content = response.content.decode('utf-8')
        self.assertIn(f'System Prompt v{self.prompt2.version}', content)
        self.assertIn(self.prompt2.content, content)
        self.assertIn('Active: True', content)

    def test_export_system_prompt_md_format(self):
        """Test exporting system prompt in Markdown format"""
        url = reverse('export-system-prompt')
        response = self.client.get(url, {'format': 'md', 'include_metadata': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/markdown')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn(f'system_prompt_v{self.prompt2.version}.md', response['Content-Disposition'])
        
        content = response.content.decode('utf-8')
        self.assertIn(f'# System Prompt v{self.prompt2.version}', content)
        self.assertIn(f'**Version:** {self.prompt2.version}', content)
        self.assertIn('**Active:** True', content)
        self.assertIn(self.prompt2.content, content)
        self.assertIn('## Statistics', content)
        self.assertIn('Word Count:', content)

    def test_export_system_prompt_without_metadata(self):
        """Test exporting system prompt without metadata"""
        url = reverse('export-system-prompt')
        response = self.client.get(url, {'format': 'json', 'include_metadata': 'false'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['version'], self.prompt2.version)
        self.assertEqual(data['content'], self.prompt2.content)
        self.assertTrue(data['is_active'])
        # Should not include detailed metadata
        self.assertNotIn('id', data)
        self.assertNotIn('created_at', data)
        self.assertNotIn('metadata', data)

    def test_export_system_prompt_txt_without_metadata(self):
        """Test exporting TXT format without metadata"""
        url = reverse('export-system-prompt')
        response = self.client.get(url, {'format': 'txt', 'include_metadata': 'false'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        content = response.content.decode('utf-8')
        # Should only contain the prompt content, no metadata headers
        self.assertEqual(content.strip(), self.prompt2.content)

    def test_export_system_prompt_unsupported_format(self):
        """Test exporting with unsupported format"""
        url = reverse('export-system-prompt')
        response = self.client.get(url, {'format': 'xml'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Unsupported export format', data['error'])

    def test_export_system_prompt_default_format(self):
        """Test exporting with default format (JSON)"""
        url = reverse('export-system-prompt')
        response = self.client.get(url)  # No format specified
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['version'], self.prompt2.version)

    def test_export_system_prompt_no_prompts_exist(self):
        """Test export when no prompts exist"""
        SystemPrompt.objects.all().delete()
        
        url = reverse('export-system-prompt')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        self.assertIn('error', data)

    def test_system_prompt_metadata_calculations(self):
        """Test that metadata calculations are correct"""
        # Create a prompt with known content for testing
        test_content = """Line 1
Line 2
Line 3 with multiple words here"""
        
        # Clear existing prompts and create new one
        SystemPrompt.objects.all().delete()
        prompt = SystemPrompt.objects.create(
            version=1000,  # Use high version number to avoid conflicts
            content=test_content,
            is_active=True
        )
        
        url = reverse('get-system-prompt')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify metadata calculations
        expected_word_count = len(test_content.split())  # Should be 10 words
        expected_char_count = len(test_content)
        expected_line_count = len(test_content.splitlines())  # Should be 3 lines
        
        self.assertEqual(data['metadata']['word_count'], expected_word_count)
        self.assertEqual(data['metadata']['character_count'], expected_char_count)
        self.assertEqual(data['metadata']['line_count'], expected_line_count)

    def test_system_prompt_response_format(self):
        """Test that system prompt response includes all required fields"""
        url = reverse('get-system-prompt')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check all required fields are present
        required_fields = [
            'id', 'version', 'content', 'is_active', 
            'created_at', 'updated_at', 'scenario_type', 
            'performance_score', 'metadata'
        ]
        
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field: {field}")
        
        # Check metadata structure
        metadata_fields = ['word_count', 'character_count', 'line_count']
        for field in metadata_fields:
            self.assertIn(field, data['metadata'], f"Missing metadata field: {field}")