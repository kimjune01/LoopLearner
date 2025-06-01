"""
Test multiple output generation for human-in-the-loop dataset creation.
Following TDD approach - these tests are written before implementation.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from django.test import TestCase
from core.models import PromptLab, SystemPrompt, EvaluationDataset
from app.services.evaluation_case_generator import EvaluationCaseGenerator
import difflib


class MultipleOutputGenerationTests(TestCase):
    """Test multiple output generation functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.generator = EvaluationCaseGenerator()
        
        # Create test prompt lab with prompt
        self.prompt_lab = PromptLab.objects.create(
            name='Test PromptLab',
            description='Test  for output generation'
        )
        
        self.prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content='Hello {{customer_name}}, I understand you have a {{issue_type}}. Let me help you.',
            version=1,
            is_active=True
        )
        
        # Test parameters
        self.test_parameters = {
            'customer_name': 'John Smith',
            'issue_type': 'billing problem'
        }
    
    def test_generate_multiple_outputs_for_single_input(self):
        """Test that generator produces 3 different output variations"""
        # Given: A prompt with substituted parameters
        input_text = "Hello John Smith, I understand you have a billing problem. Let me help you."
        
        # Mock different responses for each variation
        mock_responses = [
            "Thank you for contacting us regarding your billing problem, John. I'll be happy to review your account.",
            "Hi John! I understand you're having billing issues. Let me help you resolve this quickly.",
            "I appreciate you reaching out about your billing concern. Let me provide detailed assistance."
        ]
        
        with patch.object(self.generator.llm_provider, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = mock_responses
            
            # When: Generating multiple outputs
            outputs = self.generator.generate_multiple_outputs(
                input_text=input_text,
                prompt_template=self.prompt.content,
                num_variations=3
            )
            
            # Then: Should return exactly 3 variations
            self.assertEqual(len(outputs), 3)
            
            # Each output should be a dict with required fields
            for i, output in enumerate(outputs):
                self.assertIn('index', output)
                self.assertIn('text', output)
                self.assertIn('style', output)
                self.assertEqual(output['index'], i)
                self.assertIsInstance(output['text'], str)
                self.assertGreater(len(output['text']), 20)  # Meaningful response
    
    def test_output_variations_are_meaningfully_different(self):
        """Test that variations aren't just minor rephrasing"""
        # Given: Generated output variations with different responses
        input_text = "Hello Jane Doe, I understand you have a shipping delay. Let me help you."
        
        # Mock responses that are meaningfully different
        different_responses = [
            "Thank you for contacting us about your shipping delay. I'll track your order immediately.",
            "Hi Jane! So sorry about the delay - let me check what's happening with your shipment.",
            "I understand shipping delays can be frustrating. Let me provide you with detailed tracking information and next steps."
        ]
        
        with patch.object(self.generator.llm_provider, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = different_responses
            
            outputs = self.generator.generate_multiple_outputs(
                input_text=input_text,
                prompt_template=self.prompt.content,
                num_variations=3
            )
            
            # When: Comparing similarity between variations
            texts = [output['text'] for output in outputs]
            
            # Then: Variations should be sufficiently different
            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    similarity = self._calculate_similarity(texts[i], texts[j])
                    # Similarity should be less than 0.8 (80%)
                    self.assertLess(
                        similarity, 0.8,
                        f"Outputs {i} and {j} are too similar ({similarity:.2f})"
                    )
    
    def test_output_variations_maintain_quality(self):
        """Test that all variations are high quality responses"""
        # Given: Generated output variations
        input_text = "Hello Alice Johnson, I understand you have a refund request. Let me help you."
        
        # Mock high-quality responses
        quality_responses = [
            "Thank you for your refund request, Alice. I'll be happy to process this for you right away.",
            "Hi Alice! I understand you'd like a refund. Let me help you get this sorted out quickly.",
            "I appreciate you contacting us about your refund request. Let me provide you with complete assistance and walk you through the refund process step by step."
        ]
        
        with patch.object(self.generator.llm_provider, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = quality_responses
            
            outputs = self.generator.generate_multiple_outputs(
                input_text=input_text,
                prompt_template=self.prompt.content,
                num_variations=3
            )
            
            # When: Evaluating each variation
            for output in outputs:
                text = output['text']
                
                # Then: All should meet quality thresholds
                # Check minimum length
                self.assertGreater(len(text), 50, "Output too short")
                
                # Check it addresses the issue
                self.assertIn('refund', text.lower(), "Should mention the issue")
                
                # Check professional tone (no inappropriate language)
                inappropriate_words = ['damn', 'hell', 'stupid']
                for word in inappropriate_words:
                    self.assertNotIn(word, text.lower())
                
                # Check it's a complete sentence
                self.assertTrue(
                    text.strip().endswith(('.', '!', '?')),
                    "Should end with proper punctuation"
                )
    
    def test_output_styles_are_different(self):
        """Test that each variation has a different style"""
        # Given: Generated outputs
        input_text = "Hello Bob Wilson, I understand you have a technical issue. Let me help you."
        
        with patch.object(self.generator.llm_provider, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = "Mock response for style testing"
            
            outputs = self.generator.generate_multiple_outputs(
                input_text=input_text,
                prompt_template=self.prompt.content,
                num_variations=3
            )
            
            # When: Checking styles
            styles = [output['style'] for output in outputs]
            
            # Then: Styles should be unique
            self.assertEqual(len(set(styles)), 3, "All styles should be different")
            
            # Expected styles
            expected_styles = {'formal', 'friendly', 'detailed'}
            self.assertEqual(set(styles), expected_styles)
    
    def test_generate_outputs_with_custom_styles(self):
        """Test generating outputs with specified styles"""
        # Given: Custom style preferences
        custom_styles = ['empathetic', 'solution-focused', 'explanatory']
        input_text = "Hello Mary Johnson, I understand you have a warranty question. Let me help you."
        
        with patch.object(self.generator.llm_provider, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = "Mock response for custom style testing"
            
            # When: Generating with custom styles
            outputs = self.generator.generate_multiple_outputs(
                input_text=input_text,
                prompt_template=self.prompt.content,
                num_variations=3,
                styles=custom_styles
            )
            
            # Then: Should use the custom styles
            generated_styles = [output['style'] for output in outputs]
            self.assertEqual(generated_styles, custom_styles)
    
    def test_handles_generation_errors_gracefully(self):
        """Test error handling when LLM fails"""
        # Given: A mock that raises an error
        with patch.object(self.generator.llm_provider, 'generate', side_effect=Exception("LLM Error")):
            input_text = "Hello Test User, I understand you have a problem. Let me help you."
            
            # When: Attempting to generate outputs
            outputs = self.generator.generate_multiple_outputs(
                input_text=input_text,
                prompt_template=self.prompt.content,
                num_variations=3
            )
            
            # Then: Should return fallback outputs
            self.assertEqual(len(outputs), 3)
            for output in outputs:
                self.assertIn('text', output)
                # Fallback responses should be helpful
                text_lower = output['text'].lower()
                self.assertTrue(
                    any(phrase in text_lower for phrase in ['thank you', 'help', 'assist', 'here to']),
                    f"Fallback text should be helpful: {output['text']}"
                )
    
    def test_generation_performance(self):
        """Test that generation completes within 10 seconds"""
        import time
        
        # Given: A typical input
        input_text = "Hello Customer, I understand you have an issue. Let me help you."
        
        # Mock the LLM provider for faster testing
        with patch.object(self.generator.llm_provider, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = "Mock response for testing performance"
            
            # When: Generating outputs
            start_time = time.time()
            outputs = self.generator.generate_multiple_outputs(
                input_text=input_text,
                prompt_template=self.prompt.content,
                num_variations=3
            )
            end_time = time.time()
            
            # Then: Should complete within 10 seconds
            duration = end_time - start_time
            self.assertLess(duration, 10.0, f"Generation took {duration:.2f} seconds")
            self.assertEqual(len(outputs), 3)
    
    def test_preserves_input_context_in_outputs(self):
        """Test that outputs appropriately reference the input context"""
        # Given: Specific input context
        input_text = "Hello Sarah Connor, I understand you have a damaged product issue. Let me help you."
        
        # Mock responses that preserve context
        context_responses = [
            "I understand your product was damaged. Let me help you with a replacement.",
            "Hi Sarah! I'm sorry to hear about the damaged product. Let's get this resolved quickly.",
            "Thank you for reporting the damaged product. I'll provide detailed steps for your return."
        ]
        
        with patch.object(self.generator.llm_provider, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = context_responses
            
            # When: Generating outputs
            outputs = self.generator.generate_multiple_outputs(
                input_text=input_text,
                prompt_template=self.prompt.content,
                num_variations=3
            )
            
            # Then: Outputs should reference the specific issue
            for output in outputs:
                text = output['text'].lower()
                # Should mention either damage, product, or related terms
                context_preserved = any(term in text for term in ['damage', 'product', 'replacement', 'return'])
                self.assertTrue(
                    context_preserved,
                    f"Output doesn't preserve context: {output['text']}"
                )
    
    def test_concurrent_generation_requests(self):
        """Test handling multiple simultaneous generation requests"""
        import concurrent.futures
        
        # Given: Multiple different inputs
        inputs = [
            "Hello User1, I understand you have a billing issue. Let me help you.",
            "Hello User2, I understand you have a shipping issue. Let me help you.",
            "Hello User3, I understand you have a technical issue. Let me help you."
        ]
        
        with patch.object(self.generator.llm_provider, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = "Mock concurrent response"
            
            # When: Generating outputs concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(
                        self.generator.generate_multiple_outputs,
                        input_text=input_text,
                        prompt_template=self.prompt.content,
                        num_variations=3
                    )
                    for input_text in inputs
                ]
                
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Then: All should complete successfully
            self.assertEqual(len(results), 3)
            for result in results:
                self.assertEqual(len(result), 3)
    
    def _calculate_similarity(self, text1, text2):
        """Calculate similarity ratio between two texts"""
        return difflib.SequenceMatcher(None, text1, text2).ratio()


class OutputVariationIntegrationTests(TestCase):
    """Integration tests for output variation in case generation"""
    
    def setUp(self):
        """Set up test data"""
        self.generator = EvaluationCaseGenerator()
        
        # Create test dataset
        self.prompt_lab = PromptLab.objects.create(name='Test PromptLab')
        self.prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content='Customer {{name}} needs help with {{issue}}',
            version=1,
            is_active=True
        )
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name='Test Dataset',
            parameters=['name', 'issue']
        )
    
    def test_case_preview_includes_output_variations(self):
        """Test that case previews include multiple output options"""
        # Given: A request for case generation with variations
        with patch.object(self.generator.llm_provider, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = "Mock variation response"
            
            # When: Generating case previews
            previews = self.generator.generate_cases_preview_with_variations(
                prompt=self.prompt,
                count=2,
                enable_variations=True
            )
            
            # Then: Each preview should have output_variations
            self.assertEqual(len(previews), 2)
            for preview in previews:
                self.assertIn('output_variations', preview)
                self.assertEqual(len(preview['output_variations']), 3)
                self.assertNotIn('expected_output', preview)  # Should not have single output
    
    def test_backward_compatibility_single_output(self):
        """Test that single output generation still works"""
        # Given: A request without variations
        with patch.object(self.generator.llm_provider, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = "Mock single output response"
            
            # When: Generating case previews
            previews = self.generator.generate_cases_preview(
                prompt=self.prompt,
                count=2
            )
            
            # Then: Should have single expected_output (backward compatible)
            self.assertEqual(len(previews), 2)
            for preview in previews:
                self.assertIn('expected_output', preview)
                self.assertNotIn('output_variations', preview)