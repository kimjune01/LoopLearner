from abc import ABC, abstractmethod
from typing import List
from core.models import Email
import random
from django.utils import timezone
from asgiref.sync import sync_to_async


class EmailGenerator(ABC):
    """Abstract interface for generating synthetic emails"""
    
    @abstractmethod
    async def generate_synthetic_email(self, scenario_type: str = "random") -> Email:
        """Generate a synthetic email for testing"""
        pass
    
    @abstractmethod
    async def generate_batch_emails(self, count: int, scenarios: List[str]) -> List[Email]:
        """Generate multiple synthetic emails"""
        pass


class SyntheticEmailGenerator(EmailGenerator):
    """Concrete implementation for synthetic email generation"""
    
    # Template data for different scenarios
    TEMPLATES = {
        'professional': {
            'subjects': [
                'Meeting Request: Q4 Planning Session',
                'Follow-up on Proposal Discussion',
                'Project Update Required',
                'Budget Approval Request',
                'Team Performance Review Schedule'
            ],
            'bodies': [
                'I hope this email finds you well. I wanted to reach out regarding our upcoming project milestone. Could we schedule a brief meeting to discuss the next steps and ensure we are aligned on the deliverables?',
                'Thank you for your time during our call yesterday. As discussed, I am following up with the proposal details. Please review the attached documents and let me know if you have any questions.',
                'I wanted to provide you with a quick update on the current project status. We have completed phase one and are on track to meet our deadline. However, I wanted to discuss some potential adjustments to the timeline.'
            ],
            'senders': ['manager@company.com', 'colleague@business.org', 'client@enterprise.com']
        },
        'casual': {
            'subjects': [
                'Coffee chat next week?',
                'Quick question about the weekend',
                'Lunch plans for Friday',
                'Book recommendation',
                'How was your vacation?'
            ],
            'bodies': [
                'Hey! Hope you\'re doing well. I was wondering if you\'d be up for grabbing coffee sometime next week? I\'d love to catch up and hear about what you\'ve been working on lately.',
                'Hi there! I was just thinking about our conversation the other day and had a quick question. Do you remember the name of that restaurant you mentioned? I\'d love to try it out.',
                'Hope your week is going great! I was thinking about trying that new place downtown for lunch on Friday. Want to join me? Let me know if you\'re free!'
            ],
            'senders': ['friend@email.com', 'buddy@personal.net', 'pal@gmail.com']
        },
        'complaint': {
            'subjects': [
                'Unacceptable Service Experience',
                'Product Quality Issue - Immediate Response Needed',
                'Billing Error on Recent Invoice',
                'Disappointed with Recent Purchase',
                'Service Interruption Complaint'
            ],
            'bodies': [
                'I am writing to express my dissatisfaction with the service I received yesterday. The issue was not resolved despite multiple attempts to contact your support team. I expect a prompt resolution and compensation for the inconvenience caused.',
                'I recently purchased your product and am extremely disappointed with the quality. The item arrived damaged and does not match the description provided on your website. I demand a full refund and an explanation for this poor experience.',
                'I have noticed an error in my recent bill that has resulted in an overcharge. This is the second time this has happened, and I am concerned about the accuracy of your billing system. Please investigate this matter immediately.'
            ],
            'senders': ['customer.service@complaints.com', 'upset.customer@email.com', 'concerned.buyer@mail.net']
        },
        'inquiry': {
            'subjects': [
                'Information Request about Your Services',
                'Pricing Inquiry for Upcoming Project',
                'Product Specifications Question',
                'Availability Check for Consultation',
                'Partnership Opportunity Discussion'
            ],
            'bodies': [
                'I am interested in learning more about your services and how they might benefit my organization. Could you please provide me with detailed information about your offerings and pricing structure?',
                'We are currently evaluating vendors for an upcoming project and would like to know more about your capabilities. Could you share some case studies or examples of similar work you have completed?',
                'I came across your company while researching solutions for our current challenge. Would it be possible to schedule a brief call to discuss how your services might align with our needs?'
            ],
            'senders': ['prospect@potential.com', 'inquiry@business.org', 'interested.party@company.net']
        }
    }
    
    async def generate_synthetic_email(self, scenario_type: str = "random") -> Email:
        """Generate a synthetic email for testing"""
        if scenario_type == "random":
            scenario_type = random.choice(list(self.TEMPLATES.keys()))
        
        if scenario_type not in self.TEMPLATES:
            scenario_type = "professional"  # fallback
            
        template = self.TEMPLATES[scenario_type]
        
        email = await sync_to_async(Email.objects.create)(
            subject=random.choice(template['subjects']),
            body=random.choice(template['bodies']),
            sender=random.choice(template['senders']),
            scenario_type=scenario_type,
            is_synthetic=True
        )
        
        return email
    
    async def generate_batch_emails(self, count: int, scenarios: List[str]) -> List[Email]:
        """Generate multiple synthetic emails"""
        emails = []
        for i in range(count):
            scenario = scenarios[i % len(scenarios)] if scenarios else "random"
            email = await self.generate_synthetic_email(scenario)
            emails.append(email)
        return emails