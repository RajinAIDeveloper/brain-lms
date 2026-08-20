from django.test import TestCase
from django.urls import reverse

from .management.commands.seed_demo import DEMO_PASSWORD
from .models import ClassBatch, Enrollment, Level, ParentStudentLink, User


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

# Create your tests here.
