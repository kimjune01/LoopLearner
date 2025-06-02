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
from django.db import models
from django.utils import timezone
from core.models import PromptLab, EvaluationDataset, EvaluationCase, SystemPrompt, DraftCase
from app.services.evaluation_case_generator import EvaluationCaseGenerator
from app.services.evaluation_dataset_migrator import EvaluationDatasetMigrator
from app.services.draft_case_manager import DraftCaseManager


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationDatasetListView(View):
    """
    Handle dataset listing and creation
    GET /api/evaluations/datasets/?prompt_lab_id=<uuid>
    POST /api/evaluations/datasets/
    """
    
    def get(self, request):
        """List datasets (global and session-scoped) with optional parameter filtering"""
        prompt_lab_id = request.GET.get('prompt_lab_id')
        filter_by_params = request.GET.get('filter_by_params', 'false').lower() == 'true'
        
        if prompt_lab_id:
            # Get prompt lab-specific datasets
            prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id)
            
            if filter_by_params:
                # Get active system prompt parameters for this prompt lab
                active_prompt = prompt_lab.prompts.filter(is_active=True).first()
                if active_prompt and active_prompt.parameters:
                    # Find datasets that have matching parameters
                    datasets = EvaluationDataset.objects.filter(prompt_lab=prompt_lab)
                    # Filter by parameter overlap in Python since JSONField queries can be complex
                    compatible_datasets = []
                    for dataset in datasets:
                        if dataset.parameters:
                            # Check if there's any overlap between prompt parameters and dataset parameters
                            overlap = set(active_prompt.parameters) & set(dataset.parameters)
                            if overlap:
                                compatible_datasets.append(dataset)
                        elif not dataset.parameters:
                            # Include datasets with no parameters as they're universally compatible
                            compatible_datasets.append(dataset)
                    datasets = compatible_datasets
                else:
                    # No active prompt or no parameters, show datasets with no parameters
                    datasets = EvaluationDataset.objects.filter(
                        prompt_lab=prompt_lab,
                        parameters__isnull=True
                    ) | EvaluationDataset.objects.filter(
                        prompt_lab=prompt_lab,
                        parameters=[]
                    )
                    datasets = list(datasets)
            else:
                # Show all prompt lab datasets without filtering
                datasets = EvaluationDataset.objects.filter(prompt_lab=prompt_lab)
        else:
            # All datasets must be prompt lab-scoped - return error if no prompt_lab_id provided
            return JsonResponse({'error': 'prompt_lab_id is required - all datasets are prompt lab-scoped'}, status=400)
        
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
        
        prompt_lab_id = data.get('prompt_lab_id')
        name = data.get('name')
        description = data.get('description', '')
        parameters = data.get('parameters', [])
        parameter_descriptions = data.get('parameter_descriptions', {})
        
        if not name:
            return JsonResponse({'error': 'name is required'}, status=400)
        
        if not prompt_lab_id:
            return JsonResponse({'error': 'prompt_lab_id is required - all datasets must be associated with a prompt lab'}, status=400)
        
        prompt_lab = get_object_or_404(PromptLab, id=prompt_lab_id)
        
        dataset = EvaluationDataset.objects.create(
            prompt_lab=prompt_lab,
            name=name,
            description=description,
            parameters=parameters,
            parameter_descriptions=parameter_descriptions
        )
        
        # Trigger initial draft generation in background
        if prompt_lab:
            import threading
            draft_manager = DraftCaseManager()
            def run_background_generation():
                import asyncio
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(draft_manager.trigger_background_generation(dataset))
                    loop.close()
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Background draft generation failed: {str(e)}")
            
            thread = threading.Thread(target=run_background_generation)
            thread.start()
        
        return JsonResponse({
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'parameters': dataset.parameters,
            'parameter_descriptions': dataset.parameter_descriptions,
            'created_at': dataset.created_at.isoformat(),
            'updated_at': dataset.updated_at.isoformat(),
            'prompt_lab_id': str(prompt_lab.id) if prompt_lab else None,
            'case_count': 0,
            'average_score': None
        }, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationDatasetDetailView(View):
    """
    Handle dataset details
    GET /api/evaluations/datasets/<id>/
    PUT /api/evaluations/datasets/<id>/
    DELETE /api/evaluations/datasets/<id>/
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
            'prompt_lab_id': str(dataset.prompt_lab.id) if dataset.prompt_lab else None,
            'case_count': len(cases_data),
            'average_score': None,  # TODO: Calculate from evaluation runs
            'cases': cases_data
        })
    
    def put(self, request, dataset_id):
        """Update an evaluation dataset"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Update allowed fields
        if 'name' in data:
            dataset.name = data['name']
        if 'description' in data:
            dataset.description = data['description']
        if 'parameter_descriptions' in data:
            dataset.parameter_descriptions = data['parameter_descriptions']
        
        dataset.save()
        
        return JsonResponse({
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'parameters': dataset.parameters,
            'parameter_descriptions': dataset.parameter_descriptions,
            'created_at': dataset.created_at.isoformat(),
            'updated_at': dataset.updated_at.isoformat(),
            'prompt_lab_id': str(dataset.prompt_lab.id) if dataset.prompt_lab else None,
            'case_count': dataset.cases.count(),
            'average_score': None
        })
    
    def delete(self, request, dataset_id):
        """Delete an evaluation dataset"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        dataset.delete()
        return JsonResponse({'message': 'Dataset deleted successfully'}, status=200)


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
class EvaluationCaseDetailView(View):
    """
    Handle individual case operations
    GET /api/evaluations/datasets/<dataset_id>/cases/<case_id>/
    PUT /api/evaluations/datasets/<dataset_id>/cases/<case_id>/
    DELETE /api/evaluations/datasets/<dataset_id>/cases/<case_id>/
    """
    
    def get(self, request, dataset_id, case_id):
        """Get a specific case"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        case = get_object_or_404(EvaluationCase, id=case_id, dataset=dataset)
        
        return JsonResponse({
            'id': case.id,
            'input_text': case.input_text,
            'expected_output': case.expected_output,
            'context': case.context,
            'created_at': case.created_at.isoformat(),
            'dataset_id': dataset.id
        })
    
    def put(self, request, dataset_id, case_id):
        """Update a specific case"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        case = get_object_or_404(EvaluationCase, id=case_id, dataset=dataset)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Update fields if provided
        if 'input_text' in data:
            case.input_text = data['input_text']
        if 'expected_output' in data:
            case.expected_output = data['expected_output']
        if 'context' in data:
            case.context = data['context']
        
        case.save()
        
        return JsonResponse({
            'id': case.id,
            'input_text': case.input_text,
            'expected_output': case.expected_output,
            'context': case.context,
            'created_at': case.created_at.isoformat(),
            'dataset_id': dataset.id
        })
    
    def delete(self, request, dataset_id, case_id):
        """Delete a specific case"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        case = get_object_or_404(EvaluationCase, id=case_id, dataset=dataset)
        
        case.delete()
        
        return JsonResponse({'message': 'Case deleted successfully'}, status=200)


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
        """Generate evaluation cases (immediately persisted to database)"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        template = data.get('template')
        count = data.get('count', 5)
        use_prompt_lab_prompt = data.get('use_prompt_lab_prompt', False)
        prompt_id = data.get('prompt_id')  # Alternative to use_prompt_lab_prompt
        generate_output_variations = data.get('generate_output_variations', False)
        variations_count = data.get('variations_count', 3)
        persist_immediately = data.get('persist_immediately', False)  # Default to preview mode for backward compatibility
        max_tokens = data.get('max_tokens', 500)  # Allow user to control response length
        
        if count > 20:  # Limit to prevent abuse
            return JsonResponse({'error': 'Maximum 20 cases per generation'}, status=400)
        
        try:
            # Determine which prompt to use
            active_prompt = None
            generation_method = None
            
            if prompt_id:
                # Use specific prompt by ID
                from core.models import SystemPrompt
                active_prompt = get_object_or_404(SystemPrompt, id=prompt_id)
                generation_method = 'prompt_id'
            elif use_prompt_lab_prompt and dataset.prompt_lab:
                # Use prompt lab's active prompt
                active_prompt = dataset.prompt_lab.prompts.filter(is_active=True).first()
                if not active_prompt:
                    return JsonResponse({'error': 'No active prompt found in prompt lab'}, status=400)
                generation_method = 'prompt_lab_prompt'
            
            if active_prompt:
                # Use prompt-based generation
                if generate_output_variations:
                    # Use new method for multiple output variations
                    generated_cases = self.case_generator.generate_cases_preview_with_variations(
                        active_prompt, count, enable_variations=True, 
                        dataset=dataset, persist_immediately=persist_immediately, max_tokens=max_tokens
                    )
                else:
                    # Use existing method for backward compatibility
                    generated_cases = self.case_generator.generate_cases_preview(
                        active_prompt, count,
                        dataset=dataset, persist_immediately=persist_immediately, max_tokens=max_tokens
                    )
            else:
                # Use template-based generation (existing behavior)
                if not template:
                    return JsonResponse({'error': 'template or prompt_id is required'}, status=400)
                generated_cases = self.case_generator.generate_cases_from_template(
                    template, dataset.parameters, count,
                    dataset=dataset, persist_immediately=persist_immediately, max_tokens=max_tokens
                )
                generation_method = 'template'
            
            # Store generated cases in cache only if not persisted
            persisted_cases = []
            preview_cases = []
            
            for case in generated_cases:
                if case.get('persisted', False):
                    persisted_cases.append(case)
                else:
                    preview_cases.append(case)
                    _preview_cases_cache[case['preview_id']] = case
            
            # Maintain backward compatibility with different response formats
            if generation_method == 'template':
                # Template-based generation uses 'previews' key for backward compatibility
                response_data = {
                    'previews': generated_cases,
                    'dataset_id': dataset.id,
                    'count': len(generated_cases),
                    'template': template,
                    'generation_method': 'template',
                    'supports_variations': False,
                    'persist_immediately': persist_immediately,
                    'persisted_count': len(persisted_cases)
                }
            else:
                # Prompt-based generation uses 'generated_cases' key for backward compatibility
                response_data = {
                    'generated_cases': generated_cases,
                    'dataset_id': dataset.id,
                    'count': len(generated_cases),
                    'generation_method': generation_method,
                    'supports_variations': True,
                    'persist_immediately': persist_immediately,
                    'persisted_count': len(persisted_cases)
                }
                
                # Include prompt context
                if active_prompt:
                    response_data.update({
                        'prompt_content': active_prompt.content,
                        'prompt_parameters': active_prompt.parameters or [],
                    })
                    
                if dataset.prompt_lab:
                    response_data.update({
                        'prompt_lab_id': str(dataset.prompt_lab.id),
                        'prompt_lab_name': dataset.prompt_lab.name,
                    })
            
            # Return appropriate status code based on whether cases were persisted
            status_code = 201 if persisted_cases else 200
            return JsonResponse(response_data, status=status_code)
            
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
        
        # Support multiple formats: preview_ids, cases with selections, and selected_cases
        preview_ids = data.get('preview_ids', [])
        cases_data = data.get('cases', [])
        selected_cases = data.get('selected_cases', [])
        
        if not preview_ids and not cases_data and not selected_cases:
            return JsonResponse({'error': 'No cases selected'}, status=400)
        
        created_cases = []
        case_ids = []
        added_cases_response = []
        
        try:
            # Handle selected_cases format (test compatibility)
            if selected_cases:
                for case_data in selected_cases:
                    # Extract case data for direct storage
                    input_text = case_data.get('input_text')
                    expected_output = case_data.get('expected_output')
                    parameters = case_data.get('parameters', {})
                    
                    if input_text and expected_output:
                        case = EvaluationCase.objects.create(
                            dataset=dataset,
                            input_text=input_text,
                            expected_output=expected_output,
                            context=parameters
                        )
                        created_cases.append(case)
                        case_ids.append(case.id)
            
            # Handle legacy format for backward compatibility
            elif preview_ids:
                for preview_id in preview_ids:
                    # Get case data from cache
                    case_data = _preview_cases_cache.get(preview_id)
                    if not case_data:
                        continue  # Skip missing cases
                    
                    # Handle both session-based and template-based generation formats
                    if 'input_text' in case_data:
                        # Session-based generation format
                        input_text = case_data['input_text']
                        expected_output = case_data['expected_output']
                    else:
                        # Template-based generation format
                        input_text = case_data['generated_input']
                        expected_output = case_data['generated_output']
                    
                    case = EvaluationCase.objects.create(
                        dataset=dataset,
                        input_text=input_text,
                        expected_output=expected_output,
                        context=case_data.get('parameters', {})  # Store parameters in context
                    )
                    created_cases.append(case)
                    case_ids.append(case.id)
                    
                    # Remove from cache after adding to dataset
                    del _preview_cases_cache[preview_id]
            
            # Handle new format with output selection
            if cases_data:
                # First, validate all cases before creating any
                validated_cases = []
                for case_data in cases_data:
                    preview_id = case_data.get('preview_id')
                    input_text = case_data.get('input_text')
                    parameters = case_data.get('parameters', {})
                    selected_output_index = case_data.get('selected_output_index')
                    custom_output = case_data.get('custom_output')
                    output_variations = case_data.get('output_variations', [])
                    
                    # Validation
                    if not preview_id or not input_text:
                        return JsonResponse({'error': 'preview_id and input_text are required for each case'}, status=400)
                    
                    # Must have either selected_output_index OR custom_output, but not both
                    if selected_output_index is not None and custom_output is not None:
                        return JsonResponse({'error': 'Cannot specify both selected_output_index and custom_output'}, status=400)
                    
                    if selected_output_index is None and custom_output is None:
                        return JsonResponse({'error': 'Must specify either selected_output_index or custom_output'}, status=400)
                    
                    # Determine the expected output
                    if custom_output is not None:
                        expected_output = custom_output
                    else:
                        # Validate selected_output_index
                        if selected_output_index < 0 or selected_output_index >= len(output_variations):
                            return JsonResponse({'error': f'selected_output_index {selected_output_index} is out of range'}, status=400)
                        
                        expected_output = output_variations[selected_output_index]['text']
                    
                    # Store validated case data
                    validated_cases.append({
                        'preview_id': preview_id,
                        'input_text': input_text,
                        'expected_output': expected_output,
                        'parameters': parameters
                    })
                
                # If all cases are valid, create them atomically
                from django.db import transaction
                with transaction.atomic():
                    for case_data in validated_cases:
                        case = EvaluationCase.objects.create(
                            dataset=dataset,
                            input_text=case_data['input_text'],
                            expected_output=case_data['expected_output'],
                            context=case_data['parameters']
                        )
                        created_cases.append(case)
                        case_ids.append(case.id)
                        
                        # Prepare response data
                        added_cases_response.append({
                            'id': case.id,
                            'input_text': case.input_text,
                            'expected_output': case.expected_output,
                            'context': case.context,
                            'preview_id': case_data['preview_id']
                        })
                        
                        # Remove from cache if exists
                        if case_data['preview_id'] in _preview_cases_cache:
                            del _preview_cases_cache[case_data['preview_id']]
            
            response_data = {
                'added_count': len(created_cases),
                'case_ids': case_ids,
                'dataset_id': dataset.id
            }
            
            # Include detailed case data for new format
            if cases_data:
                response_data['added_cases'] = added_cases_response
            
            return JsonResponse(response_data, status=201)
            
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
        max_tokens = data.get('max_tokens', 500)
        
        if not prompt_id or not case_to_replace:
            return JsonResponse({'error': 'prompt_id and case_to_replace are required'}, status=400)
        
        prompt = get_object_or_404(SystemPrompt, id=prompt_id)
        
        try:
            regenerated_case = self.case_generator.regenerate_single_case(prompt, case_to_replace, max_tokens)
            
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
        max_tokens = data.get('max_tokens', 500)
        
        if not prompt_id or not new_parameters:
            return JsonResponse({'error': 'prompt_id and parameters are required'}, status=400)
        
        prompt = get_object_or_404(SystemPrompt, id=prompt_id)
        
        # Get existing case data from cache or create a new one
        existing_case = _preview_cases_cache.get(preview_id, {})
        if not existing_case:
            existing_case = {'preview_id': preview_id}
        
        try:
            updated_case = self.case_generator.update_case_parameters(
                prompt, existing_case, new_parameters, max_tokens
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
        max_tokens = data.get('max_tokens', 500)
        
        if not prompt_id:
            return JsonResponse({'error': 'prompt_id is required'}, status=400)
        
        prompt = get_object_or_404(SystemPrompt, id=prompt_id)
        
        # Get case data from cache
        case_data = _preview_cases_cache.get(preview_id)
        if not case_data:
            return JsonResponse({'error': 'Preview case not found'}, status=404)
        
        try:
            updated_case = self.case_generator.regenerate_expected_output(prompt, case_data, max_tokens)
            
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
            
            # Create evaluation engine
            from app.services.evaluation_engine import EvaluationEngine
            from app.services.unified_llm_provider import LLMProviderFactory, LLMConfig
            from app.services.reward_aggregator import RewardFunctionAggregator
            
            # Create LLM provider and reward aggregator
            llm_provider = LLMProviderFactory.create_provider(LLMConfig(
                provider="mock", model="test-model"
            ))
            reward_aggregator = RewardFunctionAggregator(llm_provider)
            
            engine = EvaluationEngine(llm_provider, reward_aggregator)
            
            # Create run immediately and return ID
            run = engine.create_evaluation_run(dataset, prompt)
            
            # Start execution in background thread
            import threading
            def run_evaluation_background():
                try:
                    engine.execute_evaluation_run(run)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Background evaluation execution failed: {str(e)}")
                    # Mark run as failed
                    run.status = 'failed'
                    run.completed_at = timezone.now()
                    run.save()
            
            thread = threading.Thread(target=run_evaluation_background)
            thread.start()
            
            # Return immediately with run ID
            return JsonResponse({
                'run_id': run.id,
                'status': 'pending',
                'dataset_id': dataset.id,
                'prompt_id': prompt.id,
                'started_at': run.started_at.isoformat()
            }, status=201)
            
        except Exception as e:
            return JsonResponse({'error': f'Evaluation run failed: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationRunListView(View):
    """
    List evaluation runs for a dataset
    GET /api/evaluations/datasets/<dataset_id>/runs/
    """
    
    def get(self, request, dataset_id):
        """Get all evaluation runs for a dataset"""
        try:
            from core.models import EvaluationRun, EvaluationResult
            
            dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
            runs = EvaluationRun.objects.filter(dataset=dataset).order_by('-started_at')
            
            # Add query parameters for filtering
            status_filter = request.GET.get('status')
            if status_filter:
                runs = runs.filter(status=status_filter)
            
            limit = request.GET.get('limit')
            if limit:
                try:
                    runs = runs[:int(limit)]
                except ValueError:
                    pass
            
            runs_data = []
            for run in runs:
                # Get run statistics
                results = EvaluationResult.objects.filter(run=run)
                total_cases = results.count()
                passed_cases = results.filter(passed=True).count()
                
                # Calculate additional metrics
                avg_similarity = 0
                if total_cases > 0:
                    similarity_scores = [r.similarity_score for r in results]
                    avg_similarity = sum(similarity_scores) / len(similarity_scores)
                
                # Calculate duration
                duration_seconds = None
                if run.completed_at and run.started_at:
                    duration = run.completed_at - run.started_at
                    duration_seconds = duration.total_seconds()
                
                runs_data.append({
                    'id': run.id,
                    'status': run.status,
                    'overall_score': run.overall_score,
                    'total_cases': total_cases,
                    'passed_cases': passed_cases,
                    'failed_cases': total_cases - passed_cases,
                    'pass_rate': (passed_cases / total_cases * 100) if total_cases > 0 else 0,
                    'avg_similarity_score': avg_similarity,
                    'prompt_version': run.prompt.version,
                    'prompt_id': run.prompt.id,
                    'started_at': run.started_at.isoformat(),
                    'completed_at': run.completed_at.isoformat() if run.completed_at else None,
                    'duration_seconds': duration_seconds
                })
            
            return JsonResponse({
                'dataset_id': dataset.id,
                'dataset_name': dataset.name,
                'runs': runs_data,
                'total_runs': len(runs_data)
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Failed to get evaluation runs: {str(e)}'}, status=500)
    
    def delete(self, request, dataset_id):
        """Delete all evaluation runs for a dataset"""
        try:
            from core.models import EvaluationRun
            
            dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
            
            # Check if this is the delete-all endpoint
            if request.path.endswith('/delete-all/'):
                # Delete all runs for this dataset
                runs = EvaluationRun.objects.filter(dataset=dataset)
                deleted_count = runs.count()
                runs.delete()
                
                return JsonResponse({
                    'message': f'Successfully deleted {deleted_count} evaluation runs',
                    'deleted_count': deleted_count
                })
            else:
                return JsonResponse({'error': 'Invalid delete endpoint'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': f'Failed to delete evaluation runs: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationRunDetailView(View):
    """
    Get or delete a specific evaluation run
    GET /api/evaluations/runs/<run_id>/
    DELETE /api/evaluations/runs/<run_id>/
    """
    
    def delete(self, request, run_id):
        """Delete a specific evaluation run"""
        try:
            from core.models import EvaluationRun
            
            run = get_object_or_404(EvaluationRun, id=run_id)
            run.delete()
            
            return JsonResponse({'message': 'Evaluation run deleted successfully'})
            
        except Exception as e:
            return JsonResponse({'error': f'Failed to delete evaluation run: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationRunResultsView(View):
    """
    Get evaluation run results
    GET /api/evaluations/runs/<run_id>/results/
    """
    
    def get(self, request, run_id):
        """Get detailed results for an evaluation run"""
        try:
            from core.models import EvaluationRun, EvaluationResult
            import statistics
            
            run = get_object_or_404(EvaluationRun, id=run_id)
            results = EvaluationResult.objects.filter(run=run).select_related('case')
            
            # Calculate detailed statistics
            total_cases = results.count()
            passed_cases = results.filter(passed=True).count()
            failed_cases = total_cases - passed_cases
            
            similarity_scores = [r.similarity_score for r in results]
            avg_similarity = statistics.mean(similarity_scores) if similarity_scores else 0
            median_similarity = statistics.median(similarity_scores) if similarity_scores else 0
            min_similarity = min(similarity_scores) if similarity_scores else 0
            max_similarity = max(similarity_scores) if similarity_scores else 0
            
            # Calculate performance distribution
            score_ranges = {
                'excellent': len([s for s in similarity_scores if s >= 0.9]),
                'good': len([s for s in similarity_scores if 0.7 <= s < 0.9]),
                'fair': len([s for s in similarity_scores if 0.5 <= s < 0.7]),
                'poor': len([s for s in similarity_scores if s < 0.5])
            }
            
            # Calculate duration
            duration_seconds = None
            if run.completed_at and run.started_at:
                duration = run.completed_at - run.started_at
                duration_seconds = duration.total_seconds()
            
            # Prepare detailed result data
            result_data = []
            for idx, result in enumerate(results):
                result_data.append({
                    'case_id': result.case.id,
                    'case_number': idx + 1,
                    'input_text': result.case.input_text,
                    'expected_output': result.case.expected_output,
                    'generated_output': result.generated_output,
                    'similarity_score': result.similarity_score,
                    'passed': result.passed,
                    'details': result.details,
                    'case_context': result.case.context,
                    'performance_tier': (
                        'excellent' if result.similarity_score >= 0.9 else
                        'good' if result.similarity_score >= 0.7 else
                        'fair' if result.similarity_score >= 0.5 else
                        'poor'
                    )
                })
            
            # Get prompt information
            prompt_info = {
                'id': run.prompt.id,
                'version': run.prompt.version,
                'content': run.prompt.content,
                'parameters': run.prompt.parameters,
                'performance_score': run.prompt.performance_score
            }
            
            return JsonResponse({
                'run_id': run.id,
                'dataset_id': run.dataset.id,
                'dataset_name': run.dataset.name,
                'prompt_info': prompt_info,
                'status': run.status,
                'overall_score': run.overall_score,
                'started_at': run.started_at.isoformat(),
                'completed_at': run.completed_at.isoformat() if run.completed_at else None,
                'duration_seconds': duration_seconds,
                'statistics': {
                    'total_cases': total_cases,
                    'passed_cases': passed_cases,
                    'failed_cases': failed_cases,
                    'pass_rate': (passed_cases / total_cases * 100) if total_cases > 0 else 0,
                    'avg_similarity_score': avg_similarity,
                    'median_similarity_score': median_similarity,
                    'min_similarity_score': min_similarity,
                    'max_similarity_score': max_similarity,
                    'score_distribution': score_ranges
                },
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


# Draft Case Management Endpoints

@method_decorator(csrf_exempt, name='dispatch')
class EvaluationDatasetDraftsView(View):
    """
    Handle draft cases for a dataset
    GET /api/evaluations/datasets/<dataset_id>/drafts/
    POST /api/evaluations/datasets/<dataset_id>/drafts/generate/
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.draft_manager = DraftCaseManager()
    
    def get(self, request, dataset_id):
        """Get current draft cases for a dataset"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        
        # Get query parameters
        status = request.GET.get('status')  # Filter by status
        include_metadata = request.GET.get('include_metadata', 'false').lower() == 'true'
        
        # Get drafts
        drafts = self.draft_manager.get_dataset_drafts(dataset, status)
        
        drafts_data = []
        for draft in drafts:
            draft_data = self.draft_manager._serialize_draft(draft)
            if not include_metadata:
                draft_data.pop('generation_metadata', None)
            drafts_data.append(draft_data)
        
        return JsonResponse({
            'dataset_id': dataset.id,
            'drafts': drafts_data,
            'count': len(drafts_data),
            'ready_count': len([d for d in drafts if d.status == 'ready']),
            'target_count': self.draft_manager.TARGET_DRAFTS_PER_DATASET
        })
    
    def post(self, request, dataset_id):
        """Generate new draft cases for a dataset"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        count = data.get('count', 1)
        force_generation = data.get('force', False)
        
        if count > 5:  # Limit to prevent abuse
            return JsonResponse({'error': 'Maximum 5 drafts per generation'}, status=400)
        
        try:
            import asyncio
            
            if force_generation:
                # Force generate specific number of drafts
                generated_drafts = asyncio.run(self.draft_manager._generate_draft_cases(dataset, count))
                result = {
                    'action': 'force_generated',
                    'generated_count': len(generated_drafts),
                    'generated_drafts': [self.draft_manager._serialize_draft(draft) for draft in generated_drafts]
                }
            else:
                # Use smart generation (only if needed)
                result = asyncio.run(self.draft_manager.ensure_draft_availability(dataset))
            
            return JsonResponse(result, status=201)
            
        except Exception as e:
            return JsonResponse({'error': f'Draft generation failed: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationDraftPromoteView(View):
    """
    Promote a draft case to a real evaluation case
    POST /api/evaluations/datasets/<dataset_id>/drafts/<draft_id>/promote/
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.draft_manager = DraftCaseManager()
    
    def post(self, request, dataset_id, draft_id):
        """Promote a draft to a real evaluation case"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        draft = get_object_or_404(DraftCase, id=draft_id, dataset=dataset)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        selected_output_index = data.get('selected_output_index')
        custom_output = data.get('custom_output')
        
        # Validation
        if selected_output_index is None and custom_output is None:
            return JsonResponse({'error': 'Must specify either selected_output_index or custom_output'}, status=400)
        
        if selected_output_index is not None and custom_output is not None:
            return JsonResponse({'error': 'Cannot specify both selected_output_index and custom_output'}, status=400)
        
        try:
            evaluation_case = self.draft_manager.promote_draft_to_case(
                draft, selected_output_index, custom_output
            )
            
            # Trigger background generation to maintain draft availability
            import threading
            def run_background_generation():
                import asyncio
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.draft_manager.trigger_background_generation(dataset))
                    loop.close()
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Background draft generation failed: {str(e)}")
            
            thread = threading.Thread(target=run_background_generation)
            thread.start()
            
            return JsonResponse({
                'promoted_case': {
                    'id': evaluation_case.id,
                    'input_text': evaluation_case.input_text,
                    'expected_output': evaluation_case.expected_output,
                    'context': evaluation_case.context,
                    'created_at': evaluation_case.created_at.isoformat()
                },
                'draft_id': draft.id,
                'dataset_id': dataset.id
            }, status=201)
            
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Promotion failed: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationDraftDiscardView(View):
    """
    Discard a draft case
    POST /api/evaluations/datasets/<dataset_id>/drafts/<draft_id>/discard/
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.draft_manager = DraftCaseManager()
    
    def post(self, request, dataset_id, draft_id):
        """Discard a draft case"""
        dataset = get_object_or_404(EvaluationDataset, id=dataset_id)
        draft = get_object_or_404(DraftCase, id=draft_id, dataset=dataset)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = {}
        
        reason = data.get('reason', 'User discarded')
        
        try:
            self.draft_manager.discard_draft(draft, reason)
            
            # Trigger background generation to maintain draft availability
            import threading
            def run_background_generation():
                import asyncio
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.draft_manager.trigger_background_generation(dataset))
                    loop.close()
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Background draft generation failed: {str(e)}")
            
            thread = threading.Thread(target=run_background_generation)
            thread.start()
            
            return JsonResponse({
                'discarded_draft_id': draft.id,
                'dataset_id': dataset.id,
                'reason': reason
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Discard failed: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluationDraftStatusView(View):
    """
    Get draft case status and statistics
    GET /api/evaluations/drafts/status/
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.draft_manager = DraftCaseManager()
    
    def get(self, request):
        """Get overall draft case status"""
        prompt_lab_id = request.GET.get('prompt_lab_id')
        
        # Base queryset
        datasets_query = EvaluationDataset.objects.all()
        if prompt_lab_id:
            datasets_query = datasets_query.filter(prompt_lab_id=prompt_lab_id)
        
        datasets = datasets_query.prefetch_related('draft_cases')
        
        status_summary = {
            'total_datasets': 0,
            'datasets_with_drafts': 0,
            'total_drafts': 0,
            'ready_drafts': 0,
            'target_met_datasets': 0,
            'datasets_needing_attention': []
        }
        
        for dataset in datasets:
            status_summary['total_datasets'] += 1
            
            drafts = list(dataset.draft_cases.all())
            ready_drafts = [d for d in drafts if d.status == 'ready']
            
            if drafts:
                status_summary['datasets_with_drafts'] += 1
            
            status_summary['total_drafts'] += len(drafts)
            status_summary['ready_drafts'] += len(ready_drafts)
            
            if len(ready_drafts) >= self.draft_manager.TARGET_DRAFTS_PER_DATASET:
                status_summary['target_met_datasets'] += 1
            else:
                status_summary['datasets_needing_attention'].append({
                    'dataset_id': dataset.id,
                    'dataset_name': dataset.name,
                    'ready_count': len(ready_drafts),
                    'target_count': self.draft_manager.TARGET_DRAFTS_PER_DATASET,
                    'needs': self.draft_manager.TARGET_DRAFTS_PER_DATASET - len(ready_drafts)
                })
        
        return JsonResponse(status_summary)