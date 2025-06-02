"""
Integration tests for the triple curly brace issue fix
Tests the complete flow from case generation to frontend reconstruction
"""
import pytest
from django.test import TestCase
from core.models import PromptLab, SystemPrompt, EvaluationDataset, EvaluationCase
from app.services.evaluation_case_generator import EvaluationCaseGenerator
import re


class TestTripleBraceIntegration(TestCase):
    """Integration tests for triple brace prevention"""
    
    def setUp(self):
        """Set up test environment"""
        # Create prompt lab
        self.prompt_lab = PromptLab.objects.create(
            name="Email Assistant Lab",
            description="Professional email assistant"
        )
        
        # Create the actual prompt template that caused issues
        self.email_prompt = """You are a professional email assistant tasked with improving and polishing email drafts. Your goal is to enhance the clarity, professionalism, and effectiveness of the given email while maintaining its original intent and tone.

You will be provided with the following information:

<email_content>
{{EMAIL_CONTENT}}
</email_content>

<recipient_info>
{{RECIPIENT_INFO}}
</recipient_info>

<sender_info>
{{SENDER_INFO}}
</sender_info>

First, carefully read and analyze the email content. Consider the following aspects:
1. Purpose of the email
2. Tone and level of formality
3. Structure and organization
4. Clarity of message
5. Grammar and spelling
6. Appropriateness for the recipient

Present your improved version of the email in the following format:

<improved_email>
Subject: [Improved subject line]

[Improved email content, including greeting, body, and closing]
</improved_email>

Remember to maintain the original intent and key information of the email while making it more professional and effective."""
        
        self.system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content=self.email_prompt,
            version=1,
            is_active=True
        )
        
        # Create dataset
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Professional Email Assistant Test Cases",
            description="Test cases for email assistant"
        )
        
        self.generator = EvaluationCaseGenerator()
    
    def test_end_to_end_no_triple_braces(self):
        """Test complete flow from generation to reconstruction doesn't create triple braces"""
        # Generate cases like the real system does
        cases = self.generator.generate_cases_preview(
            prompt=self.system_prompt,
            count=3,
            dataset=self.dataset,
            persist_immediately=True
        )
        
        # Test each generated case
        for case_data in cases:
            with self.subTest(case_id=case_data['id']):
                case = EvaluationCase.objects.get(id=case_data['id'])
                
                # Verify case was stored correctly
                self.assertNotIn('{{{', case.input_text)
                self.assertNotIn('}}}', case.input_text)
                
                # Test frontend reconstruction
                reconstructed = self._simulate_frontend_reconstruction(case)
                
                # This should NOT create triple braces
                self.assertNotIn('{{{', reconstructed)
                self.assertNotIn('}}}', reconstructed)
                
                # Should have proper double-brace parameters
                self.assertIn('{{EMAIL_CONTENT}}', reconstructed)
                self.assertIn('{{RECIPIENT_INFO}}', reconstructed)
                self.assertIn('{{SENDER_INFO}}', reconstructed)
    
    def test_actual_problematic_case_structure(self):
        """Test with the exact structure that caused the original issue"""
        # Create a case manually with the structure that was problematic
        case = EvaluationCase.objects.create(
            dataset=self.dataset,
            input_text=self.email_prompt.replace('{{EMAIL_CONTENT}}', 'Dear Team, Test message')
                                       .replace('{{RECIPIENT_INFO}}', 'John Doe, Premium Customer')
                                       .replace('{{SENDER_INFO}}', 'Support Team'),
            expected_output="Improved email response",
            context={
                'EMAIL_CONTENT': 'Dear Team, Test message',
                'RECIPIENT_INFO': 'John Doe, Premium Customer',
                'SENDER_INFO': 'Support Team'
            }
        )
        
        # Verify case doesn't have triple braces
        self.assertNotIn('{{{', case.input_text)
        
        # Test reconstruction
        reconstructed = self._simulate_frontend_reconstruction(case)
        
        # Should reconstruct to original template without triple braces
        self.assertNotIn('{{{', reconstructed)
        self.assertIn('{{EMAIL_CONTENT}}', reconstructed)
        self.assertIn('{{RECIPIENT_INFO}}', reconstructed)
        self.assertIn('{{SENDER_INFO}}', reconstructed)
    
    def test_xml_tag_content_no_extra_braces(self):
        """Test that XML tag content doesn't get wrapped in extra braces"""
        # Generate a case
        cases = self.generator.generate_cases_preview(
            prompt=self.system_prompt,
            count=1,
            dataset=self.dataset,
            persist_immediately=True
        )
        
        case = EvaluationCase.objects.get(id=cases[0]['id'])
        
        # Check that XML content is clean (no single braces around content)
        # This pattern would indicate the old bug: >{content}<
        email_content = case.context['EMAIL_CONTENT']
        
        # Check that XML content is clean (no single braces around content)
        # Should NOT find pattern like >{content}<
        wrapped_pattern = f">{{{email_content}}}<"
        self.assertNotIn(wrapped_pattern, case.input_text)
        
        # Should find the content properly substituted within XML tags
        self.assertIn(f"<email_content>\n{email_content}\n</email_content>", case.input_text)
    
    def test_complex_content_with_special_chars(self):
        """Test with complex email content that might break regex"""
        complex_content = """Dear Support Team,

I'm writing regarding order #12345 (placed on 01/15/2024). The issue is:
- Product: "Premium Widget" [Model: PW-2024]
- Price: $99.99 (with 10% discount)
- Status: Delayed

Can you provide an update? My email is user+test@example.com.

Best regards,
John Doe"""
        
        # Use the complex content in parameters
        result = self.generator._substitute_parameters(
            self.email_prompt,
            {
                'EMAIL_CONTENT': complex_content,
                'RECIPIENT_INFO': 'John Doe, VIP Customer (Tier: Gold)',
                'SENDER_INFO': 'Support Team <support@company.com>'
            }
        )
        
        # Verify substitution worked correctly
        self.assertIn(complex_content, result)
        self.assertNotIn('{{EMAIL_CONTENT}}', result)
        self.assertNotIn('{{{', result)
        
        # Create a case with this content
        case = EvaluationCase.objects.create(
            dataset=self.dataset,
            input_text=result,
            expected_output="Professional response",
            context={
                'EMAIL_CONTENT': complex_content,
                'RECIPIENT_INFO': 'John Doe, VIP Customer (Tier: Gold)',
                'SENDER_INFO': 'Support Team <support@company.com>'
            }
        )
        
        # Test reconstruction
        reconstructed = self._simulate_frontend_reconstruction(case)
        self.assertNotIn('{{{', reconstructed)
    
    def test_diff_generation_with_fixed_cases(self):
        """Test that diff generation works correctly with fixed cases"""
        # Create a case
        case = EvaluationCase.objects.create(
            dataset=self.dataset,
            input_text=self.email_prompt.replace('{{EMAIL_CONTENT}}', 'Test email content')
                                       .replace('{{RECIPIENT_INFO}}', 'Test recipient')
                                       .replace('{{SENDER_INFO}}', 'Test sender'),
            expected_output="Response",
            context={
                'EMAIL_CONTENT': 'Test email content',
                'RECIPIENT_INFO': 'Test recipient',
                'SENDER_INFO': 'Test sender'
            }
        )
        
        # Simulate what happens when comparing with active prompt
        reconstructed_template = self._simulate_frontend_reconstruction(case)
        active_prompt_content = self.system_prompt.content
        
        # Generate diff
        diff_lines = self._generate_diff(reconstructed_template, active_prompt_content)
        
        # Should show templates match (no differences)
        unchanged_lines = [line for line in diff_lines if line['type'] == 'unchanged']
        changed_lines = [line for line in diff_lines if line['type'] in ['added', 'removed']]
        
        # Should be mostly unchanged since templates should match
        self.assertGreater(len(unchanged_lines), len(changed_lines))
        
        # Most importantly, no triple braces in any diff line
        for line in diff_lines:
            self.assertNotIn('{{{', line['content'])
            self.assertNotIn('}}}', line['content'])
    
    def _simulate_frontend_reconstruction(self, case):
        """Simulate the frontend template reconstruction logic"""
        case_template = case.input_text
        parameters = case.context or {}
        
        # Sort parameters by value length (longest first)
        sorted_params = sorted(parameters.items(), key=lambda x: len(str(x[1])), reverse=True)
        
        for key, value in sorted_params:
            value_str = str(value)
            
            # Skip if the value is already a template placeholder that matches this key
            if value_str == f"{{{{{key}}}}}":
                continue
            
            # Skip if the value contains any template placeholders to avoid double-wrapping
            if re.search(r'\{\{[^}]+\}\}', value_str):
                continue
            
            # Create a regex that matches the exact value
            regex = re.compile(re.escape(value_str), re.IGNORECASE)
            case_template = regex.sub(f"{{{{{key}}}}}", case_template)
        
        return case_template
    
    def _generate_diff(self, old_text, new_text):
        """Simple diff generation for testing"""
        old_lines = old_text.split('\n')
        new_lines = new_text.split('\n')
        
        # Simple comparison - just mark as unchanged if lines are identical
        max_lines = max(len(old_lines), len(new_lines))
        diff_lines = []
        
        for i in range(max_lines):
            old_line = old_lines[i] if i < len(old_lines) else None
            new_line = new_lines[i] if i < len(new_lines) else None
            
            if old_line == new_line:
                if old_line is not None:
                    diff_lines.append({'type': 'unchanged', 'content': old_line})
            else:
                if old_line is not None:
                    diff_lines.append({'type': 'removed', 'content': old_line})
                if new_line is not None:
                    diff_lines.append({'type': 'added', 'content': new_line})
        
        return diff_lines


class TestRegressionScenarios(TestCase):
    """Test specific scenarios that caused the original regression"""
    
    def test_single_curly_brace_wrapping_scenario(self):
        """Test the exact scenario that caused triple braces"""
        # This was the problematic pattern in stored cases
        problematic_input = """<email_content>
{Dear Support Team, I need help with my order.}
</email_content>"""
        
        parameters = {
            'EMAIL_CONTENT': 'Dear Support Team, I need help with my order.'
        }
        
        # Simulate frontend reconstruction
        result = problematic_input
        for key, value in parameters.items():
            value_str = str(value)
            regex = re.compile(re.escape(value_str), re.IGNORECASE)
            result = regex.sub(f"{{{{{key}}}}}", result)
        
        # This would create triple braces (the original bug)
        expected_bad_result = """<email_content>
{{{EMAIL_CONTENT}}}
</email_content>"""
        
        self.assertEqual(result, expected_bad_result)
        
        # Now test the fixed version (how cases should be stored)
        fixed_input = """<email_content>
Dear Support Team, I need help with my order.
</email_content>"""
        
        result_fixed = fixed_input
        for key, value in parameters.items():
            value_str = str(value)
            regex = re.compile(re.escape(value_str), re.IGNORECASE)
            result_fixed = regex.sub(f"{{{{{key}}}}}", result_fixed)
        
        expected_good_result = """<email_content>
{{EMAIL_CONTENT}}
</email_content>"""
        
        self.assertEqual(result_fixed, expected_good_result)
        self.assertNotIn('{{{', result_fixed)
    
    def test_parameter_extraction_prevents_triple_braces(self):
        """Test that parameter extraction correctly identifies double braces only"""
        prompt = SystemPrompt()
        
        # Test content with various brace patterns
        prompt.content = """
        Valid parameter: {{EMAIL_CONTENT}}
        Triple braces (invalid): {{{TRIPLE_PARAM}}}
        Single braces (not parameters): {single}
        Nested: {{OUTER_{{INNER}}_PARAM}}
        Another valid: {{RECIPIENT_INFO}}
        """
        
        extracted = prompt.extract_parameters()
        
        # Should only extract valid double-brace parameters
        self.assertIn('EMAIL_CONTENT', extracted)
        self.assertIn('RECIPIENT_INFO', extracted)
        self.assertIn('INNER', extracted)  # The inner parameter gets extracted
        
        # Should NOT extract triple brace content
        self.assertNotIn('TRIPLE_PARAM', extracted)
        # Should NOT extract single brace content
        self.assertNotIn('single', extracted)