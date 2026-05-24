from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from trip.models import Trip, Trip_Details, Trip_Members, Trip_Day

# Create your views here.
def home_view(request):
    today = timezone.localdate()
    trips = Trip.objects.filter(status=1, to_date__gte=today).order_by('-id')
    return render(request, 'home.html', {'trips': trips})

def home_trip_details(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    
    # Try fetching details
    try:
        trip_details = Trip_Details.objects.get(trip=trip)
    except Trip_Details.DoesNotExist:
        trip_details = None
        
    trip_members = Trip_Members.objects.filter(trip=trip)
    
    # Advanced prefetching to load days, stop details, gallery items, comments, replies, and reactions
    trip_days = Trip_Day.objects.filter(trip=trip).order_by('date').prefetch_related(
        'itinerary_set',
        'itinerary_set__vehicle',
        'itinerary_set__gallery_set',
        'itinerary_set__gallery_set__uploaded_by__member__user',
        'itinerary_set__comments_set',
        'itinerary_set__comments_set__message_by__member__user',
        'itinerary_set__comments_set__replies',
        'itinerary_set__comments_set__replies__reply_by__member__user',
        'itinerary_set__comments_set__reaction_set',
        'itinerary_set__comments_set__replies__reaction_set',
        'itinerary_set__rating_set',
    )
    
    context = {
        'trip': trip,
        'trip_details': trip_details,
        'trip_members': trip_members,
        'trip_days': trip_days,
    }
    return render(request, 'home_trip_details.html', context)
