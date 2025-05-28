import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from asgiref.sync import sync_to_async
from app.services.llm_provider import OpenAIProvider
from core.models import Email, SystemPrompt, UserPreference, Draft, DraftReason


@pytest_asyncio.fixture
async def system_prompt():
    # Use get_or_create to avoid unique constraint issues
    prompt, created = await sync_to_async(SystemPrompt.objects.get_or_create)(
        version=1,
        defaults={
            'content': "You are a helpful email assistant.",
            'is_active': True
        }
    )
    return prompt

@pytest_asyncio.fixture
async def test_email():
    return await sync_to_async(Email.objects.create)(
        subject="Test Subject",
        body="Test email body",
        sender="test@example.com",
        scenario_type="professional"
    )

@pytest_asyncio.fixture
async def user_prefs():
    pref, created = await sync_to_async(UserPreference.objects.get_or_create)(
        key="tone",
        defaults={
            'value': "professional",
            'description': "Professional communication style"
        }
    )
    return [pref]

@pytest.fixture
def llm_provider():
    return OpenAIProvider("test-api-key")


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_generate_drafts_interface(llm_provider, test_email, system_prompt, user_prefs):
    """Test that generate_drafts method exists and has correct signature"""
    # Mock the OpenAI API call
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '''
    {
        "drafts": [
            {
                "content": "Thank you for your email. I will review and get back to you.",
                "reasons": [
                    {"text": "Professional tone", "confidence": 0.9},
                    {"text": "Acknowledges receipt", "confidence": 0.8}
                ]
            },
            {
                "content": "I appreciate you reaching out. Let me look into this and respond soon.",
                "reasons": [
                    {"text": "Friendly but professional", "confidence": 0.8}
                ]
            }
        ]
    }
    '''
    
    with patch.object(llm_provider.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        result = await llm_provider.generate_drafts(test_email, system_prompt, user_prefs)
        
        assert isinstance(result, list)
        assert len(result) >= 2
        assert all(isinstance(draft, Draft) for draft in result)


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_optimize_prompt_interface(llm_provider, system_prompt):
    """Test that optimize_prompt method exists and has correct signature"""
    # Mock the OpenAI API call
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Improved system prompt based on feedback."
    
    with patch.object(llm_provider.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        result = await llm_provider.optimize_prompt(system_prompt, [], [])
        
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.django_db  
@pytest.mark.asyncio
async def test_generate_drafts_returns_list(llm_provider, test_email, system_prompt, user_prefs):
    """Test that generate_drafts returns a list of Draft objects"""
    # Mock the OpenAI API call with valid JSON
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '''
    {
        "drafts": [
            {
                "content": "First draft response",
                "reasons": [
                    {"text": "Clear and concise", "confidence": 0.9}
                ]
            },
            {
                "content": "Second draft response", 
                "reasons": [
                    {"text": "Professional tone", "confidence": 0.8}
                ]
            }
        ]
    }
    '''
    
    with patch.object(llm_provider.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        result = await llm_provider.generate_drafts(test_email, system_prompt, user_prefs)
        
        assert isinstance(result, list)
        assert len(result) == 2
        # Check that drafts have reasoning
        for draft in result:
            reasons = await sync_to_async(list)(draft.reasons.all())
            assert len(reasons) >= 1


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_optimize_prompt_returns_string(llm_provider, system_prompt):
    """Test that optimize_prompt returns a string"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "You are an enhanced email assistant."
    
    with patch.object(llm_provider.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        result = await llm_provider.optimize_prompt(system_prompt, [], [])
        
        assert isinstance(result, str)
        assert "enhanced" in result.lower()