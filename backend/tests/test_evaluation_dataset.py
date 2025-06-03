"""
Tests for Story 1: Create Evaluation Dataset
Following TDD principles - these tests define the expected behavior.
"""
import json
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from core.models import PromptLab, SystemPrompt, EvaluationDataset, EvaluationCase


class EvaluationDatasetStoryTests(TestCase):
    """Test Story 1: As a user, I can create a simple evaluation dataset to test my prompts"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.prompt_lab = PromptLab.objects.create(
            name="Test PromptLab",
            description="A test session for evaluation"
        )
        self.prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="You are a helpful assistant.",
            version=1,
            is_active=True
        )
    
    def test_create_evaluation_dataset(self):
        """
        Test: Given a  with a prompt, when I create an evaluation dataset,
        then the dataset is saved with proper structure
        """
        # This test should initially fail because we haven't implemented the API yet
        url = '/api/evaluations/datasets/'
        data = {
            'prompt_lab_id': str(self.prompt_lab.id),
            'name': 'Customer Support Evaluation',
            'description': 'Test cases for customer support responses'
        }
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        
        # Expecting 201 Created
        self.assertEqual(response.status_code, 201)
        
        # Verify dataset was created
        datasets = EvaluationDataset.objects.filter(prompt_lab=self.prompt_lab)
        self.assertEqual(datasets.count(), 1)
        
        dataset = datasets.first()
        self.assertEqual(dataset.name, 'Customer Support Evaluation')
        self.assertEqual(dataset.description, 'Test cases for customer support responses')
        self.assertEqual(dataset.session, self.prompt_lab)
        
        # Verify response data
        response_data = response.json()
        self.assertEqual(response_data['name'], dataset.name)
        self.assertEqual(response_data['id'], dataset.id)
    
    def test_add_evaluation_case(self):
        """
        Test: Given an evaluation dataset, when I add a test case with input/expected output,
        then the case is stored and retrievable
        """
        # Create dataset first
        dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset"
        )
        
        # This test should initially fail because we haven't implemented the API yet
        url = f'/api/evaluations/datasets/{dataset.id}/cases/'
        data = {
            'input_text': 'Customer is asking about return policy',
            'expected_output': 'Our return policy allows returns within 30 days of purchase with original receipt.',
            'context': {'customer_tier': 'premium', 'product_category': 'electronics'}
        }
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        
        # Expecting 201 Created
        self.assertEqual(response.status_code, 201)
        
        # Verify case was created
        cases = EvaluationCase.objects.filter(dataset=dataset)
        self.assertEqual(cases.count(), 1)
        
        case = cases.first()
        self.assertEqual(case.input_text, 'Customer is asking about return policy')
        self.assertEqual(case.expected_output, 'Our return policy allows returns within 30 days of purchase with original receipt.')
        self.assertEqual(case.context['customer_tier'], 'premium')
        self.assertEqual(case.dataset, dataset)
        
        # Verify response data
        response_data = response.json()
        self.assertEqual(response_data['input_text'], case.input_text)
        self.assertEqual(response_data['id'], case.id)
    
    def test_import_jsonl_dataset(self):
        """
        Test: Given a valid JSONL file, when I import the dataset,
        then all cases are loaded correctly
        """
        # Create dataset first
        dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Imported Dataset"
        )
        
        # Make sure any existing prompts are inactive
        SystemPrompt.objects.filter(prompt_lab=self.prompt_lab).update(is_active=False)
        
        # Create a system prompt for parameter substitution
        system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="You are a customer service assistant answering questions about {{question_type}}.",
            version=2,  # Use version 2 to avoid conflicts
            is_active=True
        )
        
        # Sample JSONL content (3 test cases) using parameter format
        jsonl_content = """{"parameters": {"question_type": "return policy"}, "expected_output": "We accept returns within 30 days."}
{"parameters": {"question_type": "order tracking"}, "expected_output": "You can track your order using the tracking number sent via email."}
{"parameters": {"question_type": "order cancellation"}, "expected_output": "Orders can be cancelled within 2 hours of placement."}"""
        
        # This test should initially fail because we haven't implemented the API yet
        url = f'/api/evaluations/datasets/{dataset.id}/import/'
        
        # Simulate file upload
        from io import StringIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        jsonl_file = SimpleUploadedFile(
            "test_cases.jsonl",
            jsonl_content.encode('utf-8'),
            content_type="application/jsonl"
        )
        
        response = self.client.post(url, {'file': jsonl_file})
        
        # Expecting 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Verify all cases were imported
        cases = EvaluationCase.objects.filter(dataset=dataset)
        self.assertEqual(cases.count(), 3)
        
        # Verify first case - check that parameters were substituted
        first_case = cases.filter(context__question_type="return policy").first()
        self.assertIsNotNone(first_case)
        self.assertIn("return policy", first_case.input_text)
        self.assertEqual(first_case.expected_output, "We accept returns within 30 days.")
        self.assertEqual(first_case.context['question_type'], 'return policy')
        
        # Verify response data
        response_data = response.json()
        self.assertEqual(response_data['imported_count'], 3)
        self.assertEqual(response_data['dataset_id'], dataset.id)
    
    def test_list_datasets_for_session(self):
        """
        Test: Given multiple datasets, when I request datasets for a prompt lab,
        then only datasets for that  are returned
        """
        # Create datasets for our 
        dataset1 = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Dataset 1"
        )
        dataset2 = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Dataset 2"
        )
        
        # Create dataset for different 
        other_session = PromptLab.objects.create(name="Other PromptLab")
        other_dataset = EvaluationDataset.objects.create(
            prompt_lab=other_session,
            name="Other Dataset"
        )
        
        # This test should initially fail because we haven't implemented the API yet
        url = f'/api/evaluations/datasets/?session_id={self.prompt_lab.id}'
        
        response = self.client.get(url)
        
        # Expecting 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Verify response data
        response_data = response.json()
        self.assertEqual(len(response_data['datasets']), 2)
        
        # Verify our datasets are returned
        dataset_names = [d['name'] for d in response_data['datasets']]
        self.assertIn('Dataset 1', dataset_names)
        self.assertIn('Dataset 2', dataset_names)
        self.assertNotIn('Other Dataset', dataset_names)
    
    def test_get_dataset_details(self):
        """
        Test: Given an existing dataset, when I request dataset details,
        then I get the dataset with its cases
        """
        # Create dataset with cases
        dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset",
            description="A test dataset"
        )
        
        case1 = EvaluationCase.objects.create(
            dataset=dataset,
            input_text="Test input 1",
            expected_output="Test output 1"
        )
        case2 = EvaluationCase.objects.create(
            dataset=dataset,
            input_text="Test input 2",
            expected_output="Test output 2"
        )
        
        # This test should initially fail because we haven't implemented the API yet
        url = f'/api/evaluations/datasets/{dataset.id}/'
        
        response = self.client.get(url)
        
        # Expecting 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Verify response data
        response_data = response.json()
        self.assertEqual(response_data['name'], 'Test Dataset')
        self.assertEqual(response_data['description'], 'A test dataset')
        self.assertEqual(len(response_data['cases']), 2)
        
        # Verify cases are included
        case_inputs = [c['input_text'] for c in response_data['cases']]
        self.assertIn('Test input 1', case_inputs)
        self.assertIn('Test input 2', case_inputs)
    
    def test_import_evaluation_cases_with_parameters(self):
        """
        Test: Import evaluation cases using parameter-based format
        """
        # Create a prompt lab with a template that has parameters
        prompt_lab = PromptLab.objects.create(
            name="Customer Service Bot",
            description="Test prompt lab with parameters"
        )
        
        # Create a system prompt with parameter placeholders
        system_prompt = SystemPrompt.objects.create(
            prompt_lab=prompt_lab,
            content="You are a customer service assistant helping {{user_name}} with their {{issue_type}} regarding {{product}}. Please respond professionally.",
            version=1,
            is_active=True
        )
        
        # Create evaluation dataset
        dataset = EvaluationDataset.objects.create(
            prompt_lab=prompt_lab,
            name="Parameter-based Dataset"
        )
        
        # Sample JSONL content with parameter-based format
        jsonl_content = """{"parameters": {"user_name": "John Smith", "issue_type": "return policy", "product": "laptop"}, "expected_output": "Hi John Smith, our return policy allows returns within 30 days of purchase for laptops."}
{"parameters": {"user_name": "Sarah Johnson", "issue_type": "order tracking", "order_id": "ORD-12345"}, "expected_output": "Hello Sarah Johnson, you can track order ORD-12345 using the link in your confirmation email."}
{"parameters": {"user_name": "Mike Chen", "issue_type": "cancellation", "product": "smartphone"}, "expected_output": "Hi Mike Chen, I can help you cancel your smartphone order within 2 hours of placement."}"""
        
        url = f'/api/evaluations/datasets/{dataset.id}/import/'
        
        # Simulate file upload
        from django.core.files.uploadedfile import SimpleUploadedFile
        uploaded_file = SimpleUploadedFile(
            "test_cases.jsonl",
            jsonl_content.encode('utf-8'),
            content_type="application/json"
        )
        
        response = self.client.post(url, {'file': uploaded_file}, format='multipart')
        
        # Should get 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check response data
        response_data = response.json()
        imported_cases = response_data.get('imported_count', 0)
        
        # Check that 3 cases were imported
        self.assertEqual(imported_cases, 3)
        
        # Verify cases were actually created in database
        cases = EvaluationCase.objects.filter(dataset=dataset)
        self.assertEqual(cases.count(), 3)
        
        # Verify parameter substitution worked correctly
        case_1 = cases.filter(context__user_name="John Smith").first()
        self.assertIsNotNone(case_1)
        self.assertIn("John Smith", case_1.input_text)
        self.assertIn("return policy", case_1.input_text)
        self.assertIn("laptop", case_1.input_text)
        
        # Verify parameters are stored in context
        self.assertEqual(case_1.context['user_name'], "John Smith")
        self.assertEqual(case_1.context['issue_type'], "return policy")
        self.assertEqual(case_1.context['product'], "laptop")
        
        # Test case without active prompt (fallback behavior)
        system_prompt.is_active = False
        system_prompt.save()
        
        # Create another dataset
        dataset_2 = EvaluationDataset.objects.create(
            prompt_lab=prompt_lab,
            name="Fallback Dataset"
        )
        
        fallback_content = """{"parameters": {"user_name": "Test User", "issue": "general inquiry"}, "expected_output": "Thank you for your inquiry."}"""
        
        uploaded_file_2 = SimpleUploadedFile(
            "fallback_cases.jsonl",
            fallback_content.encode('utf-8'),
            content_type="application/json"
        )
        
        url_2 = f'/api/evaluations/datasets/{dataset_2.id}/import/'
        response_2 = self.client.post(url_2, {'file': uploaded_file_2}, format='multipart')
        
        self.assertEqual(response_2.status_code, 200)
        
        # Verify fallback case creation
        fallback_case = EvaluationCase.objects.filter(dataset=dataset_2).first()
        self.assertIsNotNone(fallback_case)
        self.assertIn("User Name: Test User", fallback_case.input_text)
        self.assertIn("Issue: general inquiry", fallback_case.input_text)