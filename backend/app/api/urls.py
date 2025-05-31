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
    FastOptimizationView,
    OptimizationRecommendationsView,
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
from .session_controller import (
    SessionListView,
    SessionDetailView,
    SessionExportView,
    SessionImportView,
    SessionDuplicateView,
    SessionStatsView,
    DraftReasoningFactorsView,
    BulkAcceptReasonsView,
    BulkRejectReasonsView,
    BulkRateReasonsView,
    QuickRateReasonView,
    SessionConfidenceView,
    RecalculateConfidenceView,
    ConfidenceHistoryView,
    ConfidenceThresholdsView,
    ExtractPreferencesView,
    SessionPreferencesView,
    UpdateSessionPreferenceView,
    ConvergenceAssessmentView,
    ForceConvergenceView,
    ConvergenceHistoryView,
    SessionColdStartView,
    SessionApplyPreferencesView,
)
from .evaluation_controller import (
    EvaluationDatasetListView,
    EvaluationDatasetDetailView,
    EvaluationCaseListView,
    EvaluationDatasetImportView,
    EvaluationCaseGeneratorView,
    EvaluationCaseSelectionView,
    EvaluationCaseRegenerateView,
    EvaluationCaseParameterEditView,
    EvaluationCaseOutputRegenerateView,
    EvaluationDatasetCompatibilityView,
    EvaluationDatasetMigrationView,
    EvaluationRunTriggerView,
    EvaluationRunResultsView,
    EvaluationComparePromptsView,
)

urlpatterns = [
    # Session management endpoints
    path('sessions/', SessionListView.as_view(), name='session-list'),
    path('sessions/<uuid:session_id>/', SessionDetailView.as_view(), name='session-detail'),
    path('sessions/<uuid:session_id>/export/', SessionExportView.as_view(), name='session-export'),
    path('sessions/import/', SessionImportView.as_view(), name='session-import'),
    path('sessions/<uuid:session_id>/duplicate/', SessionDuplicateView.as_view(), name='session-duplicate'),
    path('sessions/<uuid:session_id>/stats/', SessionStatsView.as_view(), name='session-stats'),
    
    # Session-scoped email endpoints
    path('sessions/<uuid:session_id>/generate-synthetic-email/', GenerateSyntheticEmailView.as_view(), name='session-generate-synthetic-email'),
    path('sessions/<uuid:session_id>/emails/<int:email_id>/generate-drafts/', CreateDraftView.as_view(), name='session-generate-drafts'),
    
    # Session-scoped feedback endpoints
    path('sessions/<uuid:session_id>/drafts/<int:draft_id>/submit-feedback/', SubmitFeedbackView.as_view(), name='session-submit-feedback'),
    path('sessions/<uuid:session_id>/drafts/<int:draft_id>/reasoning-factors/', DraftReasoningFactorsView.as_view(), name='draft-reasoning-factors'),
    path('sessions/<uuid:session_id>/reasons/<int:reason_id>/rate-reasoning/', RateReasoningFactorsView.as_view(), name='session-rate-reasoning'),
    
    # Quick actions for reasoning factors
    path('sessions/<uuid:session_id>/drafts/<int:draft_id>/bulk-accept-reasons/', BulkAcceptReasonsView.as_view(), name='bulk-accept-reasons'),
    path('sessions/<uuid:session_id>/drafts/<int:draft_id>/bulk-reject-reasons/', BulkRejectReasonsView.as_view(), name='bulk-reject-reasons'),
    path('sessions/<uuid:session_id>/drafts/<int:draft_id>/bulk-rate-reasons/', BulkRateReasonsView.as_view(), name='bulk-rate-reasons'),
    path('sessions/<uuid:session_id>/reasons/<int:reason_id>/quick-rate/', QuickRateReasonView.as_view(), name='quick-rate-reason'),
    
    # Confidence tracking endpoints
    path('sessions/<uuid:session_id>/confidence/', SessionConfidenceView.as_view(), name='session-confidence'),
    path('sessions/<uuid:session_id>/confidence/recalculate/', RecalculateConfidenceView.as_view(), name='recalculate-confidence'),
    path('sessions/<uuid:session_id>/confidence/history/', ConfidenceHistoryView.as_view(), name='confidence-history'),
    path('sessions/<uuid:session_id>/confidence/thresholds/', ConfidenceThresholdsView.as_view(), name='confidence-thresholds'),
    
    # Preference extraction endpoints
    path('sessions/<uuid:session_id>/preferences/extract/', ExtractPreferencesView.as_view(), name='extract-preferences'),
    path('sessions/<uuid:session_id>/preferences/', SessionPreferencesView.as_view(), name='session-preferences'),
    path('sessions/<uuid:session_id>/preferences/update/', UpdateSessionPreferenceView.as_view(), name='update-session-preference'),
    
    # Convergence detection endpoints
    path('sessions/<uuid:session_id>/convergence/', ConvergenceAssessmentView.as_view(), name='convergence-assessment'),
    path('sessions/<uuid:session_id>/convergence/force/', ForceConvergenceView.as_view(), name='force-convergence'),
    path('sessions/<uuid:session_id>/convergence/history/', ConvergenceHistoryView.as_view(), name='convergence-history'),
    
    # Cold start endpoints
    path('sessions/<uuid:session_id>/cold-start/', SessionColdStartView.as_view(), name='session-cold-start'),
    path('sessions/<uuid:session_id>/cold-start/status/', SessionColdStartView.as_view(), name='session-cold-start-status'),
    path('sessions/<uuid:session_id>/apply-preferences/', SessionApplyPreferencesView.as_view(), name='session-apply-preferences'),
    
    # Legacy endpoints (for backward compatibility)
    path('generate-synthetic-email/', GenerateSyntheticEmailView.as_view(), name='generate-synthetic-email'),
    path('emails/<int:email_id>/generate-drafts/', CreateDraftView.as_view(), name='generate-drafts'),
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
    
    # Fast optimization endpoints
    path('optimization/fast/', FastOptimizationView.as_view(), name='fast-optimization'),
    path('optimization/recommendations/', OptimizationRecommendationsView.as_view(), name='optimization-recommendations'),
    
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
    
    # Evaluation endpoints
    path('evaluations/datasets/', EvaluationDatasetListView.as_view(), name='evaluation-dataset-list'),
    path('evaluations/datasets/<int:dataset_id>/', EvaluationDatasetDetailView.as_view(), name='evaluation-dataset-detail'),
    path('evaluations/datasets/<int:dataset_id>/cases/', EvaluationCaseListView.as_view(), name='evaluation-case-list'),
    path('evaluations/datasets/<int:dataset_id>/import/', EvaluationDatasetImportView.as_view(), name='evaluation-dataset-import'),
    
    # Story 2: Case generation endpoints
    path('evaluations/datasets/<int:dataset_id>/generate-cases/', EvaluationCaseGeneratorView.as_view(), name='evaluation-generate-cases'),
    path('evaluations/datasets/<int:dataset_id>/add-selected-cases/', EvaluationCaseSelectionView.as_view(), name='evaluation-add-selected-cases'),
    path('evaluations/datasets/<int:dataset_id>/regenerate-case/', EvaluationCaseRegenerateView.as_view(), name='evaluation-regenerate-case'),
    path('evaluations/cases/preview/<str:preview_id>/parameters/', EvaluationCaseParameterEditView.as_view(), name='evaluation-edit-parameters'),
    path('evaluations/cases/preview/<str:preview_id>/regenerate-output/', EvaluationCaseOutputRegenerateView.as_view(), name='evaluation-regenerate-output'),
    
    # Parameter change management endpoints
    path('evaluations/datasets/<int:dataset_id>/compatibility/', EvaluationDatasetCompatibilityView.as_view(), name='evaluation-dataset-compatibility'),
    path('evaluations/datasets/<int:dataset_id>/migrate/', EvaluationDatasetMigrationView.as_view(), name='evaluation-dataset-migration'),
    
    # Evaluation execution endpoints
    path('evaluations/run/', EvaluationRunTriggerView.as_view(), name='evaluation-run-trigger'),
    path('evaluations/runs/<int:run_id>/results/', EvaluationRunResultsView.as_view(), name='evaluation-run-results'),
    path('evaluations/compare/', EvaluationComparePromptsView.as_view(), name='evaluation-compare-prompts'),
]