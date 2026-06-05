from member.models import Member,Coordinator
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator

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
        
        context = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'username': username,
            'is_coordinator': is_coordinator,
        }
        
        is_valid = True
        if(password != confirm_password):
            messages.error(request, "Passwords do not match")
            is_valid = False
        
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            is_valid = False
        elif password.isdigit():
            messages.error(request, "Password cannot be entirely numeric.")
            is_valid = False
        elif not any(char.isalpha() for char in password):
            messages.error(request, "Password must contain at least one letter.")
            is_valid = False
        
        if(User.objects.filter(email=email).exists()):
            messages.error(request, "Email already exists")
            is_valid = False
            context['email'] = ''
            
        if(User.objects.filter(username=username).exists()):
            messages.error(request, "Username already exists")
            is_valid = False
            context['username'] = ''
            
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
            return render(request, 'member/signup.html', context)
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

    # Prefill form data from database on GET
    form_data = {
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'dob': member.dob.strftime('%Y-%m-%d') if (member and member.dob) else '',
        'gender': member.gender if member else '',
        'phone': member.phone if member else '',
        'bgroup': member.bgroup if member else '',
        'address': member.address if member else '',
        'emergency_name': member.emergency_name if member else '',
        'emergency_contact': member.emergency_contact if member else '',
        'description': member.description if member else '',
    }

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        dob = request.POST.get('dob')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender')
        bgroup = request.POST.get('bgroup')
        emergency_contact = request.POST.get('emergency_contact')
        emergency_name = request.POST.get('emergency_name')
        description = request.POST.get('description')

        # Update form_data with submitted values
        form_data = {
            'first_name': first_name,
            'last_name': last_name,
            'dob': dob,
            'gender': gender,
            'phone': phone,
            'bgroup': bgroup,
            'address': address,
            'emergency_name': emergency_name,
            'emergency_contact': emergency_contact,
            'description': description,
        }

        is_valid = True
        
        # Phone validation: must be unique and 10 digits
        if phone:
            import re
            if not re.match(r'^\d{10}$', phone):
                messages.error(request, "Phone number must be exactly 10 digits.")
                is_valid = False
                form_data['phone'] = ''
            elif Member.objects.filter(phone=phone).exclude(user=request.user).exists():
                messages.error(request, "Phone number is already in use by another member.")
                is_valid = False
                form_data['phone'] = ''

        if is_valid:
            # Update User data
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()

            if not member:
                member = Member(user=request.user)

            if coordinator:
                member.is_coordinator = True
                if 'authorised_pdf' in request.FILES:
                    coordinator.authorised_pdf = request.FILES['authorised_pdf']
                coordinator.save()
            else:
                member.is_coordinator = False
                
            if dob: 
                member.dob = dob
            else:
                member.dob = None
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
        else:
            return render(request, 'member/profile_edit.html', {'next': next_url, 'form_data': form_data})

    return render(request, 'member/profile_edit.html', {'next': next_url, 'form_data': form_data})


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


# --- Password Reset Function Views ---

def password_reset_view(request):
    from django.contrib.auth.forms import PasswordResetForm
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                subject_template_name='member/password_reset_subject.txt',
                email_template_name='member/password_reset_email.txt',
                html_email_template_name='member/password_reset_email.html',
                from_email=None
            )
            return redirect('password_reset_done')
    else:
        form = PasswordResetForm()
    return render(request, 'member/password_reset_form.html', {'form': form})


def password_reset_done_view(request):
    return render(request, 'member/password_reset_done.html')


def password_reset_confirm_view(request, uidb64, token):
   
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        validlink = True
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                return redirect('password_reset_complete')
        else:
            form = SetPasswordForm(user)
    else:
        validlink = False
        form = None

    return render(request, 'member/password_reset_confirm.html', {
        'form': form,
        'validlink': validlink,
    })


def password_reset_complete_view(request):
    return render(request, 'member/password_reset_complete.html')


