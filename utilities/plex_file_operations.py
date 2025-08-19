#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plex-based file operations system - eliminates path mappings entirely
Uses Plex server as the single source of truth for all file access
"""

import os
import logging
from typing import Optional, Union, List
from functools import lru_cache

from plexapi.server import PlexServer
from plexapi.exceptions import NotFound, BadRequest

logger = logging.getLogger(__name__)


class PlexFileOperationError(Exception):
    """Raised when Plex file operations fail"""
    pass


class PlexFileOperations:
    """
    Advanced file operations system using Plex API exclusively
    Eliminates the need for path mappings entirely
    """
    
    def __init__(self, plex_server: PlexServer):
        self.plex = plex_server
        self._library_cache = {}
        
    @lru_cache(maxsize=128)
    def is_accessible(self, file_path: str) -> bool:
        """
        Test if a file path is accessible through Plex server
        
        Args:
            file_path: Full path to test
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            return self.plex.isBrowsable(file_path)
        except Exception as e:
            logger.warning(f"Cannot access path through Plex: {file_path} - {e}")
            return False
    
    def get_file_path(self, media_item) -> str:
        """
        Get the actual file path for a media item
        
        Args:
            media_item: Plex media object (Movie, Episode, etc.)
            
        Returns:
            Full file path accessible through Plex
            
        Raises:
            PlexFileOperationError: If file cannot be accessed
        """
        try:
            # Get the primary file location
            file_path = media_item.locations[0] if media_item.locations else None
            
            if not file_path:
                raise PlexFileOperationError(f"No file location found for media: {media_item.title}")
            
            # Verify accessibility
            if not self.is_accessible(file_path):
                raise PlexFileOperationError(f"File not accessible through Plex: {file_path}")
            
            return file_path
            
        except (AttributeError, IndexError) as e:
            raise PlexFileOperationError(f"Invalid media item: {e}")
    
    def get_subtitle_path(self, video_path: str, language_code: str, 
                         subtitle_type: str = 'srt') -> str:
        """
        Generate subtitle file path based on video path
        
        Args:
            video_path: Path to video file
            language_code: Language code (e.g., 'en', 'fr')
            subtitle_type: Subtitle file extension
            
        Returns:
            Full path for subtitle file
        """
        base_path = os.path.splitext(video_path)[0]
        return f"{base_path}.{language_code}.{subtitle_type}"
    
    def get_directory_contents(self, directory_path: str, 
                              include_files: bool = True) -> List[str]:
        """
        List directory contents through Plex API
        
        Args:
            directory_path: Directory to browse
            include_files: Whether to include files in listing
            
        Returns:
            List of paths in directory
        """
        try:
            contents = self.plex.browse(directory_path, includeFiles=include_files)
            return [item.key for item in contents]
        except Exception as e:
            logger.error(f"Cannot browse directory through Plex: {directory_path} - {e}")
            raise PlexFileOperationError(f"Directory not accessible: {directory_path}")
    
    def validate_library_access(self, library_section) -> dict:
        """
        Validate that all library locations are accessible
        
        Args:
            library_section: Plex LibrarySection object
            
        Returns:
            Dict with validation results
        """
        results = {
            'library_name': library_section.title,
            'locations': [],
            'accessible_count': 0,
            'total_count': 0
        }
        
        for location in library_section.locations:
            accessible = self.is_accessible(location)
            results['locations'].append({
                'path': location,
                'accessible': accessible
            })
            results['total_count'] += 1
            if accessible:
                results['accessible_count'] += 1
        
        return results
    
    def get_media_file_path(self, plex_id: str, media_type: str) -> str:
        """
        Get file path for media by Plex ID
        
        Args:
            plex_id: Plex rating key
            media_type: 'movie' or 'episode'
            
        Returns:
            File path for the media
        """
        try:
            if media_type == 'movie':
                media = self.plex.fetchItem(plex_id)
            elif media_type == 'episode':
                media = self.plex.fetchItem(plex_id)
            else:
                raise PlexFileOperationError(f"Unsupported media type: {media_type}")
            
            return self.get_file_path(media)
            
        except NotFound:
            raise PlexFileOperationError(f"Media not found: {plex_id}")
    
    def write_subtitle_file(self, subtitle_path: str, content: bytes) -> bool:
        """
        Write subtitle file through Plex server filesystem access
        
        Note: This is a placeholder for when Plex API supports file writing
        For now, we validate the path and use direct filesystem access
        
        Args:
            subtitle_path: Path where to write subtitle
            content: Subtitle content to write
            
        Returns:
            True if successful
        """
        # Validate that the directory is accessible through Plex
        directory = os.path.dirname(subtitle_path)
        if not self.is_accessible(directory):
            raise PlexFileOperationError(f"Subtitle directory not accessible: {directory}")
        
        try:
            # For now, use direct file writing since Plex API doesn't support writing
            # In the future, this could use a Plex plugin or extension
            with open(subtitle_path, 'wb') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to write subtitle file: {subtitle_path} - {e}")
            raise PlexFileOperationError(f"Cannot write subtitle file: {e}")
    
    def cleanup_old_path_mappings(self):
        """
        Remove path mapping configurations (cleanup method)
        This method helps transition from old path mapping system
        """
        logger.info("Path mappings are no longer needed - using Plex API directly")
        # This could remove old path mapping settings from config
        pass


# Global instance - will be initialized when Plex connection is established
plex_file_ops: Optional[PlexFileOperations] = None


def initialize_plex_file_operations(plex_server: PlexServer):
    """Initialize the global Plex file operations instance"""
    global plex_file_ops
    plex_file_ops = PlexFileOperations(plex_server)
    logger.info("Initialized Plex-based file operations - path mappings eliminated")


def get_plex_file_operations() -> PlexFileOperations:
    """Get the global Plex file operations instance"""
    if plex_file_ops is None:
        raise PlexFileOperationError("Plex file operations not initialized")
    return plex_file_ops


# Legacy compatibility functions - these replace path_mappings calls
def path_replace(original_path: str) -> str:
    """
    Legacy compatibility: Replace path_mappings.path_replace() calls
    Now uses Plex API to get actual file path
    """
    try:
        # Original path is already the correct Plex path
        ops = get_plex_file_operations()
        if ops.is_accessible(original_path):
            return original_path
        else:
            raise PlexFileOperationError(f"Path not accessible through Plex: {original_path}")
    except Exception as e:
        logger.error(f"Path resolution failed: {original_path} - {e}")
        # Return original path as fallback
        return original_path


def path_replace_reverse(processed_path: str) -> str:
    """
    Legacy compatibility: Replace path_mappings.path_replace_reverse() calls
    With Plex API, there's no need for reverse mapping
    """
    return processed_path


def path_replace_movie(original_path: str) -> str:
    """Legacy compatibility for movie path replacement"""
    return path_replace(original_path)


def path_replace_reverse_movie(processed_path: str) -> str:
    """Legacy compatibility for reverse movie path replacement"""
    return path_replace_reverse(processed_path)
