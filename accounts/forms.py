from django import forms

from .models import ClassBatch, ClassHoliday, ClassSchedule, Enrollment, Level, ParentStudentLink, StudentProfile, User


class AdminAccountCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Temporary password', widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), min_length=8)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), min_length=8)
    role = forms.ChoiceField(choices=[
        (User.Role.TEACHER, 'Teacher'),
        (User.Role.STUDENT, 'Student'),
        (User.Role.PARENT, 'Parent'),
    ])

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'role')
        widgets = {
            'first_name': forms.TextInput(attrs={'autocomplete': 'given-name', 'placeholder': 'Sara'}),
            'last_name': forms.TextInput(attrs={'autocomplete': 'family-name', 'placeholder': 'Ahmed'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'name@example.com'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password1') and cleaned_data.get('password1') != cleaned_data.get('password2'):
            self.add_error('password2', 'The passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = True
        if commit:
            user.save()
        return user


class TeacherAccountCreationForm(AdminAccountCreationForm):
    """Teacher-specific create form used by the teacher CRUD section."""

    role = forms.CharField(widget=forms.HiddenInput(), initial=User.Role.TEACHER)

    def clean_role(self):
        return User.Role.TEACHER


class TeacherEditForm(forms.Form):
    first_name = forms.CharField(max_length=150, label='First name')
    last_name = forms.CharField(max_length=150, label='Last name')
    email = forms.EmailField(label='Email')
    display_title = forms.CharField(max_length=120, label='Professional title')
    is_active = forms.BooleanField(required=False, label='Account is active')

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial.update({
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'display_title': user.teacher_profile.display_title,
                'is_active': user.is_active,
            })

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self):
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        self.user.is_active = self.cleaned_data['is_active']
        self.user.save()
        profile = self.user.teacher_profile
        profile.display_title = self.cleaned_data['display_title']
        profile.save()
        return self.user


class StudentAccountCreationForm(AdminAccountCreationForm):
    role = forms.CharField(widget=forms.HiddenInput(), initial=User.Role.STUDENT)

    def clean_role(self):
        return User.Role.STUDENT


class ParentAccountCreationForm(AdminAccountCreationForm):
    role = forms.CharField(widget=forms.HiddenInput(), initial=User.Role.PARENT)

    def clean_role(self):
        return User.Role.PARENT


class StudentEditForm(forms.Form):
    first_name = forms.CharField(max_length=150, label='First name')
    last_name = forms.CharField(max_length=150, label='Last name')
    email = forms.EmailField(label='Email')
    current_level = forms.ModelChoiceField(queryset=Level.objects.all(), required=False, label='Current level')
    is_active = forms.BooleanField(required=False, label='Account is active')

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            profile = user.student_profile
            self.initial.update({'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email, 'current_level': profile.current_level_id, 'is_active': user.is_active})

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self):
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        self.user.is_active = self.cleaned_data['is_active']
        self.user.save()
        profile = self.user.student_profile
        profile.current_level = self.cleaned_data['current_level']
        profile.save()
        return self.user


class ParentEditForm(forms.Form):
    first_name = forms.CharField(max_length=150, label='First name')
    last_name = forms.CharField(max_length=150, label='Last name')
    email = forms.EmailField(label='Email')
    is_active = forms.BooleanField(required=False, label='Account is active')

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial.update({'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email, 'is_active': user.is_active})

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self):
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        self.user.is_active = self.cleaned_data['is_active']
        self.user.save()
        return self.user


class ParentStudentLinkForm(forms.Form):
    student = forms.ModelChoiceField(queryset=StudentProfile.objects.none(), label='Student to link')
    relationship = forms.CharField(max_length=40, initial='Parent', label='Relationship')

    def __init__(self, *args, parent, **kwargs):
        self.parent = parent
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = StudentProfile.objects.filter(user__role=User.Role.STUDENT, user__is_active=True).select_related('user', 'current_level').order_by('user__first_name', 'user__last_name', 'user__email')
        self.fields['student'].label_from_instance = lambda student: f"{student.user.get_full_name() or student.user.email} · {student.current_level or 'Level not assigned'}"

    def clean_student(self):
        student = self.cleaned_data['student']
        if ParentStudentLink.objects.filter(parent=self.parent, student=student).exists():
            raise forms.ValidationError('This student is already linked to this parent.')
        return student

    def save(self):
        return ParentStudentLink.objects.create(parent=self.parent, student=self.cleaned_data['student'], relationship=self.cleaned_data['relationship'].strip() or 'Parent')


class LevelForm(forms.ModelForm):
    class Meta:
        model = Level
        fields = ('name', 'code', 'description')
        widgets = {'name': forms.TextInput(attrs={'placeholder': 'Level 2'}), 'code': forms.TextInput(attrs={'placeholder': 'L2'}), 'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What students learn at this level'})}

    def clean_code(self):
        return self.cleaned_data['code'].strip().upper()


class ClassBatchForm(forms.ModelForm):
    class Meta:
        model = ClassBatch
        fields = ('name', 'level', 'teacher', 'start_date', 'end_date', 'is_active')
        widgets = {'name': forms.TextInput(attrs={'placeholder': 'Batch A'}), 'level': forms.Select(), 'teacher': forms.Select(), 'start_date': forms.DateInput(attrs={'type': 'date'}), 'end_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].required = True
        self.fields['end_date'].required = True
        self.fields['teacher'].queryset = User.objects.filter(role=User.Role.TEACHER, is_active=True).order_by('first_name', 'last_name', 'email')
        self.fields['teacher'].label_from_instance = lambda teacher: teacher.get_full_name() or teacher.email

    def clean_teacher(self):
        teacher = self.cleaned_data['teacher']
        if teacher.role != User.Role.TEACHER:
            raise forms.ValidationError('Only teacher accounts can lead a class.')
        return teacher


class ClassScheduleForm(forms.ModelForm):
    class Meta:
        model = ClassSchedule
        fields = ('weekday', 'start_time', 'end_time')
        widgets = {'weekday': forms.Select(), 'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}), 'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'})}

    def __init__(self, *args, batch, **kwargs):
        self.batch = batch
        super().__init__(*args, **kwargs)
        self.instance.class_batch = batch

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_time')
        end = cleaned.get('end_time')
        if start and end and end <= start:
            self.add_error('end_time', 'End time must be after start time.')
        if start and end and cleaned.get('weekday') is not None:
            overlaps = ClassSchedule.objects.filter(class_batch=self.batch, weekday=cleaned['weekday'], start_time__lt=end, end_time__gt=start).exclude(pk=self.instance.pk)
            if overlaps.exists():
                self.add_error(None, 'This schedule overlaps another schedule on the same day.')
        return cleaned

    def save(self, commit=True):
        schedule = super().save(commit=False)
        schedule.class_batch = self.batch
        if commit:
            schedule.save()
        return schedule


class ClassHolidayForm(forms.ModelForm):
    class Meta:
        model = ClassHoliday
        fields = ('date', 'note')
        widgets = {'date': forms.DateInput(attrs={'type': 'date'}), 'note': forms.TextInput(attrs={'placeholder': 'Public holiday, school event, etc.'})}

    def __init__(self, *args, batch, **kwargs):
        self.batch = batch
        super().__init__(*args, **kwargs)
        self.instance.class_batch = batch

    def clean_date(self):
        date = self.cleaned_data['date']
        if self.batch.start_date and date < self.batch.start_date:
            raise forms.ValidationError('Holiday must be within the class date range.')
        if self.batch.end_date and date > self.batch.end_date:
            raise forms.ValidationError('Holiday must be within the class date range.')
        if ClassHoliday.objects.filter(class_batch=self.batch, date=date).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This date is already marked as a holiday.')
        return date

    def save(self, commit=True):
        holiday = super().save(commit=False)
        holiday.class_batch = self.batch
        if commit:
            holiday.save()
        return holiday


class EnrollmentForm(forms.Form):
    student = forms.ModelChoiceField(queryset=StudentProfile.objects.none(), label='Student to enroll')

    def __init__(self, *args, batch, **kwargs):
        self.batch = batch
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = StudentProfile.objects.filter(user__role=User.Role.STUDENT, user__is_active=True).exclude(enrollments__class_batch=batch, enrollments__is_active=True).select_related('user', 'current_level').order_by('user__first_name', 'user__last_name', 'user__email')
        self.fields['student'].label_from_instance = lambda student: f"{student.user.get_full_name() or student.user.email} · {student.current_level or 'Level not assigned'}"

    def clean_student(self):
        student = self.cleaned_data['student']
        enrollment = Enrollment.objects.filter(student=student, class_batch=self.batch).first()
        if enrollment and enrollment.is_active:
            raise forms.ValidationError('This student is already enrolled in this class.')
        return student

    def save(self):
        student = self.cleaned_data['student']
        Enrollment.objects.filter(student=student, is_active=True).exclude(class_batch=self.batch).update(is_active=False)
        enrollment, _ = Enrollment.objects.update_or_create(student=student, class_batch=self.batch, defaults={'is_active': True})
        student.current_level = self.batch.level
        student.save(update_fields=['current_level'])
        return enrollment
