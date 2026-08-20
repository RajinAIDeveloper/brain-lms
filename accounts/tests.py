from django.test import TestCase
from django.urls import reverse

from .management.commands.seed_demo import DEMO_PASSWORD
from .models import ClassBatch, Enrollment, Level, ParentProfile, ParentStudentLink, StudentProfile, TeacherProfile, User


class AuthenticationAndOnboardingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.call_command = __import__('django.core.management', fromlist=['call_command']).call_command
        cls.call_command('seed_demo')

    def test_all_demo_users_login_and_redirect_to_role_dashboard(self):
        expected = {
            'admin@braingym.local': '/dashboard/admin/',
            'teacher@braingym.local': '/dashboard/teacher/',
            'student@braingym.local': '/dashboard/student/',
            'parent@braingym.local': '/dashboard/parent/',
        }
        for email, location in expected.items():
            with self.subTest(email=email):
                self.client.logout()
                self.assertTrue(self.client.login(email=email, password=DEMO_PASSWORD))
                response = self.client.get(reverse('accounts:dashboard'))
                self.assertRedirects(response, location)

    def test_onboarding_relationships_are_seeded(self):
        self.assertEqual(ParentStudentLink.objects.count(), 1)
        self.assertEqual(Enrollment.objects.count(), 1)
        self.assertEqual(ClassBatch.objects.first().teacher.role, User.Role.TEACHER)

    def test_each_role_dashboard_renders(self):
        paths = {
            'admin@braingym.local': '/dashboard/admin/',
            'teacher@braingym.local': '/dashboard/teacher/',
            'student@braingym.local': '/dashboard/student/',
            'parent@braingym.local': '/dashboard/parent/',
        }
        for email, path in paths.items():
            with self.subTest(email=email):
                self.client.logout()
                self.client.login(email=email, password=DEMO_PASSWORD)
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_role_boundaries_block_other_dashboards(self):
        self.client.login(email='student@braingym.local', password=DEMO_PASSWORD)
        response = self.client.get(reverse('accounts:admin_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_open_user_creation_form(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        response = self.client.get('/admin/accounts/user/add/')
        self.assertEqual(response.status_code, 200)

    def test_logout_uses_post_and_ends_session(self):
        self.client.login(email='student@braingym.local', password=DEMO_PASSWORD)
        response = self.client.post('/logout/')
        self.assertRedirects(response, '/login/')
        self.assertRedirects(self.client.get('/dashboard/'), '/login/?next=/dashboard/')

    def test_admin_can_create_each_non_admin_role_account(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        self.assertEqual(self.client.get('/dashboard/admin/accounts/new/').status_code, 200)
        for role, email in [('TEACHER', 'new.teacher@braingym.local'), ('STUDENT', 'new.student@braingym.local'), ('PARENT', 'new.parent@braingym.local')]:
            with self.subTest(role=role):
                response = self.client.post('/dashboard/admin/accounts/new/', {
                    'first_name': 'New', 'last_name': role.title(), 'email': email,
                    'role': role, 'password1': 'SecureMVP!123', 'password2': 'SecureMVP!123',
                })
                self.assertRedirects(response, '/dashboard/admin/')
                user = User.objects.get(email=email)
                self.assertEqual(user.role, role)
                self.assertTrue(user.check_password('SecureMVP!123'))
        self.assertTrue(TeacherProfile.objects.filter(user__email='new.teacher@braingym.local').exists())
        self.assertTrue(StudentProfile.objects.filter(user__email='new.student@braingym.local').exists())
        self.assertTrue(ParentProfile.objects.filter(user__email='new.parent@braingym.local').exists())

    def test_non_admin_cannot_open_account_creation(self):
        self.client.login(email='teacher@braingym.local', password=DEMO_PASSWORD)
        self.assertEqual(self.client.get('/dashboard/admin/accounts/new/').status_code, 403)

    def test_admin_teacher_crud(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        self.assertEqual(self.client.get('/dashboard/admin/users/').status_code, 200)
        create_response = self.client.post('/dashboard/admin/teachers/new/', {
            'first_name': 'Mira', 'last_name': 'Coach', 'email': 'mira@braingym.local',
            'role': 'TEACHER', 'password1': 'SecureMVP!123', 'password2': 'SecureMVP!123',
        })
        teacher = User.objects.get(email='mira@braingym.local')
        self.assertRedirects(create_response, f'/dashboard/admin/teachers/{teacher.pk}/')
        self.assertEqual(self.client.get(f'/dashboard/admin/teachers/{teacher.pk}/').status_code, 200)
        edit_response = self.client.post(f'/dashboard/admin/teachers/{teacher.pk}/edit/', {
            'first_name': 'Mira', 'last_name': 'Lead Coach', 'email': 'mira@braingym.local',
            'display_title': 'Senior Math Coach', 'is_active': 'on',
        })
        self.assertRedirects(edit_response, f'/dashboard/admin/teachers/{teacher.pk}/')
        teacher.refresh_from_db()
        self.assertEqual(teacher.teacher_profile.display_title, 'Senior Math Coach')
        delete_response = self.client.post(f'/dashboard/admin/teachers/{teacher.pk}/delete/')
        self.assertRedirects(delete_response, '/dashboard/admin/teachers/')
        self.assertFalse(User.objects.filter(pk=teacher.pk).exists())

    def test_teacher_with_class_cannot_be_deleted(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        teacher = User.objects.get(email='teacher@braingym.local')
        response = self.client.post(f'/dashboard/admin/teachers/{teacher.pk}/delete/')
        self.assertRedirects(response, f'/dashboard/admin/teachers/{teacher.pk}/')
        self.assertTrue(User.objects.filter(pk=teacher.pk).exists())

    def test_admin_student_crud(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        self.assertEqual(self.client.get('/dashboard/admin/students/').status_code, 200)
        level = Level.objects.first()
        create_response = self.client.post('/dashboard/admin/students/new/', {
            'first_name': 'Lina', 'last_name': 'Learner', 'email': 'lina@braingym.local',
            'role': 'STUDENT', 'password1': 'SecureMVP!123', 'password2': 'SecureMVP!123',
        })
        student = User.objects.get(email='lina@braingym.local')
        self.assertRedirects(create_response, f'/dashboard/admin/students/{student.pk}/')
        self.assertEqual(self.client.get(f'/dashboard/admin/students/{student.pk}/').status_code, 200)
        edit_response = self.client.post(f'/dashboard/admin/students/{student.pk}/edit/', {
            'first_name': 'Lina', 'last_name': 'Learner', 'email': 'lina@braingym.local',
            'current_level': str(level.pk), 'is_active': 'on',
        })
        self.assertRedirects(edit_response, f'/dashboard/admin/students/{student.pk}/')
        student.refresh_from_db()
        self.assertEqual(student.student_profile.current_level_id, level.pk)
        delete_response = self.client.post(f'/dashboard/admin/students/{student.pk}/delete/')
        self.assertRedirects(delete_response, '/dashboard/admin/students/')
        self.assertFalse(User.objects.filter(pk=student.pk).exists())

    def test_admin_parent_crud(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        self.assertEqual(self.client.get('/dashboard/admin/parents/').status_code, 200)
        create_response = self.client.post('/dashboard/admin/parents/new/', {
            'first_name': 'Nora', 'last_name': 'Parent', 'email': 'nora@braingym.local',
            'role': 'PARENT', 'password1': 'SecureMVP!123', 'password2': 'SecureMVP!123',
        })
        parent = User.objects.get(email='nora@braingym.local')
        self.assertRedirects(create_response, f'/dashboard/admin/parents/{parent.pk}/')
        self.assertEqual(self.client.get(f'/dashboard/admin/parents/{parent.pk}/').status_code, 200)
        edit_response = self.client.post(f'/dashboard/admin/parents/{parent.pk}/edit/', {
            'first_name': 'Nora', 'last_name': 'Guardian', 'email': 'nora@braingym.local', 'is_active': 'on',
        })
        self.assertRedirects(edit_response, f'/dashboard/admin/parents/{parent.pk}/')
        parent.refresh_from_db()
        self.assertEqual(parent.last_name, 'Guardian')
        delete_response = self.client.post(f'/dashboard/admin/parents/{parent.pk}/delete/')
        self.assertRedirects(delete_response, '/dashboard/admin/parents/')
        self.assertFalse(User.objects.filter(pk=parent.pk).exists())

    def test_parent_can_be_linked_to_multiple_students_and_unlinked(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        parent = User.objects.get(email='parent@braingym.local')
        second_student = User.objects.create_user(email='second.student@braingym.local', password='SecureMVP!123', role=User.Role.STUDENT, first_name='Second', last_name='Student')
        response = self.client.post(f'/dashboard/admin/parents/{parent.pk}/link-student/', {
            'student': second_student.student_profile.pk, 'relationship': 'Guardian',
        })
        self.assertRedirects(response, f'/dashboard/admin/parents/{parent.pk}/')
        self.assertEqual(parent.parent_profile.children.count(), 2)
        duplicate = self.client.post(f'/dashboard/admin/parents/{parent.pk}/link-student/', {
            'student': second_student.student_profile.pk, 'relationship': 'Guardian',
        })
        self.assertEqual(duplicate.status_code, 200)
        self.assertContains(duplicate, 'already linked')
        link = parent.parent_profile.children.get(student=second_student.student_profile)
        unlink = self.client.post(f'/dashboard/admin/parents/{parent.pk}/unlink-student/{link.pk}/')
        self.assertRedirects(unlink, f'/dashboard/admin/parents/{parent.pk}/')
        self.assertEqual(parent.parent_profile.children.count(), 1)

    def test_non_admin_cannot_link_students_to_parents(self):
        parent = User.objects.get(email='parent@braingym.local')
        student = User.objects.get(email='student@braingym.local')
        self.client.login(email='teacher@braingym.local', password=DEMO_PASSWORD)
        response = self.client.post(f'/dashboard/admin/parents/{parent.pk}/link-student/', {'student': student.student_profile.pk})
        self.assertEqual(response.status_code, 403)

# Create your tests here.
