# Generated manually to rename SessionConfidence to PromptLabConfidence

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_rename_session_promptlab_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SessionConfidence',
            new_name='PromptLabConfidence',
        ),
    ]