from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Assignment, Attendance, ClassActivity, ClassBatch, ClassHoliday, ClassSchedule, ClassSession, CurriculumNode, Enrollment, Level, LevelPromotion, MakeupGroup, MakeupGroupStudent, ParentProfile, ParentStudentLink, Question, QuestionBank, StudentProfile, TeacherProfile, Test, TestAttempt, TestQuestion, User


@admin.register(User)
class BrainGymUserAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'get_full_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = ((None, {'fields': ('email', 'password')}), ('Personal info', {'fields': ('first_name', 'last_name', 'role')}), ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}), ('Important dates', {'fields': ('last_login', 'date_joined')}))
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2', 'role')}),)
    filter_horizontal = ('groups', 'user_permissions')


admin.site.register([Level, CurriculumNode, QuestionBank, Question, Assignment, Test, TestQuestion, TestAttempt, ClassBatch, ClassSchedule, ClassHoliday, ClassSession, ClassActivity, LevelPromotion, Attendance, MakeupGroup, MakeupGroupStudent, TeacherProfile, StudentProfile, ParentProfile, ParentStudentLink, Enrollment])

# Register your models here.
