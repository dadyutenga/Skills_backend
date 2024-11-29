from django.shortcuts import render, redirect
from django.views.generic import FormView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Quiz, Question, Choice, LearningMaterial
from .forms import QuizGenerationForm
from .services.quiz_generator import QuizGenerationService
import asyncio
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from asgiref.sync import sync_to_async

render_async = sync_to_async(render)
redirect_async = sync_to_async(redirect)

class QuizListView(ListView):
    model = Quiz
    template_name = 'personal_training/quiz_list.html'
    context_object_name = 'quizzes'

@method_decorator(csrf_protect, name='dispatch')
class QuizGenerationView(View):
    template_name = 'quiz_generation.html'
    
    async def get(self, request):
        form = QuizGenerationForm()
        return await render_async(request, self.template_name, {'form': form})
    
    async def post(self, request):
        form = QuizGenerationForm(request.POST)
        if form.is_valid():
            try:
                # Get form data
                topic = form.cleaned_data['topic']
                difficulty = form.cleaned_data['difficulty']
                num_questions = form.cleaned_data['num_questions']
                
                # Initialize quiz generator
                quiz_generator = QuizGenerationService()
                
                try:
                    # Generate quiz content - now passing topic directly
                    quiz_data = await quiz_generator.generate_quiz(
                        topic=topic,
                        num_questions=num_questions,
                        difficulty=difficulty
                    )
                except Exception as e:
                    print(f"Quiz generation error: {str(e)}")
                    messages.error(request, f"Failed to generate quiz: {str(e)}")
                    return await render_async(request, self.template_name, {'form': form})

                try:
                    # Save quiz data using sync_to_async for database operations
                    @sync_to_async
                    def save_quiz_data():
                        # Create learning material
                        learning_material = LearningMaterial.objects.create(
                            title=f"Quiz: {topic}",
                            content_type='quiz',
                            content=topic,
                            order=1
                        )
                        
                        # Create quiz
                        quiz = Quiz.objects.create(
                            learning_material=learning_material,
                            passing_score=70,  # Default value
                            max_attempts=3  # Default value
                        )
                        
                        # Create questions and choices
                        for i, q_data in enumerate(quiz_data['questions'], 1):
                            question = Question.objects.create(
                                quiz=quiz,
                                question_text=q_data['question_text'],
                                explanation=q_data['explanation'],
                                order=i,
                                points=1
                            )
                            
                            for choice in q_data['choices']:
                                Choice.objects.create(
                                    question=question,
                                    choice_text=choice['choice_text'],
                                    is_correct=choice['is_correct']
                                )
                        
                        return quiz.id

                    quiz_id = await save_quiz_data()
                    messages.success(request, 'Quiz generated successfully!')
                    return await redirect_async('quiz-detail', quiz_id=quiz_id)
                    
                except Exception as e:
                    print(f"Quiz saving error: {str(e)}")
                    messages.error(request, f"Failed to save quiz: {str(e)}")
                    
            except Exception as e:
                print(f"General error: {str(e)}")
                messages.error(request, f'Error: {str(e)}')
        
        return await render_async(request, self.template_name, {'form': form})

class QuizDetailView(DetailView):
    model = Quiz
    template_name = 'personal_training/quiz_detail.html'
    context_object_name = 'quiz'
    pk_url_kwarg = 'quiz_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.get_object()
        context['questions'] = quiz.questions.all().prefetch_related('choices')
        return context
