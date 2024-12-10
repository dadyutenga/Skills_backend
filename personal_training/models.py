from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg

class Category(models.Model):
    """Course categories like 'Financial Literacy', 'Communication Skills', etc."""
    name = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Course(models.Model):
    """Main course model containing general course information"""
    category = models.ForeignKey(Category, related_name='courses', on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    overview = models.TextField()
    learning_objectives = models.TextField()
    prerequisites = models.TextField(blank=True)
    duration_hours = models.PositiveIntegerField(help_text="Estimated hours to complete")
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

class Module(models.Model):
    """Course modules - organizational units containing lessons"""
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['course', 'order']
        unique_together = [['course', 'order']]

    def __str__(self):
        return f"{self.course.title} - Module {self.order}: {self.title}"

class Lesson(models.Model):
    """Individual lessons within modules"""
    module = models.ForeignKey(Module, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    summary = models.TextField()
    order = models.PositiveIntegerField()
    estimated_time_minutes = models.PositiveIntegerField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['module', 'order']
        unique_together = [['module', 'order']]

    def __str__(self):
        return f"{self.module.course.title} - {self.title}"

class LearningMaterial(models.Model):
    """Content items within lessons"""
    lesson = models.ForeignKey(Lesson, related_name='materials', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text Content'),
            ('video', 'Video'),
            ('article', 'Article'),
            ('infographic', 'Infographic'),
            ('quiz', 'Quiz')
        ]
    )
    content = models.TextField()
    media_url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField()
    is_required = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['lesson', 'order']
        unique_together = [['lesson', 'order']]

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"

class Quiz(models.Model):
    """Quiz configuration and settings"""
    learning_material = models.OneToOneField(
        LearningMaterial, 
        related_name='quiz_config',
        on_delete=models.CASCADE
    )
    passing_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=70
    )
    max_attempts = models.PositiveIntegerField(default=3)
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        default='intermediate'
    )
    question_types = models.JSONField(
        default=dict,
        help_text="Configuration for question types (e.g., {'mcq': 3, 'scenario': 2})"
    )
    adaptive_difficulty = models.BooleanField(
        default=False,
        help_text="Whether to adjust difficulty based on user performance"
    )
    
    class Meta:
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return f"Quiz: {self.learning_material.title}"
    
    def get_average_score(self):
        return self.attempts.aggregate(Avg('score'))['score__avg'] or 0

class Question(models.Model):
    """Quiz questions"""
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    explanation = models.TextField(blank=True)
    order = models.PositiveIntegerField()
    points = models.PositiveIntegerField(default=1)
    question_type = models.CharField(
        max_length=20,
        choices=[
            ('mcq', 'Multiple Choice'),
            ('scenario', 'Scenario Based'),
            ('application', 'Application Based'),
            ('reflection', 'Reflective'),
            ('discussion', 'Discussion')
        ],
        default='mcq'
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        default='intermediate'
    )
    scenario_context = models.TextField(
        blank=True,
        help_text="Additional context for scenario-based questions"
    )
    
    class Meta:
        ordering = ['quiz', 'order']

    def __str__(self):
        return f"{self.quiz.learning_material.title} - Question {self.order}"

class Choice(models.Model):
    """Multiple choice options for quiz questions"""
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(blank=True)

    def __str__(self):
        return f"{self.question.question_text[:30]} - {self.choice_text}"

class UserProgress(models.Model):
    """Tracking user progress through the course"""
    user = models.ForeignKey(User, related_name='course_progress', on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, related_name='user_progress', on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'lesson']

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"

class QuizAttempt(models.Model):
    """Recording user attempts at quizzes"""
    user = models.ForeignKey(User, related_name='quiz_attempts', on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, related_name='attempts', on_delete=models.CASCADE)
    score = models.PositiveIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    attempt_number = models.PositiveIntegerField()
    feedback = models.JSONField(
        default=dict,
        help_text="AI-generated feedback for each question"
    )
    performance_metrics = models.JSONField(
        default=dict,
        help_text="Detailed metrics about user performance"
    )

    class Meta:
        unique_together = ['user', 'quiz', 'attempt_number']

    def __str__(self):
        return f"{self.user.username} - {self.quiz.learning_material.title} (Attempt {self.attempt_number})"

class UserQuizHistory(models.Model):
    """Track user's quiz performance history for adaptive difficulty"""
    user = models.ForeignKey(User, related_name='quiz_history', on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, related_name='user_history', on_delete=models.CASCADE)
    average_score = models.FloatField(default=0.0)
    total_attempts = models.PositiveIntegerField(default=0)
    last_difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        default='intermediate'
    )
    performance_trend = models.JSONField(
        default=list,
        help_text="List of recent scores to track improvement"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'quiz']
        verbose_name_plural = "User quiz histories"

    def __str__(self):
        return f"{self.user.username} - {self.quiz.learning_material.title} History"      