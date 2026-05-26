from member.models import Member,Coordinator
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
# Create your views here.

def signup_view(request):
    # Backend logic to save data would go here
    if(request.method == 'POST'):
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        is_coordinator = request.POST.get('is_coordinator')
        print(first_name, last_name, email, username, password, confirm_password, is_coordinator)
        is_valid = True
        if(password != confirm_password):
            messages.error(request, "Passwords do not match")
            is_valid = False
        elif(User.objects.filter(email=email).exists()):
            messages.error(request, "Email already exists")
            is_valid = False
        elif(User.objects.filter(username=username).exists()):
            messages.error(request, "Username already exists")
            is_valid = False
        if(is_valid):
            #create user
            user = User.objects.create_user(first_name = first_name,last_name=last_name,username=username, email=email, password=password)
            user.save()
            #create member
           
            if(is_coordinator == "True"):
                approved = False
                if(request.user.is_superuser == True):
                    approved = True
                coordinator = Coordinator.objects.create(user = user, is_approved = approved)
                coordinator.save()

            if(request.user.is_superuser == True):
                return redirect('/home')
            else:
                return redirect('/member/login')
        else:
            return render(request, 'member/signup.html')
    else:
        return render(request, 'member/signup.html')
  
from django.contrib.auth import authenticate, login

def login_view(request):
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not hasattr(user, 'member'):
                if next_url:
                    return redirect(f"/member/profile/edit/?next={next_url}")
                return redirect('member_profile_edit')
            else:
                if next_url:
                    return redirect(next_url)
                return redirect('/home')
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'member/login.html', {'next': next_url})
            
    return render(request, 'member/login.html', {'next': next_url})

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/home')

from django.contrib.auth.decorators import login_required

@login_required
def profile_view(request):
    member = getattr(request.user, 'member', None)
    print("member profile_view ",member)
    if not member:
        return redirect('/member/profile/edit')
    else:
        return render(request, 'member/profile_view.html')
@login_required        
def update_profile_image(request):
    member = getattr(request.user, 'member', None)
    print("member update_profile_image ",member)
    if request.method == 'POST':
        if 'image' in request.FILES:
            member.image = request.FILES['image']
        member.save()
        return redirect('/member/profile')

@login_required
def profile_edit_view(request):
    member = getattr(request.user, 'member', None)
    coordinator = getattr(request.user, 'coordinator', None)
    print("member profile_edit_view ",member)
    print("coordinator profile_edit_view ",coordinator)
    next_url = request.POST.get('next') or request.GET.get('next') or ''

    if request.method == 'POST':
        # Update User data
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.save()

        # Update or Create Member data
        dob = request.POST.get('dob')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender')
        bgroup = request.POST.get('bgroup')
        emergency_contact = request.POST.get('emergency_contact')
        emergency_name = request.POST.get('emergency_name')
        description = request.POST.get('description')
        
        if not member:
            member = Member(user=request.user)
            # Sync coordinator status if they signed up as one
        if coordinator:
            member.is_coordinator = True
            if 'authorised_pdf' in request.FILES:
                coordinator.authorised_pdf = request.FILES['authorised_pdf']
            coordinator.save()
            print("coordinator",coordinator)
        else:
            member.is_coordinator = False
            
        if dob: member.dob = dob
        member.address = address
        member.phone = phone
        member.gender = gender
        member.bgroup = bgroup
        member.emergency_contact = emergency_contact
        member.emergency_name = emergency_name
        member.description = description
       
        if 'image' in request.FILES:
            member.image = request.FILES['image']
       
      
        
        member.save()
        print("member2",member)
        
        messages.success(request, "Profile updated successfully.")
        if next_url:
            return redirect(next_url)
        return redirect('/member/profile')
        
    return render(request, 'member/profile_edit.html', {'next': next_url})


# --- Admin Dashboard & Coordinator Management Views ---
from django.shortcuts import get_object_or_404
from collections import defaultdict
from trip.models import Trip
from member.models import Coordinator, CoordinatorNotification

def admin_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Access denied. Administrator privileges required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@admin_required
def admin_dashboard_view(request):
    trips = Trip.objects.all().order_by('from_date')
    monthly_trips = defaultdict(list)
    for trip in trips:
        month_name = trip.from_date.strftime("%B %Y")
        monthly_trips[month_name].append(trip)
        
    total_trips = trips.count()
    total_coordinators = Coordinator.objects.count()
    pending_coordinators = Coordinator.objects.filter(is_approved=False).count()
    
    context = {
        'monthly_trips': dict(monthly_trips),
        'total_trips': total_trips,
        'total_coordinators': total_coordinators,
        'pending_coordinators': pending_coordinators,
    }
    return render(request, 'member/admin_dashboard.html', context)

@admin_required
def admin_coordinators_list_view(request):
    coordinators = Coordinator.objects.all().order_by('-id')
    return render(request, 'member/admin_coordinators_list.html', {'coordinators': coordinators})

@admin_required
def admin_coordinator_detail_view(request, pk):
    coordinator = get_object_or_404(Coordinator, pk=pk)
    trips = Trip.objects.filter(coordinator=coordinator).order_by('-from_date')
    notifications = CoordinatorNotification.objects.filter(coordinator=coordinator).order_by('-created_at')
    
    context = {
        'coordinator': coordinator,
        'trips': trips,
        'notifications': notifications,
    }
    return render(request, 'member/admin_coordinator_detail.html', context)

@admin_required
def admin_coordinator_toggle_approve_view(request, pk):
    if request.method == 'POST':
        coordinator = get_object_or_404(Coordinator, pk=pk)
        coordinator.is_approved = not coordinator.is_approved
        coordinator.save()
        status_str = "approved" if coordinator.is_approved else "disapproved"
        messages.success(request, f"Coordinator '{coordinator.user.username}' has been successfully {status_str}.")
        return redirect('admin_coordinator_detail', pk=pk)
    return redirect('admin_coordinators_list')

@admin_required
def admin_coordinator_notify_view(request):
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        coordinator_id = request.POST.get('coordinator_id')
        
        if not message:
            messages.error(request, "Notification message cannot be empty.")
            return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))
            
        if coordinator_id and coordinator_id != 'all':
            coordinator = get_object_or_404(Coordinator, pk=coordinator_id)
            CoordinatorNotification.objects.create(
                coordinator=coordinator,
                message=message,
                send_to_all=False
            )
            messages.success(request, f"Notification successfully sent to coordinator {coordinator.user.username}.")
            return redirect('admin_coordinator_detail', pk=coordinator.pk)
        else:
            CoordinatorNotification.objects.create(
                message=message,
                send_to_all=True
            )
            messages.success(request, "Broadcast notification successfully sent to all coordinators.")
            return redirect('admin_dashboard')
            
    return redirect('admin_dashboard')

@login_required
def mark_notification_read_view(request, pk):
    if request.method == 'POST':
        notification = get_object_or_404(CoordinatorNotification, pk=pk)
        
        # Verify the user has access to mark it as read
        is_owner = False
        try:
            if hasattr(request.user, 'coordinator') and notification.coordinator == request.user.coordinator:
                is_owner = True
        except Exception:
            pass
            
        if notification.send_to_all:
            if hasattr(request.user, 'coordinator'):
                notification.read_by.add(request.user.coordinator)
                messages.success(request, "Notification marked as read.")
            else:
                messages.error(request, "Access denied.")
        elif is_owner:
            notification.is_read = True
            notification.save()
            messages.success(request, "Notification marked as read.")
        else:
            messages.error(request, "Access denied.")
            
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def mark_trip_broadcast_read_view(request, pk):
    if request.method == 'POST':
        from trip.models import TripBroadcastMessage, Trip_Members
        notification = get_object_or_404(TripBroadcastMessage, pk=pk)
        
        try:
            member = request.user.member
            is_joined = Trip_Members.objects.filter(trip=notification.trip, member=member, status=1).exists()
            if is_joined:
                notification.read_by.add(member)
                messages.success(request, "Announcement marked as read.")
            else:
                messages.error(request, "Access denied.")
        except Exception:
            messages.error(request, "Profile not found.")
            
    return redirect(request.META.get('HTTP_REFERER', '/'))

