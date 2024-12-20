import google.generativeai as genai
from django.conf import settings
from typing import Dict, List, Optional
import json
import os
from asgiref.sync import sync_to_async
from django.core.cache import cache
from datetime import datetime, timedelta

class FeedbackModule:
    """Module for handling comprehensive learning feedback and analytics"""
    
    def __init__(self):
        # Initialize Gemini AI for generating personalized feedback
        api_key = os.getenv('GEMINI_API_KEY') or settings.GEMINI_API_KEY
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    async def generate_quiz_feedback(
        self, 
        user_id: int,
        quiz_results: Dict,
        module_id: int,
        course_id: int
    ) -> Dict:
        """
        Generate comprehensive feedback for a completed quiz
        
        Args:
            user_id: The ID of the user
            quiz_results: Dict containing quiz answers and scores
            module_id: The module ID the quiz belongs to
            course_id: The course ID
        """
        try:
            # Calculate performance metrics
            total_questions = len(quiz_results['answers'])
            correct_answers = sum(1 for answer in quiz_results['answers'] if answer['is_correct'])
            score_percentage = (correct_answers / total_questions) * 100
            
            # Generate performance analysis prompt
            prompt = f"""
            Analyze this quiz performance and provide detailed feedback:
            
            Score: {score_percentage}%
            Correct Answers: {correct_answers}/{total_questions}
            Question Performance: {json.dumps(quiz_results['answers'], indent=2)}
            
            Provide feedback in this JSON format:
            {{
                "overall_assessment": "Overall performance analysis",
                "strength_areas": ["List of strong areas"],
                "improvement_areas": ["List of areas needing improvement"],
                "specific_recommendations": ["Detailed recommendations"],
                "next_steps": ["Suggested next steps for learning"],
                "confidence_level": "Assessment of user's confidence level"
            }}
            """
            
            response = await sync_to_async(self.model.generate_content)(prompt)
            feedback = json.loads(response.text)
            
            # Cache the feedback for future reference
            cache_key = f"quiz_feedback:{user_id}:{module_id}"
            cache.set(cache_key, feedback, timeout=60*60*24)  # 24 hours
            
            return feedback
            
        except Exception as e:
            return {
                "error": f"Failed to generate quiz feedback: {str(e)}",
                "overall_assessment": "Unable to generate detailed feedback",
                "recommendations": ["Please review the course material and try again"]
            }

    async def generate_answer_feedback(
        self,
        user_answer: str,
        correct_answer: str,
        question_context: str,
        question_type: str
    ) -> Dict:
        """
        Generate detailed feedback for a specific answer
        
        Args:
            user_answer: The user's submitted answer
            correct_answer: The correct answer
            question_context: Context or topic of the question
            question_type: Type of question (mcq, scenario, etc.)
        """
        try:
            prompt = f"""
            Analyze this answer and provide detailed feedback:
            
            Question Type: {question_type}
            Context: {question_context}
            Correct Answer: {correct_answer}
            User's Answer: {user_answer}
            
            Provide feedback in this JSON format:
            {{
                "accuracy_assessment": "Analysis of answer accuracy",
                "concept_understanding": "Assessment of concept understanding",
                "key_differences": "Key differences from correct answer",
                "improvement_suggestions": "Specific suggestions for improvement",
                "additional_resources": "Suggested resources for better understanding"
            }}
            """
            
            response = await sync_to_async(self.model.generate_content)(prompt)
            return json.loads(response.text)
            
        except Exception as e:
            return {
                "error": f"Failed to generate answer feedback: {str(e)}",
                "general_feedback": "Please review the correct answer and course materials"
            }

    async def generate_performance_feedback(
        self,
        user_id: int,
        module_id: int,
        time_period: str = "last_month"
    ) -> Dict:
        """
        Generate comprehensive performance feedback over time
        
        Args:
            user_id: The ID of the user
            module_id: The module ID
            time_period: Time period for analysis ("last_week", "last_month", etc.)
        """
        try:
            # Fetch historical performance data
            cache_key = f"performance_history:{user_id}:{module_id}"
            performance_history = cache.get(cache_key, {})
            
            prompt = f"""
            Analyze this learning performance history and provide insights:
            
            Performance History: {json.dumps(performance_history, indent=2)}
            Time Period: {time_period}
            
            Provide analysis in this JSON format:
            {{
                "performance_trend": "Analysis of performance trend",
                "learning_velocity": "Assessment of learning speed",
                "mastery_level": "Current level of mastery",
                "engagement_analysis": "Analysis of engagement patterns",
                "personalized_goals": ["Suggested learning goals"],
                "study_recommendations": ["Specific study recommendations"]
            }}
            """
            
            response = await sync_to_async(self.model.generate_content)(prompt)
            return json.loads(response.text)
            
        except Exception as e:
            return {
                "error": f"Failed to generate performance feedback: {str(e)}",
                "general_feedback": "Continue engaging with the course materials regularly"
            }

    def analyze_learning_patterns(
        self,
        user_id: int,
        course_id: int,
        timeframe_days: int = 30
    ) -> Dict:
        """
        Analyze user's learning patterns and behaviors
        
        Args:
            user_id: The ID of the user
            course_id: The course ID
            timeframe_days: Number of days to analyze
        """
        try:
            # Calculate key metrics
            completion_rate = self._calculate_completion_rate(user_id, course_id)
            engagement_score = self._calculate_engagement_score(user_id, course_id)
            progress_velocity = self._calculate_progress_velocity(user_id, course_id)
            
            return {
                "completion_rate": completion_rate,
                "engagement_score": engagement_score,
                "progress_velocity": progress_velocity,
                "learning_style": self._determine_learning_style(user_id),
                "strength_areas": self._identify_strength_areas(user_id, course_id),
                "challenge_areas": self._identify_challenge_areas(user_id, course_id)
            }
            
        except Exception as e:
            return {
                "error": f"Failed to analyze learning patterns: {str(e)}",
                "status": "Analysis unavailable"
            }

    async def get_improvement_suggestions(
        self,
        user_id: int,
        course_id: int,
        module_id: Optional[int] = None
    ) -> Dict:
        """
        Generate personalized improvement suggestions
        
        Args:
            user_id: The ID of the user
            course_id: The course ID
            module_id: Optional specific module ID
        """
        try:
            # Gather user's learning data
            performance_data = self._gather_performance_data(user_id, course_id, module_id)
            
            prompt = f"""
            Generate personalized improvement suggestions based on this data:
            
            Performance Data: {json.dumps(performance_data, indent=2)}
            
            Provide suggestions in this JSON format:
            {{
                "priority_areas": ["List of priority areas to focus on"],
                "specific_actions": ["Detailed actions to take"],
                "resource_recommendations": ["Recommended learning resources"],
                "practice_suggestions": ["Suggested practice exercises"],
                "milestone_goals": ["Suggested milestone goals"]
            }}
            """
            
            response = await sync_to_async(self.model.generate_content)(prompt)
            return json.loads(response.text)
            
        except Exception as e:
            return {
                "error": f"Failed to generate improvement suggestions: {str(e)}",
                "general_suggestions": ["Continue with the course materials", "Practice regularly"]
            }

    # Helper methods
    def _calculate_completion_rate(self, user_id: int, course_id: int) -> float:
        """Calculate the percentage of completed content in a course"""
        try:
            redis_key = f"course_progress:{user_id}:{course_id}"
            completed_items = cache.get(f"{redis_key}:completed", 0)
            total_items = cache.get(f"{redis_key}:total", 1)  # Default to 1 to avoid division by zero
            
            return (completed_items / total_items) * 100
        except Exception:
            return 0.0

    def _calculate_engagement_score(self, user_id: int, course_id: int) -> float:
        """Calculate user engagement score based on activity frequency and interaction quality"""
        try:
            # Get activity logs from the last 30 days
            redis_key = f"user_activity:{user_id}:{course_id}"
            activity_data = cache.get(redis_key, {})
            
            if not activity_data:
                return 0.0
            
            # Calculate engagement metrics
            login_frequency = activity_data.get('login_count', 0)
            content_interactions = activity_data.get('content_interactions', 0)
            avg_session_duration = activity_data.get('avg_session_duration', 0)
            
            # Weighted scoring (customize weights based on importance)
            engagement_score = (
                (login_frequency * 0.3) +
                (content_interactions * 0.4) +
                (min(avg_session_duration / 3600, 1) * 0.3)  # Normalize to 1 hour
            ) * 100
            
            return min(engagement_score, 100)  # Cap at 100
        except Exception:
            return 0.0

    def _calculate_progress_velocity(self, user_id: int, course_id: int) -> float:
        """Calculate the rate of progress (completed items per week)"""
        try:
            redis_key = f"progress_history:{user_id}:{course_id}"
            progress_data = cache.get(redis_key, [])
            
            if not progress_data:
                return 0.0
            
            # Calculate items completed in the last week
            week_ago = datetime.now() - timedelta(days=7)
            recent_progress = [
                p for p in progress_data 
                if datetime.fromisoformat(p['timestamp']) > week_ago
            ]
            
            return sum(p['completed_items'] for p in recent_progress)
        except Exception:
            return 0.0

    def _determine_learning_style(self, user_id: int) -> str:
        """Analyze user behavior to determine preferred learning style"""
        try:
            redis_key = f"learning_patterns:{user_id}"
            pattern_data = cache.get(redis_key, {})
            
            if not pattern_data:
                return "visual"  # Default learning style
            
            # Calculate time spent on different content types
            content_preferences = pattern_data.get('content_type_engagement', {})
            
            # Find the most engaged content type
            preferred_style = max(
                content_preferences.items(),
                key=lambda x: x[1],
                default=("visual", 0)
            )[0]
            
            return preferred_style
        except Exception:
            return "visual"

    def _identify_strength_areas(self, user_id: int, course_id: int) -> List[str]:
        """Identify topics where the user performs well"""
        try:
            redis_key = f"topic_performance:{user_id}:{course_id}"
            performance_data = cache.get(redis_key, {})
            
            if not performance_data:
                return []
            
            # Filter topics with score >= 80%
            strength_areas = [
                topic for topic, score in performance_data.items()
                if score >= 80
            ]
            
            return strength_areas[:5]  # Return top 5 strength areas
        except Exception:
            return []

    def _identify_challenge_areas(self, user_id: int, course_id: int) -> List[str]:
        """Identify topics where the user needs improvement"""
        try:
            redis_key = f"topic_performance:{user_id}:{course_id}"
            performance_data = cache.get(redis_key, {})
            
            if not performance_data:
                return []
            
            # Filter topics with score < 70%
            challenge_areas = [
                topic for topic, score in performance_data.items()
                if score < 70
            ]
            
            return challenge_areas[:5]  # Return top 5 challenge areas
        except Exception:
            return []

    def _gather_performance_data(self, user_id: int, course_id: int, module_id: Optional[int]) -> Dict:
        """Gather comprehensive performance data for analysis"""
        try:
            base_key = f"performance:{user_id}"
            
            # Get general performance metrics
            performance_data = {
                "completion_rate": self._calculate_completion_rate(user_id, course_id),
                "engagement_score": self._calculate_engagement_score(user_id, course_id),
                "progress_velocity": self._calculate_progress_velocity(user_id, course_id),
                "learning_style": self._determine_learning_style(user_id),
                "strength_areas": self._identify_strength_areas(user_id, course_id),
                "challenge_areas": self._identify_challenge_areas(user_id, course_id),
                "recent_activities": cache.get(f"{base_key}:recent_activities", []),
                "assessment_scores": cache.get(f"{base_key}:assessment_scores", [])
            }
            
            # Add module-specific data if module_id is provided
            if module_id:
                module_key = f"{base_key}:module:{module_id}"
                performance_data.update({
                    "module_progress": cache.get(f"{module_key}:progress", 0),
                    "module_scores": cache.get(f"{module_key}:scores", []),
                    "time_spent": cache.get(f"{module_key}:time_spent", 0)
                })
            
            return performance_data
        except Exception as e:
            return {
                "error": f"Failed to gather performance data: {str(e)}",
                "status": "Data unavailable"
            }
