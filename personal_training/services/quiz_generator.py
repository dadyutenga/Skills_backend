import google.generativeai as genai
from django.conf import settings
from typing import List, Dict, Optional
import json
import os

class QuizGenerationService:
    def __init__(self):
        # Get API key from environment variables
        api_key = os.getenv('GEMINI_API_KEY') or settings.GEMINI_API_KEY
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def _get_lesson_content(self, lesson_materials: List[Dict]) -> str:
        """Extract relevant content from lesson materials"""
        content = []
        for material in lesson_materials:
            if material['content_type'] != 'quiz':  # Skip existing quizzes
                content.append(f"Topic: {material['title']}\n{material['content']}")
        return "\n\n".join(content)

    def generate_quiz_prompt(self, 
                           content: str, 
                           num_questions: int,
                           difficulty: str = 'intermediate') -> str:
        return f"""
        As an expert quiz generator, create a quiz based on the following lesson content.
        
        Requirements:
        - Number of questions: {num_questions}
        - Difficulty level: {difficulty}
        - Each question must have exactly 4 multiple choice options
        - Exactly one correct answer per question
        - Include a clear explanation for why the correct answer is right
        
        Lesson Content:
        {content}
        
        Return the response in this exact JSON format:
        {{
            "questions": [
                {{
                    "question_text": "The actual question",
                    "choices": [
                        {{"choice_text": "Correct answer", "is_correct": true}},
                        {{"choice_text": "Wrong answer 1", "is_correct": false}},
                        {{"choice_text": "Wrong answer 2", "is_correct": false}},
                        {{"choice_text": "Wrong answer 3", "is_correct": false}}
                    ],
                    "explanation": "Detailed explanation of why the correct answer is right"
                }}
            ]
        }}

        Ensure:
        1. Questions are clear and directly related to the content
        2. All answers are plausible but only one is correct
        3. Explanations are helpful for learning
        4. The response is valid JSON
        """

    def validate_quiz_data(self, quiz_data: Dict) -> bool:
        """Validate the structure and content of generated quiz data"""
        try:
            questions = quiz_data.get('questions', [])
            if not questions or not isinstance(questions, list):
                return False

            for question in questions:
                # Check required fields
                if not all(key in question for key in ['question_text', 'choices', 'explanation']):
                    return False
                
                choices = question['choices']
                # Verify exactly 4 choices
                if len(choices) != 4:
                    return False
                
                # Verify exactly one correct answer
                correct_answers = sum(1 for choice in choices if choice['is_correct'])
                if correct_answers != 1:
                    return False

            return True
        except Exception:
            return False

    def format_quiz_data(self, quiz_data: Dict) -> Dict:
        """Format and clean the quiz data if needed"""
        formatted_questions = []
        
        for question in quiz_data['questions']:
            # Ensure choices are in a consistent order (correct answer not always first)
            choices = question['choices']
            # Shuffle choices if needed
            
            formatted_questions.append({
                'question_text': question['question_text'].strip(),
                'choices': [
                    {
                        'choice_text': choice['choice_text'].strip(),
                        'is_correct': choice['is_correct']
                    }
                    for choice in choices
                ],
                'explanation': question['explanation'].strip()
            })

        return {'questions': formatted_questions}

    async def generate_quiz(self, 
                          topic: str,
                          num_questions: int = 5,
                          difficulty: str = 'intermediate') -> Dict:
        """
        Main method to generate a quiz based on topic
        
        Args:
            topic: The topic to generate questions about
            num_questions: Number of questions to generate
            difficulty: Difficulty level of the quiz
            
        Returns:
            Dictionary containing formatted quiz data
            
        Raises:
            ValueError: If quiz generation or validation fails
        """
        try:
            # Generate the quiz directly from topic
            prompt = self.generate_quiz_prompt(topic, num_questions, difficulty)
            
            # Generate content with Gemini
            response = await self.model.generate_content(prompt)
            
            # Extract the text from the response
            response_text = response.text
            
            try:
                # First try direct JSON parsing
                quiz_data = json.loads(response_text)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response_text[start_idx:end_idx]
                    quiz_data = json.loads(json_str)
                else:
                    raise ValueError("Could not find valid JSON in response")
            
            # Validate the generated data
            if not self.validate_quiz_data(quiz_data):
                raise ValueError("Generated quiz data failed validation")
            
            # Format and return the quiz data
            return self.format_quiz_data(quiz_data)
            
        except Exception as e:
            print(f"Error generating quiz: {str(e)}")  # Add debugging
            raise ValueError(f"Quiz generation failed: {str(e)}")

    async def regenerate_question(self, 
                                content: str,
                                existing_question: Dict,
                                difficulty: str = 'intermediate') -> Dict:
        try:
            prompt = f"""
            Generate a new alternative question about this content:
            {content}
            
            The new question should be different from this existing question:
            {existing_question['question_text']}
            
            Difficulty level: {difficulty}
            
            Return in the same JSON format as before.
            """
            
            response = await self.model.generate_content(prompt)
            response_text = response.text
            
            try:
                quiz_data = json.loads(response_text)
            except json.JSONDecodeError:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response_text[start_idx:end_idx]
                    quiz_data = json.loads(json_str)
                else:
                    raise ValueError("Could not find valid JSON in response")
            
            if not self.validate_quiz_data(quiz_data):
                raise ValueError("Generated question failed validation")
                
            return quiz_data['questions'][0]
            
        except Exception as e:
            print(f"Error regenerating question: {str(e)}")  # Add debugging
            raise ValueError(f"Question regeneration failed: {str(e)}")