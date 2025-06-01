"""
Test -based evaluation case generation functionality.
Tests the integration between , prompts, and evaluation datasets.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from core.models import PromptLab, SystemPrompt, EvaluationDataset, EvaluationCase


class PromptLabBasedCaseGenerationTests(TestCase):
    """Test -based case generation functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create a test prompt lab with an active prompt
        self.prompt_lab = PromptLab.objects.create(
            name='Customer Service PromptLab',
            description='Testing prompt lab-based case generation'
        )
        
        self.prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content='Hello {{customer_name}}, thank you for contacting us about {{issue_type}}. I understand you are {{emotion}} about this situation. Let me help you with {{resolution_request}}.',
            version=1,
            is_active=True
        )
        
        # Create a prompt lab-associated dataset
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name='Customer Service Cases',
            description='Generated from prompt lab prompt',
            parameters=['customer_name', 'issue_type', 'emotion', 'resolution_request']
        )
        
        # Create a global dataset (not associated with prompt lab)
        self.global_dataset = EvaluationDataset.objects.create(
            name='Global Dataset',
            description='Not associated with any ',
            parameters=['test_param']
        )
    
    def test_prompt_lab_prompt_parameters_extracted(self):
        """Test that prompt parameters are properly extracted"""
        expected_params = ['customer_name', 'issue_type', 'emotion', 'resolution_request']
        self.assertEqual(self.prompt.parameters, expected_params)
    
    def test_dataset_session_association(self):
        """Test that dataset is properly associated with """
        self.assertEqual(self.dataset.session, self.prompt_lab)
        self.assertEqual(self.dataset.prompt_lab.name, 'Customer Service PromptLab')
    
    def test_generate_cases_with_session_prompt(self):
        """Test generating cases using  prompt"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'use_session_prompt': True,
            'count': 2
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Check response structure
        self.assertIn('previews', response_data)
        self.assertIn('generation_method', response_data)
        self.assertIn('prompt_lab_name', response_data)
        self.assertIn('prompt_content', response_data)
        self.assertIn('prompt_parameters', response_data)
        
        # Check generation method
        self.assertEqual(response_data['generation_method'], 'session_prompt')
        self.assertEqual(response_data['prompt_lab_name'], 'Customer Service PromptLab')
        self.assertEqual(response_data['prompt_content'], self.prompt.content)
        self.assertEqual(response_data['prompt_parameters'], self.prompt.parameters)
        
        # Check generated previews
        previews = response_data['previews']
        self.assertEqual(len(previews), 2)
        
        for preview in previews:
            self.assertIn('preview_id', preview)
            self.assertIn('input_text', preview)
            self.assertIn('expected_output', preview)
            self.assertIn('parameters', preview)
            
            # Check that input_text contains substituted parameters
            input_text = preview['input_text']
            self.assertNotIn('{{customer_name}}', input_text)
            self.assertNotIn('{{issue_type}}', input_text)
            self.assertNotIn('{{emotion}}', input_text)
            self.assertNotIn('{{resolution_request}}', input_text)
            
            # Check that all required parameters are present
            parameters = preview['parameters']
            for param in self.prompt.parameters:
                self.assertIn(param, parameters)
                self.assertIsInstance(parameters[param], str)
                self.assertGreater(len(parameters[param]), 0)
    
    def test_generate_cases_with_template_fallback(self):
        """Test generating cases using template when  prompt is not used"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'template': 'Customer {{customer_name}} has a problem with {{issue_type}}',
            'use_session_prompt': False,
            'count': 2
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Check generation method
        self.assertEqual(response_data['generation_method'], 'template')
        self.assertIn('template', response_data)
        self.assertEqual(response_data['template'], data['template'])
        
        # Should not have -specific fields when using template
        self.assertNotIn('prompt_lab_name', response_data)
        self.assertNotIn('prompt_content', response_data)
    
    def test_generate_cases_no_active_prompt(self):
        """Test error when  has no active prompt"""
        # Deactivate the prompt
        self.prompt.is_active = False
        self.prompt.save()
        
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'use_session_prompt': True,
            'count': 2
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('No active prompt found', response_data['error'])
    
    def test_generate_cases_global_dataset_no_session(self):
        """Test that global datasets can't use  prompt generation"""
        url = f'/api/evaluations/datasets/{self.global_dataset.id}/generate-cases/'
        data = {
            'use_session_prompt': True,
            'count': 2
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should fall back to template generation, but require template
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('template is required', response_data['error'])
    
    def test_generate_cases_without_template_or_session_prompt(self):
        """Test error when neither template nor  prompt is provided"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'use_session_prompt': False,
            'count': 2
            # No template provided
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('template is required when not using session prompt', response_data['error'])
    
    def test_parameter_value_generation_quality(self):
        """Test that generated parameter values are reasonable"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'use_session_prompt': True,
            'count': 3
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        previews = response_data['previews']
        
        for preview in previews:
            parameters = preview['parameters']
            
            # Check customer_name looks like a name
            customer_name = parameters['customer_name']
            self.assertRegex(customer_name, r'^[A-Za-z]+ [A-Za-z]+$')  # First Last format
            
            # Check issue_type is not empty and reasonable
            issue_type = parameters['issue_type']
            self.assertGreater(len(issue_type), 3)
            
            # Check emotion is not empty
            emotion = parameters['emotion']
            self.assertGreater(len(emotion), 3)
            
            # Check resolution_request is not empty
            resolution_request = parameters['resolution_request']
            self.assertGreater(len(resolution_request), 5)
    
    def test_case_generation_diversity(self):
        """Test that multiple generated cases have different parameter values"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'use_session_prompt': True,
            'count': 5
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        previews = response_data['previews']
        
        # Check that not all customer names are the same
        customer_names = [p['parameters']['customer_name'] for p in previews]
        unique_names = set(customer_names)
        self.assertGreater(len(unique_names), 1, "Generated cases should have diverse customer names")
        
        # Check that not all issue types are the same
        issue_types = [p['parameters']['issue_type'] for p in previews]
        unique_issues = set(issue_types)
        self.assertGreater(len(unique_issues), 1, "Generated cases should have diverse issue types")
    
    def test_add_session_generated_cases_to_dataset(self):
        """Test adding -generated cases to dataset"""
        # First generate cases
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'use_session_prompt': True,
            'count': 2
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        previews = response_data['previews']
        
        # Add selected cases to dataset
        preview_ids = [p['preview_id'] for p in previews]
        add_url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        add_data = {
            'preview_ids': preview_ids
        }
        
        add_response = self.client.post(
            add_url,
            data=json.dumps(add_data),
            content_type='application/json'
        )
        
        self.assertEqual(add_response.status_code, 201)
        add_response_data = add_response.json()
        self.assertEqual(add_response_data['added_count'], 2)
        
        # Verify cases were added to database
        cases = EvaluationCase.objects.filter(dataset=self.dataset)
        self.assertEqual(cases.count(), 2)
        
        for case in cases:
            self.assertIsInstance(case.input_text, str)
            self.assertIsInstance(case.expected_output, str)
            self.assertGreater(len(case.input_text), 10)
            self.assertGreater(len(case.expected_output), 10)
            
            # Check that parameters were stored in context
            self.assertIsInstance(case.context, dict)
    
    def tearDown(self):
        """Clean up test data"""
        # Django test framework handles this automatically with database rollback
        pass


class PromptLabDatasetFilteringTests(TestCase):
    """Test -based dataset filtering functionality"""
    
    def setUp(self):
        """Set up test data for filtering tests"""
        self.client = Client()
        
        # Create prompt labs with different prompts
        self.prompt_lab1 = PromptLab.objects.create(name='Session 1')
        self.prompt1 = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab1,
            content='Template with {{customer_name}} and {{issue_type}}',
            version=1,
            is_active=True
        )
        
        self.prompt_lab2 = PromptLab.objects.create(name=' 2')
        self.prompt2 = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab2,
            content='Different template with {{user_id}} and {{product_name}}',
            version=1,
            is_active=True
        )
        
        # Create datasets with different parameter combinations
        self.dataset1 = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab1,
            name='Matching Dataset',
            parameters=['customer_name', 'issue_type']
        )
        
        self.dataset2 = EvaluationDataset.objects.create(
            name='Global Dataset',
            parameters=['customer_name', 'issue_type', 'priority']
        )
        
        self.dataset3 = EvaluationDataset.objects.create(
            name='Non-matching Dataset',
            parameters=['different_param', 'another_param']
        )
    
    def test_prompt_lab_dataset_filtering_with_params(self):
        """Test that session filtering returns only compatible datasets"""
        url = '/api/evaluations/datasets/'
        params = {
            'prompt_lab_id': str(self.prompt_lab1.id),
            'filter_by_params': 'true'
        }
        
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        datasets = response_data['datasets']
        
        # Should include  dataset and compatible global dataset
        dataset_names = [d['name'] for d in datasets]
        self.assertIn('Matching Dataset', dataset_names)
        self.assertIn('Global Dataset', dataset_names)  # Has overlapping parameters
        self.assertNotIn('Non-matching Dataset', dataset_names)  # No overlapping parameters
    
    def test_prompt_lab_dataset_filtering_without_params(self):
        """Test that unfiltered session view returns all accessible datasets"""
        url = '/api/evaluations/datasets/'
        params = {
            'prompt_lab_id': str(self.prompt_lab1.id),
            'filter_by_params': 'false'
        }
        
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        datasets = response_data['datasets']
        
        # Should include  datasets and all global datasets
        dataset_names = [d['name'] for d in datasets]
        self.assertIn('Matching Dataset', dataset_names)
        self.assertIn('Global Dataset', dataset_names)
        self.assertIn('Non-matching Dataset', dataset_names)