import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from django.test import AsyncClient
from django.utils import timezone
from django.urls import reverse

from app.api.dashboard_controller import DashboardOverviewView, LearningMetricsView
from core.models import SystemPrompt, UserFeedback, Email, Draft, OptimizationRun


@pytest.fixture
def async_client():
    return AsyncClient()


@pytest.fixture
def mock_optimization_status():
    return {
        'is_running': True,
        'last_optimization_time': timezone.now() - timedelta(hours=2),
        'next_check_time': timezone.now() + timedelta(minutes=30),
        'optimizations_today': 2,
        'can_optimize_now': True
    }


@pytest.fixture
def sample_prompts():
    """Create sample system prompts for testing"""
    prompts = []
    for i in range(3):
        prompt = MagicMock(spec=SystemPrompt)
        prompt.id = i + 1
        prompt.version = i + 1
        prompt.content = f"Test prompt version {i + 1}"
        prompt.performance_score = 0.6 + (i * 0.1)  # Improving scores
        prompt.is_active = (i == 2)  # Latest is active
        prompt.created_at = timezone.now() - timedelta(days=i)
        prompts.append(prompt)
    return prompts


@pytest.fixture
def sample_feedback():
    """Create sample feedback for testing"""
    feedback_list = []
    actions = ['accept', 'reject', 'edit', 'ignore']
    
    for i in range(12):
        feedback = MagicMock(spec=UserFeedback)
        feedback.id = i + 1
        feedback.action = actions[i % len(actions)]
        feedback.created_at = timezone.now() - timedelta(hours=i)
        
        # Mock draft and email
        feedback.draft = MagicMock()
        feedback.draft.email = MagicMock()
        feedback.draft.email.scenario_type = 'professional' if i % 2 == 0 else 'casual'
        
        feedback_list.append(feedback)
    
    return feedback_list


@pytest.fixture
def sample_optimization_runs():
    """Create sample optimization runs for testing"""
    runs = []
    for i in range(5):
        run = MagicMock(spec=OptimizationRun)
        run.id = i + 1
        run.status = 'completed' if i < 4 else 'failed'
        run.performance_improvement = 5.0 + i if i < 4 else None
        run.feedback_count = 10 + i
        run.started_at = timezone.now() - timedelta(days=i)
        run.completed_at = timezone.now() - timedelta(days=i, hours=-1) if i < 4 else None
        run.error_message = 'Test error' if i == 4 else ''
        
        # Mock prompt relationships
        run.old_prompt = MagicMock()
        run.old_prompt.version = i + 1
        run.new_prompt = MagicMock() if i < 4 else None
        if run.new_prompt:
            run.new_prompt.version = i + 2
        
        runs.append(run)
    
    return runs


class TestDashboardOverviewView:
    
    @pytest.mark.asyncio
    async def test_get_dashboard_overview_success(self, async_client, mock_optimization_status, sample_prompts):
        with patch('app.api.dashboard_controller.get_optimization_status', return_value=mock_optimization_status):
            with patch('app.api.dashboard_controller.SystemPrompt.objects.filter') as mock_filter:
                # Mock active prompt query
                mock_active_query = MagicMock()
                mock_active_query.afirst = AsyncMock(return_value=sample_prompts[2])  # Active prompt
                mock_filter.return_value = mock_active_query
                
                with patch('app.api.dashboard_controller.UserFeedback.objects.filter') as mock_feedback_filter:
                    mock_feedback_query = MagicMock()
                    mock_feedback_query.acount = AsyncMock(return_value=15)
                    mock_feedback_filter.return_value = mock_feedback_query
                    
                    with patch('app.api.dashboard_controller.OptimizationRun.objects.filter') as mock_opt_filter:
                        mock_opt_query = MagicMock()
                        mock_opt_query.acount = AsyncMock(return_value=3)
                        mock_opt_filter.return_value = mock_opt_query
                        
                        response = await async_client.get('/api/dashboard/overview/')
                        
                        assert response.status_code == 200
                        data = json.loads(response.content)
                        
                        assert data['success'] is True
                        assert 'data' in data
                        assert 'timestamp' in data
                        
                        # Check system status
                        system_status = data['data']['system_status']
                        assert system_status['scheduler_running'] is True
                        assert system_status['active_prompt_version'] == 3
                        assert system_status['recent_feedback_count'] == 15
                        assert system_status['recent_optimizations'] == 3

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, async_client, sample_prompts):
        view = DashboardOverviewView()
        
        with patch('app.api.dashboard_controller.SystemPrompt.objects.filter') as mock_filter:
            # Mock queryset with async iteration
            async def mock_aiter():
                for prompt in sample_prompts:
                    yield prompt
            
            mock_queryset = MagicMock()
            mock_queryset.__aiter__ = mock_aiter
            mock_filter.return_value = mock_queryset
            
            since = timezone.now() - timedelta(days=30)
            metrics = await view._get_performance_metrics(since)
            
            assert 'prompt_versions' in metrics
            assert 'total_improvement' in metrics
            assert len(metrics['prompt_versions']) == 3
            assert metrics['total_improvement'] > 0  # Should show improvement

    @pytest.mark.asyncio
    async def test_calculate_feedback_quality(self, async_client, sample_feedback):
        view = DashboardOverviewView()
        
        with patch('app.api.dashboard_controller.UserFeedback.objects.filter') as mock_filter:
            mock_queryset = MagicMock()
            mock_queryset.acount = AsyncMock(return_value=len(sample_feedback))
            
            # Mock async iteration over feedback
            async def mock_aiter():
                for feedback in sample_feedback:
                    yield feedback
            
            mock_queryset.__aiter__ = mock_aiter
            mock_filter.return_value = mock_queryset
            
            since = timezone.now() - timedelta(days=7)
            quality_metrics = await view._calculate_feedback_quality(since)
            
            assert quality_metrics['total_feedback'] == len(sample_feedback)
            assert 'acceptance_rate' in quality_metrics
            assert 'rejection_rate' in quality_metrics
            assert 'edit_rate' in quality_metrics
            assert 'ignore_rate' in quality_metrics
            
            # Verify rates sum to 100% (approximately)
            total_rate = (
                quality_metrics['acceptance_rate'] + 
                quality_metrics['rejection_rate'] + 
                quality_metrics['edit_rate'] + 
                quality_metrics['ignore_rate']
            )
            assert abs(total_rate - 100.0) < 0.1

    @pytest.mark.asyncio
    async def test_get_optimization_activity(self, async_client, sample_optimization_runs):
        view = DashboardOverviewView()
        
        with patch('app.api.dashboard_controller.OptimizationRun.objects.filter') as mock_filter:
            # Mock queryset with select_related and ordering
            mock_queryset = MagicMock()
            mock_queryset.select_related.return_value = mock_queryset
            mock_queryset.order_by.return_value = mock_queryset
            
            # Mock async iteration
            async def mock_aiter():
                for run in sample_optimization_runs:
                    yield run
            
            mock_queryset.__aiter__ = mock_aiter
            mock_filter.return_value = mock_queryset
            
            since = timezone.now() - timedelta(days=7)
            activity = await view._get_optimization_activity(since)
            
            assert 'recent_optimizations' in activity
            assert 'total_runs' in activity
            assert 'successful_runs' in activity
            assert 'success_rate' in activity
            assert 'average_improvement' in activity
            
            assert activity['total_runs'] == 5
            assert activity['successful_runs'] == 4  # 4 completed out of 5
            assert activity['success_rate'] == 80.0  # 4/5 * 100

    @pytest.mark.asyncio
    async def test_get_feedback_trends(self, async_client, sample_feedback):
        view = DashboardOverviewView()
        
        with patch('app.api.dashboard_controller.UserFeedback.objects.filter') as mock_filter:
            mock_queryset = MagicMock()
            mock_queryset.order_by.return_value = mock_queryset
            mock_queryset.select_related.return_value = mock_queryset
            
            # Mock async iteration
            async def mock_aiter():
                for feedback in sample_feedback:
                    yield feedback
            
            mock_queryset.__aiter__ = mock_aiter
            mock_filter.return_value = mock_queryset
            
            since = timezone.now() - timedelta(days=7)
            trends = await view._get_feedback_trends(since)
            
            assert 'daily_trends' in trends
            assert 'total_days' in trends
            assert isinstance(trends['daily_trends'], list)

    @pytest.mark.asyncio
    async def test_get_real_time_status(self, async_client):
        view = DashboardOverviewView()
        
        with patch('app.api.dashboard_controller.Email.objects.filter') as mock_email_filter:
            mock_email_query = MagicMock()
            mock_email_query.acount = AsyncMock(return_value=5)
            mock_email_filter.return_value = mock_email_query
            
            with patch('app.api.dashboard_controller.Draft.objects.filter') as mock_draft_filter:
                mock_draft_query = MagicMock()
                mock_draft_query.acount = AsyncMock(return_value=15)
                mock_draft_filter.return_value = mock_draft_query
                
                with patch('app.api.dashboard_controller.UserFeedback.objects.filter') as mock_feedback_filter:
                    mock_feedback_query = MagicMock()
                    mock_feedback_query.acount = AsyncMock(return_value=8)
                    mock_feedback_filter.return_value = mock_feedback_query
                    
                    with patch('app.api.dashboard_controller.SystemPrompt.objects.filter') as mock_prompt_filter:
                        mock_prompt_query = MagicMock()
                        mock_prompt_query.aexists = AsyncMock(return_value=True)
                        mock_prompt_filter.return_value = mock_prompt_query
                        
                        status = await view._get_real_time_status()
                        
                        assert 'last_updated' in status
                        assert 'recent_activity' in status
                        assert 'system_health' in status
                        
                        recent_activity = status['recent_activity']
                        assert recent_activity['emails_generated'] == 5
                        assert recent_activity['drafts_created'] == 15
                        assert recent_activity['feedback_received'] == 8
                        
                        system_health = status['system_health']
                        assert system_health['active_prompt_exists'] is True
                        assert system_health['learning_velocity'] > 0

    @pytest.mark.asyncio
    async def test_dashboard_overview_error_handling(self, async_client):
        with patch('app.api.dashboard_controller.get_optimization_status', side_effect=Exception("Test error")):
            response = await async_client.get('/api/dashboard/overview/')
            
            assert response.status_code == 500
            data = json.loads(response.content)
            assert data['success'] is False
            assert 'error' in data


class TestLearningMetricsView:
    
    @pytest.mark.asyncio
    async def test_get_learning_metrics_success(self, async_client):
        with patch('app.api.dashboard_controller.OptimizationRun.objects.filter') as mock_filter:
            mock_query = MagicMock()
            mock_query.acount = AsyncMock(return_value=10)
            mock_filter.return_value = mock_query
            
            with patch('app.api.dashboard_controller.UserFeedback.objects.filter') as mock_feedback_filter:
                mock_feedback_query = MagicMock()
                mock_feedback_query.acount = AsyncMock(return_value=50)
                mock_feedback_filter.return_value = mock_feedback_query
                
                # Mock async iteration for feedback analysis
                async def mock_feedback_aiter():
                    for i in range(5):
                        feedback = MagicMock()
                        feedback.draft = MagicMock()
                        feedback.draft.email = MagicMock()
                        feedback.draft.email.scenario_type = 'professional'
                        feedback.action = 'accept' if i % 2 == 0 else 'reject'
                        feedback.created_at = timezone.now() - timedelta(hours=i)
                        yield feedback
                
                mock_feedback_query.__aiter__ = mock_feedback_aiter
                
                response = await async_client.get('/api/dashboard/metrics/?days=7')
                
                assert response.status_code == 200
                data = json.loads(response.content)
                
                assert data['success'] is True
                assert 'data' in data
                assert data['analysis_period_days'] == 7
                
                metrics_data = data['data']
                assert 'learning_efficiency' in metrics_data
                assert 'feedback_analysis' in metrics_data
                assert 'optimization_impact' in metrics_data
                assert 'performance_correlations' in metrics_data

    @pytest.mark.asyncio
    async def test_calculate_learning_efficiency(self, async_client):
        view = LearningMetricsView()
        
        with patch('app.api.dashboard_controller.OptimizationRun.objects.filter') as mock_filter:
            # Mock total optimizations query
            mock_total_query = MagicMock()
            mock_total_query.acount = AsyncMock(return_value=8)
            
            # Mock successful optimizations query  
            mock_success_query = MagicMock()
            mock_success_query.acount = AsyncMock(return_value=6)
            
            mock_filter.side_effect = [mock_total_query, mock_success_query]
            
            with patch('app.api.dashboard_controller.UserFeedback.objects.filter') as mock_feedback_filter:
                mock_feedback_query = MagicMock()
                mock_feedback_query.acount = AsyncMock(return_value=40)
                mock_feedback_filter.return_value = mock_feedback_query
                
                since = timezone.now() - timedelta(days=7)
                efficiency = await view._calculate_learning_efficiency(since)
                
                assert efficiency['total_optimizations'] == 8
                assert efficiency['successful_optimizations'] == 6
                assert efficiency['total_feedback'] == 40
                assert efficiency['efficiency_ratio'] == 6/40  # 0.15
                assert efficiency['feedback_per_optimization'] == 40/8  # 5.0

    @pytest.mark.asyncio
    async def test_analyze_feedback_patterns(self, async_client):
        view = LearningMetricsView()
        
        # Create mock feedback with different scenarios and times
        mock_feedback = []
        for i in range(10):
            feedback = MagicMock()
            feedback.draft = MagicMock()
            feedback.draft.email = MagicMock()
            feedback.draft.email.scenario_type = 'professional' if i % 2 == 0 else 'casual'
            feedback.action = 'accept' if i < 5 else 'reject'
            feedback.created_at = timezone.now().replace(hour=9 + (i % 12))  # Spread across hours
            mock_feedback.append(feedback)
        
        with patch('app.api.dashboard_controller.UserFeedback.objects.filter') as mock_filter:
            mock_queryset = MagicMock()
            mock_queryset.select_related.return_value = mock_queryset
            
            async def mock_aiter():
                for feedback in mock_feedback:
                    yield feedback
            
            mock_queryset.__aiter__ = mock_aiter
            mock_filter.return_value = mock_queryset
            
            since = timezone.now() - timedelta(days=7)
            patterns = await view._analyze_feedback_patterns(since)
            
            assert 'feedback_by_scenario' in patterns
            assert 'feedback_by_hour' in patterns
            assert 'peak_hours' in patterns
            
            # Check scenario analysis
            scenario_data = patterns['feedback_by_scenario']
            assert 'professional' in scenario_data
            assert 'casual' in scenario_data
            
            # Each scenario should have 5 feedback items
            assert scenario_data['professional']['total_feedback'] == 5
            assert scenario_data['casual']['total_feedback'] == 5

    @pytest.mark.asyncio
    async def test_learning_metrics_error_handling(self, async_client):
        with patch('app.api.dashboard_controller.OptimizationRun.objects.filter', side_effect=Exception("Database error")):
            response = await async_client.get('/api/dashboard/metrics/')
            
            assert response.status_code == 500
            data = json.loads(response.content)
            assert data['success'] is False
            assert 'error' in data


class TestDashboardSummary:
    
    @pytest.mark.asyncio
    async def test_dashboard_summary_success(self, async_client, mock_optimization_status):
        with patch('app.api.dashboard_controller.get_optimization_status', return_value=mock_optimization_status):
            with patch('app.api.dashboard_controller.SystemPrompt.objects.filter') as mock_prompt_filter:
                mock_prompt_query = MagicMock()
                mock_prompt_query.acount = AsyncMock(return_value=1)
                mock_prompt_filter.return_value = mock_prompt_query
                
                with patch('app.api.dashboard_controller.UserFeedback.objects.filter') as mock_feedback_filter:
                    mock_feedback_query = MagicMock()
                    mock_feedback_query.acount = AsyncMock(return_value=25)
                    mock_feedback_filter.return_value = mock_feedback_query
                    
                    with patch('app.api.dashboard_controller.OptimizationRun.objects.filter') as mock_opt_filter:
                        mock_opt_query = MagicMock()
                        mock_opt_query.acount = AsyncMock(return_value=3)
                        mock_opt_filter.return_value = mock_opt_query
                        
                        response = await async_client.get('/api/dashboard/summary/')
                        
                        assert response.status_code == 200
                        data = json.loads(response.content)
                        
                        assert data['system_healthy'] is True
                        assert data['active_prompts'] == 1
                        assert data['recent_feedback_24h'] == 25
                        assert data['recent_optimizations_24h'] == 3
                        assert data['scheduler_running'] is True
                        assert 'timestamp' in data

    @pytest.mark.asyncio
    async def test_dashboard_summary_unhealthy_system(self, async_client):
        mock_status = {
            'is_running': False,
            'last_check_time': None
        }
        
        with patch('app.api.dashboard_controller.get_optimization_status', return_value=mock_status):
            with patch('app.api.dashboard_controller.SystemPrompt.objects.filter') as mock_prompt_filter:
                mock_prompt_query = MagicMock()
                mock_prompt_query.acount = AsyncMock(return_value=0)  # No active prompts
                mock_prompt_filter.return_value = mock_prompt_query
                
                with patch('app.api.dashboard_controller.UserFeedback.objects.filter') as mock_feedback_filter:
                    mock_feedback_query = MagicMock()
                    mock_feedback_query.acount = AsyncMock(return_value=5)
                    mock_feedback_filter.return_value = mock_feedback_query
                    
                    with patch('app.api.dashboard_controller.OptimizationRun.objects.filter') as mock_opt_filter:
                        mock_opt_query = MagicMock()
                        mock_opt_query.acount = AsyncMock(return_value=0)
                        mock_opt_filter.return_value = mock_opt_query
                        
                        response = await async_client.get('/api/dashboard/summary/')
                        
                        assert response.status_code == 200
                        data = json.loads(response.content)
                        
                        assert data['system_healthy'] is False  # No active prompts and scheduler not running
                        assert data['active_prompts'] == 0
                        assert data['scheduler_running'] is False

    @pytest.mark.asyncio
    async def test_dashboard_summary_error_handling(self, async_client):
        with patch('app.api.dashboard_controller.get_optimization_status', side_effect=Exception("Status error")):
            response = await async_client.get('/api/dashboard/summary/')
            
            assert response.status_code == 500
            data = json.loads(response.content)
            assert data['system_healthy'] is False
            assert 'error' in data