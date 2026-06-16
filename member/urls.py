from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('signup/', views.signup_view, name='member_signup'),
    path('login/', views.login_view, name='member_login'),
    path('logout/', views.logout_view, name='member_logout'),
    path('profile/', views.profile_view, name='member_profile'),
    path('profile/edit/', views.profile_edit_view, name='member_profile_edit'),
    
    # Password Reset URL Patterns
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete_view, name='password_reset_complete'),

    
    # Admin Dashboard & Coordinator management URLs
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/coordinators/', views.admin_coordinators_list_view, name='admin_coordinators_list'),
    path('admin-dashboard/coordinators/<int:pk>/', views.admin_coordinator_detail_view, name='admin_coordinator_detail'),
    path('admin-dashboard/coordinators/<int:pk>/toggle-approve/', views.admin_coordinator_toggle_approve_view, name='admin_coordinator_toggle_approve'),
    path('admin-dashboard/coordinators/notify/', views.admin_coordinator_notify_view, name='admin_coordinator_notify'),
    path('notifications/<int:pk>/mark-read/', views.mark_notification_read_view, name='mark_notification_read'),
    path('trip-broadcasts/<int:pk>/mark-read/', views.mark_trip_broadcast_read_view, name='mark_trip_broadcast_read'),
    
    # Member access control routes
    path('admin-dashboard/members/<int:pk>/toggle-access/', views.admin_member_toggle_access, name='admin_member_toggle_access'),
    path('admin-dashboard/members/<int:pk>/cancel-trips/', views.admin_member_cancel_trips, name='admin_member_cancel_trips'),
    path('admin-dashboard/members/<int:pk>/handle-request/<str:action>/', views.admin_member_handle_request, name='admin_member_handle_request'),
    path('request-access/', views.member_request_access, name='member_request_access'),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
