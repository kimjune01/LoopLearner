"""
End-to-end integration tests for human-in-the-loop dataset generation.
Tests the complete workflow from  creation to dataset generation with output selection.
"""
import json
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, AsyncMock
from core.models import PromptLab, SystemPrompt, EvaluationDataset, EvaluationCase
from app.services.evaluation_case_generator import EvaluationCaseGenerator


class HumanInLoopIntegrationTests(TransactionTestCase):
    """Integration tests for complete human-in-the-loop workflow"""
    
    def setUp(self):
        """Set up test data for integration tests"""
        self.client = APIClient()
        
        # Create test 
        self.prompt_lab = PromptLab.objects.create(
            name='Integration Test PromptLab',
            description='Testing complete human-in-the-loop workflow'
        )
        
        # Create system prompt with parameters
        self.prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content='Hello {{customer_name}}, I understand you have a {{issue_type}}. How can I help you today?',
            version=1,
            is_active=True
        )
        self.prompt.extract_parameters()  # Extract customer_name and issue_type
        
        # Create evaluation dataset
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name='Human-in-Loop Integration Dataset',
            description='Testing dataset creation with human selection',
            parameters=['customer_name', 'issue_type']
        )
    
    def test_full_human_in_loop_flow(self):
        """Test complete flow from generation to dataset creation"""
        # Step 1: Generate cases with multiple output variations
        generate_url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        generate_data = {
            'use_session_prompt': True,
            'count': 2,
            'generate_output_variations': True,
            'variations_count': 3
        }
        
        with patch('app.services.evaluation_case_generator.EvaluationCaseGenerator.generate_cases_preview_with_variations') as mock_generate:
            # Mock the generator to return predictable test data
            mock_generate.return_value = [
                {
                    'preview_id': 'test-case-1',
                    'input_text': 'Hello John Smith, I understand you have a billing issue. How can I help you today?',
                    'parameters': {'customer_name': 'John Smith', 'issue_type': 'billing issue'},
                    'prompt_content': self.prompt.content,
                    'output_variations': [
                        {'index': 0, 'text': 'I\'ll be happy to help you with your billing concern. Let me review your account.', 'style': 'formal'},
                        {'index': 1, 'text': 'Hi John! I\'d love to help you sort out this billing issue quickly.', 'style': 'friendly'},
                        {'index': 2, 'text': 'Thank you for contacting us about your billing issue. Let me provide detailed assistance and walk you through the resolution process.', 'style': 'detailed'}
                    ],
                    'selected_output_index': None,
                    'custom_output': None
                },
                {
                    'preview_id': 'test-case-2',
                    'input_text': 'Hello Jane Doe, I understand you have a shipping delay. How can I help you today?',
                    'parameters': {'customer_name': 'Jane Doe', 'issue_type': 'shipping delay'},
                    'prompt_content': self.prompt.content,
                    'output_variations': [
                        {'index': 0, 'text': 'I understand your concern about the shipping delay. Let me track your order immediately.', 'style': 'formal'},
                        {'index': 1, 'text': 'Oh no! Sorry about the shipping delay. Let me check what\'s going on with your order.', 'style': 'friendly'},
                        {'index': 2, 'text': 'I apologize for the shipping delay you\'re experiencing. Let me provide you with detailed tracking information and explain the next steps.', 'style': 'detailed'}
                    ],
                    'selected_output_index': None,
                    'custom_output': None
                }
            ]
            
            # When: Generating cases
            response = self.client.post(generate_url, generate_data, format='json')
            
            # Then: Should return cases with output variations
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()
            
            self.assertIn('previews', response_data)
            self.assertEqual(len(response_data['previews']), 2)
            
            # Verify each preview has output variations
            for preview in response_data['previews']:
                self.assertIn('output_variations', preview)
                self.assertEqual(len(preview['output_variations']), 3)
                self.assertIn('selected_output_index', preview)
                self.assertIn('custom_output', preview)
        
        # Step 2: User selects outputs (mix of AI-generated and custom)
        add_cases_url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        add_cases_data = {
            'cases': [
                {
                    'preview_id': 'test-case-1',
                    'input_text': 'Hello John Smith, I understand you have a billing issue. How can I help you today?',
                    'parameters': {'customer_name': 'John Smith', 'issue_type': 'billing issue'},
                    'selected_output_index': 1,  # User selects friendly option
                    'output_variations': [
                        {'index': 0, 'text': 'I\'ll be happy to help you with your billing concern. Let me review your account.', 'style': 'formal'},
                        {'index': 1, 'text': 'Hi John! I\'d love to help you sort out this billing issue quickly.', 'style': 'friendly'},
                        {'index': 2, 'text': 'Thank you for contacting us about your billing issue. Let me provide detailed assistance and walk you through the resolution process.', 'style': 'detailed'}
                    ]
                },
                {
                    'preview_id': 'test-case-2',
                    'input_text': 'Hello Jane Doe, I understand you have a shipping delay. How can I help you today?',
                    'parameters': {'customer_name': 'Jane Doe', 'issue_type': 'shipping delay'},
                    'custom_output': 'I sincerely apologize for the shipping delay. This is unacceptable and I will personally ensure your order is expedited. Let me contact our logistics team immediately.',
                    'output_variations': [
                        {'index': 0, 'text': 'I understand your concern about the shipping delay. Let me track your order immediately.', 'style': 'formal'},
                        {'index': 1, 'text': 'Oh no! Sorry about the shipping delay. Let me check what\'s going on with your order.', 'style': 'friendly'},
                        {'index': 2, 'text': 'I apologize for the shipping delay you\'re experiencing. Let me provide you with detailed tracking information and explain the next steps.', 'style': 'detailed'}
                    ]
                }
            ]
        }
        
        # When: Adding selected cases
        response = self.client.post(add_cases_url, add_cases_data, format='json')
        
        # Then: Cases should be added to dataset
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertEqual(response_data['added_count'], 2)
        self.assertIn('added_cases', response_data)
        self.assertEqual(len(response_data['added_cases']), 2)
        
        # Verify first case uses selected AI output
        case1 = response_data['added_cases'][0]
        self.assertEqual(case1['expected_output'], 'Hi John! I\'d love to help you sort out this billing issue quickly.')
        self.assertEqual(case1['input_text'], 'Hello John Smith, I understand you have a billing issue. How can I help you today?')
        
        # Verify second case uses custom output
        case2 = response_data['added_cases'][1]
        self.assertEqual(case2['expected_output'], 'I sincerely apologize for the shipping delay. This is unacceptable and I will personally ensure your order is expedited. Let me contact our logistics team immediately.')
        
        # Step 3: Verify cases are persisted in database
        dataset_cases = EvaluationCase.objects.filter(dataset=self.dataset)
        self.assertEqual(dataset_cases.count(), 2)
        
        # Verify case data in database
        db_case1 = dataset_cases.get(context__customer_name='John Smith')
        self.assertEqual(db_case1.expected_output, 'Hi John! I\'d love to help you sort out this billing issue quickly.')
        self.assertEqual(db_case1.context['issue_type'], 'billing issue')
        
        db_case2 = dataset_cases.get(context__customer_name='Jane Doe')
        self.assertEqual(db_case2.expected_output, 'I sincerely apologize for the shipping delay. This is unacceptable and I will personally ensure your order is expedited. Let me contact our logistics team immediately.')
        self.assertEqual(db_case2.context['issue_type'], 'shipping delay')
    
    def test_mixed_selection_and_custom_outputs(self):
        """Test that users can mix AI-selected and custom outputs in the same batch"""
        # Generate test cases
        generate_url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        generate_data = {
            'use_session_prompt': True,
            'count': 3,
            'generate_output_variations': True
        }
        
        with patch('app.services.evaluation_case_generator.EvaluationCaseGenerator.generate_cases_preview_with_variations') as mock_generate:
            mock_generate.return_value = [
                {
                    'preview_id': f'mixed-case-{i}',
                    'input_text': f'Test input {i}',
                    'parameters': {'customer_name': f'User{i}', 'issue_type': 'test issue'},
                    'output_variations': [
                        {'index': 0, 'text': f'Formal response {i}', 'style': 'formal'},
                        {'index': 1, 'text': f'Friendly response {i}', 'style': 'friendly'},
                        {'index': 2, 'text': f'Detailed response {i}', 'style': 'detailed'}
                    ]
                } for i in range(3)
            ]
            
            self.client.post(generate_url, generate_data, format='json')
        
        # Add cases with mixed selection types
        add_cases_url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        add_cases_data = {
            'cases': [
                {
                    'preview_id': 'mixed-case-0',
                    'input_text': 'Test input 0',
                    'parameters': {'customer_name': 'User0', 'issue_type': 'test issue'},
                    'selected_output_index': 0,  # AI option
                    'output_variations': [
                        {'index': 0, 'text': 'Formal response 0', 'style': 'formal'},
                        {'index': 1, 'text': 'Friendly response 0', 'style': 'friendly'},
                        {'index': 2, 'text': 'Detailed response 0', 'style': 'detailed'}
                    ]
                },
                {
                    'preview_id': 'mixed-case-1',
                    'input_text': 'Test input 1',
                    'parameters': {'customer_name': 'User1', 'issue_type': 'test issue'},
                    'custom_output': 'My custom response for case 1',  # Custom option
                    'output_variations': []
                },
                {
                    'preview_id': 'mixed-case-2',
                    'input_text': 'Test input 2',
                    'parameters': {'customer_name': 'User2', 'issue_type': 'test issue'},
                    'selected_output_index': 2,  # AI option (different from case 0)
                    'output_variations': [
                        {'index': 0, 'text': 'Formal response 2', 'style': 'formal'},
                        {'index': 1, 'text': 'Friendly response 2', 'style': 'friendly'},
                        {'index': 2, 'text': 'Detailed response 2', 'style': 'detailed'}
                    ]
                }
            ]
        }
        
        response = self.client.post(add_cases_url, add_cases_data, format='json')
        
        # Verify mixed types are handled correctly
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        cases = response_data['added_cases']
        self.assertEqual(len(cases), 3)
        
        # Case 0: AI formal response
        self.assertEqual(cases[0]['expected_output'], 'Formal response 0')
        
        # Case 1: Custom response
        self.assertEqual(cases[1]['expected_output'], 'My custom response for case 1')
        
        # Case 2: AI detailed response
        self.assertEqual(cases[2]['expected_output'], 'Detailed response 2')
    
    def test_backward_compatibility_with_existing_workflow(self):
        """Test that existing single-output workflow still works"""
        # Test legacy generate-cases endpoint (without variations)
        generate_url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        generate_data = {
            'use_session_prompt': True,
            'count': 2,
            'generate_output_variations': False  # Explicitly disable variations
        }
        
        with patch('app.services.evaluation_case_generator.EvaluationCaseGenerator.generate_cases_preview') as mock_generate:
            mock_generate.return_value = [
                {
                    'preview_id': 'legacy-case-1',
                    'input_text': 'Legacy input 1',
                    'expected_output': 'Legacy output 1',
                    'parameters': {'customer_name': 'Legacy User', 'issue_type': 'legacy issue'},
                    'prompt_content': self.prompt.content
                }
            ]
            
            response = self.client.post(generate_url, generate_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()
            
            # Should use legacy format (single expected_output)
            preview = response_data['previews'][0]
            self.assertIn('expected_output', preview)
            self.assertNotIn('output_variations', preview)
        
        # Test legacy add-selected-cases endpoint (with preview_ids)
        add_cases_url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        legacy_data = {
            'preview_ids': ['legacy-case-1']
        }
        
        response = self.client.post(add_cases_url, legacy_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertEqual(response_data['added_count'], 1)
        
        # Verify case is in database
        legacy_case = EvaluationCase.objects.get(context__customer_name='Legacy User')
        self.assertEqual(legacy_case.expected_output, 'Legacy output 1')
    
    def test_validation_prevents_invalid_selections(self):
        """Test that API validation prevents invalid output selections"""
        add_cases_url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        
        # Test 1: Both selected_output_index and custom_output provided
        invalid_data1 = {
            'cases': [{
                'preview_id': 'test-id',
                'input_text': 'Test input',
                'parameters': {},
                'selected_output_index': 1,
                'custom_output': 'Custom text',
                'output_variations': []
            }]
        }
        
        response = self.client.post(add_cases_url, invalid_data1, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot specify both', response.json()['error'])
        
        # Test 2: Neither selected_output_index nor custom_output provided
        invalid_data2 = {
            'cases': [{
                'preview_id': 'test-id',
                'input_text': 'Test input',
                'parameters': {},
                'output_variations': []
            }]
        }
        
        response = self.client.post(add_cases_url, invalid_data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Must specify either', response.json()['error'])
        
        # Test 3: Invalid selected_output_index (out of range)
        invalid_data3 = {
            'cases': [{
                'preview_id': 'test-id',
                'input_text': 'Test input',
                'parameters': {},
                'selected_output_index': 5,  # Out of range
                'output_variations': [
                    {'index': 0, 'text': 'Option 1', 'style': 'formal'},
                    {'index': 1, 'text': 'Option 2', 'style': 'friendly'}
                ]
            }]
        }
        
        response = self.client.post(add_cases_url, invalid_data3, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('out of range', response.json()['error'])
    
    def test_prompt_lab_prompt_parameter_matching(self):
        """Test that dataset parameter matching works with  prompts"""
        # Create dataset with different parameters
        different_dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name='Different Parameter Dataset',
            description='Dataset with different parameters',
            parameters=['user_name', 'problem_type']  # Different from prompt parameters
        )
        
        # Should still work but might need parameter mapping
        generate_url = f'/api/evaluations/datasets/{different_dataset.id}/generate-cases/'
        generate_data = {
            'use_session_prompt': True,
            'count': 1,
            'generate_output_variations': True
        }
        
        with patch('app.services.evaluation_case_generator.EvaluationCaseGenerator.generate_cases_preview_with_variations') as mock_generate:
            mock_generate.return_value = [{
                'preview_id': 'param-test-1',
                'input_text': 'Parameter test input',
                'parameters': {'customer_name': 'Test User', 'issue_type': 'test'},
                'output_variations': [
                    {'index': 0, 'text': 'Test output', 'style': 'formal'}
                ]
            }]
            
            response = self.client.post(generate_url, generate_data, format='json')
            
            # Should succeed - parameter matching is flexible
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_performance_requirements_met(self):
        """Test that the integration meets performance requirements"""
        import time
        
        # Test generation performance
        generate_url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        generate_data = {
            'use_session_prompt': True,
            'count': 5,
            'generate_output_variations': True
        }
        
        with patch('app.services.evaluation_case_generator.EvaluationCaseGenerator.generate_cases_preview_with_variations') as mock_generate:
            # Mock realistic response time
            mock_generate.return_value = [
                {
                    'preview_id': f'perf-test-{i}',
                    'input_text': f'Performance test input {i}',
                    'parameters': {'customer_name': f'User{i}', 'issue_type': 'performance test'},
                    'output_variations': [
                        {'index': 0, 'text': f'Response {i}-0', 'style': 'formal'},
                        {'index': 1, 'text': f'Response {i}-1', 'style': 'friendly'},
                        {'index': 2, 'text': f'Response {i}-2', 'style': 'detailed'}
                    ]
                } for i in range(5)
            ]
            
            start_time = time.time()
            response = self.client.post(generate_url, generate_data, format='json')
            end_time = time.time()
            
            # Should complete quickly (mocked, but verifies no performance regressions)
            duration = end_time - start_time
            self.assertLess(duration, 2.0, f"Generation took {duration:.2f} seconds")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test case addition performance
        add_cases_url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        add_cases_data = {
            'cases': [
                {
                    'preview_id': f'perf-test-{i}',
                    'input_text': f'Performance test input {i}',
                    'parameters': {'customer_name': f'User{i}', 'issue_type': 'performance test'},
                    'selected_output_index': 0,
                    'output_variations': [
                        {'index': 0, 'text': f'Response {i}-0', 'style': 'formal'},
                        {'index': 1, 'text': f'Response {i}-1', 'style': 'friendly'},
                        {'index': 2, 'text': f'Response {i}-2', 'style': 'detailed'}
                    ]
                } for i in range(5)
            ]
        }
        
        start_time = time.time()
        response = self.client.post(add_cases_url, add_cases_data, format='json')
        end_time = time.time()
        
        # Should complete quickly
        duration = end_time - start_time
        self.assertLess(duration, 1.0, f"Case addition took {duration:.2f} seconds")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios"""
        add_cases_url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        
        # Test partial failure scenario (some cases valid, some invalid)
        mixed_data = {
            'cases': [
                {
                    'preview_id': 'valid-case',
                    'input_text': 'Valid input',
                    'parameters': {'customer_name': 'Valid User', 'issue_type': 'valid issue'},
                    'selected_output_index': 0,
                    'output_variations': [
                        {'index': 0, 'text': 'Valid output', 'style': 'formal'}
                    ]
                },
                {
                    'preview_id': 'invalid-case',
                    'input_text': 'Invalid input',
                    'parameters': {},
                    'selected_output_index': 5,  # Invalid index
                    'output_variations': [
                        {'index': 0, 'text': 'Output', 'style': 'formal'}
                    ]
                }
            ]
        }
        
        response = self.client.post(add_cases_url, mixed_data, format='json')
        
        # Should reject entire batch if any case is invalid
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify no cases were added
        self.assertEqual(EvaluationCase.objects.filter(dataset=self.dataset).count(), 0)
    
    def test_dataset_browsing_with_human_selected_cases(self):
        """Test that datasets show cases with human-selected outputs correctly"""
        # Add some cases using human-in-the-loop workflow
        self.test_full_human_in_loop_flow()  # This adds 2 cases
        
        # Get dataset details
        dataset_detail_url = f'/api/evaluations/datasets/{self.dataset.id}/'
        response = self.client.get(dataset_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # Verify dataset shows cases
        self.assertEqual(response_data['case_count'], 2)
        self.assertEqual(len(response_data['cases']), 2)
        
        # Verify case structure includes context (parameters)
        for case in response_data['cases']:
            self.assertIn('input_text', case)
            self.assertIn('expected_output', case)
            self.assertIn('context', case)
            self.assertIn('customer_name', case['context'])
            self.assertIn('issue_type', case['context'])


class CrossBrowserCompatibilityTests(TestCase):
    """Tests for cross-browser compatibility of the API responses"""
    
    def setUp(self):
        self.client = APIClient()
        self.prompt_lab = PromptLab.objects.create(name='Browser Test PromptLab')
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name='Browser Test Dataset',
            parameters=['test_param']
        )
    
    def test_api_response_format_consistency(self):
        """Test that API responses are consistent across different request formats"""
        # Test JSON content type
        response = self.client.post(
            f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/',
            data=json.dumps({'cases': []}),
            content_type='application/json'
        )
        
        # Should handle empty cases gracefully
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify response is proper JSON
        response_data = response.json()
        self.assertIn('error', response_data)
    
    def test_unicode_handling_in_custom_outputs(self):
        """Test that custom outputs handle Unicode characters correctly"""
        add_cases_url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        unicode_data = {
            'cases': [{
                'preview_id': 'unicode-test',
                'input_text': 'Hello 世界, I understand you have an issue with émojis 🌟',
                'parameters': {'test_param': 'Unicode测试'},
                'custom_output': 'Thank you for your inquiry! We support all languages: 中文, Español, العربية, 日本語 🎉',
                'output_variations': []
            }]
        }
        
        response = self.client.post(add_cases_url, unicode_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify Unicode is preserved
        case = EvaluationCase.objects.get(context__test_param='Unicode测试')
        self.assertIn('🎉', case.expected_output)
        self.assertIn('中文', case.expected_output)