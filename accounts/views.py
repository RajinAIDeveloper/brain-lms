from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from .models import ClassBatch, Enrollment, ParentStudentLink, User


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


@login_required
def dashboard_redirect(request):
    role_urls = {
        User.Role.ADMIN: 'accounts:admin_dashboard',
        User.Role.TEACHER: 'accounts:teacher_dashboard',
        User.Role.STUDENT: 'accounts:student_dashboard',
        User.Role.PARENT: 'accounts:parent_dashboard',
    }
    return redirect(role_urls.get(request.user.role, 'login'))


@role_required(User.Role.ADMIN)
def admin_dashboard(request):
    context = {'dashboard_role': 'Admin', 'eyebrow': 'Academy overview', 'summary': [
        ('Students', User.objects.filter(role=User.Role.STUDENT).count(), 'Across active learning levels'),
        ('Teachers', User.objects.filter(role=User.Role.TEACHER).count(), 'Ready to coach today'),
        ('Active classes', ClassBatch.objects.filter(is_active=True).count(), 'Teacher-led learning groups'),
        ('Enrollments', Enrollment.objects.filter(is_active=True).count(), 'Students in active classes'),
    ]}
    return render(request, 'dashboard/admin.html', context)


@role_required(User.Role.TEACHER)
def teacher_dashboard(request):
    classes = ClassBatch.objects.filter(teacher=request.user, is_active=True).select_related('level')
    context = {'dashboard_role': 'Teacher', 'eyebrow': 'Your coaching space', 'classes': classes, 'summary': [
        ('Assigned classes', classes.count(), 'Your active groups'),
        ('Students', Enrollment.objects.filter(class_batch__in=classes, is_active=True).count(), 'Students to support'),
    ]}
    return render(request, 'dashboard/teacher.html', context)


@role_required(User.Role.STUDENT)
def student_dashboard(request):
    profile = request.user.student_profile
    enrollment = profile.enrollments.filter(is_active=True).select_related('class_batch__level').first()
    context = {'dashboard_role': 'Student', 'eyebrow': 'Your learning journey', 'profile': profile, 'enrollment': enrollment, 'summary': [
        ('Current accuracy', '87%', 'Keep your rhythm going'), ('Best streak', profile.best_streak, 'Consecutive practice days'), ('Practice', '0', 'Sessions completed'),
    ]}
    return render(request, 'dashboard/student.html', context)


@role_required(User.Role.PARENT)
def parent_dashboard(request):
    children = ParentStudentLink.objects.filter(parent=request.user.parent_profile).select_related('student__user', 'student__current_level')
    context = {'dashboard_role': 'Parent', 'eyebrow': 'A clear view of progress', 'children': children, 'summary': [
        ('Children linked', children.count(), 'Profiles you can follow'), ('Attendance', '—', 'Will update with attendance'), ('Latest result', '—', 'No tests completed yet'),
    ]}
    return render(request, 'dashboard/parent.html', context)

# Create your views here.
