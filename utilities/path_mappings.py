#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DEPRECATED: Legacy path_mappings compatibility layer

This module provides compatibility for existing code that imports path_mappings,
but now uses the new Plex API-based file operations system.

All path mapping functionality has been replaced with direct Plex API access.
"""

import logging
from utilities.plex_file_operations import (
    path_replace,
    path_replace_reverse, 
    path_replace_movie,
    path_replace_reverse_movie,
    get_plex_file_operations
)

logger = logging.getLogger(__name__)

# Show deprecation warning when imported
logger.warning("⚠️  path_mappings module is DEPRECATED - now using Plex API directly")


class PathMappingsDeprecated:
    """
    DEPRECATED: Legacy PathMappings class - now uses Plex API
    
    This class maintains API compatibility while using the new Plex-based system.
    All functionality has been replaced with Plex API operations.
    """
    
    def __init__(self):
        logger.warning("PathMappings is deprecated - using Plex API file operations")
        # Initialize empty lists for compatibility
        self.path_mapping_series = []
        self.path_mapping_movies = []
    
    def update(self):
        """
        DEPRECATED: Legacy update method for compatibility
        No longer needed as Plex API handles paths directly
        """
        logger.info("Path mappings update called - no action needed with Plex API")
        # Keep empty lists since we don't use path mappings anymore
        self.path_mapping_series = []
        self.path_mapping_movies = []
    
    def path_replace(self, original_path: str) -> str:
        """DEPRECATED: Use Plex API directly"""
        return path_replace(original_path)
    
    def path_replace_reverse(self, processed_path: str) -> str:
        """DEPRECATED: Use Plex API directly"""
        return path_replace_reverse(processed_path)
    
    def path_replace_movie(self, original_path: str) -> str:
        """DEPRECATED: Use Plex API directly"""
        return path_replace_movie(original_path)
    
    def path_replace_reverse_movie(self, processed_path: str) -> str:
        """DEPRECATED: Use Plex API directly"""
        return path_replace_reverse_movie(processed_path)


# Legacy compatibility instance
path_mappings = PathMappingsDeprecated()

# Expose functions for direct import
__all__ = [
    'path_mappings',
    'path_replace',
    'path_replace_reverse',
    'path_replace_movie', 
    'path_replace_reverse_movie'
]
