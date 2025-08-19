#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plex Path Resolver: Advanced path resolution system for multiple library locations
Replaces path_mappings by dynamically resolving paths through Plex API
"""

import logging
import os
from typing import List, Dict, Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)


class PlexPathResolver:
    """
    Advanced path resolution system that handles multiple library locations
    Eliminates the need for static path mappings by using Plex API dynamically
    """
    
    def __init__(self):
        self.plex_server = None
        self._library_cache = {}
        
    def get_plex_server(self):
        """Get authenticated Plex server connection"""
        if self.plex_server is None:
            try:
                from bazarr.plex.operations import get_plex_server
                self.plex_server = get_plex_server()
            except Exception as e:
                logger.error(f"Failed to connect to Plex server: {e}")
                return None
        return self.plex_server
    
    @lru_cache(maxsize=128)
    def get_library_locations(self, library_type: str) -> List[str]:
        """
        Get all library locations for a specific media type
        
        Args:
            library_type: 'movie' or 'show'
            
        Returns:
            List of all paths where this media type might be located
        """
        try:
            server = self.get_plex_server()
            if not server:
                return []
                
            locations = []
            
            # Map Bazarr types to Plex types
            plex_type = 'movie' if library_type == 'movie' else 'show'
            
            for library in server.library.sections():
                if library.type == plex_type:
                    # Each library can have multiple locations
                    for location in library.locations:
                        locations.append(location)
                        
            logger.debug(f"Found {len(locations)} {library_type} library locations: {locations}")
            return locations
            
        except Exception as e:
            logger.error(f"Failed to get library locations for {library_type}: {e}")
            return []
    
    def resolve_media_path(self, media_item_key: str, media_type: str) -> Optional[str]:
        """
        Resolve the actual file path for a specific media item using Plex API
        
        Args:
            media_item_key: Plex media item key/ID
            media_type: 'movie' or 'episode'
            
        Returns:
            Actual accessible file path or None if not found
        """
        try:
            server = self.get_plex_server()
            if not server:
                return None
                
            # Get the media item from Plex
            media_item = server.fetchItem(media_item_key)
            
            # Get the first media part (file)
            if hasattr(media_item, 'media') and media_item.media:
                for media in media_item.media:
                    if hasattr(media, 'parts') and media.parts:
                        file_path = media.parts[0].file
                        
                        # Verify file is accessible
                        if self.is_path_accessible(file_path):
                            return file_path
                            
            return None
            
        except Exception as e:
            logger.error(f"Failed to resolve path for {media_item_key}: {e}")
            return None
    
    def find_media_in_libraries(self, original_path: str, media_type: str) -> Optional[str]:
        """
        Find media file across all library locations by matching filename/relative path
        
        Args:
            original_path: Original path from Sonarr/Radarr
            media_type: 'movie' or 'episode'
            
        Returns:
            Actual accessible path or None if not found
        """
        try:
            # Extract filename and relative structure
            filename = os.path.basename(original_path)
            
            # Get all possible library locations
            library_type = 'movie' if media_type in ['movie'] else 'show'
            locations = self.get_library_locations(library_type)
            
            # Try to find the file in each library location
            for location in locations:
                # Try direct filename match first
                potential_path = os.path.join(location, filename)
                if self.is_path_accessible(potential_path):
                    logger.debug(f"Found media at: {potential_path}")
                    return potential_path
                
                # Try to match directory structure
                # Extract relative path from original
                relative_path = self._extract_relative_path(original_path)
                if relative_path:
                    potential_path = os.path.join(location, relative_path)
                    if self.is_path_accessible(potential_path):
                        logger.debug(f"Found media with relative path at: {potential_path}")
                        return potential_path
            
            logger.warning(f"Could not find media file {filename} in any library location")
            return None
            
        except Exception as e:
            logger.error(f"Failed to find media in libraries: {e}")
            return None
    
    def _extract_relative_path(self, original_path: str) -> Optional[str]:
        """
        Extract the relative path portion that might be common across libraries
        
        For example:
        /old/mount/Movies/Action/Movie.mkv -> Movies/Action/Movie.mkv
        """
        try:
            # Common root folder names to look for
            common_roots = ['Movies', 'TV Shows', 'Series', 'Films', 'Television']
            
            path_parts = original_path.split('/')
            for i, part in enumerate(path_parts):
                if part in common_roots:
                    # Return everything from this point onwards
                    return '/'.join(path_parts[i:])
            
            # If no common root found, return None
            return None
            
        except Exception:
            return None
    
    def is_path_accessible(self, file_path: str) -> bool:
        """
        Check if a file path is accessible to Bazarr
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file exists and is accessible
        """
        try:
            return os.path.exists(file_path) and os.access(file_path, os.R_OK)
        except Exception:
            return False
    
    def get_subtitle_location(self, video_path: str, language_code: str, 
                             subtitle_type: str = 'srt') -> str:
        """
        Determine where subtitle should be stored relative to video file
        
        Args:
            video_path: Path to video file
            language_code: Language code for subtitle
            subtitle_type: Subtitle format (srt, vtt, etc.)
            
        Returns:
            Path where subtitle should be stored
        """
        try:
            from app.config import settings
            video_dir = os.path.dirname(video_path)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            
            # Check if we should use subdirectory for subtitles
            if settings.general.subfolder:
                if settings.general.subfolder == "relative":
                    subtitle_dir = os.path.join(video_dir, "Subs")
                elif settings.general.subfolder == "absolute":
                    subtitle_dir = settings.general.subfolder_custom or os.path.join(video_dir, "Subs")
                else:
                    subtitle_dir = video_dir
            else:
                subtitle_dir = video_dir
            
            # Create subtitle filename
            subtitle_filename = f"{video_name}.{language_code}.{subtitle_type}"
            
            return os.path.join(subtitle_dir, subtitle_filename)
            
        except Exception as e:
            logger.error(f"Failed to determine subtitle location: {e}")
            # Fallback to same directory as video
            video_dir = os.path.dirname(video_path)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            return os.path.join(video_dir, f"{video_name}.{language_code}.{subtitle_type}")
    
    def clear_cache(self):
        """Clear all cached data"""
        self._library_cache.clear()
        self.get_library_locations.cache_clear()
        
        
# Global instance
plex_path_resolver = PlexPathResolver()


# Legacy compatibility functions for path_mappings replacement
def path_replace(original_path: str) -> str:
    """
    Replace path_mappings.path_replace() with Plex-based resolution
    
    Args:
        original_path: Original path from database
        
    Returns:
        Resolved accessible path
    """
    try:
        # Try to resolve using Plex API
        resolved_path = plex_path_resolver.find_media_in_libraries(
            original_path, 
            'episode' if 'episode' in original_path.lower() else 'movie'
        )
        
        if resolved_path:
            return resolved_path
        else:
            logger.warning(f"Could not resolve path via Plex API, returning original: {original_path}")
            return original_path
            
    except Exception as e:
        logger.error(f"Path resolution failed for {original_path}: {e}")
        return original_path


def path_replace_reverse(processed_path: str) -> str:
    """
    Legacy compatibility: No reverse mapping needed with Plex API
    """
    return processed_path


def path_replace_movie(original_path: str) -> str:
    """
    Replace path_mappings.path_replace_movie() with Plex-based resolution
    """
    return path_replace(original_path)


def path_replace_reverse_movie(processed_path: str) -> str:
    """
    Legacy compatibility: No reverse mapping needed with Plex API
    """
    return processed_path
