"""
Tests for optimization API endpoints
"""
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from core.models import PromptLab, SystemPrompt, EvaluationDataset


class TestOptimizationAPI(TestCase):
    """Test optimization API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test prompt lab
        self.prompt_lab = PromptLab.objects.create(
            name="Test Prompt Lab",
            description="Test prompt lab for optimization"
        )
        
        # Create active prompt
        self.active_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="You are a helpful assistant with {{tone}} tone.",
            version=1,
            is_active=True,
            parameters=["tone"]
        )
        
        # Create evaluation datasets
        self.dataset1 = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset 1",
            description="First test dataset",
            parameters=["tone"],
            case_count=5,
            quality_score=0.8,
            human_reviewed_count=3
        )
        
        self.dataset2 = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset 2", 
            description="Second test dataset",
            parameters=["tone", "style"],
            case_count=3,
            quality_score=0.6,
            human_reviewed_count=1
        )
    
    def test_trigger_optimization_with_datasets_success(self):
        """Test successful optimization trigger with datasets"""
        url = reverse('trigger-optimization-with-dataset')
        data = {
            "prompt_lab_id": str(self.prompt_lab.id),
            "dataset_ids": [self.dataset1.id, self.dataset2.id],
            "force": False
        }
        
        # Mock the optimization orchestrator
        with patch('app.services.optimization_orchestrator.OptimizationOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Mock successful optimization
            mock_result = Mock()
            mock_result.id = "opt-123"
            mock_result.best_candidate = Mock(improvement=0.15)
            mock_orchestrator.trigger_optimization_with_datasets = AsyncMock(return_value=mock_result)
            
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], 'success')
            self.assertEqual(response.data['optimization_id'], 'opt-123')
            self.assertEqual(response.data['improvement'], 0.15)
            self.assertEqual(response.data['datasets_used'], 2)
            self.assertIn('15.0%', response.data['message'])
    
    def test_trigger_optimization_prompt_lab_not_found(self):
        """Test optimization trigger with non-existent prompt lab"""
        url = reverse('trigger-optimization-with-dataset')
        data = {
            "prompt_lab_id": "00000000-0000-0000-0000-000000000000",
            "dataset_ids": [1],
            "force": False
        }
        
        with patch('app.services.optimization_orchestrator.OptimizationOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            mock_orchestrator.trigger_optimization_with_datasets = AsyncMock(
                side_effect=PromptLab.DoesNotExist()
            )
            
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_trigger_optimization_no_datasets(self):
        """Test optimization trigger with empty dataset list"""
        url = reverse('trigger-optimization-with-dataset')
        data = {
            "prompt_lab_id": str(self.prompt_lab.id),
            "dataset_ids": [],
            "force": False
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_trigger_optimization_convergence_error(self):
        """Test optimization trigger when prompt has converged"""
        url = reverse('trigger-optimization-with-dataset')
        data = {
            "prompt_lab_id": str(self.prompt_lab.id),
            "dataset_ids": [self.dataset1.id],
            "force": False
        }
        
        with patch('app.services.optimization_orchestrator.OptimizationOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            mock_orchestrator.trigger_optimization_with_datasets = AsyncMock(
                side_effect=ValueError("Prompt has converged. Use force=True to override.")
            )
            
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("converged", response.data['detail'])
    
    def test_trigger_optimization_force_convergence(self):
        """Test forcing optimization despite convergence"""
        url = reverse('trigger-optimization-with-dataset')
        data = {
            "prompt_lab_id": str(self.prompt_lab.id),
            "dataset_ids": [self.dataset1.id],
            "force": True
        }
        
        with patch('app.services.optimization_orchestrator.OptimizationOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Should succeed with force=True
            mock_result = Mock()
            mock_result.id = "opt-456"
            mock_result.best_candidate = Mock(improvement=0.08)
            mock_orchestrator.trigger_optimization_with_datasets = AsyncMock(return_value=mock_result)
            
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['improvement'], 0.08)
    
    def test_get_optimization_datasets(self):
        """Test getting datasets available for optimization"""
        url = reverse('evaluation-optimization-datasets', kwargs={'prompt_lab_id': str(self.prompt_lab.id)})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Check first dataset
        dataset1_data = next(d for d in response.data if d['id'] == self.dataset1.id)
        self.assertEqual(dataset1_data['name'], 'Test Dataset 1')
        self.assertEqual(dataset1_data['case_count'], 5)
        self.assertEqual(dataset1_data['quality_score'], 0.8)
        self.assertEqual(dataset1_data['human_reviewed'], True)
        self.assertEqual(dataset1_data['parameters'], ['tone'])
    
    def test_get_optimization_datasets_no_cases(self):
        """Test that datasets without cases are not returned"""
        # Create dataset without cases
        empty_dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Empty Dataset",
            description="Dataset with no cases",
            parameters=["tone"],
            case_count=0
        )
        
        url = reverse('evaluation-optimization-datasets', kwargs={'prompt_lab_id': str(self.prompt_lab.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return datasets with cases
        self.assertEqual(len(response.data), 2)
        dataset_ids = [d['id'] for d in response.data]
        self.assertNotIn(empty_dataset.id, dataset_ids)
    
    def test_get_optimization_datasets_prompt_lab_not_found(self):
        """Test getting datasets for non-existent prompt lab"""
        url = reverse('evaluation-optimization-datasets', 
                     kwargs={'prompt_lab_id': '00000000-0000-0000-0000-000000000000'})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_trigger_optimization_invalid_data(self):
        """Test optimization trigger with invalid request data"""
        url = reverse('trigger-optimization-with-dataset')
        
        # Missing required fields
        data = {
            "prompt_lab_id": str(self.prompt_lab.id)
            # Missing dataset_ids
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_trigger_optimization_general_error(self):
        """Test handling of unexpected errors during optimization"""
        url = reverse('trigger-optimization-with-dataset')
        data = {
            "prompt_lab_id": str(self.prompt_lab.id),
            "dataset_ids": [self.dataset1.id],
            "force": False
        }
        
        with patch('app.services.optimization_orchestrator.OptimizationOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            mock_orchestrator.trigger_optimization_with_datasets = AsyncMock(
                side_effect=Exception("Unexpected error")
            )
            
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.data['detail'], 'Optimization failed')