from member.models import CoordinatorNotification
from django.db.models import Q

def coordinator_notifications(request):
    unread_admin_notifs = []
    unread_trip_broadcasts = []
    total_count = 0
    
    if request.user.is_authenticated:
        # 1. Fetch Admin alerts for Coordinators
        try:
            if hasattr(request.user, 'coordinator'):
                coordinator = request.user.coordinator
                unread_admin_notifs = CoordinatorNotification.objects.filter(
                    Q(coordinator=coordinator, is_read=False) | Q(send_to_all=True)
                ).exclude(read_by=coordinator).distinct().order_by('-created_at')
                total_count += unread_admin_notifs.count()
        except Exception:
            pass
            
        # 2. Fetch Coordinator announcements for Trip Members
        try:
            if hasattr(request.user, 'member'):
                member = request.user.member
                from trip.models import Trip_Members, TripBroadcastMessage
                joined_trips = Trip_Members.objects.filter(member=member, status=1).values_list('trip_id', flat=True)
                unread_trip_broadcasts = TripBroadcastMessage.objects.filter(
                    trip_id__in=joined_trips
                ).exclude(read_by=member).distinct().order_by('-created_at')
                total_count += unread_trip_broadcasts.count()
        except Exception:
            pass
            
    return {
        'unread_coordinator_notifications': unread_admin_notifs,
        'unread_trip_broadcasts': unread_trip_broadcasts,
        'unread_notifications_count': total_count
    }
