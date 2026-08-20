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
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    class_batch = models.ForeignKey(ClassBatch, on_delete=models.CASCADE, related_name='enrollments')
    is_active = models.BooleanField(default=True)
    enrolled_on = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['student', 'class_batch'], name='unique_student_class')]
        ordering = ['-is_active', '-enrolled_on']

    def __str__(self):
        return f'{self.student} in {self.class_batch}'

# Create your models here.
