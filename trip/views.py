from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from .models import Trip, Trip_Details, Trip_Members, Trip_Day, Itinerary, Gallery, Comments, Reply, Reaction, Rating
from .forms import TripForm, TripFilterForm, TripDetailsForm, TripMembersForm, TripDayForm, ItineraryForm, GalleryForm, CommentsForm



class TripListView(ListView):
    model = Trip
    template_name = 'trip/trip_list.html'
    context_object_name = 'trips'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filter_form = TripFilterForm(self.request.GET)
        
        if self.filter_form.is_valid():
            title = self.filter_form.cleaned_data.get('title')
            location_from_name = self.filter_form.cleaned_data.get('location_from_name')
            location_to_name = self.filter_form.cleaned_data.get('location_to_name')
            from_date = self.filter_form.cleaned_data.get('from_date')
            to_date = self.filter_form.cleaned_data.get('to_date')
            status = self.filter_form.cleaned_data.get('status')
            
            if title:
                queryset = queryset.filter(title__icontains=title)
            if location_from_name:
                queryset = queryset.filter(location_from_name__icontains=location_from_name)
            if location_to_name:
                queryset = queryset.filter(location_to_name__icontains=location_to_name)
            if from_date:
                queryset = queryset.filter(Q(from_date=from_date) | Q(to_date=from_date))
            if to_date:
                queryset = queryset.filter(to_date__lte=to_date)
            if status:
                queryset = queryset.filter(status=status)
                
        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = getattr(self, 'filter_form', TripFilterForm(self.request.GET))
        return context

class TripDetailView(DetailView):
    model = Trip
    template_name = 'trip/trip_detail.html'
    context_object_name = 'trip'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = self.object
        
        # Details
        from .models import Trip_Details, Trip_Members, Trip_Day
        try:
            context['trip_details'] = Trip_Details.objects.get(trip=trip)
        except Trip_Details.DoesNotExist:
            context['trip_details'] = None
            
        # Members
        context['trip_members'] = Trip_Members.objects.filter(trip=trip)
        
        # Days
        context['trip_days'] = Trip_Day.objects.filter(trip=trip).prefetch_related('itinerary_set')
        
        # Finance metrics calculations
        trip_details = context['trip_details']
        trip_members = context['trip_members']
        
        from finance.models import Expenses
        from django.db.models import Sum
        
        # Total expected collection / Estimated Cost
        estimated_cost = trip_details.estimated_cost if trip_details else 0.0
        context['estimated_cost'] = estimated_cost
        
        # Actual collection = sum of paid_amount of all trip members
        actual_collection = trip_members.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0.0
        context['actual_collection'] = actual_collection
        
        # Total expenses = sum of amount of all expenses related to this trip
        expenses = Expenses.objects.filter(trip=trip).order_by('-id')
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0.0
        context['expenses'] = expenses
        context['total_expenses'] = total_expenses
        
        # Pending money for trip = actual collection - total expenses
        pending_money = actual_collection - total_expenses
        context['pending_money'] = pending_money
        
        # Additional collection and per-head cost calculations
        additional_collection = 0.0
        additional_cost_per_head = 0.0
        if total_expenses > estimated_cost:
            additional_collection = total_expenses - estimated_cost
            joined_count = sum(m.group_size for m in trip_members.filter(status=1))
            if joined_count == 0:
                joined_count = trip_details.no_of_members or trip_details.max_members or 1
            additional_cost_per_head = additional_collection / joined_count
            
        context['additional_collection'] = additional_collection
        context['additional_cost_per_head'] = additional_cost_per_head
        
        # Check if user is coordinator of this trip or admin
        is_coordinator = False
        if self.request.user.is_authenticated:
            if self.request.user.is_superuser or self.request.user.is_staff or trip.coordinator.user == self.request.user:
                is_coordinator = True
        context['is_coordinator'] = is_coordinator
        
        # Fetch trip broadcast messages
        from .models import TripBroadcastMessage
        context['broadcast_messages'] = TripBroadcastMessage.objects.filter(trip=trip).order_by('-created_at')
        
        return context

from .models import Trip_Details, Trip_Members, Trip_Day, Itinerary
from .forms import TripDetailsForm, TripMembersForm, TripDayForm, ItineraryForm
from django.urls import reverse

class TripDetailsCreateView(CreateView):
    model = Trip_Details
    form_class = TripDetailsForm
    template_name = 'trip/trip_form.html'
    
    def form_valid(self, form):
        trip = get_object_or_404(Trip, pk=self.kwargs['trip_id'])
        form.instance.trip = trip
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.kwargs['trip_id']})

class TripDetailsUpdateView(UpdateView):
    model = Trip_Details
    form_class = TripDetailsForm
    template_name = 'trip/trip_form.html'
    
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.object.trip.pk})

class TripMembersCreateView(CreateView):
    model = Trip_Members
    form_class = TripMembersForm
    template_name = 'trip/trip_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        trip = get_object_or_404(Trip, pk=self.kwargs['trip_id'])
        try:
            trip_details = Trip_Details.objects.get(trip=trip)
            initial['unpaid_amount'] = trip_details.per_head_cost
        except Trip_Details.DoesNotExist:
            initial['unpaid_amount'] = 0.0
        initial['paid_amount'] = 0.0
        return initial
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = get_object_or_404(Trip, pk=self.kwargs['trip_id'])
        try:
            trip_details = Trip_Details.objects.get(trip=trip)
            context['per_head_cost'] = trip_details.per_head_cost
        except Trip_Details.DoesNotExist:
            context['per_head_cost'] = None
        return context
    
    def form_valid(self, form):
        trip = get_object_or_404(Trip, pk=self.kwargs['trip_id'])
        form.instance.trip = trip
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.kwargs['trip_id']})

class TripMembersUpdateView(UpdateView):
    model = Trip_Members
    form_class = TripMembersForm
    template_name = 'trip/trip_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = "Update Trip Member Details"
        
        # Inject co-travellers for the member of this trip
        from .models import CoTraveller
        context['co_travellers'] = CoTraveller.objects.filter(
            trip=self.object.trip,
            user=self.object.member.user
        )
        return context
        
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.object.trip.pk})

class TripDayCreateView(CreateView):
    model = Trip_Day
    form_class = TripDayForm
    template_name = 'trip/trip_form.html'
    
    def form_valid(self, form):
        trip = get_object_or_404(Trip, pk=self.kwargs['trip_id'])
        form.instance.trip = trip
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.kwargs['trip_id']})

class ItineraryCreateView(CreateView):
    model = Itinerary
    form_class = ItineraryForm
    template_name = 'trip/trip_form.html'
    
    def form_valid(self, form):
        day = get_object_or_404(Trip_Day, pk=self.kwargs['day_id'])
        form.instance.trip_day = day
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.object.trip_day.trip.pk})

class TripCreateView(CreateView):
    model = Trip
    form_class = TripForm
    template_name = 'trip/trip_form.html'
    success_url = reverse_lazy('trip_list')

class TripUpdateView(UpdateView):
    model = Trip
    form_class = TripForm
    template_name = 'trip/trip_form.html'
    success_url = reverse_lazy('trip_list')

class TripDeleteView(DeleteView):
    model = Trip
    template_name = 'trip/trip_confirm_delete.html'
    success_url = reverse_lazy('trip_list')

class ItineraryDetailView(DetailView):
    model = Itinerary
    template_name = 'trip/itinerary_detail.html'
    context_object_name = 'itinerary'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['gallery_items'] = Gallery.objects.filter(itinerary=self.object).order_by('-date_time')
        context['comments'] = Comments.objects.filter(itinerary=self.object).order_by('-date_time')
        from .forms import GalleryForm
        context['gallery_form'] = GalleryForm()
        return context

class GalleryCreateView(LoginRequiredMixin, CreateView):
    model = Gallery
    form_class = GalleryForm
    
    def form_valid(self, form):
        itinerary = get_object_or_404(Itinerary, pk=self.kwargs['itinerary_id'])
        
        # Get or create Member profile for logged in user
        from member.models import Member
        member, created = Member.objects.get_or_create(user=self.request.user)
        
        # Get or create Trip_Members for this member and trip
        trip = itinerary.trip_day.trip
        trip_member, tm_created = Trip_Members.objects.get_or_create(
            trip=trip,
            member=member,
            defaults={'status': 1}
        )
        
        form.instance.itinerary = itinerary
        form.instance.uploaded_by = trip_member
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse('itinerary_detail', kwargs={'pk': self.kwargs['itinerary_id']})


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comments
    form_class = CommentsForm
    
    def form_valid(self, form):
        itinerary = get_object_or_404(Itinerary, pk=self.kwargs['itinerary_id'])
        
        # Get or create Member profile for logged in user
        from member.models import Member
        member, created = Member.objects.get_or_create(user=self.request.user)
        
        # Get or create Trip_Members for this member and trip
        trip = itinerary.trip_day.trip
        trip_member, tm_created = Trip_Members.objects.get_or_create(
            trip=trip,
            member=member,
            defaults={'status': 1} # 1 is Joined
        )
        
        form.instance.itinerary = itinerary
        form.instance.message_by = trip_member
        return super().form_valid(form)
        
    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('itinerary_detail', kwargs={'pk': self.kwargs['itinerary_id']})

from django.views import View

class CommentLikeView(LoginRequiredMixin, View):
    def post(self, request, comment_id):
        comment = get_object_or_404(Comments, pk=comment_id)
        
        # Get or create Member profile for logged in user
        from member.models import Member
        member, created = Member.objects.get_or_create(user=request.user)
        
        # Get or create Trip_Members for this member and trip
        trip = comment.itinerary.trip_day.trip
        trip_member, tm_created = Trip_Members.objects.get_or_create(
            trip=trip,
            member=member,
            defaults={'status': 1}
        )
        
        # Check if reaction already exists
        reaction = Reaction.objects.filter(comment=comment, member=trip_member).first()
        if reaction:
            reaction.delete() # Toggle off
        else:
            Reaction.objects.create(comment=comment, member=trip_member, is_like=1)
            
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect(reverse('itinerary_detail', kwargs={'pk': comment.itinerary.pk}))

class ReplyCreateView(LoginRequiredMixin, CreateView):
    model = Reply
    fields = ['text']
    
    def form_valid(self, form):
        comment = get_object_or_404(Comments, pk=self.kwargs['comment_id'])
        
        # Get or create Member profile for logged in user
        from member.models import Member
        member, created = Member.objects.get_or_create(user=self.request.user)
        
        # Get or create Trip_Members for this member and trip
        trip = comment.itinerary.trip_day.trip
        trip_member, tm_created = Trip_Members.objects.get_or_create(
            trip=trip,
            member=member,
            defaults={'status': 1}
        )
        
        form.instance.comment = comment
        form.instance.reply_by = trip_member
        return super().form_valid(form)
        
    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        comment = get_object_or_404(Comments, pk=self.kwargs['comment_id'])
        return reverse('itinerary_detail', kwargs={'pk': comment.itinerary.pk})

class MyTripsView(LoginRequiredMixin, ListView):
    model = Trip
    template_name = 'trip/trip_list.html'
    context_object_name = 'trips'
    paginate_by = 10

    def get_queryset(self):
        from member.models import Member, Coordinator
        try:
            member = self.request.user.member
        except Member.DoesNotExist:
            member = None
            
        try:
            coordinator = self.request.user.coordinator
        except Coordinator.DoesNotExist:
            coordinator = None
            
        queryset = Trip.objects.filter( Q(trip_members__member=member) | Q(coordinator=coordinator)).distinct() 

        self.filter_form = TripFilterForm(self.request.GET)
        if self.filter_form.is_valid():
            title = self.filter_form.cleaned_data.get('title')
            location_from_name = self.filter_form.cleaned_data.get('location_from_name')
            location_to_name = self.filter_form.cleaned_data.get('location_to_name')
            from_date = self.filter_form.cleaned_data.get('from_date')
            to_date = self.filter_form.cleaned_data.get('to_date')
            status = self.filter_form.cleaned_data.get('status')
            
            if title:
                queryset = queryset.filter(title__icontains=title)
            if location_from_name:
                queryset = queryset.filter(location_from_name__icontains=location_from_name)
            if location_to_name:
                queryset = queryset.filter(location_to_name__icontains=location_to_name)
            if from_date:
                queryset = queryset.filter(Q(from_date=from_date) | Q(to_date=from_date))
            if to_date:
                queryset = queryset.filter(to_date__lte=to_date)
            if status:
                queryset = queryset.filter(status=status)
                
        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = getattr(self, 'filter_form', TripFilterForm(self.request.GET))
        
        # If coordinator, fetch notifications
        if hasattr(self.request.user, 'coordinator'):
            from member.models import CoordinatorNotification
            from django.db.models import Q
            context['coordinator_notifications'] = CoordinatorNotification.objects.filter(
                Q(coordinator=self.request.user.coordinator) | Q(send_to_all=True),
                is_read=False
            ).order_by('-created_at')
            
        return context

from django.contrib import messages
from django.views import View

class TripMemberApproveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        tm = get_object_or_404(Trip_Members, pk=pk)
        tm.status = 1  # 1 is Joined
        tm.save()
        messages.success(request, f"Successfully approved {tm.member.user.first_name}'s request to join.")
        return redirect(reverse('trip_detail', kwargs={'pk': tm.trip.pk}))

class TripFinishView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from django.utils import timezone
        trip = get_object_or_404(Trip, pk=pk)
        
        # Verify that the logged-in user is the coordinator of this trip
        if trip.coordinator.user != request.user and not request.user.is_superuser:
            messages.error(request, "You do not have permission to finish this trip.")
            return redirect(reverse('trip_detail', kwargs={'pk': trip.pk}))
            
        today = timezone.localdate()
        reason = request.POST.get('reason', '').strip()
        
        # If today is not the end date of the trip, reason is mandatory
        if today != trip.to_date:
            if not reason:
                messages.error(request, "The trip's end date is not met. A mandatory reason is required to finish the trip.")
                return redirect(reverse('trip_detail', kwargs={'pk': trip.pk}))
            
        trip.status = 2  # Set status to 2 (Finished)
        trip.finish_reason = reason
        trip.save()
        
        messages.success(request, f"Trip '{trip.title}' has been successfully finished!")
        return redirect(reverse('trip_detail', kwargs={'pk': trip.pk}))

class TripBroadcastCreateView(LoginRequiredMixin, View):
    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id)
        
        # Verify permissions: must be superuser, staff, or coordinator of this trip
        if not (request.user.is_superuser or request.user.is_staff or trip.coordinator.user == request.user):
            messages.error(request, "You do not have permission to send broadcast messages for this trip.")
            return redirect(reverse('trip_detail', kwargs={'pk': trip_id}))
            
        message_text = request.POST.get('message', '').strip()
        if not message_text:
            messages.error(request, "Broadcast message cannot be empty.")
            return redirect(reverse('trip_detail', kwargs={'pk': trip_id}))
            
        from .models import TripBroadcastMessage
        TripBroadcastMessage.objects.create(
            trip=trip,
            sender=request.user,
            message=message_text
        )
        messages.success(request, "Broadcast message sent to all trip members successfully!")
        return redirect(reverse('trip_detail', kwargs={'pk': trip_id}))
