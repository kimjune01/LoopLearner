import pytest
import json
from django.test import TestCase, Client
from core.models import PromptLab, SystemPrompt


class ParameterExtractionTestCase(TestCase):
    """Test cases for parameter extraction functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test 
        self.prompt_lab = PromptLab.objects.create(
            name="Parameter Test PromptLab",
            description="Testing parameter extraction"
        )
    
    def test_parameter_extraction_from_content(self):
        """Test that parameters are correctly extracted from prompt content"""
        prompt_content = "Hello {{user_name}}, you are working on {{project}} with {{priority}} priority."
        
        system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content=prompt_content,
            version=1,
            is_active=True
        )
        
        # Check that parameters were extracted
        expected_parameters = ['user_name', 'project', 'priority']
        self.assertEqual(set(system_prompt.parameters), set(expected_parameters))
    
    def test_parameter_extraction_with_duplicates(self):
        """Test that duplicate parameters are handled correctly"""
        prompt_content = "Hello {{name}}, your role is {{role}}. Remember {{name}}, your {{role}} is important."
        
        system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content=prompt_content,
            version=1,
            is_active=True
        )
        
        # Should only have unique parameters
        expected_parameters = ['name', 'role']
        self.assertEqual(set(system_prompt.parameters), set(expected_parameters))
        self.assertEqual(len(system_prompt.parameters), 2)
    
    def test_parameter_extraction_with_spaces(self):
        """Test parameter extraction with spaces in parameter names"""
        prompt_content = "You are {{ assistant name }} for {{ company name }} handling {{ task type }}."
        
        system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content=prompt_content,
            version=1,
            is_active=True
        )
        
        expected_parameters = ['assistant name', 'company name', 'task type']
        self.assertEqual(set(system_prompt.parameters), set(expected_parameters))
    
    def test_parameter_extraction_multiline(self):
        """Test parameter extraction from multiline content"""
        prompt_content = """You are {{assistant_name}} for {{company}}.

Key responsibilities:
- Handle {{task_type}} requests
- Maintain {{communication_style}} tone
- Follow {{company_guidelines}}

Current user: {{current_user}}
Department: {{user_department}}"""
        
        system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content=prompt_content,
            version=1,
            is_active=True
        )
        
        expected_parameters = [
            'assistant_name', 'company', 'task_type', 
            'communication_style', 'company_guidelines', 
            'current_user', 'user_department'
        ]
        self.assertEqual(set(system_prompt.parameters), set(expected_parameters))
    
    def test_no_parameters_in_content(self):
        """Test prompt with no parameters"""
        prompt_content = "This is a regular prompt with no parameters."
        
        system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content=prompt_content,
            version=1,
            is_active=True
        )
        
        self.assertEqual(system_prompt.parameters, [])
    
    def test_empty_content(self):
        """Test prompt with empty content"""
        system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="",
            version=1,
            is_active=True
        )
        
        self.assertEqual(system_prompt.parameters, [])
    
    def test_parameters_updated_on_content_change(self):
        """Test that parameters are updated when content changes"""
        # Create initial prompt
        system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="Hello {{user}}",
            version=1,
            is_active=True
        )
        
        self.assertEqual(system_prompt.parameters, ['user'])
        
        # Update content
        system_prompt.content = "Welcome {{name}} to {{app}}"
        system_prompt.save()
        
        # Parameters should be updated
        expected_parameters = ['name', 'app']
        self.assertEqual(set(system_prompt.parameters), set(expected_parameters))
    
    def test_prompt_lab_detail_api_includes_parameters(self):
        """Test that  detail API includes parameters in response"""
        # Create prompt with parameters
        prompt_content = "Hello {{user_name}}, your task is {{task_type}}."
        
        SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content=prompt_content,
            version=1,
            is_active=True
        )
        
        # Call  detail API
        response = self.client.get(f'/api/prompt-labs/{self.prompt_lab.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that active_prompt includes parameters
        self.assertIn('active_prompt', data)
        active_prompt = data['active_prompt']
        
        self.assertIn('parameters', active_prompt)
        expected_parameters = ['user_name', 'task_type']
        self.assertEqual(set(active_prompt['parameters']), set(expected_parameters))
    
    def test_prompt_update_preserves_parameters(self):
        """Test that updating a prompt via API correctly extracts new parameters"""
        # Create initial prompt
        SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="Initial prompt with {{old_param}}",
            version=1,
            is_active=True
        )
        
        # Update prompt via API
        new_prompt_content = "Updated prompt with {{new_param}} and {{another_param}}"
        response = self.client.put(
            f'/api/prompt-labs/{self.prompt_lab.id}/',
            data=json.dumps({'initial_prompt': new_prompt_content}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify parameters were extracted
        updated_prompt = SystemPrompt.objects.get(
            prompt_lab=self.prompt_lab,
            is_active=True
        )
        
        expected_parameters = ['new_param', 'another_param']
        self.assertEqual(set(updated_prompt.parameters), set(expected_parameters))
    
    def test_invalid_parameter_patterns(self):
        """Test handling of invalid or malformed parameter patterns"""
        prompt_content = "This has {single} braces and {{incomplete} and }}incomplete{{ patterns."
        
        system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content=prompt_content,
            version=1,
            is_active=True
        )
        
        # Should only extract valid patterns (none in this case)
        self.assertEqual(system_prompt.parameters, [])
    
    def test_nested_braces_handling(self):
        """Test handling of nested or complex brace patterns"""
        prompt_content = "Valid: {{param1}} and {{param2}}. Invalid: {{{nested}}} and {{{{quad}}}}"
        
        system_prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content=prompt_content,
            version=1,
            is_active=True
        )
        
        # Should extract only the valid double-brace patterns
        expected_parameters = ['param1', 'param2']
        self.assertEqual(set(system_prompt.parameters), set(expected_parameters))


if __name__ == '__main__':
    pytest.main([__file__])