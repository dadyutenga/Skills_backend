from typing import Dict, Optional
from django.core.exceptions import ValidationError
from ..models import UserFeedback, UserCourseEnrollment, Module
from Oauth.models import User
import logging
import uuid

logger = logging.getLogger(__name__)

class FeedbackModule:
    """Service for managing feedback on course delivery and platform functionality"""

    def __init__(self):
        self.logger = logger

    def create_course_feedback(
        self, 
        user_id: uuid.UUID,
        enrollment_id: int,
        module_id: Optional[int] = None,
        content_delivery_feedback: Dict = None,
        platform_experience_feedback: Dict = None,
        learning_experience_feedback: Dict = None
    ) -> UserFeedback:
        """
        Create feedback about course delivery and platform experience
        """
        try:
            enrollment = UserCourseEnrollment.objects.get(
                id=enrollment_id,
                user_id=user_id
            )
            
            feedback = UserFeedback.objects.create(
                user_id=user_id,
                enrollment=enrollment,
                module_id=module_id,
                quiz_feedback={
                    'content_delivery': content_delivery_feedback or {},
                    'platform_experience': platform_experience_feedback or {},
                    'learning_experience': learning_experience_feedback or {}
                }
            )
            return feedback
        except Exception as e:
            self.logger.error(f"Error creating feedback for user {user_id}: {str(e)}")
            raise ValidationError("Failed to create feedback")

    def update_delivery_feedback(
        self, 
        user_id: uuid.UUID,
        enrollment_id: int,
        module_id: int,
        delivery_feedback: Dict
    ) -> UserFeedback:
        """
        Update feedback about content delivery methods
        """
        try:
            enrollment = UserCourseEnrollment.objects.get(
                id=enrollment_id,
                user_id=user_id
            )
            feedback, _ = UserFeedback.objects.get_or_create(
                user_id=user_id,
                enrollment=enrollment,
                module_id=module_id
            )
            
            current_feedback = feedback.quiz_feedback.get('content_delivery', {})
            current_feedback.update(delivery_feedback)
            feedback.quiz_feedback['content_delivery'] = current_feedback
            feedback.save()
            
            return feedback
        except Exception as e:
            self.logger.error(f"Error updating delivery feedback for user {user_id}: {str(e)}")
            raise ValidationError("Failed to update delivery feedback")

    def add_platform_feedback(
        self, 
        user_id: uuid.UUID,
        enrollment_id: int,
        module_id: int,
        feature_id: str,
        feedback_text: str
    ) -> UserFeedback:
        """
        Add feedback about platform features and functionality
        """
        try:
            enrollment = UserCourseEnrollment.objects.get(
                id=enrollment_id,
                user_id=user_id
            )
            feedback, _ = UserFeedback.objects.get_or_create(
                user_id=user_id,
                enrollment=enrollment,
                module_id=module_id
            )
            
            if 'platform_experience' not in feedback.quiz_feedback:
                feedback.quiz_feedback['platform_experience'] = {}
                
            feedback.quiz_feedback['platform_experience'][feature_id] = feedback_text
            feedback.save()
            
            return feedback
        except Exception as e:
            self.logger.error(f"Error adding platform feedback for user {user_id}: {str(e)}")
            raise ValidationError("Failed to add platform feedback")

    def update_learning_experience(
        self, 
        enrollment_id: int,
        feedback_data: Dict
    ) -> UserFeedback:
        """
        Update feedback about overall learning experience
        """
        try:
            enrollment = UserCourseEnrollment.objects.get(id=enrollment_id)
            feedback, _ = UserFeedback.objects.get_or_create(
                enrollment=enrollment
            )
            
            current_feedback = feedback.quiz_feedback.get('learning_experience', {})
            current_feedback.update(feedback_data)
            feedback.quiz_feedback['learning_experience'] = current_feedback
            feedback.save()
            
            return feedback
        except Exception as e:
            self.logger.error(f"Error updating learning experience feedback: {str(e)}")
            raise ValidationError("Failed to update learning experience feedback")

    def get_course_feedback(
        self, 
        user_id: Optional[uuid.UUID] = None,
        enrollment_id: Optional[int] = None,
        module_id: Optional[int] = None
    ) -> Dict:
        """
        Retrieve feedback for course delivery and platform experience
        """
        try:
            query = UserFeedback.objects.all()
            
            if user_id:
                query = query.filter(user_id=user_id)
            if enrollment_id:
                query = query.filter(enrollment_id=enrollment_id)
            if module_id:
                query = query.filter(module_id=module_id)

            feedbacks = query.order_by('-updated_at')
            
            return {
                'feedbacks': [
                    {
                        'user_id': feedback.user_id,
                        'user_email': feedback.user.email,
                        'course_name': feedback.enrollment.course.title,
                        'module_id': feedback.module_id,
                        'content_delivery': feedback.quiz_feedback.get('content_delivery', {}),
                        'platform_experience': feedback.quiz_feedback.get('platform_experience', {}),
                        'learning_experience': feedback.quiz_feedback.get('learning_experience', {}),
                        'updated_at': feedback.updated_at
                    }
                    for feedback in feedbacks
                ]
            }
        except Exception as e:
            self.logger.error(f"Error retrieving course feedback: {str(e)}")
            return {'feedbacks': []}