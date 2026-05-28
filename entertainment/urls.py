from django.urls import path
from . import views

urlpatterns = [
    path('playlist/add/<int:trip_id>/', views.add_playlist, name='add_playlist'),
    path('playlist/delete/<int:playlist_id>/', views.delete_playlist, name='delete_playlist'),
    path('media/add/<int:playlist_id>/', views.add_media, name='add_media'),
    path('media/delete/<int:media_id>/', views.delete_media, name='delete_media'),
]
