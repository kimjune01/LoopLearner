"""
Test Story 2: Generate Evaluation Cases from Prompt Parameters (Updated)
Following TDD principles - these tests define the expected behavior for case generation.
"""
import json
import pytest
from django.test import TestCase, Client
from core.models import PromptLab, SystemPrompt, EvaluationDataset, EvaluationCase


class EvaluationGeneratorStoryTests(TestCase):
    """Test Story 2: As a user, I can generate evaluation cases automatically from templates and parameters"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.prompt_lab = PromptLab.objects.create(
            name="Test PromptLab",
            description="A test session for evaluation"
        )
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset",
            description="A test evaluation dataset",
            parameters=["user_name", "product_type", "user_question"]
        )
    
    def test_generate_cases_from_template(self):
        """
        Test: Given a template with parameters like {user_name}, {product_type},
        when I generate evaluation cases, then cases are created with different parameter values but not yet saved
        """
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'template': 'You are a helpful customer service assistant. Help {user_name} with their {product_type} question: {user_question}',
            'count': 3
        }
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        
        # Expecting 200 OK (preview, not saved)
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertEqual(len(response_data['previews']), 3)
        
        # Verify cases have parameter values filled in
        for case in response_data['previews']:
            self.assertIn('generated_input', case)
            self.assertIn('generated_output', case)
            self.assertIn('parameters', case)
            self.assertIn('user_name', case['parameters'])
            self.assertIn('product_type', case['parameters'])
            self.assertIn('user_question', case['parameters'])
            
            # Verify parameters are substituted in generated_input
            self.assertNotIn('{user_name}', case['generated_input'])
            self.assertNotIn('{product_type}', case['generated_input'])
            self.assertNotIn('{user_question}', case['generated_input'])
        
        # Verify cases are NOT saved to database yet
        self.assertEqual(EvaluationCase.objects.filter(dataset=self.dataset).count(), 0)
    
    def test_synthetic_case_generation_diversity(self):
        """
        Test: Given a template and parameter schema, when I request N evaluation cases,
        then N diverse cases are generated with realistic parameter values for preview
        """
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'template': 'User {user_name} needs help with {product_type}: {user_question}',
            'count': 5
        }
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Verify we get exactly 5 cases
        self.assertEqual(len(response_data['previews']), 5)
        
        # Verify diversity - parameter values should be different across cases
        user_names = set()
        product_types = set()
        user_questions = set()
        
        for case in response_data['previews']:
            user_names.add(case['parameters']['user_name'])
            product_types.add(case['parameters']['product_type'])
            user_questions.add(case['parameters']['user_question'])
        
        # Should have some diversity (at least 2 different values for each parameter)
        self.assertGreaterEqual(len(user_names), 2)
        self.assertGreaterEqual(len(product_types), 2)
        self.assertGreaterEqual(len(user_questions), 2)
    
    def test_add_selected_cases_to_dataset(self):
        """
        Test: Given generated case previews, when I select specific cases to add,
        then only those cases are added to the evaluation dataset permanently
        """
        # First generate cases
        generate_url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        generate_data = {
            'template': 'Customer {user_name} has a question about {product_type}: {user_question}',
            'count': 3
        }
        
        response = self.client.post(generate_url, json.dumps(generate_data), content_type='application/json')
        generated_cases = response.json()['previews']
        
        # Select first and third cases (indices 0 and 2)
        selected_preview_ids = [generated_cases[0]['preview_id'], generated_cases[2]['preview_id']]
        
        # Add selected cases to dataset
        add_url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        add_data = {
            'preview_ids': selected_preview_ids
        }
        
        response = self.client.post(add_url, json.dumps(add_data), content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        
        # Verify correct number of cases added
        self.assertEqual(response_data['added_count'], 2)
        
        # Verify cases are now in the database
        saved_cases = EvaluationCase.objects.filter(dataset=self.dataset)
        self.assertEqual(saved_cases.count(), 2)
        
        # Verify the saved cases match the selected previews
        for saved_case in saved_cases:
            self.assertIsNotNone(saved_case.input_text)
            self.assertIsNotNone(saved_case.expected_output)
            self.assertIsInstance(saved_case.context, dict)  # Parameters stored in context
    
    def test_error_handling_missing_template(self):
        """
        Test: Given a request without template, when I try to generate cases,
        then an appropriate error is returned
        """
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'count': 3
            # Missing template
        }
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('template or prompt_id is required', response_data['error'])
    
    def test_error_handling_excessive_count(self):
        """
        Test: Given a request for too many cases, when I try to generate cases,
        then an appropriate error is returned
        """
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'template': 'User {user_name} asks: {user_question}',
            'count': 25  # Over the limit of 20
        }
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('Maximum 20 cases', response_data['error'])