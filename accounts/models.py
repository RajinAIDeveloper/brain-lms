from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models


class UserManager(BaseUserManager):
    """Create users using email as the login identifier."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('An email address is required.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        TEACHER = 'TEACHER', 'Teacher'
        STUDENT = 'STUDENT', 'Student'
        PARENT = 'PARENT', 'Parent'

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.get_full_name() or self.email

    def save(self, *args, **kwargs):
        if self.role == self.Role.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)


class Level(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.code} · {self.name}'


class CurriculumNode(models.Model):
    """A level-scoped curriculum tree with unlimited nesting."""

    class NodeType(models.TextChoices):
        SUBJECT = 'SUBJECT', 'Subject'
        TOPIC = 'TOPIC', 'Topic'
        SECTION = 'SECTION', 'Section'
        SUBSECTION = 'SUBSECTION', 'Subsection'

    level = models.ForeignKey(Level, on_delete=models.PROTECT, related_name='curriculum_nodes')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    title = models.CharField(max_length=160)
    node_type = models.CharField(max_length=20, choices=NodeType.choices)
    description = models.TextField(blank=True)
    ordering = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordering', 'title']

    def clean(self):
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError({'parent': 'A curriculum node cannot be its own parent.'})
        if self.parent_id and self.level_id and self.parent.level_id != self.level_id:
            raise ValidationError({'parent': 'Parent nodes must belong to the same level.'})
        if not self.parent_id and self.node_type != self.NodeType.SUBJECT:
            raise ValidationError({'node_type': 'Top-level curriculum nodes must be subjects.'})
        if self.parent_id and self.node_type == self.NodeType.SUBJECT:
            raise ValidationError({'node_type': 'Only top-level nodes can be subjects.'})
        ancestor = self.parent
        seen = set()
        while ancestor:
            if ancestor.pk in seen or ancestor.pk == self.pk:
                raise ValidationError({'parent': 'This parent would create a curriculum cycle.'})
            seen.add(ancestor.pk)
            ancestor = ancestor.parent

    def __str__(self):
        return f'{self.level.code} · {self.title}'

    @property
    def breadcrumb(self):
        parts = []
        node = self
        while node:
            parts.append(node.title)
            node = node.parent
        return ' → '.join(reversed(parts))


class QuestionBank(models.Model):
    node = models.ForeignKey(CurriculumNode, on_delete=models.CASCADE, related_name='question_banks')
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_question_banks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Question(models.Model):
    class QuestionType(models.TextChoices):
        NUMERIC = 'NUMERIC', 'Numeric'
        MULTIPLE_CHOICE = 'MULTIPLE_CHOICE', 'Multiple choice'

    bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='questions')
    prompt = models.TextField()
    question_type = models.CharField(max_length=20, choices=QuestionType.choices, default=QuestionType.NUMERIC)
    correct_answer = models.CharField(max_length=240)
    options = models.JSONField(default=list, blank=True)
    explanation = models.TextField(blank=True)
    difficulty = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['difficulty', 'pk']

    def __str__(self):
        return self.prompt[:80]


class Assignment(models.Model):
    node = models.ForeignKey(CurriculumNode, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=160)
    instructions = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_assignments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', 'title']

    def __str__(self):
        return self.title


class Test(models.Model):
    node = models.ForeignKey(CurriculumNode, on_delete=models.CASCADE, related_name='tests')
    title = models.CharField(max_length=160)
    instructions = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=15)
    passing_score = models.PositiveSmallIntegerField(default=70)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_tests')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', 'title']

    def clean(self):
        if self.passing_score > 100:
            raise ValidationError({'passing_score': 'Passing score must be between 0 and 100.'})
        if self.duration_minutes < 1:
            raise ValidationError({'duration_minutes': 'Test duration must be at least one minute.'})

    @property
    def question_count(self):
        return self.test_questions.count()

    def __str__(self):
        return self.title


class TestQuestion(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='test_questions')
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name='test_memberships')
    ordering = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['ordering', 'pk']
        constraints = [
            models.UniqueConstraint(fields=['test', 'question'], name='unique_question_per_test'),
            models.UniqueConstraint(fields=['test', 'ordering'], name='unique_test_question_order'),
        ]

    def __str__(self):
        return f'{self.test} · {self.question}'


class TestAttempt(models.Model):
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE, related_name='test_attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField(default=0)
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    average_answer_time = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.student} · {self.test} · {self.score}'


class ClassBatch(models.Model):
    name = models.CharField(max_length=120)
    level = models.ForeignKey(Level, on_delete=models.PROTECT, related_name='classes')
    teacher = models.ForeignKey(User, on_delete=models.PROTECT, related_name='teaching_classes', limit_choices_to={'role': User.Role.TEACHER})
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['level__code', 'name']

    def clean(self):
        if self.teacher_id and self.teacher.role != User.Role.TEACHER:
            raise ValidationError({'teacher': 'Only teacher users can be assigned to a class.'})
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'End date must be on or after the start date.'})

    def __str__(self):
        return f'{self.level.code} · {self.name}'


class ClassSchedule(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, 'Monday'
        TUESDAY = 1, 'Tuesday'
        WEDNESDAY = 2, 'Wednesday'
        THURSDAY = 3, 'Thursday'
        FRIDAY = 4, 'Friday'
        SATURDAY = 5, 'Saturday'
        SUNDAY = 6, 'Sunday'

    class_batch = models.ForeignKey(ClassBatch, on_delete=models.CASCADE, related_name='schedules')
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['weekday', 'start_time']
        constraints = [models.UniqueConstraint(fields=['class_batch', 'weekday', 'start_time'], name='unique_batch_schedule_start')]

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({'end_time': 'End time must be after start time.'})
        overlaps = ClassSchedule.objects.filter(class_batch=self.class_batch, weekday=self.weekday, start_time__lt=self.end_time, end_time__gt=self.start_time).exclude(pk=self.pk) if self.class_batch_id and self.weekday is not None and self.start_time and self.end_time else ClassSchedule.objects.none()
        if overlaps.exists():
            raise ValidationError('This weekly schedule overlaps another schedule on the same day.')

    def __str__(self):
        return f'{self.get_weekday_display()} {self.start_time:%H:%M}–{self.end_time:%H:%M}'


class ClassHoliday(models.Model):
    class_batch = models.ForeignKey(ClassBatch, on_delete=models.CASCADE, related_name='holidays')
    date = models.DateField()
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['date']
        constraints = [models.UniqueConstraint(fields=['class_batch', 'date'], name='unique_batch_holiday_date')]

    def clean(self):
        if self.date and self.class_batch.start_date and self.date < self.class_batch.start_date:
            raise ValidationError({'date': 'Holiday must fall within the class start and end dates.'})
        if self.date and self.class_batch.end_date and self.date > self.class_batch.end_date:
            raise ValidationError({'date': 'Holiday must fall within the class start and end dates.'})

    def __str__(self):
        return f'{self.class_batch} · {self.date}'


class ClassSession(models.Model):
    """One dated meeting in a recurring class schedule."""

    class_batch = models.ForeignKey(ClassBatch, on_delete=models.CASCADE, related_name='sessions')
    schedule = models.ForeignKey(ClassSchedule, on_delete=models.PROTECT, related_name='sessions')
    date = models.DateField()
    curriculum_node = models.ForeignKey(CurriculumNode, on_delete=models.PROTECT, related_name='class_sessions', null=True, blank=True)
    learning_objective = models.TextField(blank=True)
    acceptance_criteria = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date', 'schedule__start_time']
        constraints = [models.UniqueConstraint(fields=['class_batch', 'schedule', 'date'], name='unique_class_session_date')]

    def clean(self):
        if self.schedule_id and self.schedule.class_batch_id != self.class_batch_id:
            raise ValidationError({'schedule': 'The schedule must belong to this class.'})
        if self.date and self.class_batch.start_date and self.date < self.class_batch.start_date:
            raise ValidationError({'date': 'Session must be within the class date range.'})
        if self.date and self.class_batch.end_date and self.date > self.class_batch.end_date:
            raise ValidationError({'date': 'Session must be within the class date range.'})
        if self.date and self.schedule_id and self.date.weekday() != self.schedule.weekday:
            raise ValidationError({'date': 'Session date must match the selected weekly schedule day.'})
        if self.curriculum_node_id and self.curriculum_node.level_id != self.class_batch.level_id:
            raise ValidationError({'curriculum_node': 'Lesson coverage must belong to the class level.'})

    def __str__(self):
        return f'{self.class_batch} · {self.date}'


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    display_title = models.CharField(max_length=120, default='Math Coach')

    def __str__(self):
        return str(self.user)


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    current_level = models.ForeignKey(Level, on_delete=models.PROTECT, related_name='students', null=True, blank=True)
    best_streak = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.user)


class LevelPromotion(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='promotions')
    from_level = models.ForeignKey(Level, on_delete=models.PROTECT, related_name='promotions_from', null=True, blank=True)
    to_level = models.ForeignKey(Level, on_delete=models.PROTECT, related_name='promotions_to')
    promoted_on = models.DateField(auto_now_add=True)
    promoted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='level_promotions')
    note = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ['-promoted_on', '-pk']

    def __str__(self):
        return f'{self.student} promoted to {self.to_level.code}'


class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')

    def __str__(self):
        return str(self.user)


class ParentStudentLink(models.Model):
    parent = models.ForeignKey(ParentProfile, on_delete=models.CASCADE, related_name='children')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='parents')
    relationship = models.CharField(max_length=40, default='Parent')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['parent', 'student'], name='unique_parent_student_link')]

    def __str__(self):
        return f'{self.parent} → {self.student}'


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ONGOING = 'ONGOING', 'Ongoing'
        COMPLETED = 'COMPLETED', 'Completed'
        LEFT = 'LEFT', 'Left'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    class_batch = models.ForeignKey(ClassBatch, on_delete=models.CASCADE, related_name='enrollments')
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ONGOING)
    enrolled_on = models.DateField(auto_now_add=True)
    ended_on = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['student', 'class_batch'], name='unique_student_class')]
        ordering = ['-is_active', '-enrolled_on']

    def __str__(self):
        return f'{self.student} in {self.class_batch}'


class ClassActivity(models.Model):
    """A class-targeted assignment or test with attendance eligibility."""

    class_batch = models.ForeignKey(ClassBatch, on_delete=models.CASCADE, related_name='activities')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='class_activities', null=True, blank=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='class_activities', null=True, blank=True)
    required_attendance_percent = models.PositiveSmallIntegerField(default=75)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_class_activities')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['class_batch', 'assignment'], condition=models.Q(assignment__isnull=False), name='unique_batch_assignment_activity'),
            models.UniqueConstraint(fields=['class_batch', 'test'], condition=models.Q(test__isnull=False), name='unique_batch_test_activity'),
        ]

    def clean(self):
        if bool(self.assignment_id) == bool(self.test_id):
            raise ValidationError('Choose exactly one assignment or test.')
        if self.required_attendance_percent > 100:
            raise ValidationError({'required_attendance_percent': 'Attendance requirement must be between 0 and 100.'})
        target = self.assignment or self.test
        if target and target.node.level_id != self.class_batch.level_id:
            raise ValidationError('The activity must belong to the class level.')

    @property
    def title(self):
        return (self.assignment or self.test).title

    def __str__(self):
        return f'{self.class_batch} · {self.title}'


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LATE = 'LATE', 'Late'
        EXCUSED = 'EXCUSED', 'Excused'

    class_batch = models.ForeignKey(ClassBatch, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices)
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='recorded_attendance')
    recorded_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'student__user__last_name']
        constraints = [models.UniqueConstraint(fields=['class_batch', 'student', 'date'], name='unique_attendance_per_class_student_date')]

    def clean(self):
        if not Enrollment.objects.filter(student=self.student, class_batch=self.class_batch).exists():
            raise ValidationError({'student': 'The student must be enrolled in this class before attendance can be recorded.'})

    def __str__(self):
        return f'{self.student} · {self.date} · {self.get_status_display()}'


class MakeupGroup(models.Model):
    source_batch = models.ForeignKey(ClassBatch, on_delete=models.PROTECT, related_name='makeup_groups')
    name = models.CharField(max_length=120)
    teacher = models.ForeignKey(User, on_delete=models.PROTECT, related_name='makeup_groups')
    scheduled_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_makeup_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    students = models.ManyToManyField(StudentProfile, through='MakeupGroupStudent', related_name='makeup_groups')

    class Meta:
        ordering = ['-created_at', 'name']

    def clean(self):
        if self.teacher_id and self.teacher.role != User.Role.TEACHER:
            raise ValidationError({'teacher': 'Only teacher users can lead a makeup group.'})
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({'end_time': 'End time must be after start time.'})

    def __str__(self):
        return self.name


class MakeupGroupStudent(models.Model):
    group = models.ForeignKey(MakeupGroup, on_delete=models.CASCADE, related_name='memberships')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='makeup_memberships')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['group', 'student'], name='unique_makeup_group_student')]

# Create your models here.
