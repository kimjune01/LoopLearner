"""
Test Story 2: Generate Evaluation Cases from Prompt Parameters
Following TDD principles - these tests define the expected behavior for case generation.
"""
import json
import pytest
from django.test import TestCase, Client
from core.models import Session, SystemPrompt, EvaluationDataset, EvaluationCase


class EvaluationGeneratorStoryTests(TestCase):
    """Test Story 2: As a user, I can generate evaluation cases automatically from my prompt and its parameters"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.session = Session.objects.create(
            name="Test Session",
            description="A test session for evaluation"
        )
        self.dataset = EvaluationDataset.objects.create(
            session=self.session,
            name="Test Dataset",
            description="A test evaluation dataset",
            parameters=["user_name", "product_type", "user_question"]
        )
        self.prompt = SystemPrompt.objects.create(
            session=self.session,
            content="You are a helpful customer service assistant. Help {{user_name}} with their {{product_type}} question: {{user_question}}",
            version=1,
            is_active=True,
            parameters=["user_name", "product_type", "user_question"]
        )
    
    def test_generate_cases_from_prompt_parameters(self):
        """
        Test: Given a prompt with parameters like {{user_name}}, {{product_type}},
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
    
    def test_synthetic_case_generation(self):
        """
        Test: Given a prompt and parameter schema, when I request N evaluation cases,
        then N diverse cases are generated with realistic parameter values for preview
        """
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'template': 'You are a helpful customer service assistant. Help {user_name} with their {product_type} question: {user_question}',
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
    
    def test_parameter_value_generation(self):
        """
        Test: Given parameters with different types (names, emails, products),
        when I generate case values, then values are appropriate for each parameter type
        """
        # Create prompt with typed parameters
        typed_prompt = SystemPrompt.objects.create(
            session=self.session,
            content="Send email to {{customer_email}} about their {{order_id}} for {{product_name}}",
            version=2,
            parameters=["customer_email", "order_id", "product_name"]
        )
        
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'prompt_id': str(typed_prompt.id),
            'count': 3
        }
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        for case in response_data['generated_cases']:
            params = case['parameters']
            
            # Verify email format
            email = params['customer_email']
            self.assertIn('@', email)
            self.assertTrue(email.endswith('.com') or email.endswith('.org') or email.endswith('.net'))
            
            # Verify order_id format (should be alphanumeric)
            order_id = params['order_id']
            self.assertTrue(len(order_id) >= 5)
            
            # Verify product_name is reasonable
            product_name = params['product_name']
            self.assertTrue(len(product_name) >= 3)
    
    def test_preview_generated_cases(self):
        """
        Test: Given generated evaluation cases, when I view the preview,
        then I see input text, expected output, and parameter values for each case
        """
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'prompt_id': str(self.prompt.id),
            'count': 2
        }
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Verify preview structure
        self.assertIn('generated_cases', response_data)
        self.assertIn('prompt_content', response_data)
        self.assertIn('dataset_id', response_data)
        
        for case in response_data['generated_cases']:
            # Required fields for preview
            self.assertIn('preview_id', case)  # Temporary ID for selection
            self.assertIn('input_text', case)
            self.assertIn('expected_output', case)
            self.assertIn('parameters', case)
            
            # Verify input_text has parameters substituted
            input_text = case['input_text']
            self.assertIn(case['parameters']['user_name'], input_text)
            self.assertIn(case['parameters']['product_type'], input_text)
            self.assertIn(case['parameters']['user_question'], input_text)
    
    def test_select_cases_for_dataset(self):
        """
        Test: Given a list of generated cases with selection checkboxes,
        when I select specific cases and confirm, then only selected cases are added to the evaluation dataset
        """
        # First generate cases
        generate_url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        generate_data = {
            'prompt_id': str(self.prompt.id),
            'count': 4
        }
        
        response = self.client.post(generate_url, json.dumps(generate_data), content_type='application/json')
        generated_cases = response.json()['generated_cases']
        
        # Select only first and third cases
        selected_cases = [generated_cases[0], generated_cases[2]]
        
        # Add selected cases to dataset
        select_url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        select_data = {
            'selected_cases': selected_cases
        }
        
        response = self.client.post(select_url, json.dumps(select_data), content_type='application/json')
        
        # Expecting 201 Created
        self.assertEqual(response.status_code, 201)
        
        # Verify only 2 cases were added to database
        saved_cases = EvaluationCase.objects.filter(dataset=self.dataset)
        self.assertEqual(saved_cases.count(), 2)
        
        # Verify the cases match our selection
        saved_inputs = [case.input_text for case in saved_cases]
        self.assertIn(selected_cases[0]['input_text'], saved_inputs)
        self.assertIn(selected_cases[1]['input_text'], saved_inputs)
        
        response_data = response.json()
        self.assertEqual(response_data['added_count'], 2)
        self.assertEqual(len(response_data['case_ids']), 2)
    
    def test_regenerate_individual_cases(self):
        """
        Test: Given a generated case I don't like, when I click regenerate on that specific case,
        then a new case with different parameter values is generated
        """
        # First generate a case
        generate_url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        generate_data = {
            'prompt_id': str(self.prompt.id),
            'count': 1
        }
        
        response = self.client.post(generate_url, json.dumps(generate_data), content_type='application/json')
        original_case = response.json()['generated_cases'][0]
        
        # Regenerate this specific case
        regenerate_url = f'/api/evaluations/datasets/{self.dataset.id}/regenerate-case/'
        regenerate_data = {
            'prompt_id': str(self.prompt.id),
            'case_to_replace': original_case
        }
        
        response = self.client.post(regenerate_url, json.dumps(regenerate_data), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        new_case = response.json()['regenerated_case']
        
        # Verify structure is the same
        self.assertIn('input_text', new_case)
        self.assertIn('expected_output', new_case)
        self.assertIn('parameters', new_case)
        
        # Verify at least one parameter value changed
        original_params = original_case['parameters']
        new_params = new_case['parameters']
        
        # At least one parameter should be different
        params_changed = (
            original_params['user_name'] != new_params['user_name'] or
            original_params['product_type'] != new_params['product_type'] or
            original_params['user_question'] != new_params['user_question']
        )
        self.assertTrue(params_changed)
    
    def test_edit_case_parameters_manually(self):
        """
        Test: Given a generated case with parameters like {{user_name: "John"}}, {{product_type: "laptop"}},
        when I edit the parameter values directly (e.g., change "John" to "Sarah"),
        then the case input text and expected output are updated to reflect the new parameter values
        """
        # First generate a case
        generate_url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        generate_data = {
            'prompt_id': str(self.prompt.id),
            'count': 1
        }
        
        response = self.client.post(generate_url, json.dumps(generate_data), content_type='application/json')
        original_case = response.json()['generated_cases'][0]
        preview_id = original_case['preview_id']
        
        # Edit parameters
        edit_url = f'/api/evaluations/cases/preview/{preview_id}/parameters/'
        new_parameters = {
            'user_name': 'Sarah',
            'product_type': 'smartphone',
            'user_question': 'How do I reset my device?'
        }
        edit_data = {
            'parameters': new_parameters,
            'prompt_id': str(self.prompt.id)
        }
        
        response = self.client.put(edit_url, json.dumps(edit_data), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        updated_case = response.json()['updated_case']
        
        # Verify parameters were updated
        self.assertEqual(updated_case['parameters']['user_name'], 'Sarah')
        self.assertEqual(updated_case['parameters']['product_type'], 'smartphone')
        self.assertEqual(updated_case['parameters']['user_question'], 'How do I reset my device?')
        
        # Verify input_text reflects new parameters
        input_text = updated_case['input_text']
        self.assertIn('Sarah', input_text)
        self.assertIn('smartphone', input_text)
        self.assertIn('How do I reset my device?', input_text)
    
    def test_validate_edited_parameters(self):
        """
        Test: Given a case with manually edited parameters, when I save the changes,
        then the system validates the parameter values and updates the case accordingly
        """
        # Generate a case first
        generate_url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        generate_data = {
            'prompt_id': str(self.prompt.id),
            'count': 1
        }
        
        response = self.client.post(generate_url, json.dumps(generate_data), content_type='application/json')
        original_case = response.json()['generated_cases'][0]
        preview_id = original_case['preview_id']
        
        # Try to edit with invalid parameters (missing required parameter)
        edit_url = f'/api/evaluations/cases/preview/{preview_id}/parameters/'
        invalid_parameters = {
            'user_name': 'Sarah',
            'product_type': 'smartphone'
            # Missing 'user_question' - should cause validation error
        }
        edit_data = {
            'parameters': invalid_parameters,
            'prompt_id': str(self.prompt.id)
        }
        
        response = self.client.put(edit_url, json.dumps(edit_data), content_type='application/json')
        
        # Should return validation error
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertIn('user_question', response.json()['error'])
    
    def test_regenerate_output_after_parameter_edit(self):
        """
        Test: Given a case where I've manually edited parameter values,
        when I request to regenerate the expected output,
        then a new expected output is generated using the updated parameter values
        """
        # Generate a case first
        generate_url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        generate_data = {
            'prompt_id': str(self.prompt.id),
            'count': 1
        }
        
        response = self.client.post(generate_url, json.dumps(generate_data), content_type='application/json')
        original_case = response.json()['generated_cases'][0]
        preview_id = original_case['preview_id']
        
        # Edit parameters first
        edit_url = f'/api/evaluations/cases/preview/{preview_id}/parameters/'
        new_parameters = {
            'user_name': 'Alice',
            'product_type': 'tablet',
            'user_question': 'How do I update the software?'
        }
        edit_data = {
            'parameters': new_parameters,
            'prompt_id': str(self.prompt.id)
        }
        
        response = self.client.put(edit_url, json.dumps(edit_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Now regenerate the expected output
        regenerate_url = f'/api/evaluations/cases/preview/{preview_id}/regenerate-output/'
        regenerate_data = {
            'prompt_id': str(self.prompt.id)
        }
        
        response = self.client.post(regenerate_url, json.dumps(regenerate_data), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        updated_case = response.json()['updated_case']
        
        # Verify the expected output was regenerated
        self.assertNotEqual(updated_case['expected_output'], original_case['expected_output'])
        
        # Verify the expected output references the new parameters
        expected_output = updated_case['expected_output']
        # The output should be contextually relevant to Alice, tablet, and software update
        self.assertTrue(len(expected_output) > 10)  # Should be a meaningful response