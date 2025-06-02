#!/usr/bin/env python
"""
Test script for the Draft Case System
Tests the complete draft case workflow including generation, curation, and promotion.
"""
import os
import sys
import django
import json
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'looplearner.settings')
django.setup()

from core.models import PromptLab, EvaluationDataset, DraftCase, EvaluationCase, SystemPrompt
from app.services.draft_case_manager import DraftCaseManager


def setup_test_data():
    """Create test data for the draft case system"""
    print("Setting up test data...")
    
    # Create a test prompt lab
    prompt_lab = PromptLab.objects.create(
        name="Test Prompt Lab for Draft Cases",
        description="A test prompt lab for testing draft case functionality"
    )
    
    # Create a system prompt with parameters
    system_prompt = SystemPrompt.objects.create(
        prompt_lab=prompt_lab,
        content="You are a customer service assistant. Help the customer with their inquiry about {{product_name}} from order {{order_id}}. Customer name: {{customer_name}}.",
        version=1,
        is_active=True
    )
    
    # Create an evaluation dataset
    dataset = EvaluationDataset.objects.create(
        prompt_lab=prompt_lab,
        name="Customer Service Test Dataset",
        description="Test dataset for customer service scenarios",
        parameters=["product_name", "order_id", "customer_name"],
        parameter_descriptions={
            "product_name": "Name of the product the customer is asking about",
            "order_id": "Customer's order identification number", 
            "customer_name": "Customer's full name"
        }
    )
    
    print(f"Created prompt lab: {prompt_lab.id}")
    print(f"Created system prompt: {system_prompt.id}")
    print(f"Created dataset: {dataset.id}")
    
    return prompt_lab, system_prompt, dataset


def test_draft_generation():
    """Test draft case generation"""
    print("\n=== Testing Draft Generation ===")
    
    prompt_lab, system_prompt, dataset = setup_test_data()
    draft_manager = DraftCaseManager()
    
    # Test generating draft cases
    import asyncio
    
    async def run_generation_test():
        print("Generating draft cases...")
        result = await draft_manager.ensure_draft_availability(dataset)
        print(f"Generation result: {result}")
        
        # Check that drafts were created using async-safe method
        from asgiref.sync import sync_to_async
        drafts = await sync_to_async(draft_manager.get_ready_drafts)(dataset)
        print(f"Found {len(drafts)} ready drafts")
        
        for i, draft in enumerate(drafts):
            print(f"Draft {i+1}:")
            print(f"  ID: {draft.id}")
            print(f"  Input: {draft.input_text[:100]}...")
            print(f"  Variations: {len(draft.output_variations)}")
            print(f"  Status: {draft.status}")
            print(f"  Parameters: {draft.parameters}")
        
        return drafts
    
    drafts = asyncio.run(run_generation_test())
    return prompt_lab, system_prompt, dataset, drafts


def test_api_endpoints():
    """Test the draft case API endpoints"""
    print("\n=== Testing API Endpoints ===")
    
    prompt_lab, system_prompt, dataset, drafts = test_draft_generation()
    client = Client()
    
    # Test GET drafts endpoint
    print("Testing GET /api/evaluations/datasets/{id}/drafts/")
    response = client.get(f'/api/evaluations/datasets/{dataset.id}/drafts/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"Response: {json.dumps(data, indent=2)}")
    
    # Test draft promotion
    if drafts:
        draft = drafts[0]
        print(f"\nTesting draft promotion for draft {draft.id}")
        
        promotion_data = {
            'selected_output_index': 0  # Select first output variation
        }
        
        response = client.post(
            f'/api/evaluations/datasets/{dataset.id}/drafts/{draft.id}/promote/',
            data=json.dumps(promotion_data),
            content_type='application/json'
        )
        
        print(f"Promotion status: {response.status_code}")
        if response.status_code == 201:
            data = json.loads(response.content)
            print(f"Promotion response: {json.dumps(data, indent=2)}")
            
            # Verify the case was created
            case_id = data['promoted_case']['id']
            case = EvaluationCase.objects.get(id=case_id)
            print(f"Created evaluation case: {case}")
    
    # Test draft status endpoint
    print("\nTesting GET /api/evaluations/drafts/status/")
    response = client.get('/api/evaluations/drafts/status/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"Status response: {json.dumps(data, indent=2)}")


def test_draft_discard():
    """Test discarding draft cases"""
    print("\n=== Testing Draft Discard ===")
    
    # Create fresh test data
    prompt_lab, system_prompt, dataset = setup_test_data()
    draft_manager = DraftCaseManager()
    
    # Generate drafts
    import asyncio
    drafts = asyncio.run(draft_manager._generate_draft_cases(dataset, 2))
    
    if drafts:
        draft = drafts[0]
        print(f"Discarding draft {draft.id}")
        
        client = Client()
        discard_data = {
            'reason': 'Test discard - not suitable for evaluation'
        }
        
        response = client.post(
            f'/api/evaluations/datasets/{dataset.id}/drafts/{draft.id}/discard/',
            data=json.dumps(discard_data),
            content_type='application/json'
        )
        
        print(f"Discard status: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.content)
            print(f"Discard response: {json.dumps(data, indent=2)}")
            
            # Verify draft status changed
            draft.refresh_from_db()
            print(f"Draft status after discard: {draft.status}")


def test_background_generation():
    """Test background draft generation triggers"""
    print("\n=== Testing Background Generation ===")
    
    # Create a new dataset (should trigger background generation)
    prompt_lab, system_prompt, _ = setup_test_data()
    
    client = Client()
    dataset_data = {
        'prompt_lab_id': str(prompt_lab.id),
        'name': 'Background Test Dataset',
        'description': 'Dataset to test background draft generation',
        'parameters': ['test_param'],
        'parameter_descriptions': {'test_param': 'A test parameter'}
    }
    
    print("Creating new dataset (should trigger background generation)...")
    response = client.post(
        '/api/evaluations/datasets/',
        data=json.dumps(dataset_data),
        content_type='application/json'
    )
    
    print(f"Dataset creation status: {response.status_code}")
    if response.status_code == 201:
        data = json.loads(response.content)
        dataset_id = data['id']
        print(f"Created dataset: {dataset_id}")
        
        # Wait a moment for background generation
        import time
        print("Waiting for background generation...")
        time.sleep(2)
        
        # Check if drafts were generated
        response = client.get(f'/api/evaluations/datasets/{dataset_id}/drafts/')
        if response.status_code == 200:
            data = json.loads(response.content)
            print(f"Drafts after background generation: {data['count']}")


def cleanup_test_data():
    """Clean up test data"""
    print("\n=== Cleaning Up Test Data ===")
    
    # Delete all test prompt labs (cascades to related objects)
    test_labs = PromptLab.objects.filter(name__icontains="Test Prompt Lab")
    count = test_labs.count()
    test_labs.delete()
    
    print(f"Deleted {count} test prompt labs and related data")


def main():
    """Run all tests"""
    print("Testing Draft Case System")
    print("=" * 50)
    
    try:
        # Run tests
        test_draft_generation()
        test_api_endpoints()
        test_draft_discard()
        test_background_generation()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        cleanup_test_data()


if __name__ == '__main__':
    main()