from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from .models import Quiz, Question, Choice, LearningMaterial
from .forms import QuizGenerationForm
from .services.quiz_generator import QuizGenerationService
import asyncio

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('learning_material', 'passing_score', 'max_attempts')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'generate-quiz/',
                self.admin_site.admin_view(self.generate_quiz_view),
                name='generate-quiz',
            ),
        ]
        return custom_urls + urls

    def generate_quiz_view(self, request):
        if request.method == 'POST':
            form = QuizGenerationForm(request.POST)
            if form.is_valid():
                return self.generate_quiz_from_form(form)
        else:
            form = QuizGenerationForm()

        context = {
            'form': form,
            'title': 'Generate Quiz using AI',
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/quiz_generation_form.html', context)

    def generate_quiz_from_form(self, form):
        quiz_service = QuizGenerationService()
        
        # Run async generation in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            quiz_data = loop.run_until_complete(
                quiz_service.generate_quiz(
                    topic=form.cleaned_data['topic'],
                    difficulty=form.cleaned_data['difficulty'],
                    num_questions=form.cleaned_data['num_questions']
                )
            )
        finally:
            loop.close()

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

        return redirect('admin:personal_training_quiz_change', quiz.id)
