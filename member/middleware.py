from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages

class BlockedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                member_profile = request.user.member
                if member_profile.access_denied:
                    logout(request)
                    messages.error(request, "Your account has been blocked by the admin.")
                    return redirect('/member/login/')
            except Exception:
                pass
        return self.get_response(request)
