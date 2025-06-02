"""
Management command to fix triple curly braces in evaluation cases
"""
from django.core.management.base import BaseCommand
from core.models import EvaluationCase
import re


class Command(BaseCommand):
    help = 'Fix triple curly braces in evaluation cases'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Pattern to find triple braces
        triple_brace_pattern = re.compile(r'\{\{\{(\w+)\}\}\}')
        
        cases_to_fix = []
        
        # Check both EvaluationCase and DraftCase
        self.stdout.write('Checking EvaluationCase entries...')
        for case in EvaluationCase.objects.all():
            if triple_brace_pattern.search(case.input_text):
                cases_to_fix.append(('EvaluationCase', case))
        
        from core.models import DraftCase
        self.stdout.write('Checking DraftCase entries...')
        for case in DraftCase.objects.all():
            if triple_brace_pattern.search(case.input_text):
                cases_to_fix.append(('DraftCase', case))
        
        if not cases_to_fix:
            self.stdout.write(self.style.SUCCESS('No cases with triple braces found.'))
            
            # Do a more thorough check
            self.stdout.write('\nDoing detailed check...')
            for case in EvaluationCase.objects.all()[:10]:
                if '{{{' in case.input_text or '}}}' in case.input_text:
                    self.stdout.write(f'Case {case.id} might have formatting issues')
                    # Show a snippet
                    start = max(0, case.input_text.find('{{{') - 20)
                    end = min(len(case.input_text), start + 100)
                    self.stdout.write(f'  Snippet: ...{case.input_text[start:end]}...')
            return
        
        self.stdout.write(f'Found {len(cases_to_fix)} cases with triple braces.')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made.'))
        
        fixed_count = 0
        for case_type, case in cases_to_fix:
            original = case.input_text
            # Replace triple braces with double braces
            fixed = triple_brace_pattern.sub(r'{{\1}}', original)
            
            self.stdout.write(f'\n{case_type} ID {case.id}:')
            self.stdout.write(f'  Dataset: {case.dataset.name}')
            
            # Show a sample of the change
            matches = triple_brace_pattern.findall(original)
            for match in matches[:3]:  # Show first 3 matches
                self.stdout.write(f'  {{{{{match}}}}} → {{{match}}}')
            if len(matches) > 3:
                self.stdout.write(f'  ... and {len(matches) - 3} more')
            
            if not dry_run:
                case.input_text = fixed
                case.save()
                fixed_count += 1
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'\nFixed {fixed_count} cases.'))
        else:
            self.stdout.write(self.style.WARNING(f'\nWould fix {len(cases_to_fix)} cases.'))