from django import forms
from .models import Trip
from member.models import Coordinator

class TripForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TripForm, self).__init__(*args, **kwargs)
        if 'coordinator' in self.fields:
            self.fields['coordinator'].queryset = Coordinator.objects.filter(status=1)

    class Meta:
        model = Trip
        fields = ['image', 'title', 'category', 'location_from_name', 'location_from_lattitude', 'location_from_longitude', 'location_to_name', 'location_to_lattitude', 'location_to_longitude', 'distance', 'from_date', 'from_time', 'to_date', 'to_time', 'duration', 'description', 'coordinator', 'guidelines', 'status']
        exclude = []
        widgets = {
            'from_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'to_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'from_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'to_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'location_from_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_location_from_name'}),
            'location_to_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_location_to_name'}),
            'location_from_lattitude': forms.HiddenInput(attrs={'id': 'id_location_from_lattitude'}),
            'location_from_longitude': forms.HiddenInput(attrs={'id': 'id_location_from_longitude'}),
            'location_to_lattitude': forms.HiddenInput(attrs={'id': 'id_location_to_lattitude'}),
            'location_to_longitude': forms.HiddenInput(attrs={'id': 'id_location_to_longitude'}),
            'distance': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_distance', 'readonly': 'readonly'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_duration', 'readonly': 'readonly'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'guidelines': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'coordinator': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class TripFilterForm(forms.Form):
    title = forms.CharField(required=False, label='Title', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by title...'}))
    location_from_name = forms.CharField(required=False, label='Location-Start', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by Start location...'}))
    location_to_name = forms.CharField(required=False, label='Location-Destination', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by Destination location...'}))
    from_date = forms.DateField(required=False, label='From Date (>=)', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    to_date = forms.DateField(required=False, label='To Date (<=)', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    status = forms.ChoiceField(choices=[('', 'All'), (1, 'Active'), (0, 'Inactive')], required=False, widget=forms.Select(attrs={'class': 'form-control'}))

from .models import Trip_Details, Trip_Members, Trip_Day, Itinerary

class TripDetailsForm(forms.ModelForm):
    class Meta:
        model = Trip_Details
        fields = ['max_members', 'no_of_members', 'estimated_cost', 'description']

class TripMembersForm(forms.ModelForm):
    class Meta:
        model = Trip_Members
        fields = ['member', 'status', 'payment_status', 'description']

class TripDayForm(forms.ModelForm):
    class Meta:
        model = Trip_Day
        fields = ['activity_type', 'vehicle', 'date', 'time', 'location', 'location_image', 'guidelines', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }

class ItineraryForm(forms.ModelForm):
    class Meta:
        model = Itinerary
        fields = ['title', 'vehicle', 'date_start', 'time_start', 'location_start_geo', 'location_start_name', 'date_end', 'time_end', 'distance', 'travel_time', 'location_end_geo', 'location_end_name', 'spending_time', 'location_image', 'guidelines', 'description']
        widgets = {
            'date_start': forms.DateInput(attrs={'type': 'date'}),
            'time_start': forms.TimeInput(attrs={'type': 'time'}),
            'date_end': forms.DateInput(attrs={'type': 'date'}),
            'time_end': forms.TimeInput(attrs={'type': 'time'}),
        }

