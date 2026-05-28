from django.db import models
from django.contrib.auth.models import User
from trip.models import Trip

class EntertainmentPlaylist(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='playlists')
    playlist_name = models.CharField(max_length=255)
    thumbnail = models.ImageField(upload_to='playlists/thumbnails/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.playlist_name} (Trip: {self.trip.title})"

class EntertainmentMedia(models.Model):
    playlist = models.ForeignKey(EntertainmentPlaylist, on_delete=models.CASCADE, related_name='media_items')
    media_name = models.CharField(max_length=255)
    media_url = models.URLField()
    description = models.TextField(null=True, blank=True)
    media_type = models.CharField(max_length=50, default='video') # 'youtube', 'spotify', 'audio', 'video'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.media_name

    def save(self, *args, **kwargs):
        from .utils import detect_media_type
        self.media_type, _ = detect_media_type(self.media_url)
        super().save(*args, **kwargs)

    @property
    def embed_url(self):
        from .utils import detect_media_type
        _, embed = detect_media_type(self.media_url)
        return embed

    @property
    def resolved_media_type(self):
        from .utils import detect_media_type
        mtype, _ = detect_media_type(self.media_url)
        return mtype
