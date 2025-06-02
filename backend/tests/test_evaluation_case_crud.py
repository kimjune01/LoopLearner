"""
Comprehensive CRUD tests for evaluation cases
Tests all Create, Read, Update, Delete operations for evaluation cases
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from core.models import PromptLab, EvaluationDataset, EvaluationCase, SystemPrompt


class EvaluationCaseCRUDTestCase(TestCase):
    """Test CRUD operations for evaluation cases"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test prompt lab
        self.prompt_lab = PromptLab.objects.create(
            name="Test Email Assistant",
            description="Test prompt lab for case CRUD tests"
        )
        
        # Create system prompt
        self.system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="You are an email assistant. Handle: {{EMAIL_CONTENT}} for {{RECIPIENT_INFO}}",
            version=1,
            is_active=True
        )
        
        # Create test dataset
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset",
            description="Dataset for CRUD testing",
            parameters=["EMAIL_CONTENT", "RECIPIENT_INFO"]
        )
        
        # Create initial test case
        self.test_case = EvaluationCase.objects.create(
            dataset=self.dataset,
            input_text="Test email input",
            expected_output="Expected response",
            context={
                "EMAIL_CONTENT": "Hello team",
                "RECIPIENT_INFO": "John Doe"
            }
        )
    
    def test_create_case_via_api(self):
        """Test creating a new case via POST API"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/'
        data = {
            'input_text': 'New test input',
            'expected_output': 'New expected output',
            'context': {
                'EMAIL_CONTENT': 'Test email content',
                'RECIPIENT_INFO': 'Jane Smith'
            }
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        
        # Verify response structure
        self.assertIn('id', response_data)
        self.assertEqual(response_data['input_text'], data['input_text'])
        self.assertEqual(response_data['expected_output'], data['expected_output'])
        self.assertEqual(response_data['context'], data['context'])
        self.assertEqual(response_data['dataset_id'], self.dataset.id)
        
        # Verify case was created in database
        created_case = EvaluationCase.objects.get(id=response_data['id'])
        self.assertEqual(created_case.input_text, data['input_text'])
        self.assertEqual(created_case.expected_output, data['expected_output'])
        self.assertEqual(created_case.context, data['context'])
    
    def test_create_case_missing_required_fields(self):
        """Test creating case with missing required fields"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/'
        
        # Test missing input_text
        response = self.client.post(
            url,
            data=json.dumps({'expected_output': 'Test output'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('input_text and expected_output are required', response.json()['error'])
        
        # Test missing expected_output
        response = self.client.post(
            url,
            data=json.dumps({'input_text': 'Test input'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('input_text and expected_output are required', response.json()['error'])
    
    def test_create_case_invalid_json(self):
        """Test creating case with invalid JSON"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/'
        
        response = self.client.post(
            url,
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid JSON', response.json()['error'])
    
    def test_read_all_cases(self):
        """Test reading all cases via GET API"""
        # Create additional test cases
        case2 = EvaluationCase.objects.create(
            dataset=self.dataset,
            input_text="Second test input",
            expected_output="Second expected output",
            context={"EMAIL_CONTENT": "Second email"}
        )
        
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Verify response structure
        self.assertIn('cases', response_data)
        self.assertIn('count', response_data)
        self.assertEqual(response_data['dataset_id'], self.dataset.id)
        self.assertEqual(response_data['count'], 2)
        
        # Verify cases data
        cases = response_data['cases']
        self.assertEqual(len(cases), 2)
        
        # Check first case
        case1_data = next(c for c in cases if c['id'] == self.test_case.id)
        self.assertEqual(case1_data['input_text'], self.test_case.input_text)
        self.assertEqual(case1_data['expected_output'], self.test_case.expected_output)
        self.assertEqual(case1_data['context'], self.test_case.context)
        
        # Check second case
        case2_data = next(c for c in cases if c['id'] == case2.id)
        self.assertEqual(case2_data['input_text'], case2.input_text)
        self.assertEqual(case2_data['expected_output'], case2.expected_output)
        self.assertEqual(case2_data['context'], case2.context)
    
    def test_read_single_case(self):
        """Test reading a single case via GET API"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/{self.test_case.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Verify response data
        self.assertEqual(response_data['id'], self.test_case.id)
        self.assertEqual(response_data['input_text'], self.test_case.input_text)
        self.assertEqual(response_data['expected_output'], self.test_case.expected_output)
        self.assertEqual(response_data['context'], self.test_case.context)
        self.assertEqual(response_data['dataset_id'], self.dataset.id)
        self.assertIn('created_at', response_data)
    
    def test_read_nonexistent_case(self):
        """Test reading a case that doesn't exist"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/99999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_read_case_wrong_dataset(self):
        """Test reading a case with wrong dataset ID"""
        # Create another dataset
        other_dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Other Dataset",
            description="Another dataset"
        )
        
        # Try to access case from wrong dataset
        url = f'/api/evaluations/datasets/{other_dataset.id}/cases/{self.test_case.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_update_case_expected_output(self):
        """Test updating a case's expected output"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/{self.test_case.id}/'
        update_data = {
            'expected_output': 'Updated expected output'
        }
        
        response = self.client.put(
            url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Verify response
        self.assertEqual(response_data['expected_output'], update_data['expected_output'])
        self.assertEqual(response_data['input_text'], self.test_case.input_text)  # Unchanged
        self.assertEqual(response_data['context'], self.test_case.context)  # Unchanged
        
        # Verify database update
        updated_case = EvaluationCase.objects.get(id=self.test_case.id)
        self.assertEqual(updated_case.expected_output, update_data['expected_output'])
    
    def test_update_case_input_text(self):
        """Test updating a case's input text"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/{self.test_case.id}/'
        update_data = {
            'input_text': 'Updated input text'
        }
        
        response = self.client.put(
            url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Verify response
        self.assertEqual(response_data['input_text'], update_data['input_text'])
        self.assertEqual(response_data['expected_output'], self.test_case.expected_output)  # Unchanged
        
        # Verify database update
        updated_case = EvaluationCase.objects.get(id=self.test_case.id)
        self.assertEqual(updated_case.input_text, update_data['input_text'])
    
    def test_update_case_context(self):
        """Test updating a case's context parameters"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/{self.test_case.id}/'
        update_data = {
            'context': {
                'EMAIL_CONTENT': 'Updated email content',
                'RECIPIENT_INFO': 'Updated recipient',
                'NEW_PARAM': 'New parameter value'
            }
        }
        
        response = self.client.put(
            url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Verify response
        self.assertEqual(response_data['context'], update_data['context'])
        
        # Verify database update
        updated_case = EvaluationCase.objects.get(id=self.test_case.id)
        self.assertEqual(updated_case.context, update_data['context'])
    
    def test_update_case_all_fields(self):
        """Test updating all case fields at once"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/{self.test_case.id}/'
        update_data = {
            'input_text': 'Completely new input',
            'expected_output': 'Completely new output',
            'context': {
                'EMAIL_CONTENT': 'New email content',
                'RECIPIENT_INFO': 'New recipient info'
            }
        }
        
        response = self.client.put(
            url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Verify all fields updated
        self.assertEqual(response_data['input_text'], update_data['input_text'])
        self.assertEqual(response_data['expected_output'], update_data['expected_output'])
        self.assertEqual(response_data['context'], update_data['context'])
        
        # Verify database update
        updated_case = EvaluationCase.objects.get(id=self.test_case.id)
        self.assertEqual(updated_case.input_text, update_data['input_text'])
        self.assertEqual(updated_case.expected_output, update_data['expected_output'])
        self.assertEqual(updated_case.context, update_data['context'])
    
    def test_update_case_partial_fields(self):
        """Test updating only some fields leaves others unchanged"""
        original_input = self.test_case.input_text
        original_context = self.test_case.context
        
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/{self.test_case.id}/'
        update_data = {
            'expected_output': 'Only output changed'
        }
        
        response = self.client.put(
            url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify database - only expected_output changed
        updated_case = EvaluationCase.objects.get(id=self.test_case.id)
        self.assertEqual(updated_case.expected_output, update_data['expected_output'])
        self.assertEqual(updated_case.input_text, original_input)  # Unchanged
        self.assertEqual(updated_case.context, original_context)  # Unchanged
    
    def test_update_case_invalid_json(self):
        """Test updating case with invalid JSON"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/{self.test_case.id}/'
        
        response = self.client.put(
            url,
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid JSON', response.json()['error'])
    
    def test_update_nonexistent_case(self):
        """Test updating a case that doesn't exist"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/99999/'
        update_data = {'expected_output': 'New output'}
        
        response = self.client.put(
            url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_delete_case(self):
        """Test deleting a case"""
        case_id = self.test_case.id
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/{case_id}/'
        
        # Verify case exists before deletion
        self.assertTrue(EvaluationCase.objects.filter(id=case_id).exists())
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['message'], 'Case deleted successfully')
        
        # Verify case no longer exists
        self.assertFalse(EvaluationCase.objects.filter(id=case_id).exists())
    
    def test_delete_nonexistent_case(self):
        """Test deleting a case that doesn't exist"""
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/99999/'
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)
    
    def test_delete_case_wrong_dataset(self):
        """Test deleting a case with wrong dataset ID"""
        # Create another dataset
        other_dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Other Dataset",
            description="Another dataset"
        )
        
        # Try to delete case from wrong dataset
        url = f'/api/evaluations/datasets/{other_dataset.id}/cases/{self.test_case.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 404)
        
        # Verify case still exists
        self.assertTrue(EvaluationCase.objects.filter(id=self.test_case.id).exists())
    
    def test_crud_with_metadata_parameters(self):
        """Test CRUD operations with cases containing metadata parameters"""
        # Create case with metadata parameters (like promoted cases)
        case_with_metadata = EvaluationCase.objects.create(
            dataset=self.dataset,
            input_text="Promoted case input",
            expected_output="Promoted case output",
            context={
                "EMAIL_CONTENT": "Test email",
                "RECIPIENT_INFO": "Test recipient",
                "promoted_from_draft": 123,
                "selected_variation_index": 1,
                "used_custom_output": True
            }
        )
        
        # Test reading case with metadata
        url = f'/api/evaluations/datasets/{self.dataset.id}/cases/{case_with_metadata.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Verify metadata parameters are preserved
        context = response_data['context']
        self.assertEqual(context['promoted_from_draft'], 123)
        self.assertEqual(context['selected_variation_index'], 1)
        self.assertEqual(context['used_custom_output'], True)
        
        # Test updating case with metadata
        update_data = {
            'expected_output': 'Updated output with metadata',
            'context': {
                **context,
                'EMAIL_CONTENT': 'Updated email content'
            }
        }
        
        response = self.client.put(
            url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify metadata parameters are still preserved after update
        updated_case = EvaluationCase.objects.get(id=case_with_metadata.id)
        self.assertEqual(updated_case.context['promoted_from_draft'], 123)
        self.assertEqual(updated_case.context['selected_variation_index'], 1)
        self.assertEqual(updated_case.context['used_custom_output'], True)
        self.assertEqual(updated_case.context['EMAIL_CONTENT'], 'Updated email content')
    
    def test_case_count_consistency(self):
        """Test that case count remains consistent during CRUD operations"""
        # Initial count
        initial_count = EvaluationCase.objects.filter(dataset=self.dataset).count()
        self.assertEqual(initial_count, 1)  # Our setUp case
        
        # Create new case
        create_url = f'/api/evaluations/datasets/{self.dataset.id}/cases/'
        create_data = {
            'input_text': 'Count test input',
            'expected_output': 'Count test output'
        }
        
        response = self.client.post(
            create_url,
            data=json.dumps(create_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        new_case_id = response.json()['id']
        
        # Verify count increased
        self.assertEqual(EvaluationCase.objects.filter(dataset=self.dataset).count(), 2)
        
        # Update case (shouldn't change count)
        update_url = f'/api/evaluations/datasets/{self.dataset.id}/cases/{new_case_id}/'
        update_data = {'expected_output': 'Updated output'}
        
        response = self.client.put(
            update_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify count unchanged
        self.assertEqual(EvaluationCase.objects.filter(dataset=self.dataset).count(), 2)
        
        # Delete case
        response = self.client.delete(update_url)
        self.assertEqual(response.status_code, 200)
        
        # Verify count decreased
        self.assertEqual(EvaluationCase.objects.filter(dataset=self.dataset).count(), 1)
    
    def test_case_isolation_between_datasets(self):
        """Test that cases are properly isolated between datasets"""
        # Create second dataset
        dataset2 = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Second Dataset",
            description="Second dataset for isolation testing"
        )
        
        # Create case in second dataset
        case2 = EvaluationCase.objects.create(
            dataset=dataset2,
            input_text="Dataset 2 input",
            expected_output="Dataset 2 output"
        )
        
        # Test that dataset 1 cases don't include dataset 2 cases
        url1 = f'/api/evaluations/datasets/{self.dataset.id}/cases/'
        response1 = self.client.get(url1)
        self.assertEqual(response1.status_code, 200)
        
        cases1 = response1.json()['cases']
        case1_ids = [c['id'] for c in cases1]
        self.assertIn(self.test_case.id, case1_ids)
        self.assertNotIn(case2.id, case1_ids)
        
        # Test that dataset 2 cases don't include dataset 1 cases
        url2 = f'/api/evaluations/datasets/{dataset2.id}/cases/'
        response2 = self.client.get(url2)
        self.assertEqual(response2.status_code, 200)
        
        cases2 = response2.json()['cases']
        case2_ids = [c['id'] for c in cases2]
        self.assertIn(case2.id, case2_ids)
        self.assertNotIn(self.test_case.id, case2_ids)