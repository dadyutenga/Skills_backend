from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Lesson, LearningMaterial, Quiz, Question, Choice
from .services.quiz_generator import QuizGenerationService
from asgiref.sync import sync_to_async
import json

async def generate_quiz(request):
    if request.method == 'POST':
        try:
            # Get lesson ID from the form
            lesson_id = request.POST.get('lesson_id')
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
                num_questions=5
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
                    max_attempts=3
                )
                
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
