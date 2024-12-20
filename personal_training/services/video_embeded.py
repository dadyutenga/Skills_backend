from typing import Dict, Optional, Tuple, List
from urllib.parse import urlparse, parse_qs
import requests
from django.core.cache import cache
from django.conf import settings
from datetime import timedelta
import logging
import json

class VideoEmbededService:
    """Service for handling video embedding functionality"""
    
    YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"
    CACHE_TTL = 60 * 60 * 24  # 24 hours
    
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        self.logger = logging.getLogger(__name__)

    def embed_video(self, video_url: str, module_id: Optional[int] = None) -> Dict:
        """
        Process video URL and return embedding information
        
        Args:
            video_url: URL of the video
            module_id: Optional module ID for progress tracking
        """
        try:
            # Extract video source and ID
            video_source, video_id = self._parse_video_url(video_url)
            cache_key = f"video_data:{video_source}:{video_id}"
            
            # Try to get from cache first
            video_data = cache.get(cache_key)
            if not video_data:
                if video_source == 'youtube':
                    video_data = self._process_youtube_video(video_id)
                else:
                    raise ValueError(f"Unsupported video source: {video_source}")
                
                # Cache the video data
                cache.set(cache_key, video_data, self.CACHE_TTL)
            
            # Add module tracking if provided
            if module_id:
                video_data['tracking_info'] = self._initialize_video_tracking(video_id, module_id)
            
            return video_data
            
        except Exception as e:
            self.logger.error(f"Error embedding video: {str(e)}")
            raise

    def get_video_url(self, video_id: str, quality: str = 'high') -> str:
        """Get the appropriate video URL based on quality preference"""
        cache_key = f"video_url:{video_id}:{quality}"
        
        url = cache.get(cache_key)
        if not url:
            try:
                video_data = self._fetch_video_data(video_id)
                url = self._select_video_quality(video_data, quality)
                cache.set(cache_key, url, 3600)  # Cache for 1 hour
            except Exception as e:
                self.logger.error(f"Error getting video URL: {str(e)}")
                raise
        
        return url

    def validate_video_source(self, url: str) -> bool:
        """Validate if the video source is supported and accessible"""
        try:
            source, video_id = self._parse_video_url(url)
            if source == 'youtube':
                return self._validate_youtube_video(video_id)
            return False
        except Exception:
            return False

    def get_video_metadata(self, video_id: str) -> Dict:
        """Fetch comprehensive video metadata"""
        cache_key = f"video_metadata:{video_id}"
        
        metadata = cache.get(cache_key)
        if not metadata:
            try:
                response = requests.get(
                    f"{self.YOUTUBE_API_BASE_URL}/videos",
                    params={
                        'part': 'snippet,contentDetails,statistics',
                        'id': video_id,
                        'key': self.api_key
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if not data.get('items'):
                    raise ValueError(f"No video found with ID: {video_id}")
                
                video_data = data['items'][0]
                metadata = {
                    'title': video_data['snippet']['title'],
                    'description': video_data['snippet']['description'],
                    'thumbnail_url': video_data['snippet']['thumbnails']['high']['url'],
                    'duration': self._parse_duration(video_data['contentDetails']['duration']),
                    'view_count': video_data['statistics'].get('viewCount', 0),
                    'like_count': video_data['statistics'].get('likeCount', 0),
                    'published_at': video_data['snippet']['publishedAt']
                }
                
                cache.set(cache_key, metadata, self.CACHE_TTL)
            
            except Exception as e:
                self.logger.error(f"Error fetching video metadata: {str(e)}")
                raise
        
        return metadata

    def process_video_timestamps(self, video_id: str, module_id: int) -> Dict:
        """Process and store video viewing timestamps for progress tracking"""
        try:
            redis_key = f"video_progress:{module_id}:{video_id}"
            
            return {
                'video_id': video_id,
                'module_id': module_id,
                'progress_key': redis_key,
                'timestamp_endpoint': f"/api/v1/video/timestamp/{video_id}/",
                'progress_endpoint': f"/api/v1/video/progress/{video_id}/"
            }
        except Exception as e:
            self.logger.error(f"Error processing video timestamps: {str(e)}")
            raise

    def generate_video_preview(self, video_id: str, timestamp: int = 0) -> Dict:
        """Generate video preview data including thumbnail and preview clip"""
        try:
            metadata = self.get_video_metadata(video_id)
            
            preview_data = {
                'thumbnail_url': metadata['thumbnail_url'],
                'title': metadata['title'],
                'duration': metadata['duration'],
                'preview_start': timestamp,
                'preview_duration': min(30, metadata['duration']),  # 30-second preview or full video if shorter
                'preview_url': self._generate_preview_url(video_id, timestamp)
            }
            
            return preview_data
            
        except Exception as e:
            self.logger.error(f"Error generating video preview: {str(e)}")
            raise

    def _parse_video_url(self, url: str) -> Tuple[str, str]:
        """Parse video URL to determine source and video ID"""
        parsed_url = urlparse(url)
        
        # YouTube URL parsing
        if 'youtube.com' in parsed_url.netloc:
            query_params = parse_qs(parsed_url.query)
            video_id = query_params.get('v', [None])[0]
            return 'youtube', video_id
        elif 'youtu.be' in parsed_url.netloc:
            video_id = parsed_url.path.lstrip('/')
            return 'youtube', video_id
            
        raise ValueError("Unsupported video URL format")

    def _process_youtube_video(self, video_id: str) -> Dict:
        """Process YouTube video data"""
        metadata = self.get_video_metadata(video_id)
        
        return {
            'embed_url': f"https://www.youtube.com/embed/{video_id}",
            'thumbnail_url': metadata['thumbnail_url'],
            'title': metadata['title'],
            'duration': metadata['duration'],
            'source': 'youtube',
            'video_id': video_id,
            'metadata': metadata
        }

    def _initialize_video_tracking(self, video_id: str, module_id: int) -> Dict:
        """Initialize video tracking data"""
        tracking_key = f"video_tracking:{module_id}:{video_id}"
        
        tracking_data = {
            'start_time': None,
            'last_position': 0,
            'completed_segments': [],
            'total_watch_time': 0,
            'completion_status': 0
        }
        
        cache.set(tracking_key, tracking_data, timeout=None)  # No expiration
        
        return {
            'tracking_key': tracking_key,
            'tracking_enabled': True,
            'tracking_interval': 5,  # Send tracking data every 5 seconds
            'minimum_watch_threshold': 0.9  # 90% watch requirement for completion
        }

    def _parse_duration(self, duration_str: str) -> int:
        """Convert ISO 8601 duration to seconds"""
        try:
            # Remove 'PT' from start of duration
            duration_str = duration_str[2:]
            
            hours = minutes = seconds = 0
            
            # Parse hours, minutes, seconds
            if 'H' in duration_str:
                hours, duration_str = duration_str.split('H')
                hours = int(hours)
            if 'M' in duration_str:
                minutes, duration_str = duration_str.split('M')
                minutes = int(minutes)
            if 'S' in duration_str:
                seconds = int(duration_str.rstrip('S'))
            
            return (hours * 3600) + (minutes * 60) + seconds
            
        except Exception:
            return 0

    def _validate_youtube_video(self, video_id: str) -> bool:
        """Validate YouTube video existence and availability"""
        try:
            response = requests.get(
                f"{self.YOUTUBE_API_BASE_URL}/videos",
                params={
                    'part': 'status',
                    'id': video_id,
                    'key': self.api_key
                }
            )
            
            data = response.json()
            return bool(data.get('items'))
            
        except Exception:
            return False