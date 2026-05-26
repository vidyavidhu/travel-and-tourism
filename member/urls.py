from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('signup/', views.signup_view, name='member_signup'),
    path('login/', views.login_view, name='member_login'),
    path('logout/', views.logout_view, name='member_logout'),
    path('profile/', views.profile_view, name='member_profile'),
    path('profile/edit/', views.profile_edit_view, name='member_profile_edit'),
    
    # Admin Dashboard & Coordinator management URLs
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/coordinators/', views.admin_coordinators_list_view, name='admin_coordinators_list'),
    path('admin-dashboard/coordinators/<int:pk>/', views.admin_coordinator_detail_view, name='admin_coordinator_detail'),
    path('admin-dashboard/coordinators/<int:pk>/toggle-approve/', views.admin_coordinator_toggle_approve_view, name='admin_coordinator_toggle_approve'),
    path('admin-dashboard/coordinators/notify/', views.admin_coordinator_notify_view, name='admin_coordinator_notify'),
    path('notifications/<int:pk>/mark-read/', views.mark_notification_read_view, name='mark_notification_read'),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
