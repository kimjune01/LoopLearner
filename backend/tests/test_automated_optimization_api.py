"""Test automated optimization API endpoints."""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from core.models import PromptLab, SystemPrompt


class AutomatedOptimizationAPITests(APITestCase):
    """Test API endpoints for automated optimization control."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        # Create test 
        self.prompt_lab = PromptLab.objects.create(
            name="Test PromptLab",
            description="Test Description"
        )
        
        self.system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="You are a helpful assistant.",
            version=1,
            is_active=True
        )
    
    def test_get_optimization_scheduler_status(self):
        """Test getting optimization scheduler status."""
        url = reverse('optimization-scheduler')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('is_running', data)
        self.assertIn('check_interval_minutes', data)
        self.assertIn('trigger_config', data)
        self.assertIn('last_check_time', data)
    
    def test_update_scheduler_configuration(self):
        """Test updating scheduler configuration."""
        url = reverse('optimization-scheduler')
        data = {
            'check_interval_minutes': 30,
            'trigger_config': {
                'min_feedback_count': 10,
                'min_negative_feedback_ratio': 0.4,
                'feedback_window_hours': 12
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['check_interval_minutes'], 30)
        self.assertEqual(data['trigger_config']['min_feedback_count'], 10)
    
    def test_trigger_immediate_check(self):
        """Test triggering immediate optimization check."""
        url = reverse('optimization-scheduler')
        
        # Create feedback to trigger optimization
        from core.models import Email, Draft, UserFeedback
        for i in range(5):
            email = Email.objects.create(
                prompt_lab=self.prompt_lab,
                subject=f"Test Email {i}",
                body=f"Test body {i}",
                sender="test@example.com"
            )
            draft = Draft.objects.create(
                email=email,
                content=f"Draft content {i}",
                system_prompt=self.system_prompt
            )
            UserFeedback.objects.create(
                draft=draft,
                action="reject",
                reason=f"Test reason {i}"
            )
        
        response = self.client.post(url, {'action': 'check_now'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['action'], 'immediate_check')
        self.assertIsInstance(data['results'], list)
        # At least one  should be checked
        self.assertGreaterEqual(len(data['results']), 1)
    
    def test_start_scheduler(self):
        """Test starting the optimization scheduler."""
        url = reverse('optimization-scheduler')
        
        response = self.client.post(url, {'action': 'start'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['action'], 'started')
        self.assertTrue(data['is_running'])
    
    def test_stop_scheduler(self):
        """Test stopping the optimization scheduler."""
        url = reverse('optimization-scheduler')
        
        response = self.client.post(url, {'action': 'stop'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['action'], 'stopped')
        self.assertFalse(data['is_running'])
    
    def test_get_optimization_history(self):
        """Test getting optimization history."""
        url = reverse('optimization-history')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('optimizations', data)
        self.assertIn('total_count', data)
        self.assertIn('success_rate', data)