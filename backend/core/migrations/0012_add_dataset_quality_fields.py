# Generated manually for dataset quality tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_add_draft_case_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluationdataset',
            name='case_count',
            field=models.IntegerField(default=0, help_text='Number of evaluation cases in this dataset'),
        ),
        migrations.AddField(
            model_name='evaluationdataset',
            name='quality_score',
            field=models.FloatField(default=0.5, help_text='Quality score between 0 and 1'),
        ),
        migrations.AddField(
            model_name='evaluationdataset',
            name='human_reviewed_count',
            field=models.IntegerField(default=0, help_text='Number of human-reviewed cases'),
        ),
    ]