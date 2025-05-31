"""
Tests for evaluation dataset migration when prompt parameters change
"""
import pytest
from django.test import TestCase
from core.models import Session, SystemPrompt, EvaluationDataset, EvaluationCase
from app.services.evaluation_dataset_migrator import EvaluationDatasetMigrator
from app.services.evaluation_case_generator import EvaluationCaseGenerator


class EvaluationDatasetMigrationTests(TestCase):
    """Test dataset migration functionality when prompt parameters change"""
    
    def setUp(self):
        """Set up test data"""
        self.session = Session.objects.create(
            name="Migration Test Session",
            description="Testing dataset migration"
        )
        
        # Original prompt with simple parameters
        self.original_prompt = SystemPrompt.objects.create(
            session=self.session,
            content="""You are an email assistant.

Email: {{EMAIL_CONTENT}}
Recipient: {{RECIPIENT_INFO}}

Provide a professional response.""",
            version=1,
            parameters=['EMAIL_CONTENT', 'RECIPIENT_INFO']
        )
        
        # Updated prompt with different parameters
        self.updated_prompt = SystemPrompt.objects.create(
            session=self.session,
            content="""You are a customer service assistant.

Email Content: {{EMAIL_CONTENT}}
Customer: {{CUSTOMER_INFO}}
Priority: {{PRIORITY}}
Department: {{DEPARTMENT}}

Provide a professional response.""",
            version=2,
            parameters=['EMAIL_CONTENT', 'CUSTOMER_INFO', 'PRIORITY', 'DEPARTMENT']
        )
        
        # Create dataset with original cases
        self.dataset = EvaluationDataset.objects.create(
            session=self.session,
            name="Test Migration Dataset"
        )
        
        # Create test cases with original parameters
        self.original_cases = [
            EvaluationCase.objects.create(
                dataset=self.dataset,
                input_text="""You are an email assistant.

Email: Hi, I need help with my order.
Recipient: John Smith, Premium Customer

Provide a professional response.""",
                expected_output="Thank you for contacting us about your order...",
                context={'parameters_used': {'EMAIL_CONTENT': 'Hi, I need help with my order.', 'RECIPIENT_INFO': 'John Smith, Premium Customer'}}
            ),
            EvaluationCase.objects.create(
                dataset=self.dataset,
                input_text="""You are an email assistant.

Email: Can you help me return this item?
Recipient: Sarah Johnson, Business Account

Provide a professional response.""",
                expected_output="I'll be happy to help you with your return...",
                context={'parameters_used': {'EMAIL_CONTENT': 'Can you help me return this item?', 'RECIPIENT_INFO': 'Sarah Johnson, Business Account'}}
            )
        ]
        
        self.migrator = EvaluationDatasetMigrator()
    
    def test_analyze_parameter_compatibility_with_compatible_prompt(self):
        """Test compatibility analysis when prompts are compatible"""
        # Same parameters should be compatible
        analysis = self.migrator.analyze_parameter_compatibility(self.dataset, self.original_prompt)
        
        self.assertEqual(analysis['status'], 'analyzed')
        self.assertTrue(analysis['compatible'])
        self.assertFalse(analysis['migration_needed'])
        self.assertEqual(len(analysis['parameter_changes']['removed']), 0)
        self.assertEqual(len(analysis['parameter_changes']['added']), 0)
        self.assertEqual(len(analysis['parameter_changes']['kept']), 2)
    
    def test_analyze_parameter_compatibility_with_incompatible_prompt(self):
        """Test compatibility analysis when prompts have different parameters"""
        analysis = self.migrator.analyze_parameter_compatibility(self.dataset, self.updated_prompt)
        
        self.assertEqual(analysis['status'], 'analyzed')
        self.assertFalse(analysis['compatible'])  # Added new parameters
        self.assertTrue(analysis['migration_needed'])
        
        # Check parameter changes
        changes = analysis['parameter_changes']
        self.assertIn('RECIPIENT_INFO', changes['removed'])
        self.assertIn('CUSTOMER_INFO', changes['added'])
        self.assertIn('PRIORITY', changes['added'])
        self.assertIn('DEPARTMENT', changes['added'])
        self.assertIn('EMAIL_CONTENT', changes['kept'])
    
    def test_analyze_empty_dataset_compatibility(self):
        """Test compatibility analysis with empty dataset"""
        empty_dataset = EvaluationDataset.objects.create(
            session=self.session,
            name="Empty Dataset"
        )
        
        analysis = self.migrator.analyze_parameter_compatibility(empty_dataset, self.updated_prompt)
        
        self.assertEqual(analysis['status'], 'empty_dataset')
        self.assertTrue(analysis['compatible'])
        self.assertFalse(analysis['migration_needed'])
        self.assertEqual(analysis['cases_analyzed'], 0)
    
    def test_migrate_dataset_regenerate_all_strategy(self):
        """Test full dataset regeneration migration strategy"""
        original_count = self.dataset.cases.count()
        
        result = self.migrator.migrate_dataset(
            self.dataset, 
            self.updated_prompt, 
            migration_strategy='regenerate_all'
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['strategy'], 'regenerate_all')
        self.assertEqual(result['original_case_count'], original_count)
        self.assertGreater(result['migrated_case_count'], 0)
        
        # Verify new cases have correct parameters
        migrated_cases = list(self.dataset.cases.all())
        self.assertGreater(len(migrated_cases), 0)
        
        for case in migrated_cases:
            # Should contain new parameters in context
            if 'parameters_used' in case.context:
                params = case.context['parameters_used']
                self.assertIn('EMAIL_CONTENT', params)
                self.assertIn('CUSTOMER_INFO', params)
                self.assertIn('PRIORITY', params)
                self.assertIn('DEPARTMENT', params)
    
    def test_migrate_dataset_create_new_strategy(self):
        """Test creating new dataset migration strategy"""
        original_dataset_id = self.dataset.id
        original_count = self.dataset.cases.count()
        
        result = self.migrator.migrate_dataset(
            self.dataset,
            self.updated_prompt,
            migration_strategy='create_new'
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['strategy'], 'create_new')
        self.assertEqual(result['original_dataset_id'], original_dataset_id)
        self.assertNotEqual(result['new_dataset_id'], original_dataset_id)
        self.assertGreater(result['new_case_count'], 0)
        
        # Verify original dataset is unchanged
        self.assertEqual(self.dataset.cases.count(), original_count)
        
        # Verify new dataset exists with new cases
        new_dataset = EvaluationDataset.objects.get(id=result['new_dataset_id'])
        self.assertGreater(new_dataset.cases.count(), 0)
        self.assertIn(self.dataset.name, new_dataset.name)
    
    def test_extract_parameters_from_case_with_context(self):
        """Test parameter extraction from case context"""
        case = self.original_cases[0]
        
        extracted_params = self.migrator._extract_parameters_from_case(case)
        
        # Should extract from context
        self.assertIn('EMAIL_CONTENT', extracted_params)
        self.assertIn('RECIPIENT_INFO', extracted_params)
    
    def test_extract_parameters_from_case_without_context(self):
        """Test parameter extraction when context is missing"""
        case_without_context = EvaluationCase.objects.create(
            dataset=self.dataset,
            input_text="Email about {{SUBJECT}} for {{USER_NAME}}",
            expected_output="Response...",
            context={}  # No parameters_used in context
        )
        
        extracted_params = self.migrator._extract_parameters_from_case(case_without_context)
        
        # Should detect remaining placeholders
        self.assertIn('SUBJECT', extracted_params)
        self.assertIn('USER_NAME', extracted_params)
    
    def test_generate_recommendations_for_compatible_dataset(self):
        """Test recommendation generation for compatible datasets"""
        recommendations = self.migrator._generate_recommendations(
            compatible=True,
            migration_needed=False,
            removed_params=set(),
            added_params=set()
        )
        
        self.assertIn('✅ Dataset is fully compatible', ' '.join(recommendations))
        self.assertIn('💡 No action needed', ' '.join(recommendations))
    
    def test_generate_recommendations_for_incompatible_dataset(self):
        """Test recommendation generation for incompatible datasets"""
        recommendations = self.migrator._generate_recommendations(
            compatible=False,
            migration_needed=True,
            removed_params={'OLD_PARAM'},
            added_params={'NEW_PARAM1', 'NEW_PARAM2'}
        )
        
        recommendations_text = ' '.join(recommendations)
        self.assertIn('⚠️ New parameters added', recommendations_text)
        self.assertIn('📉 Parameters removed', recommendations_text)
        self.assertIn('🔧 Regenerate cases', recommendations_text)
        self.assertIn('🎯 Recommended: Run full dataset migration', recommendations_text)
    
    def test_migration_preserves_dataset_metadata(self):
        """Test that migration preserves important dataset metadata"""
        original_name = self.dataset.name
        original_session = self.dataset.session
        
        result = self.migrator.migrate_dataset(
            self.dataset,
            self.updated_prompt,
            migration_strategy='regenerate_all'
        )
        
        # Refresh dataset from database
        self.dataset.refresh_from_db()
        
        # Metadata should be preserved
        self.assertEqual(self.dataset.name, original_name)
        self.assertEqual(self.dataset.session, original_session)
        
        # But cases should be updated
        updated_cases = list(self.dataset.cases.all())
        self.assertGreater(len(updated_cases), 0)
        
        # Migration metadata should be added to cases
        for case in updated_cases:
            if 'migration_source' in case.context:
                self.assertEqual(case.context['migration_source'], 'regenerate_all')
                self.assertEqual(case.context['prompt_version'], self.updated_prompt.version)
    
    def test_invalid_migration_strategy_returns_error(self):
        """Test that invalid migration strategies return error results"""
        result = self.migrator.migrate_dataset(
            self.dataset,
            self.updated_prompt,
            migration_strategy='invalid_strategy'
        )
        
        self.assertEqual(result['status'], 'failed')
        self.assertIn('Unknown migration strategy', result['error'])