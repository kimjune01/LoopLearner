import pytest
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, AsyncMock
from core.models import Email, SystemPrompt, Draft, UserFeedback, UserPreference
from app.services.unified_llm_provider import EmailDraft


class EmailEndpointsTest(APITestCase):
    """Test email generation and draft creation endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.system_prompt = SystemPrompt.objects.create(
            content="You are a helpful email assistant.",
            version=1
        )
        
        self.user_preference = UserPreference.objects.create(
            key="tone",
            value="professional",
            description="Maintain professional tone",
            is_active=True
        )
        
        self.sample_email_data = {
            "sender": "john@example.com",
            "subject": "Meeting Request",
            "body": "Hi, can we schedule a meeting for next week?",
            "scenario_type": "professional"
        }
    
    def test_generate_synthetic_email_endpoint_exists(self):
        """Test that synthetic email generation endpoint exists"""
        url = reverse('generate-synthetic-email')
        response = self.client.post(url, {
            "scenario": "professional",
            "complexity": "medium"
        })
        # Should not return 404 (endpoint exists)
        self.assertNotEqual(response.status_code, 404)
    
    def test_generate_synthetic_email_creates_email(self):
        """Test synthetic email generation creates Email object"""
        url = reverse('generate-synthetic-email')
        
        with patch('app.services.unified_llm_provider.LLMProviderFactory.from_environment') as mock_provider:
            mock_llm = AsyncMock()
            mock_llm.generate.return_value = """
            From: sarah@company.com
            Subject: Project Update Required
            
            Hi team,
            
            I need an update on the Q4 project timeline. Can someone provide 
            a status report by Friday?
            
            Thanks,
            Sarah
            """
            mock_provider.return_value = mock_llm
            
            response = self.client.post(url, {
                "scenario": "professional",
                "complexity": "medium"
            })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('email_id', response.data)
        self.assertIn('sender', response.data)
        self.assertIn('subject', response.data)
        self.assertIn('body', response.data)
        
        # Verify email was created in database
        email_id = response.data['email_id']
        email = Email.objects.get(id=email_id)
        self.assertEqual(email.scenario_type, "professional")
    
    def test_generate_drafts_endpoint_exists(self):
        """Test that draft generation endpoint exists"""
        email = Email.objects.create(**self.sample_email_data)
        url = reverse('generate-drafts', kwargs={'email_id': email.id})
        
        response = self.client.post(url, {
            "num_drafts": 2,
            "preferences": [{"key": "tone", "value": "casual"}]
        })
        # Should not return 404 (endpoint exists)
        self.assertNotEqual(response.status_code, 404)
    
    def test_generate_drafts_creates_draft_objects(self):
        """Test draft generation creates Draft objects with reasoning"""
        email = Email.objects.create(**self.sample_email_data)
        url = reverse('generate-drafts', kwargs={'email_id': email.id})
        
        with patch('app.services.unified_llm_provider.LLMProviderFactory.from_environment') as mock_provider:
            mock_llm = AsyncMock()
            mock_llm.generate_drafts.return_value = [
                EmailDraft(
                    content="Hi John, I'd be happy to schedule a meeting. How about Tuesday at 2 PM?",
                    reasoning=["Professional tone maintained", "Specific time suggested", "Friendly approach"],
                    confidence=0.85,
                    draft_id=1
                ),
                EmailDraft(
                    content="Hello! Sure, let's meet next week. What day works best for you?",
                    reasoning=["Casual friendly tone", "Open-ended question", "Shows flexibility"],
                    confidence=0.78,
                    draft_id=2
                )
            ]
            mock_provider.return_value = mock_llm
            
            response = self.client.post(url, {
                "num_drafts": 2,
                "preferences": [{"key": "tone", "value": "casual"}]
            })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['drafts']), 2)
        
        # Check draft structure
        draft_data = response.data['drafts'][0]
        self.assertIn('id', draft_data)
        self.assertIn('content', draft_data)
        self.assertIn('reasoning', draft_data)
        self.assertIn('confidence', draft_data)
        
        # Verify drafts were created in database
        drafts = Draft.objects.filter(email=email)
        self.assertEqual(drafts.count(), 2)
        
        # Verify reasoning was stored
        first_draft = drafts.first()
        self.assertEqual(first_draft.reasoning.count(), 3)
    
    def test_generate_drafts_with_constraints(self):
        """Test draft generation with length and tone constraints"""
        email = Email.objects.create(**self.sample_email_data)
        url = reverse('generate-drafts', kwargs={'email_id': email.id})
        
        with patch('app.services.unified_llm_provider.LLMProviderFactory.from_environment') as mock_provider:
            mock_llm = AsyncMock()
            mock_llm.generate_drafts.return_value = [
                EmailDraft(
                    content="Brief response meeting request.",
                    reasoning=["Concise as requested", "Direct approach", "Meets length constraint"],
                    confidence=0.90,
                    draft_id=1
                )
            ]
            mock_provider.return_value = mock_llm
            
            response = self.client.post(url, {
                "num_drafts": 1,
                "constraints": {
                    "max_length": 50,
                    "tone": "direct"
                }
            })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify LLM was called with constraints
        mock_llm.generate_drafts.assert_called_once()
        call_args = mock_llm.generate_drafts.call_args
        self.assertIn('constraints', call_args.kwargs)
        self.assertEqual(call_args.kwargs['constraints']['max_length'], 50)
    
    def test_generate_drafts_invalid_email_id(self):
        """Test draft generation with non-existent email ID"""
        url = reverse('generate-drafts', kwargs={'email_id': 99999})
        
        response = self.client.post(url, {"num_drafts": 1})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_generate_drafts_invalid_request_data(self):
        """Test draft generation with invalid request data"""
        email = Email.objects.create(**self.sample_email_data)
        url = reverse('generate-drafts', kwargs={'email_id': email.id})
        
        # Missing required fields
        response = self.client.post(url, {})
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Invalid num_drafts
        response = self.client.post(url, {"num_drafts": -1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FeedbackEndpointsTest(APITestCase):
    """Test feedback collection and processing endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.email = Email.objects.create(
            sender="test@example.com",
            subject="Test Email",
            body="Test email body",
            scenario_type="professional"
        )
        
        self.draft = Draft.objects.create(
            email=self.email,
            content="Test draft response"
        )
    
    def test_submit_feedback_endpoint_exists(self):
        """Test that feedback submission endpoint exists"""
        url = reverse('submit-feedback', kwargs={'draft_id': self.draft.id})
        response = self.client.post(url, {
            "action": "accept",
            "reason": "Good response"
        })
        # Should not return 404 (endpoint exists)
        self.assertNotEqual(response.status_code, 404)
    
    def test_submit_feedback_accept_action(self):
        """Test submitting accept feedback"""
        url = reverse('submit-feedback', kwargs={'draft_id': self.draft.id})
        
        with patch('app.services.human_feedback_integrator.HumanFeedbackIntegrator') as mock_integrator:
            mock_hfi = AsyncMock()
            mock_hfi.process_user_feedback.return_value = type('Signal', (), {
                'reward_value': 1.0,
                'confidence': 0.9,
                'action': 'accept'
            })()
            mock_integrator.return_value = mock_hfi
            
            response = self.client.post(url, {
                "action": "accept",
                "reason": "Perfect response, exactly what I needed"
            })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('feedback_id', response.data)
        self.assertEqual(response.data['action'], 'accept')
        
        # Verify feedback was created in database
        feedback = UserFeedback.objects.get(id=response.data['feedback_id'])
        self.assertEqual(feedback.action, 'accept')
        self.assertEqual(feedback.draft, self.draft)
    
    def test_submit_feedback_reject_action(self):
        """Test submitting reject feedback with reason"""
        url = reverse('submit-feedback', kwargs={'draft_id': self.draft.id})
        
        response = self.client.post(url, {
            "action": "reject",
            "reason": "Too formal for this context"
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify feedback was created
        feedback = UserFeedback.objects.get(id=response.data['feedback_id'])
        self.assertEqual(feedback.action, 'reject')
        self.assertEqual(feedback.reason, "Too formal for this context")
    
    def test_submit_feedback_edit_action(self):
        """Test submitting edit feedback with edited content"""
        url = reverse('submit-feedback', kwargs={'draft_id': self.draft.id})
        
        response = self.client.post(url, {
            "action": "edit",
            "reason": "Needed to be more concise",
            "edited_content": "Thanks, I can meet Tuesday at 2 PM."
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify feedback was created with edited content
        feedback = UserFeedback.objects.get(id=response.data['feedback_id'])
        self.assertEqual(feedback.action, 'edit')
        self.assertEqual(feedback.edited_content, "Thanks, I can meet Tuesday at 2 PM.")
    
    def test_submit_feedback_ignore_action(self):
        """Test submitting ignore feedback"""
        url = reverse('submit-feedback', kwargs={'draft_id': self.draft.id})
        
        response = self.client.post(url, {
            "action": "ignore",
            "reason": "Email no longer relevant"
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify feedback was created
        feedback = UserFeedback.objects.get(id=response.data['feedback_id'])
        self.assertEqual(feedback.action, 'ignore')
    
    def test_submit_feedback_invalid_action(self):
        """Test submitting feedback with invalid action"""
        url = reverse('submit-feedback', kwargs={'draft_id': self.draft.id})
        
        response = self.client.post(url, {
            "action": "invalid_action",
            "reason": "Test reason"
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('action', response.data)
    
    def test_submit_feedback_missing_required_fields(self):
        """Test submitting feedback with missing required fields"""
        url = reverse('submit-feedback', kwargs={'draft_id': self.draft.id})
        
        # Missing action
        response = self.client.post(url, {
            "reason": "Test reason"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing reason for reject action
        response = self.client.post(url, {
            "action": "reject"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_rate_reasoning_factor_endpoint(self):
        """Test rating individual reasoning factors"""
        # Create reasoning for draft
        from core.models import DraftReason
        reason = DraftReason.objects.create(
            draft=self.draft,
            factor="Professional tone maintained",
            order=1
        )
        
        url = reverse('rate-reasoning', kwargs={'reason_id': reason.id})
        
        response = self.client.post(url, {
            "liked": True,
            "comment": "Yes, this was important"
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify rating was created
        from core.models import ReasonRating
        rating = ReasonRating.objects.get(reason=reason)
        self.assertTrue(rating.liked)
        self.assertEqual(rating.comment, "Yes, this was important")


class StateEndpointsTest(APITestCase):
    """Test state management and export endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.system_prompt = SystemPrompt.objects.create(
            content="You are helpful.",
            version=1
        )
        
        self.user_preference = UserPreference.objects.create(
            key="tone",
            value="professional",
            is_active=True
        )
    
    def test_get_system_state_endpoint(self):
        """Test retrieving current system state"""
        url = reverse('get-system-state')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('current_prompt', response.data)
        self.assertIn('user_preferences', response.data)
        self.assertIn('confidence_score', response.data)
        self.assertIn('optimization_history', response.data)
    
    def test_export_system_state_endpoint(self):
        """Test exporting complete system state as JSON"""
        url = reverse('export-system-state')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('Content-Disposition', response)
        
        # Verify exported data structure
        exported_data = json.loads(response.content)
        self.assertIn('current_prompt', exported_data)
        self.assertIn('user_preferences', exported_data)
        self.assertIn('evaluation_snapshots', exported_data)
        self.assertIn('export_timestamp', exported_data)
    
    def test_import_system_state_endpoint(self):
        """Test importing system state from JSON"""
        url = reverse('import-system-state')
        
        import_data = {
            "current_prompt": {
                "content": "You are a helpful assistant.",
                "version": 2
            },
            "user_preferences": [
                {"key": "tone", "value": "casual", "is_active": True}
            ],
            "evaluation_snapshots": []
        }
        
        response = self.client.post(url, 
            data=json.dumps(import_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('imported_items', response.data)
        
        # Verify data was imported
        new_prompt = SystemPrompt.objects.filter(version=2).first()
        self.assertIsNotNone(new_prompt)
        self.assertEqual(new_prompt.content, "You are a helpful assistant.")


class OptimizationEndpointsTest(APITestCase):
    """Test prompt optimization and learning endpoints"""
    
    def test_trigger_optimization_endpoint(self):
        """Test triggering prompt optimization cycle"""
        url = reverse('trigger-optimization')
        
        with patch('app.services.prompt_rewriter.PPOPromptRewriter') as mock_rewriter:
            mock_rewriter.return_value = AsyncMock()
            
            response = self.client.post(url, {
                "optimization_mode": "conservative",
                "max_iterations": 3
            })
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('optimization_id', response.data)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'started')
    
    def test_get_optimization_status_endpoint(self):
        """Test getting optimization status"""
        # Create optimization record
        from core.models import OptimizationRun
        optimization = OptimizationRun.objects.create(
            status='running',
            mode='conservative',
            progress=0.3
        )
        
        url = reverse('get-optimization-status', kwargs={'optimization_id': optimization.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'running')
        self.assertEqual(response.data['progress'], 0.3)
    
    def test_get_learning_progress_endpoint(self):
        """Test getting overall learning progress metrics"""
        url = reverse('get-learning-progress')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_feedback', response.data)
        self.assertIn('confidence_trend', response.data)
        self.assertIn('optimization_runs', response.data)
        self.assertIn('performance_metrics', response.data)


class HealthEndpointsTest(APITestCase):
    """Test system health and status endpoints"""
    
    def test_health_check_endpoint(self):
        """Test basic health check endpoint"""
        url = reverse('health-check')
        
        with patch('app.services.unified_llm_provider.LLMProviderFactory.from_environment') as mock_provider:
            mock_llm = AsyncMock()
            mock_llm.health_check.return_value = {
                "status": "healthy",
                "provider": "ollama",
                "model": "llama3.2:3b"
            }
            mock_provider.return_value = mock_llm
            
            response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('llm_provider', response.data)
        self.assertIn('database', response.data)
        self.assertIn('timestamp', response.data)
    
    def test_system_metrics_endpoint(self):
        """Test system metrics and performance endpoint"""
        url = reverse('system-metrics')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_emails', response.data)
        self.assertIn('total_drafts', response.data)
        self.assertIn('total_feedback', response.data)
        self.assertIn('avg_response_time', response.data)
        self.assertIn('success_rate', response.data)