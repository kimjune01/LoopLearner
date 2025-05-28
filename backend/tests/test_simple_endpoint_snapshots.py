"""
Simple snapshot tests for backend API endpoints
Basic validation without complex mocking
"""

import pytest
from django.test import TestCase, Client


@pytest.mark.django_db
class TestSimpleEndpointSnapshots(TestCase):
    """Simple snapshot tests for API endpoints"""
    
    def setUp(self):
        self.client = Client()

    def test_health_endpoint_responds(self):
        """Test /api/health/ endpoint returns 200"""
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)

    def test_metrics_endpoint_responds(self):
        """Test /api/metrics/ endpoint returns 200"""
        response = self.client.get('/api/metrics/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, dict)

    def test_demo_health_endpoint_responds(self):
        """Test /api/demo/health/ endpoint returns 200"""
        response = self.client.get('/api/demo/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('healthy', data)

    def test_demo_scenarios_endpoint_responds(self):
        """Test /api/demo/workflow/ GET endpoint returns 200"""
        response = self.client.get('/api/demo/workflow/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('data', data)
        self.assertIn('available_scenarios', data['data'])

    def test_demo_status_endpoint_responds(self):
        """Test /api/demo/status/ endpoint returns 200"""
        response = self.client.get('/api/demo/status/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, dict)

    def test_optimization_history_endpoint_responds(self):
        """Test /api/optimization/history/ endpoint returns 200"""
        response = self.client.get('/api/optimization/history/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('data', data)
        self.assertIn('recent_optimizations', data['data'])

    def test_synthetic_email_post_endpoint_responds(self):
        """Test /api/generate-synthetic-email/ POST endpoint"""
        response = self.client.post('/api/generate-synthetic-email/', {})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('email_id', data)
        self.assertIn('subject', data)

    def test_nonexistent_endpoint_404(self):
        """Test nonexistent endpoint returns 404"""
        response = self.client.get('/api/nonexistent/')
        self.assertEqual(response.status_code, 404)


class TestEndpointStructure(TestCase):
    """Test response structure consistency"""
    
    def setUp(self):
        self.client = Client()
    
    def test_json_responses(self):
        """Test that API endpoints return JSON"""
        endpoints = [
            '/api/health/',
            '/api/metrics/',
            '/api/demo/health/',
            '/api/demo/workflow/',
            '/api/demo/status/',
            '/api/optimization/history/',
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
            # Should be able to parse as JSON
            data = response.json()
            self.assertIsInstance(data, dict)


class TestBasicPerformance(TestCase):
    """Basic performance validation"""
    
    def setUp(self):
        self.client = Client()
    
    def test_health_endpoints_fast(self):
        """Test health endpoints respond quickly"""
        import time
        
        endpoints = ['/api/health/', '/api/demo/health/']
        
        for endpoint in endpoints:
            start = time.time()
            response = self.client.get(endpoint)
            duration = time.time() - start
            
            self.assertEqual(response.status_code, 200)
            self.assertLess(duration, 2.0)  # Should respond in under 2 seconds