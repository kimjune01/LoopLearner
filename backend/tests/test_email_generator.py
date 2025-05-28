import pytest
from django.test import TestCase
from django.db import transaction
from asgiref.sync import sync_to_async
from app.services.email_generator import SyntheticEmailGenerator
from core.models import Email


@pytest.mark.django_db
@pytest.mark.asyncio
class TestEmailGenerator:
    """Test cases for email generator interface"""
    
    def setup_method(self):
        self.generator = SyntheticEmailGenerator()
    
    async def test_generate_synthetic_email_interface(self):
        """Test that generate_synthetic_email method exists and works"""
        result = await self.generator.generate_synthetic_email("professional")
        assert isinstance(result, Email)
        assert result.id is not None
        assert result.subject is not None
        assert result.body is not None
        assert result.sender is not None
        assert result.scenario_type == "professional"
        assert result.is_synthetic is True
    
    async def test_generate_batch_emails_interface(self):
        """Test that generate_batch_emails method exists and works"""
        count = 3
        result = await self.generator.generate_batch_emails(count, ["professional", "casual"])
        assert isinstance(result, list)
        assert len(result) == count
        assert all(isinstance(email, Email) for email in result)
    
    async def test_generate_synthetic_email_returns_email_message(self):
        """Test that generates valid Email model instance"""
        result = await self.generator.generate_synthetic_email("professional")
        assert isinstance(result, Email)
        assert result.id is not None
        assert result.subject is not None
        assert result.body is not None
        assert result.sender is not None
        assert result.scenario_type == "professional"
        assert result.is_synthetic is True
    
    async def test_generate_batch_emails_returns_list(self):
        """Test that batch generation returns correct count"""
        count = 3
        result = await self.generator.generate_batch_emails(count, ["professional"])
        assert isinstance(result, list)
        assert len(result) == count
        assert all(isinstance(email, Email) for email in result)
        
        # Verify all emails are saved to database
        total_emails = await sync_to_async(Email.objects.count)()
        assert total_emails >= count