from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Attendance, ClassBatch, ClassHoliday, ClassSchedule, Enrollment, Level, LevelPromotion, ParentProfile, ParentStudentLink, StudentProfile, TeacherProfile, User


@admin.register(User)
class BrainGymUserAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'get_full_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = ((None, {'fields': ('email', 'password')}), ('Personal info', {'fields': ('first_name', 'last_name', 'role')}), ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}), ('Important dates', {'fields': ('last_login', 'date_joined')}))
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2', 'role')}),)
    filter_horizontal = ('groups', 'user_permissions')


admin.site.register([Level, ClassBatch, ClassSchedule, ClassHoliday, LevelPromotion, Attendance, TeacherProfile, StudentProfile, ParentProfile, ParentStudentLink, Enrollment])

# Register your models here.
