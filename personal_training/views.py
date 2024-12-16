from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .services.platform import QuizGenerationService
from asgiref.sync import sync_to_async
import json

@csrf_exempt
@require_http_methods(["POST"])
async def generate_quiz(request):
    """Generate a quiz based on course content"""
    try:
        data = json.loads(request.body)
        course_content = data.get('course_content')
        
        if not course_content:
            return JsonResponse({
                'error': 'Course content is required'
            }, status=400)

        # Initialize quiz service through platform
        quiz_service = QuizGenerationService()
        
        # Generate quiz based on course content
        quiz_data = await quiz_service.generate_quiz(
            topic=course_content,
            user_id=request.user.id if request.user.is_authenticated else None
        )

        return JsonResponse({
            'success': True,
            'quiz_data': quiz_data
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"]) 
async def validate_answer(request):
    """Validate a quiz answer and provide feedback"""
    try:
        data = json.loads(request.body)
        question_type = data.get('question_type')
        user_answer = data.get('answer')
        correct_answer = data.get('correct_answer')
        context = data.get('context', None)

        if not all([question_type, user_answer, correct_answer]):
            return JsonResponse({
                'error': 'Missing required fields'
            }, status=400)

        quiz_service = QuizGenerationService()
        
        # Generate feedback for the answer
        feedback = await quiz_service.generate_feedback(
            user_answer=user_answer,
            correct_answer=correct_answer,
            question_type=question_type,
            context=context
        )

        return JsonResponse({
            'success': True,
            'feedback': feedback
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
async def evaluate_quiz(request):
    """Evaluate entire quiz submission"""
    try:
        data = json.loads(request.body)
        quiz_answers = data.get('answers')
        quiz_data = data.get('quiz_data')
        
        if not quiz_answers or not quiz_data:
            return JsonResponse({
                'error': 'Quiz answers and data are required'
            }, status=400)

        quiz_service = QuizGenerationService()
        
        # Calculate score and generate feedback
        score = 0
        total_questions = len(quiz_data['questions'])
        feedback_list = []

        for answer, question in zip(quiz_answers, quiz_data['questions']):
            feedback = await quiz_service.generate_feedback(
                user_answer=answer,
                correct_answer=question.get('model_answer') or question.get('choices')[0]['choice_text'],
                question_type=question['question_type'],
                context=question.get('scenario_context')
            )
            feedback_list.append(feedback)
            
            # For MCQ, check if answer matches correct choice
            if question['question_type'] == 'mcq':
                correct_choice = next(
                    choice['choice_text'] for choice in question['choices'] 
                    if choice['is_correct']
                )
                if answer == correct_choice:
                    score += 1

        # Calculate percentage score
        percentage_score = (score / total_questions) * 100 if total_questions > 0 else 0

        return JsonResponse({
            'success': True,
            'score': percentage_score,
            'total_questions': total_questions,
            'correct_answers': score,
            'feedback': feedback_list
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)