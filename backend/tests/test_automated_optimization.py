"""Test automated optimization based on feedback thresholds."""
import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock, call
from core.models import Session, SystemPrompt, UserFeedback, Email, Draft
from app.services.background_scheduler import BackgroundOptimizationScheduler
from app.services.optimization_orchestrator import OptimizationTrigger


class AutomatedOptimizationTests(TestCase):
    """Test automated optimization triggering based on feedback thresholds."""
    
    def setUp(self):
        """Set up test data."""
        # Create session with system prompt
        self.session = Session.objects.create(
            name="Test Session",
            description="Test Description"
        )
        
        self.system_prompt = SystemPrompt.objects.create(
            session=self.session,
            content="You are a helpful assistant.",
            version=1,
            is_active=True
        )
        
        # Create scheduler with test configuration
        self.trigger_config = OptimizationTrigger(
            min_feedback_count=5,
            min_negative_feedback_ratio=0.3,
            feedback_window_hours=24,
            min_time_since_last_optimization_hours=1,
            max_optimization_frequency_per_day=10
        )
        
        self.scheduler = BackgroundOptimizationScheduler(trigger_config=self.trigger_config)
    
    def create_feedback(self, action="reject", hours_ago=0):
        """Helper to create feedback entries."""
        email = Email.objects.create(
            session=self.session,
            subject=f"Test Email",
            body=f"Test body",
            sender="test@example.com",
            scenario_type="inquiry"
        )
        draft = Draft.objects.create(
            email=email,
            content=f"Draft content",
            system_prompt=self.system_prompt
        )
        feedback = UserFeedback.objects.create(
            draft=draft,
            action=action,
            reason=f"Test reason"
        )
        # Adjust created_at if needed
        if hours_ago > 0:
            feedback.created_at = timezone.now() - timedelta(hours=hours_ago)
            feedback.save()
        return feedback
    
    def test_should_trigger_optimization_enough_negative_feedback(self):
        """Test optimization triggers with enough negative feedback."""
        # Create 6 feedback items: 4 reject, 2 accept (66% negative)
        for i in range(4):
            self.create_feedback(action="reject")
        for i in range(2):
            self.create_feedback(action="accept")
        
        with patch.object(self.scheduler, '_execute_optimization') as mock_execute:
            should_trigger = self.scheduler.check_and_trigger_optimization()
            
            self.assertTrue(should_trigger)
            mock_execute.assert_called_once()
    
    def test_should_not_trigger_insufficient_feedback(self):
        """Test optimization doesn't trigger with too few feedback items."""
        # Create only 3 feedback items (below threshold of 5)
        for i in range(3):
            self.create_feedback(action="reject")
        
        with patch.object(self.scheduler, '_execute_optimization') as mock_execute:
            should_trigger = self.scheduler.check_and_trigger_optimization()
            
            self.assertFalse(should_trigger)
            mock_execute.assert_not_called()
    
    def test_should_not_trigger_low_negative_ratio(self):
        """Test optimization doesn't trigger with low negative feedback ratio."""
        # Create 6 feedback items: 1 reject, 5 accept (16% negative, below 30% threshold)
        self.create_feedback(action="reject")
        for i in range(5):
            self.create_feedback(action="accept")
        
        with patch.object(self.scheduler, '_execute_optimization') as mock_execute:
            should_trigger = self.scheduler.check_and_trigger_optimization()
            
            self.assertFalse(should_trigger)
            mock_execute.assert_not_called()
    
    def test_respects_time_window(self):
        """Test only considers feedback within the time window."""
        # Create old feedback (outside 24-hour window)
        for i in range(5):
            self.create_feedback(action="reject", hours_ago=25)
        
        # Create recent feedback (not enough on its own)
        for i in range(2):
            self.create_feedback(action="reject")
        
        with patch.object(self.scheduler, '_execute_optimization') as mock_execute:
            should_trigger = self.scheduler.check_and_trigger_optimization()
            
            # Should not trigger because recent feedback count is below threshold
            self.assertFalse(should_trigger)
            mock_execute.assert_not_called()
    
    def test_respects_optimization_frequency_limit(self):
        """Test respects minimum time between optimizations."""
        # Create feedback that would normally trigger
        for i in range(5):
            self.create_feedback(action="reject")
        
        # Mock a recent optimization
        self.scheduler._last_optimization_time = timezone.now() - timedelta(minutes=30)
        
        with patch.object(self.scheduler, '_execute_optimization') as mock_execute:
            should_trigger = self.scheduler.check_and_trigger_optimization()
            
            # Should not trigger due to recent optimization
            self.assertFalse(should_trigger)
            mock_execute.assert_not_called()
    
    def test_respects_daily_optimization_limit(self):
        """Test respects maximum daily optimization limit."""
        # Create feedback that would normally trigger
        for i in range(5):
            self.create_feedback(action="reject")
        
        # Mock hitting daily limit
        self.scheduler._optimization_count_today = 10
        self.scheduler._last_count_reset_date = timezone.now().date()
        
        with patch.object(self.scheduler, '_execute_optimization') as mock_execute:
            should_trigger = self.scheduler.check_and_trigger_optimization()
            
            # Should not trigger due to daily limit
            self.assertFalse(should_trigger)
            mock_execute.assert_not_called()
    
    def test_resets_daily_count(self):
        """Test daily count resets on new day."""
        # Set count from yesterday
        self.scheduler._optimization_count_today = 10
        self.scheduler._last_count_reset_date = (timezone.now() - timedelta(days=1)).date()
        
        # Create feedback that would trigger
        for i in range(5):
            self.create_feedback(action="reject")
        
        with patch.object(self.scheduler, '_execute_optimization') as mock_execute:
            should_trigger = self.scheduler.check_and_trigger_optimization()
            
            # Should trigger because it's a new day
            self.assertTrue(should_trigger)
            mock_execute.assert_called_once()
            
            # Verify count was reset
            self.assertEqual(self.scheduler._optimization_count_today, 1)
    
    def test_multiple_sessions_isolated(self):
        """Test that optimization only considers feedback from relevant sessions."""
        # Create another session with its own feedback
        other_session = Session.objects.create(
            name="Other Session",
            description="Other Description"
        )
        other_prompt = SystemPrompt.objects.create(
            session=other_session,
            content="Different prompt",
            version=1,
            is_active=True
        )
        
        # Create negative feedback for other session
        for i in range(10):
            email = Email.objects.create(
                session=other_session,
                subject=f"Other Email {i}",
                body=f"Other body {i}",
                sender="other@example.com"
            )
            draft = Draft.objects.create(
                email=email,
                content=f"Other draft {i}",
                system_prompt=other_prompt
            )
            UserFeedback.objects.create(
                draft=draft,
                action="reject",
                reason=f"Other reason {i}"
            )
        
        # Create insufficient feedback for our session
        for i in range(2):
            self.create_feedback(action="reject")
        
        with patch.object(self.scheduler, '_execute_optimization') as mock_execute:
            # Check for our session specifically
            should_trigger = self.scheduler.check_and_trigger_optimization(session=self.session)
            
            # Should not trigger for our session
            self.assertFalse(should_trigger)
            mock_execute.assert_not_called()
            
            # But should trigger for other session
            should_trigger_other = self.scheduler.check_and_trigger_optimization(session=other_session)
            self.assertTrue(should_trigger_other)
    
    @patch('app.services.optimization_orchestrator.OptimizationOrchestrator')
    def test_execute_optimization_success(self, mock_orchestrator_class):
        """Test successful execution of optimization."""
        # Create feedback
        feedback_list = []
        for i in range(5):
            feedback_list.append(self.create_feedback(action="reject"))
        
        # Mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator_class.return_value = mock_orchestrator
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.new_prompt = SystemPrompt.objects.create(
            session=self.session,
            content="Improved prompt",
            version=2,
            is_active=False
        )
        mock_result.improvement_percentage = 12.5
        
        mock_orchestrator.optimize_prompt.return_value = mock_result
        
        # Execute
        result = self.scheduler._execute_optimization(self.session, feedback_list)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['new_prompt_version'], 2)
        self.assertEqual(result['improvement_percentage'], 12.5)
        
        # Verify optimization was called
        mock_orchestrator.optimize_prompt.assert_called_once_with(self.session, feedback_list)
    
    def test_scheduled_check_all_sessions(self):
        """Test scheduled check processes all active sessions."""
        # Create multiple sessions
        sessions = []
        for i in range(3):
            session = Session.objects.create(
                name=f"Session {i}",
                description=f"Description {i}"
            )
            SystemPrompt.objects.create(
                session=session,
                content=f"Prompt {i}",
                version=1,
                is_active=True
            )
            sessions.append(session)
            
            # Add triggering feedback to first two sessions
            if i < 2:
                for j in range(5):
                    email = Email.objects.create(
                        session=session,
                        subject=f"Email {j}",
                        body=f"Body {j}",
                        sender="test@example.com"
                    )
                    draft = Draft.objects.create(
                        email=email,
                        content=f"Draft {j}",
                        system_prompt=session.prompts.first()
                    )
                    UserFeedback.objects.create(
                        draft=draft,
                        action="reject",
                        reason=f"Reason {j}"
                    )
        
        with patch.object(self.scheduler, '_execute_optimization') as mock_execute:
            mock_execute.return_value = {'success': True}
            
            results = self.scheduler.check_all_sessions()
            
            # Should have checked at least our 3 sessions (might be more from other tests)
            self.assertGreaterEqual(len(results), 3)
            
            # Filter to only our test sessions
            test_session_ids = [s.id for s in sessions]
            test_results = [r for r in results if r['session_id'] in test_session_ids]
            
            # Should have checked all 3 test sessions
            self.assertEqual(len(test_results), 3)
            
            # Should have triggered optimization for first 2 sessions
            triggered_count = sum(1 for r in test_results if r['triggered'])
            # Note: The scheduler processes each session with check_all_sessions()
            # which calls check_and_trigger_optimization individually for each session
            self.assertEqual(triggered_count, 2)
            
            # Verify execute was called for the two sessions with feedback
            # Filter calls to only our test sessions
            test_session_names = [s.name for s in sessions[:2]]  # First two have feedback
            executed_sessions = []
            for call in mock_execute.call_args_list:
                session_arg = call[0][0]  # First positional argument is session
                if session_arg.name in test_session_names:
                    executed_sessions.append(session_arg.name)
            
            self.assertEqual(len(executed_sessions), 2)