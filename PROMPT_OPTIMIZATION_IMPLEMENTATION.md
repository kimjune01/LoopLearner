# Manual Dataset-Based Prompt Optimization - Implementation Guide

## Overview
Enable users to manually trigger prompt optimization by selecting specific evaluation datasets from the UI.

## Quick Reference
- **Main Integration Points**: `optimization_orchestrator.py`, `evaluation_engine.py`
- **New Service**: `dataset_optimization_service.py`
- **Key Models**: `EvaluationDataset`, `EvaluationCase`
- **API Endpoints**: `/api/optimization/trigger-with-dataset/`
- **UI Component**: Dataset selection in PromptLabDetail evaluations tab

## UI Flow
1. User navigates to PromptLab > Evaluations tab
2. User selects one or more evaluation datasets
3. User clicks "Optimize with Selected Datasets" button
4. System runs optimization using only the selected datasets
5. User sees optimization progress and results

## Phase 1: Backend Implementation

### 1.1 Create Dataset Optimization Service
**File**: `backend/app/services/dataset_optimization_service.py`

```python
class DatasetOptimizationService:
    def __init__(self):
        # Initialize with LLM provider and database session
        
    def select_datasets_for_optimization(self, prompt_lab_id: str, parameters: List[str]) -> List[EvaluationDataset]:
        """Select relevant datasets based on prompt parameters and quality scores"""
        # 1. Get all datasets for prompt lab
        # 2. Filter by parameter match
        # 3. Sort by quality score (human_reviewed > generated)
        # 4. Return top N datasets
        
    def load_evaluation_cases(self, dataset_ids: List[int], limit: int = 50) -> List[EvaluationCase]:
        """Load cases from selected datasets"""
        # 1. Query cases from datasets
        # 2. Prioritize human-reviewed cases
        # 3. Balance case distribution
        # 4. Return formatted test cases
        
    def track_dataset_usage(self, optimization_run_id: str, dataset_ids: List[int], results: Dict):
        """Record which datasets were used and their effectiveness"""
        # Store in OptimizationRun model (may need to extend)
```

### 1.2 Modify Evaluation Engine
**File**: `backend/app/services/evaluation_engine.py`

**Changes to `compare_prompt_candidates()` method (around line 509)**:
```python
async def compare_prompt_candidates(
    self,
    baseline_prompt: SystemPrompt,
    candidate_prompts: List[SystemPrompt],
    test_suite: Optional[EvaluationTestSuite] = None,
    dataset_ids: Optional[List[int]] = None,  # NEW PARAMETER
    evaluation_config: Optional[EvaluationConfig] = None
) -> EvaluationResult:
```

**Changes to `generate_test_cases()` method (around line 366)**:
```python
def generate_test_cases(
    self, 
    prompt_lab: PromptLab,
    dataset_ids: Optional[List[int]] = None  # NEW PARAMETER
) -> List[TestCase]:
    if dataset_ids:
        # Load cases from datasets
        dataset_service = DatasetOptimizationService()
        cases = dataset_service.load_evaluation_cases(dataset_ids)
        return [self._convert_to_test_case(case) for case in cases]
    else:
        # Existing logic for email/synthetic generation
```

### 1.3 Update Optimization Orchestrator
**File**: `backend/app/services/optimization_orchestrator.py`

**Add new method for dataset-based optimization**:
```python
async def trigger_optimization_with_datasets(
    self,
    prompt_lab_id: str,
    dataset_ids: List[int],
    force: bool = False
) -> OptimizationResult:
    """Manually trigger optimization using specific datasets"""
    # 1. Load prompt lab
    prompt_lab = await self._get_prompt_lab(prompt_lab_id)
    
    # 2. Check if optimization is allowed
    if not force:
        convergence = await self.convergence_detector.check_convergence(prompt_lab)
        if convergence.has_converged:
            raise ValueError("Prompt has converged. Use force=True to override.")
    
    # 3. Load dataset cases
    dataset_service = DatasetOptimizationService()
    test_cases = dataset_service.load_evaluation_cases(dataset_ids)
    
    if not test_cases:
        raise ValueError("No evaluation cases found in selected datasets")
    
    # 4. Build optimization context
    context = await self._build_optimization_context(prompt_lab)
    context['dataset_ids'] = dataset_ids
    context['manual_trigger'] = True
    
    # 5. Generate candidate prompts
    candidates = await self.prompt_rewriter.generate_candidates(
        current_prompt=prompt_lab.active_prompt,
        context=context
    )
    
    # 6. Evaluate with datasets
    evaluation_result = await self.evaluation_engine.compare_prompt_candidates(
        baseline_prompt=prompt_lab.active_prompt,
        candidate_prompts=candidates,
        dataset_ids=dataset_ids,
        evaluation_config=self.config.evaluation
    )
    
    # 7. Deploy if improved
    if evaluation_result.best_candidate.improvement > self.config.deployment_threshold:
        await self._deploy_prompt(prompt_lab, evaluation_result.best_candidate)
    
    # 8. Track dataset usage
    dataset_service.track_dataset_usage(
        optimization_run_id=evaluation_result.id,
        dataset_ids=dataset_ids,
        results=evaluation_result.to_dict()
    )
    
    return evaluation_result
```

## Phase 2: Multi-Metric Evaluation

### 2.1 Add Correction-to-Completion Ratio (CCR)
**File**: `backend/app/services/evaluation_engine.py`

```python
def calculate_ccr(self, evaluation_case: EvaluationCase, output: str) -> float:
    """Calculate Correction-to-Completion Ratio"""
    # Compare output with expected output
    # Count corrections needed
    # Return ratio
```

### 2.2 Implement Natural Language Gradients
**File**: `backend/app/services/optimization_orchestrator.py`

**Add new method**:
```python
async def _generate_error_summary(self, failed_cases: List[Dict]) -> str:
    """Summarize errors for natural language gradient"""
    error_patterns = self._analyze_error_patterns(failed_cases)
    summary_prompt = f"""
    Analyze these error patterns from prompt evaluation:
    {error_patterns}
    
    Provide a concise summary of:
    1. Common failure modes
    2. Specific improvements needed
    3. Parameter handling issues
    """
    return await self.llm_provider.generate(summary_prompt)
```

### 2.3 Enhance A/B Testing
**File**: `backend/app/services/evaluation_engine.py`

**Add statistical significance testing**:
```python
def calculate_statistical_significance(self, baseline_scores: List[float], candidate_scores: List[float]) -> float:
    """Calculate p-value for performance difference"""
    # Use scipy.stats for t-test
    # Return p-value
```

## Phase 3: Human-in-the-Loop Enhancement

### 3.1 Dataset Quality Scoring
**File**: `backend/core/models.py`

**Add to EvaluationDataset model**:
```python
quality_score = models.FloatField(default=0.5)
human_reviewed_count = models.IntegerField(default=0)
last_used_in_optimization = models.DateTimeField(null=True)
effectiveness_score = models.FloatField(default=0.5)  # Based on optimization outcomes
```

### 3.2 Feedback to Dataset Pipeline
**File**: `backend/app/services/evaluation_case_generator.py`

**Add method**:
```python
def create_case_from_feedback(self, feedback: UserFeedback, draft: Draft) -> EvaluationCase:
    """Convert user feedback into evaluation case"""
    # Extract context and parameters
    # Create expected output based on action
    # Add to appropriate dataset
```

## Phase 2: API Implementation

### 2.1 Create Manual Optimization Endpoint
**File**: `backend/app/api/optimization_controller.py`

```python
from pydantic import BaseModel
from typing import List

class DatasetOptimizationRequest(BaseModel):
    prompt_lab_id: str
    dataset_ids: List[int]
    force: bool = False

@router.post("/trigger-with-dataset/")
async def trigger_optimization_with_dataset(
    request: DatasetOptimizationRequest,
    db: Session = Depends(get_db)
):
    """Manually trigger optimization using selected datasets"""
    try:
        orchestrator = OptimizationOrchestrator(db)
        result = await orchestrator.trigger_optimization_with_datasets(
            prompt_lab_id=request.prompt_lab_id,
            dataset_ids=request.dataset_ids,
            force=request.force
        )
        
        return {
            "status": "success",
            "optimization_id": result.id,
            "improvement": result.best_candidate.improvement,
            "datasets_used": len(request.dataset_ids),
            "message": f"Optimization completed with {result.best_candidate.improvement:.1%} improvement"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Optimization failed")
```

### 2.2 Get Available Datasets for Optimization
**File**: `backend/app/api/evaluation_controller.py`

**Add endpoint to get datasets suitable for optimization**:
```python
@router.get("/prompt-labs/{prompt_lab_id}/optimization-datasets/")
async def get_optimization_datasets(
    prompt_lab_id: str,
    db: Session = Depends(get_db)
):
    """Get evaluation datasets that can be used for optimization"""
    # Get prompt lab to check parameters
    prompt_lab = db.query(PromptLab).filter_by(id=prompt_lab_id).first()
    if not prompt_lab:
        raise HTTPException(status_code=404, detail="Prompt lab not found")
    
    # Get datasets with matching parameters
    datasets = db.query(EvaluationDataset).filter(
        EvaluationDataset.prompt_lab_id == prompt_lab_id,
        EvaluationDataset.case_count > 0  # Only datasets with cases
    ).all()
    
    return [{
        "id": d.id,
        "name": d.name,
        "description": d.description,
        "case_count": d.case_count,
        "parameters": d.parameters,
        "human_reviewed": d.human_reviewed_count > 0,
        "quality_score": getattr(d, 'quality_score', 0.5)
    } for d in datasets]
```

## Phase 3: Frontend Implementation

### 3.1 Add Optimization Service
**File**: `frontend/src/services/optimizationService.ts`

```typescript
export interface DatasetOptimizationRequest {
  promptLabId: string;
  datasetIds: number[];
  force?: boolean;
}

export interface OptimizationResult {
  status: string;
  optimization_id: string;
  improvement: number;
  datasets_used: number;
  message: string;
}

export const optimizationService = {
  async triggerWithDatasets(request: DatasetOptimizationRequest): Promise<OptimizationResult> {
    const response = await fetch(`${API_BASE_URL}/api/optimization/trigger-with-dataset/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt_lab_id: request.promptLabId,
        dataset_ids: request.datasetIds,
        force: request.force || false
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Optimization failed');
    }
    
    return response.json();
  },
  
  async getOptimizationDatasets(promptLabId: string): Promise<EvaluationDataset[]> {
    const response = await fetch(`${API_BASE_URL}/api/evaluation/prompt-labs/${promptLabId}/optimization-datasets/`);
    if (!response.ok) throw new Error('Failed to load datasets');
    return response.json();
  }
};
```

### 3.2 Update PromptLabDetail Component
**File**: `frontend/src/components/PromptLabDetail.tsx`

**Add state for dataset selection** (after line 30):
```typescript
const [selectedDatasets, setSelectedDatasets] = useState<number[]>([]);
const [isOptimizing, setIsOptimizing] = useState(false);
const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
```

**Add optimization handler** (after loadDatasets function):
```typescript
const handleOptimizeWithDatasets = async () => {
  if (selectedDatasets.length === 0) {
    setError('Please select at least one dataset');
    return;
  }
  
  try {
    setIsOptimizing(true);
    setError(null);
    
    const result = await optimizationService.triggerWithDatasets({
      promptLabId: id!,
      datasetIds: selectedDatasets,
      force: false
    });
    
    setOptimizationResult(result);
    setSelectedDatasets([]);
    
    // Reload prompt lab to show new version
    await loadPromptLab();
    
    // Show success message
    alert(`Optimization completed! Improvement: ${(result.improvement * 100).toFixed(1)}%`);
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Optimization failed');
  } finally {
    setIsOptimizing(false);
  }
};
```

**Update evaluations tab UI** (modify the actions bar in evaluations tab, around line 801):
```typescript
{/* Actions Bar */}
<div className="mb-6 flex items-center justify-between">
  <div className="flex items-center space-x-4">
    <div className="relative">
      <input
        type="text"
        placeholder="Search datasets..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="w-64 rounded-lg border border-gray-300 px-4 py-2 pl-10 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
      />
      <svg
        className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
      </svg>
    </div>
    
    {selectedDatasets.length > 0 && (
      <div className="flex items-center space-x-2">
        <span className="text-sm text-gray-600">
          {selectedDatasets.length} dataset{selectedDatasets.length > 1 ? 's' : ''} selected
        </span>
        <button
          onClick={() => setSelectedDatasets([])}
          className="text-sm text-purple-600 hover:text-purple-800"
        >
          Clear selection
        </button>
      </div>
    )}
  </div>

  <div className="flex items-center space-x-3">
    {selectedDatasets.length > 0 && (
      <button
        onClick={handleOptimizeWithDatasets}
        disabled={isOptimizing}
        className="btn-primary flex items-center space-x-2 bg-gradient-to-r from-purple-600 to-indigo-600"
      >
        {isOptimizing ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            <span>Optimizing...</span>
          </>
        ) : (
          <>
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>Optimize with Selected Datasets</span>
          </>
        )}
      </button>
    )}
    
    <button
      onClick={() => setShowCreateModal(true)}
      className="btn-secondary flex items-center space-x-2"
    >
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
      </svg>
      <span>New Dataset</span>
    </button>
  </div>
</div>
```

**Update DatasetCard to support selection** (modify DatasetCard component):
```typescript
interface DatasetCardProps {
  dataset: EvaluationDataset;
  onClick: () => void;
  onDelete: () => void;
  isSelected: boolean;
  onSelect: (id: number) => void;
}

const DatasetCard: React.FC<DatasetCardProps> = ({ dataset, onClick, onDelete, isSelected, onSelect }) => {
  return (
    <div 
      className={`card-elevated group cursor-pointer relative ${
        isSelected ? 'ring-2 ring-purple-500 ring-offset-2' : ''
      }`}
    >
      {/* Selection checkbox */}
      <div
        className="absolute top-4 left-4 z-10"
        onClick={(e) => {
          e.stopPropagation();
          onSelect(dataset.id);
        }}
      >
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => {}}
          className="h-5 w-5 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
        />
      </div>
      
      <div className="p-6 pl-12" onClick={onClick}>
        {/* Rest of the card content... */}
      </div>
    </div>
  );
};
```

**Update dataset grid to pass selection props**:
```typescript
{filteredDatasets.map((dataset) => (
  <DatasetCard
    key={dataset.id}
    dataset={dataset}
    isSelected={selectedDatasets.includes(dataset.id)}
    onSelect={(id) => {
      setSelectedDatasets(prev =>
        prev.includes(id)
          ? prev.filter(d => d !== id)
          : [...prev, id]
      );
    }}
    onDelete={() => handleDeleteDataset(dataset.id)}
    onClick={() => navigate(`/evaluation/datasets/${dataset.id}`)}
  />
))}
```

## Testing Checklist

### Unit Tests
- [ ] Test dataset selection logic
- [ ] Test case loading and balancing
- [ ] Test CCR calculation
- [ ] Test error summarization
- [ ] Test statistical significance

### Integration Tests
- [ ] Test full optimization cycle with datasets
- [ ] Test dataset quality scoring updates
- [ ] Test feedback to case conversion
- [ ] Test API endpoints

### Files to Create
1. `backend/app/services/dataset_optimization_service.py`
2. `backend/tests/test_dataset_optimization.py`
3. `backend/tests/test_dataset_integration.py`

### Files to Modify
1. `backend/app/services/optimization_orchestrator.py` - Add dataset support
2. `backend/app/services/evaluation_engine.py` - Accept dataset parameters
3. `backend/core/models.py` - Add quality scoring fields
4. `backend/app/api/optimization_controller.py` - New endpoints
5. `frontend/src/services/optimizationService.ts` - Frontend API calls
6. `frontend/src/components/PromptLabDetail.tsx` - Show optimization with datasets

## Migration Commands
```bash
cd backend
uv run python manage.py makemigrations -n add_dataset_quality_fields
uv run python manage.py migrate
```

## Implementation Order
1. Create `DatasetOptimizationService` class
2. Add `trigger_optimization_with_datasets()` method to `OptimizationOrchestrator`
3. Modify `EvaluationEngine.compare_prompt_candidates()` to accept dataset_ids
4. Create API endpoint `/api/optimization/trigger-with-dataset/`
5. Create frontend optimization service
6. Update PromptLabDetail component with dataset selection UI
7. Test the complete flow

## Quick Implementation Steps

### Step 1: Backend - Core Service
```bash
# Create the dataset optimization service
touch backend/app/services/dataset_optimization_service.py
# Copy the service code from section 1.1
```

### Step 2: Backend - Update Orchestrator
```bash
# Edit optimization_orchestrator.py
# Add the trigger_optimization_with_datasets method from section 1.3
```

### Step 3: Backend - Update Evaluation Engine
```bash
# Edit evaluation_engine.py
# Add dataset_ids parameter to compare_prompt_candidates
# Modify generate_test_cases to load from datasets when provided
```

### Step 4: Backend - Create API Endpoint
```bash
# Edit optimization_controller.py
# Add the DatasetOptimizationRequest model and endpoint from section 2.1
```

### Step 5: Frontend - Create Service
```bash
# Create optimization service
touch frontend/src/services/optimizationService.ts
# Copy the service code from section 3.1
```

### Step 6: Frontend - Update UI
```bash
# Edit PromptLabDetail.tsx
# Add state variables
# Add optimization handler
# Update evaluations tab UI with selection checkboxes
# Update DatasetCard component
```

### Step 7: Test
```bash
# Backend tests
cd backend
uv run pytest tests/test_dataset_optimization.py -v

# Frontend tests
cd frontend
pnpm test:run
```

## Manual Testing Flow
1. Navigate to a PromptLab with an active prompt
2. Go to Evaluations tab
3. Create a dataset with some evaluation cases
4. Select the dataset (checkbox appears)
5. Click "Optimize with Selected Datasets"
6. Watch optimization progress
7. See improvement percentage
8. Verify prompt version incremented