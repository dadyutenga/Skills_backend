from django.urls import path
from .views import QuizListView, QuizGenerationView, QuizDetailView

urlpatterns = [
    path('quizzes/', QuizListView.as_view(), name='quiz-list'),
    path('quizzes/generate/', QuizGenerationView.as_view(), name='quiz-generate'),
    path('quizzes/<int:quiz_id>/', QuizDetailView.as_view(), name='quiz-detail'),
]
