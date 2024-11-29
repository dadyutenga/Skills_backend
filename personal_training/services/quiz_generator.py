import google.generativeai as genai
from django.conf import settings
from typing import List, Dict
import json

class QuizGenerationService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_quiz_prompt(self, topic: str, difficulty: str, num_questions: int) -> str:
        return f"""
        Generate a quiz about {topic} with the following specifications:
        - Difficulty level: {difficulty}
        - Number of questions: {num_questions}
        - Each question should have 4 multiple choice options
        - One correct answer per question
        - Include an explanation for the correct answer
        
        Format the response as a JSON object with this structure:
        {{
            "questions": [
                {{
                    "question_text": "string",
                    "choices": [
                        {{
                            "choice_text": "string",
                            "is_correct": boolean
                        }}
                    ],
                    "explanation": "string"
                }}
            ]
        }}
        """

    async def generate_quiz(self, topic: str, difficulty: str, num_questions: int = 5) -> Dict:
        prompt = self.generate_quiz_prompt(topic, difficulty, num_questions)
        response = await self.model.generate_content(prompt)
        
        try:
            # Extract JSON from response
            quiz_data = json.loads(response.text)
            return quiz_data
        except json.JSONDecodeError:
            raise ValueError("Failed to generate valid quiz data") 