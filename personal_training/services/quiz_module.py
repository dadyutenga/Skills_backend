import google.generativeai as genai
from django.conf import settings
import json
import os
from asgiref.sync import sync_to_async
from typing import Dict, List, Optional
from ..models import Quiz, UserQuizHistory

class QuizGenerationService:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY') or settings.GEMINI_API_KEY
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def _format_prompt(self, content: str, question_types: Dict[str, int], difficulty: str) -> str:
        type_descriptions = {
            'mcq': 'standard multiple choice questions testing knowledge recall',
            'scenario': 'scenario-based questions that present a situation and ask for analysis',
            'application': 'questions that test application of concepts to real-world situations',
            'reflection': 'questions that encourage reflection on personal experiences',
            'discussion': 'open-ended questions that promote discussion and critical thinking'
        }
        
        prompt = f"""
        Generate a quiz based on this content. Format your response as a valid JSON object.

        Content to quiz on:
        {content}

        Question Types Required:
        {', '.join([f'{count} {type_descriptions[qtype]}' for qtype, count in question_types.items()])}

        Difficulty Level: {difficulty}

        Rules:
        1. Generate questions according to the specified types and counts
        2. Each question must have:
           - Clear question text
           - For MCQs: Exactly 4 multiple choice options
           - For other types: Appropriate response format
           - Clear explanation or model answer
           - Difficulty level matching the specified level
        3. For scenario-based questions:
           - Include detailed scenario context
           - Make scenarios relevant to real-world applications
        4. For application questions:
           - Focus on practical applications of concepts
           - Include real-world examples
        5. For reflective questions:
           - Encourage personal insight
           - Connect concepts to personal experience
        6. For discussion questions:
           - Promote critical thinking
           - Allow for multiple valid perspectives

        Return ONLY a JSON object in this exact format:
        {{
            "questions": [
                {{
                    "question_text": "Question goes here?",
                    "question_type": "mcq|scenario|application|reflection|discussion",
                    "difficulty_level": "{difficulty}",
                    "scenario_context": "For scenario-based questions only",
                    "choices": [  // For MCQ type only
                        {{"choice_text": "Correct answer", "is_correct": true}},
                        {{"choice_text": "Wrong answer 1", "is_correct": false}},
                        {{"choice_text": "Wrong answer 2", "is_correct": false}},
                        {{"choice_text": "Wrong answer 3", "is_correct": false}}
                    ],
                    "model_answer": "For non-MCQ questions, provide a model answer or evaluation criteria",
                    "explanation": "Explanation of the correct answer or key points"
                }}
            ]
        }}

        IMPORTANT: Return ONLY the JSON object, no other text.
        """
        return prompt

    def _clean_response(self, response_text: str) -> str:
        """Clean the response text to extract valid JSON."""
        # Find the first { and last }
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        
        if start == -1 or end == 0:
            raise ValueError("No JSON object found in response")
            
        json_str = response_text[start:end]
        
        # Validate it's proper JSON
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON structure in response")

    def _validate_quiz_data(self, quiz_data: dict, question_types: Dict[str, int]) -> bool:
        """Validate the quiz data structure."""
        if not isinstance(quiz_data, dict) or 'questions' not in quiz_data:
            return False
            
        questions = quiz_data['questions']
        if not isinstance(questions, list) or not questions:
            return False
            
        # Count questions by type
        type_counts = {}
        for question in questions:
            if not all(key in question for key in ['question_text', 'question_type', 'difficulty_level', 'explanation']):
                return False
                
            qtype = question['question_type']
            type_counts[qtype] = type_counts.get(qtype, 0) + 1
            
            # Validate MCQ structure
            if qtype == 'mcq':
                if 'choices' not in question:
                    return False
                choices = question['choices']
                if len(choices) != 4:
                    return False
                correct_answers = sum(1 for choice in choices if choice['is_correct'])
                if correct_answers != 1:
                    return False
            # Validate scenario questions
            elif qtype == 'scenario':
                if not question.get('scenario_context'):
                    return False
            # Validate other question types
            elif qtype in ['application', 'reflection', 'discussion']:
                if not question.get('model_answer'):
                    return False
                    
        # Verify question type counts match requirements
        for qtype, count in question_types.items():
            if type_counts.get(qtype, 0) != count:
                return False
                
        return True

    async def generate_quiz(self, topic: str, question_types: Optional[Dict[str, int]] = None, 
                          difficulty: str = 'intermediate', user_id: Optional[int] = None,
                          quiz_id: Optional[int] = None) -> dict:
        """Generate a quiz based on the given topic with specified question types and difficulty."""
        try:
            # If no question types specified, default to 5 MCQs
            if not question_types:
                question_types = {'mcq': 5}
                
            # If user_id and quiz_id provided, adjust difficulty based on history
            if user_id and quiz_id:
                difficulty = await self._get_adaptive_difficulty(user_id, quiz_id, difficulty)
            
            # Generate the prompt
            prompt = self._format_prompt(topic, question_types, difficulty)
            
            # Get response from Gemini
            response = await sync_to_async(self.model.generate_content)(prompt)
            
            # Clean and parse the response
            json_str = self._clean_response(response.text)
            quiz_data = json.loads(json_str)
            
            # Validate the quiz data
            if not self._validate_quiz_data(quiz_data, question_types):
                raise ValueError("Generated quiz data failed validation")
                
            return quiz_data
            
        except Exception as e:
            raise ValueError(f"Quiz generation failed: {str(e)}")
            
    async def _get_adaptive_difficulty(self, user_id: int, quiz_id: int, default_difficulty: str) -> str:
        """Determine appropriate difficulty level based on user's quiz history."""
        try:
            history = await sync_to_async(UserQuizHistory.objects.get)(
                user_id=user_id,
                quiz_id=quiz_id
            )
            
            # If user consistently scores high, increase difficulty
            if history.average_score >= 90 and len(history.performance_trend) >= 3:
                recent_scores = history.performance_trend[-3:]
                if all(score >= 85 for score in recent_scores):
                    if default_difficulty == 'beginner':
                        return 'intermediate'
                    elif default_difficulty == 'intermediate':
                        return 'advanced'
                        
            # If user consistently scores low, decrease difficulty
            elif history.average_score <= 60 and len(history.performance_trend) >= 3:
                recent_scores = history.performance_trend[-3:]
                if all(score <= 65 for score in recent_scores):
                    if default_difficulty == 'advanced':
                        return 'intermediate'
                    elif default_difficulty == 'intermediate':
                        return 'beginner'
                        
        except UserQuizHistory.DoesNotExist:
            pass
            
        return default_difficulty
            
    async def generate_feedback(self, user_answer: str, correct_answer: str, 
                              question_type: str, context: Optional[str] = None) -> str:
        """Generate personalized feedback for a user's answer."""
        try:
            prompt = f"""
            Analyze this answer and provide constructive feedback.
            
            Question Type: {question_type}
            {"Context: " + context if context else ""}
            Correct Answer: {correct_answer}
            User's Answer: {user_answer}
            
            Provide feedback that:
            1. Acknowledges what the user did well
            2. Identifies areas for improvement
            3. Explains key concepts they might have missed
            4. Offers specific suggestions for improvement
            
            Format your response as a JSON object with these fields:
            {{
                "strengths": "What the user did well",
                "areas_for_improvement": "What could be better",
                "key_concepts": "Important concepts to remember",
                "suggestions": "Specific tips for improvement"
            }}
            """
            
            response = await sync_to_async(self.model.generate_content)(prompt)
            feedback_data = json.loads(self._clean_response(response.text))
            return feedback_data
            
        except Exception as e:
            return {
                "strengths": "Unable to analyze strengths",
                "areas_for_improvement": "Unable to analyze areas for improvement",
                "key_concepts": "Please review the correct answer",
                "suggestions": "Try reviewing the related course materials"
            }