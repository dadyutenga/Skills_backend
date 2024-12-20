from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q, F, Sum
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from personal_training.models import Course, Module
from Oauth.models import User

class ProgressTrackingService:
    """
    Comprehensive service for tracking and analyzing user progress in courses and modules
    """
    
    def __init__(self, user: User):
        self.user = user
        self.redis_client = self._initialize_redis_client()

    def track_module_progress(self, module_id: int, progress_data: Dict) -> Dict:
        """
        Track user progress in a specific module with detailed analytics
        
        Args:
            module_id: Module identifier
            progress_data: Dict containing progress metrics
                {
                    'completion_status': float,
                    'time_spent': int,
                    'interaction_points': int,
                    'content_progress': Dict,
                    'assessment_results': Dict
                }
        """
        try:
            with transaction.atomic():
                module = Module.objects.select_related('course').get(id=module_id)
                
                # Validate user access and prerequisites
                self._validate_module_access(module)
                
                # Calculate comprehensive progress metrics
                progress_metrics = self._calculate_module_metrics(module, progress_data)
                
                # Update Redis cache for real-time tracking
                self._update_redis_progress(module_id, progress_metrics)
                
                # Update course progress if module completed
                if progress_metrics['is_completed']:
                    self._update_course_progress(module.course_id)
                
                return {
                    'module_progress': progress_metrics,
                    'course_progress': self._get_course_progress(module.course_id),
                    'recommendations': self._generate_recommendations(module)
                }
                
        except Exception as e:
            self._log_error(f"Error tracking module progress: {str(e)}")
            raise

    def get_user_progress_analytics(self, course_id: Optional[int] = None) -> Dict:
        """
        Get detailed analytics of user's progress across courses or for a specific course
        """
        try:
            filters = {'user': self.user}
            if course_id:
                filters['course_id'] = course_id
            
            # Aggregate progress data
            progress_data = self._aggregate_progress_data(filters)
            
            # Analyze learning patterns
            learning_patterns = self._analyze_learning_patterns()
            
            # Generate performance insights
            performance_insights = self._generate_performance_insights(progress_data)
            
            return {
                'progress_summary': progress_data,
                'learning_patterns': learning_patterns,
                'performance_insights': performance_insights,
                'recommendations': self._generate_personalized_recommendations()
            }
            
        except Exception as e:
            self._log_error(f"Error fetching progress analytics: {str(e)}")
            raise

    def update_course_progress(self, course_id: int) -> Dict:
        """
        Update overall course progress with comprehensive metrics
        """
        try:
            with transaction.atomic():
                course = Course.objects.get(id=course_id)
                modules = course.modules.all()
                
                # Calculate module completion rates
                module_progress = self._calculate_modules_progress(modules)
                
                # Update overall course progress
                course_progress = self._update_course_completion(course, module_progress)
                
                # Generate achievement milestones
                achievements = self._process_achievements(course_progress)
                
                return {
                    'course_progress': course_progress,
                    'module_breakdown': module_progress,
                    'achievements': achievements,
                    'next_steps': self._generate_next_steps(course_progress)
                }
                
        except Exception as e:
            self._log_error(f"Error updating course progress: {str(e)}")
            raise

    def _calculate_module_metrics(self, module: Module, progress_data: Dict) -> Dict:
        """Calculate comprehensive module progress metrics"""
        base_metrics = {
            'completion_percentage': progress_data['completion_status'],
            'time_spent_minutes': progress_data['time_spent'],
            'interaction_score': self._calculate_interaction_score(progress_data),
            'last_interaction': timezone.now()
        }
        
        # Enhance with advanced metrics
        enhanced_metrics = {
            **base_metrics,
            'engagement_score': self._calculate_engagement_score(base_metrics),
            'mastery_level': self._assess_mastery_level(progress_data),
            'learning_velocity': self._calculate_learning_velocity(module, base_metrics)
        }
        
        return enhanced_metrics

    def _analyze_learning_patterns(self) -> Dict:
        """Analyze user's learning patterns and preferences"""
        recent_activities = self._get_recent_activities()
        
        return {
            'peak_learning_hours': self._identify_peak_hours(recent_activities),
            'content_type_preferences': self._analyze_content_preferences(),
            'learning_consistency': self._calculate_learning_consistency(),
            'engagement_trends': self._analyze_engagement_trends()
        }

    def _generate_performance_insights(self, progress_data: Dict) -> List[Dict]:
        """Generate actionable insights based on performance data"""
        insights = []
        
        # Analyze completion patterns
        completion_insight = self._analyze_completion_patterns(progress_data)
        if completion_insight:
            insights.append(completion_insight)
        
        # Analyze engagement levels
        engagement_insight = self._analyze_engagement_levels(progress_data)
        if engagement_insight:
            insights.append(engagement_insight)
        
        # Generate improvement recommendations
        improvement_insights = self._generate_improvement_recommendations(progress_data)
        insights.extend(improvement_insights)
        
        return insights

    def _calculate_learning_velocity(self, module: Module, metrics: Dict) -> float:
        """Calculate user's learning velocity for the module"""
        historical_velocity = self._get_historical_velocity()
        current_velocity = metrics['completion_percentage'] / max(metrics['time_spent_minutes'], 1)
        
        # Apply weighted average
        velocity = (0.7 * current_velocity) + (0.3 * historical_velocity)
        
        # Store for future reference
        self._store_velocity_metric(module.id, velocity)
        
        return velocity

    def _generate_next_steps(self, progress: Dict) -> List[Dict]:
        """Generate personalized next steps based on progress"""
        next_steps = []
        
        # Identify knowledge gaps
        gaps = self._identify_knowledge_gaps(progress)
        
        # Generate recommendations
        for gap in gaps:
            next_steps.append({
                'type': 'knowledge_gap',
                'description': gap['description'],
                'recommended_actions': self._get_recommended_actions(gap),
                'priority': gap['priority']
            })
        
        # Add skill improvement recommendations
        skill_recommendations = self._generate_skill_recommendations(progress)
        next_steps.extend(skill_recommendations)
        
        return sorted(next_steps, key=lambda x: x['priority'], reverse=True)

    def _process_achievements(self, progress: Dict) -> List[Dict]:
        """Process and generate achievements based on progress"""
        achievements = []
        
        # Check for milestone achievements
        milestone_achievements = self._check_milestone_achievements(progress)
        achievements.extend(milestone_achievements)
        
        # Check for skill mastery achievements
        mastery_achievements = self._check_mastery_achievements(progress)
        achievements.extend(mastery_achievements)
        
        # Store achievements
        self._store_achievements(achievements)
        
        return achievements

    # Additional helper methods...
    def _validate_module_access(self, module: Module) -> None:
        """Validate user's access to module and prerequisites"""
        if not self._has_module_access(module):
            raise ValidationError("User does not have access to this module")
        
        if not self._prerequisites_completed(module):
            raise ValidationError("Module prerequisites not completed")

   

    def _log_error(self, error_message: str) -> None:
        """
        Log error with comprehensive context and metrics
        
        Args:
            error_message: Primary error message to log
        """
        try:
            logger = logging.getLogger(__name__)
            
            # Gather detailed context
            error_context = {
                'user_id': str(self.user.id),
                'user_email': self.user.email,
                'timestamp': datetime.now().isoformat(),
                'service': 'ProgressTrackingService',
                'environment': settings.ENVIRONMENT,
                'error': error_message,
                'stack_trace': traceback.format_exc(),
                'session_data': {
                    'last_activity': self.user.last_login.isoformat() if self.user.last_login else None,
                    'current_course': getattr(self, '_current_course_id', None),
                    'current_module': getattr(self, '_current_module_id', None),
                    'progress_cache_status': bool(self.redis_client.ping())
                },
                'performance_metrics': {
                    'memory_usage': self._get_memory_usage(),
                    'cache_hits': self.redis_client.info().get('keyspace_hits', 0),
                    'cache_misses': self.redis_client.info().get('keyspace_misses', 0)
                }
            }

            # Log to different streams based on error severity
            if 'CRITICAL' in error_message.upper() or 'FATAL' in error_message.upper():
                logger.critical(
                    f"CRITICAL Progress Tracking Error: {error_message}",
                    extra=error_context,
                    exc_info=True
                )
                # Alert DevOps for critical errors
                self._alert_devops(error_context)
                
            elif 'WARNING' in error_message.upper():
                logger.warning(
                    f"Progress Tracking Warning: {error_message}",
                    extra=error_context
                )
            else:
                logger.error(
                    f"Progress Tracking Error: {error_message}",
                    extra=error_context,
                    exc_info=True
                )

            # Store error in Redis for real-time monitoring
            self._cache_error(error_context)
            
            # Update error metrics
            self._update_error_metrics(error_context)

        except Exception as e:
            # Fallback logging if main logging fails
            fallback_logger = logging.getLogger('fallback')
            fallback_logger.error(
                f"Fallback Error Log - Original: {error_message}, Logging Error: {str(e)}",
                exc_info=True
            )
