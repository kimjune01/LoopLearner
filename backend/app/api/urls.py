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
from .promptlab_controller import (
    PromptLabListView,
    PromptLabDetailView,
    PromptLabExportView,
    PromptLabImportView,
    PromptLabDuplicateView,
    PromptLabStatsView,
    DraftReasoningFactorsView,
    BulkAcceptReasonsView,
    BulkRejectReasonsView,
    BulkRateReasonsView,
    QuickRateReasonView,
    PromptLabConfidenceView,
    RecalculateConfidenceView,
    ConfidenceHistoryView,
    ConfidenceThresholdsView,
    ExtractPreferencesView,
    PromptLabPreferencesView,
    UpdatePromptLabPreferenceView,
    ConvergenceAssessmentView,
    ForceConvergenceView,
    ConvergenceHistoryView,
    PromptLabColdStartView,
    PromptLabApplyPreferencesView,
)
from .evaluation_controller import (
    EvaluationDatasetListView,
    EvaluationDatasetDetailView,
    EvaluationCaseListView,
    EvaluationCaseDetailView,
    EvaluationDatasetImportView,
    EvaluationCaseGeneratorView,
    EvaluationCaseSelectionView,
    EvaluationCaseRegenerateView,
    EvaluationCaseParameterEditView,
    EvaluationCaseOutputRegenerateView,
    EvaluationDatasetCompatibilityView,
    EvaluationDatasetMigrationView,
    EvaluationRunTriggerView,
    EvaluationRunListView,
    EvaluationRunDetailView,
    EvaluationRunResultsView,
    EvaluationComparePromptsView,
    # Draft case management
    EvaluationDatasetDraftsView,
    EvaluationDraftPromoteView,
    EvaluationDraftDiscardView,
    EvaluationDraftStatusView,
)
from .llm_status_controller import LLMStatusView

urlpatterns = [
    # PromptLab management endpoints
    path('prompt-labs/', PromptLabListView.as_view(), name='prompt-lab-list'),
    path('prompt-labs/<uuid:prompt_lab_id>/', PromptLabDetailView.as_view(), name='prompt-lab-detail'),
    path('prompt-labs/<uuid:prompt_lab_id>/export/', PromptLabExportView.as_view(), name='prompt-lab-export'),
    path('prompt-labs/import/', PromptLabImportView.as_view(), name='prompt-lab-import'),
    path('prompt-labs/<uuid:prompt_lab_id>/duplicate/', PromptLabDuplicateView.as_view(), name='prompt-lab-duplicate'),
    path('prompt-labs/<uuid:prompt_lab_id>/stats/', PromptLabStatsView.as_view(), name='prompt-lab-stats'),
    
    # PromptLab-scoped email endpoints
    path('prompt-labs/<uuid:prompt_lab_id>/generate-synthetic-email/', GenerateSyntheticEmailView.as_view(), name='prompt-lab-generate-synthetic-email'),
    path('prompt-labs/<uuid:prompt_lab_id>/emails/<int:email_id>/generate-drafts/', CreateDraftView.as_view(), name='prompt-lab-generate-drafts'),
    
    # PromptLab-scoped feedback endpoints
    path('prompt-labs/<uuid:prompt_lab_id>/drafts/<int:draft_id>/submit-feedback/', SubmitFeedbackView.as_view(), name='prompt-lab-submit-feedback'),
    path('prompt-labs/<uuid:prompt_lab_id>/drafts/<int:draft_id>/reasoning-factors/', DraftReasoningFactorsView.as_view(), name='draft-reasoning-factors'),
    path('prompt-labs/<uuid:prompt_lab_id>/reasons/<int:reason_id>/rate-reasoning/', RateReasoningFactorsView.as_view(), name='prompt-lab-rate-reasoning'),
    
    # Quick actions for reasoning factors
    path('prompt-labs/<uuid:prompt_lab_id>/drafts/<int:draft_id>/bulk-accept-reasons/', BulkAcceptReasonsView.as_view(), name='bulk-accept-reasons'),
    path('prompt-labs/<uuid:prompt_lab_id>/drafts/<int:draft_id>/bulk-reject-reasons/', BulkRejectReasonsView.as_view(), name='bulk-reject-reasons'),
    path('prompt-labs/<uuid:prompt_lab_id>/drafts/<int:draft_id>/bulk-rate-reasons/', BulkRateReasonsView.as_view(), name='bulk-rate-reasons'),
    path('prompt-labs/<uuid:prompt_lab_id>/reasons/<int:reason_id>/quick-rate/', QuickRateReasonView.as_view(), name='quick-rate-reason'),
    
    # Confidence tracking endpoints
    path('prompt-labs/<uuid:prompt_lab_id>/confidence/', PromptLabConfidenceView.as_view(), name='prompt-lab-confidence'),
    path('prompt-labs/<uuid:prompt_lab_id>/confidence/recalculate/', RecalculateConfidenceView.as_view(), name='recalculate-confidence'),
    path('prompt-labs/<uuid:prompt_lab_id>/confidence/history/', ConfidenceHistoryView.as_view(), name='confidence-history'),
    path('prompt-labs/<uuid:prompt_lab_id>/confidence/thresholds/', ConfidenceThresholdsView.as_view(), name='confidence-thresholds'),
    
    # Preference extraction endpoints
    path('prompt-labs/<uuid:prompt_lab_id>/preferences/extract/', ExtractPreferencesView.as_view(), name='extract-preferences'),
    path('prompt-labs/<uuid:prompt_lab_id>/preferences/', PromptLabPreferencesView.as_view(), name='prompt-lab-preferences'),
    path('prompt-labs/<uuid:prompt_lab_id>/preferences/update/', UpdatePromptLabPreferenceView.as_view(), name='update-prompt-lab-preference'),
    
    # Convergence detection endpoints
    path('prompt-labs/<uuid:prompt_lab_id>/convergence/', ConvergenceAssessmentView.as_view(), name='convergence-assessment'),
    path('prompt-labs/<uuid:prompt_lab_id>/convergence/force/', ForceConvergenceView.as_view(), name='force-convergence'),
    path('prompt-labs/<uuid:prompt_lab_id>/convergence/history/', ConvergenceHistoryView.as_view(), name='convergence-history'),
    
    # Cold start endpoints
    path('prompt-labs/<uuid:prompt_lab_id>/cold-start/', PromptLabColdStartView.as_view(), name='prompt-lab-cold-start'),
    path('prompt-labs/<uuid:prompt_lab_id>/cold-start/status/', PromptLabColdStartView.as_view(), name='prompt-lab-cold-start-status'),
    path('prompt-labs/<uuid:prompt_lab_id>/apply-preferences/', PromptLabApplyPreferencesView.as_view(), name='prompt-lab-apply-preferences'),
    
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
    
    # LLM status endpoint
    path('llm/status/', LLMStatusView.as_view(), name='llm-status'),
    
    # Evaluation endpoints
    path('evaluations/datasets/', EvaluationDatasetListView.as_view(), name='evaluation-dataset-list'),
    path('evaluations/datasets/<int:dataset_id>/', EvaluationDatasetDetailView.as_view(), name='evaluation-dataset-detail'),
    path('evaluations/datasets/<int:dataset_id>/cases/', EvaluationCaseListView.as_view(), name='evaluation-case-list'),
    path('evaluations/datasets/<int:dataset_id>/cases/<int:case_id>/', EvaluationCaseDetailView.as_view(), name='evaluation-case-detail'),
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
    path('evaluations/datasets/<int:dataset_id>/runs/', EvaluationRunListView.as_view(), name='evaluation-run-list'),
    path('evaluations/datasets/<int:dataset_id>/runs/delete-all/', EvaluationRunListView.as_view(), name='evaluation-run-delete-all'),
    path('evaluations/runs/<int:run_id>/', EvaluationRunDetailView.as_view(), name='evaluation-run-detail'),
    path('evaluations/runs/<int:run_id>/results/', EvaluationRunResultsView.as_view(), name='evaluation-run-results'),
    path('evaluations/compare/', EvaluationComparePromptsView.as_view(), name='evaluation-compare-prompts'),
    
    # Draft case management endpoints
    path('evaluations/datasets/<int:dataset_id>/drafts/', EvaluationDatasetDraftsView.as_view(), name='evaluation-dataset-drafts'),
    path('evaluations/datasets/<int:dataset_id>/drafts/generate/', EvaluationDatasetDraftsView.as_view(), name='evaluation-generate-drafts'),
    path('evaluations/datasets/<int:dataset_id>/drafts/<int:draft_id>/promote/', EvaluationDraftPromoteView.as_view(), name='evaluation-promote-draft'),
    path('evaluations/datasets/<int:dataset_id>/drafts/<int:draft_id>/discard/', EvaluationDraftDiscardView.as_view(), name='evaluation-discard-draft'),
    path('evaluations/drafts/status/', EvaluationDraftStatusView.as_view(), name='evaluation-draft-status'),
]