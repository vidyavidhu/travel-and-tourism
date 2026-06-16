from django import forms
from .models import Trip
from member.models import Coordinator

class TripForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TripForm, self).__init__(*args, **kwargs)
        if 'coordinator' in self.fields:
            if user and hasattr(user, 'coordinator') and not user.is_superuser:
                self.fields['coordinator'].initial = user.coordinator
                self.fields['coordinator'].widget = forms.HiddenInput()
                self.fields['coordinator'].required = False
            else:
                qs = Coordinator.objects.filter(status=1)
                
                from_date = None
                to_date = None
                
                if self.is_bound and self.data:
                    from_date = self.data.get('from_date')
                    to_date = self.data.get('to_date')
                elif self.instance and self.instance.pk:
                    from_date = self.instance.from_date
                    to_date = self.instance.to_date
                    
                if from_date and to_date:
                    from django.db.models import Q
                    overlapping_trips = Trip.objects.filter(
                        Q(from_date__lte=to_date) & Q(to_date__gte=from_date)
                    )
                    if self.instance and self.instance.pk:
                        overlapping_trips = overlapping_trips.exclude(pk=self.instance.pk)
                        
                    busy_coordinator_ids = overlapping_trips.values_list('coordinator_id', flat=True)
                    qs = qs.exclude(id__in=busy_coordinator_ids)
                    
                self.fields['coordinator'].queryset = qs

    def clean_max_members(self):
        max_members = self.cleaned_data.get('max_members')
        if max_members is not None and max_members < 1:
            raise forms.ValidationError("There must be a minimum of 1 member to go on a trip.")
        return max_members

    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')
        from_time = cleaned_data.get('from_time')
        to_time = cleaned_data.get('to_time')

        from django.utils import timezone
        today = timezone.localdate()

        if from_date and from_date < today:
            self.add_error('from_date', "From date cannot be in the past.")

        if from_date and from_date == today:
            # Check from_time is not in the past today
            current_time = timezone.localtime().time()
            if from_time and from_time < current_time:
                self.add_error('from_time', "From time cannot be in the past for today's date.")

        if to_date:
            if from_date:
                if to_date < from_date:
                    self.add_error('to_date', "To date must be on or after the From date.")
            else:
                if to_date < today:
                    self.add_error('to_date', "To date cannot be in the past.")

        if from_date and to_date and from_date == to_date:
            if from_time and to_time and from_time >= to_time:
                self.add_error('to_time', "To time must be after the From time when the dates are the same.")

        return cleaned_data

    class Meta:
        model = Trip
        fields = ['image', 'title', 'category', 'max_members', 'location_from_name', 'location_from_lattitude', 'location_from_longitude', 'location_to_name', 'location_to_lattitude', 'location_to_longitude', 'distance', 'from_date', 'from_time', 'to_date', 'to_time', 'duration', 'description', 'coordinator', 'guidelines', 'status', 'approval_required']
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
            'max_members': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'guidelines': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'coordinator': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'approval_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TripFilterForm(forms.Form):
    title = forms.CharField(required=False, label='Title', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by title...'}))
    location_from_name = forms.CharField(required=False, label='Location-Start', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by Start location...'}))
    location_to_name = forms.CharField(required=False, label='Location-Destination', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by Destination location...'}))
    from_date = forms.DateField(required=False, label='From Date (>=)', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    to_date = forms.DateField(required=False, label='To Date (<=)', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    status = forms.ChoiceField(choices=[('', 'All'), (1, 'Active'), (0, 'Inactive'), (2, 'Completed')], required=False, widget=forms.Select(attrs={'class': 'form-control'}))

from .models import Trip_Details, Trip_Members, Trip_Day, Itinerary, Gallery, Comments

class TripDetailsForm(forms.ModelForm):
    class Meta:
        model = Trip_Details
        fields = ['max_members', 'estimated_cost', 'advance_amount', 'description']
        widgets = {
            'max_members': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'advance_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        max_members = cleaned_data.get('max_members')
        
        if max_members is not None and max_members < 1:
            self.add_error('max_members', "There must be a minimum of 1 member to go on a trip.")

        estimated_cost = cleaned_data.get('estimated_cost', 0.0) or 0.0
        advance_amount = cleaned_data.get('advance_amount', 0.0) or 0.0

        if max_members and max_members > 0:
            per_head_cost = estimated_cost / max_members
        else:
            per_head_cost = estimated_cost

        if advance_amount > per_head_cost:
            self.add_error('advance_amount', f"Advance amount (₹{advance_amount:.2f}) cannot be greater than the per-head cost (₹{per_head_cost:.2f}).")
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.no_of_members = instance.max_members
        if commit:
            instance.save()
        return instance

class TripMembersForm(forms.ModelForm):
    status = forms.TypedChoiceField(
        choices=[(0, 'Pending'), (1, 'Joined'), (2, 'Cancelled'), (3, 'Awaiting Advance')],
        coerce=int,
        initial=0,
        required=True,
        label="Join Status"
    )
    payment_status = forms.TypedChoiceField(
        choices=[(0, 'Unpaid'), (1, 'Paid')],
        coerce=int,
        initial=0,
        required=True,
        label="Payment Status"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is an update form, make unpaid_amount read-only
        if self.instance and self.instance.pk:
            self.fields['unpaid_amount'].widget.attrs['readonly'] = 'readonly'

    def clean(self):
        cleaned_data = super().clean()
        paid_amount = cleaned_data.get('paid_amount', 0.0) or 0.0
        unpaid_amount = cleaned_data.get('unpaid_amount', 0.0) or 0.0
        
        if self.instance and self.instance.pk:
            # During updates, calculate payment increase
            old_paid_amount = self.instance.paid_amount or 0.0
            old_unpaid_amount = self.instance.unpaid_amount or 0.0
            
            payment_amount = paid_amount - old_paid_amount
            if payment_amount > 0 and payment_amount > old_unpaid_amount:
                raise forms.ValidationError(
                    f"Payment amount (₹{payment_amount:.2f}) cannot be greater than the remaining unpaid amount (₹{old_unpaid_amount:.2f})."
                )
        else:
            # During creation, paid amount cannot exceed unpaid amount
            if paid_amount > unpaid_amount:
                raise forms.ValidationError(
                    f"Paid amount (₹{paid_amount:.2f}) cannot be greater than the unpaid amount (₹{unpaid_amount:.2f})."
                )
        
        return cleaned_data

    class Meta:
        model = Trip_Members
        fields = ['member', 'status', 'payment_status', 'paid_amount', 'unpaid_amount', 'description']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-control'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unpaid_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TripDayForm(forms.ModelForm):
    class Meta:
        model = Trip_Day
        fields = ['date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class ItineraryForm(forms.ModelForm):
    class Meta:
        model = Itinerary
        fields = ['title', 'vehicle', 'time_start', 'location_from_name', 'location_from_lattitude', 'location_from_longitude', 'time_end', 'distance', 'duration', 'location_to_name', 'location_to_lattitude', 'location_to_longitude', 'spending_time', 'location_image', 'guidelines', 'description']
        widgets = {
            'time_start': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'time_end': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'location_from_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_location_from_name'}),
            'location_to_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_location_to_name'}),
            'location_from_lattitude': forms.HiddenInput(attrs={'id': 'id_location_from_lattitude'}),
            'location_from_longitude': forms.HiddenInput(attrs={'id': 'id_location_from_longitude'}),
            'location_to_lattitude': forms.HiddenInput(attrs={'id': 'id_location_to_lattitude'}),
            'location_to_longitude': forms.HiddenInput(attrs={'id': 'id_location_to_longitude'}),
            'distance': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_distance', 'readonly': 'readonly'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_duration', 'readonly': 'readonly'}),
        }

class GalleryForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = ['title', 'image', 'video', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'video': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CommentsForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control bg-light border-0',
                'rows': 3,
                'placeholder': 'Share your thoughts about this place...',
                'required': 'required',
            })
        }
