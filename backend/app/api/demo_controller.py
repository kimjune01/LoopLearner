"""
API Controller for demonstration workflows
Provides endpoints to run, monitor, and control demo scenarios
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging
from typing import Dict, Any
import asyncio

from app.services.demo_workflow import DemoWorkflowOrchestrator, run_quick_demo
from app.services.unified_llm_provider import LLMConfig
import os

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class DemoWorkflowView(View):
    """API endpoints for running demonstration workflows"""
    
    async def get(self, request):
        """Get available demo scenarios and status"""
        try:
            # Create orchestrator to get scenarios
            llm_config = self._get_llm_config()
            orchestrator = DemoWorkflowOrchestrator(llm_config)
            
            scenarios = []
            for scenario in orchestrator.demo_scenarios:
                scenarios.append({
                    'name': scenario.name,
                    'description': scenario.description,
                    'email_scenarios': scenario.email_scenarios,
                    'expected_improvement': scenario.expected_improvement,
                    'learning_objectives': scenario.learning_objectives
                })
            
            return JsonResponse({
                'success': True,
                'data': {
                    'available_scenarios': scenarios,
                    'total_scenarios': len(scenarios),
                    'demo_status': 'ready'
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting demo scenarios: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def post(self, request):
        """Run a demonstration workflow"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            action = data.get('action', 'run_demo')
            
            if action == 'run_demo':
                scenario_name = data.get('scenario_name', 'Professional Email Optimization')
                llm_config = self._get_llm_config(data.get('llm_config', {}))
                
                # Run complete demo workflow
                orchestrator = DemoWorkflowOrchestrator(llm_config)
                results = await orchestrator.run_complete_demo(scenario_name)
                
                # Generate comprehensive report
                report = await orchestrator.create_demo_report(results)
                
                return JsonResponse({
                    'success': True,
                    'data': {
                        'demo_results': {
                            'scenario_name': results.scenario_name,
                            'total_emails_processed': results.total_emails_processed,
                            'total_feedback_collected': results.total_feedback_collected,
                            'optimizations_triggered': results.optimizations_triggered,
                            'final_performance_improvement': results.final_performance_improvement,
                            'learning_objectives_met': results.learning_objectives_met,
                            'execution_time': str(results.execution_time),
                            'detailed_metrics': results.detailed_metrics
                        },
                        'demo_report': report
                    }
                })
                
            elif action == 'get_guided_steps':
                scenario_name = data.get('scenario_name', 'Professional Email Optimization')
                llm_config = self._get_llm_config()
                
                orchestrator = DemoWorkflowOrchestrator(llm_config)
                steps = await orchestrator.run_guided_demo_steps(scenario_name)
                
                return JsonResponse({
                    'success': True,
                    'data': {
                        'guided_steps': [
                            {
                                'step_number': step.step_number,
                                'title': step.title,
                                'description': step.description,
                                'action_type': step.action_type,
                                'expected_duration': step.expected_duration,
                                'success_criteria': step.success_criteria
                            }
                            for step in steps
                        ],
                        'total_steps': len(steps),
                        'estimated_duration': sum(step.expected_duration for step in steps)
                    }
                })
                
            elif action == 'quick_demo':
                llm_config = self._get_llm_config(data.get('llm_config', {}))
                result = await run_quick_demo(llm_config)
                
                return JsonResponse({
                    'success': result['success'],
                    'data': result
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
            logger.error(f"Error running demo workflow: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _get_llm_config(self, config_override: Dict[str, Any] = None) -> LLMConfig:
        """Get LLM configuration from environment or override"""
        
        config_override = config_override or {}
        
        return LLMConfig(
            provider=config_override.get('provider', os.getenv('LLM_PROVIDER', 'mock')),
            model=config_override.get('model', os.getenv('LLM_MODEL', 'demo-model')),
            api_key=config_override.get('api_key', os.getenv('LLM_API_KEY')),
            base_url=config_override.get('base_url', os.getenv('LLM_BASE_URL')),
            temperature=config_override.get('temperature', 0.7),
            max_tokens=config_override.get('max_tokens', 300)
        )


@method_decorator(csrf_exempt, name='dispatch')
class DemoStatusView(View):
    """API endpoints for demo status and monitoring"""
    
    async def get(self, request):
        """Get current demo system status"""
        try:
            from core.models import SystemPrompt, Email, Draft, UserFeedback, OptimizationRun
            
            # Get demo statistics
            total_emails = await Email.objects.filter(is_synthetic=True).acount()
            total_drafts = await Draft.objects.acount()
            total_feedback = await UserFeedback.objects.acount()
            total_optimizations = await OptimizationRun.objects.acount()
            
            # Get active prompt info
            active_prompt = await SystemPrompt.objects.filter(is_active=True).afirst()
            
            # Get recent activity (last hour)
            from django.utils import timezone
            from datetime import timedelta
            
            last_hour = timezone.now() - timedelta(hours=1)
            recent_emails = await Email.objects.filter(
                created_at__gte=last_hour,
                is_synthetic=True
            ).acount()
            recent_feedback = await UserFeedback.objects.filter(
                created_at__gte=last_hour
            ).acount()
            
            return JsonResponse({
                'success': True,
                'data': {
                    'demo_statistics': {
                        'total_emails': total_emails,
                        'total_drafts': total_drafts,
                        'total_feedback': total_feedback,
                        'total_optimizations': total_optimizations
                    },
                    'active_prompt': {
                        'version': active_prompt.version if active_prompt else None,
                        'performance_score': active_prompt.performance_score if active_prompt else None,
                        'created_at': active_prompt.created_at.isoformat() if active_prompt else None
                    },
                    'recent_activity': {
                        'emails_last_hour': recent_emails,
                        'feedback_last_hour': recent_feedback
                    },
                    'system_health': {
                        'has_active_prompt': active_prompt is not None,
                        'has_feedback_data': total_feedback > 0,
                        'has_optimization_history': total_optimizations > 0,
                        'demo_ready': active_prompt is not None
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting demo status: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@require_http_methods(["POST"])
async def reset_demo_data(request):
    """Reset all demo data for a fresh start"""
    try:
        from core.models import SystemPrompt, Email, Draft, UserFeedback, OptimizationRun
        
        # Count existing data
        emails_count = await Email.objects.filter(is_synthetic=True).acount()
        drafts_count = await Draft.objects.acount()
        feedback_count = await UserFeedback.objects.acount()
        optimization_count = await OptimizationRun.objects.acount()
        
        # Delete demo data (keeping non-synthetic emails if any)
        await Email.objects.filter(is_synthetic=True).adelete()
        await Draft.objects.all().adelete()
        await UserFeedback.objects.all().adelete()
        await OptimizationRun.objects.all().adelete()
        await SystemPrompt.objects.all().adelete()
        
        return JsonResponse({
            'success': True,
            'data': {
                'deleted_counts': {
                    'emails': emails_count,
                    'drafts': drafts_count,
                    'feedback': feedback_count,
                    'optimizations': optimization_count
                },
                'message': 'Demo data reset successfully'
            }
        })
        
    except Exception as e:
        logger.error(f"Error resetting demo data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
async def demo_health_check(request):
    """Health check for demo system"""
    try:
        from core.models import SystemPrompt
        
        # Check if system is ready for demo
        active_prompt = await SystemPrompt.objects.filter(is_active=True).aexists()
        
        return JsonResponse({
            'healthy': True,
            'demo_ready': active_prompt,
            'timestamp': timezone.now().isoformat(),
            'status': 'Demo system operational'
        })
        
    except Exception as e:
        logger.error(f"Demo health check error: {e}")
        return JsonResponse({
            'healthy': False,
            'demo_ready': False,
            'error': str(e),
            'status': 'Demo system error'
        }, status=500)