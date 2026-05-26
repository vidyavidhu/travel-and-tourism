from member.models import CoordinatorNotification
from django.db.models import Q

def coordinator_notifications(request):
    if request.user.is_authenticated:
        try:
            if hasattr(request.user, 'coordinator'):
                coordinator = request.user.coordinator
                # Unread notifications:
                # - Direct notifications where coordinator = coordinator and is_read = False
                # - Broadcast notifications where send_to_all = True and they are NOT in read_by many-to-many relation
                unread = CoordinatorNotification.objects.filter(
                    Q(coordinator=coordinator, is_read=False) | Q(send_to_all=True)
                ).exclude(read_by=coordinator).distinct().order_by('-created_at')
                
                return {
                    'unread_coordinator_notifications': unread,
                    'unread_notifications_count': unread.count()
                }
        except Exception:
            pass
            
    return {
        'unread_coordinator_notifications': [],
        'unread_notifications_count': 0
    }
