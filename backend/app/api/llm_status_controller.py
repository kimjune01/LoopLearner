"""
LLM Status API controller for getting current LLM provider information
"""

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from app.services.unified_llm_provider import LLMProviderFactory
import asyncio


@method_decorator(csrf_exempt, name='dispatch')
class LLMStatusView(View):
    """
    Get current LLM provider status and configuration
    GET /api/llm/status/
    """
    
    def get(self, request):
        """Get LLM provider status"""
        try:
            # Get the current provider
            provider = LLMProviderFactory.from_environment()
            
            # Get health status
            health_check = asyncio.run(provider.health_check())
            
            return JsonResponse({
                'provider': provider.config.provider,
                'model': provider.config.model,
                'status': health_check.get('status', 'unknown'),
                'health': health_check,
                'base_url': provider.config.base_url,
                'temperature': provider.config.temperature,
                'max_tokens': provider.config.max_tokens
            })
            
        except Exception as e:
            return JsonResponse({
                'provider': 'unknown',
                'model': 'unknown',
                'status': 'error',
                'error': str(e)
            }, status=500)