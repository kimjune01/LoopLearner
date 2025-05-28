from abc import ABC, abstractmethod
from typing import List
from ..models.email import EmailMessage


class EmailGenerator(ABC):
    """Abstract interface for generating synthetic emails"""
    
    @abstractmethod
    async def generate_synthetic_email(self, scenario_type: str = "random") -> EmailMessage:
        """Generate a synthetic email for testing"""
        pass
    
    @abstractmethod
    async def generate_batch_emails(self, count: int, scenarios: List[str]) -> List[EmailMessage]:
        """Generate multiple synthetic emails"""
        pass


class SyntheticEmailGenerator(EmailGenerator):
    """Concrete implementation for synthetic email generation"""
    
    async def generate_synthetic_email(self, scenario_type: str = "random") -> EmailMessage:
        # TODO: Implement synthetic email generation
        raise NotImplementedError("Synthetic email generation not implemented")
    
    async def generate_batch_emails(self, count: int, scenarios: List[str]) -> List[EmailMessage]:
        # TODO: Implement batch email generation
        raise NotImplementedError("Batch email generation not implemented")