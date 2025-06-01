"""
Test API endpoints for case generation with multiple output variations.
Following TDD approach - these tests are written before API implementation.
"""
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, AsyncMock
from core.models import PromptLab, SystemPrompt, EvaluationDataset


class CaseGenerationAPITests(TestCase):
    """Test case generation API with multiple output support"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test  with prompt
        self.prompt_lab = PromptLab.objects.create(
            name='Test PromptLab for API',
            description='Testing case generation API'
        )
        
        self.prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content='Hello {{customer_name}}, I understand you have a {{issue_type}}. Let me help you.',
            version=1,
            is_active=True
        )
        
        # Create test dataset
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name='Test API Dataset',
            description='Testing API functionality',
            parameters=['customer_name', 'issue_type']
        )
    
    def test_generate_cases_returns_multiple_outputs(self):
        """Test API returns multiple output options when requested"""
        # Given: A request for case generation with variations
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'use_session_prompt': True,
            'count': 2,
            'generate_output_variations': True,
            'variations_count': 3
        }
        
        with patch('app.services.evaluation_case_generator.EvaluationCaseGenerator.generate_cases_preview_with_variations') as mock_generate:
            # Mock the generator response
            mock_generate.return_value = [
                {
                    'preview_id': 'test-id-1',
                    'input_text': 'Hello John Smith, I understand you have a billing issue. Let me help you.',
                    'parameters': {'customer_name': 'John Smith', 'issue_type': 'billing issue'},
                    'prompt_content': self.prompt.content,
                    'output_variations': [
                        {'index': 0, 'text': 'Formal response variation 1', 'style': 'formal'},
                        {'index': 1, 'text': 'Friendly response variation 2', 'style': 'friendly'},
                        {'index': 2, 'text': 'Detailed response variation 3', 'style': 'detailed'}
                    ],
                    'selected_output_index': None,
                    'custom_output': None
                },
                {
                    'preview_id': 'test-id-2',
                    'input_text': 'Hello Jane Doe, I understand you have a shipping delay. Let me help you.',
                    'parameters': {'customer_name': 'Jane Doe', 'issue_type': 'shipping delay'},
                    'prompt_content': self.prompt.content,
                    'output_variations': [
                        {'index': 0, 'text': 'Formal shipping response', 'style': 'formal'},
                        {'index': 1, 'text': 'Friendly shipping response', 'style': 'friendly'},
                        {'index': 2, 'text': 'Detailed shipping response', 'style': 'detailed'}
                    ],
                    'selected_output_index': None,
                    'custom_output': None
                }
            ]
            
            # When: Calling generate endpoint with variations enabled
            response = self.client.post(url, data, format='json')
            
            # Then: Response should include output_variations array
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()
            
            self.assertIn('previews', response_data)
            self.assertEqual(len(response_data['previews']), 2)
            
            for preview in response_data['previews']:
                self.assertIn('output_variations', preview)
                self.assertEqual(len(preview['output_variations']), 3)
                self.assertIn('selected_output_index', preview)
                self.assertIn('custom_output', preview)
                self.assertIsNone(preview['selected_output_index'])
                self.assertIsNone(preview['custom_output'])
                
                # Verify each variation has required fields
                for variation in preview['output_variations']:
                    self.assertIn('index', variation)
                    self.assertIn('text', variation)
                    self.assertIn('style', variation)
    
    def test_generate_cases_backward_compatibility_single_output(self):
        """Test API maintains backward compatibility for single output"""
        # Given: A request without variations enabled
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'use_session_prompt': True,
            'count': 2,
            'generate_output_variations': False
        }
        
        with patch('app.services.evaluation_case_generator.EvaluationCaseGenerator.generate_cases_preview') as mock_generate:
            # Mock the generator response for single output
            mock_generate.return_value = [
                {
                    'preview_id': 'test-id-1',
                    'input_text': 'Hello John Smith, I understand you have a billing issue.',
                    'expected_output': 'Single output response',
                    'parameters': {'customer_name': 'John Smith', 'issue_type': 'billing issue'},
                    'prompt_content': self.prompt.content
                }
            ]
            
            # When: Calling generate endpoint without variations
            response = self.client.post(url, data, format='json')
            
            # Then: Response should have single expected_output (backward compatible)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()
            
            self.assertIn('previews', response_data)
            preview = response_data['previews'][0]
            self.assertIn('expected_output', preview)
            self.assertNotIn('output_variations', preview)
    
    def test_add_cases_with_selected_outputs(self):
        """Test adding cases with user-selected outputs"""
        # Given: Preview cases with selected outputs
        url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        data = {
            'cases': [
                {
                    'preview_id': 'test-id-1',
                    'input_text': 'Hello John Smith, I understand you have a billing issue.',
                    'parameters': {'customer_name': 'John Smith', 'issue_type': 'billing issue'},
                    'selected_output_index': 1,
                    'output_variations': [
                        {'index': 0, 'text': 'Formal response', 'style': 'formal'},
                        {'index': 1, 'text': 'Friendly response', 'style': 'friendly'},
                        {'index': 2, 'text': 'Detailed response', 'style': 'detailed'}
                    ]
                },
                {
                    'preview_id': 'test-id-2',
                    'input_text': 'Hello Jane Doe, I understand you have a shipping delay.',
                    'parameters': {'customer_name': 'Jane Doe', 'issue_type': 'shipping delay'},
                    'selected_output_index': 0,
                    'output_variations': [
                        {'index': 0, 'text': 'Professional shipping response', 'style': 'formal'},
                        {'index': 1, 'text': 'Casual shipping response', 'style': 'friendly'},
                        {'index': 2, 'text': 'Comprehensive shipping response', 'style': 'detailed'}
                    ]
                }
            ]
        }
        
        # When: Adding cases with selected outputs
        response = self.client.post(url, data, format='json')
        
        # Then: Cases should be added with selected outputs, not defaults
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertIn('added_cases', response_data)
        self.assertEqual(len(response_data['added_cases']), 2)
        
        # Verify first case uses selected output (index 1)
        case1 = response_data['added_cases'][0]
        self.assertEqual(case1['expected_output'], 'Friendly response')
        self.assertEqual(case1['input_text'], 'Hello John Smith, I understand you have a billing issue.')
        
        # Verify second case uses selected output (index 0)
        case2 = response_data['added_cases'][1]
        self.assertEqual(case2['expected_output'], 'Professional shipping response')
        self.assertEqual(case2['input_text'], 'Hello Jane Doe, I understand you have a shipping delay.')
    
    def test_add_cases_with_custom_outputs(self):
        """Test adding cases with user-provided custom outputs"""
        # Given: Preview cases with custom outputs
        url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        data = {
            'cases': [
                {
                    'preview_id': 'test-id-1',
                    'input_text': 'Hello Bob Wilson, I understand you have a technical issue.',
                    'parameters': {'customer_name': 'Bob Wilson', 'issue_type': 'technical issue'},
                    'custom_output': "I understand you're experiencing technical difficulties. Let me connect you with our technical support team who can provide specialized assistance.",
                    'output_variations': [
                        {'index': 0, 'text': 'Standard tech response', 'style': 'formal'},
                        {'index': 1, 'text': 'Friendly tech response', 'style': 'friendly'},
                        {'index': 2, 'text': 'Detailed tech response', 'style': 'detailed'}
                    ]
                }
            ]
        }
        
        # When: Adding cases with custom outputs
        response = self.client.post(url, data, format='json')
        
        # Then: Cases should use custom outputs
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertIn('added_cases', response_data)
        self.assertEqual(len(response_data['added_cases']), 1)
        
        case = response_data['added_cases'][0]
        self.assertEqual(case['expected_output'], "I understand you're experiencing technical difficulties. Let me connect you with our technical support team who can provide specialized assistance.")
        self.assertEqual(case['input_text'], 'Hello Bob Wilson, I understand you have a technical issue.')
    
    def test_add_cases_with_mixed_selection_and_custom_outputs(self):
        """Test mixing AI-selected and custom outputs in same request"""
        # Given: Mixed cases with both selected and custom outputs
        url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        data = {
            'cases': [
                {
                    'preview_id': 'test-id-1',
                    'input_text': 'Case with selected output',
                    'parameters': {'customer_name': 'User1', 'issue_type': 'billing'},
                    'selected_output_index': 2,
                    'output_variations': [
                        {'index': 0, 'text': 'Option 1', 'style': 'formal'},
                        {'index': 1, 'text': 'Option 2', 'style': 'friendly'},
                        {'index': 2, 'text': 'Option 3', 'style': 'detailed'}
                    ]
                },
                {
                    'preview_id': 'test-id-2',
                    'input_text': 'Case with custom output',
                    'parameters': {'customer_name': 'User2', 'issue_type': 'shipping'},
                    'custom_output': 'This is my custom response text',
                    'output_variations': [
                        {'index': 0, 'text': 'AI Option 1', 'style': 'formal'},
                        {'index': 1, 'text': 'AI Option 2', 'style': 'friendly'},
                        {'index': 2, 'text': 'AI Option 3', 'style': 'detailed'}
                    ]
                }
            ]
        }
        
        # When: Adding mixed cases
        response = self.client.post(url, data, format='json')
        
        # Then: Both types should be saved correctly
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        cases = response_data['added_cases']
        self.assertEqual(len(cases), 2)
        
        # First case should use selected output
        self.assertEqual(cases[0]['expected_output'], 'Option 3')
        
        # Second case should use custom output
        self.assertEqual(cases[1]['expected_output'], 'This is my custom response text')
    
    def test_add_cases_validation_errors(self):
        """Test validation for case addition"""
        # Given: Invalid case data
        url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        
        # Test 1: Missing required fields
        data = {'cases': [{'preview_id': 'test-id-1'}]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test 2: Both selected_output_index and custom_output provided
        data = {
            'cases': [{
                'preview_id': 'test-id-1',
                'input_text': 'Test input',
                'parameters': {},
                'selected_output_index': 1,
                'custom_output': 'Custom text',
                'output_variations': []
            }]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test 3: Neither selected_output_index nor custom_output provided
        data = {
            'cases': [{
                'preview_id': 'test-id-1',
                'input_text': 'Test input',
                'parameters': {},
                'output_variations': []
            }]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test 4: Invalid selected_output_index
        data = {
            'cases': [{
                'preview_id': 'test-id-1',
                'input_text': 'Test input',
                'parameters': {},
                'selected_output_index': 5,  # Out of range
                'output_variations': [
                    {'index': 0, 'text': 'Option 1', 'style': 'formal'},
                    {'index': 1, 'text': 'Option 2', 'style': 'friendly'}
                ]
            }]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_add_cases_persists_to_database(self):
        """Test that added cases are actually saved to database"""
        # Given: Valid case data
        url = f'/api/evaluations/datasets/{self.dataset.id}/add-selected-cases/'
        data = {
            'cases': [{
                'preview_id': 'test-id-1',
                'input_text': 'Hello Test User, I understand you have a test issue.',
                'parameters': {'customer_name': 'Test User', 'issue_type': 'test issue'},
                'selected_output_index': 0,
                'output_variations': [
                    {'index': 0, 'text': 'Selected response', 'style': 'formal'},
                    {'index': 1, 'text': 'Not selected', 'style': 'friendly'}
                ]
            }]
        }
        
        # When: Adding the case
        response = self.client.post(url, data, format='json')
        
        # Then: Case should be persisted in database
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify case exists in database
        from core.models import EvaluationCase
        cases = EvaluationCase.objects.filter(dataset=self.dataset)
        self.assertEqual(cases.count(), 1)
        
        case = cases.first()
        self.assertEqual(case.input_text, 'Hello Test User, I understand you have a test issue.')
        self.assertEqual(case.expected_output, 'Selected response')
        self.assertEqual(case.context['customer_name'], 'Test User')
        self.assertEqual(case.context['issue_type'], 'test issue')
    
    def test_performance_requirements(self):
        """Test that API meets performance requirements"""
        import time
        
        # Given: Request for multiple cases with variations
        url = f'/api/evaluations/datasets/{self.dataset.id}/generate-cases/'
        data = {
            'use_session_prompt': True,
            'count': 5,
            'generate_output_variations': True,
            'variations_count': 3
        }
        
        with patch('app.services.evaluation_case_generator.EvaluationCaseGenerator.generate_cases_preview_with_variations') as mock_generate:
            # Mock quick response
            mock_generate.return_value = [
                {
                    'preview_id': f'test-id-{i}',
                    'input_text': f'Test input {i}',
                    'parameters': {},
                    'output_variations': [
                        {'index': 0, 'text': f'Response {i}-0', 'style': 'formal'},
                        {'index': 1, 'text': f'Response {i}-1', 'style': 'friendly'},
                        {'index': 2, 'text': f'Response {i}-2', 'style': 'detailed'}
                    ]
                } for i in range(5)
            ]
            
            # When: Making the request
            start_time = time.time()
            response = self.client.post(url, data, format='json')
            end_time = time.time()
            
            # Then: Should complete within reasonable time
            duration = end_time - start_time
            self.assertLess(duration, 5.0, f"API took {duration:.2f} seconds")
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class CaseGenerationAPIUrlTests(TestCase):
    """Test URL routing for case generation endpoints"""
    
    def test_generate_cases_url_exists(self):
        """Test that generate cases URL is properly configured"""
        # Given: A dataset ID
        dataset_id = 1
        
        # When: Resolving the URL
        url = reverse('evaluation-generate-cases', kwargs={'dataset_id': dataset_id})
        
        # Then: URL should be correct
        self.assertEqual(url, f'/api/evaluations/datasets/{dataset_id}/generate-cases/')
    
    def test_add_selected_cases_url_exists(self):
        """Test that add selected cases URL is properly configured"""
        # Given: A dataset ID
        dataset_id = 1
        
        # When: Resolving the URL
        url = reverse('evaluation-add-selected-cases', kwargs={'dataset_id': dataset_id})
        
        # Then: URL should be correct
        self.assertEqual(url, f'/api/evaluations/datasets/{dataset_id}/add-selected-cases/')