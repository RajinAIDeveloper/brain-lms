# Brain Gym MVP Implementation Plan

## Purpose

Build and validate the core learning and progress-tracking loop for a mental-math/abacus academy. The MVP is successful only when a teacher can assign learning work, a student can complete it, the system can score it automatically, and the result is visible to both the teacher and the student's parent.

This document is the implementation source of truth for agents working on the project. Implement in the order below. Do not expand the product into branch management, billing, notifications, complex reporting, or additional staff roles until the core loop works.

## Product decisions locked for MVP

- Use four roles only: **Admin**, **Teacher**, **Student**, and **Parent**.
- Admin combines super-admin, branch-admin, content-manager, and academic-coordinator duties.
- Start with fixed, admin-authored question-bank content; do not build procedural question generation first.
- A student has one active class/batch at a time. Keep the schema extensible if future multiple enrolments are needed.
- Support auto-gradable numeric and multiple-choice questions only.
- Practice gives immediate correctness feedback. Tests reveal results only after submission.
- Assignments may have an optional due date. Do not implement scheduling rules, notifications, payments, branches, or live classes in MVP.
- Parent access is read-only and limited to linked children.

## Technology and design constraints

- Django with server-rendered Django templates.
- PostgreSQL in production and SQLite only for local development.
- Tailwind CSS for all interface styling and reusable UI patterns.
- GSAP only for intentional, short interactions: page/card entrance, progress fill, answer feedback, and completion celebration.
- Use Django's authentication system, custom user model, groups/roles, model validation, and permission checks in views/querysets.
- Use the Django admin as the fast internal back office. Build polished custom dashboards for all four user roles.
- Optimise teacher/admin for desktop data work and student/parent screens for mobile as well as desktop.

## Roles and access boundaries

| Role | Permitted responsibilities | Must not access |
| --- | --- | --- |
| Admin | Users, parent links, classes, curriculum, levels, content, assignments, all reports | None within the application scope |
| Teacher | Assigned classes and enrolled students; attendance; assignments; results; feedback | Other teachers' classes/students and global content administration |
| Student | Own assignments, attempts, scores, progress, achievements | Any other student's or class data |
| Parent | Read-only attendance, results, practice history, progress, and feedback for linked children | Unlinked children, editing academic data, and staff reports |

Permissions are a backend concern, not just a navigation concern. Every view and queryset must enforce the role and scope above.

## Core relationship model

```text
Admin
 ├─ creates → Teacher
 ├─ creates → Student ── linked to → Parent
 ├─ creates → ClassBatch ── has → Teacher + Students
 └─ creates → Curriculum → Level → Lesson → Practice/Test

Teacher → assigns Practice/Test → Student
Student → completes work → system grades automatically
System → saves score, accuracy, duration, and average answer time
Teacher and Parent → view the resulting progress
```

## Data model

Use Django model names equivalent to the following. Add normal audit fields (`created_at`, `updated_at`) where useful.

| Domain | Models | Important relationships / fields |
| --- | --- | --- |
| Identity | `User`, `Profile` | Custom user from the first migration; one role per MVP user |
| People | `TeacherProfile`, `StudentProfile`, `ParentProfile`, `ParentStudentLink` | Parent can be linked to one or more students |
| Academics | `Curriculum`, `Level`, `Lesson`, `ClassBatch`, `ClassSchedule`, `ClassHoliday`, `Enrollment`, `LevelPromotion`, `Attendance` | A batch has one teacher, date range, weekly schedule, and holiday exceptions; enrollment history identifies class status and attendance |
| Content | `QuestionBank`, `Question`, `Exercise`, `ExerciseQuestion`, `Test`, `TestQuestion` | Questions have topic, difficulty, type, correct answer, explanation, time target |
| Assignment | `Assignment` | Type, target class or students, due date, status, created by teacher/admin |
| Learning | `PracticeSession`, `TestAttempt`, `Answer` | Persist question order, submitted answer, correctness, response duration, aggregate results |
| Operations | `Attendance`, `TeacherFeedback`, `Achievement` | Attendance per student/class/date; feedback belongs to a student and author |

### Required metrics

- **Score:** correct answers / total questions, expressed as raw score and percentage.
- **Accuracy:** `correct_answers / answered_questions * 100`.
- **Average answer time:** total response duration / answered questions.
- **Practice count:** completed practice sessions.
- **Attendance percentage:** present (optionally count late) / recorded sessions * 100.
- **Streak:** consecutive qualifying practice days, based on the student's configured/local date policy.

Store raw attempt and answer timing data. Calculate dashboard aggregates from persisted data, not from browser-only state.

## Screen inventory

### Shared

- Login, logout, password reset, role-aware post-login redirect.
- Role-aware navigation, empty states, error/permission pages, and responsive base layout.

### Admin

- Dashboard: students, teachers, active classes, tests today, average accuracy, completed practice.
- User management: create teachers/students/parents and link parent to student.
- Academic management: curricula, levels, lessons, batches, teacher assignment, student enrolment.
- Content management: question banks, questions, exercises, and tests.
- Reporting: student, class, attendance, test-result, and teacher/class activity views.

### Teacher

- Assigned class list and class details.
- Student table with accuracy, average time, and completed-practice count.
- Attendance-taking page.
- Practice/test assignment flow for a class or selected students.
- Student detail with attempt history, answers, performance trends, and teacher feedback entry.

### Student

- Dashboard: current level, today's practice, pending work, accuracy, best streak, recent activity.
- Timed practice flow: one question at a time, answer submission, immediate correctness feedback, progress indicator.
- Test flow: one question at a time, no correctness feedback until final submit.
- Results screen: score, accuracy, duration, average answer speed, answer review where permitted, and next action.
- Progress history and achievements.

### Parent

- Child selector when linked to multiple students.
- Read-only child overview: current level, attendance, practice sessions, accuracy, average speed, latest test score.
- Progress graph, practice/test history, and teacher comments.

## UI and motion guidance

- Visual tone: calm, premium, encouraging, and academically clear. Avoid a generic administrative look.
- Establish Tailwind tokens for surface, text, accent, success, warning, danger, radius, shadows, and spacing before building screens.
- Use large readable metrics, clean tables, obvious status chips, and accessible form controls.
- Support keyboard navigation, visible focus, semantic labels, and sufficient colour contrast.
- GSAP must never delay task completion or hide essential state. Respect `prefers-reduced-motion`.
- Use motion sparingly: staggered dashboard cards, a one-time metric count-up, progress-bar fill, correct/incorrect answer feedback, and a brief completion celebration.

## Build order

### Phase 1 — Foundation

1. Initialise Django project and apps.
2. Configure custom user model before first migration.
3. Configure authentication, roles, role-aware redirects, base templates, Tailwind build, and reusable UI primitives.
4. Add permission helpers/mixins and tests proving each role is isolated.

**Done when:** each sample role can log in and only reach its own blank dashboard.

### Phase 2 — Academic setup

1. Implement profiles and parent-student links.
2. Implement curriculum, levels, lessons, classes/batches, teacher assignment, and student enrolment.
3. Configure practical Django admin workflows for all setup entities.

**Done when:** an admin can create a teacher, a student, a parent, a class, and a level; link and enrol everyone correctly.

### Phase 3 — Content and assignments

1. Implement question banks and numeric/multiple-choice questions.
2. Implement exercises and tests, including ordered question membership.
3. Implement assignments to a class or selected students with optional due date.
4. Make assignments visible only to their intended students and assigned teachers.

**Done when:** a teacher can assign existing practice or a test to a target class/student.

### Phase 4 — Learning and auto-grading

1. Build the student practice flow with answer-level timing and immediate feedback.
2. Build the test flow with deferred feedback.
3. Persist attempts, answers, score, accuracy, duration, and average answer time.
4. Guard against duplicate final submissions and access to unassigned content.

**Done when:** a student can complete an assignment and receive accurate results that persist after reload.

### Phase 5 — Teacher operations

1. Build class/student performance views with metrics and filters.
2. Implement attendance recording.
3. Add answer/attempt review and feedback comments.
4. Surface basic at-risk indicators: low accuracy, incomplete work, or low attendance.

**Done when:** a teacher can monitor only their students, record attendance, review attempts, and leave feedback.

### Phase 6 — Parent visibility

1. Build parent child selector and read-only child dashboard.
2. Add attendance, practice/test history, progress chart, and teacher comments.
3. Validate that a parent cannot view any unlinked student.

**Done when:** results of a completed student assignment appear clearly to the linked parent.

### Phase 7 — Admin reporting and polish

1. Build aggregate dashboard metrics and reports.
2. Add date/class/level filters and CSV export only if the core reports are stable.
3. Complete responsive layouts, empty states, reduced-motion support, and visual animation polish.

**Done when:** an admin can see academy-wide operational and learning trends without inspecting raw records.

## Acceptance test: one complete operational journey

The MVP is ready for validation only after this exact sequence works end to end:

1. Admin creates a teacher, student, and parent account.
2. Admin links the parent to the student.
3. Admin creates a level and class, assigns the teacher, and enrols the student.
4. Admin creates questions and a practice exercise or test.
5. Teacher assigns the work to the student and records attendance.
6. Student completes the timed work.
7. The system saves and calculates score, accuracy, total duration, and average answer time.
8. Teacher sees the result and can add feedback.
9. Parent sees attendance, the completed work, result metrics, and feedback.
10. Role-access tests confirm no user can access out-of-scope records.

## Explicit non-goals for MVP

- Multiple branches with branch-specific administration
- Billing, subscriptions, payments, and invoices
- Push/email/SMS notifications
- Live video classes or messaging
- Manual grading, essay answers, or arbitrary file submission
- Complex adaptive learning or AI-generated questions
- Advanced data warehouse reporting
- Native mobile applications

## Engineering guardrails

- Keep models and business logic in focused Django apps rather than putting all work in views.
- Add migrations and tests with each domain change.
- Use fixtures or factories to create a reliable demo set: one admin, teacher, parent, student, class, and assignment.
- Never rely on frontend filtering for access control.
- Do not add new roles or modules without updating this document and obtaining an explicit product decision.
- Prefer small vertical slices that complete a user outcome over building all database tables without usable screens.
