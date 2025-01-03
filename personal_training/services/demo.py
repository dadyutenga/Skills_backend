from typing import Dict, List, Optional, Union
from datetime import datetime
import logging
from django.core.exceptions import ValidationError
from personal_training.models import Course, Category

logger = logging.getLogger(__name__)

class DemoService:
    """Service for handling user onboarding and personalized course recommendations"""

    # Age group definitions
    AGE_GROUPS = {
        'child': (5, 12),
        'teenager': (13, 17),
        'young_adult': (18, 25),
        'adult': (26, 50),
        'senior': (51, 100)
    }

    # TODO: Future Implementation - Learning style preferences
    # These styles will be used to personalize content delivery once all content types are fully implemented
    LEARNING_STYLES = {
        'text': 'Learn through written content and documentation',
        'video': 'Learn through video demonstrations',
        'articles': 'Learn through in-depth articles',
        'interactive': 'Learn through hands-on exercises'
    }

    def __init__(self):
        self.user_profile = {}
        self.recommendations = {}

    def initialize_user_profile(self, 
                              age: int,
                              experience_level: str,
                              has_mentor: bool = False,
                              learning_style: str = 'mixed') -> Dict:
        """
        Initialize user profile with basic information
        
        Args:
            age (int): User's age
            experience_level (str): Beginner/Intermediate/Advanced
            has_mentor (bool): Whether user wants mentor support
            learning_style (str): Preferred learning style
            
        Returns:
            Dict: User profile data
        """
        try:
            if not isinstance(age, int) or age < 5 or age > 100:
                raise ValidationError("Age must be between 5 and 100")

            if experience_level not in ['beginner', 'intermediate', 'advanced']:
                raise ValidationError("Invalid experience level")

            # Commented out learning style validation for future implementation
            # if learning_style not in self.LEARNING_STYLES.keys():
            #     raise ValidationError("Invalid learning style")

            self.user_profile = {
                'age': age,
                'age_group': self._determine_age_group(age),
                'experience_level': experience_level,
                'has_mentor': has_mentor,
                'learning_style': learning_style,  # Will keep storing but not validating for now
                'created_at': datetime.now().isoformat()
            }

            return self.user_profile

        except Exception as e:
            logger.error(f"Error initializing user profile: {str(e)}")
            raise

    def get_course_recommendations(self) -> Dict[str, List[Dict]]:
        """
        Generate personalized course recommendations based on user profile
        
        Returns:
            Dict: Categorized course recommendations
        """
        try:
            if not self.user_profile:
                raise ValidationError("User profile not initialized")

            # Get courses based on difficulty level and active status
            courses = Course.objects.filter(
                is_active=True,
                difficulty_level=self._map_experience_to_difficulty()
            )

            # Filter courses by age appropriateness using the model's method
            age = self.user_profile['age']
            age_appropriate_courses = [
                course for course in courses 
                if course.is_age_appropriate(age)
            ]

            # Organize recommendations by category
            self.recommendations = {
                'recommended': [
                    {
                        'id': course.id,
                        'title': course.title,
                        'category': course.category.name,
                        'difficulty': course.difficulty_level,
                        'duration_hours': course.duration_hours,
                        'thumbnail': course.thumbnail,
                        'preview_video': course.preview_video,
                        'overview': course.overview,
                        'learning_objectives': course.learning_objectives,
                        'prerequisites': course.prerequisites,
                        'modules_count': course.modules.count(),
                        'age_group': course.age_group,
                    }
                    for course in age_appropriate_courses[:5]  # Top 5 recommendations
                ],
                'alternative': [
                    {
                        'id': course.id,
                        'title': course.title,
                        'category': course.category.name,
                        'difficulty': course.difficulty_level,
                        'duration_hours': course.duration_hours,
                        'thumbnail': course.thumbnail,
                        'overview': course.overview,
                        'age_group': course.age_group,
                    }
                    for course in age_appropriate_courses[5:10]  # Next 5 recommendations
                ],
                'mentor_supported': [
                    {
                        'id': course.id,
                        'title': course.title,
                        'category': course.category.name,
                        'difficulty': course.difficulty_level,
                        'duration_hours': course.duration_hours,
                        'thumbnail': course.thumbnail,
                        'overview': course.overview,
                    }
                    for course in age_appropriate_courses 
                    if self.user_profile['has_mentor']
                ][:5]  # Top 5 mentor-supported courses
            }

            return self.recommendations

        except Exception as e:
            logger.error(f"Error generating course recommendations: {str(e)}")
            raise

    #def get_learning_path(self) -> Dict:
        """
        Generate a structured learning path based on user profile and recommendations
        
        Returns:
            Dict: Structured learning path with milestones
        """
        try:
            if not self.recommendations:
                self.get_course_recommendations()

            return {
                'profile': self.user_profile,
                'path': {
                    'beginner_milestones': self._generate_milestones('beginner'),
                    'intermediate_milestones': self._generate_milestones('intermediate'),
                    'advanced_milestones': self._generate_milestones('advanced'),
                },
                'estimated_completion_time': self._calculate_completion_time(),
                # Commented out learning style adaptations for future implementation
                # 'learning_style_adaptations': self._get_learning_style_adaptations()
            }

        except Exception as e:
            logger.error(f"Error generating learning path: {str(e)}")
            raise

    def _determine_age_group(self, age: int) -> str:
        """Determine user's age group"""
        for group, (min_age, max_age) in self.AGE_GROUPS.items():
            if min_age <= age <= max_age:
                return group
        return 'adult'  # Default age group

    def _map_experience_to_difficulty(self) -> str:
        """Map user experience level to course difficulty"""
        mapping = {
            'beginner': 'beginner',
            'intermediate': 'intermediate',
            'advanced': 'advanced'
        }
        return mapping.get(self.user_profile['experience_level'], 'beginner')

    def _filter_age_appropriate_courses(self, courses) -> List:
        """Filter courses based on age appropriateness"""
        age_group = self.user_profile['age_group']
        return [
            course for course in courses
            if self._is_course_age_appropriate(course, age_group)
        ]

    def _is_course_age_appropriate(self, course: Course, age_group: str) -> bool:
        """Check if course is appropriate for age group"""
        # Add your age appropriateness logic here
        return True  # Placeholder return

    def _get_primary_recommendations(self, courses) -> List[Dict]:
        """Get primary course recommendations"""
        return [
            {
                'id': course.id,
                'title': course.title,
                'category': course.category.name,
                'difficulty': course.difficulty_level,
                'duration_hours': course.duration_hours,
                # Commented out learning style match for future implementation
                # 'learning_style_match': self._calculate_learning_style_match(course)
            }
            for course in courses[:5]  # Top 5 recommendations
        ]

    def _get_alternative_recommendations(self, courses) -> List[Dict]:
        """Get alternative course recommendations"""
        return [
            {
                'id': course.id,
                'title': course.title,
                'category': course.category.name,
                'difficulty': course.difficulty_level,
                'duration_hours': course.duration_hours
            }
            for course in courses[5:10]  # Next 5 recommendations
        ]

    #def _get_mentor_supported_courses(self, courses) -> List[Dict]:
        """Get courses with mentor support"""
        try:
            if not self.user_profile.get('has_mentor'):
                return []

            mentor_supported_courses = [
                {
                    'id': course.id,
                    'title': course.title,
                    'category': course.category.name,
                    'difficulty': course.difficulty_level,
                    'duration_hours': course.duration_hours,
                    'thumbnail': course.thumbnail,
                    'overview': course.overview,
                    'prerequisites': course.prerequisites,
                    'modules_count': course.modules.count()
                }
                for course in courses
                if course.is_active and self._is_suitable_for_mentoring(course)
            ][:5]  # Limit to top 5 mentor-supported courses

            return mentor_supported_courses

        except Exception as e:
            logger.error(f"Error getting mentor supported courses: {str(e)}")
            return []

    def _is_suitable_for_mentoring(self, course: Course) -> bool:
        """
        Determine if a course is suitable for mentoring based on:
        - Course difficulty level
        - User's experience level
        """
        user_level = self.user_profile.get('experience_level', 'beginner')
        course_level = course.difficulty_level

        # Match mentoring suitability based on experience levels
        mentoring_matrix = {
            'beginner': ['beginner', 'intermediate'],
            'intermediate': ['intermediate', 'professional'],
            'advanced': ['professional']
        }

        return course_level in mentoring_matrix.get(user_level, [])

    def _calculate_completion_time(self) -> Dict:
        """Calculate estimated completion time for recommended courses"""
        return {
            'minimum_weeks': 8,
            'maximum_weeks': 12,
            'hours_per_week': 10
        }

    # Commented out helper methods for future learning style implementation
    # def _calculate_learning_style_match(self, course: Course) -> float:
    #     """Calculate how well a course matches user's learning style"""
    #     return 0.8  # Placeholder return

    # def _get_learning_style_adaptations(self) -> Dict:
    #     """Get learning style specific adaptations"""
    #     style = self.user_profile['learning_style']
    #     return {
    #         'recommended_materials': self._get_style_specific_materials(style),
    #         'study_techniques': self._get_style_specific_techniques(style),
    #         'tools': self._get_style_specific_tools(style)
    #     }

    # def _get_style_specific_materials(self, style: str) -> List[str]:
    #     """Get learning style specific materials"""
    #     materials_map = {
    #         'visual': ['Video tutorials', 'Infographics', 'Mind maps'],
    #         'auditory': ['Audio lectures', 'Podcast episodes', 'Group discussions'],
    #         'reading': ['Text tutorials', 'Documentation', 'Case studies'],
    #         'kinesthetic': ['Interactive exercises', 'Projects', 'Labs'],
    #         'mixed': ['Varied content types', 'Multi-modal resources']
    #     }
    #     return materials_map.get(style, [])

    # def _get_style_specific_techniques(self, style: str) -> List[str]:
    #     """Get learning style specific study techniques"""
    #     techniques_map = {
    #         'visual': ['Diagram creation', 'Visual note-taking'],
    #         'auditory': ['Recording summaries', 'Group discussions'],
    #         'reading': ['Note-taking', 'Summarization'],
    #         'kinesthetic': ['Practice exercises', 'Real-world applications'],
    #         'mixed': ['Mixed approach techniques']
    #     }
    #     return techniques_map.get(style, [])

    # def _get_style_specific_tools(self, style: str) -> List[str]:
    #     """Get learning style specific tools"""
    #     tools_map = {
    #         'visual': ['Mind mapping software', 'Video editing tools'],
    #         'auditory': ['Audio recording apps', 'Discussion platforms'],
    #         'reading': ['Note-taking apps', 'Document readers'],
    #         'kinesthetic': ['Interactive coding platforms', 'Project management tools'],
    #         'mixed': ['All-in-one learning platforms']
    #     }
    #     return tools_map.get(style, [])

    

