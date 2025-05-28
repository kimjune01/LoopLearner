"""
API Controller for optimization status and controls
Provides endpoints to monitor and control the automated optimization system
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging
from typing import Dict, Any

from app.services.background_scheduler import (
    get_scheduler, start_optimization_scheduler, stop_optimization_scheduler,
    get_optimization_status
)
from app.services.optimization_orchestrator import OptimizationTrigger
from app.services.unified_llm_provider import LLMConfig
import os

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class OptimizationStatusView(View):
    """API endpoints for optimization status and control"""
    
    async def get(self, request):
        """Get current optimization status"""
        try:
            status = await get_optimization_status()
            return JsonResponse({
                'success': True,
                'data': status
            })
        except Exception as e:
            logger.error(f"Error getting optimization status: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def post(self, request):
        """Control optimization scheduler (start/stop/configure)"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            action = data.get('action')
            
            if action == 'start':
                # Get LLM config from environment or request
                llm_config = self._get_llm_config(data.get('llm_config', {}))
                await start_optimization_scheduler(llm_config)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Optimization scheduler started'
                })
                
            elif action == 'stop':
                await stop_optimization_scheduler()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Optimization scheduler stopped'
                })
                
            elif action == 'force_check':
                scheduler = await get_scheduler()
                result = await scheduler.force_check()
                
                return JsonResponse({
                    'success': True,
                    'data': result
                })
                
            elif action == 'update_config':
                config_data = data.get('config', {})
                trigger_config = OptimizationTrigger(
                    min_feedback_count=config_data.get('min_feedback_count', 10),
                    min_negative_feedback_ratio=config_data.get('min_negative_feedback_ratio', 0.3),
                    feedback_window_hours=config_data.get('feedback_window_hours', 24),
                    min_time_since_last_optimization_hours=config_data.get('min_time_since_last_optimization_hours', 6),
                    max_optimization_frequency_per_day=config_data.get('max_optimization_frequency_per_day', 4)
                )
                
                scheduler = await get_scheduler()
                scheduler.trigger_config = trigger_config
                if scheduler.orchestrator:
                    scheduler.orchestrator.trigger_config = trigger_config
                
                return JsonResponse({
                    'success': True,
                    'message': 'Optimization configuration updated'
                })
                
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Unknown action: {action}'
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Error controlling optimization: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _get_llm_config(self, config_override: Dict[str, Any]) -> LLMConfig:
        """Get LLM configuration from environment or override"""
        
        return LLMConfig(
            provider=config_override.get('provider', os.getenv('LLM_PROVIDER', 'mock')),
            model=config_override.get('model', os.getenv('LLM_MODEL', 'test-model')),
            api_key=config_override.get('api_key', os.getenv('LLM_API_KEY')),
            base_url=config_override.get('base_url', os.getenv('LLM_BASE_URL')),
            temperature=config_override.get('temperature', 0.7),
            max_tokens=config_override.get('max_tokens', 500)
        )


@method_decorator(csrf_exempt, name='dispatch')
class OptimizationHistoryView(View):
    """API endpoints for optimization history and analytics"""
    
    async def get(self, request):
        """Get optimization history and metrics"""
        try:
            # This would typically query a database for optimization history
            # For now, return basic status
            status = await get_optimization_status()
            
            # Mock historical data structure
            history = {
                'recent_optimizations': [],
                'performance_trends': {
                    'total_optimizations': status.get('total_optimizations', 0),
                    'success_rate': 0.85,  # Example metric
                    'average_improvement': 12.3,  # Example metric
                },
                'trigger_frequency': {
                    'negative_feedback': 0.6,
                    'low_ratings': 0.3,
                    'consistent_issues': 0.1
                }
            }
            
            return JsonResponse({
                'success': True,
                'data': history
            })
            
        except Exception as e:
            logger.error(f"Error getting optimization history: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@require_http_methods(["GET"])
async def optimization_health_check(request):
    """Health check endpoint for optimization system"""
    try:
        status = await get_optimization_status()
        
        is_healthy = (
            status.get('is_running', False) and
            status.get('scheduler_initialized', False)
        )
        
        return JsonResponse({
            'healthy': is_healthy,
            'status': 'running' if is_healthy else 'stopped',
            'last_check': status.get('last_check_time'),
            'next_check': status.get('next_check_time')
        })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JsonResponse({
            'healthy': False,
            'status': 'error',
            'error': str(e)
        }, status=500)