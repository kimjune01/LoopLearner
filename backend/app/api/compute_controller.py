"""
Compute Management API Controller
Provides visibility and control over LLM compute spend
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
import logging

from core.models import PromptLab
from app.services.compute_optimizer import ComputeOptimizer

logger = logging.getLogger(__name__)


class ComputeBudgetView(APIView):
    """Get compute budget and usage statistics"""
    
    def get(self, request):
        """Get current compute budget status"""
        try:
            optimizer = ComputeOptimizer()
            
            # Get user ID from request if authenticated
            user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
            
            budget_status = optimizer.get_compute_budget_status(user_id)
            
            return Response({
                'budget_status': budget_status,
                'recommendations': self._get_budget_recommendations(budget_status)
            })
            
        except Exception as e:
            logger.error(f"Error getting compute budget: {str(e)}")
            return Response(
                {'error': 'Failed to get compute budget'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_budget_recommendations(self, budget_status):
        """Generate recommendations based on budget status"""
        recommendations = []
        
        percentage_used = budget_status.get('percentage_used', 0)
        
        if percentage_used >= 90:
            recommendations.append({
                'type': 'warning',
                'message': 'Approaching daily compute limit',
                'action': 'Consider batching operations or waiting for reset'
            })
        elif percentage_used >= 75:
            recommendations.append({
                'type': 'info',
                'message': 'High compute usage today',
                'action': 'Prioritize high-value optimizations'
            })
        
        return recommendations


class PromptLabComputeCostView(APIView):
    """Get compute cost estimates for a prompt lab"""
    
    def get(self, request, session_id):
        """Get compute cost breakdown for prompt lab"""
        prompt_lab = get_object_or_404(PromptLab, id=session_id, is_active=True)
        
        try:
            optimizer = ComputeOptimizer()
            
            # Current costs
            cost_estimate = optimizer.estimate_optimization_cost(prompt_lab)
            
            # Should we continue?
            optimization_decision = optimizer.should_continue_optimization(prompt_lab)
            
            # Historical costs (simplified - in production, track actual costs)
            historical_costs = {
                'total_iterations': session.optimization_iterations,
                'estimated_total_cost': session.optimization_iterations * cost_estimate['total_cost'],
                'average_cost_per_iteration': cost_estimate['total_cost']
            }
            
            response_data = {
                'session_id': str(session.id),
                'next_iteration_cost': cost_estimate,
                'historical_costs': historical_costs,
                'optimization_recommendation': optimization_decision,
                'cost_saving_tips': self._get_cost_saving_tips(session, optimization_decision)
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error calculating session costs: {str(e)}")
            return Response(
                {'error': 'Failed to calculate costs'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_cost_saving_tips(self, session, optimization_decision):
        """Generate cost-saving recommendations"""
        tips = []
        
        if optimization_decision.get('stage') == 'diminishing_returns':
            tips.append({
                'tip': 'PromptLab in diminishing returns phase',
                'savings': 'Stop now to save ~$0.50-1.00',
                'impact': 'Minimal performance improvement expected'
            })
        
        if session.emails.count() > 50:
            tips.append({
                'tip': 'Large email dataset increases evaluation costs',
                'savings': 'Use sampling for evaluation to save ~30%',
                'impact': 'Slightly less precise metrics'
            })
        
        if optimization_decision.get('improvement_rate', 0) < 0.02:
            tips.append({
                'tip': 'Low improvement rate detected',
                'savings': 'Stop optimization to save future costs',
                'impact': 'Current performance likely near optimal'
            })
        
        return tips


class BatchOptimizationView(APIView):
    """Batch multiple sessions for cost-efficient optimization"""
    
    def post(self, request):
        """Queue sessions for batch optimization"""
        session_ids = request.data.get('session_ids', [])
        
        if not session_ids:
            return Response(
                {'error': 'No session IDs provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            optimizer = ComputeOptimizer()
            
            # Analyze sessions for batching potential
            batch_analysis = []
            total_estimated_cost = 0
            
            for session_id in session_ids:
                try:
                    prompt_lab = PromptLab.objects.get(id=session_id, is_active=True)
                    
                    # Check if optimization is worthwhile
                    should_optimize = optimizer.should_continue_optimization(session)
                    cost_estimate = optimizer.estimate_optimization_cost(session)
                    
                    batch_analysis.append({
                        'session_id': str(session_id),
                        'session_name': session.name,
                        'should_optimize': should_optimize.get('continue', False),
                        'reason': should_optimize.get('reason', 'unknown'),
                        'estimated_cost': cost_estimate['total_cost'],
                        'stage': should_optimize.get('stage', 'unknown')
                    })
                    
                    if should_optimize.get('continue', False):
                        total_estimated_cost += cost_estimate['total_cost']
                        
                except PromptLab.DoesNotExist:
                    batch_analysis.append({
                        'session_id': str(session_id),
                        'error': 'PromptLab not found'
                    })
            
            # Calculate batch savings
            individual_cost = total_estimated_cost
            batch_cost = total_estimated_cost * 0.7  # 30% savings from batching
            savings = individual_cost - batch_cost
            
            return Response({
                'batch_analysis': batch_analysis,
                'cost_summary': {
                    'individual_cost': round(individual_cost, 2),
                    'batch_cost': round(batch_cost, 2),
                    'estimated_savings': round(savings, 2),
                    'savings_percentage': 30
                },
                'recommendation': 'Proceed with batch optimization' if savings > 0.10 else 'Savings too small to justify batching'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in batch optimization analysis: {str(e)}")
            return Response(
                {'error': 'Failed to analyze batch optimization'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )