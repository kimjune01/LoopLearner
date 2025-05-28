import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from asgiref.sync import sync_to_async
from app.services.human_feedback_integrator import (
    HumanFeedbackIntegrator,
    FeedbackSignal,
    UserPreferenceLearning,
    AcceptFeedbackProcessor,
    RejectFeedbackProcessor,
    EditFeedbackProcessor,
    IgnoreFeedbackProcessor
)
from core.models import UserFeedback, Draft, Email, SystemPrompt


@pytest_asyncio.fixture
async def test_email():
    """Test email for feedback integration"""
    return await sync_to_async(Email.objects.create)(
        subject="Feedback Integration Test",
        body="This is a test email for feedback integration.",
        sender="feedback@test.com",
        scenario_type="professional"
    )


@pytest_asyncio.fixture
async def system_prompt():
    """Test system prompt"""
    prompt, created = await sync_to_async(SystemPrompt.objects.get_or_create)(
        version=40,  # Use different version to avoid conflicts
        defaults={
            'content': "You are a helpful feedback test assistant.",
            'is_active': True
        }
    )
    return prompt


@pytest_asyncio.fixture
async def test_draft(test_email, system_prompt):
    """Test draft for feedback"""
    return await sync_to_async(Draft.objects.create)(
        email=test_email,
        content="This is a test draft response for feedback testing.",
        system_prompt=system_prompt
    )


@pytest_asyncio.fixture
async def accept_feedback(test_draft):
    """Mock accept feedback"""
    feedback = type('MockFeedback', (), {
        'action': 'accept',
        'reason': 'Excellent response, very professional',
        'draft': test_draft,
        'edited_content': None,
        'reason_ratings': type('MockQuerySet', (), {
            'all': lambda self: [
                type('MockRating', (), {'liked': True})(),
                type('MockRating', (), {'liked': True})(),
                type('MockRating', (), {'liked': False})()
            ]
        })()
    })()
    return feedback


@pytest_asyncio.fixture
async def reject_feedback(test_draft):
    """Mock reject feedback"""
    feedback = type('MockFeedback', (), {
        'action': 'reject',
        'reason': 'Too formal and lengthy for this context',
        'draft': test_draft,
        'edited_content': None,
        'reason_ratings': type('MockQuerySet', (), {
            'all': lambda self: []
        })()
    })()
    return feedback


@pytest_asyncio.fixture
async def edit_feedback(test_draft):
    """Mock edit feedback"""
    feedback = type('MockFeedback', (), {
        'action': 'edit',
        'reason': 'Good but needs minor adjustments',
        'draft': test_draft,
        'edited_content': 'This is a revised draft response that is more concise.',
        'reason_ratings': type('MockQuerySet', (), {
            'all': lambda self: []
        })()
    })()
    return feedback


@pytest_asyncio.fixture
async def ignore_feedback(test_draft):
    """Mock ignore feedback"""
    feedback = type('MockFeedback', (), {
        'action': 'ignore',
        'reason': '',
        'draft': test_draft,
        'edited_content': None,
        'reason_ratings': type('MockQuerySet', (), {
            'all': lambda self: []
        })()
    })()
    return feedback


@pytest.fixture
def feedback_integrator():
    """Human feedback integrator instance"""
    return HumanFeedbackIntegrator()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_feedback_integrator_initialization(feedback_integrator):
    """Test feedback integrator initialization"""
    assert len(feedback_integrator.feedback_processors) == 4
    assert 'accept' in feedback_integrator.feedback_processors
    assert 'reject' in feedback_integrator.feedback_processors
    assert 'edit' in feedback_integrator.feedback_processors
    assert 'ignore' in feedback_integrator.feedback_processors
    
    assert isinstance(feedback_integrator.feedback_processors['accept'], AcceptFeedbackProcessor)
    assert isinstance(feedback_integrator.feedback_processors['reject'], RejectFeedbackProcessor)
    assert isinstance(feedback_integrator.feedback_processors['edit'], EditFeedbackProcessor)
    assert isinstance(feedback_integrator.feedback_processors['ignore'], IgnoreFeedbackProcessor)
    
    assert feedback_integrator.user_preferences == {}
    assert feedback_integrator.feedback_history == []
    assert feedback_integrator.scenario_performance == {}


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_accept_feedback_processor(accept_feedback):
    """Test accept feedback processing"""
    processor = AcceptFeedbackProcessor()
    
    context = {
        'email_scenario': 'professional',
        'email_id': 1,
        'draft_id': 123
    }
    
    signal = await processor.process_feedback(accept_feedback, context)
    
    assert isinstance(signal, FeedbackSignal)
    assert signal.action == 'accept'
    assert signal.email_scenario == 'professional'
    assert signal.reward_value > 1.0  # Should get bonus for positive reason ratings
    assert signal.confidence == 0.9
    assert signal.reasoning == accept_feedback.reason


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_reject_feedback_processor(reject_feedback):
    """Test reject feedback processing"""
    processor = RejectFeedbackProcessor()
    
    context = {
        'email_scenario': 'professional',
        'email_id': 1,
        'draft_id': 123
    }
    
    signal = await processor.process_feedback(reject_feedback, context)
    
    assert signal.action == 'reject'
    assert signal.reward_value == 0.0
    assert signal.confidence == 0.95
    assert 'tone' in signal.metadata['reason_categories']  # Should extract from reason
    assert 'length' in signal.metadata['reason_categories']


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_edit_feedback_processor(edit_feedback):
    """Test edit feedback processing"""
    processor = EditFeedbackProcessor()
    
    context = {
        'email_scenario': 'professional',
        'original_content': edit_feedback.draft.content
    }
    
    signal = await processor.process_feedback(edit_feedback, context)
    
    assert signal.action == 'edit'
    assert 0.4 <= signal.reward_value <= 0.8  # Partial reward
    assert signal.confidence == 0.7
    assert 'edit_analysis' in signal.metadata
    assert signal.metadata['edited_content'] == edit_feedback.edited_content


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_ignore_feedback_processor(ignore_feedback):
    """Test ignore feedback processing"""
    processor = IgnoreFeedbackProcessor()
    
    context = {
        'email_scenario': 'professional'
    }
    
    signal = await processor.process_feedback(ignore_feedback, context)
    
    assert signal.action == 'ignore'
    assert signal.reward_value == 0.3
    assert signal.confidence == 0.4


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_edit_analysis(edit_feedback):
    """Test edit change analysis"""
    processor = EditFeedbackProcessor()
    
    original = "This is a long original draft response for testing purposes."
    edited = "This is a shorter edited response."
    
    analysis = processor._analyze_edit_changes(original, edited)
    
    assert 'edit_ratio' in analysis
    assert 'length_change' in analysis
    assert 'original_length' in analysis
    assert 'edited_length' in analysis
    
    assert analysis['original_length'] == 10  # Word count
    assert analysis['edited_length'] == 6
    assert analysis['length_change'] == -4


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_process_user_feedback_accept(feedback_integrator, accept_feedback, test_email, test_draft):
    """Test processing accept feedback through integrator"""
    signal = await feedback_integrator.process_user_feedback(
        accept_feedback,
        test_email,
        test_draft
    )
    
    assert isinstance(signal, FeedbackSignal)
    assert signal.action == 'accept'
    assert len(feedback_integrator.feedback_history) == 1
    assert feedback_integrator.feedback_history[0] == signal


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_process_user_feedback_reject(feedback_integrator, reject_feedback, test_email, test_draft):
    """Test processing reject feedback through integrator"""
    signal = await feedback_integrator.process_user_feedback(
        reject_feedback,
        test_email,
        test_draft
    )
    
    assert signal.action == 'reject'
    assert signal.reward_value == 0.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_user_preference_learning_accept(feedback_integrator, accept_feedback, test_email, test_draft):
    """Test user preference learning from accept feedback"""
    # Add user_id to feedback for preference learning
    accept_feedback.user_id = "test_user_123"
    
    await feedback_integrator.process_user_feedback(
        accept_feedback,
        test_email,
        test_draft
    )
    
    # Check user preferences were created
    assert "test_user_123" in feedback_integrator.user_preferences
    user_prefs = feedback_integrator.user_preferences["test_user_123"]
    assert isinstance(user_prefs, UserPreferenceLearning)
    assert user_prefs.interaction_count == 1


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_user_preference_learning_reject(feedback_integrator, reject_feedback, test_email, test_draft):
    """Test user preference learning from reject feedback"""
    reject_feedback.user_id = "test_user_123"
    
    await feedback_integrator.process_user_feedback(
        reject_feedback,
        test_email,
        test_draft
    )
    
    user_prefs = feedback_integrator.user_preferences["test_user_123"]
    
    # Should have negative preferences for features that led to rejection
    assert len(user_prefs.preference_vector) > 0
    
    # Should extract negative preferences from reason
    assert any(value < 0 for value in user_prefs.preference_vector.values())


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_feature_extraction(feedback_integrator, test_email, test_draft):
    """Test feature extraction from email and draft"""
    features = feedback_integrator._extract_features(test_email, test_draft)
    
    assert f'scenario_{test_email.scenario_type}' in features
    assert features[f'scenario_{test_email.scenario_type}'] == 1.0
    
    # Should extract length features
    word_count = len(test_draft.content.split())
    if word_count < 50:
        assert 'length_short' in features
    elif word_count > 150:
        assert 'length_long' in features
    else:
        assert 'length_medium' in features


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_negative_preference_extraction(feedback_integrator):
    """Test extraction of negative preferences from rejection reasons"""
    user_prefs = UserPreferenceLearning(
        user_id="test_user",
        preference_vector={},
        confidence_scores={},
        last_updated=datetime.now(),
        interaction_count=1
    )
    
    await feedback_integrator._extract_negative_preferences(
        user_prefs,
        "Response was too formal and too long for this context"
    )
    
    # Should extract negative preferences
    assert 'tone_formal' in user_prefs.preference_vector
    assert user_prefs.preference_vector['tone_formal'] < 0
    assert 'length_long' in user_prefs.preference_vector
    assert user_prefs.preference_vector['length_long'] < 0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_learn_from_edit(feedback_integrator):
    """Test learning from user edits"""
    user_prefs = UserPreferenceLearning(
        user_id="test_user",
        preference_vector={},
        confidence_scores={},
        last_updated=datetime.now(),
        interaction_count=1
    )
    
    original = "This is a very long original response that goes on and on with lots of details."
    edited = "This is a concise edited response."
    
    await feedback_integrator._learn_from_edit(user_prefs, original, edited)
    
    # Should learn length preference (user shortened response significantly)
    assert 'length_preference' in user_prefs.preference_vector
    assert user_prefs.preference_vector['length_preference'] < 0  # Prefers shorter


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_scenario_performance_tracking(feedback_integrator, accept_feedback, test_email, test_draft):
    """Test scenario performance tracking"""
    await feedback_integrator.process_user_feedback(
        accept_feedback,
        test_email,
        test_draft
    )
    
    scenario = test_email.scenario_type
    assert scenario in feedback_integrator.scenario_performance
    assert len(feedback_integrator.scenario_performance[scenario]) == 1


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_scenario_performance_limit(feedback_integrator, test_email, test_draft):
    """Test scenario performance history size limit"""
    # Add many feedback signals
    for i in range(60):  # More than the 50 limit
        feedback = type('MockFeedback', (), {
            'action': 'accept',
            'reason': f'Feedback {i}',
            'draft': test_draft,
            'user_id': None
        })()
        
        await feedback_integrator.process_user_feedback(feedback, test_email, test_draft)
    
    scenario = test_email.scenario_type
    # Should keep only last 50
    assert len(feedback_integrator.scenario_performance[scenario]) == 50


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_get_user_preferences(feedback_integrator, accept_feedback, test_email, test_draft):
    """Test retrieving user preferences"""
    # Add user with preferences
    accept_feedback.user_id = "test_user_123"
    await feedback_integrator.process_user_feedback(accept_feedback, test_email, test_draft)
    
    # Get preferences
    prefs = await feedback_integrator.get_user_preferences("test_user_123")
    assert prefs is not None
    assert isinstance(prefs, dict)
    
    # Non-existent user
    no_prefs = await feedback_integrator.get_user_preferences("nonexistent_user")
    assert no_prefs is None


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_get_feedback_batch_for_training(feedback_integrator, test_email, test_draft):
    """Test getting feedback batch for RL training"""
    # Add various feedback with different confidence levels
    feedback_data = [
        ('accept', 0.9, 'Great response'),
        ('reject', 0.95, 'Poor response'),
        ('edit', 0.7, 'Okay response'),
        ('ignore', 0.4, ''),  # Below confidence threshold
        ('accept', 0.8, 'Good response')
    ]
    
    for action, confidence, reason in feedback_data:
        feedback = type('MockFeedback', (), {
            'action': action,
            'reason': reason,
            'draft': test_draft,
            'user_id': None,
            'edited_content': 'Edited content' if action == 'edit' else None,
            'reason_ratings': type('MockQuerySet', (), {
                'all': lambda self: []
            })()
        })()
        
        signal = await feedback_integrator.process_user_feedback(feedback, test_email, test_draft)
        # Manually set confidence for test
        signal.confidence = confidence
    
    # Get training batch with min confidence 0.5
    batch = await feedback_integrator.get_feedback_batch_for_training(min_confidence=0.5)
    
    # Should exclude ignore feedback (confidence 0.4)
    assert len(batch) == 4
    assert all(signal.confidence >= 0.5 for signal in batch)


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_get_scenario_performance_summary(feedback_integrator, test_email, test_draft):
    """Test getting scenario performance summary"""
    # Add feedback for performance tracking
    rewards = [0.8, 0.9, 0.7, 0.85, 0.6, 0.9, 0.8, 0.75, 0.8, 0.9, 0.85, 0.7]
    
    for i, reward in enumerate(rewards):
        feedback = type('MockFeedback', (), {
            'action': 'accept',
            'reason': f'Feedback {i}',
            'draft': test_draft,
            'user_id': None,
            'edited_content': None,
            'reason_ratings': type('MockQuerySet', (), {
                'all': lambda self: []
            })()
        })()
        
        signal = await feedback_integrator.process_user_feedback(feedback, test_email, test_draft)
        signal.reward_value = reward  # Set reward for test
        # Update the scenario performance with the modified reward
        feedback_integrator.scenario_performance[test_email.scenario_type][-1] = reward
    
    summary = await feedback_integrator.get_scenario_performance_summary()
    
    scenario = test_email.scenario_type
    assert scenario in summary
    
    scenario_data = summary[scenario]
    assert 'average_reward' in scenario_data
    assert 'recent_average' in scenario_data
    assert 'total_feedback' in scenario_data
    assert 'trend' in scenario_data
    
    assert scenario_data['total_feedback'] == len(rewards)
    assert 0.0 <= scenario_data['average_reward'] <= 1.0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_performance_trend_calculation(feedback_integrator):
    """Test performance trend calculation"""
    # Test improving trend
    improving_performance = [0.5, 0.6, 0.7, 0.8, 0.9, 0.8, 0.9, 0.95, 0.9, 0.95]
    trend = feedback_integrator._calculate_trend(improving_performance)
    assert trend == 'improving'
    
    # Test declining trend
    declining_performance = [0.9, 0.8, 0.85, 0.8, 0.7, 0.6, 0.5, 0.4, 0.5, 0.4]
    trend = feedback_integrator._calculate_trend(declining_performance)
    assert trend == 'declining'
    
    # Test stable trend
    stable_performance = [0.8, 0.8, 0.75, 0.8, 0.85, 0.8, 0.8, 0.75, 0.8, 0.8]
    trend = feedback_integrator._calculate_trend(stable_performance)
    assert trend == 'stable'
    
    # Test insufficient data
    insufficient_data = [0.8, 0.9]
    trend = feedback_integrator._calculate_trend(insufficient_data)
    assert trend == 'insufficient_data'


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_get_integration_metrics(feedback_integrator, test_email, test_draft):
    """Test getting integration metrics"""
    # Add various types of feedback
    feedback_types = ['accept', 'reject', 'edit', 'ignore', 'accept']
    
    for action in feedback_types:
        feedback = type('MockFeedback', (), {
            'action': action,
            'reason': f'{action} feedback',
            'draft': test_draft,
            'user_id': f'user_{action}' if action == 'accept' else None,
            'edited_content': 'Edited content' if action == 'edit' else None,
            'reason_ratings': type('MockQuerySet', (), {
                'all': lambda self: []
            })()
        })()
        
        await feedback_integrator.process_user_feedback(feedback, test_email, test_draft)
    
    metrics = await feedback_integrator.get_integration_metrics()
    
    assert metrics['total_signals'] == 5
    assert 'action_distribution' in metrics
    assert metrics['action_distribution']['accept'] == 2
    assert metrics['action_distribution']['reject'] == 1
    assert 'average_confidence' in metrics
    assert 'unique_users' in metrics
    assert 'scenarios_tracked' in metrics


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_feedback_signal_dataclass():
    """Test FeedbackSignal dataclass"""
    signal = FeedbackSignal(
        user_id="test_user",
        email_scenario="professional",
        action="accept",
        reward_value=0.9,
        confidence=0.8,
        reasoning="Good response",
        metadata={"draft_id": 123}
    )
    
    assert signal.user_id == "test_user"
    assert signal.email_scenario == "professional"
    assert signal.action == "accept"
    assert signal.reward_value == 0.9
    assert signal.confidence == 0.8
    assert signal.reasoning == "Good response"
    assert signal.metadata["draft_id"] == 123


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_user_preference_learning_dataclass():
    """Test UserPreferenceLearning dataclass"""
    now = datetime.now()
    learning = UserPreferenceLearning(
        user_id="test_user",
        preference_vector={"tone_formal": 0.5, "length_short": -0.3},
        confidence_scores={"tone_formal": 0.8, "length_short": 0.6},
        last_updated=now,
        interaction_count=5
    )
    
    assert learning.user_id == "test_user"
    assert learning.preference_vector["tone_formal"] == 0.5
    assert learning.confidence_scores["tone_formal"] == 0.8
    assert learning.last_updated == now
    assert learning.interaction_count == 5