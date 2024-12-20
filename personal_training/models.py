from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    """Course categories with enhanced metadata"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    icon = models.URLField(max_length=500, blank=True)  # Category icon URL
    featured = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Course(models.Model):
    """Enhanced course model with direct age restrictions and media"""
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('professional', 'Professional')
    ]

    AGE_GROUP_CHOICES = [
        ('children', 'Children (5-12)'),
        ('teenager', 'Teenager (13-17)'),
        ('young_adult', 'Young Adult (18-25)'),
        ('adult', 'Adult (26-50)'),
        ('senior', 'Senior (51+)')
    ]

    category = models.ForeignKey(Category, related_name='courses', on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    overview = models.TextField()
    learning_objectives = models.TextField()
    prerequisites = models.TextField(blank=True)
    duration_hours = models.PositiveIntegerField(help_text="Estimated hours to complete")
    
    # Age restrictions directly in course
    min_age = models.PositiveIntegerField(default=5)
    max_age = models.PositiveIntegerField(default=100)
    age_group = models.CharField(max_length=20, choices=AGE_GROUP_CHOICES)
    
    # Media fields
    thumbnail = models.URLField(max_length=500, blank=True)
    preview_video = models.URLField(max_length=500, blank=True)
    
    # Course metadata
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    def is_age_appropriate(self, user_age: int) -> bool:
        """Check if course is appropriate for user's age"""
        return self.min_age <= user_age <= self.max_age

class UserCourseEnrollment(models.Model):
    """Track user enrollment and progress in courses"""
    user = models.ForeignKey('Oauth.User', related_name='enrollments', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='enrollments', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    progress_percentage = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.email} - {self.course.title}"

class Module(models.Model):
    """Enhanced module model with integrated learning materials"""
    CONTENT_TYPES = [
        ('text', 'Text Content'),
        ('video', 'Video'),
        ('article', 'Article'),
        ('infographic', 'Infographic'),
        ('interactive', 'Interactive Content')
    ]

    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content = models.TextField()
    order = models.PositiveIntegerField()
    
    # Media fields
    thumbnail = models.URLField(max_length=500, blank=True)
    media_url = models.URLField(max_length=500, blank=True)
    
    # Module metadata
    duration_minutes = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=True)
    is_preview = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'order']
        unique_together = [['course', 'order']]

    def __str__(self):
        return f"{self.course.title} - Module {self.order}: {self.title}"

class UserModuleProgress(models.Model):
    """Track user progress through modules"""
    user = models.ForeignKey('Oauth.User', related_name='module_progress', on_delete=models.CASCADE)
    module = models.ForeignKey(Module, related_name='user_progress', on_delete=models.CASCADE)
    enrollment = models.ForeignKey(UserCourseEnrollment, related_name='module_progress', on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'module']

    def __str__(self):
        return f"{self.user.email} - {self.module.title}"      