"""
Tests using real feedback processing implementations instead of mocks
Tests actual text analysis and learning algorithms
"""

import pytest
from datetime import datetime, timedelta
from app.services.human_feedback_integrator import (
    HumanFeedbackIntegrator,
    AcceptFeedbackProcessor,
    RejectFeedbackProcessor,
    EditFeedbackProcessor,
    IgnoreFeedbackProcessor,
    FeedbackSignal,
    UserPreferenceLearning
)
from core.models import Email, Draft, UserFeedback


class TestRealFeedbackProcessing:
    """Test actual feedback processing implementations"""

    @pytest.mark.asyncio
    async def test_accept_feedback_processor_real_implementation(self):
        """Test AcceptFeedbackProcessor with real implementation"""
        processor = AcceptFeedbackProcessor()
        
        # Create mock feedback object
        mock_draft = type('MockDraft', (), {'id': 123})()
        
        # Create mock reason ratings with proper liked attribute
        mock_rating_1 = type('MockRating', (), {'liked': True})()
        mock_rating_2 = type('MockRating', (), {'liked': True})()
        mock_rating_3 = type('MockRating', (), {'liked': False})()
        
        # Create mock QuerySet that returns the ratings
        def mock_all(self):
            return [mock_rating_1, mock_rating_2, mock_rating_3]
        
        mock_reason_ratings = type('MockQuerySet', (), {
            'all': mock_all
        })()
        
        mock_feedback = type('MockFeedback', (), {
            'action': 'accept',
            'reason': 'Great response, very professional',
            'reason_ratings': mock_reason_ratings,
            'user_id': 'test_user',
            'draft': mock_draft
        })()
        
        context = {
            'email_scenario': 'professional',
            'email_id': 1,
            'draft_id': 123
        }
        
        signal = await processor.process_feedback(mock_feedback, context)
        
        # Verify real calculation: base 1.0 + (2/3 liked ratings * 0.2) = 1.133
        assert isinstance(signal, FeedbackSignal)
        assert signal.action == 'accept'
        assert signal.email_scenario == 'professional'
        assert abs(signal.reward_value - 1.133) < 0.001  # Real calculation
        assert signal.confidence == 0.9
        assert signal.reasoning == 'Great response, very professional'

    @pytest.mark.asyncio
    async def test_reject_feedback_processor_real_implementation(self):
        """Test RejectFeedbackProcessor with real implementation"""
        processor = RejectFeedbackProcessor()
        
        mock_draft = type('MockDraft', (), {'id': 123})()
        mock_feedback = type('MockFeedback', (), {
            'action': 'reject',
            'reason': 'Response was too informal and lengthy',
            'user_id': 'test_user',
            'draft': mock_draft
        })()
        
        context = {
            'email_scenario': 'professional',
            'email_id': 1,
            'draft_id': 123
        }
        
        signal = await processor.process_feedback(mock_feedback, context)
        
        assert signal.action == 'reject'
        assert signal.reward_value == 0.0
        assert signal.confidence == 0.95
        # Should extract categories from reason using real logic
        assert 'reason_categories' in signal.metadata
        categories = signal.metadata['reason_categories']
        assert isinstance(categories, list)
        assert len(categories) > 0  # Should extract some categories

    @pytest.mark.asyncio 
    async def test_edit_feedback_processor_real_analysis(self):
        """Test EditFeedbackProcessor with real edit analysis"""
        processor = EditFeedbackProcessor()
        
        # Mock draft with content
        mock_draft = type('MockDraft', (), {
            'content': 'Hello, I hope this email finds you well.',
            'id': 123
        })()
        
        # Original: "Hello, I hope this email finds you well." = 8 words
        # Edited: "Hello, I hope this email finds you well. I wanted to provide additional information about our meeting." = ? words
        # Let me count: Hello(1) I(2) hope(3) this(4) email(5) finds(6) you(7) well(8) I(9) wanted(10) to(11) provide(12) additional(13) information(14) about(15) our(16) meeting(17) = 17 words
        mock_feedback = type('MockFeedback', (), {
            'action': 'edit',
            'reason': 'Good start but needs more detail',
            'edited_content': 'Hello, I hope this email finds you well. I wanted to provide additional information about our meeting.',
            'draft': mock_draft,
            'user_id': 'test_user'
        })()
        
        context = {
            'email_scenario': 'professional',
            'original_content': mock_draft.content
        }
        
        signal = await processor.process_feedback(mock_feedback, context)
        
        assert signal.action == 'edit'
        assert 0.4 <= signal.reward_value <= 0.8  # Partial reward based on real analysis
        
        # Check real edit analysis results
        edit_analysis = signal.metadata['edit_analysis']
        assert 'edit_ratio' in edit_analysis
        assert 'length_change' in edit_analysis
        assert edit_analysis['length_change'] > 0  # Text was expanded
        assert edit_analysis['original_length'] == 8  # Original word count
        assert edit_analysis['edited_length'] == 17  # Edited word count (corrected)

    def test_analyze_edit_changes_real_implementation(self):
        """Test _analyze_edit_changes with real text analysis"""
        processor = EditFeedbackProcessor()
        
        original = "Hello world this is a test"
        edited = "Hello world this is a much better test"
        
        analysis = processor._analyze_edit_changes(original, edited)
        
        # Verify real calculation
        original_words = set(original.split())  # {Hello, world, this, is, a, test}
        edited_words = set(edited.split())      # {Hello, world, this, is, a, much, better, test}
        intersection = original_words & edited_words  # {Hello, world, this, is, a, test}
        edit_ratio = 1.0 - (len(intersection) / max(len(original_words), 1))
        # edit_ratio = 1.0 - (6 / 6) = 0.0 (no words removed, only added)
        
        assert analysis['edit_ratio'] == 0.0
        assert analysis['length_change'] == 2  # 8 - 6 = 2 words added
        assert analysis['original_length'] == 6
        assert analysis['edited_length'] == 8

    def test_analyze_edit_changes_with_replacements(self):
        """Test edit analysis with word replacements"""
        processor = EditFeedbackProcessor()
        
        original = "The quick brown fox jumps"
        edited = "The fast red fox leaps"
        
        analysis = processor._analyze_edit_changes(original, edited)
        
        # Original: {The, quick, brown, fox, jumps} = 5 words
        # Edited: {The, fast, red, fox, leaps} = 5 words  
        # Intersection: {The, fox} = 2 words
        # edit_ratio = 1.0 - (2 / 5) = 0.6
        
        assert analysis['edit_ratio'] == 0.6
        assert analysis['length_change'] == 0  # Same length
        assert analysis['original_length'] == 5
        assert analysis['edited_length'] == 5


class TestRealTextAnalysis:
    """Test real text analysis functions"""

    def test_extract_features_real_implementation(self):
        """Test _extract_features with real feature extraction"""
        integrator = HumanFeedbackIntegrator()
        
        # Create mock email
        mock_email = type('MockEmail', (), {
            'scenario_type': 'professional'
        })()
        
        # Create mock draft with specific content for feature testing (11 words = short)
        mock_draft = type('MockDraft', (), {
            'content': 'Thank you for your email. Please let me know immediately.'  # 11 words
        })()
        
        features = integrator._extract_features(mock_email, mock_draft)
        
        # Verify real feature extraction
        assert features['scenario_professional'] == 1.0
        
        # Length analysis (11 words = short)
        assert 'length_short' in features
        assert features['length_short'] == 1.0
        
        # Tone analysis - should detect polite and urgent keywords
        assert 'tone_polite' in features  # "Thank you", "Please"
        assert features['tone_polite'] == 1.0
        assert 'tone_urgent' in features  # "immediately" 
        assert features['tone_urgent'] == 1.0

    def test_extract_features_short_length(self):
        """Test feature extraction for short content"""
        integrator = HumanFeedbackIntegrator()
        
        mock_email = type('MockEmail', (), {'scenario_type': 'casual'})()
        mock_draft = type('MockDraft', (), {
            'content': 'Yes, that works for me.'  # 5 words = short
        })()
        
        features = integrator._extract_features(mock_email, mock_draft)
        
        assert features['scenario_casual'] == 1.0
        assert 'length_short' in features
        assert features['length_short'] == 1.0
        assert 'length_medium' not in features
        assert 'length_long' not in features

    def test_extract_features_long_length(self):
        """Test feature extraction for long content"""
        integrator = HumanFeedbackIntegrator()
        
        mock_email = type('MockEmail', (), {'scenario_type': 'business'})()
        # Create content with 160 words (> 150 = long)
        long_content = ' '.join(['word'] * 160)
        mock_draft = type('MockDraft', (), {'content': long_content})()
        
        features = integrator._extract_features(mock_email, mock_draft)
        
        assert features['scenario_business'] == 1.0
        assert 'length_long' in features
        assert features['length_long'] == 1.0
        assert 'length_short' not in features
        assert 'length_medium' not in features

    def test_extract_features_no_draft(self):
        """Test feature extraction with no draft"""
        integrator = HumanFeedbackIntegrator()
        
        mock_email = type('MockEmail', (), {'scenario_type': 'support'})()
        
        features = integrator._extract_features(mock_email, None)
        
        # Should only have scenario feature
        assert features['scenario_support'] == 1.0
        assert len(features) == 1  # Only scenario feature


class TestRealPreferenceLearning:
    """Test real preference learning algorithms"""

    def test_calculate_trend_real_implementation(self):
        """Test _calculate_trend with real trend analysis"""
        integrator = HumanFeedbackIntegrator()
        
        # Test improving trend
        improving_performances = [0.5, 0.5, 0.6, 0.6, 0.7, 0.8, 0.8, 0.9, 0.9, 1.0]
        trend = integrator._calculate_trend(improving_performances)
        
        # Recent 5: [0.8, 0.8, 0.9, 0.9, 1.0] avg = 0.88
        # Older 5: [0.6, 0.6, 0.7, 0.8, 0.8] avg = 0.7
        # Difference: 0.88 - 0.7 = 0.18 > 0.1 = improving
        assert trend == 'improving'
        
        # Test declining trend  
        declining_performances = [1.0, 0.9, 0.9, 0.8, 0.8, 0.7, 0.6, 0.6, 0.5, 0.5]
        trend = integrator._calculate_trend(declining_performances)
        
        # Recent 5: [0.7, 0.6, 0.6, 0.5, 0.5] avg = 0.58
        # Older 5: [1.0, 0.9, 0.9, 0.8, 0.8] avg = 0.88
        # Difference: 0.58 - 0.88 = -0.3 < -0.1 = declining
        assert trend == 'declining'
        
        # Test stable trend
        stable_performances = [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7]
        trend = integrator._calculate_trend(stable_performances)
        
        # Recent 5: [0.7, 0.7, 0.7, 0.7, 0.7] avg = 0.7
        # Older 5: [0.7, 0.7, 0.7, 0.7, 0.7] avg = 0.7  
        # Difference: 0.0 (within ±0.1) = stable
        assert trend == 'stable'

    def test_calculate_trend_insufficient_data(self):
        """Test trend calculation with insufficient data"""
        integrator = HumanFeedbackIntegrator()
        
        short_performances = [0.5, 0.6, 0.7]  # Only 3 data points
        trend = integrator._calculate_trend(short_performances)
        
        assert trend == 'insufficient_data'

    def test_calculate_trend_edge_cases(self):
        """Test trend calculation edge cases"""
        integrator = HumanFeedbackIntegrator()
        
        # Test exactly at threshold (recent avg = older avg + 0.1)
        threshold_performances = [0.6, 0.6, 0.6, 0.6, 0.6, 0.7, 0.7, 0.7, 0.7, 0.7]
        trend = integrator._calculate_trend(threshold_performances)
        
        # Recent 5: [0.6, 0.7, 0.7, 0.7, 0.7] avg = 0.68
        # Older 5: [0.6, 0.6, 0.6, 0.6, 0.6] avg = 0.6
        # Difference: 0.68 - 0.6 = 0.08 < 0.1 = stable (not improving)
        assert trend == 'stable'


class TestRealDualLLMCoordinatorPerformance:
    """Test real DualLLMCoordinator performance tracking functions"""

    def test_update_performance_history_real_implementation(self):
        """Test _update_performance_history with real implementation"""
        from app.services.dual_llm_coordinator import DualLLMCoordinator
        from unittest.mock import AsyncMock
        
        # Create coordinator with mocked dependencies
        mock_rewriter = AsyncMock()
        mock_task_llm = AsyncMock()
        mock_reward_aggregator = AsyncMock()
        mock_meta_prompt_manager = AsyncMock()
        
        coordinator = DualLLMCoordinator(
            mock_rewriter,
            mock_task_llm,
            mock_reward_aggregator,
            mock_meta_prompt_manager
        )
        
        # Test real performance history tracking
        scenario = "professional"
        prompt_id = 123
        performance_metrics = {
            "overall_quality": 0.85,
            "relevance": 0.9,
            "clarity": 0.8,
            "professionalism": 0.9,
            "completeness": 0.8
        }
        
        # Test first update
        coordinator._update_performance_history(scenario, prompt_id, performance_metrics, False)
        
        key = f"{scenario}_{prompt_id}"
        assert key in coordinator.performance_history
        assert coordinator.performance_history[key] == [0.85]  # Only overall_quality stored
        
        # Test multiple updates
        coordinator._update_performance_history(scenario, prompt_id, {"overall_quality": 0.75}, True)
        coordinator._update_performance_history(scenario, prompt_id, {"overall_quality": 0.95}, False)
        
        assert coordinator.performance_history[key] == [0.85, 0.75, 0.95]
        
    def test_performance_history_size_limit_real_implementation(self):
        """Test real implementation of performance history size limiting"""
        from app.services.dual_llm_coordinator import DualLLMCoordinator
        from unittest.mock import AsyncMock
        
        coordinator = DualLLMCoordinator(
            AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock()
        )
        
        scenario = "business"
        prompt_id = 456
        
        # Add 25 entries to test the 20-entry limit
        for i in range(25):
            metrics = {"overall_quality": i / 25.0}
            coordinator._update_performance_history(scenario, prompt_id, metrics, False)
        
        key = f"{scenario}_{prompt_id}"
        
        # Should only keep last 20 entries
        assert len(coordinator.performance_history[key]) == 20
        
        # Should keep the most recent entries (5-24, values 0.2-0.96)
        expected_values = [i / 25.0 for i in range(5, 25)]
        assert coordinator.performance_history[key] == expected_values
        
        # Verify the values are correct
        assert coordinator.performance_history[key][0] == 5 / 25.0  # 0.2
        assert coordinator.performance_history[key][-1] == 24 / 25.0  # 0.96

    @pytest.mark.asyncio
    async def test_evaluate_generation_performance_real_calculation(self):
        """Test real implementation of _evaluate_generation_performance calculation"""
        from app.services.dual_llm_coordinator import DualLLMCoordinator
        from unittest.mock import AsyncMock
        
        # Create mock task LLM that returns known scores
        mock_task_llm = AsyncMock()
        mock_task_llm.evaluate_response_quality.side_effect = [
            {"relevance": 0.8, "clarity": 0.9, "professionalism": 0.7, "completeness": 0.8},
            {"relevance": 0.9, "clarity": 0.8, "professionalism": 0.9, "completeness": 0.9}
        ]
        
        coordinator = DualLLMCoordinator(
            AsyncMock(), mock_task_llm, AsyncMock(), AsyncMock()
        )
        
        # Create mock objects
        mock_email = type('MockEmail', (), {'id': 1, 'scenario_type': 'professional'})()
        mock_prompt = type('MockPrompt', (), {'id': 1, 'content': 'Test prompt'})()
        mock_draft_1 = type('MockDraft', (), {'content': 'First draft content'})()
        mock_draft_2 = type('MockDraft', (), {'content': 'Second draft content'})()
        
        drafts = [mock_draft_1, mock_draft_2]
        
        # Call real implementation
        metrics = await coordinator._evaluate_generation_performance(
            mock_email, drafts, mock_prompt
        )
        
        # Verify real calculations
        # Draft 1: (0.8 + 0.9 + 0.7 + 0.8) / 4 = 3.2 / 4 = 0.8
        # Draft 2: (0.9 + 0.8 + 0.9 + 0.9) / 4 = 3.5 / 4 = 0.875
        # Overall: (0.8 + 0.875) / 2 = 1.675 / 2 = 0.8375
        
        assert "overall_quality" in metrics
        assert abs(metrics["overall_quality"] - 0.8375) < 0.001
        
        assert "best_draft_quality" in metrics
        assert abs(metrics["best_draft_quality"] - 0.875) < 0.001
        
        assert "consistency" in metrics
        # Consistency = 1 - abs(0.8 - 0.875) = 1 - 0.075 = 0.925
        assert abs(metrics["consistency"] - 0.925) < 0.001
        
        assert metrics["num_drafts"] == 2

    @pytest.mark.asyncio
    async def test_evaluate_generation_performance_empty_drafts(self):
        """Test real implementation with empty drafts list"""
        from app.services.dual_llm_coordinator import DualLLMCoordinator
        from unittest.mock import AsyncMock
        
        coordinator = DualLLMCoordinator(
            AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock()
        )
        
        mock_email = type('MockEmail', (), {})()
        mock_prompt = type('MockPrompt', (), {})()
        
        metrics = await coordinator._evaluate_generation_performance(
            mock_email, [], mock_prompt
        )
        
        # Should return minimal metrics for empty drafts
        assert metrics == {"overall_quality": 0.0}

    @pytest.mark.asyncio
    async def test_should_rewrite_prompt_real_decision_logic(self):
        """Test real implementation of _should_rewrite_prompt decision logic"""
        from app.services.dual_llm_coordinator import DualLLMCoordinator, DraftGenerationRequest
        from unittest.mock import AsyncMock
        
        coordinator = DualLLMCoordinator(
            AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock(),
            rewrite_threshold=0.6
        )
        
        # Create mock request
        mock_email = type('MockEmail', (), {'scenario_type': 'professional'})()
        mock_prompt = type('MockPrompt', (), {'id': 123})()
        request = DraftGenerationRequest(
            email=mock_email,
            prompt=mock_prompt,
            user_preferences=[]
        )
        
        # Test 1: New prompt/scenario combination (no history) - should rewrite
        should_rewrite = await coordinator._should_rewrite_prompt(request)
        assert should_rewrite is True
        
        # Test 2: Good recent performance (above threshold) - should not rewrite
        key = f"{mock_email.scenario_type}_{mock_prompt.id}"
        coordinator.performance_history[key] = [0.7, 0.8, 0.9, 0.8, 0.85]  # avg = 0.826
        
        should_rewrite = await coordinator._should_rewrite_prompt(request)
        assert should_rewrite is False
        
        # Test 3: Poor recent performance (below threshold) - should rewrite
        coordinator.performance_history[key] = [0.3, 0.4, 0.5, 0.6, 0.4]  # avg = 0.44
        
        should_rewrite = await coordinator._should_rewrite_prompt(request)
        assert should_rewrite is True
        
        # Test 4: Performance exactly at threshold - should not rewrite
        coordinator.performance_history[key] = [0.6, 0.6, 0.6, 0.6, 0.6]  # avg = 0.6
        
        should_rewrite = await coordinator._should_rewrite_prompt(request)
        assert should_rewrite is False
        
        # Test 5: Limited history (less than 5 entries) - uses available entries
        coordinator.performance_history[key] = [0.5, 0.4]  # avg = 0.45
        
        should_rewrite = await coordinator._should_rewrite_prompt(request)
        assert should_rewrite is True


class TestRealFeedbackIntegration:
    """Test real feedback integration algorithms"""

    @pytest.mark.asyncio
    async def test_real_feedback_processing_pipeline(self):
        """Test complete feedback processing pipeline with real implementations"""
        integrator = HumanFeedbackIntegrator()
        
        # Create mock feedback with various types
        mock_email = type('MockEmail', (), {
            'id': 1,
            'scenario_type': 'professional'
        })()
        
        mock_draft = type('MockDraft', (), {
            'id': 1,
            'content': 'Thank you for your inquiry. Please let me know if you need assistance.',
            'email': mock_email
        })()
        
        # Test accept feedback
        accept_feedback = type('MockFeedback', (), {
            'action': 'accept',
            'reason': 'Professional and helpful',
            'draft': mock_draft,
            'user_id': 'user123'
        })()
        
        # Process feedback using real implementations
        signal = await integrator.process_user_feedback(accept_feedback, mock_email, mock_draft)
        
        # Verify real processing results
        assert isinstance(signal, FeedbackSignal)
        assert signal.action == 'accept'
        assert signal.email_scenario == 'professional'
        assert signal.reward_value > 0.8  # Should be high for accept
        assert signal.user_id == 'user123'
        
        # Verify the integrator stored the signal
        assert len(integrator.feedback_history) == 1
        assert integrator.feedback_history[0] == signal

    def test_real_preference_vector_updates(self):
        """Test real preference vector learning"""
        integrator = HumanFeedbackIntegrator()
        
        # Simulate learning from feedback
        mock_email = type('MockEmail', (), {'scenario_type': 'professional'})()
        mock_draft = type('MockDraft', (), {
            'content': 'Please find the requested information attached.'
        })()
        
        features = integrator._extract_features(mock_email, mock_draft)
        
        # Test that features are extracted correctly for learning
        assert isinstance(features, dict)
        assert all(isinstance(v, (int, float)) for v in features.values())
        assert all(v >= 0 for v in features.values())  # Non-negative feature values
        
        # Features should be meaningful for learning
        assert len(features) > 1  # Should extract multiple features
        assert 'scenario_professional' in features
        
    def test_mathematical_accuracy_of_real_functions(self):
        """Test mathematical accuracy of real calculation functions"""
        processor = EditFeedbackProcessor()
        
        # Test edit ratio calculation with known values
        original = "a b c d e"
        edited = "a b f g h"
        
        analysis = processor._analyze_edit_changes(original, edited)
        
        # Manual calculation:
        # Original words: {a, b, c, d, e} = 5
        # Edited words: {a, b, f, g, h} = 5
        # Intersection: {a, b} = 2
        # Edit ratio: 1.0 - (2/5) = 0.6
        
        assert abs(analysis['edit_ratio'] - 0.6) < 0.001
        assert analysis['length_change'] == 0
        assert analysis['original_length'] == 5
        assert analysis['edited_length'] == 5