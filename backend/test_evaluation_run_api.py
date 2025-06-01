"""
Test script to verify evaluation run API functionality
"""

import requests
import json

API_BASE = "http://localhost:8000/api"

def test_evaluation_run():
    """Test the evaluation run endpoint"""
    
    # First, get a session with an active prompt
    sessions_response = requests.get(f"{API_BASE}/sessions/")
    sessions = sessions_response.json()['sessions']
    
    if not sessions:
        print("No sessions found. Creating a test session...")
        # Create a test session
        session_data = {
            "name": "Test Session for Evaluation",
            "description": "Testing evaluation functionality",
            "initial_prompt": "You are a helpful assistant that {{tone}} responds to emails about {{topic}}."
        }
        session_response = requests.post(f"{API_BASE}/sessions/", json=session_data)
        session = session_response.json()
        session_id = session['id']
    else:
        session = sessions[0]
        session_id = session['id']
    
    print(f"Using session: {session['name']} (ID: {session_id})")
    
    # Get session details to find the active prompt
    session_detail_response = requests.get(f"{API_BASE}/sessions/{session_id}/")
    session_detail = session_detail_response.json()
    
    active_prompt = session_detail.get('active_prompt')
    if not active_prompt or not active_prompt.get('id'):
        print("No active prompt found in session")
        return
    
    prompt_id = active_prompt['id']
    print(f"Active prompt ID: {prompt_id}, Version: {active_prompt['version']}")
    
    # Create a test evaluation dataset
    dataset_data = {
        "session_id": session_id,
        "name": "Test Evaluation Dataset",
        "description": "Testing evaluation run functionality",
        "parameters": ["tone", "topic"],
        "parameter_descriptions": {
            "tone": "The tone of the response (friendly, professional, etc.)",
            "topic": "The topic being discussed"
        }
    }
    
    dataset_response = requests.post(f"{API_BASE}/evaluations/datasets/", json=dataset_data)
    if dataset_response.status_code != 201:
        print(f"Failed to create dataset: {dataset_response.text}")
        return
    
    dataset = dataset_response.json()
    dataset_id = dataset['id']
    print(f"Created dataset: {dataset['name']} (ID: {dataset_id})")
    
    # Add some test cases
    test_cases = [
        {
            "input_text": "Please help me with my order",
            "expected_output": "I'd be happy to help you with your order",
            "context": {"tone": "friendly", "topic": "customer service"}
        },
        {
            "input_text": "I need technical support",
            "expected_output": "Let me assist you with your technical issue",
            "context": {"tone": "professional", "topic": "technical support"}
        }
    ]
    
    for case in test_cases:
        case_response = requests.post(
            f"{API_BASE}/evaluations/datasets/{dataset_id}/cases/",
            json=case
        )
        if case_response.status_code == 201:
            print(f"Added test case: {case['input_text'][:30]}...")
        else:
            print(f"Failed to add case: {case_response.text}")
    
    # Now run the evaluation
    print("\nRunning evaluation...")
    run_data = {
        "dataset_id": dataset_id,
        "prompt_id": prompt_id
    }
    
    run_response = requests.post(f"{API_BASE}/evaluations/run/", json=run_data)
    
    if run_response.status_code == 201:
        run_result = run_response.json()
        print("\nEvaluation completed successfully!")
        print(f"Run ID: {run_result['run_id']}")
        print(f"Status: {run_result['status']}")
        print(f"Overall Score: {run_result.get('overall_score', 'N/A')}")
        print(f"Cases Passed: {run_result.get('passed_cases', 0)}/{run_result.get('total_cases', 0)}")
        
        # Get detailed results
        if run_result.get('run_id'):
            results_response = requests.get(f"{API_BASE}/evaluations/runs/{run_result['run_id']}/results/")
            if results_response.status_code == 200:
                results = results_response.json()
                print(f"\nDetailed Results:")
                for i, result in enumerate(results.get('results', [])):
                    print(f"\nCase {i+1}:")
                    print(f"  Input: {result['input_text'][:50]}...")
                    print(f"  Expected: {result['expected_output'][:50]}...")
                    print(f"  Generated: {result['generated_output'][:50]}...")
                    print(f"  Similarity: {result['similarity_score']:.2f}")
                    print(f"  Passed: {result['passed']}")
    else:
        print(f"\nEvaluation failed: {run_response.status_code}")
        print(run_response.text)

if __name__ == "__main__":
    test_evaluation_run()