"""
Evaluation Dataset Migration Service
Handles parameter changes and dataset compatibility issues
"""

from typing import List, Dict, Any, Tuple, Optional
from core.models import SystemPrompt, EvaluationDataset, EvaluationCase
from .evaluation_case_generator import EvaluationCaseGenerator
import logging

logger = logging.getLogger(__name__)


class EvaluationDatasetMigrator:
    """Service for migrating evaluation datasets when prompt parameters change"""
    
    def __init__(self):
        self.case_generator = EvaluationCaseGenerator()
    
    def analyze_parameter_compatibility(
        self, 
        dataset: EvaluationDataset, 
        new_prompt: SystemPrompt
    ) -> Dict[str, Any]:
        """
        Analyze compatibility between existing dataset and new prompt parameters
        
        Returns:
            Dictionary with compatibility analysis and migration recommendations
        """
        if not new_prompt.parameters:
            new_prompt.extract_parameters()
        
        # Get existing cases
        existing_cases = list(dataset.cases.all())
        if not existing_cases:
            return {
                'status': 'empty_dataset',
                'message': 'Dataset has no cases, safe to use with new prompt',
                'compatible': True,
                'migration_needed': False,
                'cases_analyzed': 0
            }
        
        # Analyze parameter fingerprint from first case
        first_case = existing_cases[0]
        original_parameters = self._extract_parameters_from_case(first_case)
        
        new_params = set(new_prompt.parameters)
        original_params = set(original_parameters)
        
        # Parameter change analysis
        removed_params = original_params - new_params
        added_params = new_params - original_params
        kept_params = original_params & new_params
        
        # Compatibility assessment
        compatible = len(added_params) == 0  # Can only be compatible if no new params added
        migration_needed = len(added_params) > 0 or len(removed_params) > 0
        
        # Check case-by-case compatibility
        case_analysis = []
        for case in existing_cases[:5]:  # Sample first 5 cases
            case_issues = self._analyze_case_compatibility(case, new_prompt)
            case_analysis.append(case_issues)
        
        return {
            'status': 'analyzed',
            'compatible': compatible,
            'migration_needed': migration_needed,
            'cases_analyzed': len(existing_cases),
            'cases_sampled': len(case_analysis),
            'parameter_changes': {
                'removed': list(removed_params),
                'added': list(added_params),
                'kept': list(kept_params)
            },
            'case_samples': case_analysis,
            'recommendations': self._generate_recommendations(
                compatible, migration_needed, removed_params, added_params
            )
        }
    
    def migrate_dataset(
        self, 
        dataset: EvaluationDataset, 
        new_prompt: SystemPrompt,
        migration_strategy: str = 'regenerate_all'
    ) -> Dict[str, Any]:
        """
        Migrate dataset to be compatible with new prompt parameters
        
        Args:
            dataset: Dataset to migrate
            new_prompt: New prompt with updated parameters
            migration_strategy: 'regenerate_all', 'partial_update', or 'create_new'
        
        Returns:
            Migration results
        """
        if not new_prompt.parameters:
            new_prompt.extract_parameters()
        
        original_case_count = dataset.cases.count()
        
        try:
            if migration_strategy == 'regenerate_all':
                return self._regenerate_all_cases(dataset, new_prompt)
            elif migration_strategy == 'partial_update':
                return self._partial_update_cases(dataset, new_prompt)
            elif migration_strategy == 'create_new':
                return self._create_new_dataset(dataset, new_prompt)
            else:
                raise ValueError(f"Unknown migration strategy: {migration_strategy}")
                
        except Exception as e:
            logger.error(f"Dataset migration failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'original_case_count': original_case_count,
                'migrated_case_count': 0
            }
    
    def _extract_parameters_from_case(self, case: EvaluationCase) -> List[str]:
        """Extract parameters that were used to generate this case"""
        # Try to get from context first
        if 'parameters_used' in case.context:
            return list(case.context['parameters_used'].keys())
        
        # Fallback: detect parameters from input text
        import re
        # Look for remaining placeholder patterns in input
        placeholder_pattern = r'{{([^{}]+)}}'
        remaining_placeholders = re.findall(placeholder_pattern, case.input_text)
        
        # If no placeholders remain, we can't reliably determine original parameters
        # This is a limitation of the current design
        if not remaining_placeholders:
            # Try to infer from common patterns in the input text
            return self._infer_parameters_from_content(case.input_text)
        
        return remaining_placeholders
    
    def _infer_parameters_from_content(self, content: str) -> List[str]:
        """Attempt to infer what parameters were likely used based on content"""
        # This is heuristic-based and not 100% reliable
        potential_params = []
        
        content_lower = content.lower()
        
        # Common parameter patterns
        if 'email:' in content_lower or 'email content' in content_lower:
            potential_params.append('EMAIL_CONTENT')
        if 'recipient' in content_lower:
            potential_params.append('RECIPIENT_INFO')
        if 'sender' in content_lower:
            potential_params.append('SENDER_INFO')
        if 'customer' in content_lower:
            potential_params.append('CUSTOMER_INFO')
        
        return potential_params
    
    def _analyze_case_compatibility(self, case: EvaluationCase, new_prompt: SystemPrompt) -> Dict[str, Any]:
        """Analyze if a specific case is compatible with new prompt"""
        # Check for placeholder mismatches
        import re
        
        # Find any remaining placeholders in input text
        placeholder_pattern = r'{{([^{}]+)}}'
        remaining_placeholders = re.findall(placeholder_pattern, case.input_text)
        
        new_params = set(new_prompt.parameters)
        case_placeholders = set(remaining_placeholders)
        
        missing_params = new_params - case_placeholders
        extra_placeholders = case_placeholders - new_params
        
        return {
            'case_id': case.id,
            'compatible': len(missing_params) == 0 and len(extra_placeholders) == 0,
            'missing_parameters': list(missing_params),
            'extra_placeholders': list(extra_placeholders),
            'input_preview': case.input_text[:100] + '...' if len(case.input_text) > 100 else case.input_text
        }
    
    def _generate_recommendations(
        self, 
        compatible: bool, 
        migration_needed: bool, 
        removed_params: set, 
        added_params: set
    ) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        if compatible and not migration_needed:
            recommendations.append("✅ Dataset is fully compatible with new prompt")
            recommendations.append("💡 No action needed, cases can be used as-is")
        
        elif migration_needed:
            if added_params:
                recommendations.append(f"⚠️ New parameters added: {list(added_params)}")
                recommendations.append("🔧 Regenerate cases to include new parameters")
            
            if removed_params:
                recommendations.append(f"📉 Parameters removed: {list(removed_params)}")
                recommendations.append("🧹 Update cases to remove obsolete parameters")
            
            recommendations.append("🎯 Recommended: Run full dataset migration")
            recommendations.append("⚡ Alternative: Create new dataset for new prompt")
        
        recommendations.append("💾 Consider backing up existing dataset before migration")
        
        return recommendations
    
    def _regenerate_all_cases(self, dataset: EvaluationDataset, new_prompt: SystemPrompt) -> Dict[str, Any]:
        """Regenerate all cases in dataset with new prompt parameters"""
        original_case_count = dataset.cases.count()
        
        # Get sample of original cases for reference
        original_cases = list(dataset.cases.all())
        
        # Clear existing cases
        dataset.cases.all().delete()
        
        # Generate new cases
        try:
            new_cases_data = self.case_generator.generate_cases_preview(
                new_prompt, 
                count=min(original_case_count, 10)  # Limit to reasonable number
            )
            
            migrated_cases = []
            for case_data in new_cases_data:
                new_case = EvaluationCase.objects.create(
                    dataset=dataset,
                    input_text=case_data['input_text'],
                    expected_output=case_data['expected_output'],
                    context={
                        'parameters_used': case_data['parameters'],
                        'migration_source': 'regenerate_all',
                        'prompt_version': new_prompt.version
                    }
                )
                migrated_cases.append(new_case)
            
            return {
                'status': 'success',
                'strategy': 'regenerate_all',
                'original_case_count': original_case_count,
                'migrated_case_count': len(migrated_cases),
                'dataset_id': dataset.id
            }
            
        except Exception as e:
            # Restore original cases if migration fails
            for original_case in original_cases:
                EvaluationCase.objects.create(
                    dataset=dataset,
                    input_text=original_case.input_text,
                    expected_output=original_case.expected_output,
                    context=original_case.context
                )
            raise e
    
    def _partial_update_cases(self, dataset: EvaluationDataset, new_prompt: SystemPrompt) -> Dict[str, Any]:
        """Update existing cases to work with new prompt (if possible)"""
        # This is a more complex strategy that tries to preserve existing cases
        # while updating them to work with new parameters
        
        updated_count = 0
        failed_count = 0
        
        for case in dataset.cases.all():
            try:
                # Try to update case to work with new prompt
                updated_input = self._update_case_input(case.input_text, new_prompt)
                
                if updated_input != case.input_text:
                    case.input_text = updated_input
                    case.context.update({
                        'migration_source': 'partial_update',
                        'prompt_version': new_prompt.version
                    })
                    case.save()
                    updated_count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to update case {case.id}: {e}")
                failed_count += 1
        
        return {
            'status': 'success',
            'strategy': 'partial_update',
            'updated_count': updated_count,
            'failed_count': failed_count,
            'total_cases': dataset.cases.count()
        }
    
    def _update_case_input(self, input_text: str, new_prompt: SystemPrompt) -> str:
        """Update case input text to work with new prompt parameters"""
        # This is a simplified implementation - in practice, this would be much more complex
        # and might involve LLM assistance to intelligently map old parameters to new ones
        
        # For now, just replace the prompt template portion
        # This assumes the input_text starts with the prompt template
        
        lines = input_text.split('\n')
        
        # Find where the actual email content starts (heuristic)
        content_start = 0
        for i, line in enumerate(lines):
            if 'email:' in line.lower() or line.strip().startswith('dear') or line.strip().startswith('hi'):
                content_start = i
                break
        
        # Extract the content portion
        if content_start > 0:
            content_lines = lines[content_start:]
            content = '\n'.join(content_lines)
            
            # Generate new parameter values for the new prompt
            param_values = self.case_generator._generate_parameter_values(new_prompt.parameters)
            
            # Create new input with new prompt template
            new_input = self.case_generator._substitute_parameters(new_prompt.content, param_values)
            
            return new_input
        
        # If we can't parse it, return original
        return input_text
    
    def _create_new_dataset(self, original_dataset: EvaluationDataset, new_prompt: SystemPrompt) -> Dict[str, Any]:
        """Create a new dataset instead of migrating the existing one"""
        
        new_dataset = EvaluationDataset.objects.create(
            session=original_dataset.session,
            name=f"{original_dataset.name} (v{new_prompt.version})",
            description=f"Migrated from '{original_dataset.name}' for prompt v{new_prompt.version}"
        )
        
        # Generate cases for new dataset
        case_count = min(original_dataset.cases.count(), 10)
        new_cases_data = self.case_generator.generate_cases_preview(new_prompt, count=case_count)
        
        created_cases = []
        for case_data in new_cases_data:
            new_case = EvaluationCase.objects.create(
                dataset=new_dataset,
                input_text=case_data['input_text'],
                expected_output=case_data['expected_output'],
                context={
                    'parameters_used': case_data['parameters'],
                    'migration_source': 'create_new',
                    'original_dataset_id': original_dataset.id,
                    'prompt_version': new_prompt.version
                }
            )
            created_cases.append(new_case)
        
        return {
            'status': 'success',
            'strategy': 'create_new',
            'original_dataset_id': original_dataset.id,
            'new_dataset_id': new_dataset.id,
            'new_case_count': len(created_cases)
        }