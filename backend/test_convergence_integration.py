#!/usr/bin/env python3
"""
Test the convergence detection integration with optimization orchestrator
"""
import os
import sys
import django
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'looplearner.settings')
django.setup()

from django.utils import timezone
from asgiref.sync import sync_to_async
from core.models import Session, SystemPrompt, Email, Draft, UserFeedback, SessionConfidence
from app.services.optimization_orchestrator import OptimizationOrchestrator
from app.services.convergence_detector import ConvergenceDetector

async def test_convergence_integration():
    """Test that convergence detection properly blocks optimization"""
    print("Testing convergence detection integration...")
    
    # Create a test session
    session = await sync_to_async(Session.objects.create)(
        name="Test Convergence Session",
        description="Testing convergence detection",
        optimization_iterations=5,  # Sufficient but not excessive iteration count
        total_feedback_collected=20  # Sufficient feedback
    )
    
    # Create a system prompt with good performance scores
    prompt = await sync_to_async(SystemPrompt.objects.create)(
        session=session,
        content="Test prompt content",
        version=5,
        is_active=True,
        performance_score=0.95  # High performance score
    )
    
    # Create some high-performance historical prompts (plateau)
    for i in range(4):
        await sync_to_async(SystemPrompt.objects.create)(
            session=session,
            content=f"Historical prompt {i}",
            version=i+1,
            is_active=False,
            performance_score=0.94 + (i * 0.001)  # Very small improvements (plateau)
        )
    
    # Create emails and feedback indicating stability
    email = await sync_to_async(Email.objects.create)(
        session=session,
        subject="Test email",
        body="Test email body",
        sender="test@example.com"
    )
    
    draft = await sync_to_async(Draft.objects.create)(
        email=email,
        content="Test draft response",
        system_prompt=prompt
    )
    
    # Create stable feedback pattern (high acceptance rate)
    for i in range(20):
        await sync_to_async(UserFeedback.objects.create)(
            draft=draft,
            action='accept',  # High acceptance indicates satisfaction
            reason="Good response",
            created_at=timezone.now() - timedelta(hours=i)
        )
    
    # Create a session confidence tracker to meet confidence convergence criteria
    await sync_to_async(SessionConfidence.objects.create)(
        session=session,
        user_confidence=0.85,  # High user confidence
        system_confidence=0.90,  # High system confidence
        confidence_trend=0.02,  # Low positive trend (stable)
        feedback_consistency_score=0.88,  # High consistency
        reasoning_alignment_score=0.90,  # High alignment
        total_feedback_count=20,
        consistent_feedback_streak=15
    )
    
    # Test convergence detection
    detector = ConvergenceDetector()
    assessment = await sync_to_async(detector.assess_convergence)(session)
    
    print(f"Convergence assessment:")
    print(f"  Converged: {assessment.get('converged', False)}")
    print(f"  Confidence: {assessment.get('confidence_score', 0.0):.2f}")
    print(f"  Factors: {assessment.get('factors', {})}")
    
    # Test optimization orchestrator integration
    # Mock the required dependencies
    mock_llm = MagicMock()
    mock_rewriter = MagicMock()
    mock_evaluator = MagicMock()
    
    orchestrator = OptimizationOrchestrator(mock_llm, mock_rewriter, mock_evaluator)
    
    # Mock the feedback batch to include our test feedback
    test_feedback = await sync_to_async(list)(UserFeedback.objects.filter(draft=draft))
    
    with patch.object(orchestrator, '_analyze_feedback_for_triggers') as mock_analyze:
        mock_analyze.return_value = {
            'should_trigger': True,
            'reason': 'Test trigger',
            'feedback_count': len(test_feedback),
            'feedback_batch': test_feedback
        }
        
        # Check if convergence blocks optimization
        try:
            convergence_blocked = await orchestrator._check_convergence_status(test_feedback)
            print(f"Optimization blocked by convergence: {convergence_blocked}")
            
            if convergence_blocked:
                print("✅ SUCCESS: Convergence properly blocks optimization")
            else:
                print("❌ FAILURE: Convergence did not block optimization")
        except Exception as e:
            print(f"Error in convergence check: {e}")
            convergence_blocked = False
    
    # Test force optimization with convergence override
    with patch.object(orchestrator, '_execute_optimization_cycle') as mock_execute:
        mock_execute.return_value = MagicMock()
        
        # This should be blocked by convergence
        result = await orchestrator.force_optimization(
            reason="Test force optimization",
            override_convergence=False
        )
        
        if result.deployed == False and "blocked" in result.trigger_reason.lower():
            print("✅ SUCCESS: Force optimization properly blocked by convergence")
        else:
            print("❌ FAILURE: Force optimization not blocked by convergence")
        
        # This should bypass convergence
        result = await orchestrator.force_optimization(
            reason="Test force optimization with override",
            override_convergence=True
        )
        
        if mock_execute.called:
            print("✅ SUCCESS: Force optimization with override bypasses convergence")
        else:
            print("❌ FAILURE: Force optimization with override still blocked")
    
    # Cleanup
    await sync_to_async(session.delete)()
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_convergence_integration())