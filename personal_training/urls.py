from django.urls import path
from . import views

app_name = 'personal_training'

urlpatterns = [
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quiz/generate/', views.generate_quiz, name='generate_quiz'),
    path('quiz/<int:pk>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<int:quiz_id>/submit-answer/', views.submit_quiz_answer, name='submit_quiz_answer'),
    path('quiz/<int:quiz_id>/complete/', views.complete_quiz, name='complete_quiz'),
]
