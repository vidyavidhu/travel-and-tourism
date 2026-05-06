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
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
