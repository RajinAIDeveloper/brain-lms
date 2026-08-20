from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect, render

from .models import ClassBatch, Enrollment, ParentStudentLink, User
from .forms import (
    AdminAccountCreationForm,
    ParentAccountCreationForm,
    ParentEditForm,
    StudentAccountCreationForm,
    StudentEditForm,
    TeacherAccountCreationForm,
    TeacherEditForm,
)


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
    context['recent_accounts'] = User.objects.exclude(pk=request.user.pk).order_by('-date_joined')[:6]
    return render(request, 'dashboard/admin.html', context)


@role_required(User.Role.ADMIN)
def admin_users(request):
    return render(request, 'dashboard/admin_users.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access'})


@role_required(User.Role.ADMIN)
def admin_create_account(request):
    form = AdminAccountCreationForm(request.POST or None, initial={'role': request.GET.get('role', User.Role.STUDENT)})
    if request.method == 'POST' and form.is_valid():
        account = form.save()
        messages.success(request, f'{account.get_role_display()} account created for {account.get_full_name() or account.email}.')
        return redirect('accounts:admin_dashboard')
    return render(request, 'dashboard/admin_create_account.html', {'dashboard_role': 'Admin', 'eyebrow': 'Academy setup', 'form': form})


@role_required(User.Role.ADMIN)
def teacher_list(request):
    query = request.GET.get('q', '').strip()
    teachers = User.objects.filter(role=User.Role.TEACHER).select_related('teacher_profile').order_by('first_name', 'last_name', 'email')
    if query:
        teachers = teachers.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query))
    return render(request, 'dashboard/teachers/list.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'teachers': teachers, 'query': query})


@role_required(User.Role.ADMIN)
def teacher_create(request):
    form = TeacherAccountCreationForm(request.POST or None, initial={'role': User.Role.TEACHER})
    if request.method == 'POST' and form.is_valid():
        teacher = form.save()
        messages.success(request, f'Teacher account created for {teacher.get_full_name() or teacher.email}.')
        return redirect('accounts:teacher_detail', pk=teacher.pk)
    return render(request, 'dashboard/teachers/form.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'form': form, 'mode': 'Create', 'teacher': None})


@role_required(User.Role.ADMIN)
def teacher_detail(request, pk):
    teacher = User.objects.filter(pk=pk, role=User.Role.TEACHER).select_related('teacher_profile').prefetch_related('teaching_classes__level').first()
    if not teacher:
        raise PermissionDenied
    return render(request, 'dashboard/teachers/detail.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'teacher': teacher})


@role_required(User.Role.ADMIN)
def teacher_edit(request, pk):
    teacher = User.objects.filter(pk=pk, role=User.Role.TEACHER).select_related('teacher_profile').first()
    if not teacher:
        raise PermissionDenied
    form = TeacherEditForm(request.POST or None, user=teacher)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Teacher profile updated.')
        return redirect('accounts:teacher_detail', pk=teacher.pk)
    return render(request, 'dashboard/teachers/form.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'form': form, 'mode': 'Edit', 'teacher': teacher})


@role_required(User.Role.ADMIN)
def teacher_delete(request, pk):
    teacher = User.objects.filter(pk=pk, role=User.Role.TEACHER).select_related('teacher_profile').first()
    if not teacher:
        raise PermissionDenied
    if request.method == 'POST':
        name = teacher.get_full_name() or teacher.email
        try:
            teacher.delete()
        except ProtectedError:
            messages.error(request, 'This teacher is assigned to one or more classes. Remove those assignments before deleting the account.')
            return redirect('accounts:teacher_detail', pk=pk)
        messages.success(request, f'Teacher account for {name} was deleted.')
        return redirect('accounts:teacher_list')
    return render(request, 'dashboard/teachers/delete.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'teacher': teacher})


@role_required(User.Role.ADMIN)
def student_list(request):
    query = request.GET.get('q', '').strip()
    students = User.objects.filter(role=User.Role.STUDENT).select_related('student_profile__current_level').prefetch_related('student_profile__enrollments__class_batch').order_by('first_name', 'last_name', 'email')
    if query:
        students = students.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query))
    return render(request, 'dashboard/students/list.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'students': students, 'query': query})


@role_required(User.Role.ADMIN)
def student_create(request):
    form = StudentAccountCreationForm(request.POST or None, initial={'role': User.Role.STUDENT})
    if request.method == 'POST' and form.is_valid():
        student = form.save()
        messages.success(request, f'Student account created for {student.get_full_name() or student.email}.')
        return redirect('accounts:student_detail', pk=student.pk)
    return render(request, 'dashboard/people/form.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'form': form, 'mode': 'Create', 'entity_label': 'student', 'back_url': 'accounts:student_list'})


@role_required(User.Role.ADMIN)
def student_detail(request, pk):
    student = User.objects.filter(pk=pk, role=User.Role.STUDENT).select_related('student_profile__current_level').prefetch_related('student_profile__enrollments__class_batch__level', 'student_profile__parents__parent__user').first()
    if not student:
        raise PermissionDenied
    return render(request, 'dashboard/students/detail.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'student': student})


@role_required(User.Role.ADMIN)
def student_edit(request, pk):
    student = User.objects.filter(pk=pk, role=User.Role.STUDENT).select_related('student_profile__current_level').first()
    if not student:
        raise PermissionDenied
    form = StudentEditForm(request.POST or None, user=student)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Student profile updated.')
        return redirect('accounts:student_detail', pk=student.pk)
    return render(request, 'dashboard/people/form.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'form': form, 'mode': 'Edit', 'entity_label': 'student', 'back_url': 'accounts:student_list'})


@role_required(User.Role.ADMIN)
def student_delete(request, pk):
    student = User.objects.filter(pk=pk, role=User.Role.STUDENT).first()
    if not student:
        raise PermissionDenied
    if request.method == 'POST':
        name = student.get_full_name() or student.email
        student.delete()
        messages.success(request, f'Student account for {name} was deleted.')
        return redirect('accounts:student_list')
    return render(request, 'dashboard/people/delete.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'person': student, 'entity_label': 'student', 'detail_url': 'accounts:student_detail'})


@role_required(User.Role.ADMIN)
def parent_list(request):
    query = request.GET.get('q', '').strip()
    parents = User.objects.filter(role=User.Role.PARENT).select_related('parent_profile').prefetch_related('parent_profile__children__student__user').order_by('first_name', 'last_name', 'email')
    if query:
        parents = parents.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query))
    return render(request, 'dashboard/parents/list.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'parents': parents, 'query': query})


@role_required(User.Role.ADMIN)
def parent_create(request):
    form = ParentAccountCreationForm(request.POST or None, initial={'role': User.Role.PARENT})
    if request.method == 'POST' and form.is_valid():
        parent = form.save()
        messages.success(request, f'Parent account created for {parent.get_full_name() or parent.email}.')
        return redirect('accounts:parent_detail', pk=parent.pk)
    return render(request, 'dashboard/people/form.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'form': form, 'mode': 'Create', 'entity_label': 'parent', 'back_url': 'accounts:parent_list'})


@role_required(User.Role.ADMIN)
def parent_detail(request, pk):
    parent = User.objects.filter(pk=pk, role=User.Role.PARENT).select_related('parent_profile').prefetch_related('parent_profile__children__student__current_level').first()
    if not parent:
        raise PermissionDenied
    return render(request, 'dashboard/parents/detail.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'parent': parent})


@role_required(User.Role.ADMIN)
def parent_edit(request, pk):
    parent = User.objects.filter(pk=pk, role=User.Role.PARENT).select_related('parent_profile').first()
    if not parent:
        raise PermissionDenied
    form = ParentEditForm(request.POST or None, user=parent)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Parent profile updated.')
        return redirect('accounts:parent_detail', pk=parent.pk)
    return render(request, 'dashboard/people/form.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'form': form, 'mode': 'Edit', 'entity_label': 'parent', 'back_url': 'accounts:parent_list'})


@role_required(User.Role.ADMIN)
def parent_delete(request, pk):
    parent = User.objects.filter(pk=pk, role=User.Role.PARENT).first()
    if not parent:
        raise PermissionDenied
    if request.method == 'POST':
        name = parent.get_full_name() or parent.email
        parent.delete()
        messages.success(request, f'Parent account for {name} was deleted.')
        return redirect('accounts:parent_list')
    return render(request, 'dashboard/people/delete.html', {'dashboard_role': 'Admin', 'eyebrow': 'People and access', 'person': parent, 'entity_label': 'parent', 'detail_url': 'accounts:parent_detail'})


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
