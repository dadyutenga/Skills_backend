from typing import Dict, Optional
from django.core.exceptions import ValidationError
from ..models import UserFeedback, Course, Module
import logging

logger = logging.getLogger(__name__)

class FeedbackModule:
    """Service for managing user feedback during learning process"""

    def __init__(self):
        self.logger = logger

    def create_feedback(
        self, 
        user_id: int, 
        course_id: int, 
        module_id: Optional[int] = None,
        quiz_feedback: Dict = None,
        answer_feedback: Dict = None,
        performance_feedback: Dict = None
    ) -> UserFeedback:
        """
        Create new feedback entry for a user
        """
        try:
            feedback = UserFeedback.objects.create(
                user_id=user_id,
                course_id=course_id,
                module_id=module_id,
                quiz_feedback=quiz_feedback or {},
                answer_feedback=answer_feedback or {},
                performance_feedback=performance_feedback or {}
            )
            return feedback
        except Exception as e:
            self.logger.error(f"Error creating feedback: {str(e)}")
            raise ValidationError("Failed to create feedback")

    def update_quiz_feedback(
        self, 
        user_id: int, 
        course_id: int, 
        module_id: int,
        quiz_feedback: Dict
    ) -> UserFeedback:
        """
        Update quiz feedback for a specific module
        """
        try:
            feedback, _ = UserFeedback.objects.get_or_create(
                user_id=user_id,
                course_id=course_id,
                module_id=module_id
            )
            feedback.quiz_feedback.update(quiz_feedback)
            feedback.save()
            return feedback
        except Exception as e:
            self.logger.error(f"Error updating quiz feedback: {str(e)}")
            raise ValidationError("Failed to update quiz feedback")

    def add_answer_feedback(
        self, 
        user_id: int, 
        course_id: int, 
        module_id: int,
        question_id: str,
        feedback_text: str
    ) -> UserFeedback:
        """
        Add feedback for a specific answer
        """
        try:
            feedback, _ = UserFeedback.objects.get_or_create(
                user_id=user_id,
                course_id=course_id,
                module_id=module_id
            )
            feedback.answer_feedback[question_id] = feedback_text
            feedback.save()
            return feedback
        except Exception as e:
            self.logger.error(f"Error adding answer feedback: {str(e)}")
            raise ValidationError("Failed to add answer feedback")

    def update_performance_feedback(
        self, 
        user_id: int, 
        course_id: int,
        feedback_data: Dict
    ) -> UserFeedback:
        """
        Update overall performance feedback
        """
        try:
            feedback, _ = UserFeedback.objects.get_or_create(
                user_id=user_id,
                course_id=course_id
            )
            feedback.performance_feedback.update(feedback_data)
            feedback.save()
            return feedback
        except Exception as e:
            self.logger.error(f"Error updating performance feedback: {str(e)}")
            raise ValidationError("Failed to update performance feedback")

    def get_user_feedback(
        self, 
        user_id: int, 
        course_id: Optional[int] = None, 
        module_id: Optional[int] = None
    ) -> Dict:
        """
        Retrieve user feedback for course/module
        """
        try:
            query = UserFeedback.objects.filter(user_id=user_id)
            
            if course_id:
                query = query.filter(course_id=course_id)
            if module_id:
                query = query.filter(module_id=module_id)

            feedbacks = query.order_by('-updated_at')
            
            return {
                'feedbacks': [
                    {
                        'course_id': feedback.course_id,
                        'module_id': feedback.module_id,
                        'quiz_feedback': feedback.quiz_feedback,
                        'answer_feedback': feedback.answer_feedback,
                        'performance_feedback': feedback.performance_feedback,
                        'updated_at': feedback.updated_at
                    }
                    for feedback in feedbacks
                ]
            }
        except Exception as e:
            self.logger.error(f"Error retrieving feedback: {str(e)}")
            return {'feedbacks': []}