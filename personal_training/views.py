from django.shortcuts import render, redirect
from django.views.generic import FormView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Quiz, Question, Choice, LearningMaterial
from .forms import QuizGenerationForm
from .services.quiz_generator import QuizGenerationService
import asyncio

class QuizListView(ListView):
    model = Quiz
    template_name = 'personal_training/quiz_list.html'
    context_object_name = 'quizzes'

class QuizGenerationView(FormView):
    form_class = QuizGenerationForm
    template_name = 'personal_training/quiz_generation.html'
    success_url = reverse_lazy('quiz-list')

    async def form_valid(self, form):
        quiz_service = QuizGenerationService()
        
        try:
            # Generate quiz data
            quiz_data = await quiz_service.generate_quiz(
                topic=form.cleaned_data['topic'],
                difficulty=form.cleaned_data['difficulty'],
                num_questions=form.cleaned_data['num_questions']
            )

            # Create Quiz and related objects
            learning_material = form.cleaned_data['learning_material']
            quiz = Quiz.objects.create(
                learning_material=learning_material,
                passing_score=70,  # Default value
                max_attempts=3     # Default value
            )

            # Create Questions and Choices
            for q_data in quiz_data['questions']:
                question = Question.objects.create(
                    quiz=quiz,
                    question_text=q_data['question_text'],
                    explanation=q_data['explanation'],
                    order=Question.objects.filter(quiz=quiz).count() + 1
                )
                
                for c_data in q_data['choices']:
                    Choice.objects.create(
                        question=question,
                        choice_text=c_data['choice_text'],
                        is_correct=c_data['is_correct']
                    )

            return redirect(self.success_url)

        except Exception as e:
            form.add_error(None, f"Failed to generate quiz: {str(e)}")
            return self.form_invalid(form)
