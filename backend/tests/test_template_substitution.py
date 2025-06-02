"""
Tests for template parameter substitution to prevent triple curly brace regression
"""
import pytest
from django.test import TestCase
from core.models import PromptLab, SystemPrompt, EvaluationDataset, EvaluationCase
from app.services.evaluation_case_generator import EvaluationCaseGenerator


class TestTemplateSubstitution(TestCase):
    """Test parameter substitution in templates"""
    
    def setUp(self):
        """Set up test data"""
        # Create a prompt lab
        self.prompt_lab = PromptLab.objects.create(
            name="Test Prompt Lab",
            description="Test lab for template substitution"
        )
        
        # Create a system prompt with parameters
        self.prompt_template = """You are a professional email assistant.

<email_content>
{{EMAIL_CONTENT}}
</email_content>

<recipient_info>
{{RECIPIENT_INFO}}
</recipient_info>

<sender_info>
{{SENDER_INFO}}
</sender_info>

Please improve this email."""
        
        self.system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content=self.prompt_template,
            version=1,
            is_active=True
        )
        
        # Create dataset
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset",
            description="Test dataset for template substitution"
        )
        
        self.generator = EvaluationCaseGenerator()
    
    def test_parameter_substitution_no_triple_braces(self):
        """Test that parameter substitution doesn't create triple braces"""
        parameters = {
            'EMAIL_CONTENT': 'Dear Team, This is a test email.',
            'RECIPIENT_INFO': 'John Doe, Premium Customer',
            'SENDER_INFO': 'Support Team'
        }
        
        # Substitute parameters
        result = self.generator._substitute_parameters(self.prompt_template, parameters)
        
        # Check no triple braces
        self.assertNotIn('{{{', result)
        self.assertNotIn('}}}', result)
        
        # Check correct substitution
        self.assertIn('Dear Team, This is a test email.', result)
        self.assertIn('John Doe, Premium Customer', result)
        self.assertIn('Support Team', result)
        
        # Check no template placeholders remain
        self.assertNotIn('{{EMAIL_CONTENT}}', result)
        self.assertNotIn('{{RECIPIENT_INFO}}', result)
        self.assertNotIn('{{SENDER_INFO}}', result)
    
    def test_parameter_substitution_with_special_characters(self):
        """Test substitution with special regex characters"""
        parameters = {
            'EMAIL_CONTENT': 'Test with special chars: $100 (discount) [limited offer]',
            'RECIPIENT_INFO': 'User+Email@example.com',
            'SENDER_INFO': 'Support.*Team'
        }
        
        result = self.generator._substitute_parameters(self.prompt_template, parameters)
        
        # Check substitution worked correctly
        self.assertIn('$100 (discount) [limited offer]', result)
        self.assertIn('User+Email@example.com', result)
        self.assertIn('Support.*Team', result)
        
        # No triple braces
        self.assertNotIn('{{{', result)
    
    def test_parameter_substitution_with_newlines(self):
        """Test substitution with multi-line content"""
        parameters = {
            'EMAIL_CONTENT': 'Line 1\nLine 2\n\nLine 4 with gap',
            'RECIPIENT_INFO': 'Multi\nLine\nRecipient',
            'SENDER_INFO': 'Sender\nWith\nNewlines'
        }
        
        result = self.generator._substitute_parameters(self.prompt_template, parameters)
        
        # Check content preserved
        self.assertIn('Line 1\nLine 2\n\nLine 4 with gap', result)
        self.assertNotIn('{{{', result)
    
    def test_xml_wrapped_content_no_single_braces(self):
        """Test that XML-wrapped content doesn't get single braces"""
        # This tests the specific issue we fixed
        template_with_xml = """<email_content>
{{EMAIL_CONTENT}}
</email_content>"""
        
        parameters = {'EMAIL_CONTENT': 'Test content'}
        result = self.generator._substitute_parameters(template_with_xml, parameters)
        
        # Should not have single braces around content
        self.assertNotIn('{Test content}', result)
        # Should have clean substitution
        self.assertIn('<email_content>\nTest content\n</email_content>', result)
    
    def test_case_generation_no_triple_braces(self):
        """Test that generated cases don't produce triple braces in reconstruction"""
        # Generate a case
        cases = self.generator.generate_cases_preview(
            prompt=self.system_prompt,
            count=1,
            dataset=self.dataset,
            persist_immediately=True
        )
        
        self.assertEqual(len(cases), 1)
        case = EvaluationCase.objects.get(id=cases[0]['id'])
        
        # Simulate frontend reconstruction
        reconstructed = self._simulate_frontend_reconstruction(case)
        
        # Check no triple braces in reconstruction
        self.assertNotIn('{{{', reconstructed)
        self.assertNotIn('}}}', reconstructed)
    
    def test_edge_case_parameter_value_with_braces(self):
        """Test parameter values that contain braces"""
        parameters = {
            'EMAIL_CONTENT': 'Content with {braces} and {{double}}',
            'RECIPIENT_INFO': 'Normal recipient',
            'SENDER_INFO': 'Normal sender'
        }
        
        result = self.generator._substitute_parameters(self.prompt_template, parameters)
        
        # Check content is preserved exactly
        self.assertIn('Content with {braces} and {{double}}', result)
        # No triple braces
        self.assertNotIn('{{{EMAIL_CONTENT}}}', result)
    
    def test_parameter_names_case_sensitive(self):
        """Test that parameter substitution is case-sensitive"""
        template = "{{email_content}} vs {{EMAIL_CONTENT}}"
        parameters = {
            'email_content': 'lowercase',
            'EMAIL_CONTENT': 'UPPERCASE'
        }
        
        result = self.generator._substitute_parameters(template, parameters)
        
        self.assertEqual(result, "lowercase vs UPPERCASE")
    
    def _simulate_frontend_reconstruction(self, case):
        """Simulate what frontend does when reconstructing template"""
        import re
        
        case_template = case.input_text
        parameters = case.context or {}
        
        # Sort by length (longest first)
        sorted_params = sorted(parameters.items(), key=lambda x: len(str(x[1])), reverse=True)
        
        for key, value in sorted_params:
            value_str = str(value)
            
            # Skip if already template placeholder
            if value_str == f"{{{{{key}}}}}":
                continue
            
            # Skip if contains template placeholders
            if re.search(r'\{\{[^}]+\}\}', value_str):
                continue
            
            # Replace value with placeholder
            regex = re.compile(re.escape(value_str), re.IGNORECASE)
            case_template = regex.sub(f"{{{{{key}}}}}", case_template)
        
        return case_template


class TestPromptParameterExtraction(TestCase):
    """Test parameter extraction from prompts"""
    
    def test_extract_parameters_double_braces(self):
        """Test extraction only finds double braces, not triple"""
        prompt = SystemPrompt()
        prompt.content = """
        Normal: {{PARAM1}}
        Triple should not match: {{{PARAM2}}}
        Nested: {{INNER}}
        Valid: {{PARAM3}}
        """
        
        params = prompt.extract_parameters()
        
        # Should only extract double-brace parameters
        self.assertIn('PARAM1', params)
        self.assertIn('PARAM3', params)
        self.assertIn('INNER', params)
        # Should not extract triple brace content
        self.assertNotIn('PARAM2', params)
        # Should not extract single brace content
        self.assertNotIn('{PARAM2}', params)
    
    def test_extract_parameters_no_duplicates(self):
        """Test that duplicate parameters are not included multiple times"""
        prompt = SystemPrompt()
        prompt.content = "{{PARAM}} and {{PARAM}} again {{PARAM}}"
        
        params = prompt.extract_parameters()
        
        self.assertEqual(params.count('PARAM'), 1)
        self.assertEqual(len(params), 1)


class TestEvaluationCaseStorage(TestCase):
    """Test that evaluation cases are stored correctly"""
    
    def setUp(self):
        self.prompt_lab = PromptLab.objects.create(name="Test Lab")
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset"
        )
    
    def test_case_stores_substituted_content(self):
        """Test that cases store substituted content, not templates"""
        case = EvaluationCase.objects.create(
            dataset=self.dataset,
            input_text="Email content: Dear Team, Test message.",
            expected_output="Improved email",
            context={
                'EMAIL_CONTENT': 'Dear Team, Test message.'
            }
        )
        
        # Input text should not contain template placeholders
        self.assertNotIn('{{EMAIL_CONTENT}}', case.input_text)
        # Should contain actual content
        self.assertIn('Dear Team, Test message.', case.input_text)
    
    def test_case_context_preserves_parameter_values(self):
        """Test that case context correctly stores parameter values"""
        context = {
            'PARAM1': 'Value with spaces',
            'PARAM2': 'Value\nwith\nnewlines',
            'PARAM3': 'Value with "quotes" and \'apostrophes\''
        }
        
        case = EvaluationCase.objects.create(
            dataset=self.dataset,
            input_text="Test input",
            expected_output="Test output",
            context=context
        )
        
        # Reload from database
        case.refresh_from_db()
        
        # Check all values preserved exactly
        self.assertEqual(case.context['PARAM1'], 'Value with spaces')
        self.assertEqual(case.context['PARAM2'], 'Value\nwith\nnewlines')
        self.assertEqual(case.context['PARAM3'], 'Value with "quotes" and \'apostrophes\'')


class TestRegressionPrevention(TestCase):
    """Specific regression tests for the triple curly brace issue"""
    
    def setUp(self):
        self.generator = EvaluationCaseGenerator()
    
    def test_no_f_string_formatting_issues(self):
        """Test that we're not using f-strings for brace substitution"""
        # This would fail with f-string approach
        template = "{{PARAM}}"
        parameters = {'PARAM': 'value'}
        
        result = self.generator._substitute_parameters(template, parameters)
        self.assertEqual(result, "value")
        
        # Test with multiple braces
        template2 = "{{PARAM1}} and {{PARAM2}}"
        parameters2 = {'PARAM1': 'val1', 'PARAM2': 'val2'}
        
        result2 = self.generator._substitute_parameters(template2, parameters2)
        self.assertEqual(result2, "val1 and val2")
    
    def test_xml_content_regression(self):
        """Test the specific XML content case that caused the issue"""
        template = """<email_content>
{{EMAIL_CONTENT}}
</email_content>

<recipient_info>
{{RECIPIENT_INFO}}
</recipient_info>"""
        
        parameters = {
            'EMAIL_CONTENT': 'Test email content',
            'RECIPIENT_INFO': 'Test recipient'
        }
        
        result = self.generator._substitute_parameters(template, parameters)
        
        # Should not have any braces around the substituted content
        self.assertIn('<email_content>\nTest email content\n</email_content>', result)
        self.assertIn('<recipient_info>\nTest recipient\n</recipient_info>', result)
        
        # Definitely no triple braces
        self.assertNotIn('{{{', result)
        self.assertNotIn('}}}', result)
        
        # And no single braces wrapping content
        self.assertNotIn('{Test email content}', result)
        self.assertNotIn('{Test recipient}', result)