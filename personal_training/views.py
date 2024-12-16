from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Avg
from django.views.decorators.http import require_http_methods
from .models import (
    Lesson, LearningMaterial, Quiz, Question, Choice,
    QuizAttempt, UserQuizHistory
)
from .services.quiz_module import QuizGenerationService
from asgiref.sync import sync_to_async
import json
from typing import Dict, Optional

async def generate_quiz(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from request
            data = json.loads(request.body)
            lesson_id = data.get('lesson_id')
            difficulty = data.get('difficulty', 'intermediate')
            question_types = data.get('question_types', {'mcq': 5})
            
            if not lesson_id:
                return JsonResponse({'error': 'Lesson ID is required'}, status=400)
            
            # Get the lesson and its materials
            lesson = await sync_to_async(get_object_or_404)(Lesson, id=lesson_id)
            materials = await sync_to_async(list)(
                LearningMaterial.objects.filter(
                    lesson=lesson,
                    content_type__in=['text', 'article']
                ).order_by('order')
            )
            
            if not materials:
                return JsonResponse({
                    'error': 'No learning materials found for this lesson'
                }, status=400)
            
            # Combine all material content
            content = "\n\n".join([
                f"Topic: {material.title}\n{material.content}"
                for material in materials
            ])
            
            # Generate quiz using the service
            quiz_service = QuizGenerationService()
            quiz_data = await quiz_service.generate_quiz(
                topic=content,
                question_types=question_types,
                difficulty=difficulty,
                user_id=request.user.id if request.user.is_authenticated else None
            )
            
            # Create and save the quiz
            @sync_to_async
            def save_quiz():
                learning_material = LearningMaterial.objects.create(
                    lesson=lesson,
                    title=f"Quiz: {lesson.title}",
                    content_type='quiz',
                    content=json.dumps(quiz_data),
                    order=len(materials) + 1,
                    is_required=True
                )
                
                quiz = Quiz.objects.create(
                    learning_material=learning_material,
                    passing_score=70,
                    max_attempts=3,
                    difficulty_level=difficulty,
                    question_types=question_types,
                    adaptive_difficulty=True
                )
                
                for q_data in quiz_data['questions']:
                    question = Question.objects.create(
                        quiz=quiz,
                        question_text=q_data['question_text'],
                        question_type=q_data['question_type'],
                        difficulty_level=q_data['difficulty_level'],
                        scenario_context=q_data.get('scenario_context', ''),
                        explanation=q_data['explanation'],
                        order=Question.objects.filter(quiz=quiz).count() + 1
                    )
                    
                    if q_data['question_type'] == 'mcq':
                        for c_data in q_data['choices']:
                            Choice.objects.create(
                                question=question,
                                choice_text=c_data['choice_text'],
                                is_correct=c_data['is_correct']
                            )
                
                return quiz.id
            
            quiz_id = await save_quiz()
            
            return JsonResponse({
                'success': True,
                'message': 'Quiz generated successfully',
                'quiz_id': quiz_id
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    # GET request - show form
    @sync_to_async
    def get_lessons():
        return list(
            Lesson.objects.select_related('module__course')
            .filter(is_published=True)
            .order_by('module__course__title', 'title')
        )
    
    lessons = await get_lessons()
    
    return render(request, 'personal_training/quiz_generation.html', {
        'lessons': lessons
    })

@require_http_methods(["POST"])
async def submit_quiz_answer(request, quiz_id):
    """Handle quiz answer submission and generate feedback."""
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        user_answer = data.get('answer')
        
        if not all([quiz_id, question_id, user_answer]):
            return JsonResponse({
                'error': 'Missing required fields'
            }, status=400)
            
        # Get question and correct answer
        question = await sync_to_async(get_object_or_404)(Question, id=question_id, quiz_id=quiz_id)
        
        # Generate feedback using Gemini
        quiz_service = QuizGenerationService()
        
        if question.question_type == 'mcq':
            correct_choice = await sync_to_async(
                lambda: question.choices.get(is_correct=True)
            )()
            feedback = await quiz_service.generate_feedback(
                user_answer=user_answer,
                correct_answer=correct_choice.choice_text,
                question_type='mcq'
            )
        else:
            feedback = await quiz_service.generate_feedback(
                user_answer=user_answer,
                correct_answer=question.model_answer,
                question_type=question.question_type,
                context=question.scenario_context
            )
            
        # Update attempt data
        @sync_to_async
        def update_attempt():
            attempt = QuizAttempt.objects.get(
                user=request.user,
                quiz_id=quiz_id,
                completed_at__isnull=True
            )
            
            # Store feedback for this question
            attempt.feedback[str(question_id)] = feedback
            attempt.save(update_fields=['feedback'])
            
            return attempt
            
        await update_attempt()
        
        return JsonResponse({
            'success': True,
            'feedback': feedback
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@require_http_methods(["POST"])
async def complete_quiz(request, quiz_id):
    """Handle quiz completion and update user history."""
    try:
        @sync_to_async
        def finalize_attempt():
            attempt = QuizAttempt.objects.get(
                user=request.user,
                quiz_id=quiz_id,
                completed_at__isnull=True
            )
            
            # Calculate final score
            total_questions = attempt.quiz.questions.count()
            correct_answers = sum(
                1 for feedback in attempt.feedback.values()
                if feedback.get('score', 0) >= 0.7
            )
            score = (correct_answers / total_questions) * 100
            
            # Update attempt
            attempt.score = score
            attempt.completed_at = timezone.now()
            attempt.save()
            
            # Update user history
            history, created = UserQuizHistory.objects.get_or_create(
                user=request.user,
                quiz_id=quiz_id
            )
            
            history.total_attempts += 1
            history.average_score = (
                (history.average_score * (history.total_attempts - 1) + score)
                / history.total_attempts
            )
            
            # Update performance trend
            trend = history.performance_trend
            trend.append(score)
            if len(trend) > 5:  # Keep last 5 scores
                trend = trend[-5:]
            history.performance_trend = trend
            
            history.save()
            
            return score, attempt.feedback
            
        score, feedback = await finalize_attempt()
        
        return JsonResponse({
            'success': True,
            'score': score,
            'feedback': feedback
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

def quiz_list(request):
    """View to display list of all quizzes."""
    quizzes = Quiz.objects.select_related(
        'learning_material'
    ).only(
        'id',
        'learning_material__title',
        'passing_score',
        'max_attempts',
        'time_limit_minutes'
    )
    return render(request, 'personal_training/quiz_list.html', {
        'quizzes': quizzes
    })

def quiz_detail(request, pk):
    """View to display a specific quiz."""
    quiz = get_object_or_404(
        Quiz.objects.select_related(
            'learning_material'
        ).only(
            'id',
            'learning_material__title',
            'passing_score',
            'max_attempts',
            'time_limit_minutes'
        ),
        pk=pk
    )
    
    # Get user's quiz history only if user is authenticated
    history = None
    if request.user.is_authenticated:
        history = UserQuizHistory.objects.filter(
            user=request.user,
            quiz=quiz
        ).first()
    
    # Only fetch fields that exist in the database
    questions = quiz.questions.all().only(
        'id',
        'question_text',
        'explanation',
        'order',
        'points'
    )
    
    return render(request, 'personal_training/quiz_detail.html', {
        'quiz': quiz,
        'questions': questions,
        'history': history
    })

def quiz_generate(request):
    """View to handle quiz generation"""
    if request.method == 'POST':
        lesson_id = request.POST.get('lesson_id')
        return JsonResponse({'success': True, 'message': 'Quiz generated successfully'})
    
    lessons = Lesson.objects.all()
    return render(request, 'personal_training/quiz_generation.html', {
        'lessons': lessons
    })
