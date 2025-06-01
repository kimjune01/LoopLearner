"""
Tests for evaluation models following TDD principles.
These tests define the expected behavior for evaluation models.
"""
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from core.models import PromptLab, SystemPrompt, EvaluationDataset, EvaluationCase, EvaluationRun, EvaluationResult


class EvaluationDatasetModelTests(TestCase):
    """Test cases for EvaluationDataset model"""
    
    def setUp(self):
        """Set up test data"""
        self.prompt_lab = PromptLab.objects.create(
            name="Test PromptLab",
            description="A test session for evaluation"
        )
    
    def test_create_evaluation_dataset(self):
        """Test creating an evaluation dataset with valid data"""
        dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset",
            description="A test evaluation dataset"
        )
        
        self.assertEqual(dataset.name, "Test Dataset")
        self.assertEqual(dataset.description, "A test evaluation dataset")
        self.assertEqual(dataset.session, self.prompt_lab)
        self.assertIsNotNone(dataset.created_at)
        self.assertIsNotNone(dataset.updated_at)
    
    def test_evaluation_dataset_str_representation(self):
        """Test string representation of dataset"""
        dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset"
        )
        expected_str = f"Test Dataset ({self.prompt_lab.name})"
        self.assertEqual(str(dataset), expected_str)
    
    def test_evaluation_dataset_session_relationship(self):
        """Test that dataset is properly linked to """
        dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset"
        )
        
        # Test forward relationship
        self.assertEqual(dataset.session, self.prompt_lab)
        
        # Test reverse relationship
        self.assertIn(dataset, self.prompt_lab.evaluation_datasets.all())


class EvaluationCaseModelTests(TestCase):
    """Test cases for EvaluationCase model"""
    
    def setUp(self):
        """Set up test data"""
        self.prompt_lab = PromptLab.objects.create(
            name="Test PromptLab",
            description="A test session for evaluation"
        )
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset"
        )
    
    def test_create_evaluation_case(self):
        """Test creating an evaluation case with valid data"""
        case = EvaluationCase.objects.create(
            dataset=self.dataset,
            input_text="What is the capital of France?",
            expected_output="The capital of France is Paris."
        )
        
        self.assertEqual(case.input_text, "What is the capital of France?")
        self.assertEqual(case.expected_output, "The capital of France is Paris.")
        self.assertEqual(case.dataset, self.dataset)
        self.assertEqual(case.context, {})  # Should default to empty dict
        self.assertIsNotNone(case.created_at)
    
    def test_evaluation_case_str_representation(self):
        """Test string representation of case"""
        case = EvaluationCase.objects.create(
            dataset=self.dataset,
            input_text="What is the capital of France?",
            expected_output="The capital of France is Paris."
        )
        expected_str = f"Case {case.id}: What is the capital of France?..."
        self.assertEqual(str(case), expected_str)
    
    def test_evaluation_case_dataset_relationship(self):
        """Test that case is properly linked to dataset"""
        case = EvaluationCase.objects.create(
            dataset=self.dataset,
            input_text="Test input",
            expected_output="Test output"
        )
        
        # Test forward relationship
        self.assertEqual(case.dataset, self.dataset)
        
        # Test reverse relationship
        self.assertIn(case, self.dataset.cases.all())
    
    def test_evaluation_case_context_json_field(self):
        """Test that context JSON field works correctly"""
        context_data = {"user_type": "premium", "language": "en"}
        case = EvaluationCase.objects.create(
            dataset=self.dataset,
            input_text="Test input",
            expected_output="Test output",
            context=context_data
        )
        
        # Retrieve from database and verify JSON is preserved
        saved_case = EvaluationCase.objects.get(id=case.id)
        self.assertEqual(saved_case.context, context_data)


class EvaluationRunModelTests(TestCase):
    """Test cases for EvaluationRun model"""
    
    def setUp(self):
        """Set up test data"""
        self.prompt_lab = PromptLab.objects.create(
            name="Test PromptLab",
            description="A test session for evaluation"
        )
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset"
        )
        self.prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="You are a helpful assistant.",
            version=1
        )
    
    def test_create_evaluation_run(self):
        """Test creating an evaluation run with valid data"""
        run = EvaluationRun.objects.create(
            dataset=self.dataset,
            prompt=self.prompt
        )
        
        self.assertEqual(run.dataset, self.dataset)
        self.assertEqual(run.prompt, self.prompt)
        self.assertEqual(run.status, 'pending')  # Should default to pending
        self.assertIsNone(run.overall_score)  # Should be None initially
        self.assertIsNotNone(run.started_at)
        self.assertIsNone(run.completed_at)  # Should be None initially
    
    def test_evaluation_run_default_status(self):
        """Test that run status defaults to 'pending'"""
        run = EvaluationRun.objects.create(
            dataset=self.dataset,
            prompt=self.prompt
        )
        self.assertEqual(run.status, 'pending')
    
    def test_evaluation_run_relationships(self):
        """Test that run has correct relationships with dataset and prompt"""
        run = EvaluationRun.objects.create(
            dataset=self.dataset,
            prompt=self.prompt
        )
        
        # Test forward relationships
        self.assertEqual(run.dataset, self.dataset)
        self.assertEqual(run.prompt, self.prompt)


class EvaluationResultModelTests(TestCase):
    """Test cases for EvaluationResult model"""
    
    def setUp(self):
        """Set up test data"""
        self.prompt_lab = PromptLab.objects.create(
            name="Test PromptLab",
            description="A test session for evaluation"
        )
        self.dataset = EvaluationDataset.objects.create(
            prompt_lab=self.prompt_lab,
            name="Test Dataset"
        )
        self.case = EvaluationCase.objects.create(
            dataset=self.dataset,
            input_text="What is 2+2?",
            expected_output="4"
        )
        self.prompt = SystemPrompt.objects.create(
            prompt_lab=self.prompt_lab,
            content="You are a helpful assistant.",
            version=1
        )
        self.run = EvaluationRun.objects.create(
            dataset=self.dataset,
            prompt=self.prompt
        )
    
    def test_create_evaluation_result(self):
        """Test creating an evaluation result with valid data"""
        result = EvaluationResult.objects.create(
            run=self.run,
            case=self.case,
            generated_output="The answer is 4",
            similarity_score=0.85,
            passed=True
        )
        
        self.assertEqual(result.run, self.run)
        self.assertEqual(result.case, self.case)
        self.assertEqual(result.generated_output, "The answer is 4")
        self.assertEqual(result.similarity_score, 0.85)
        self.assertTrue(result.passed)
        self.assertEqual(result.details, {})  # Should default to empty dict
    
    def test_evaluation_result_boolean_passed(self):
        """Test that passed field stores boolean correctly"""
        result = EvaluationResult.objects.create(
            run=self.run,
            case=self.case,
            generated_output="Wrong answer",
            similarity_score=0.3,
            passed=False
        )
        self.assertFalse(result.passed)
    
    def test_evaluation_result_details_json(self):
        """Test that details JSON field works correctly"""
        details_data = {"confidence": 0.9, "processing_time": 1.2}
        result = EvaluationResult.objects.create(
            run=self.run,
            case=self.case,
            generated_output="The answer is 4",
            similarity_score=0.85,
            passed=True,
            details=details_data
        )
        
        # Retrieve from database and verify JSON is preserved
        saved_result = EvaluationResult.objects.get(id=result.id)
        self.assertEqual(saved_result.details, details_data)
    
    def test_evaluation_result_str_representation(self):
        """Test string representation of result"""
        result = EvaluationResult.objects.create(
            run=self.run,
            case=self.case,
            generated_output="The answer is 4",
            similarity_score=0.85,
            passed=True
        )
        expected_str = f"Result {result.id}: 0.85 (PASS)"
        self.assertEqual(str(result), expected_str)