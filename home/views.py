from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from trip.models import Trip, Trip_Details, Trip_Members, Trip_Day, CoTraveller, MemberType
from member.models import Member

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
    
    user_member_detail = None
    membership_status = None
    if request.user.is_authenticated:
        try:
            member = request.user.member
            tm = Trip_Members.objects.filter(trip=trip, member=member).first()
            if tm:
                user_member_detail = tm
                membership_status = tm.status
        except Member.DoesNotExist:
            pass
            
    is_coordinator = False
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff or (hasattr(request.user, 'coordinator') and trip.coordinator.user == request.user):
            is_coordinator = True
            
    is_joined_or_coordinator = (membership_status == 1) or is_coordinator
            
    # Fetch joined members and attach their co-travellers
    joined_members = trip_members.filter(status=1)
    for tm in joined_members:
        tm.co_travellers_list = CoTraveller.objects.filter(trip=trip, user=tm.member.user)
        
    joined_count = sum(m.group_size for m in joined_members)

    from django.db.models import Q
    from trip.models import TripBroadcastMessage
    if request.user.is_authenticated:
        try:
            member = request.user.member
            broadcast_messages = TripBroadcastMessage.objects.filter(trip=trip).filter(
                Q(recipient__isnull=True) | Q(recipient=member)
            ).order_by('-created_at')
        except Exception:
            broadcast_messages = TripBroadcastMessage.objects.filter(trip=trip, recipient__isnull=True).order_by('-created_at')
    else:
        broadcast_messages = TripBroadcastMessage.objects.filter(trip=trip, recipient__isnull=True).order_by('-created_at')
            
    context = {
        'trip': trip,
        'trip_details': trip_details,
        'trip_members': trip_members,
        'trip_days': trip_days,
        'membership_status': membership_status,
        'user_member_detail': user_member_detail,
        'broadcast_messages': broadcast_messages,
        'is_coordinator': is_coordinator,
        'is_joined_or_coordinator': is_joined_or_coordinator,
        'joined_members': joined_members,
        'joined_count': joined_count,
    }
    return render(request, 'home_trip_details.html', context)

@login_required
def join_trip(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    
    if trip.is_started:
        messages.error(request, "This trip has already commenced. Registration is closed.")
        return redirect('home_trip_details', pk=trip.id)
        
    member, created = Member.objects.get_or_create(user=request.user)
    trip_member = Trip_Members.objects.filter(trip=trip, member=member).first()
    
    if trip_member and trip_member.status in [0, 1]:
        if trip_member.status == 1:
            messages.info(request, "You are already a member of this trip!")
        else:
            messages.info(request, "Your request to join this trip is already pending approval.")
        return redirect('home_trip_details', pk=trip.id)
        
    try:
        trip_details = Trip_Details.objects.get(trip=trip)
    except Trip_Details.DoesNotExist:
        trip_details = None
        
    # Auto-seed standard MemberTypes if not populated
    if not MemberType.objects.exists():
        MemberType.objects.create(name="adult", description="Adult traveler")
        MemberType.objects.create(name="child", description="Child traveler")
        
    member_types = MemberType.objects.all()
    
    # Capacity calculations:
    total_occupied = sum(m.group_size for m in Trip_Members.objects.filter(trip=trip, status=1))
    
    max_members = trip_details.max_members if trip_details else 10
    remaining_slots = max(0, max_members - total_occupied)
    # The current user occupies 1 slot, so they can add up to (remaining_slots - 1) adult co-travellers
    max_co_travellers = max(0, remaining_slots - 1)
    
    context = {
        'trip': trip,
        'trip_details': trip_details,
        'member': member,
        'trip_member': trip_member,
        'member_types': member_types,
        'remaining_slots': remaining_slots,
        'max_co_travellers': max_co_travellers,
        'max_members': max_members,
    }
    
    if request.method == 'POST':
        if remaining_slots < 1:
            messages.error(request, "Sorry, this trip has already reached its maximum capacity of members.")
            return redirect('home_trip_details', pk=trip.id)
            
        co_names = request.POST.getlist('co_name[]')
        co_ages = request.POST.getlist('co_age[]')
        co_genders = request.POST.getlist('co_gender[]')
        co_bgroups = request.POST.getlist('co_bgroup[]')
        co_types = request.POST.getlist('co_type[]')
        co_descriptions = request.POST.getlist('co_description[]')
        
        # Validate adult co-traveller limit (Children do not count)
        adult_count = 0
        for i in range(len(co_names)):
            mtype = get_object_or_404(MemberType, pk=co_types[i])
            if mtype.name.lower() == 'adult':
                adult_count += 1
                
        if adult_count > max_co_travellers:
            messages.error(request, f"You can only add up to {max_co_travellers} adult co-travellers due to trip capacity.")
            return render(request, 'join_trip.html', context)
            
        if not trip_member:
            trip_member = Trip_Members(trip=trip, member=member)
        
        trip_member.status = 0  # 0 means Pending (Requested to Join)
        
        # Optionally update profile info directly from the form
        phone = request.POST.get('phone')
        bgroup = request.POST.get('bgroup')
        emergency_name = request.POST.get('emergency_name')
        emergency_contact = request.POST.get('emergency_contact')
        notes = request.POST.get('description', '')
        
        if phone: member.phone = phone
        if bgroup: member.bgroup = bgroup
        if emergency_name: member.emergency_name = emergency_name
        if emergency_contact: member.emergency_contact = emergency_contact
        member.save()
        
        trip_member.description = notes
        trip_member.save()
        
        # Save each CoTraveller
        for i in range(len(co_names)):
            mtype = get_object_or_404(MemberType, pk=co_types[i])
            CoTraveller.objects.create(
                trip=trip,
                user=request.user,
                member_type=mtype,
                name=co_names[i],
                age=int(co_ages[i]) if co_ages[i] else None,
                gender=co_genders[i],
                bgroup=co_bgroups[i],
                description=co_descriptions[i]
            )

        # Recalculate unpaid_amount with the newly added co-travellers
        try:
            per_head_cost = trip.trip_details.per_head_cost
        except Exception:
            per_head_cost = 0.0
        trip_member.unpaid_amount = per_head_cost * trip_member.group_size
        trip_member.save()

        messages.success(request, f"Your request to join the '{trip.title}' adventure with {len(co_names)} co-traveller(s) has been successfully submitted and is pending coordinator approval!")
        return redirect('home_trip_details', pk=trip.id)
        
    return render(request, 'join_trip.html', context)
