from django.test import TestCase
from django.urls import reverse

from .management.commands.seed_demo import DEMO_PASSWORD
from .models import Assignment, Attendance, ClassActivity, ClassBatch, ClassHoliday, ClassSchedule, ClassSession, CurriculumNode, Enrollment, Level, MakeupGroup, ParentProfile, ParentStudentLink, Question, QuestionBank, StudentProfile, TeacherProfile, Test, TestQuestion, User


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

    def test_admin_level_crud_and_protected_delete(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        self.assertEqual(self.client.get('/dashboard/admin/levels/').status_code, 200)
        create_response = self.client.post('/dashboard/admin/levels/new/', {'name': 'Level 3', 'code': 'l3', 'description': 'Advanced speed work'})
        level = Level.objects.get(code='L3')
        self.assertRedirects(create_response, f'/dashboard/admin/levels/{level.pk}/')
        self.assertEqual(self.client.get(f'/dashboard/admin/levels/{level.pk}/').status_code, 200)
        edit_response = self.client.post(f'/dashboard/admin/levels/{level.pk}/edit/', {'name': 'Level Three', 'code': 'l3', 'description': 'Advanced speed work'})
        self.assertRedirects(edit_response, f'/dashboard/admin/levels/{level.pk}/')
        level.refresh_from_db()
        self.assertEqual(level.name, 'Level Three')
        delete_response = self.client.post(f'/dashboard/admin/levels/{level.pk}/delete/')
        self.assertRedirects(delete_response, '/dashboard/admin/levels/')
        self.assertFalse(Level.objects.filter(pk=level.pk).exists())
        seeded_level = Level.objects.get(code='L2')
        protected = self.client.post(f'/dashboard/admin/levels/{seeded_level.pk}/delete/')
        self.assertRedirects(protected, f'/dashboard/admin/levels/{seeded_level.pk}/')
        self.assertTrue(Level.objects.filter(pk=seeded_level.pk).exists())

    def test_admin_batch_crud_and_student_enrollment(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        level = Level.objects.get(code='L2')
        teacher = User.objects.get(email='teacher@braingym.local')
        second_student = User.objects.create_user(email='batch.student@braingym.local', password='SecureMVP!123', role=User.Role.STUDENT, first_name='Batch', last_name='Student')
        self.assertEqual(self.client.get('/dashboard/admin/classes/').status_code, 200)
        create_response = self.client.post('/dashboard/admin/classes/new/', {'name': 'Batch B', 'level': level.pk, 'teacher': teacher.pk, 'start_date': '2026-01-01', 'end_date': '2026-12-31', 'is_active': 'on'})
        batch = ClassBatch.objects.get(name='Batch B')
        self.assertRedirects(create_response, f'/dashboard/admin/classes/{batch.pk}/')
        self.assertEqual(self.client.get(f'/dashboard/admin/classes/{batch.pk}/').status_code, 200)
        enroll_response = self.client.post(f'/dashboard/admin/classes/{batch.pk}/enroll/', {'student': second_student.student_profile.pk})
        self.assertRedirects(enroll_response, f'/dashboard/admin/classes/{batch.pk}/')
        enrollment = Enrollment.objects.get(student=second_student.student_profile, class_batch=batch)
        self.assertTrue(enrollment.is_active)
        second_student.student_profile.refresh_from_db()
        self.assertEqual(second_student.student_profile.current_level_id, level.pk)
        edit_response = self.client.post(f'/dashboard/admin/classes/{batch.pk}/edit/', {'name': 'Batch B Updated', 'level': level.pk, 'teacher': teacher.pk, 'start_date': '2026-01-01', 'end_date': '2026-12-31', 'is_active': 'on'})
        self.assertRedirects(edit_response, f'/dashboard/admin/classes/{batch.pk}/')
        batch.refresh_from_db()
        self.assertEqual(batch.name, 'Batch B Updated')
        unenroll_response = self.client.post(f'/dashboard/admin/classes/{batch.pk}/unenroll/{enrollment.pk}/')
        self.assertRedirects(unenroll_response, f'/dashboard/admin/classes/{batch.pk}/')
        enrollment.refresh_from_db()
        self.assertFalse(enrollment.is_active)
        delete_response = self.client.post(f'/dashboard/admin/classes/{batch.pk}/delete/')
        self.assertRedirects(delete_response, '/dashboard/admin/classes/')
        self.assertFalse(ClassBatch.objects.filter(pk=batch.pk).exists())

    def test_class_weekly_schedule_and_holidays(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        batch = ClassBatch.objects.get(name='Batch A')
        self.assertEqual(self.client.get(f'/dashboard/admin/classes/{batch.pk}/').status_code, 200)
        ClassSchedule.objects.get_or_create(class_batch=batch, weekday=1, start_time='17:30', defaults={'end_time': '18:40'})
        ClassSchedule.objects.get_or_create(class_batch=batch, weekday=3, start_time='19:30', defaults={'end_time': '20:50'})
        self.assertEqual(ClassSchedule.objects.filter(class_batch=batch).count(), 2)
        overlap = self.client.post(f'/dashboard/admin/classes/{batch.pk}/schedule/new/', {'weekday': 1, 'start_time': '18:00', 'end_time': '19:00'})
        self.assertEqual(overlap.status_code, 200)
        self.assertContains(overlap, 'overlaps')
        holiday = self.client.post(f'/dashboard/admin/classes/{batch.pk}/holiday/new/', {'date': '2026-02-03', 'note': 'School holiday'})
        self.assertRedirects(holiday, f'/dashboard/admin/classes/{batch.pk}/')
        holiday_record = ClassHoliday.objects.get(class_batch=batch, date='2026-02-03')
        outside_range = self.client.post(f'/dashboard/admin/classes/{batch.pk}/holiday/new/', {'date': '2027-02-03', 'note': 'Outside range'})
        self.assertEqual(outside_range.status_code, 200)
        self.assertContains(outside_range, 'within the class date range')
        schedule = ClassSchedule.objects.get(class_batch=batch, weekday=1)
        edit_schedule = self.client.post(f'/dashboard/admin/classes/{batch.pk}/schedule/{schedule.pk}/edit/', {'weekday': 1, 'start_time': '18:00', 'end_time': '19:10'})
        self.assertRedirects(edit_schedule, f'/dashboard/admin/classes/{batch.pk}/')
        remove_schedule = self.client.post(f'/dashboard/admin/classes/{batch.pk}/schedule/{schedule.pk}/delete/')
        self.assertRedirects(remove_schedule, f'/dashboard/admin/classes/{batch.pk}/')
        remove_holiday = self.client.post(f'/dashboard/admin/classes/{batch.pk}/holiday/{holiday_record.pk}/delete/')
        self.assertRedirects(remove_holiday, f'/dashboard/admin/classes/{batch.pk}/')
        self.assertFalse(ClassHoliday.objects.filter(pk=holiday_record.pk).exists())

    def test_admin_promotes_student_and_records_class_status(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        student = User.objects.get(email='student@braingym.local')
        next_level = Level.objects.create(name='Level 3', code='L3')
        promotion = self.client.post(f'/dashboard/admin/students/{student.pk}/promote/', {'to_level': next_level.pk, 'note': 'Passed assessment'})
        self.assertRedirects(promotion, f'/dashboard/admin/students/{student.pk}/')
        student.student_profile.refresh_from_db()
        self.assertEqual(student.student_profile.current_level_id, next_level.pk)
        self.assertEqual(student.student_profile.promotions.count(), 1)
        enrollment = student.student_profile.enrollments.first()
        status = self.client.post(f'/dashboard/admin/students/{student.pk}/enrollments/{enrollment.pk}/status/', {'status': Enrollment.Status.COMPLETED})
        self.assertRedirects(status, f'/dashboard/admin/students/{student.pk}/')
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, Enrollment.Status.COMPLETED)
        self.assertFalse(enrollment.is_active)

    def test_monthly_roster_records_attendance_for_scheduled_date(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        batch = ClassBatch.objects.get(name='Batch A')
        ClassSchedule.objects.get_or_create(class_batch=batch, weekday=1, start_time='17:30', defaults={'end_time': '18:40'})
        roster = self.client.get(f'/dashboard/admin/classes/{batch.pk}/roster/?month=2026-02&date=2026-02-03')
        self.assertEqual(roster.status_code, 200)
        self.assertContains(roster, 'Attendance')
        student = User.objects.get(email='student@braingym.local')
        saved = self.client.post(f'/dashboard/admin/classes/{batch.pk}/roster/attendance/', {'date': '2026-02-03', f'status_{student.student_profile.pk}': Attendance.Status.PRESENT})
        self.assertRedirects(saved, f'/dashboard/admin/classes/{batch.pk}/roster/?month=2026-02&date=2026-02-03')
        record = Attendance.objects.get(class_batch=batch, student=student.student_profile, date='2026-02-03')
        self.assertEqual(record.status, Attendance.Status.PRESENT)
        holiday = ClassHoliday.objects.create(class_batch=batch, date='2026-02-10', note='Holiday')
        holiday_roster = self.client.get(f'/dashboard/admin/classes/{batch.pk}/roster/?month=2026-02&date=2026-02-10')
        self.assertContains(holiday_roster, 'HOLIDAY')

    def test_admin_can_build_nested_curriculum_and_content(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        level = Level.objects.get(code='L2')
        self.assertEqual(self.client.get('/dashboard/admin/curriculum/').status_code, 200)
        subject_response = self.client.post('/dashboard/admin/curriculum/nodes/new/', {'level': level.pk, 'title': 'Mental Math', 'node_type': 'SUBJECT', 'description': '', 'ordering': 0, 'is_active': 'on'})
        subject = CurriculumNode.objects.get(title='Mental Math')
        self.assertRedirects(subject_response, f'/dashboard/admin/curriculum/nodes/{subject.pk}/')
        topic_response = self.client.post('/dashboard/admin/curriculum/nodes/new/', {'level': level.pk, 'parent': subject.pk, 'title': 'Addition', 'node_type': 'TOPIC', 'description': '', 'ordering': 0, 'is_active': 'on'})
        topic = CurriculumNode.objects.get(title='Addition')
        self.assertRedirects(topic_response, f'/dashboard/admin/curriculum/nodes/{topic.pk}/')
        parent = topic
        for index in range(3):
            self.client.post('/dashboard/admin/curriculum/nodes/new/', {'level': level.pk, 'parent': parent.pk, 'title': f'Section {index}', 'node_type': 'SECTION' if index == 0 else 'SUBSECTION', 'description': '', 'ordering': index, 'is_active': 'on'})
            parent = CurriculumNode.objects.get(title=f'Section {index}')
        bank_response = self.client.post(f'/dashboard/admin/curriculum/nodes/{parent.pk}/question-banks/new/', {'name': 'Warm up', 'description': '', 'is_active': 'on'})
        bank = QuestionBank.objects.get(name='Warm up')
        self.assertRedirects(bank_response, f'/dashboard/admin/question-banks/{bank.pk}/')
        question_response = self.client.post(f'/dashboard/admin/question-banks/{bank.pk}/questions/new/', {'prompt': '2 + 2?', 'question_type': 'NUMERIC', 'correct_answer': '4', 'options': '[]', 'explanation': '', 'difficulty': 1, 'is_active': 'on'})
        self.assertRedirects(question_response, f'/dashboard/admin/question-banks/{bank.pk}/')
        self.assertEqual(Question.objects.filter(bank=bank).count(), 1)
        assignment_response = self.client.post(f'/dashboard/admin/curriculum/nodes/{parent.pk}/assignments/new/', {'title': 'Practice 1', 'instructions': 'Solve these.', 'due_date': '', 'is_published': 'on'})
        self.assertRedirects(assignment_response, f'/dashboard/admin/curriculum/nodes/{parent.pk}/')
        self.assertTrue(Assignment.objects.filter(node=parent, title='Practice 1').exists())

    def test_non_admin_cannot_open_curriculum(self):
        self.client.login(email='teacher@braingym.local', password=DEMO_PASSWORD)
        self.assertEqual(self.client.get('/dashboard/admin/curriculum/').status_code, 403)

    def test_admin_can_create_test_from_level_questions(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        level = Level.objects.get(code='L2')
        node = CurriculumNode.objects.create(level=level, title='Speed Math', node_type=CurriculumNode.NodeType.SUBJECT)
        bank = QuestionBank.objects.create(node=node, name='Speed bank', created_by=User.objects.get(email='admin@braingym.local'))
        question = Question.objects.create(bank=bank, prompt='3 + 4?', correct_answer='7')
        response = self.client.post(f'/dashboard/admin/curriculum/nodes/{node.pk}/tests/new/', {'title': 'Speed assessment', 'instructions': 'Complete calmly.', 'duration_minutes': 10, 'passing_score': 70, 'is_published': 'on'})
        test = Test.objects.get(title='Speed assessment')
        self.assertRedirects(response, f'/dashboard/admin/tests/{test.pk}/')
        add_question = self.client.post(f'/dashboard/admin/tests/{test.pk}/questions/new/', {'question': question.pk, 'ordering': 1, 'points': 1})
        self.assertRedirects(add_question, f'/dashboard/admin/tests/{test.pk}/')
        self.assertTrue(TestQuestion.objects.filter(test=test, question=question).exists())
        self.assertContains(self.client.get(f'/dashboard/admin/tests/{test.pk}/'), 'Speed assessment')

    def test_admin_reports_show_students_classes_and_tests(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        self.assertEqual(self.client.get('/dashboard/admin/tests/').status_code, 200)
        response = self.client.get('/dashboard/admin/reports/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student performance')
        self.assertContains(response, 'Class reports')
        self.assertContains(response, 'student@braingym.local')
        self.client.logout()
        self.client.login(email='teacher@braingym.local', password=DEMO_PASSWORD)
        self.assertEqual(self.client.get('/dashboard/admin/reports/').status_code, 403)

    def test_admin_plans_daily_coverage_tracks_eligibility_and_makeup_group(self):
        self.client.login(email='admin@braingym.local', password=DEMO_PASSWORD)
        batch = ClassBatch.objects.get(name='Batch A')
        schedule = ClassSchedule.objects.filter(class_batch=batch, weekday=1).first()
        if not schedule:
            schedule = ClassSchedule.objects.create(class_batch=batch, weekday=1, start_time='17:30', end_time='18:40')
        node = CurriculumNode.objects.create(level=batch.level, title='Carry addition', node_type=CurriculumNode.NodeType.TOPIC, parent=CurriculumNode.objects.create(level=batch.level, title='Arithmetic', node_type=CurriculumNode.NodeType.SUBJECT))
        planned = self.client.post(f'/dashboard/admin/classes/{batch.pk}/sessions/new/', {'schedule': schedule.pk, 'date': '2026-02-03', 'curriculum_node': node.pk, 'learning_objective': 'Add with carry', 'acceptance_criteria': '8 of 10 correct', 'summary': 'Introduced regrouping', 'is_completed': 'on'})
        self.assertRedirects(planned, f'/dashboard/admin/classes/{batch.pk}/')
        session = ClassSession.objects.get(class_batch=batch, date='2026-02-03')
        self.assertEqual(session.curriculum_node_id, node.pk)
        student = User.objects.get(email='student@braingym.local')
        Attendance.objects.update_or_create(class_batch=batch, student=student.student_profile, date='2026-02-03', defaults={'status': Attendance.Status.ABSENT, 'recorded_by': User.objects.get(email='admin@braingym.local')})
        assignment = Assignment.objects.create(node=node, title='Carry homework', created_by=User.objects.get(email='admin@braingym.local'))
        linked = self.client.post(f'/dashboard/admin/classes/{batch.pk}/activities/new/', {'assignment': assignment.pk, 'test': '', 'required_attendance_percent': 80})
        self.assertRedirects(linked, f'/dashboard/admin/classes/{batch.pk}/')
        self.assertTrue(ClassActivity.objects.filter(class_batch=batch, assignment=assignment).exists())
        report = self.client.get('/dashboard/admin/reports/')
        self.assertContains(report, 'Missed curriculum coverage')
        self.assertContains(report, 'Carry addition')
        group_page = self.client.get(f'/dashboard/admin/makeup-groups/new/?batch={batch.pk}')
        self.assertEqual(group_page.status_code, 200)
        created = self.client.post(f'/dashboard/admin/makeup-groups/new/?batch={batch.pk}', {'source_batch': batch.pk, 'name': 'Carry recovery', 'teacher': batch.teacher.pk, 'scheduled_date': '2026-02-05', 'start_time': '17:30', 'end_time': '18:30', 'notes': 'Recover carry addition', 'students': [student.student_profile.pk], 'is_active': 'on'})
        group = MakeupGroup.objects.get(name='Carry recovery')
        self.assertRedirects(created, f'/dashboard/admin/makeup-groups/{group.pk}/')
        self.assertTrue(group.students.filter(pk=student.student_profile.pk).exists())

# Create your tests here.
