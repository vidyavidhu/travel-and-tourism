from django.urls import path
from .views import TripListView, TripDetailView, TripCreateView, TripUpdateView, TripDeleteView, TripDetailsCreateView, TripDetailsUpdateView, TripMembersCreateView, TripDayCreateView, ItineraryCreateView, ItineraryDetailView, GalleryCreateView, CommentCreateView, CommentLikeView, ReplyCreateView

urlpatterns = [
    path('', TripListView.as_view(), name='trip_list'),
    path('create/', TripCreateView.as_view(), name='trip_create'),
    path('<int:pk>/', TripDetailView.as_view(), name='trip_detail'),
    path('<int:pk>/update/', TripUpdateView.as_view(), name='trip_update'),
    path('<int:pk>/delete/', TripDeleteView.as_view(), name='trip_delete'),
    
    # Trip Details
    path('<int:trip_id>/details/add/', TripDetailsCreateView.as_view(), name='trip_details_create'),
    path('details/<int:pk>/update/', TripDetailsUpdateView.as_view(), name='trip_details_update'),
    
    # Trip Members
    path('<int:trip_id>/members/add/', TripMembersCreateView.as_view(), name='trip_members_create'),
    
    # Trip Days & Itinerary
    path('<int:trip_id>/days/add/', TripDayCreateView.as_view(), name='trip_day_create'),
    path('days/<int:day_id>/itinerary/add/', ItineraryCreateView.as_view(), name='itinerary_create'),
    path('itinerary/<int:pk>/', ItineraryDetailView.as_view(), name='itinerary_detail'),
    path('itinerary/<int:itinerary_id>/gallery/add/', GalleryCreateView.as_view(), name='gallery_create'),
    path('itinerary/<int:itinerary_id>/comment/add/', CommentCreateView.as_view(), name='comment_create'),
    path('comment/<int:comment_id>/like/', CommentLikeView.as_view(), name='comment_like'),
    path('comment/<int:comment_id>/reply/', ReplyCreateView.as_view(), name='reply_create'),
]
