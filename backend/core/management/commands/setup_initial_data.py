from django.core.management.base import BaseCommand
from core.models import SystemPrompt, UserPreference


class Command(BaseCommand):
    help = 'Set up initial system prompt and user preferences'

    def handle(self, *args, **options):
        # Create initial system prompt if none exists
        if not SystemPrompt.objects.exists():
            initial_prompt = SystemPrompt.objects.create(
                content="""You are a helpful email assistant that generates professional and appropriate email responses. 

Your task is to:
1. Analyze the incoming email carefully
2. Generate 2 different draft responses that are appropriate for the context
3. For each draft, provide clear reasoning for why you chose that approach
4. Consider the sender, tone, and content of the original email
5. Maintain professionalism while adapting to the scenario type

Guidelines:
- Be concise but thorough
- Match the appropriate level of formality
- Address all key points from the original email
- Provide helpful and actionable responses
- Always be polite and respectful""",
                version=1,
                is_active=True,
                performance_score=0.8
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created initial system prompt (version {initial_prompt.version})')
            )
        else:
            self.stdout.write('System prompt already exists')

        # Create default user preferences if none exist
        default_preferences = [
            {
                'key': 'tone',
                'value': 'professional',
                'description': 'Default communication tone for email responses'
            },
            {
                'key': 'length',
                'value': 'concise',
                'description': 'Preferred length for email responses'
            },
            {
                'key': 'formality',
                'value': 'business',
                'description': 'Level of formality in communications'
            }
        ]

        created_count = 0
        for pref_data in default_preferences:
            preference, created = UserPreference.objects.get_or_create(
                key=pref_data['key'],
                defaults={
                    'value': pref_data['value'],
                    'description': pref_data['description']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created preference: {preference.key} = {preference.value}')

        if created_count == 0:
            self.stdout.write('All default preferences already exist')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Created {created_count} default user preferences')
            )

        self.stdout.write(
            self.style.SUCCESS('Initial data setup complete!')
        )