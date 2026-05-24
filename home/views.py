from django.shortcuts import render
from django.utils import timezone
from trip.models import Trip

# Create your views here.
def home_view(request):
    trips = Trip.objects.all().order_by('-id')
    return render(request, 'home.html', {'trips': trips})
