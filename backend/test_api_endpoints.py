#!/usr/bin/env python3
"""
Comprehensive API endpoint verification script.
Tests all major endpoints to ensure they are accessible and returning expected responses.
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000/api"

def test_endpoint(
    method: str, 
    endpoint: str, 
    expected_status: int = 200,
    data: Optional[Dict[str, Any]] = None,
    description: str = ""
) -> bool:
    """Test a single API endpoint."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url)
        else:
            print(f"❌ {description}: Unsupported method {method}")
            return False
        
        if response.status_code == expected_status:
            print(f"✅ {description}: {method} {endpoint} -> {response.status_code}")
            return True
        else:
            print(f"❌ {description}: {method} {endpoint} -> {response.status_code} (expected {expected_status})")
            try:
                error_data = response.json()
                if 'error' in error_data:
                    print(f"   Error: {error_data['error']}")
            except:
                pass
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {description}: Connection failed to {url}")
        return False
    except Exception as e:
        print(f"❌ {description}: {str(e)}")
        return False

def main():
    """Run comprehensive API endpoint tests."""
    print("🔍 Testing Loop Learner API Endpoints")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 0
    
    # Test cases: (method, endpoint, expected_status, data, description)
    test_cases = [
        # Core system endpoints
        ("GET", "/health/", 200, None, "System Health Check"),
        ("GET", "/metrics/", 200, None, "System Metrics"),
        
        # Session management
        ("GET", "/sessions/", 200, None, "List Sessions"),
        ("POST", "/sessions/", 201, {
            "name": "API Test Session",
            "description": "Testing API endpoints"
        }, "Create Session"),
        
        # System state
        ("GET", "/system/state/", 200, None, "Get System State"),
        ("GET", "/system/prompt/", 200, None, "Get System Prompt"),
        
        # Evaluation datasets (global)
        ("GET", "/evaluations/datasets/", 200, None, "List Global Evaluation Datasets"),
        ("POST", "/evaluations/datasets/", 201, {
            "name": "API Test Dataset",
            "description": "Testing evaluation dataset API",
            "parameters": ["test_param"]
        }, "Create Global Evaluation Dataset"),
        
        # Dashboard endpoints
        ("GET", "/dashboard/overview/", 200, None, "Dashboard Overview"),
        ("GET", "/dashboard/summary/", 200, None, "Dashboard Summary"),
        
        # Optimization endpoints
        ("GET", "/optimization/scheduler/", 200, None, "Optimization Scheduler Status"),
        ("GET", "/optimization/history/", 200, None, "Optimization History"),
        ("GET", "/optimization/health/", 200, None, "Optimization Health Check"),
        
        # Demo endpoints
        ("GET", "/demo/status/", 200, None, "Demo Status"),
        ("GET", "/demo/health/", 200, None, "Demo Health Check"),
        
        # Legacy core endpoints (backward compatibility)
        ("GET", "/emails/", 200, None, "List Legacy Emails"),
        ("GET", "/optimization/status/", 200, None, "Legacy Optimization Status"),
    ]
    
    # Run basic tests
    for method, endpoint, expected_status, data, description in test_cases:
        total_tests += 1
        if test_endpoint(method, endpoint, expected_status, data, description):
            tests_passed += 1
    
    print("\n" + "=" * 50)
    
    # Get a session ID for session-specific tests
    try:
        response = requests.get(f"{BASE_URL}/sessions/")
        if response.status_code == 200:
            sessions = response.json().get('sessions', [])
            if sessions:
                session_id = sessions[0]['id']
                print(f"🔍 Testing session-specific endpoints with session: {session_id}")
                
                session_tests = [
                    ("GET", f"/sessions/{session_id}/", 200, None, "Get Session Detail"),
                    ("GET", f"/sessions/{session_id}/stats/", 200, None, "Get Session Stats"),
                    ("GET", f"/sessions/{session_id}/confidence/", 200, None, "Get Session Confidence"),
                    ("GET", f"/sessions/{session_id}/preferences/", 200, None, "Get Session Preferences"),
                    ("GET", f"/sessions/{session_id}/convergence/", 200, None, "Get Convergence Assessment"),
                    ("GET", f"/sessions/{session_id}/export/", 200, None, "Export Session Data"),
                ]
                
                for method, endpoint, expected_status, data, description in session_tests:
                    total_tests += 1
                    if test_endpoint(method, endpoint, expected_status, data, description):
                        tests_passed += 1
    except Exception as e:
        print(f"⚠️  Could not test session-specific endpoints: {e}")
    
    # Get an evaluation dataset ID for dataset-specific tests
    try:
        response = requests.get(f"{BASE_URL}/evaluations/datasets/")
        if response.status_code == 200:
            datasets = response.json().get('datasets', [])
            if datasets:
                dataset_id = datasets[0]['id']
                print(f"🔍 Testing evaluation dataset endpoints with dataset: {dataset_id}")
                
                dataset_tests = [
                    ("GET", f"/evaluations/datasets/{dataset_id}/", 200, None, "Get Dataset Detail"),
                    ("GET", f"/evaluations/datasets/{dataset_id}/cases/", 200, None, "List Dataset Cases"),
                ]
                
                for method, endpoint, expected_status, data, description in dataset_tests:
                    total_tests += 1
                    if test_endpoint(method, endpoint, expected_status, data, description):
                        tests_passed += 1
    except Exception as e:
        print(f"⚠️  Could not test dataset-specific endpoints: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All API endpoints are accessible and working correctly!")
        return 0
    else:
        failed_tests = total_tests - tests_passed
        print(f"⚠️  {failed_tests} test(s) failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)