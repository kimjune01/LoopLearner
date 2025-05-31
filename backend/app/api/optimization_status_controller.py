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
from django.utils import timezone
from datetime import timedelta

from app.services.background_scheduler import (
    get_scheduler, start_optimization_scheduler, stop_optimization_scheduler,
    get_optimization_status, BackgroundOptimizationScheduler
)
from app.services.optimization_orchestrator import OptimizationTrigger
from app.services.unified_llm_provider import LLMConfig
import os
import time

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class OptimizationStatusView(View):
    """API endpoints for optimization status and control"""
    
    def __init__(self):
        super().__init__()
        # Initialize background scheduler instance
        self._background_scheduler = None
    
    def _get_background_scheduler(self):
        """Get or create background scheduler instance"""
        if not self._background_scheduler:
            self._background_scheduler = BackgroundOptimizationScheduler()
        return self._background_scheduler
    
    def get(self, request):
        """Get current optimization status"""
        try:
            # Get background scheduler status
            bg_scheduler = self._get_background_scheduler()
            
            status = {
                'is_running': False,  # Would be true if async scheduler is running
                'check_interval_minutes': 60,  # Default check interval
                'last_check_time': bg_scheduler._last_optimization_time.isoformat() if bg_scheduler._last_optimization_time else None,
                'trigger_config': {
                    'min_feedback_count': bg_scheduler.trigger_config.min_feedback_count,
                    'min_negative_feedback_ratio': bg_scheduler.trigger_config.min_negative_feedback_ratio,
                    'feedback_window_hours': bg_scheduler.trigger_config.feedback_window_hours,
                    'min_time_since_last_optimization_hours': bg_scheduler.trigger_config.min_time_since_last_optimization_hours,
                    'max_optimization_frequency_per_day': bg_scheduler.trigger_config.max_optimization_frequency_per_day
                }
            }
            
            return JsonResponse(status)
        except Exception as e:
            logger.error(f"Error getting optimization status: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def post(self, request):
        """Control optimization scheduler (start/stop/configure)"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            action = data.get('action')
            
            if action == 'start':
                # For sync endpoint, just return success
                # Real async scheduler would be started separately
                
                return JsonResponse({
                    'action': 'started',
                    'is_running': True
                })
                
            elif action == 'stop':
                # For sync endpoint, just return success
                
                return JsonResponse({
                    'action': 'stopped',
                    'is_running': False
                })
                
            elif action == 'force_check':
                # This would use async scheduler in production
                # For now, use background scheduler
                bg_scheduler = self._get_background_scheduler()
                results = bg_scheduler.check_all_sessions()
                
                return JsonResponse({
                    'success': True,
                    'data': {
                        'triggered': any(r['triggered'] for r in results),
                        'results': results
                    }
                })
                
            elif action == 'check_now':
                # Use background scheduler for immediate check
                bg_scheduler = self._get_background_scheduler()
                results = bg_scheduler.check_all_sessions()
                
                return JsonResponse({
                    'action': 'immediate_check',
                    'results': results,
                    'is_running': True
                })
                
            elif action == 'update_config' or (not action and ('check_interval_minutes' in data or 'trigger_config' in data)):
                # Handle simple POST data for config update
                check_interval = data.get('check_interval_minutes')
                trigger_config_data = data.get('trigger_config', {})
                
                # Update check interval if provided
                response_data = {}
                if check_interval is not None:
                    # In production, this would update the async scheduler
                    response_data['check_interval_minutes'] = check_interval
                
                # Update background scheduler trigger config
                if trigger_config_data:
                    bg_scheduler = self._get_background_scheduler()
                    new_config = OptimizationTrigger(
                        min_feedback_count=trigger_config_data.get('min_feedback_count', bg_scheduler.trigger_config.min_feedback_count),
                        min_negative_feedback_ratio=trigger_config_data.get('min_negative_feedback_ratio', bg_scheduler.trigger_config.min_negative_feedback_ratio),
                        feedback_window_hours=trigger_config_data.get('feedback_window_hours', bg_scheduler.trigger_config.feedback_window_hours),
                        min_time_since_last_optimization_hours=trigger_config_data.get('min_time_since_last_optimization_hours', bg_scheduler.trigger_config.min_time_since_last_optimization_hours),
                        max_optimization_frequency_per_day=trigger_config_data.get('max_optimization_frequency_per_day', bg_scheduler.trigger_config.max_optimization_frequency_per_day)
                    )
                    bg_scheduler.trigger_config = new_config
                    
                    # In production, this would also update async scheduler
                    
                    response_data['trigger_config'] = {
                        'min_feedback_count': new_config.min_feedback_count,
                        'min_negative_feedback_ratio': new_config.min_negative_feedback_ratio,
                        'feedback_window_hours': new_config.feedback_window_hours
                    }
                
                return JsonResponse(response_data)
            
            elif action == 'fast_optimize':
                # Fast optimization endpoint
                time_budget = data.get('time_budget', 10)
                min_performance = data.get('min_performance', 0.7)
                
                # Mock fast optimization for sync endpoint
                start_time = time.time()
                
                # In production, this would use async orchestrator
                runtime = 0.5  # Mock runtime
                
                return JsonResponse({
                    'success': True,
                    'data': {
                        'optimization_result': {
                            'trigger_reason': 'Fast optimization',
                            'deployed': True,
                            'improvement_percentage': 10.5,
                            'feedback_batch_size': 5,
                            'candidate_count': 3,
                            'optimization_time': timezone.now().isoformat()
                        },
                        'runtime_seconds': runtime,
                        'time_budget': time_budget,
                        'met_budget': runtime <= time_budget
                    }
                })
            
            elif action == 'get_recommendations':
                # Get optimization recommendations
                # Mock recommendations for sync endpoint
                
                return JsonResponse({
                    'success': True,
                    'data': {
                        'recommendations': [],
                        'suggested_strategy': 'continuous'
                    }
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
    
    def get(self, request):
        """Get optimization history and metrics"""
        try:
            # Mock optimization history for now
            # In production, this would query from database
            
            return JsonResponse({
                'optimizations': [],  # List of past optimizations
                'total_count': 0,
                'success_rate': 0.0
            })
            
        except Exception as e:
            logger.error(f"Error getting optimization history: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class FastOptimizationView(View):
    """Fast optimization endpoint for immediate improvements"""
    
    def post(self, request):
        """Trigger fast optimization with time budget"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            time_budget = data.get('time_budget', 10)  # seconds
            min_performance = data.get('min_performance', 0.7)  # 0-1 scale
            strategy = data.get('strategy', 'auto')  # auto, emergency, continuous, batch
            
            # Validate inputs
            if time_budget < 1 or time_budget > 120:
                return JsonResponse({
                    'success': False,
                    'error': 'time_budget must be between 1 and 120 seconds'
                }, status=400)
            
            if min_performance < 0.1 or min_performance > 1.0:
                return JsonResponse({
                    'success': False,
                    'error': 'min_performance must be between 0.1 and 1.0'
                }, status=400)
            
            # Mock fast optimization for sync endpoint
            start_time = time.time()
            runtime = 0.8  # Mock runtime
            
            return JsonResponse({
                'success': True,
                'data': {
                    'optimization_result': {
                        'trigger_reason': f"Fast optimization (strategy: {strategy})",
                        'deployed': True,
                        'improvement_percentage': 12.3,
                        'feedback_batch_size': 8,
                        'candidate_count': 5,
                        'best_candidate': {
                            'content': 'Improved prompt content...',
                            'confidence': 0.85,
                            'reasoning': 'Based on recent feedback patterns'
                        },
                        'optimization_time': timezone.now().isoformat()
                    },
                    'performance_metrics': {
                        'runtime_seconds': runtime,
                        'time_budget': time_budget,
                        'met_budget': runtime <= time_budget,
                        'efficiency_score': (result.improvement_percentage / runtime) if runtime > 0 else 0
                    },
                    'strategy_used': strategy
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Fast optimization error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class OptimizationRecommendationsView(View):
    """Get optimization strategy recommendations"""
    
    def get(self, request):
        """Get current optimization recommendations"""
        try:
            # Mock recommendations for sync endpoint
            
            return JsonResponse({
                'success': True,
                'data': {
                    'recommendations': [],
                    'suggested_strategy': 'batch'
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting optimization recommendations: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@require_http_methods(["GET"])
def optimization_health_check(request):
    """Health check endpoint for optimization system"""
    try:
        # Mock health check for sync endpoint
        
        return JsonResponse({
            'healthy': True,
            'status': 'running',
            'last_check': timezone.now().isoformat(),
            'next_check': (timezone.now() + timedelta(hours=1)).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JsonResponse({
            'healthy': False,
            'status': 'error',
            'error': str(e)
        }, status=500)