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
            approved = False
            if(is_coordinator=="True" and request.user.is_superuser==True):
               approved=True
            else:  
                approved=False
            coordinator=Coordinator.objects.create(user=user, is_approved=approved)
            coordinator.save()

            if(request.user.is_superuser==True):
                return redirect('/home')
            else:
                return redirect('/member/login')
        else:
            return render(request, 'member/signup.html',{'messages': messages.get_messages(request)})
    else:
        return render(request, 'member/signup.html')
  
from django.contrib.auth import authenticate, login

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not hasattr(user, 'member'):
                return redirect('member_profile_edit')
            return redirect('/home')
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'member/login.html', {'messages': messages.get_messages(request)})
            
    return render(request, 'member/login.html')

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/home')

from django.contrib.auth.decorators import login_required

@login_required
def profile_view(request):
    member = getattr(request.user, 'member', None)
    has_coordinator = hasattr(request.user, 'coordinator')
    return render(request, 'member/profile_view.html', {
        'member': member,
        'has_coordinator': has_coordinator
    })

@login_required
def profile_edit_view(request):
    member = getattr(request.user, 'member', None)
    has_coordinator = hasattr(request.user, 'coordinator')
    
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
            
        if has_coordinator and 'authorised_pdf' in request.FILES:
            request.user.coordinator.authorised_pdf = request.FILES['authorised_pdf']
            request.user.coordinator.save()
        
        if hasattr(request.user, 'coordinator') and request.user.coordinator.is_approved == True:
            member.is_coordinator=True
            
        member.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('member_profile')
        
    return render(request, 'member/profile_edit.html', {
        'member': member,
        'has_coordinator': has_coordinator
    })
