from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    # ===== 選択画面 =====
    path('', views.user_select, name='user_select'),

    # ===== 認証 =====
    path('login/', views.ReportLoginView.as_view(), name='login'),
    path('signup/', views.signup_view, name='signup'),

    # ===== 一般ユーザー =====
    path('list/', views.report_list, name='report_list'),
    path('create/', views.report_create, name='report_create'),
    path('skill-sheet/create/', views.skill_sheet_create, name='skill_sheet_create'),
    path('<int:pk>/edit/', views.report_update, name='report_update'),
    path('<int:pk>/delete/', views.report_delete, name='report_delete'),
    path('logout/', views.ReportLogoutView.as_view(), name='logout'),

    # ===== 管理者 =====
    path('admin-login/', views.AdminLoginView.as_view(), name='admin_login'),
    path('admin-list/', views.admin_report_list, name='admin_report_list'),
    path('admin-users/', views.admin_user_list, name='admin_user_list'),
    path('admin-logout/', views.AdminLogoutView.as_view(), name='admin_logout'),

    # ===== PDF =====
    path('<int:pk>/pdf/', views.report_pdf, name='report_pdf'),

     # ===== password =====
path('password-reset/',auth_views.PasswordResetView.as_view(),name='password_reset'),
path('password-reset/done/',auth_views.PasswordResetDoneView.as_view(),name='password_reset_done'),
path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(),name='password_reset_confirm'),
path('reset/done/',auth_views.PasswordResetCompleteView.as_view(),name='password_reset_complete'),
]