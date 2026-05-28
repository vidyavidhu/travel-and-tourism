import re
from urllib.parse import urlparse, parse_qs

def detect_media_type(url):
    """
    Auto-detects the media type from the given URL and generates the appropriate embed URL.
    Returns: (media_type, embed_url)
    Where media_type can be 'youtube', 'spotify', 'audio', or 'video'.
    """
    if not url:
        return 'video', ''

    url = url.strip()

    # 1. YouTube detection (Robust parsing using urllib.parse)
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path
        
        # Check for youtube.com or youtu.be domains
        if 'youtube.com' in domain or 'youtu.be' in domain:
            video_id = None
            
            if 'youtu.be' in domain:
                # e.g., https://youtu.be/dQw4w9WgXcQ?si=...
                path_parts = path.strip('/').split('/')
                if path_parts:
                    video_id = path_parts[0]
            elif 'embed' in path:
                # e.g., https://www.youtube.com/embed/dQw4w9WgXcQ
                path_parts = path.strip('/').split('/')
                if len(path_parts) >= 2:
                    video_id = path_parts[1]
            elif 'shorts' in path:
                # e.g., https://www.youtube.com/shorts/dQw4w9WgXcQ
                path_parts = path.strip('/').split('/')
                if len(path_parts) >= 2:
                    video_id = path_parts[1]
            else:
                # e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ or https://m.youtube.com/watch?feature=shared&v=dQw4w9WgXcQ
                query = parse_qs(parsed.query)
                v_list = query.get('v')
                if v_list:
                    video_id = v_list[0]
            
            # Clean up the video ID if it has extra pathing/parameters
            if video_id:
                # Extract first 11 characters typical of YouTube video IDs
                video_id = video_id[:11]
                return 'youtube', f"https://www.youtube.com/embed/{video_id}"
    except Exception as e:
        # Fallback to regex or direct check in case of malformed URLs
        pass

    # 2. Spotify detection
    # Regex covers tracks, playlists, albums, and artists
    spotify_pattern = r'(?:https?://)?open\.spotify\.com/(track|playlist|album|artist)/([a-zA-Z0-9]+)'
    sp_match = re.search(spotify_pattern, url, re.IGNORECASE)
    if sp_match:
        media_kind = sp_match.group(1)
        spotify_id = sp_match.group(2)
        return 'spotify', f"https://open.spotify.com/embed/{media_kind}/{spotify_id}"

    # 3. Direct Audio files
    audio_extensions = ['.mp3', '.ogg', '.wav', '.aac', '.m4a', '.mpga', '.opus']
    if any(url.lower().endswith(ext) or f"{ext}?" in url.lower() for ext in audio_extensions):
        return 'audio', url

    # 4. Direct Video files
    video_extensions = ['.mp4', '.webm', '.ogv', '.mov', '.mkv']
    if any(url.lower().endswith(ext) or f"{ext}?" in url.lower() for ext in video_extensions):
        return 'video', url

    # Fallback to video player/general URL
    return 'video', url
