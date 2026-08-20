from datetime import date

from django import forms

from .models import Assignment, ClassBatch, ClassHoliday, ClassSchedule, CurriculumNode, Enrollment, Level, LevelPromotion, ParentStudentLink, Question, QuestionBank, StudentProfile, Test, TestQuestion, User


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


class CurriculumNodeForm(forms.ModelForm):
    class Meta:
        model = CurriculumNode
        fields = ('level', 'parent', 'title', 'node_type', 'description', 'ordering', 'is_active')
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Mental addition'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Learning outcomes and guidance'}),
            'ordering': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['level'].queryset = Level.objects.order_by('code')
        self.fields['parent'].queryset = CurriculumNode.objects.select_related('level').order_by('level__code', 'ordering', 'title')
        self.fields['parent'].label_from_instance = lambda node: f'{node.level.code} · {node.title}'

    def clean(self):
        cleaned = super().clean()
        level = cleaned.get('level')
        parent = cleaned.get('parent')
        node_type = cleaned.get('node_type')
        if parent and level and parent.level_id != level.pk:
            self.add_error('parent', 'Choose a parent from the selected level.')
        if not parent and node_type and node_type != CurriculumNode.NodeType.SUBJECT:
            self.add_error('node_type', 'Top-level nodes must be subjects.')
        if parent and node_type == CurriculumNode.NodeType.SUBJECT:
            self.add_error('node_type', 'Subjects must be top-level nodes.')
        if parent and self.instance.pk:
            ancestor = parent
            seen = set()
            while ancestor:
                if ancestor.pk == self.instance.pk or ancestor.pk in seen:
                    self.add_error('parent', 'This parent would create a curriculum cycle.')
                    break
                seen.add(ancestor.pk)
                ancestor = ancestor.parent
        return cleaned


class QuestionBankForm(forms.ModelForm):
    class Meta:
        model = QuestionBank
        fields = ('name', 'description', 'is_active')
        widgets = {'name': forms.TextInput(attrs={'placeholder': 'Addition warm-up'}), 'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, node, created_by, **kwargs):
        self.node = node
        self.created_by = created_by
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        bank = super().save(commit=False)
        bank.node = self.node
        if not bank.pk:
            bank.created_by = self.created_by
        if commit:
            bank.save()
        return bank


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('prompt', 'question_type', 'correct_answer', 'options', 'explanation', 'difficulty', 'is_active')
        widgets = {
            'prompt': forms.Textarea(attrs={'rows': 3, 'placeholder': 'What is 7 + 8?'}),
            'options': forms.Textarea(attrs={'rows': 2, 'placeholder': '["13", "14", "15"]'}),
            'explanation': forms.Textarea(attrs={'rows': 2}),
            'difficulty': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }

    def __init__(self, *args, bank, **kwargs):
        self.bank = bank
        super().__init__(*args, **kwargs)

    def clean_options(self):
        options = self.cleaned_data.get('options')
        if options is None:
            return []
        if not isinstance(options, list):
            raise forms.ValidationError('Options must be a JSON list, for example ["12", "13"].')
        return options

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('question_type') == Question.QuestionType.MULTIPLE_CHOICE and not cleaned.get('options'):
            self.add_error('options', 'Multiple-choice questions need at least one option.')
        if cleaned.get('question_type') == Question.QuestionType.MULTIPLE_CHOICE and cleaned.get('options') and cleaned.get('correct_answer') not in [str(option) for option in cleaned['options']]:
            self.add_error('correct_answer', 'The correct answer must match one of the options.')
        return cleaned

    def save(self, commit=True):
        question = super().save(commit=False)
        question.bank = self.bank
        if commit:
            question.save()
        return question


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ('title', 'instructions', 'due_date', 'is_published')
        widgets = {'title': forms.TextInput(attrs={'placeholder': 'Week 1 practice'}), 'instructions': forms.Textarea(attrs={'rows': 4}), 'due_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, node, created_by, **kwargs):
        self.node = node
        self.created_by = created_by
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        assignment = super().save(commit=False)
        assignment.node = self.node
        if not assignment.pk:
            assignment.created_by = self.created_by
        if commit:
            assignment.save()
        return assignment


class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ('title', 'instructions', 'duration_minutes', 'passing_score', 'is_published')
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Level 2 assessment'}),
            'instructions': forms.Textarea(attrs={'rows': 4}),
            'duration_minutes': forms.NumberInput(attrs={'min': 1}),
            'passing_score': forms.NumberInput(attrs={'min': 0, 'max': 100}),
        }

    def __init__(self, *args, node, created_by, **kwargs):
        self.node = node
        self.created_by = created_by
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        test = super().save(commit=False)
        test.node = self.node
        if not test.pk:
            test.created_by = self.created_by
        if commit:
            test.save()
        return test


class TestQuestionForm(forms.ModelForm):
    class Meta:
        model = TestQuestion
        fields = ('question', 'ordering', 'points')
        widgets = {'ordering': forms.NumberInput(attrs={'min': 1}), 'points': forms.NumberInput(attrs={'min': 1})}

    def __init__(self, *args, test, **kwargs):
        self.test = test
        super().__init__(*args, **kwargs)
        self.fields['ordering'].required = True
        if not self.is_bound and not self.instance.pk:
            self.initial['ordering'] = test.test_questions.count() + 1
        node_ids = {test.node_id}
        frontier = {test.node_id}
        while frontier:
            child_ids = set(CurriculumNode.objects.filter(level=test.node.level, parent_id__in=frontier).values_list('pk', flat=True))
            frontier = child_ids - node_ids
            node_ids.update(frontier)
        self.fields['question'].queryset = Question.objects.filter(
            bank__node_id__in=node_ids,
            is_active=True,
        ).exclude(test_memberships__test=test).select_related('bank__node').order_by('bank__name', 'difficulty', 'pk')
        self.fields['question'].label_from_instance = lambda question: f'{question.bank.name} · {question.prompt[:70]}'

    def clean_ordering(self):
        ordering = self.cleaned_data['ordering']
        if TestQuestion.objects.filter(test=self.test, ordering=ordering).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This question number is already used in the test.')
        return ordering


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
        Enrollment.objects.filter(student=student, is_active=True).exclude(class_batch=self.batch).update(is_active=False, status=Enrollment.Status.LEFT, ended_on=date.today())
        enrollment, _ = Enrollment.objects.update_or_create(student=student, class_batch=self.batch, defaults={'is_active': True, 'status': Enrollment.Status.ONGOING, 'ended_on': None})
        student.current_level = self.batch.level
        student.save(update_fields=['current_level'])
        return enrollment


class StudentPromotionForm(forms.Form):
    to_level = forms.ModelChoiceField(queryset=Level.objects.all(), label='Promote to level')
    note = forms.CharField(max_length=240, required=False, label='Promotion note', widget=forms.TextInput(attrs={'placeholder': 'Passed Level 2 assessment'}))

    def __init__(self, *args, student, **kwargs):
        self.student = student
        super().__init__(*args, **kwargs)
        if student.student_profile.current_level_id:
            self.fields['to_level'].queryset = Level.objects.exclude(pk=student.student_profile.current_level_id)

    def clean_to_level(self):
        level = self.cleaned_data['to_level']
        if self.student.student_profile.current_level_id == level.pk:
            raise forms.ValidationError('The student is already at this level.')
        return level


class EnrollmentStatusForm(forms.Form):
    status = forms.ChoiceField(choices=Enrollment.Status.choices, label='Class status')

    def __init__(self, *args, enrollment, **kwargs):
        self.enrollment = enrollment
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial['status'] = enrollment.status

    def save(self):
        status = self.cleaned_data['status']
        self.enrollment.status = status
        self.enrollment.is_active = status == Enrollment.Status.ONGOING
        self.enrollment.ended_on = None if self.enrollment.is_active else date.today()
        self.enrollment.save(update_fields=['status', 'is_active', 'ended_on'])
        return self.enrollment
