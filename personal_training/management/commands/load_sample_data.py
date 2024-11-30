from django.core.management.base import BaseCommand
from django.utils.text import slugify
from personal_training.models import Category, Course, Module, Lesson, LearningMaterial

class Command(BaseCommand):
    help = 'Loads sample training data into the database'

    def handle(self, *args, **kwargs):
        # Create Categories
        self.stdout.write('Creating categories...')
        financial_cat = Category.objects.create(
            name="Financial Literacy",
            description="Learn essential financial management skills",
            slug="financial-literacy"
        )
        
        communication_cat = Category.objects.create(
            name="Communication Skills",
            description="Master professional communication techniques",
            slug="communication-skills"
        )

        # Create Courses
        self.stdout.write('Creating courses...')
        financial_course = Course.objects.create(
            category=financial_cat,
            title="Financial Literacy for Beginners",
            slug="financial-literacy-beginners",
            overview="Master essential financial concepts and practices",
            learning_objectives="Understand budgeting, saving, and basic financial planning",
            duration_hours=10,
            difficulty_level="beginner"
        )

        communication_course = Course.objects.create(
            category=communication_cat,
            title="Communication Skills for Professionals",
            slug="communication-skills-professionals",
            overview="Develop effective professional communication skills",
            learning_objectives="Master active listening, clear communication, and professional interaction",
            duration_hours=8,
            difficulty_level="intermediate"
        )

        # Create Modules
        self.stdout.write('Creating modules...')
        financial_module = Module.objects.create(
            course=financial_course,
            title="Budgeting Fundamentals",
            description="Learn the basics of effective budgeting",
            order=1
        )

        communication_module = Module.objects.create(
            course=communication_course,
            title="Active Listening Skills",
            description="Master the art of active listening",
            order=1
        )

        # Create Lessons
        self.stdout.write('Creating lessons...')
        budget_lesson = Lesson.objects.create(
            module=financial_module,
            title="Mastering Budgeting Basics",
            summary="Learn fundamental budgeting principles and the 50-30-20 rule",
            order=1,
            estimated_time_minutes=45,
            is_published=True
        )

        listening_lesson = Lesson.objects.create(
            module=communication_module,
            title="Excelling in Active Listening",
            summary="Learn key active listening techniques for professional settings",
            order=1,
            estimated_time_minutes=45,
            is_published=True
        )

        # Create Learning Materials
        self.stdout.write('Creating learning materials...')
        
        # Financial Literacy Materials
        LearningMaterial.objects.create(
            lesson=budget_lesson,
            title="Understanding the 50-30-20 Rule",
            content_type="text",
            content="""The 50-30-20 rule is a budgeting principle that suggests allocating your income as follows:

50% for needs (essential expenses)
30% for wants (non-essential items)
20% for savings and debt repayment

This simple framework helps create a balanced and sustainable budget.""",
            order=1,
            is_required=True
        )

        LearningMaterial.objects.create(
            lesson=budget_lesson,
            title="Practical Budgeting Examples",
            content_type="text",
            content="""Example 1: Monthly Income of $3000
- Needs ($1500): Rent, utilities, groceries, insurance
- Wants ($900): Entertainment, dining out, hobbies
- Savings ($600): Emergency fund, retirement, goals

Example 2: Monthly Income of $5000
- Needs ($2500): Housing, transportation, healthcare
- Wants ($1500): Travel, shopping, recreation
- Savings ($1000): Investments, future plans""",
            order=2,
            is_required=True
        )

        # Communication Skills Materials
        LearningMaterial.objects.create(
            lesson=listening_lesson,
            title="Core Active Listening Principles",
            content_type="text",
            content="""Active listening involves:
1. Maintaining eye contact
2. Using non-verbal cues to show engagement
3. Avoiding interruption
4. Asking clarifying questions
5. Paraphrasing to confirm understanding

These techniques help build trust and ensure clear communication.""",
            order=1,
            is_required=True
        )

        LearningMaterial.objects.create(
            lesson=listening_lesson,
            title="Professional Listening Scenarios",
            content_type="text",
            content="""Common workplace scenarios requiring active listening:
1. Team meetings and presentations
2. One-on-one feedback sessions
3. Client consultations
4. Problem-solving discussions
5. Performance reviews""",
            order=2,
            is_required=True
        )

        self.stdout.write(self.style.SUCCESS('Successfully loaded sample data')) 