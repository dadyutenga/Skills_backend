# Generated by Django 5.1.4 on 2024-12-20 18:29

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Oauth', '0002_user_age_user_specialization'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('slug', models.SlugField(unique=True)),
                ('icon', models.URLField(blank=True, max_length=500)),
                ('featured', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('overview', models.TextField()),
                ('learning_objectives', models.TextField()),
                ('prerequisites', models.TextField(blank=True)),
                ('duration_hours', models.PositiveIntegerField(help_text='Estimated hours to complete')),
                ('min_age', models.PositiveIntegerField(default=5)),
                ('max_age', models.PositiveIntegerField(default=100)),
                ('age_group', models.CharField(choices=[('children', 'Children (5-12)'), ('teenager', 'Teenager (13-17)'), ('young_adult', 'Young Adult (18-25)'), ('adult', 'Adult (26-50)'), ('senior', 'Senior (51+)')], default='adult', max_length=20)),
                ('thumbnail', models.URLField(blank=True, max_length=500)),
                ('preview_video', models.URLField(blank=True, max_length=500)),
                ('difficulty_level', models.CharField(choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('professional', 'Professional')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='courses', to='personal_training.category')),
            ],
            options={
                'ordering': ['title'],
            },
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('content_type', models.CharField(choices=[('text', 'Text Content'), ('video', 'Video'), ('article', 'Article'), ('infographic', 'Infographic'), ('interactive', 'Interactive Content')], default='text', max_length=20)),
                ('content', models.TextField(blank=True, default='')),
                ('order', models.PositiveIntegerField()),
                ('thumbnail', models.URLField(blank=True, max_length=500)),
                ('media_url', models.URLField(blank=True, max_length=500)),
                ('duration_minutes', models.PositiveIntegerField(default=0)),
                ('is_required', models.BooleanField(default=True)),
                ('is_preview', models.BooleanField(default=False)),
                ('is_published', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='modules', to='personal_training.course')),
            ],
            options={
                'ordering': ['course', 'order'],
                'unique_together': {('course', 'order')},
            },
        ),
        migrations.CreateModel(
            name='UserCourseEnrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enrolled_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('progress_percentage', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('last_accessed', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='personal_training.course')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='Oauth.user')),
            ],
            options={
                'unique_together': {('user', 'course')},
            },
        ),
        migrations.CreateModel(
            name='UserModuleProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('progress_percentage', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('last_accessed', models.DateTimeField(auto_now=True)),
                ('enrollment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='module_progress', to='personal_training.usercourseenrollment')),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_progress', to='personal_training.module')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='module_progress', to='Oauth.user')),
            ],
            options={
                'unique_together': {('user', 'module')},
            },
        ),
    ]
