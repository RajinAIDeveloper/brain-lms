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
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['level__code', 'name']

    def clean(self):
        if self.teacher_id and self.teacher.role != User.Role.TEACHER:
            raise ValidationError({'teacher': 'Only teacher users can be assigned to a class.'})

    def __str__(self):
        return f'{self.level.code} · {self.name}'


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

    def __str__(self):
        return f'{self.student} in {self.class_batch}'

# Create your models here.
