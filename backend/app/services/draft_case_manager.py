"""
Draft Case Management Service
Handles draft case generation, curation, and promotion to real cases.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.db import transaction
from asgiref.sync import sync_to_async
from core.models import EvaluationDataset, DraftCase, EvaluationCase, SystemPrompt
from .evaluation_case_generator import EvaluationCaseGenerator
from .unified_llm_provider import get_llm_provider

logger = logging.getLogger(__name__)


class DraftCaseManager:
    """Service for managing draft evaluation cases"""
    
    TARGET_DRAFTS_PER_DATASET = 2
    
    def __init__(self):
        self.case_generator = EvaluationCaseGenerator()
        self.llm_provider = get_llm_provider()
    
    def get_dataset_drafts(self, dataset: EvaluationDataset, status: Optional[str] = None) -> List[DraftCase]:
        """Get current draft cases for a dataset"""
        queryset = dataset.draft_cases.all()
        if status:
            queryset = queryset.filter(status=status)
        return list(queryset)
    
    def get_ready_drafts(self, dataset: EvaluationDataset) -> List[DraftCase]:
        """Get draft cases ready for curation"""
        return self.get_dataset_drafts(dataset, status='ready')
    
    async def ensure_draft_availability(self, dataset: EvaluationDataset) -> Dict[str, Any]:
        """Ensure dataset has target number of ready drafts"""
        ready_drafts = await sync_to_async(self.get_ready_drafts)(dataset)
        ready_count = len(ready_drafts)
        
        if ready_count >= self.TARGET_DRAFTS_PER_DATASET:
            return {
                'action': 'none_needed',
                'ready_count': ready_count,
                'target_count': self.TARGET_DRAFTS_PER_DATASET
            }
        
        needed_count = self.TARGET_DRAFTS_PER_DATASET - ready_count
        generated_drafts = await self._generate_draft_cases(dataset, needed_count)
        
        return {
            'action': 'generated',
            'ready_count': ready_count,
            'target_count': self.TARGET_DRAFTS_PER_DATASET,
            'generated_count': len(generated_drafts),
            'generated_drafts': [await sync_to_async(self._serialize_draft)(draft) for draft in generated_drafts]
        }
    
    async def _generate_draft_cases(self, dataset: EvaluationDataset, count: int) -> List[DraftCase]:
        """Generate new draft cases for a dataset"""
        # Use sync_to_async to safely access related fields
        dataset_prompt_lab = await sync_to_async(lambda: dataset.prompt_lab)()
        
        if not dataset_prompt_lab:
            logger.warning(f"Cannot generate drafts for dataset {dataset.id}: no associated prompt lab")
            return []
        
        # Get active prompt from the prompt lab
        active_prompt = await sync_to_async(
            lambda: dataset_prompt_lab.prompts.filter(is_active=True).first()
        )()
        
        if not active_prompt:
            logger.warning(f"Cannot generate drafts for dataset {dataset.id}: no active prompt in prompt lab")
            return []
        
        generated_drafts = []
        
        for i in range(count):
            try:
                # Generate multiple output variations for each input
                variations_count = 3  # Generate 3 variations per draft
                case_data = await self._generate_case_with_variations(active_prompt, variations_count)
                
                # Create draft case in database using sync_to_async
                draft = await sync_to_async(DraftCase.objects.create)(
                    dataset=dataset,
                    input_text=case_data['input_text'],
                    output_variations=case_data['output_variations'],
                    parameters=case_data['parameters'],
                    status='ready',  # Mark as ready immediately
                    generation_metadata={
                        'prompt_id': str(active_prompt.id),
                        'prompt_version': active_prompt.version,
                        'generated_at': timezone.now().isoformat(),
                        'variations_count': variations_count
                    }
                )
                
                generated_drafts.append(draft)
                logger.info(f"Generated draft case {draft.id} for dataset {dataset.id}")
                
            except Exception as e:
                logger.error(f"Failed to generate draft case for dataset {dataset.id}: {str(e)}")
                continue
        
        return generated_drafts
    
    async def _generate_case_with_variations(self, prompt: SystemPrompt, variations_count: int) -> Dict[str, Any]:
        """Generate a case with multiple output variations"""
        # Ensure prompt parameters are extracted
        if not prompt.parameters:
            await sync_to_async(prompt.extract_parameters)()
        
        # Generate parameter values
        parameter_values = await sync_to_async(self.case_generator._generate_parameter_values)(prompt.parameters)
        
        # Substitute parameters in prompt content to create input text
        input_text = await sync_to_async(self.case_generator._substitute_parameters)(prompt.content, parameter_values)
        
        # Generate multiple output variations
        output_variations = []
        for i in range(variations_count):
            try:
                # Use slightly different prompts or add variation instructions
                variation_prompt = f"{prompt.content}\n\nGenerate a unique response (variation {i+1}):"
                expected_output = await sync_to_async(self.case_generator._generate_expected_output)(input_text, variation_prompt)
                
                output_variations.append({
                    'text': expected_output,
                    'variation_id': i,
                    'generated_at': timezone.now().isoformat(),
                    'method': 'llm_variation'
                })
            except Exception as e:
                logger.error(f"Failed to generate output variation {i}: {str(e)}")
                continue
        
        return {
            'input_text': input_text,
            'output_variations': output_variations,
            'parameters': parameter_values
        }
    
    def promote_draft_to_case(self, draft: DraftCase, selected_output_index: int, custom_output: Optional[str] = None) -> EvaluationCase:
        """Promote a draft case to a real evaluation case"""
        if draft.status != 'ready':
            raise ValueError(f"Draft {draft.id} is not ready for promotion (status: {draft.status})")
        
        # Determine the expected output
        if custom_output is not None:
            expected_output = custom_output
        else:
            if selected_output_index < 0 or selected_output_index >= len(draft.output_variations):
                raise ValueError(f"Invalid output index {selected_output_index}")
            expected_output = draft.output_variations[selected_output_index]['text']
        
        # Create the real evaluation case
        with transaction.atomic():
            evaluation_case = EvaluationCase.objects.create(
                dataset=draft.dataset,
                input_text=draft.input_text,
                expected_output=expected_output,
                context={
                    **draft.parameters,
                    'promoted_from_draft': draft.id,
                    'selected_variation_index': selected_output_index if custom_output is None else None,
                    'used_custom_output': custom_output is not None
                }
            )
            
            # Update draft status
            draft.status = 'promoted'
            draft.save()
        
        logger.info(f"Promoted draft {draft.id} to evaluation case {evaluation_case.id}")
        return evaluation_case
    
    def discard_draft(self, draft: DraftCase, reason: Optional[str] = None) -> None:
        """Discard a draft case"""
        draft.status = 'discarded'
        if reason:
            draft.generation_metadata['discard_reason'] = reason
            draft.generation_metadata['discarded_at'] = timezone.now().isoformat()
        draft.save()
        
        logger.info(f"Discarded draft {draft.id}: {reason or 'no reason provided'}")
    
    def _serialize_draft(self, draft: DraftCase) -> Dict[str, Any]:
        """Serialize a draft case for API responses"""
        return {
            'id': draft.id,
            'input_text': draft.input_text,
            'output_variations': draft.output_variations,
            'parameters': draft.parameters,
            'status': draft.status,
            'created_at': draft.created_at.isoformat(),
            'updated_at': draft.updated_at.isoformat(),
            'generation_metadata': draft.generation_metadata
        }
    
    async def trigger_background_generation(self, dataset: EvaluationDataset) -> None:
        """Trigger background generation for a dataset (non-blocking)"""
        try:
            await self.ensure_draft_availability(dataset)
        except Exception as e:
            logger.error(f"Background draft generation failed for dataset {dataset.id}: {str(e)}")


class DraftCaseScheduler:
    """Background scheduler for maintaining draft case availability"""
    
    def __init__(self):
        self.manager = DraftCaseManager()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self, check_interval_minutes: int = 30):
        """Start the background scheduler"""
        if self.is_running:
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._scheduler_loop(check_interval_minutes))
        logger.info(f"Started draft case scheduler (check interval: {check_interval_minutes} minutes)")
    
    async def stop(self):
        """Stop the background scheduler"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped draft case scheduler")
    
    async def _scheduler_loop(self, check_interval_minutes: int):
        """Main scheduler loop"""
        while self.is_running:
            try:
                await self._check_all_datasets()
                await asyncio.sleep(check_interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in draft case scheduler: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    async def _check_all_datasets(self):
        """Check all datasets and ensure draft availability"""
        datasets = EvaluationDataset.objects.filter(prompt_lab__isnull=False)
        
        for dataset in datasets:
            try:
                await self.manager.ensure_draft_availability(dataset)
            except Exception as e:
                logger.error(f"Failed to ensure drafts for dataset {dataset.id}: {str(e)}")


# Global scheduler instance
_draft_scheduler: Optional[DraftCaseScheduler] = None


async def get_draft_scheduler() -> DraftCaseScheduler:
    """Get the global draft case scheduler"""
    global _draft_scheduler
    if _draft_scheduler is None:
        _draft_scheduler = DraftCaseScheduler()
    return _draft_scheduler


async def start_draft_scheduler():
    """Start the global draft case scheduler"""
    scheduler = await get_draft_scheduler()
    await scheduler.start()


async def stop_draft_scheduler():
    """Stop the global draft case scheduler"""
    global _draft_scheduler
    if _draft_scheduler:
        await _draft_scheduler.stop()