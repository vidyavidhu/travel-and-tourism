from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from trip.models import Trip, Trip_Members
from .models import EntertainmentPlaylist, EntertainmentMedia

@login_required
def add_playlist(request, trip_id):
    if request.method != 'POST':
        return redirect('home')
    
    trip = get_object_or_404(Trip, pk=trip_id)
    is_member = Trip_Members.objects.filter(trip=trip, member__user=request.user, status=1).exists()
    is_coordinator = (trip.coordinator.user == request.user or request.user.is_superuser or request.user.is_staff)
    
    if not (is_member or is_coordinator):
        messages.error(request, "You do not have permission to add playlists to this trip.")
        return redirect('trip_detail', pk=trip.id)
    
    playlist_name = request.POST.get('playlist_name')
    if not playlist_name:
        messages.error(request, "Playlist name is required.")
        return redirect(request.META.get('HTTP_REFERER') or reverse('trip_detail', kwargs={'pk': trip.id}))
        
    thumbnail = request.FILES.get('thumbnail')
    
    playlist = EntertainmentPlaylist.objects.create(
        trip=trip,
        playlist_name=playlist_name,
        thumbnail=thumbnail,
        created_by=request.user
    )
    
    messages.success(request, f"Playlist '{playlist.playlist_name}' created successfully!")
    
    referer = request.META.get('HTTP_REFERER') or ''
    if 'home_trip_details' in referer or '/home/' in referer:
        return redirect(reverse('home_trip_details', kwargs={'pk': trip.id}) + "?tab=entertainment")
    return redirect(reverse('trip_detail', kwargs={'pk': trip.id}) + "?tab=entertainment")

@login_required
def delete_playlist(request, playlist_id):
    if request.method != 'POST':
        return redirect('home')
        
    playlist = get_object_or_404(EntertainmentPlaylist, pk=playlist_id)
    trip = playlist.trip
    
    is_coordinator = (trip.coordinator.user == request.user or request.user.is_superuser or request.user.is_staff)
    is_creator = (playlist.created_by == request.user)
    
    if not (is_coordinator or is_creator):
        messages.error(request, "You do not have permission to delete this playlist.")
        return redirect('trip_detail', pk=trip.id)
        
    playlist_name = playlist.playlist_name
    playlist.delete()
    messages.success(request, f"Playlist '{playlist_name}' has been deleted.")
    
    referer = request.META.get('HTTP_REFERER') or ''
    if 'home_trip_details' in referer or '/home/' in referer:
        return redirect(reverse('home_trip_details', kwargs={'pk': trip.id}) + "?tab=entertainment")
    return redirect(reverse('trip_detail', kwargs={'pk': trip.id}) + "?tab=entertainment")

@login_required
def add_media(request, playlist_id):
    if request.method != 'POST':
        return redirect('home')
        
    playlist = get_object_or_404(EntertainmentPlaylist, pk=playlist_id)
    trip = playlist.trip
    
    is_member = Trip_Members.objects.filter(trip=trip, member__user=request.user, status=1).exists()
    is_coordinator = (trip.coordinator.user == request.user or request.user.is_superuser or request.user.is_staff)
    
    if not (is_member or is_coordinator):
        messages.error(request, "You do not have permission to modify this playlist.")
        return redirect('trip_detail', pk=trip.id)
        
    media_name = request.POST.get('media_name')
    media_url = request.POST.get('media_url')
    description = request.POST.get('description', '')
    
    if not media_name or not media_url:
        messages.error(request, "Media Name and URL are required.")
        return redirect(request.META.get('HTTP_REFERER') or reverse('trip_detail', kwargs={'pk': trip.id}))
        
    media = EntertainmentMedia.objects.create(
        playlist=playlist,
        media_name=media_name,
        media_url=media_url,
        description=description
    )
    
    messages.success(request, f"Added '{media.media_name}' to playlist '{playlist.playlist_name}'!")
    
    referer = request.META.get('HTTP_REFERER') or ''
    if 'home_trip_details' in referer or '/home/' in referer:
        return redirect(reverse('home_trip_details', kwargs={'pk': trip.id}) + f"?tab=entertainment&playlist={playlist.id}")
    return redirect(reverse('trip_detail', kwargs={'pk': trip.id}) + f"?tab=entertainment&playlist={playlist.id}")

@login_required
def delete_media(request, media_id):
    if request.method != 'POST':
        return redirect('home')
        
    media = get_object_or_404(EntertainmentMedia, pk=media_id)
    playlist = media.playlist
    trip = playlist.trip
    
    is_coordinator = (trip.coordinator.user == request.user or request.user.is_superuser or request.user.is_staff)
    is_creator = (playlist.created_by == request.user)
    
    if not (is_coordinator or is_creator):
        messages.error(request, "You do not have permission to delete items from this playlist.")
        return redirect('trip_detail', pk=trip.id)
        
    media_name = media.media_name
    media.delete()
    messages.success(request, f"Removed '{media_name}' from the playlist.")
    
    referer = request.META.get('HTTP_REFERER') or ''
    if 'home_trip_details' in referer or '/home/' in referer:
        return redirect(reverse('home_trip_details', kwargs={'pk': trip.id}) + f"?tab=entertainment&playlist={playlist.id}")
    return redirect(reverse('trip_detail', kwargs={'pk': trip.id}) + f"?tab=entertainment&playlist={playlist.id}")
