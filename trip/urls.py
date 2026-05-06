from django.urls import path
from .views import TripListView, TripDetailView, TripCreateView, TripUpdateView, TripDeleteView

urlpatterns = [
    path('', TripListView.as_view(), name='trip_list'),
    path('create/', TripCreateView.as_view(), name='trip_create'),
    path('<int:pk>/', TripDetailView.as_view(), name='trip_detail'),
    path('<int:pk>/update/', TripUpdateView.as_view(), name='trip_update'),
    path('<int:pk>/delete/', TripDeleteView.as_view(), name='trip_delete'),
]
