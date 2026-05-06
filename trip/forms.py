from django import forms
from .models import Trip

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['image', 'title', 'category', 'location', 'distance', 'from_date', 'from_time', 'to_date', 'to_time', 'duration', 'description', 'coordinator', 'guidelines', 'status']
        widgets = {
            'from_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'to_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'from_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'to_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'distance': forms.NumberInput(attrs={'class': 'form-control'}),
            'duration': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'guidelines': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'coordinator': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class TripFilterForm(forms.Form):
    title = forms.CharField(required=False, label='Title', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by title...'}))
    location = forms.CharField(required=False, label='Location', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by location...'}))
    from_date = forms.DateField(required=False, label='From Date (>=)', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    to_date = forms.DateField(required=False, label='To Date (<=)', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    status = forms.ChoiceField(choices=[('', 'All'), (1, 'Active'), (0, 'Inactive')], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
