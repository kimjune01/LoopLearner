from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404
import json
import asyncio
import logging
from asgiref.sync import sync_to_async

from core.models import Email
from app.services.unified_llm_provider import LLMProviderFactory, EmailDraft
from app.services.email_generator import EmailGenerator
from app.services.human_feedback_integrator import HumanFeedbackIntegrator
from app.services.dual_llm_coordinator import DualLLMCoordinator
from app.services.prompt_rewriter import PPOPromptRewriter
from app.services.reward_aggregator import RewardFunctionAggregator

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class EmailAPIView(View):
    """Base class for email-related API views"""
    
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"API Error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


class GenerateSyntheticEmailView(EmailAPIView):
    """Generate synthetic email for testing"""
    
    async def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
            scenario_type = data.get('scenario_type', 'random')
            
            # Generate synthetic email
            generator = EmailGenerator()
            email_data = await generator.generate_synthetic_email(scenario_type)
            
            # Create Email object
            email = await sync_to_async(Email.objects.create)(
                subject=email_data['subject'],
                body=email_data['content'],
                sender=email_data['sender'],
                scenario_type=scenario_type
            )
            
            return JsonResponse({
                'id': email.id,
                'subject': email.subject,
                'content': email.body,
                'sender': email.sender,
                'scenario_type': email.scenario_type,
                'created_at': email.created_at.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error generating synthetic email: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


class CreateDraftView(EmailAPIView):
    """Create draft response for an email"""
    
    async def post(self, request, email_id):
        try:
            email = await sync_to_async(get_object_or_404)(Email, id=email_id)
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
            
            # Get unified LLM provider
            llm_provider = LLMProviderFactory.from_environment()
            
            # Generate draft response
            draft = await llm_provider.generate_draft_response(
                email_content=email.body,
                context=data.get('context', {})
            )
            
            return JsonResponse({
                'draft_id': draft.id,
                'content': draft.content,
                'prompt_used': draft.prompt_used,
                'model_used': draft.model_used,
                'created_at': draft.created_at.isoformat(),
                'metadata': draft.metadata
            })
            
        except Exception as e:
            logger.error(f"Error creating draft: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


class SubmitFeedbackView(EmailAPIView):
    """Submit user feedback for email/draft"""
    
    async def post(self, request, draft_id):
        try:
            data = json.loads(request.body.decode('utf-8'))
            feedback_type = data.get('feedback_type')  # 'accept', 'reject', 'edit', 'ignore'
            edited_content = data.get('edited_content')
            reasoning_factors = data.get('reasoning_factors', {})
            
            # Process feedback
            integrator = HumanFeedbackIntegrator()
            result = await integrator.process_feedback(
                draft_id=draft_id,
                feedback_type=feedback_type,
                edited_content=edited_content,
                reasoning_factors=reasoning_factors
            )
            
            return JsonResponse({
                'feedback_id': result['feedback_id'],
                'processed': True,
                'learning_signal_strength': result.get('learning_signal_strength', 0.0)
            })
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


class RateReasoningFactorsView(EmailAPIView):
    """Rate reasoning factors for draft quality"""
    
    async def post(self, request, reason_id):
        try:
            data = json.loads(request.body.decode('utf-8'))
            draft_id = data.get('draft_id')
            ratings = data.get('ratings', {})  # {'clarity': 4, 'relevance': 5, etc.}
            
            # Process reasoning factor ratings
            integrator = HumanFeedbackIntegrator()
            result = await integrator.rate_reasoning_factors(
                draft_id=draft_id,
                ratings=ratings
            )
            
            return JsonResponse({
                'rating_id': result['rating_id'],
                'processed': True,
                'updated_preferences': result.get('updated_preferences', {})
            })
            
        except Exception as e:
            logger.error(f"Error rating reasoning factors: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


class GetSystemStateView(EmailAPIView):
    """Get current system state"""
    
    async def get(self, request):
        try:
            # Collect system state from various components
            coordinator = DualLLMCoordinator()
            state = await coordinator.get_system_state()
            
            return JsonResponse({
                'current_prompt': state.get('current_prompt', ''),
                'optimization_history': state.get('optimization_history', []),
                'performance_metrics': state.get('performance_metrics', {}),
                'model_configurations': state.get('model_configurations', {}),
                'timestamp': state.get('timestamp')
            })
            
        except Exception as e:
            logger.error(f"Error getting system state: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


class ExportSystemStateView(EmailAPIView):
    """Export system state for backup/analysis"""
    
    async def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
            export_format = data.get('format', 'json')
            
            coordinator = DualLLMCoordinator()
            export_data = await coordinator.export_system_state(export_format)
            
            return JsonResponse({
                'export_id': export_data['export_id'],
                'format': export_format,
                'size': export_data['size'],
                'download_url': export_data.get('download_url', ''),
                'created_at': export_data['created_at']
            })
            
        except Exception as e:
            logger.error(f"Error exporting system state: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


class ImportSystemStateView(EmailAPIView):
    """Import system state from backup"""
    
    async def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            state_data = data.get('state_data')
            import_options = data.get('options', {})
            
            coordinator = DualLLMCoordinator()
            result = await coordinator.import_system_state(state_data, import_options)
            
            return JsonResponse({
                'import_id': result['import_id'],
                'imported_components': result['imported_components'],
                'conflicts_resolved': result.get('conflicts_resolved', []),
                'warnings': result.get('warnings', [])
            })
            
        except Exception as e:
            logger.error(f"Error importing system state: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


class TriggerOptimizationView(EmailAPIView):
    """Trigger prompt optimization process"""
    
    async def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
            optimization_type = data.get('type', 'conservative')  # conservative, exploratory, hybrid
            target_metrics = data.get('target_metrics', ['f1_score', 'perplexity'])
            
            # Start optimization
            rewriter = PPOPromptRewriter()
            optimization_id = await rewriter.start_optimization(
                optimization_type=optimization_type,
                target_metrics=target_metrics
            )
            
            return JsonResponse({
                'optimization_id': optimization_id,
                'type': optimization_type,
                'target_metrics': target_metrics,
                'status': 'started',
                'estimated_duration': '5-10 minutes'
            })
            
        except Exception as e:
            logger.error(f"Error triggering optimization: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


class GetOptimizationProgressView(EmailAPIView):
    """Get optimization progress"""
    
    async def get(self, request, optimization_id):
        try:
            rewriter = PPOPromptRewriter()
            progress = await rewriter.get_optimization_progress(optimization_id)
            
            return JsonResponse({
                'optimization_id': optimization_id,
                'status': progress['status'],
                'progress_percentage': progress['progress_percentage'],
                'current_iteration': progress['current_iteration'],
                'total_iterations': progress['total_iterations'],
                'best_reward': progress.get('best_reward', 0.0),
                'current_candidates': progress.get('current_candidates', []),
                'estimated_time_remaining': progress.get('estimated_time_remaining', '')
            })
            
        except Exception as e:
            logger.error(f"Error getting optimization progress: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


class HealthCheckView(EmailAPIView):
    """System health check"""
    
    async def get(self, request):
        try:
            # Check various system components
            health_status = {
                'status': 'healthy',
                'components': {},
                'timestamp': None
            }
            
            # Check LLM provider
            try:
                llm_provider = LLMProviderFactory.from_environment()
                await llm_provider.health_check()
                health_status['components']['llm_provider'] = 'healthy'
            except Exception as e:
                health_status['components']['llm_provider'] = f'unhealthy: {str(e)}'
                health_status['status'] = 'degraded'
            
            # Check database connectivity
            try:
                await sync_to_async(Email.objects.count)()
                health_status['components']['database'] = 'healthy'
            except Exception as e:
                health_status['components']['database'] = f'unhealthy: {str(e)}'
                health_status['status'] = 'degraded'
            
            # Check optimization components
            try:
                rewriter = PPOPromptRewriter()
                await rewriter.health_check()
                health_status['components']['optimization_engine'] = 'healthy'
            except Exception as e:
                health_status['components']['optimization_engine'] = f'unhealthy: {str(e)}'
                health_status['status'] = 'degraded'
            
            from datetime import datetime
            health_status['timestamp'] = datetime.now().isoformat()
            
            status_code = 200 if health_status['status'] == 'healthy' else 503
            return JsonResponse(health_status, status=status_code)
            
        except Exception as e:
            logger.error(f"Error in health check: {str(e)}")
            return JsonResponse({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, status=503)


class GetSystemMetricsView(EmailAPIView):
    """Get system performance metrics"""
    
    async def get(self, request):
        try:
            # Collect metrics from various components
            aggregator = RewardFunctionAggregator()
            metrics = await aggregator.get_system_metrics()
            
            return JsonResponse({
                'performance_metrics': metrics.get('performance', {}),
                'optimization_metrics': metrics.get('optimization', {}),
                'resource_usage': metrics.get('resources', {}),
                'user_interaction_stats': metrics.get('user_interactions', {}),
                'model_performance': metrics.get('model_performance', {}),
                'timestamp': metrics.get('timestamp')
            })
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)