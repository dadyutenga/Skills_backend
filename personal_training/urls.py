from django.urls import path
from . import views

app_name = 'personal_training'

urlpatterns = [
    path('api/quiz/generate/', views.generate_quiz, name='generate_quiz'),
    path('api/quiz/validate/', views.validate_answer, name='validate_answer'),
    path('api/quiz/evaluate/', views.evaluate_quiz, name='evaluate_quiz'),
]
