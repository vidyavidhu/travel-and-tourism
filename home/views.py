from django.shortcuts import render
from django.utils import timezone
from trip.models import Trip

# Create your views here.
def home_view(request):
    # Fetch active ongoing or upcoming trips based on current date
    trips = Trip.objects.filter(status=1, to_date__gte=timezone.now().date()).order_by('from_date')[:6]
    return render(request, 'home.html', {'trips': trips})
