"""
Evaluation API controller for managing evaluation datasets and cases.
Implements Story 1: Create Evaluation Dataset
Implements Story 2: Generate Evaluation Cases from Prompt Parameters
"""
import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from core.models import Session, EvaluationDataset, EvaluationCase, SystemPrompt
from app.services.evaluation_case_generator import EvaluationCaseGenerator
from app.services.evaluation_dataset_migrator import EvaluationDatasetMigrator


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationDatasetListView(View):
    """
    Handle dataset listing and creation
    GET /api/evaluations/datasets/?session_id=<uuid>
    POST /api/evaluations/datasets/
    """
    
    def get(self, request):
        """List datasets (global and session-scoped)"""
        session_id = request.GET.get('session_id')
        
        if session_id:
            # Get session-specific datasets
            session = get_object_or_404(Session, id=session_id)
            datasets = EvaluationDataset.objects.filter(session=session)
        else:
            # Get all global datasets (session=null)
            datasets = EvaluationDataset.objects.filter(session__isnull=True)
        
        dataset_data = []
        for dataset in datasets:
            dataset_data.append({
                'id': dataset.id,
                'name': dataset.name,
                'description': dataset.description,
                'parameters': dataset.parameters,
                'parameter_descriptions': dataset.parameter_descriptions,
                'created_at': dataset.created_at.isoformat(),
                'updated_at': dataset.updated_at.isoformat(),
                'case_count': dataset.cases.count(),
                'average_score': None  # TODO: Calculate from evaluation runs
            })
        
        return JsonResponse({'datasets': dataset_data})
    
    def post(self, request):
        """Create a new evaluation dataset"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        session_id = data.get('session_id')  # Optional for global datasets
        name = data.get('name')
        description = data.get('description', '')
        parameters = data.get('parameters', [])
        parameter_descriptions = data.get('parameter_descriptions', {})
        
        if not name:
            return JsonResponse({'error': 'name is required'}, status=400)
        
        session = None
        if session_id:
            session = get_object_or_404(Session, id=session_id)
        
        dataset = EvaluationDataset.objects.create(
            session=session,
            name=name,
            description=description,
            parameters=parameters,
            parameter_descriptions=parameter_descriptions
        )
        
        return JsonResponse({
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'parameters': dataset.parameters,
            'parameter_descriptions': dataset.parameter_descriptions,
            'created_at': dataset.created_at.isoformat(),
            'updated_at': dataset.updated_at.isoformat(),
            'session_id': str(session.id) if session else None,
            'case_count': 0,
            'average_score': None
        }, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationDatasetDetailView(View):
    """
    Handle dataset details
    GET /api/evaluations/datasets/<id>/
    """
    
    def get(self, request, dataset_id):
        """Get dataset details with cases"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        
        cases_data = []
        for case in dataset.cases.all():
            cases_data.append({
                'id': case.id,
                'input_text': case.input_text,
                'expected_output': case.expected_output,
                'context': case.context,
                'created_at': case.created_at.isoformat()
            })
        
        return JsonResponse({
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'parameters': dataset.parameters,
            'parameter_descriptions': dataset.parameter_descriptions,
            'created_at': dataset.created_at.isoformat(),
            'updated_at': dataset.updated_at.isoformat(),
            'session_id': str(dataset.session.id) if dataset.session else None,
            'case_count': len(cases_data),
            'average_score': None,  # TODO: Calculate from evaluation runs
            'cases': cases_data
        })


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationCaseListView(View):
    """
    Handle case listing and creation for a dataset
    GET /api/evaluations/datasets/<dataset_id>/cases/
    POST /api/evaluations/datasets/<dataset_id>/cases/
    """
    
    def get(self, request, dataset_id):
        """List all cases for a dataset"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        cases = dataset.cases.all().order_by('created_at')
        
        cases_data = []
        for case in cases:
            cases_data.append({
                'id': case.id,
                'input_text': case.input_text,
                'expected_output': case.expected_output,
                'context': case.context,
                'created_at': case.created_at.isoformat()
            })
        
        return JsonResponse({
            'dataset_id': dataset.id,
            'cases': cases_data,
            'count': len(cases_data)
        })
    
    def post(self, request, dataset_id):
        """Add a new case to the dataset"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        input_text = data.get('input_text')
        expected_output = data.get('expected_output')
        context = data.get('context', {})
        
        if not input_text or not expected_output:
            return JsonResponse({'error': 'input_text and expected_output are required'}, status=400)
        
        case = EvaluationCase.objects.create(
            dataset=dataset,
            input_text=input_text,
            expected_output=expected_output,
            context=context
        )
        
        return JsonResponse({
            'id': case.id,
            'input_text': case.input_text,
            'expected_output': case.expected_output,
            'context': case.context,
            'created_at': case.created_at.isoformat(),
            'dataset_id': dataset.id
        }, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationDatasetImportView(View):
    """
    Handle JSONL import for a dataset
    POST /api/evaluations/datasets/<dataset_id>/import/
    """
    
    def post(self, request, dataset_id):
        """Import cases from JSONL file"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        uploaded_file = request.FILES['file']
        
        try:
            # Read file content
            content = uploaded_file.read().decode('utf-8')
            lines = content.strip().split('\n')
            
            imported_count = 0
            for line in lines:
                if line.strip():  # Skip empty lines
                    case_data = json.loads(line)
                    
                    # Map JSONL fields to our model fields
                    input_text = case_data.get('input') or case_data.get('input_text')
                    expected_output = case_data.get('expected') or case_data.get('expected_output')
                    context = case_data.get('context', {})
                    
                    if input_text and expected_output:
                        EvaluationCase.objects.create(
                            dataset=dataset,
                            input_text=input_text,
                            expected_output=expected_output,
                            context=context
                        )
                        imported_count += 1
            
            return JsonResponse({
                'imported_count': imported_count,
                'dataset_id': dataset.id
            })
            
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return JsonResponse({'error': f'Invalid file format: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Import failed: {str(e)}'}, status=500)


# Story 2: Generate Evaluation Cases from Prompt Parameters

@method_decorator(csrf_exempt, name='dispatch')
class EvaluationCaseGeneratorView(View):
    """
    Generate evaluation cases from prompt parameters
    POST /api/evaluations/datasets/<dataset_id>/generate-cases/
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.case_generator = EvaluationCaseGenerator()
    
    def post(self, request, dataset_id):
        """Generate evaluation cases preview (not saved to database)"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        prompt_id = data.get('prompt_id')
        count = data.get('count', 5)
        
        if not prompt_id:
            return JsonResponse({'error': 'prompt_id is required'}, status=400)
        
        if count > 20:  # Limit to prevent abuse
            return JsonResponse({'error': 'Maximum 20 cases per generation'}, status=400)
        
        prompt = get_object_or_404(SystemPrompt, id=prompt_id)
        
        try:
            generated_cases = self.case_generator.generate_cases_preview(prompt, count)
            
            return JsonResponse({
                'generated_cases': generated_cases,
                'prompt_content': prompt.content,
                'dataset_id': dataset.id,
                'count': len(generated_cases)
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Generation failed: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationCaseSelectionView(View):
    """
    Add selected generated cases to dataset
    POST /api/evaluations/datasets/<dataset_id>/add-selected-cases/
    """
    
    def post(self, request, dataset_id):
        """Add selected cases to the evaluation dataset"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        selected_cases = data.get('selected_cases', [])
        
        if not selected_cases:
            return JsonResponse({'error': 'No cases selected'}, status=400)
        
        created_cases = []
        case_ids = []
        
        try:
            for case_data in selected_cases:
                case = EvaluationCase.objects.create(
                    dataset=dataset,
                    input_text=case_data['input_text'],
                    expected_output=case_data['expected_output'],
                    context=case_data.get('parameters', {})  # Store parameters in context
                )
                created_cases.append(case)
                case_ids.append(case.id)
            
            return JsonResponse({
                'added_count': len(created_cases),
                'case_ids': case_ids,
                'dataset_id': dataset.id
            }, status=201)
            
        except Exception as e:
            return JsonResponse({'error': f'Failed to save cases: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationCaseRegenerateView(View):
    """
    Regenerate a specific case with new parameter values
    POST /api/evaluations/datasets/<dataset_id>/regenerate-case/
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.case_generator = EvaluationCaseGenerator()
    
    def post(self, request, dataset_id):
        """Regenerate a single case"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        prompt_id = data.get('prompt_id')
        case_to_replace = data.get('case_to_replace')
        
        if not prompt_id or not case_to_replace:
            return JsonResponse({'error': 'prompt_id and case_to_replace are required'}, status=400)
        
        prompt = get_object_or_404(SystemPrompt, id=prompt_id)
        
        try:
            regenerated_case = self.case_generator.regenerate_single_case(prompt, case_to_replace)
            
            return JsonResponse({
                'regenerated_case': regenerated_case,
                'dataset_id': dataset.id
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Regeneration failed: {str(e)}'}, status=500)


# In-memory storage for preview cases (for parameter editing)
# In production, this could be Redis or database with TTL
_preview_cases_cache = {}

@method_decorator(csrf_exempt, name='dispatch')
class EvaluationCaseParameterEditView(View):
    """
    Edit parameters for a preview case
    PUT /api/evaluations/cases/preview/<preview_id>/parameters/
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.case_generator = EvaluationCaseGenerator()
    
    def put(self, request, preview_id):
        """Update parameters for a preview case"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        prompt_id = data.get('prompt_id')
        new_parameters = data.get('parameters')
        
        if not prompt_id or not new_parameters:
            return JsonResponse({'error': 'prompt_id and parameters are required'}, status=400)
        
        prompt = get_object_or_404(SystemPrompt, id=prompt_id)
        
        # Get existing case data from cache or create a new one
        existing_case = _preview_cases_cache.get(preview_id, {})
        if not existing_case:
            existing_case = {'preview_id': preview_id}
        
        try:
            updated_case = self.case_generator.update_case_parameters(
                prompt, existing_case, new_parameters
            )
            
            # Store updated case in cache
            _preview_cases_cache[preview_id] = updated_case
            
            return JsonResponse({
                'updated_case': updated_case
            })
            
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Parameter update failed: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationCaseOutputRegenerateView(View):
    """
    Regenerate expected output for a preview case
    POST /api/evaluations/cases/preview/<preview_id>/regenerate-output/
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.case_generator = EvaluationCaseGenerator()
    
    def post(self, request, preview_id):
        """Regenerate expected output for an existing case"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        prompt_id = data.get('prompt_id')
        
        if not prompt_id:
            return JsonResponse({'error': 'prompt_id is required'}, status=400)
        
        prompt = get_object_or_404(SystemPrompt, id=prompt_id)
        
        # Get case data from cache
        case_data = _preview_cases_cache.get(preview_id)
        if not case_data:
            return JsonResponse({'error': 'Preview case not found'}, status=404)
        
        try:
            updated_case = self.case_generator.regenerate_expected_output(prompt, case_data)
            
            # Store updated case back in cache
            _preview_cases_cache[preview_id] = updated_case
            
            return JsonResponse({
                'updated_case': updated_case
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Output regeneration failed: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationDatasetCompatibilityView(View):
    """
    Check dataset compatibility with new prompt parameters
    POST /api/evaluations/datasets/<dataset_id>/compatibility/
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.migrator = EvaluationDatasetMigrator()
    
    def post(self, request, dataset_id):
        """Analyze compatibility between dataset and new prompt"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        prompt_id = data.get('prompt_id')
        if not prompt_id:
            return JsonResponse({'error': 'prompt_id is required'}, status=400)
        
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        prompt = get_object_or_404(SystemPrompt, id=prompt_id)
        
        try:
            analysis = self.migrator.analyze_parameter_compatibility(dataset, prompt)
            return JsonResponse(analysis)
            
        except Exception as e:
            return JsonResponse({'error': f'Compatibility analysis failed: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationDatasetMigrationView(View):
    """
    Migrate dataset to work with new prompt parameters
    POST /api/evaluations/datasets/<dataset_id>/migrate/
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.migrator = EvaluationDatasetMigrator()
    
    def post(self, request, dataset_id):
        """Migrate dataset to new prompt parameters"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        prompt_id = data.get('prompt_id')
        strategy = data.get('strategy', 'regenerate_all')  # 'regenerate_all', 'partial_update', 'create_new'
        
        if not prompt_id:
            return JsonResponse({'error': 'prompt_id is required'}, status=400)
        
        if strategy not in ['regenerate_all', 'partial_update', 'create_new']:
            return JsonResponse({'error': 'Invalid migration strategy'}, status=400)
        
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        prompt = get_object_or_404(SystemPrompt, id=prompt_id)
        
        try:
            result = self.migrator.migrate_dataset(dataset, prompt, strategy)
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({'error': f'Dataset migration failed: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationRunTriggerView(View):
    """
    Trigger evaluation runs
    POST /api/evaluations/run/
    """
    
    def post(self, request):
        """Trigger an evaluation run"""
        try:
            data = json.loads(request.body)
            dataset_id = data.get('dataset_id')
            prompt_id = data.get('prompt_id')
            
            if not dataset_id or not prompt_id:
                return JsonResponse({'error': 'dataset_id and prompt_id are required'}, status=400)
            
            # Get dataset and prompt
            dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
            prompt = get_object_or_404(SystemPrompt, id=prompt_id)
            
            # Execute evaluation
            from app.services.evaluation_engine import EvaluationEngine
            from app.services.unified_llm_provider import LLMProviderFactory, LLMConfig
            from app.services.reward_aggregator import RewardFunctionAggregator
            
            # Create LLM provider and reward aggregator
            llm_provider = LLMProviderFactory.create_provider(LLMConfig(
                provider="mock", model="test-model"
            ))
            reward_aggregator = RewardFunctionAggregator(llm_provider)
            
            engine = EvaluationEngine(llm_provider, reward_aggregator)
            
            # Create and execute run
            run = engine.create_evaluation_run(dataset, prompt)
            results = engine.execute_evaluation_run(run)
            
            return JsonResponse({
                'run_id': run.id,
                'status': run.status,
                'overall_score': run.overall_score,
                'total_cases': len(results),
                'passed_cases': sum(1 for r in results if r.passed),
                'started_at': run.started_at.isoformat(),
                'completed_at': run.completed_at.isoformat() if run.completed_at else None
            }, status=201)
            
        except Exception as e:
            return JsonResponse({'error': f'Evaluation run failed: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationRunResultsView(View):
    """
    Get evaluation run results
    GET /api/evaluations/runs/<run_id>/results/
    """
    
    def get(self, request, run_id):
        """Get results for an evaluation run"""
        try:
            from core.models import EvaluationRun, EvaluationResult
            
            run = get_object_or_404(EvaluationRun, id=run_id)
            results = EvaluationResult.objects.filter(run=run).select_related('case')
            
            result_data = []
            for result in results:
                result_data.append({
                    'case_id': result.case.id,
                    'input_text': result.case.input_text,
                    'expected_output': result.case.expected_output,
                    'generated_output': result.generated_output,
                    'similarity_score': result.similarity_score,
                    'passed': result.passed,
                    'details': result.details
                })
            
            return JsonResponse({
                'run_id': run.id,
                'dataset_name': run.dataset.name,
                'prompt_version': run.prompt.version,
                'status': run.status,
                'overall_score': run.overall_score,
                'started_at': run.started_at.isoformat(),
                'completed_at': run.completed_at.isoformat() if run.completed_at else None,
                'results': result_data
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Failed to get results: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationComparePromptsView(View):
    """
    Compare multiple prompts on a dataset
    POST /api/evaluations/compare/
    """
    
    def post(self, request):
        """Compare multiple prompts"""
        try:
            data = json.loads(request.body)
            dataset_id = data.get('dataset_id')
            prompt_ids = data.get('prompt_ids', [])
            
            if not dataset_id or len(prompt_ids) < 2:
                return JsonResponse({'error': 'dataset_id and at least 2 prompt_ids are required'}, status=400)
            
            # Get dataset and prompts
            dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
            prompts = []
            for prompt_id in prompt_ids:
                prompt = get_object_or_404(SystemPrompt, id=prompt_id)
                prompts.append(prompt)
            
            # Execute comparison
            from app.services.evaluation_engine import EvaluationEngine
            from app.services.unified_llm_provider import LLMProviderFactory, LLMConfig
            from app.services.reward_aggregator import RewardFunctionAggregator
            
            # Create LLM provider and reward aggregator
            llm_provider = LLMProviderFactory.create_provider(LLMConfig(
                provider="mock", model="test-model"
            ))
            reward_aggregator = RewardFunctionAggregator(llm_provider)
            
            engine = EvaluationEngine(llm_provider, reward_aggregator)
            
            comparison = engine.compare_prompts(dataset, prompts)
            
            return JsonResponse(comparison)
            
        except Exception as e:
            return JsonResponse({'error': f'Prompt comparison failed: {str(e)}'}, status=500)