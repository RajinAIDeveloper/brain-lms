# Implementation status

## Completed: Foundation + authentication/onboarding

- Django project scaffolded in `config/` with an `accounts` app.
- Custom email-first `User` model with exactly four MVP roles.
- Built-in login, logout, password reset request, reset confirmation, and completion screens.
- Role-aware post-login redirect and protected role dashboards.
- Role profile models for teachers, students, and parents.
- Parent-to-one-or-more-students links.
- Curriculum level, class/batch, teacher assignment, and student enrollment models.
- Django admin registration for onboarding entities.
- Repeatable `seed_demo` management command.
- Automated tests for demo login redirects, dashboard rendering, relationships, permissions, and admin user creation.
- Dedicated Admin account-creation screen for Teacher, Student, and Parent users with duplicate-email and password validation.
- Admin workspace sidebar now includes Create users and Teachers; teacher management has list/search, create, detail, edit, and safe delete flows.
- Student and Parent management now include list/search, create, detail, edit, and delete flows; student details expose level/enrollment context and parent details expose linked children.
- Admins can link any active student to a parent from the parent detail page, link multiple students per parent, prevent duplicates, and unlink relationships without deleting accounts.
- Academic management now has sidebar links and full CRUD for levels and classes/batches. Levels can contain many batches; batches assign one teacher and support student enrollment, single-active-class movement, and unenrollment.
- Applied migration `accounts.0002_alter_enrollment_options` to keep active enrollments first when displaying a student's class context.
- Classes now support required date-range entry, recurring weekday/time schedules, schedule overlap validation, and date-bounded holidays with add/edit/remove controls. Migration `accounts.0003_classbatch_end_date_classbatch_start_date_and_more` is applied.
- Students now have level-promotion history and Admin promotion controls. Enrollment history tracks ongoing/completed/left status and ended dates. Attendance records support present, absent, late, and excused states with per-class percentages.
- Each class has a monthly roster calendar with scheduled-day highlighting, holiday colors, selected-day schedule times, and attendance entry for active students. Migration `accounts.0004_enrollment_ended_on_enrollment_status_levelpromotion_and_more` is applied.
- Admin can promote students between levels with a promotion history and note. Student and Admin views show enrollment history, ongoing/completed/left class status, attendance counts, and per-class attendance percentages. Demo Batch A includes Tuesday and Thursday weekly schedule examples.
- Curriculum studio now supports an unlimited self-referential tree under each level: Subject → Topic → Section → Subsection (and any further depth). Admins can create, edit, and delete nodes, attach assignments, and manage question banks with numeric or multiple-choice questions. Migration `accounts.0005_curriculumnode_assignment_questionbank_question` is applied.

- Admins can now create and manage published or draft tests on any curriculum node, add ordered questions from that level's question banks, set duration and passing score, and remove questions. Test attempts are persisted for reporting. Migration `accounts.0006_test_testattempt_testquestion` is applied.
- Added an Admin Reports workspace with level filtering, all-student performance rows (attendance, active class, test count, average score), class reports, and recent test activity. The existing Classes workspace remains the full class/batch management view.
- Added dated class lesson plans with curriculum coverage, learning objective, acceptance criteria, summary, and completion state. Admins can link attendance-eligible assignments/tests to a class, see missed subject/topic/section/subsection coverage, and create makeup groups from students with recorded absences. Migrations `accounts.0007_classactivity_makeupgroup_makeupgroupstudent_and_more` and `accounts.0008_classactivity_unique_batch_assignment_activity_and_more` are applied.

## Validation command

```powershell
& 'C:\Users\user\AppData\Local\Programs\Python\Python310\python.exe' manage.py check
& 'C:\Users\user\AppData\Local\Programs\Python\Python310\python.exe' manage.py test
```

## Next implementation slice

Build the remaining Phase 3 learning objects from the MVP plan: teacher-created assignment targeting and then the student test/practice completion flow that writes `TestAttempt` metrics. Preserve the existing role boundaries and extend tests before adding new dashboard behaviour.
