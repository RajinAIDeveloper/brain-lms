from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.dashboard_redirect, name='home'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/users/', views.admin_users, name='admin_users'),
    path('dashboard/admin/accounts/new/', views.admin_create_account, name='admin_create_account'),
    path('dashboard/admin/teachers/', views.teacher_list, name='teacher_list'),
    path('dashboard/admin/teachers/new/', views.teacher_create, name='teacher_create'),
    path('dashboard/admin/teachers/<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('dashboard/admin/teachers/<int:pk>/edit/', views.teacher_edit, name='teacher_edit'),
    path('dashboard/admin/teachers/<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/parent/', views.parent_dashboard, name='parent_dashboard'),
]
