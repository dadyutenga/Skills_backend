from django import forms
from .models import Lesson, Quiz

class QuizGenerationForm(forms.Form):
    topic = forms.CharField(
        max_length=200,
        help_text="The main topic for the quiz"
    )
    
    difficulty = forms.ChoiceField(
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        initial='intermediate'
    )
    
    num_questions = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=5,
        help_text="Number of questions to generate (max 20)"
    ) 