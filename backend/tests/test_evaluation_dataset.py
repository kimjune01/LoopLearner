"""
Tests for Story 1: Create Evaluation Dataset
Following TDD principles - these tests define the expected behavior.
"""
import json
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from core.models import Session, SystemPrompt, EvaluationDataset, EvaluationCase


class EvaluationDatasetStoryTests(TestCase):
    """Test Story 1: As a user, I can create a simple evaluation dataset to test my prompts"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.session = Session.objects.create(
            name="Test Session",
            description="A test session for evaluation"
        )
        self.prompt = SystemPrompt.objects.create(
            session=self.session,
            content="You are a helpful assistant.",
            version=1,
            is_active=True
        )
    
    def test_create_evaluation_dataset(self):
        """
        Test: Given a session with a prompt, when I create an evaluation dataset,
        then the dataset is saved with proper structure
        """
        # This test should initially fail because we haven't implemented the API yet
        url = '/api/evaluations/datasets/'
        data = {
            'session_id': str(self.session.id),
            'name': 'Customer Support Evaluation',
            'description': 'Test cases for customer support responses'
        }
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        
        # Expecting 201 Created
        self.assertEqual(response.status_code, 201)
        
        # Verify dataset was created
        datasets = EvaluationDataset.objects.filter(session=self.session)
        self.assertEqual(datasets.count(), 1)
        
        dataset = datasets.first()
        self.assertEqual(dataset.name, 'Customer Support Evaluation')
        self.assertEqual(dataset.description, 'Test cases for customer support responses')
        self.assertEqual(dataset.session, self.session)
        
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
            session=self.session,
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
            session=self.session,
            name="Imported Dataset"
        )
        
        # Sample JSONL content (3 test cases)
        jsonl_content = """{"input": "What is your return policy?", "expected": "We accept returns within 30 days.", "context": {"type": "policy"}}
{"input": "How do I track my order?", "expected": "You can track your order using the tracking number sent via email.", "context": {"type": "tracking"}}
{"input": "Can I cancel my order?", "expected": "Orders can be cancelled within 2 hours of placement.", "context": {"type": "cancellation"}}"""
        
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
        
        # Verify first case
        first_case = cases.filter(input_text="What is your return policy?").first()
        self.assertIsNotNone(first_case)
        self.assertEqual(first_case.expected_output, "We accept returns within 30 days.")
        self.assertEqual(first_case.context['type'], 'policy')
        
        # Verify response data
        response_data = response.json()
        self.assertEqual(response_data['imported_count'], 3)
        self.assertEqual(response_data['dataset_id'], dataset.id)
    
    def test_list_datasets_for_session(self):
        """
        Test: Given multiple datasets, when I request datasets for a session,
        then only datasets for that session are returned
        """
        # Create datasets for our session
        dataset1 = EvaluationDataset.objects.create(
            session=self.session,
            name="Dataset 1"
        )
        dataset2 = EvaluationDataset.objects.create(
            session=self.session,
            name="Dataset 2"
        )
        
        # Create dataset for different session
        other_session = Session.objects.create(name="Other Session")
        other_dataset = EvaluationDataset.objects.create(
            session=other_session,
            name="Other Dataset"
        )
        
        # This test should initially fail because we haven't implemented the API yet
        url = f'/api/evaluations/datasets/?session_id={self.session.id}'
        
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
            session=self.session,
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