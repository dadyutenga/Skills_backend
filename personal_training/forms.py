from django import forms

class QuizGenerationForm(forms.Form):
    topic = forms.CharField(max_length=200)
    difficulty = forms.ChoiceField(choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ])
    num_questions = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=5
    )
    learning_material = forms.ModelChoiceField(
        queryset=LearningMaterial.objects.filter(content_type='quiz')
    ) 