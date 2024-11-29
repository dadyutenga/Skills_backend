from django.urls import path
from .views import QuizListView, QuizGenerationView

urlpatterns = [
    path('quizzes/', QuizListView.as_view(), name='quiz-list'),
    path('quizzes/generate/', QuizGenerationView.as_view(), name='quiz-generate'),
]
