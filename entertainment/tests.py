from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from trip.models import Trip, TripCategory, Trip_Details, Trip_Members
from member.models import Member, Coordinator
from entertainment.models import EntertainmentPlaylist, EntertainmentMedia
from entertainment.utils import detect_media_type

class EntertainmentTabTestCase(TestCase):
    def setUp(self):
        # 1. Create Users
        self.coordinator_user = User.objects.create_user(
            username='coordinator',
            email='coordinator@test.com',
            password='password123',
            first_name='Coordinator',
            last_name='User'
        )
        self.member_user = User.objects.create_user(
            username='member',
            email='member@test.com',
            password='password123',
            first_name='Member',
            last_name='User'
        )
        self.non_member_user = User.objects.create_user(
            username='nonmember',
            email='nonmember@test.com',
            password='password123',
            first_name='Non',
            last_name='Member'
        )

        # 2. Create Profiles
        self.coord_profile = Coordinator.objects.create(
            user=self.coordinator_user,
            is_authorised=True,
            is_approved=True
        )
        self.member_profile = Member.objects.create(
            user=self.member_user,
            phone='9876543210'
        )
        self.non_member_profile = Member.objects.create(
            user=self.non_member_user,
            phone='1234567890'
        )

        # 3. Create Trip Setup
        self.category = TripCategory.objects.create(name='Adventure')
        self.trip = Trip.objects.create(
            title='Himalayan Trek',
            category=self.category,
            location_from_name='Delhi',
            location_to_name='Manali',
            distance=550.0,
            from_date=timezone.localdate() + timedelta(days=10),
            from_time=timezone.now().time(),
            to_date=timezone.localdate() + timedelta(days=15),
            to_time=timezone.now().time(),
            duration='5 Days',
            coordinator=self.coord_profile
        )

        # 4. Set Membership status
        # Member is joined and approved (status=1)
        self.tm_member = Trip_Members.objects.create(
            trip=self.trip,
            member=self.member_profile,
            status=1,
            group_size=1
        )
        # Non-member is pending (status=0)
        self.tm_non_member = Trip_Members.objects.create(
            trip=self.trip,
            member=self.non_member_profile,
            status=0,
            group_size=1
        )

        # Setup Clients
        self.coord_client = Client()
        self.coord_client.login(username='coordinator', password='password123')

        self.member_client = Client()
        self.member_client.login(username='member', password='password123')

        self.non_member_client = Client()
        self.non_member_client.login(username='nonmember', password='password123')

        self.anon_client = Client()

    def test_url_detection(self):
        # 1. YouTube link detection
        yt_urls = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube", "https://www.youtube.com/embed/dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "youtube", "https://www.youtube.com/embed/dQw4w9WgXcQ"),
            ("https://www.youtube.com/embed/dQw4w9WgXcQ", "youtube", "https://www.youtube.com/embed/dQw4w9WgXcQ"),
            ("https://youtube.com/shorts/dQw4w9WgXcQ", "youtube", "https://www.youtube.com/embed/dQw4w9WgXcQ")
        ]
        for url, expected_type, expected_embed in yt_urls:
            mtype, embed = detect_media_type(url)
            self.assertEqual(mtype, expected_type)
            self.assertEqual(embed, expected_embed)

        # 2. Spotify link detection
        spotify_urls = [
            ("https://open.spotify.com/track/4PTG3Z6ehGkBFmzIuvhkui", "spotify", "https://open.spotify.com/embed/track/4PTG3Z6ehGkBFmzIuvhkui"),
            ("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGo7BMJm", "spotify", "https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGo7BMJm"),
            ("https://open.spotify.com/album/4aawyABYnZwqViiRb7G77Y", "spotify", "https://open.spotify.com/embed/album/4aawyABYnZwqViiRb7G77Y")
        ]
        for url, expected_type, expected_embed in spotify_urls:
            mtype, embed = detect_media_type(url)
            self.assertEqual(mtype, expected_type)
            self.assertEqual(embed, expected_embed)

        # 3. Audio/Video direct files
        self.assertEqual(detect_media_type("https://example.com/song.mp3")[0], "audio")
        self.assertEqual(detect_media_type("https://example.com/video.mp4")[0], "video")

    def test_playlist_creation_and_authorization(self):
        add_url = reverse('add_playlist', kwargs={'trip_id': self.trip.id})

        # 1. Anonymous user blocked
        response = self.anon_client.post(add_url, {'playlist_name': 'Anon Vibes'})
        self.assertEqual(response.status_code, 302) # Redirects to login
        self.assertFalse(EntertainmentPlaylist.objects.filter(playlist_name='Anon Vibes').exists())

        # 2. Non-member (pending status=0) blocked
        response = self.non_member_client.post(add_url, {'playlist_name': 'Pending Vibes'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(EntertainmentPlaylist.objects.filter(playlist_name='Pending Vibes').exists())

        # 3. Joined member (status=1) allowed
        response = self.member_client.post(add_url, {'playlist_name': 'Member Vibes'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(EntertainmentPlaylist.objects.filter(playlist_name='Member Vibes').exists())
        playlist = EntertainmentPlaylist.objects.get(playlist_name='Member Vibes')
        self.assertEqual(playlist.created_by, self.member_user)

        # 4. Coordinator allowed
        response = self.coord_client.post(add_url, {'playlist_name': 'Coord Vibes'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(EntertainmentPlaylist.objects.filter(playlist_name='Coord Vibes').exists())

    def test_media_addition_and_detection(self):
        # Setup active playlist
        playlist = EntertainmentPlaylist.objects.create(
            trip=self.trip,
            playlist_name='Hype Tunes',
            created_by=self.coordinator_user
        )

        add_media_url = reverse('add_media', kwargs={'playlist_id': playlist.id})

        # 1. Block unauthorized additions
        response = self.non_member_client.post(add_media_url, {
            'media_name': 'Invalid',
            'media_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(playlist.media_items.count(), 0)

        # 2. Allow active member addition and auto-detect type
        response = self.member_client.post(add_media_url, {
            'media_name': 'Never Gonna Give You Up',
            'media_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'description': 'Classic anthem'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(playlist.media_items.count(), 1)
        media = playlist.media_items.first()
        self.assertEqual(media.media_name, 'Never Gonna Give You Up')
        self.assertEqual(media.media_type, 'youtube')
        self.assertEqual(media.embed_url, 'https://www.youtube.com/embed/dQw4w9WgXcQ')
        self.assertEqual(media.description, 'Classic anthem')

    def test_deletions_and_cascades(self):
        playlist = EntertainmentPlaylist.objects.create(
            trip=self.trip,
            playlist_name='Party Mix',
            created_by=self.member_user
        )
        media = EntertainmentMedia.objects.create(
            playlist=playlist,
            media_name='Direct MP3',
            media_url='https://example.com/file.mp3'
        )

        delete_media_url = reverse('delete_media', kwargs={'media_id': media.id})
        delete_playlist_url = reverse('delete_playlist', kwargs={'playlist_id': playlist.id})

        # 1. Non-member cannot delete media
        response = self.non_member_client.post(delete_media_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(EntertainmentMedia.objects.filter(id=media.id).exists())

        # 2. Playlist owner can delete media
        response = self.member_client.post(delete_media_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(EntertainmentMedia.objects.filter(id=media.id).exists())

        # Re-create media
        media = EntertainmentMedia.objects.create(
            playlist=playlist,
            media_name='Direct MP3',
            media_url='https://example.com/file.mp3'
        )

        # 3. Non-owner / Non-coordinator cannot delete playlist
        non_owner_user = User.objects.create_user(username='other_member', password='password123')
        other_profile = Member.objects.create(user=non_owner_user, phone='1212121212')
        Trip_Members.objects.create(trip=self.trip, member=other_profile, status=1, group_size=1)
        
        other_client = Client()
        other_client.login(username='other_member', password='password123')
        response = other_client.post(delete_playlist_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(EntertainmentPlaylist.objects.filter(id=playlist.id).exists())

        # 4. Deleting playlist deletes media item cascade
        response = self.member_client.post(delete_playlist_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(EntertainmentPlaylist.objects.filter(id=playlist.id).exists())
        self.assertFalse(EntertainmentMedia.objects.filter(id=media.id).exists())
