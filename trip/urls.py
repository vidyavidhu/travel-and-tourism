from django.urls import path
from .views import TripListView, TripDetailView, TripCreateView, TripUpdateView, TripDeleteView, TripDetailsCreateView, TripDetailsUpdateView, TripMembersCreateView, TripMembersUpdateView, TripDayCreateView, ItineraryCreateView, ItineraryDetailView, GalleryCreateView, CommentCreateView, CommentLikeView, ReplyCreateView, MyTripsView, TripMemberApproveView, TripFinishView
from finance.views import ExpenseCreateView, ExpenseDeleteView

urlpatterns = [
    path('', TripListView.as_view(), name='trip_list'),
    path('create/', TripCreateView.as_view(), name='trip_create'),
    path('my-trips/', MyTripsView.as_view(), name='my_trips'),
    path('<int:pk>/', TripDetailView.as_view(), name='trip_detail'),
    path('<int:pk>/update/', TripUpdateView.as_view(), name='trip_update'),
    path('<int:pk>/delete/', TripDeleteView.as_view(), name='trip_delete'),
    path('<int:pk>/finish/', TripFinishView.as_view(), name='trip_finish'),
    
    # Trip Details
    path('<int:trip_id>/details/add/', TripDetailsCreateView.as_view(), name='trip_details_create'),
    path('details/<int:pk>/update/', TripDetailsUpdateView.as_view(), name='trip_details_update'),
    
    # Trip Members
    path('<int:trip_id>/members/add/', TripMembersCreateView.as_view(), name='trip_members_create'),
    path('members/<int:pk>/update/', TripMembersUpdateView.as_view(), name='trip_members_update'),
    path('members/<int:pk>/approve/', TripMemberApproveView.as_view(), name='trip_member_approve'),
    
    # Trip Days & Itinerary
    path('<int:trip_id>/days/add/', TripDayCreateView.as_view(), name='trip_day_create'),
    path('days/<int:day_id>/itinerary/add/', ItineraryCreateView.as_view(), name='itinerary_create'),
    path('itinerary/<int:pk>/', ItineraryDetailView.as_view(), name='itinerary_detail'),
    path('itinerary/<int:itinerary_id>/gallery/add/', GalleryCreateView.as_view(), name='gallery_create'),
    path('itinerary/<int:itinerary_id>/comment/add/', CommentCreateView.as_view(), name='comment_create'),
    path('comment/<int:comment_id>/like/', CommentLikeView.as_view(), name='comment_like'),
    path('comment/<int:comment_id>/reply/', ReplyCreateView.as_view(), name='reply_create'),
    
    # Finance Expenses
    path('<int:trip_id>/finance/expense/add/', ExpenseCreateView.as_view(), name='expense_create'),
    path('finance/expense/<int:pk>/delete/', ExpenseDeleteView.as_view(), name='expense_delete'),
]
