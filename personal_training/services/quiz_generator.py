import google.generativeai as genai
from django.conf import settings
import json
import os
from asgiref.sync import sync_to_async

class QuizGenerationService:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY') or settings.GEMINI_API_KEY
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def _format_prompt(self, content: str, num_questions: int = 5) -> str:
        return f"""
        Generate a quiz based on this content. Format your response as a valid JSON object.

        Content to quiz on:
        {content}

        Rules:
        1. Generate {num_questions} questions
        2. Each question must have:
           - Clear question text
           - Exactly 4 multiple choice options
           - Only one correct answer
           - A clear explanation for the correct answer
        3. Make questions engaging and relevant to the content
        4. Vary question difficulty

        Return ONLY a JSON object in this exact format:
        {{
            "questions": [
                {{
                    "question_text": "Question goes here?",
                    "choices": [
                        {{"choice_text": "Correct answer", "is_correct": true}},
                        {{"choice_text": "Wrong answer 1", "is_correct": false}},
                        {{"choice_text": "Wrong answer 2", "is_correct": false}},
                        {{"choice_text": "Wrong answer 3", "is_correct": false}}
                    ],
                    "explanation": "Explanation why the correct answer is right"
                }}
            ]
        }}

        IMPORTANT: Return ONLY the JSON object, no other text.
        """

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

    def _validate_quiz_data(self, quiz_data: dict) -> bool:
        """Validate the quiz data structure."""
        if not isinstance(quiz_data, dict) or 'questions' not in quiz_data:
            return False
            
        questions = quiz_data['questions']
        if not isinstance(questions, list) or not questions:
            return False
            
        for question in questions:
            if not all(key in question for key in ['question_text', 'choices', 'explanation']):
                return False
                
            choices = question['choices']
            if len(choices) != 4:
                return False
                
            correct_answers = sum(1 for choice in choices if choice['is_correct'])
            if correct_answers != 1:
                return False
                
        return True

    async def generate_quiz(self, topic: str, num_questions: int = 5) -> dict:
        """Generate a quiz based on the given topic."""
        try:
            # Generate the prompt
            prompt = self._format_prompt(topic, num_questions)
            
            # Get response from Gemini
            response = await sync_to_async(self.model.generate_content)(prompt)
            
            # Clean and parse the response
            json_str = self._clean_response(response.text)
            quiz_data = json.loads(json_str)
            
            # Validate the quiz data
            if not self._validate_quiz_data(quiz_data):
                raise ValueError("Generated quiz data failed validation")
                
            return quiz_data
            
        except Exception as e:
            raise ValueError(f"Quiz generation failed: {str(e)}")