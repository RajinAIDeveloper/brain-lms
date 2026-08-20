from django.core.management.base import BaseCommand

from accounts.models import ClassBatch, Enrollment, Level, ParentProfile, ParentStudentLink, StudentProfile, TeacherProfile, User


DEMO_PASSWORD = 'BrainGymMVP!2026'


class Command(BaseCommand):
    help = 'Create the four demo role accounts and their onboarding relationships.'

    def user(self, email, role, first_name, last_name):
        user, created = User.objects.get_or_create(email=email, defaults={'role': role, 'first_name': first_name, 'last_name': last_name})
        user.role = role
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = True
        user.set_password(DEMO_PASSWORD)
        if role == User.Role.ADMIN:
            user.is_staff = True
            user.is_superuser = True
        user.save()
        return user, created

    def handle(self, *args, **options):
        admin, _ = self.user('admin@braingym.local', User.Role.ADMIN, 'Amina', 'Admin')
        teacher, _ = self.user('teacher@braingym.local', User.Role.TEACHER, 'Nadia', 'Rahman')
        student, _ = self.user('student@braingym.local', User.Role.STUDENT, 'Sara', 'Ahmed')
        parent, _ = self.user('parent@braingym.local', User.Role.PARENT, 'Kamal', 'Ahmed')

        TeacherProfile.objects.get_or_create(user=teacher)
        level, _ = Level.objects.get_or_create(code='L2', defaults={'name': 'Level 2', 'description': 'Confident mental addition and subtraction'})
        student_profile, _ = StudentProfile.objects.get_or_create(user=student)
        student_profile.current_level = level
        student_profile.best_streak = 24
        student_profile.save()
        parent_profile, _ = ParentProfile.objects.get_or_create(user=parent)
        class_batch, _ = ClassBatch.objects.get_or_create(name='Batch A', level=level, defaults={'teacher': teacher})
        class_batch.teacher = teacher
        class_batch.is_active = True
        class_batch.save()
        Enrollment.objects.get_or_create(student=student_profile, class_batch=class_batch, defaults={'is_active': True})
        ParentStudentLink.objects.get_or_create(parent=parent_profile, student=student_profile, defaults={'relationship': 'Parent'})

        self.stdout.write(self.style.SUCCESS('Demo data is ready.'))
        self.stdout.write(f'Password for all demo users: {DEMO_PASSWORD}')
        self.stdout.write('admin@braingym.local · teacher@braingym.local · student@braingym.local · parent@braingym.local')
