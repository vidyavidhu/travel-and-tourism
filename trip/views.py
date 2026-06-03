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

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        trip = self.object
        
        if not request.user.is_authenticated:
            return redirect('member_login')
            
        is_coordinator = False
        if request.user.is_superuser or request.user.is_staff or trip.coordinator.user == request.user:
            is_coordinator = True
            
        if not is_coordinator:
            return redirect('home_trip_details', pk=trip.pk)
            
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

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
        trip_members = Trip_Members.objects.filter(trip=trip)
        context['trip_members'] = trip_members
        context['pending_members'] = trip_members.filter(status=0)
        context['joined_members'] = trip_members.filter(status=1)
        context['cancelled_members'] = trip_members.filter(status=2)
        
        # Calculate joined members count and left count
        joined_count = 0
        left_count = 0
        if context['trip_details']:
            joined_count = sum(m.group_size for m in context['joined_members'])
            left_count = max(0, context['trip_details'].max_members - joined_count)
        context['joined_count'] = joined_count
        context['left_count'] = left_count
        
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
        
        # Total expenses = sum of active expenses (NORMAL_EXPENSE or APPROVED MEMBER_REIMBURSEMENT)
        expenses = Expenses.objects.filter(trip=trip).order_by('-id')
        total_expenses = expenses.filter(
            Q(expense_type='NORMAL_EXPENSE') | Q(expense_type='MEMBER_REIMBURSEMENT', approval_status='APPROVED')
        ).aggregate(Sum('amount'))['amount__sum'] or 0.0
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
        
        # Fetch trip playlists for Entertainment
        from entertainment.models import EntertainmentPlaylist
        context['playlists'] = EntertainmentPlaylist.objects.filter(trip=trip).prefetch_related('media_items').order_by('created_at')
        
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
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse('trip_detail', kwargs={'pk': self.kwargs['trip_id']}) + '?tab=details'
        return context
        
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.kwargs['trip_id']}) + '?tab=details'

class TripDetailsUpdateView(UpdateView):
    model = Trip_Details
    form_class = TripDetailsForm
    template_name = 'trip/trip_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse('trip_detail', kwargs={'pk': self.object.trip.pk}) + '?tab=details'
        return context
        
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.object.trip.pk}) + '?tab=details'

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
        context['cancel_url'] = reverse('trip_detail', kwargs={'pk': self.kwargs['trip_id']}) + '?tab=members'
        try:
            trip_details = Trip_Details.objects.get(trip=trip)
            context['per_head_cost'] = trip_details.per_head_cost
        except Trip_Details.DoesNotExist:
            context['per_head_cost'] = None
        return context
    
    def form_valid(self, form):
        trip = get_object_or_404(Trip, pk=self.kwargs['trip_id'])
        form.instance.trip = trip
        
        # Check capacity
        try:
            trip_details = Trip_Details.objects.get(trip=trip)
            max_members = trip_details.max_members
        except Trip_Details.DoesNotExist:
            max_members = 0
            
        if max_members > 0:
            joined_members = Trip_Members.objects.filter(trip=trip, status=1)
            joined_count = sum(m.group_size for m in joined_members)
            new_group_size = form.instance.group_size
            if (joined_count + new_group_size) > max_members:
                form.add_error(None, f"Cannot add member. This action would exceed the maximum capacity of {max_members} members (currently joined: {joined_count}, new member group size: {new_group_size}).")
                return self.form_invalid(form)
                
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.kwargs['trip_id']}) + '?tab=members'

class TripMembersUpdateView(UpdateView):
    model = Trip_Members
    form_class = TripMembersForm
    template_name = 'trip/trip_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = "Update Trip Member Details"
        context['cancel_url'] = reverse('trip_detail', kwargs={'pk': self.object.trip.pk}) + '?tab=members'
        
        # Inject co-travellers for the member of this trip
        from .models import CoTraveller
        context['co_travellers'] = CoTraveller.objects.filter(
            trip=self.object.trip,
            user=self.object.member.user
        )
        return context
        
    def form_valid(self, form):
        trip = self.object.trip
        
        # Check capacity
        try:
            trip_details = Trip_Details.objects.get(trip=trip)
            max_members = trip_details.max_members
        except Trip_Details.DoesNotExist:
            max_members = 0
            
        if max_members > 0 and form.instance.status == 1:
            joined_members = Trip_Members.objects.filter(trip=trip, status=1).exclude(pk=self.object.pk)
            joined_count = sum(m.group_size for m in joined_members)
            new_group_size = form.instance.group_size
            if (joined_count + new_group_size) > max_members:
                form.add_error(None, f"Cannot update member. This action would exceed the maximum capacity of {max_members} members (other joined: {joined_count}, updated group size: {new_group_size}).")
                return self.form_invalid(form)
                
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.object.trip.pk}) + '?tab=members'

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
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        day = get_object_or_404(Trip_Day, pk=self.kwargs['day_id'])
        context['cancel_url'] = reverse('trip_detail', kwargs={'pk': day.trip.pk}) + '?tab=itinerary'
        return context
        
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.object.trip_day.trip.pk}) + '?tab=itinerary'

class TripCreateView(LoginRequiredMixin, CreateView):
    model = Trip
    form_class = TripForm
    template_name = 'trip/trip_form.html'
    success_url = reverse_lazy('trip_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if hasattr(self.request.user, 'coordinator') and not self.request.user.is_superuser:
            form.instance.coordinator = self.request.user.coordinator
        return super().form_valid(form)

class TripUpdateView(LoginRequiredMixin, UpdateView):
    model = Trip
    form_class = TripForm
    template_name = 'trip/trip_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse('trip_detail', kwargs={'pk': self.object.pk})
        return context
        
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.object.pk})

class TripDeleteView(LoginRequiredMixin, DeleteView):
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
        trip = itinerary.trip_day.trip
        
        # Get or create Member profile for logged in user
        from member.models import Member
        member, created = Member.objects.get_or_create(user=self.request.user)
        
        # Check permissions: must be coordinator or joined member (status == 1)
        is_coordinator = self.request.user.is_superuser or self.request.user.is_staff or (hasattr(trip, 'coordinator') and trip.coordinator.user == self.request.user)
        trip_member = Trip_Members.objects.filter(trip=trip, member=member).first()
        is_joined = trip_member and trip_member.status == 1
        
        if not (is_coordinator or is_joined):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You must be a joined member of this trip to upload gallery items.")
            
        # Ensure a Trip_Members record exists (especially for coordinator)
        if not trip_member:
            trip_member = Trip_Members.objects.create(trip=trip, member=member, status=1)
        
        form.instance.itinerary = itinerary
        form.instance.uploaded_by = trip_member
        return super().form_valid(form)
        
    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('itinerary_detail', kwargs={'pk': self.kwargs['itinerary_id']})


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comments
    form_class = CommentsForm
    
    def form_valid(self, form):
        itinerary = get_object_or_404(Itinerary, pk=self.kwargs['itinerary_id'])
        trip = itinerary.trip_day.trip
        
        # Get or create Member profile for logged in user
        from member.models import Member
        member, created = Member.objects.get_or_create(user=self.request.user)
        
        # Check permissions
        is_coordinator = self.request.user.is_superuser or self.request.user.is_staff or (hasattr(trip, 'coordinator') and trip.coordinator.user == self.request.user)
        trip_member = Trip_Members.objects.filter(trip=trip, member=member).first()
        is_joined = trip_member and trip_member.status == 1
        
        if not (is_coordinator or is_joined):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You must be a joined member of this trip to post comments.")
            
        # Ensure a Trip_Members record exists (especially for coordinator)
        if not trip_member:
            trip_member = Trip_Members.objects.create(trip=trip, member=member, status=1)
        
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
        trip = comment.itinerary.trip_day.trip
        
        # Get or create Member profile for logged in user
        from member.models import Member
        member, created = Member.objects.get_or_create(user=request.user)
        
        # Check permissions
        is_coordinator = request.user.is_superuser or request.user.is_staff or (hasattr(trip, 'coordinator') and trip.coordinator.user == request.user)
        trip_member = Trip_Members.objects.filter(trip=trip, member=member).first()
        is_joined = trip_member and trip_member.status == 1
        
        if not (is_coordinator or is_joined):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You must be a joined member of this trip to react to comments.")
            
        # Ensure a Trip_Members record exists (especially for coordinator)
        if not trip_member:
            trip_member = Trip_Members.objects.create(trip=trip, member=member, status=1)
        
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
        trip = comment.itinerary.trip_day.trip
        
        # Get or create Member profile for logged in user
        from member.models import Member
        member, created = Member.objects.get_or_create(user=self.request.user)
        
        # Check permissions
        is_coordinator = self.request.user.is_superuser or self.request.user.is_staff or (hasattr(trip, 'coordinator') and trip.coordinator.user == self.request.user)
        trip_member = Trip_Members.objects.filter(trip=trip, member=member).first()
        is_joined = trip_member and trip_member.status == 1
        
        if not (is_coordinator or is_joined):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You must be a joined member of this trip to reply to comments.")
            
        # Ensure a Trip_Members record exists (especially for coordinator)
        if not trip_member:
            trip_member = Trip_Members.objects.create(trip=trip, member=member, status=1)
        
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
        
        # Check capacity
        trip = tm.trip
        try:
            trip_details = Trip_Details.objects.get(trip=trip)
            max_members = trip_details.max_members
        except Trip_Details.DoesNotExist:
            max_members = 0
            
        if max_members > 0:
            joined_members = Trip_Members.objects.filter(trip=trip, status=1)
            joined_count = sum(m.group_size for m in joined_members)
            if (joined_count + tm.group_size) > max_members:
                messages.error(request, f"Cannot approve request. This action would exceed the maximum capacity of {max_members} members (currently joined: {joined_count}, requesting size: {tm.group_size}).")
                return redirect(reverse('trip_detail', kwargs={'pk': trip.pk}))
                
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

class ItineraryCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from .models import Itinerary
        itinerary = get_object_or_404(Itinerary, pk=pk)
        trip = itinerary.trip_day.trip
        
        # Verify permissions: must be superuser, staff, or coordinator of this trip
        if not (request.user.is_superuser or request.user.is_staff or trip.coordinator.user == request.user):
            messages.error(request, "You do not have permission to cancel stops for this trip.")
            return redirect(reverse('itinerary_detail', kwargs={'pk': pk}))
            
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, "Cancellation reason is mandatory.")
            return redirect(reverse('itinerary_detail', kwargs={'pk': pk}))
            
        itinerary.is_cancelled = True
        itinerary.cancellation_reason = reason
        itinerary.save()
        
        messages.success(request, f"Stop '{itinerary.title}' has been successfully cancelled.")
        return redirect(reverse('itinerary_detail', kwargs={'pk': pk}))

class ItineraryDismissCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from .models import Itinerary
        itinerary = get_object_or_404(Itinerary, pk=pk)
        trip = itinerary.trip_day.trip
        
        # Verify permissions: must be superuser, staff, or coordinator of this trip
        if not (request.user.is_superuser or request.user.is_staff or trip.coordinator.user == request.user):
            messages.error(request, "You do not have permission to modify stops for this trip.")
            return redirect(reverse('itinerary_detail', kwargs={'pk': pk}))
            
        itinerary.is_cancelled = False
        itinerary.cancellation_reason = ""
        itinerary.save()
        
        messages.success(request, f"Cancellation for stop '{itinerary.title}' has been dismissed and the stop is now active.")
        return redirect(reverse('itinerary_detail', kwargs={'pk': pk}))


from django.contrib.auth.decorators import login_required
from payment.models import Payment
from .models import CoTraveller, TripBroadcastMessage

@login_required
def trip_member_detail(request, tm_id):
    """
    Coordinator-only detail view for a specific member registered to a trip.
    Shows profile details, group travellers, detailed payments log, and direct messages.
    """
    tm = get_object_or_404(Trip_Members, pk=tm_id)
    trip = tm.trip
    
    # Permission check: must be admin or the trip coordinator
    is_coordinator = request.user.is_superuser or request.user.is_staff
    if not is_coordinator and hasattr(request.user, 'coordinator'):
        # Check if the user is the coordinator of this trip
        if trip.coordinator and trip.coordinator.user == request.user:
            is_coordinator = True
            
    if not is_coordinator:
        messages.error(request, "Access denied. Only the trip coordinator or administrators can view member details.")
        return redirect('home')

    member = tm.member
    # Fetch co-travellers registered for this user and trip
    co_travellers = CoTraveller.objects.filter(trip=trip, user=member.user)
    # Fetch payment transactions related to this booking
    payments = Payment.objects.filter(booking=tm).order_by('-created_at')
    
    # Process Direct Message Submission
    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        if message_text:
            TripBroadcastMessage.objects.create(
                trip=trip,
                sender=request.user,
                recipient=member,
                message=message_text
            )
            messages.success(request, f"Secure message successfully sent to {member.user.first_name + ' ' + member.user.last_name}!")
            return redirect('trip_member_detail', tm_id=tm.id)
        else:
            messages.error(request, "Message content cannot be blank.")
            
    # Fetch past messages sent specifically to this member for this trip
    direct_messages = TripBroadcastMessage.objects.filter(trip=trip, recipient=member).order_by('-created_at')

    context = {
        'tm': tm,
        'trip': trip,
        'member': member,
        'co_travellers': co_travellers,
        'payments': payments,
        'direct_messages': direct_messages,
    }
    return render(request, 'trip/trip_member_detail.html', context)


from django.utils import timezone
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from django.http import HttpResponse

@login_required
def export_finance_excel(request, pk):
    """
    Exports the trip financial data into an Excel spreadsheet containing multiple sheets:
    1. Financial Overview
    2. Revenue Ledger (Collections & Pending from members)
    3. Cost Details (All expenses added)
    """
    trip = get_object_or_404(Trip, pk=pk)
    
    # Permission verification
    is_coordinator = request.user.is_superuser or request.user.is_staff
    if not is_coordinator and hasattr(request.user, 'coordinator'):
        if trip.coordinator and trip.coordinator.user == request.user:
            is_coordinator = True
            
    if not is_coordinator:
        messages.error(request, "Access denied. Only trip coordinators or admins can export financial data.")
        return redirect('home')

    # Fetch context variables
    try:
        trip_details = trip.trip_details
        estimated_cost = trip_details.estimated_cost
    except Exception:
        trip_details = None
        estimated_cost = 0.0

    from finance.models import Expenses
    from django.db.models import Sum
    
    trip_members = Trip_Members.objects.filter(trip=trip)
    actual_collection = trip_members.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0.0
    expenses_qs = Expenses.objects.filter(trip=trip).order_by('-id')
    total_expenses = expenses_qs.aggregate(Sum('amount'))['amount__sum'] or 0.0
    pending_money = actual_collection - total_expenses
    outstanding_unpaid = trip_members.aggregate(Sum('unpaid_amount'))['unpaid_amount__sum'] or 0.0
    total_expected = estimated_cost  # Base expected collection
    
    # Initialize Workbook
    wb = openpyxl.Workbook()
    
    # Sheet 1: Financial Overview
    ws_overview = wb.active
    ws_overview.title = "Financial Overview"
    ws_overview.views.sheetView[0].showGridLines = True
    
    # Styles
    title_font = Font(name="Calibri", size=16, bold=True, color="ffffff")
    title_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # Elegant Slate
    header_font = Font(name="Calibri", size=11, bold=True, color="ffffff")
    header_fill = PatternFill(start_color="475569", end_color="475569", fill_type="solid") # Dark Gray Accent
    sub_header_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    sub_header_font = Font(name="Calibri", size=11, bold=True, color="1E293B")
    
    border_thin = Side(style='thin', color='CBD5E1')
    border_double = Side(style='double', color='1E293B')
    box_border = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)
    total_border = Border(top=border_thin, bottom=border_double)
    
    # Title Block
    ws_overview.merge_cells('A1:C1')
    ws_overview['A1'] = f"TRIP WEAVER - FINANCIAL OVERVIEW"
    ws_overview['A1'].font = title_font
    ws_overview['A1'].fill = title_fill
    ws_overview['A1'].alignment = Alignment(horizontal="center", vertical="center")
    ws_overview.row_dimensions[1].height = 40
    
    # Metadata
    ws_overview['A3'] = "Trip Title:"
    ws_overview['B3'] = trip.title
    ws_overview['A4'] = "Coordinator:"
    ws_overview['B4'] = trip.coordinator.user.first_name + ' ' + trip.coordinator.user.last_name if trip.coordinator else "N/A"
    ws_overview['A5'] = "Export Date:"
    ws_overview['B5'] = timezone.now().strftime("%Y-%m-%d %H:%M")
    
    for row in range(3, 6):
        ws_overview[f'A{row}'].font = Font(bold=True)
        ws_overview[f'B{row}'].alignment = Alignment(horizontal="left")
        
    # Overview Table Headers
    ws_overview['A7'] = "Financial Indicator"
    ws_overview['B7'] = "Amount (INR)"
    ws_overview['C7'] = "Status / Reference"
    for col in ['A', 'B', 'C']:
        ws_overview[f'{col}7'].font = header_font
        ws_overview[f'{col}7'].fill = header_fill
        ws_overview[f'{col}7'].alignment = Alignment(horizontal="left" if col=='A' else "right" if col=='B' else "center")
    
    # Overview Data Rows
    metrics = [
        ("Base Expected Collection", total_expected, "Estimated booking revenue"),
        ("Actual Collections Received", actual_collection, "Transferred to Trip Ledger"),
        ("Total Expenses Incurred", total_expenses, "Invoices paid"),
        ("Net Pending from Members", outstanding_unpaid, "Outstanding payments"),
        ("Liquid Ledger Balance", pending_money, "Actual Collections - Total Expenses")
    ]
    
    current_row = 8
    for metric, val, ref in metrics:
        ws_overview.cell(row=current_row, column=1, value=metric).font = Font(bold=True if metric == "Liquid Ledger Balance" else False)
        cell_val = ws_overview.cell(row=current_row, column=2, value=val)
        cell_val.number_format = '$#,##0.00'
        if metric == "Liquid Ledger Balance":
            cell_val.font = Font(bold=True, color="28A745" if val>=0 else "DC3545")
        ws_overview.cell(row=current_row, column=3, value=ref).font = Font(italic=True, size=9)
        
        for col in [1, 2, 3]:
            ws_overview.cell(row=current_row, column=col).border = box_border
        current_row += 1
        
    ws_overview.column_dimensions['A'].width = 30
    ws_overview.column_dimensions['B'].width = 18
    ws_overview.column_dimensions['C'].width = 30
    
    # Sheet 2: Revenue Ledger
    ws_rev = wb.create_sheet(title="Revenue Ledger")
    ws_rev.views.sheetView[0].showGridLines = True
    
    # Headers
    ws_rev.merge_cells('A1:F1')
    ws_rev['A1'] = "REVENUE LEDGER (MEMBER COLLECTIONS)"
    ws_rev['A1'].font = title_font
    ws_rev['A1'].fill = title_fill
    ws_rev['A1'].alignment = Alignment(horizontal="center", vertical="center")
    ws_rev.row_dimensions[1].height = 35
    
    headers_rev = ["Member Name", "Booking Status", "Group Size", "Payment Status", "Paid Amount (INR)", "Pending Balance (INR)"]
    for idx, header in enumerate(headers_rev, 1):
        cell = ws_rev.cell(row=3, column=idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center" if idx in [2,3,4] else "left" if idx==1 else "right")
        
    row_idx = 4
    for tm in trip_members:
        status_text = "Joined" if tm.status==1 else "Pending" if tm.status==0 else "Cancelled"
        pay_text = "Paid" if tm.payment_status==1 else "Unpaid"
        ws_rev.cell(row=row_idx, column=1, value=tm.member.user.first_name + ' ' + tm.member.user.last_name)
        ws_rev.cell(row=row_idx, column=2, value=status_text).alignment = Alignment(horizontal="center")
        ws_rev.cell(row=row_idx, column=3, value=tm.group_size).alignment = Alignment(horizontal="center")
        ws_rev.cell(row=row_idx, column=4, value=pay_text).alignment = Alignment(horizontal="center")
        
        c_paid = ws_rev.cell(row=row_idx, column=5, value=tm.paid_amount)
        c_paid.number_format = '$#,##0.00'
        c_paid.alignment = Alignment(horizontal="right")
        
        c_unpaid = ws_rev.cell(row=row_idx, column=6, value=tm.unpaid_amount)
        c_unpaid.number_format = '$#,##0.00'
        c_unpaid.alignment = Alignment(horizontal="right")
        
        for col in range(1, 7):
            ws_rev.cell(row=row_idx, column=col).border = box_border
        row_idx += 1
        
    # Total row for Revenue
    ws_rev.cell(row=row_idx, column=1, value="TOTALS").font = Font(bold=True)
    ws_rev.cell(row=row_idx, column=3, value=f"=SUM(C4:C{row_idx-1})").font = Font(bold=True)
    ws_rev.cell(row=row_idx, column=3).alignment = Alignment(horizontal="center")
    
    t_paid = ws_rev.cell(row=row_idx, column=5, value=f"=SUM(E4:E{row_idx-1})")
    t_paid.font = Font(bold=True)
    t_paid.number_format = '$#,##0.00'
    t_paid.alignment = Alignment(horizontal="right")
    
    t_unpaid = ws_rev.cell(row=row_idx, column=6, value=f"=SUM(F4:F{row_idx-1})")
    t_unpaid.font = Font(bold=True)
    t_unpaid.number_format = '$#,##0.00'
    t_unpaid.alignment = Alignment(horizontal="right")
    
    for col in range(1, 7):
        ws_rev.cell(row=row_idx, column=col).border = total_border
        ws_rev.cell(row=row_idx, column=col).fill = sub_header_fill
        
    # Adjust widths
    for col in ws_rev.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_rev.column_dimensions[col_letter].width = max(max_len + 4, 15)
        
    # Sheet 3: Cost Ledger
    ws_cost = wb.create_sheet(title="Cost Details")
    ws_cost.views.sheetView[0].showGridLines = True
    
    # Headers
    ws_cost.merge_cells('A1:C1')
    ws_cost['A1'] = "COST LEDGER (TRIP EXPENSES)"
    ws_cost['A1'].font = title_font
    ws_cost['A1'].fill = title_fill
    ws_cost['A1'].alignment = Alignment(horizontal="center", vertical="center")
    ws_cost.row_dimensions[1].height = 35
    
    headers_cost = ["Expense Category", "Description", "Amount (INR)"]
    for idx, header in enumerate(headers_cost, 1):
        cell = ws_cost.cell(row=3, column=idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="left" if idx in [1,2] else "right")
        
    cost_row = 4
    for exp in expenses_qs:
        ws_cost.cell(row=cost_row, column=1, value=exp.expense_category.name)
        ws_cost.cell(row=cost_row, column=2, value=exp.description or "N/A")
        
        c_amt = ws_cost.cell(row=cost_row, column=3, value=exp.amount)
        c_amt.number_format = '$#,##0.00'
        c_amt.alignment = Alignment(horizontal="right")
        
        for col in range(1, 4):
            ws_cost.cell(row=cost_row, column=col).border = box_border
        cost_row += 1
        
    # Total row for Costs
    ws_cost.cell(row=cost_row, column=1, value="TOTAL EXPENSES").font = Font(bold=True)
    
    t_cost = ws_cost.cell(row=cost_row, column=3, value=f"=SUM(C4:C{cost_row-1})")
    t_cost.font = Font(bold=True, color="DC3545")
    t_cost.number_format = '$#,##0.00'
    t_cost.alignment = Alignment(horizontal="right")
    
    for col in range(1, 4):
        ws_cost.cell(row=cost_row, column=col).border = total_border
        ws_cost.cell(row=cost_row, column=col).fill = sub_header_fill
        
    # Adjust widths
    for col in ws_cost.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_cost.column_dimensions[col_letter].width = max(max_len + 4, 18)
        
    # Prepare Download Response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Trip_{trip.id}_Finance_Report.xlsx'
    wb.save(response)
    return response

@login_required
def export_finance_pdf(request, pk):
    """
    Renders a print-ready HTML page of the trip's finance metrics, revenue lists,
    and costs ledger. The page auto-triggers the print dialog.
    """
    trip = get_object_or_404(Trip, pk=pk)
    
    # Permission verification
    is_coordinator = request.user.is_superuser or request.user.is_staff
    if not is_coordinator and hasattr(request.user, 'coordinator'):
        if trip.coordinator and trip.coordinator.user == request.user:
            is_coordinator = True
            
    if not is_coordinator:
        messages.error(request, "Access denied. Only trip coordinators or admins can view finance reports.")
        return redirect('home')

    try:
        trip_details = trip.trip_details
        estimated_cost = trip_details.estimated_cost
    except Exception:
        trip_details = None
        estimated_cost = 0.0

    from finance.models import Expenses
    from django.db.models import Sum
    
    trip_members = Trip_Members.objects.filter(trip=trip)
    actual_collection = trip_members.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0.0
    expenses = Expenses.objects.filter(trip=trip).order_by('-id')
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0.0
    pending_money = actual_collection - total_expenses
    outstanding_unpaid = trip_members.aggregate(Sum('unpaid_amount'))['unpaid_amount__sum'] or 0.0
    
    context = {
        'trip': trip,
        'trip_details': trip_details,
        'trip_members': trip_members,
        'estimated_cost': estimated_cost,
        'actual_collection': actual_collection,
        'expenses': expenses,
        'total_expenses': total_expenses,
        'pending_money': pending_money,
        'outstanding_unpaid': outstanding_unpaid,
    }
    return render(request, 'trip/finance_report_pdf.html', context)


