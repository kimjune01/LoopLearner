"""
Tests for improved evaluation case generation
Covers the realistic parameter value generation and case quality improvements
"""
import pytest
from django.test import TestCase
from core.models import Session, SystemPrompt, EvaluationDataset
from app.services.evaluation_case_generator import EvaluationCaseGenerator


class ImprovedCaseGenerationTests(TestCase):
    """Test the improved case generation with realistic parameter values"""
    
    def setUp(self):
        """Set up test data"""
        self.session = Session.objects.create(
            name="Test Session",
            description="Test session for improved case generation"
        )
        
        # Email assistant prompt with EMAIL_CONTENT, RECIPIENT_INFO, SENDER_INFO parameters
        self.email_prompt = SystemPrompt.objects.create(
            session=self.session,
            content="""You are a professional email assistant tasked with improving and polishing email drafts.

<email_content>
{{EMAIL_CONTENT}}
</email_content>

<recipient_info>
{{RECIPIENT_INFO}}
</recipient_info>

<sender_info>
{{SENDER_INFO}}
</sender_info>

Improve the email following professional standards.""",
            version=1,
            parameters=['EMAIL_CONTENT', 'RECIPIENT_INFO', 'SENDER_INFO']
        )
        
        # Customer service prompt with different parameters
        self.customer_service_prompt = SystemPrompt.objects.create(
            session=self.session,
            content="""You are a customer service assistant. Help {{user_name}} with their {{product_type}} issue: {{user_question}}""",
            version=1,
            parameters=['user_name', 'product_type', 'user_question']
        )
        
        self.dataset = EvaluationDataset.objects.create(
            session=self.session,
            name="Test Dataset"
        )
        
        self.case_generator = EvaluationCaseGenerator()
    
    def test_email_content_generation_is_realistic(self):
        """Test that EMAIL_CONTENT generates realistic customer service emails"""
        cases = self.case_generator.generate_cases_preview(self.email_prompt, count=2)
        
        for case in cases:
            email_content = case['parameters']['EMAIL_CONTENT']
            
            # Should be actual email content, not just an email address
            self.assertGreater(len(email_content), 20, "Email content should be substantial")
            self.assertIn('\n', email_content, "Email content should have line breaks")
            
            # Should contain common email elements
            email_lower = email_content.lower()
            has_greeting = any(greeting in email_lower for greeting in ['hi', 'hello', 'dear'])
            has_request = any(word in email_lower for word in ['help', 'issue', 'problem', 'question', 'order'])
            
            self.assertTrue(has_greeting or has_request, 
                          f"Email should have greeting or request. Got: {email_content[:100]}...")
    
    def test_recipient_info_generation_is_contextual(self):
        """Test that RECIPIENT_INFO generates meaningful customer context"""
        cases = self.case_generator.generate_cases_preview(self.email_prompt, count=2)
        
        for case in cases:
            recipient_info = case['parameters']['RECIPIENT_INFO']
            
            # Should not be generic "ValueXX" format
            self.assertNotRegex(recipient_info, r'^Value\d+$', 
                               "Recipient info should not be generic Value format")
            
            # Should contain customer context
            recipient_lower = recipient_info.lower()
            has_name = any(char.isupper() for char in recipient_info)  # Proper names have capitals
            has_context = any(word in recipient_lower for word in 
                            ['customer', 'member', 'premium', 'business', 'account', 'since', 'corporate', 'client', 'buyer', 'frequent'])
            
            self.assertTrue(has_name, f"Recipient should have proper name format: {recipient_info}")
            self.assertTrue(has_context, f"Recipient should have customer context: {recipient_info}")
    
    def test_sender_info_generation_is_professional(self):
        """Test that SENDER_INFO generates appropriate support team information"""
        cases = self.case_generator.generate_cases_preview(self.email_prompt, count=2)
        
        for case in cases:
            sender_info = case['parameters']['SENDER_INFO']
            
            # Should not be generic "ValueXX" format
            self.assertNotRegex(sender_info, r'^Value\d+$', 
                               "Sender info should not be generic Value format")
            
            # Should contain professional role context
            sender_lower = sender_info.lower()
            has_role = any(role in sender_lower for role in 
                         ['support', 'service', 'team', 'specialist', 'manager', 'agent', 'department', 'billing'])
            
            self.assertTrue(has_role, f"Sender should have professional role: {sender_info}")
    
    def test_traditional_parameters_still_work(self):
        """Test that traditional parameters like user_name still generate appropriate values"""
        cases = self.case_generator.generate_cases_preview(self.customer_service_prompt, count=2)
        
        for case in cases:
            user_name = case['parameters']['user_name']
            product_type = case['parameters']['product_type']
            user_question = case['parameters']['user_question']
            
            # User name should be realistic
            self.assertRegex(user_name, r'^[A-Z][a-z]+ [A-Z][a-z]+$', 
                           f"User name should be 'First Last' format: {user_name}")
            
            # Product type should be a real product
            self.assertGreater(len(product_type), 3, "Product type should be meaningful")
            self.assertNotRegex(product_type, r'^Value\d+$', "Product type should not be generic")
            
            # User question should be a realistic question
            self.assertIn('?', user_question, "User question should end with question mark")
            self.assertGreater(len(user_question), 10, "User question should be substantial")
    
    def test_parameter_value_diversity(self):
        """Test that generated parameter values are diverse across multiple cases"""
        cases = self.case_generator.generate_cases_preview(self.email_prompt, count=3)
        
        # Collect all parameter values
        email_contents = [case['parameters']['EMAIL_CONTENT'] for case in cases]
        recipient_infos = [case['parameters']['RECIPIENT_INFO'] for case in cases]
        sender_infos = [case['parameters']['SENDER_INFO'] for case in cases]
        
        # Should have diversity (not all the same)
        self.assertGreater(len(set(email_contents)), 1, 
                          "Should have diverse email content across cases")
        self.assertGreater(len(set(recipient_infos)), 1, 
                          "Should have diverse recipient info across cases")
        self.assertGreater(len(set(sender_infos)), 1, 
                          "Should have diverse sender info across cases")
    
    def test_case_input_text_has_realistic_substitutions(self):
        """Test that the generated input text has realistic parameter substitutions"""
        cases = self.case_generator.generate_cases_preview(self.email_prompt, count=2)
        
        for case in cases:
            input_text = case['input_text']
            email_content = case['parameters']['EMAIL_CONTENT']
            recipient_info = case['parameters']['RECIPIENT_INFO']
            sender_info = case['parameters']['SENDER_INFO']
            
            # Input text should contain the actual parameter values, not placeholders
            self.assertIn(email_content, input_text, 
                         "Input text should contain the actual email content")
            self.assertIn(recipient_info, input_text, 
                         "Input text should contain the actual recipient info")
            self.assertIn(sender_info, input_text, 
                         "Input text should contain the actual sender info")
            
            # Should not contain the placeholder syntax
            self.assertNotIn('{{EMAIL_CONTENT}}', input_text, 
                           "Input text should not contain placeholder syntax")
            self.assertNotIn('{{RECIPIENT_INFO}}', input_text, 
                           "Input text should not contain placeholder syntax")
            self.assertNotIn('{{SENDER_INFO}}', input_text, 
                           "Input text should not contain placeholder syntax")
    
    def test_expected_output_quality(self):
        """Test that expected outputs are relevant and professional"""
        cases = self.case_generator.generate_cases_preview(self.email_prompt, count=2)
        
        for case in cases:
            expected_output = case['expected_output']
            
            # Should be substantial content
            self.assertGreater(len(expected_output), 50, 
                             "Expected output should be substantial")
            
            # Should contain professional email elements
            output_lower = expected_output.lower()
            has_professional_elements = any(element in output_lower for element in 
                                          ['subject:', 'dear', 'best regards', 'sincerely', 'thank you'])
            
            self.assertTrue(has_professional_elements, 
                          f"Expected output should contain professional email elements: {expected_output[:100]}...")
    
    def test_case_regeneration_produces_different_values(self):
        """Test that regenerating a case produces different parameter values"""
        # Generate initial case
        original_cases = self.case_generator.generate_cases_preview(self.email_prompt, count=1)
        original_case = original_cases[0]
        
        # Regenerate the same case
        regenerated_result = self.case_generator.regenerate_single_case(
            self.email_prompt, original_case
        )
        
        # At least one parameter should be different
        original_params = original_case['parameters']
        regenerated_params = regenerated_result['parameters']
        
        params_changed = (
            original_params['EMAIL_CONTENT'] != regenerated_params['EMAIL_CONTENT'] or
            original_params['RECIPIENT_INFO'] != regenerated_params['RECIPIENT_INFO'] or
            original_params['SENDER_INFO'] != regenerated_params['SENDER_INFO']
        )
        
        self.assertTrue(params_changed, 
                       "Regenerated case should have at least one different parameter value")
    
    def test_parameter_update_functionality(self):
        """Test that manually updating parameters works correctly"""
        # Generate initial case
        cases = self.case_generator.generate_cases_preview(self.email_prompt, count=1)
        original_case = cases[0]
        
        # Update parameters manually
        new_parameters = {
            'EMAIL_CONTENT': 'Custom email content for testing',
            'RECIPIENT_INFO': 'Jane Doe, Test Customer',
            'SENDER_INFO': 'Test Support Agent'
        }
        
        updated_case = self.case_generator.update_case_parameters(
            self.email_prompt, original_case, new_parameters
        )
        
        # Verify parameters were updated
        self.assertEqual(updated_case['parameters']['EMAIL_CONTENT'], 
                        'Custom email content for testing')
        self.assertEqual(updated_case['parameters']['RECIPIENT_INFO'], 
                        'Jane Doe, Test Customer')
        self.assertEqual(updated_case['parameters']['SENDER_INFO'], 
                        'Test Support Agent')
        
        # Verify input text reflects the new parameters
        input_text = updated_case['input_text']
        self.assertIn('Custom email content for testing', input_text)
        self.assertIn('Jane Doe, Test Customer', input_text)
        self.assertIn('Test Support Agent', input_text)
    
    def test_parameter_validation_on_update(self):
        """Test that parameter validation works when updating manually"""
        cases = self.case_generator.generate_cases_preview(self.email_prompt, count=1)
        original_case = cases[0]
        
        # Try to update with missing required parameter
        incomplete_parameters = {
            'EMAIL_CONTENT': 'Test content',
            'RECIPIENT_INFO': 'Test recipient'
            # Missing SENDER_INFO
        }
        
        with self.assertRaises(ValueError) as context:
            self.case_generator.update_case_parameters(
                self.email_prompt, original_case, incomplete_parameters
            )
        
        self.assertIn('SENDER_INFO', str(context.exception))
        self.assertIn('Missing required parameters', str(context.exception))
    
    def test_no_generic_value_fallbacks_for_known_parameters(self):
        """Test that known parameters don't fall back to generic Value## format"""
        cases = self.case_generator.generate_cases_preview(self.email_prompt, count=2)
        
        for case in cases:
            for param_name, param_value in case['parameters'].items():
                # None of the known parameters should have generic "ValueXX" format
                self.assertNotRegex(param_value, r'^Value\d+$', 
                                   f"Parameter {param_name} should not use generic format: {param_value}")
                
                # Should not be empty or just whitespace
                self.assertTrue(param_value.strip(), 
                               f"Parameter {param_name} should not be empty")
    
    def test_case_generation_performance(self):
        """Test that case generation completes in reasonable time"""
        import time
        
        start_time = time.time()
        cases = self.case_generator.generate_cases_preview(self.email_prompt, count=2)
        end_time = time.time()
        
        # Should complete within 20 seconds (includes LLM calls)
        generation_time = end_time - start_time
        self.assertLess(generation_time, 20, 
                       f"Case generation took too long: {generation_time:.2f} seconds")
        
        # Should actually generate the requested number of cases
        self.assertEqual(len(cases), 2, "Should generate exactly 2 cases")
    
    def test_preview_id_uniqueness(self):
        """Test that each generated case has a unique preview ID"""
        cases = self.case_generator.generate_cases_preview(self.email_prompt, count=3)
        
        preview_ids = [case['preview_id'] for case in cases]
        unique_ids = set(preview_ids)
        
        self.assertEqual(len(preview_ids), len(unique_ids), 
                        "All preview IDs should be unique")
        
        # Each preview ID should be a valid UUID format
        import uuid
        for preview_id in preview_ids:
            try:
                uuid.UUID(preview_id)
            except ValueError:
                self.fail(f"Preview ID should be valid UUID format: {preview_id}")