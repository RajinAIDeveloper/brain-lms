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

## Validation command

```powershell
& 'C:\Users\user\AppData\Local\Programs\Python\Python310\python.exe' manage.py check
& 'C:\Users\user\AppData\Local\Programs\Python\Python310\python.exe' manage.py test
```

## Next implementation slice

Build Phase 3 from the MVP plan: question banks, questions, exercises, tests, and teacher-created assignments. Preserve the existing role boundaries and extend tests before adding new dashboard behaviour.
