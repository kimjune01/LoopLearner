"""
Dashboard API Controller for real-time learning progress monitoring
Provides comprehensive metrics and status visualization for the optimization system
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, Any, List

from app.services.background_scheduler import get_optimization_status
from core.models import (
    SystemPrompt, UserFeedback, Email, Draft, OptimizationRun, 
    EvaluationSnapshot
)

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class DashboardOverviewView(View):
    """Main dashboard overview with key metrics"""
    
    async def get(self, request):
        """Get dashboard overview data"""
        try:
            # Get time ranges for analysis
            now = timezone.now()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            last_30d = now - timedelta(days=30)
            
            # Core system metrics
            overview_data = {
                'system_status': await self._get_system_status(),
                'performance_metrics': await self._get_performance_metrics(last_30d),
                'optimization_activity': await self._get_optimization_activity(last_7d),
                'feedback_trends': await self._get_feedback_trends(last_7d),
                'prompt_evolution': await self._get_prompt_evolution(),
                'real_time_status': await self._get_real_time_status()
            }
            
            return JsonResponse({
                'success': True,
                'data': overview_data,
                'timestamp': now.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        
        # Get optimization scheduler status
        scheduler_status = await get_optimization_status()
        
        # Get active prompt info
        active_prompt = await SystemPrompt.objects.filter(is_active=True).afirst()
        
        # Count recent activity
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        recent_feedback_count = await UserFeedback.objects.filter(
            created_at__gte=last_24h
        ).acount()
        
        recent_optimizations = await OptimizationRun.objects.filter(
            started_at__gte=last_24h
        ).acount()
        
        return {
            'scheduler_running': scheduler_status.get('is_running', False),
            'active_prompt_version': active_prompt.version if active_prompt else None,
            'active_prompt_score': active_prompt.performance_score if active_prompt else None,
            'recent_feedback_count': recent_feedback_count,
            'recent_optimizations': recent_optimizations,
            'last_optimization': scheduler_status.get('last_optimization_time'),
            'next_check': scheduler_status.get('next_check_time'),
            'daily_optimization_count': scheduler_status.get('optimizations_today', 0),
            'can_optimize': scheduler_status.get('can_optimize_now', False)
        }
    
    async def _get_performance_metrics(self, since: datetime) -> Dict[str, Any]:
        """Get performance metrics over time"""
        
        # Performance trend over time
        prompt_versions = []
        async for prompt in SystemPrompt.objects.filter(
            created_at__gte=since
        ).order_by('created_at'):
            prompt_versions.append({
                'version': prompt.version,
                'score': prompt.performance_score,
                'created_at': prompt.created_at.isoformat(),
                'is_active': prompt.is_active
            })
        
        # Calculate performance improvement
        if len(prompt_versions) >= 2:
            latest_score = prompt_versions[-1]['score'] or 0
            baseline_score = prompt_versions[0]['score'] or 0
            improvement = ((latest_score - baseline_score) / baseline_score * 100) if baseline_score > 0 else 0
        else:
            improvement = 0.0
        
        # Feedback quality metrics
        feedback_stats = await self._calculate_feedback_quality(since)
        
        return {
            'prompt_versions': prompt_versions,
            'total_improvement': round(improvement, 2),
            'current_score': prompt_versions[-1]['score'] if prompt_versions else None,
            'baseline_score': prompt_versions[0]['score'] if prompt_versions else None,
            'feedback_quality': feedback_stats
        }
    
    async def _calculate_feedback_quality(self, since: datetime) -> Dict[str, Any]:
        """Calculate feedback quality metrics"""
        
        total_feedback = await UserFeedback.objects.filter(
            created_at__gte=since
        ).acount()
        
        if total_feedback == 0:
            return {
                'total_feedback': 0,
                'acceptance_rate': 0.0,
                'rejection_rate': 0.0,
                'edit_rate': 0.0
            }
        
        # Count by action type
        action_counts = {}
        async for feedback in UserFeedback.objects.filter(created_at__gte=since):
            action_counts[feedback.action] = action_counts.get(feedback.action, 0) + 1
        
        return {
            'total_feedback': total_feedback,
            'acceptance_rate': round((action_counts.get('accept', 0) / total_feedback) * 100, 1),
            'rejection_rate': round((action_counts.get('reject', 0) / total_feedback) * 100, 1),
            'edit_rate': round((action_counts.get('edit', 0) / total_feedback) * 100, 1),
            'ignore_rate': round((action_counts.get('ignore', 0) / total_feedback) * 100, 1)
        }
    
    async def _get_optimization_activity(self, since: datetime) -> Dict[str, Any]:
        """Get optimization activity metrics"""
        
        optimizations = []
        total_runs = 0
        successful_runs = 0
        total_improvement = 0.0
        
        async for opt_run in OptimizationRun.objects.filter(
            started_at__gte=since
        ).select_related('old_prompt', 'new_prompt').order_by('-started_at'):
            
            total_runs += 1
            if opt_run.status == 'completed' and opt_run.new_prompt:
                successful_runs += 1
                if opt_run.performance_improvement:
                    total_improvement += opt_run.performance_improvement
            
            optimizations.append({
                'id': opt_run.id,
                'old_version': opt_run.old_prompt.version,
                'new_version': opt_run.new_prompt.version if opt_run.new_prompt else None,
                'status': opt_run.status,
                'improvement': opt_run.performance_improvement,
                'feedback_count': opt_run.feedback_count,
                'started_at': opt_run.started_at.isoformat(),
                'completed_at': opt_run.completed_at.isoformat() if opt_run.completed_at else None,
                'error_message': opt_run.error_message
            })
        
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
        avg_improvement = (total_improvement / successful_runs) if successful_runs > 0 else 0
        
        return {
            'recent_optimizations': optimizations[:10],  # Last 10
            'total_runs': total_runs,
            'successful_runs': successful_runs,
            'success_rate': round(success_rate, 1),
            'average_improvement': round(avg_improvement, 2)
        }
    
    async def _get_feedback_trends(self, since: datetime) -> Dict[str, Any]:
        """Get feedback trends over time"""
        
        # Group feedback by day
        daily_feedback = {}
        
        async for feedback in UserFeedback.objects.filter(
            created_at__gte=since
        ).order_by('created_at'):
            
            day_key = feedback.created_at.date().isoformat()
            if day_key not in daily_feedback:
                daily_feedback[day_key] = {
                    'total': 0,
                    'accept': 0,
                    'reject': 0,
                    'edit': 0,
                    'ignore': 0
                }
            
            daily_feedback[day_key]['total'] += 1
            daily_feedback[day_key][feedback.action] += 1
        
        # Convert to time series
        trend_data = []
        for date_str, counts in sorted(daily_feedback.items()):
            trend_data.append({
                'date': date_str,
                'total_feedback': counts['total'],
                'acceptance_rate': round((counts['accept'] / counts['total']) * 100, 1),
                'rejection_rate': round((counts['reject'] / counts['total']) * 100, 1),
                'counts': counts
            })
        
        return {
            'daily_trends': trend_data,
            'total_days': len(trend_data)
        }
    
    async def _get_prompt_evolution(self) -> Dict[str, Any]:
        """Get prompt evolution timeline"""
        
        evolution = []
        async for prompt in SystemPrompt.objects.all().order_by('version'):
            evolution.append({
                'version': prompt.version,
                'performance_score': prompt.performance_score,
                'created_at': prompt.created_at.isoformat(),
                'is_active': prompt.is_active,
                'content_preview': prompt.content[:100] + "..." if len(prompt.content) > 100 else prompt.content
            })
        
        return {
            'evolution_timeline': evolution,
            'total_versions': len(evolution),
            'active_version': next((p['version'] for p in evolution if p['is_active']), None)
        }
    
    async def _get_real_time_status(self) -> Dict[str, Any]:
        """Get real-time system status"""
        
        now = timezone.now()
        
        # Recent activity (last hour)
        last_hour = now - timedelta(hours=1)
        recent_emails = await Email.objects.filter(created_at__gte=last_hour).acount()
        recent_drafts = await Draft.objects.filter(created_at__gte=last_hour).acount()
        recent_feedback = await UserFeedback.objects.filter(created_at__gte=last_hour).acount()
        
        # System health indicators
        active_prompt_exists = await SystemPrompt.objects.filter(is_active=True).aexists()
        
        # Learning velocity (feedback per hour over last 24h)
        last_24h = now - timedelta(hours=24)
        feedback_24h = await UserFeedback.objects.filter(created_at__gte=last_24h).acount()
        learning_velocity = round(feedback_24h / 24, 1)
        
        return {
            'last_updated': now.isoformat(),
            'recent_activity': {
                'emails_generated': recent_emails,
                'drafts_created': recent_drafts,
                'feedback_received': recent_feedback
            },
            'system_health': {
                'active_prompt_exists': active_prompt_exists,
                'learning_velocity': learning_velocity,  # feedback per hour
                'system_operational': active_prompt_exists and learning_velocity > 0
            }
        }


@method_decorator(csrf_exempt, name='dispatch')
class LearningMetricsView(View):
    """Detailed learning metrics and analytics"""
    
    async def get(self, request):
        """Get detailed learning analytics"""
        try:
            # Parse query parameters
            days = int(request.GET.get('days', 7))
            since = timezone.now() - timedelta(days=days)
            
            metrics_data = {
                'learning_efficiency': await self._calculate_learning_efficiency(since),
                'feedback_analysis': await self._analyze_feedback_patterns(since),
                'optimization_impact': await self._analyze_optimization_impact(since),
                'performance_correlations': await self._calculate_performance_correlations(since)
            }
            
            return JsonResponse({
                'success': True,
                'data': metrics_data,
                'analysis_period_days': days,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting learning metrics: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def _calculate_learning_efficiency(self, since: datetime) -> Dict[str, Any]:
        """Calculate learning efficiency metrics"""
        
        # Count optimizations and their outcomes
        total_optimizations = await OptimizationRun.objects.filter(
            started_at__gte=since
        ).acount()
        
        successful_optimizations = await OptimizationRun.objects.filter(
            started_at__gte=since,
            status='completed',
            new_prompt__isnull=False
        ).acount()
        
        # Calculate feedback-to-optimization ratio
        total_feedback = await UserFeedback.objects.filter(
            created_at__gte=since
        ).acount()
        
        efficiency_ratio = (successful_optimizations / total_feedback) if total_feedback > 0 else 0
        
        return {
            'total_optimizations': total_optimizations,
            'successful_optimizations': successful_optimizations,
            'total_feedback': total_feedback,
            'efficiency_ratio': round(efficiency_ratio, 4),
            'feedback_per_optimization': round(total_feedback / total_optimizations, 1) if total_optimizations > 0 else 0
        }
    
    async def _analyze_feedback_patterns(self, since: datetime) -> Dict[str, Any]:
        """Analyze feedback patterns for insights"""
        
        feedback_by_scenario = {}
        feedback_by_hour = {}
        
        async for feedback in UserFeedback.objects.filter(
            created_at__gte=since
        ).select_related('draft__email'):
            
            # Group by scenario type
            scenario = feedback.draft.email.scenario_type
            if scenario not in feedback_by_scenario:
                feedback_by_scenario[scenario] = {'total': 0, 'accept': 0, 'reject': 0, 'edit': 0}
            
            feedback_by_scenario[scenario]['total'] += 1
            feedback_by_scenario[scenario][feedback.action] += 1
            
            # Group by hour of day
            hour = feedback.created_at.hour
            if hour not in feedback_by_hour:
                feedback_by_hour[hour] = 0
            feedback_by_hour[hour] += 1
        
        # Calculate acceptance rates by scenario
        scenario_performance = {}
        for scenario, counts in feedback_by_scenario.items():
            scenario_performance[scenario] = {
                'total_feedback': counts['total'],
                'acceptance_rate': round((counts['accept'] / counts['total']) * 100, 1) if counts['total'] > 0 else 0
            }
        
        return {
            'feedback_by_scenario': scenario_performance,
            'feedback_by_hour': feedback_by_hour,
            'peak_hours': sorted(feedback_by_hour.items(), key=lambda x: x[1], reverse=True)[:3]
        }
    
    async def _analyze_optimization_impact(self, since: datetime) -> Dict[str, Any]:
        """Analyze the impact of optimizations"""
        
        impact_data = []
        
        async for opt_run in OptimizationRun.objects.filter(
            started_at__gte=since,
            status='completed',
            new_prompt__isnull=False
        ).select_related('old_prompt', 'new_prompt'):
            
            # Get feedback before and after optimization
            before_feedback = await UserFeedback.objects.filter(
                draft__system_prompt=opt_run.old_prompt,
                created_at__lt=opt_run.completed_at
            ).acount()
            
            after_feedback = await UserFeedback.objects.filter(
                draft__system_prompt=opt_run.new_prompt,
                created_at__gte=opt_run.completed_at
            ).acount()
            
            impact_data.append({
                'optimization_id': opt_run.id,
                'version_change': f"v{opt_run.old_prompt.version} → v{opt_run.new_prompt.version}",
                'performance_improvement': opt_run.performance_improvement,
                'feedback_before': before_feedback,
                'feedback_after': after_feedback,
                'completed_at': opt_run.completed_at.isoformat()
            })
        
        return {
            'optimization_impacts': impact_data,
            'total_analyzed': len(impact_data)
        }
    
    async def _calculate_performance_correlations(self, since: datetime) -> Dict[str, Any]:
        """Calculate correlations between different metrics"""
        
        # This is a simplified correlation analysis
        # In a real system, you'd use statistical libraries
        
        daily_metrics = {}
        
        # Collect daily metrics
        current_date = since.date()
        end_date = timezone.now().date()
        
        while current_date <= end_date:
            day_start = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
            day_end = day_start + timedelta(days=1)
            
            daily_feedback = await UserFeedback.objects.filter(
                created_at__range=(day_start, day_end)
            ).acount()
            
            daily_acceptance = await UserFeedback.objects.filter(
                created_at__range=(day_start, day_end),
                action='accept'
            ).acount()
            
            acceptance_rate = (daily_acceptance / daily_feedback * 100) if daily_feedback > 0 else 0
            
            daily_metrics[current_date.isoformat()] = {
                'total_feedback': daily_feedback,
                'acceptance_rate': acceptance_rate
            }
            
            current_date += timedelta(days=1)
        
        return {
            'daily_metrics': daily_metrics,
            'analysis_note': 'Basic correlation data - statistical analysis would require more sophisticated computation'
        }


@require_http_methods(["GET"])
async def dashboard_summary(request):
    """Quick dashboard summary for health checks and monitoring"""
    try:
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        # Quick counts
        active_prompts = await SystemPrompt.objects.filter(is_active=True).acount()
        recent_feedback = await UserFeedback.objects.filter(created_at__gte=last_24h).acount()
        recent_optimizations = await OptimizationRun.objects.filter(started_at__gte=last_24h).acount()
        
        # System status
        scheduler_status = await get_optimization_status()
        
        return JsonResponse({
            'system_healthy': active_prompts > 0 and scheduler_status.get('is_running', False),
            'active_prompts': active_prompts,
            'recent_feedback_24h': recent_feedback,
            'recent_optimizations_24h': recent_optimizations,
            'scheduler_running': scheduler_status.get('is_running', False),
            'last_check': scheduler_status.get('last_check_time'),
            'timestamp': now.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Dashboard summary error: {e}")
        return JsonResponse({
            'system_healthy': False,
            'error': str(e)
        }, status=500)