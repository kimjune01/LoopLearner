from django.urls import path
from .views import (
    GenerateSyntheticEmailView,
    CreateDraftView,
    SubmitFeedbackView,
    RateReasoningFactorsView,
    GetSystemStateView,
    ExportSystemStateView,
    ImportSystemStateView,
    TriggerOptimizationView,
    GetOptimizationProgressView,
    HealthCheckView,
    GetSystemMetricsView,
    GetSystemPromptView,
    ExportSystemPromptView,
)
from .optimization_status_controller import (
    OptimizationStatusView,
    OptimizationHistoryView,
    optimization_health_check,
)
from .dashboard_controller import (
    DashboardOverviewView,
    LearningMetricsView,
    dashboard_summary,
)
from .demo_controller import (
    DemoWorkflowView,
    DemoStatusView,
    reset_demo_data,
    demo_health_check,
)

urlpatterns = [
    # Email endpoints
    path('generate-synthetic-email/', GenerateSyntheticEmailView.as_view(), name='generate-synthetic-email'),
    path('emails/<int:email_id>/generate-drafts/', CreateDraftView.as_view(), name='generate-drafts'),
    
    # Feedback endpoints - use draft_id not email_id for consistency with tests
    path('drafts/<int:draft_id>/submit-feedback/', SubmitFeedbackView.as_view(), name='submit-feedback'),
    path('reasons/<int:reason_id>/rate-reasoning/', RateReasoningFactorsView.as_view(), name='rate-reasoning'),
    
    # State management endpoints
    path('system/state/', GetSystemStateView.as_view(), name='get-system-state'),
    path('system/export/', ExportSystemStateView.as_view(), name='export-system-state'),
    path('system/import/', ImportSystemStateView.as_view(), name='import-system-state'),
    
    # System prompt endpoints
    path('system/prompt/', GetSystemPromptView.as_view(), name='get-system-prompt'),
    path('system/prompt/export/', ExportSystemPromptView.as_view(), name='export-system-prompt'),
    
    # Optimization endpoints
    path('optimization/trigger/', TriggerOptimizationView.as_view(), name='trigger-optimization'),
    path('optimization/<str:optimization_id>/status/', GetOptimizationProgressView.as_view(), name='get-optimization-status'),
    path('learning/progress/', GetOptimizationProgressView.as_view(), name='get-learning-progress'),
    
    # Automated optimization control endpoints
    path('optimization/scheduler/', OptimizationStatusView.as_view(), name='optimization-scheduler'),
    path('optimization/history/', OptimizationHistoryView.as_view(), name='optimization-history'),
    path('optimization/health/', optimization_health_check, name='optimization-health'),
    
    # Dashboard and analytics endpoints
    path('dashboard/overview/', DashboardOverviewView.as_view(), name='dashboard-overview'),
    path('dashboard/metrics/', LearningMetricsView.as_view(), name='learning-metrics'),
    path('dashboard/summary/', dashboard_summary, name='dashboard-summary'),
    
    # Demo workflow endpoints
    path('demo/workflow/', DemoWorkflowView.as_view(), name='demo-workflow'),
    path('demo/status/', DemoStatusView.as_view(), name='demo-status'),
    path('demo/reset/', reset_demo_data, name='demo-reset'),
    path('demo/health/', demo_health_check, name='demo-health'),
    
    # Health and metrics endpoints
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('metrics/', GetSystemMetricsView.as_view(), name='system-metrics'),
]