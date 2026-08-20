from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Assignment, Attendance, ClassBatch, ClassHoliday, ClassSchedule, CurriculumNode, Enrollment, Level, LevelPromotion, ParentProfile, ParentStudentLink, Question, QuestionBank, StudentProfile, TeacherProfile, User


@admin.register(User)
class BrainGymUserAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'get_full_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = ((None, {'fields': ('email', 'password')}), ('Personal info', {'fields': ('first_name', 'last_name', 'role')}), ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}), ('Important dates', {'fields': ('last_login', 'date_joined')}))
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2', 'role')}),)
    filter_horizontal = ('groups', 'user_permissions')


admin.site.register([Level, CurriculumNode, QuestionBank, Question, Assignment, ClassBatch, ClassSchedule, ClassHoliday, LevelPromotion, Attendance, TeacherProfile, StudentProfile, ParentProfile, ParentStudentLink, Enrollment])

# Register your models here.
