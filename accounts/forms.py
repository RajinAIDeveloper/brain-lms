from django import forms

from .models import User


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
