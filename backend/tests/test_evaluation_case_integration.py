"""
Integration tests for evaluation case CRUD workflow
Tests the complete end-to-end flow including the frontend fixes
"""
import json
from django.test import TestCase, Client
from core.models import PromptLab, EvaluationDataset, EvaluationCase, SystemPrompt


class EvaluationCaseIntegrationTestCase(TestCase):
    """Integration tests for case CRUD workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test prompt lab
        self.prompt_lab = PromptLab.objects.create(
            name="Integration Test Lab",
            description="Integration testing prompt lab"
        )
        
        # Create system prompt with parameters
        self.system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="Handle {{EMAIL_CONTENT}} for {{RECIPIENT_INFO}} from {{SENDER_INFO}}",
            version=1,
            is_active=True
        )
        
        # Create test dataset
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Integration Test Dataset",
            description="Dataset for integration testing",
            parameters=["EMAIL_CONTENT", "RECIPIENT_INFO", "SENDER_INFO"]
        )
    
    def test_full_case_lifecycle_without_metadata(self):
        """Test complete case lifecycle: create -> read -> update -> delete"""
        
        # 1. CREATE: Create a new case
        create_data = {
            'input_text': 'Integration test input',
            'expected_output': 'Integration test output',
            'context': {
                'EMAIL_CONTENT': 'Test email content',
                'RECIPIENT_INFO': 'Test recipient',
                'SENDER_INFO': 'Test sender'
            }
        }
        
        create_response = self.client.post(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/',
            data=json.dumps(create_data),
            content_type='application/json'
        )
        
        self.assertEqual(create_response.status_code, 201)
        created_case = create_response.json()
        case_id = created_case['id']
        
        # Verify created case has expected data
        self.assertEqual(created_case['input_text'], create_data['input_text'])
        self.assertEqual(created_case['expected_output'], create_data['expected_output'])
        self.assertEqual(created_case['context'], create_data['context'])
        
        # 2. READ: Retrieve the case
        read_response = self.client.get(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/{case_id}/'
        )
        
        self.assertEqual(read_response.status_code, 200)
        retrieved_case = read_response.json()
        
        # Verify retrieved case matches created case
        self.assertEqual(retrieved_case['id'], case_id)
        self.assertEqual(retrieved_case['input_text'], create_data['input_text'])
        self.assertEqual(retrieved_case['expected_output'], create_data['expected_output'])
        self.assertEqual(retrieved_case['context'], create_data['context'])
        
        # 3. UPDATE: Update the case (simulating frontend edit)
        update_data = {
            'expected_output': 'Updated integration test output',
            'context': {
                **create_data['context'],
                'EMAIL_CONTENT': 'Updated email content'
            }
        }
        
        update_response = self.client.put(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/{case_id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(update_response.status_code, 200)
        updated_case = update_response.json()
        
        # Verify updates were applied
        self.assertEqual(updated_case['expected_output'], update_data['expected_output'])
        self.assertEqual(updated_case['context'], update_data['context'])
        self.assertEqual(updated_case['input_text'], create_data['input_text'])  # Unchanged
        
        # 4. READ: Verify update persisted
        verify_response = self.client.get(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/{case_id}/'
        )
        
        self.assertEqual(verify_response.status_code, 200)
        verified_case = verify_response.json()
        self.assertEqual(verified_case['expected_output'], update_data['expected_output'])
        self.assertEqual(verified_case['context'], update_data['context'])
        
        # 5. DELETE: Delete the case
        delete_response = self.client.delete(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/{case_id}/'
        )
        
        self.assertEqual(delete_response.status_code, 200)
        delete_result = delete_response.json()
        self.assertEqual(delete_result['message'], 'Case deleted successfully')
        
        # 6. READ: Verify case is gone
        final_response = self.client.get(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/{case_id}/'
        )
        
        self.assertEqual(final_response.status_code, 404)
        
        # Verify case no longer exists in database
        self.assertFalse(EvaluationCase.objects.filter(id=case_id).exists())
    
    def test_promoted_case_parameter_handling(self):
        """Test case with metadata parameters (like promoted from draft)"""
        
        # Create a case with metadata parameters (simulating promoted case)
        case_data = {
            'input_text': 'Promoted case input',
            'expected_output': 'Promoted case output',
            'context': {
                'EMAIL_CONTENT': 'Test email',
                'RECIPIENT_INFO': 'Test recipient',
                'SENDER_INFO': 'Test sender',
                # Metadata parameters that shouldn't affect prompt compatibility
                'promoted_from_draft': 123,
                'selected_variation_index': 1,
                'used_custom_output': True
            }
        }
        
        create_response = self.client.post(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/',
            data=json.dumps(case_data),
            content_type='application/json'
        )
        
        self.assertEqual(create_response.status_code, 201)
        created_case = create_response.json()
        case_id = created_case['id']
        
        # Verify metadata parameters are preserved
        context = created_case['context']
        self.assertEqual(context['promoted_from_draft'], 123)
        self.assertEqual(context['selected_variation_index'], 1)
        self.assertEqual(context['used_custom_output'], True)
        
        # Test parameter filtering logic (simulating frontend comparison)
        metadata_params = ['promoted_from_draft', 'selected_variation_index', 'used_custom_output']
        case_params = [param for param in context.keys() if param not in metadata_params]
        case_params.sort()
        
        active_params = self.system_prompt.parameters.copy()
        active_params.sort()
        
        # These should match because metadata parameters are filtered out
        self.assertEqual(case_params, active_params)
        self.assertEqual(case_params, ['EMAIL_CONTENT', 'RECIPIENT_INFO', 'SENDER_INFO'])
        
        # Update the case while preserving metadata
        update_data = {
            'expected_output': 'Updated promoted case output',
            'context': {
                **context,
                'EMAIL_CONTENT': 'Updated email content'
            }
        }
        
        update_response = self.client.put(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/{case_id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(update_response.status_code, 200)
        updated_case = update_response.json()
        
        # Verify metadata parameters are still preserved after update
        updated_context = updated_case['context']
        self.assertEqual(updated_context['promoted_from_draft'], 123)
        self.assertEqual(updated_context['selected_variation_index'], 1)
        self.assertEqual(updated_context['used_custom_output'], True)
        self.assertEqual(updated_context['EMAIL_CONTENT'], 'Updated email content')
    
    def test_bulk_operations(self):
        """Test bulk case operations"""
        
        # Create multiple cases
        case_ids = []
        for i in range(3):
            case_data = {
                'input_text': f'Bulk test case {i+1} input',
                'expected_output': f'Bulk test case {i+1} output',
                'context': {
                    'EMAIL_CONTENT': f'Email content {i+1}',
                    'RECIPIENT_INFO': f'Recipient {i+1}',
                    'SENDER_INFO': f'Sender {i+1}'
                }
            }
            
            response = self.client.post(
                f'/api/evaluations/datasets/{self.dataset.id}/cases/',
                data=json.dumps(case_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 201)
            case_ids.append(response.json()['id'])
        
        # Read all cases
        list_response = self.client.get(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/'
        )
        
        self.assertEqual(list_response.status_code, 200)
        cases_data = list_response.json()
        
        self.assertEqual(cases_data['count'], 3)
        self.assertEqual(len(cases_data['cases']), 3)
        
        # Verify all created cases are in the list
        retrieved_ids = [case['id'] for case in cases_data['cases']]
        for case_id in case_ids:
            self.assertIn(case_id, retrieved_ids)
        
        # Bulk delete (simulating frontend bulk delete)
        for case_id in case_ids:
            delete_response = self.client.delete(
                f'/api/evaluations/datasets/{self.dataset.id}/cases/{case_id}/'
            )
            self.assertEqual(delete_response.status_code, 200)
        
        # Verify all cases are deleted
        final_list_response = self.client.get(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/'
        )
        
        self.assertEqual(final_list_response.status_code, 200)
        final_cases = final_list_response.json()
        self.assertEqual(final_cases['count'], 0)
        self.assertEqual(len(final_cases['cases']), 0)
    
    def test_error_handling_integration(self):
        """Test error handling in various scenarios"""
        
        # Test creating case with invalid data
        invalid_data = {'input_text': ''}  # Missing required field
        
        create_response = self.client.post(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(create_response.status_code, 400)
        self.assertIn('input_text and expected_output are required', create_response.json()['error'])
        
        # Test updating nonexistent case
        update_response = self.client.put(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/99999/',
            data=json.dumps({'expected_output': 'test'}),
            content_type='application/json'
        )
        
        self.assertEqual(update_response.status_code, 404)
        
        # Test deleting nonexistent case
        delete_response = self.client.delete(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/99999/'
        )
        
        self.assertEqual(delete_response.status_code, 404)
        
        # Test invalid JSON
        invalid_json_response = self.client.post(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(invalid_json_response.status_code, 400)
        self.assertIn('Invalid JSON', invalid_json_response.json()['error'])
    
    def test_dataset_isolation(self):
        """Test that cases are properly isolated between datasets"""
        
        # Create second dataset
        dataset2 = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Second Integration Dataset",
            description="Second dataset for isolation testing"
        )
        
        # Create case in first dataset
        case1_data = {
            'input_text': 'Dataset 1 case',
            'expected_output': 'Dataset 1 output',
            'context': {'param': 'value1'}
        }
        
        response1 = self.client.post(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/',
            data=json.dumps(case1_data),
            content_type='application/json'
        )
        
        self.assertEqual(response1.status_code, 201)
        case1_id = response1.json()['id']
        
        # Create case in second dataset
        case2_data = {
            'input_text': 'Dataset 2 case',
            'expected_output': 'Dataset 2 output',
            'context': {'param': 'value2'}
        }
        
        response2 = self.client.post(
            f'/api/evaluations/datasets/{dataset2.id}/cases/',
            data=json.dumps(case2_data),
            content_type='application/json'
        )
        
        self.assertEqual(response2.status_code, 201)
        case2_id = response2.json()['id']
        
        # Verify cases are isolated
        list1_response = self.client.get(
            f'/api/evaluations/datasets/{self.dataset.id}/cases/'
        )
        list2_response = self.client.get(
            f'/api/evaluations/datasets/{dataset2.id}/cases/'
        )
        
        self.assertEqual(list1_response.status_code, 200)
        self.assertEqual(list2_response.status_code, 200)
        
        list1_data = list1_response.json()
        list2_data = list2_response.json()
        
        # Each dataset should have only its own case
        self.assertEqual(list1_data['count'], 1)
        self.assertEqual(list2_data['count'], 1)
        
        case1_ids = [case['id'] for case in list1_data['cases']]
        case2_ids = [case['id'] for case in list2_data['cases']]
        
        self.assertIn(case1_id, case1_ids)
        self.assertNotIn(case1_id, case2_ids)
        self.assertIn(case2_id, case2_ids)
        self.assertNotIn(case2_id, case1_ids)
        
        # Test cross-dataset access fails
        cross_access_response = self.client.get(
            f'/api/evaluations/datasets/{dataset2.id}/cases/{case1_id}/'
        )
        
        self.assertEqual(cross_access_response.status_code, 404)