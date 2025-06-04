"""
Management command to clean up stuck optimization runs.
Marks old running optimizations as failed if they haven't been updated recently.
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import OptimizationRun


class Command(BaseCommand):
    help = 'Clean up stuck optimization runs that are still marked as running'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout-minutes',
            type=int,
            default=30,
            help='Consider optimizations stuck if running longer than this many minutes (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually doing it'
        )

    def handle(self, *args, **options):
        timeout_minutes = options['timeout_minutes']
        dry_run = options['dry_run']
        
        # Calculate the cutoff time
        cutoff_time = timezone.now() - timedelta(minutes=timeout_minutes)
        
        # Find stuck optimizations
        stuck_optimizations = OptimizationRun.objects.filter(
            status='running',
            started_at__lt=cutoff_time
        )
        
        count = stuck_optimizations.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No stuck optimizations found.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(
                f'Found {count} stuck optimization(s) running longer than {timeout_minutes} minutes:'
            )
        )
        
        for opt in stuck_optimizations:
            duration = timezone.now() - opt.started_at
            duration_minutes = int(duration.total_seconds() / 60)
            
            self.stdout.write(
                f'  - ID: {opt.id}, Prompt Lab: {opt.prompt_lab.name}, '
                f'Started: {opt.started_at}, Duration: {duration_minutes} minutes'
            )
            
            if opt.progress_data:
                self.stdout.write(f'    Last step: {opt.progress_data.get("current_step", "Unknown")}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nDry run mode - no changes made.')
            )
        else:
            # Update stuck optimizations with detailed error information
            for opt in stuck_optimizations:
                duration = timezone.now() - opt.started_at
                duration_minutes = int(duration.total_seconds() / 60)
                
                # Create detailed error message based on available information
                error_parts = [f"Optimization stuck for {duration_minutes} minutes"]
                
                if opt.current_step:
                    error_parts.append(f"last step: {opt.current_step}")
                
                if opt.progress_data:
                    evaluated = opt.progress_data.get('evaluated_cases', 0)
                    total = opt.progress_data.get('total_cases', 0)
                    if total > 0:
                        error_parts.append(f"progress: {evaluated}/{total} cases")
                
                detailed_error = " | ".join(error_parts)
                
                opt.status = 'failed'
                opt.error_message = detailed_error
                opt.completed_at = timezone.now()
                opt.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully cleaned up {count} stuck optimization(s) with detailed error messages.'
                )
            )