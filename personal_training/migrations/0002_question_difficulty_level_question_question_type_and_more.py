# Generated by Django 5.1.4 on 2024-12-15 17:00

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personal_training', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='difficulty_level',
            field=models.CharField(choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], default='intermediate', max_length=20),
        ),
        migrations.AddField(
            model_name='question',
            name='question_type',
            field=models.CharField(choices=[('mcq', 'Multiple Choice'), ('scenario', 'Scenario Based'), ('application', 'Application Based'), ('reflection', 'Reflective'), ('discussion', 'Discussion')], default='mcq', max_length=20),
        ),
        migrations.AddField(
            model_name='question',
            name='scenario_context',
            field=models.TextField(blank=True, help_text='Additional context for scenario-based questions'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='adaptive_difficulty',
            field=models.BooleanField(default=False, help_text='Whether to adjust difficulty based on user performance'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='difficulty_level',
            field=models.CharField(choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], default='intermediate', max_length=20),
        ),
        migrations.AddField(
            model_name='quiz',
            name='question_types',
            field=models.JSONField(default=dict, help_text="Configuration for question types (e.g., {'mcq': 3, 'scenario': 2})"),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='feedback',
            field=models.JSONField(default=dict, help_text='AI-generated feedback for each question'),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='performance_metrics',
            field=models.JSONField(default=dict, help_text='Detailed metrics about user performance'),
        ),
        migrations.CreateModel(
            name='UserQuizHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('average_score', models.FloatField(default=0.0)),
                ('total_attempts', models.PositiveIntegerField(default=0)),
                ('last_difficulty_level', models.CharField(choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], default='intermediate', max_length=20)),
                ('performance_trend', models.JSONField(default=list, help_text='List of recent scores to track improvement')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_history', to='personal_training.quiz')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_history', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'User quiz histories',
                'unique_together': {('user', 'quiz')},
            },
        ),
    ]
