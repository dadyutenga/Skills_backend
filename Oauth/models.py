from django.db import models
import uuid

# Create your models here.

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auth0_id = models.CharField(max_length=255, unique=True)  # Store Auth0 sub
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    picture = models.URLField(max_length=1024, blank=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    age = models.PositiveIntegerField(blank=True, null=True)  # Allow empty age values
    specialization = models.CharField(max_length=255, blank=True)  # Allow empty specialization

    def __str__(self):
        return self.email
