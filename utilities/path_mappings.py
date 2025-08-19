#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ENHANCED: Path mappings replacement using Plex API with multiple library support

This module provides compatibility for existing code that imports path_mappings,
but now uses the new Plex API-based path resolution system that handles multiple
library locations automatically.

All path mapping functionality has been replaced with dynamic Plex API resolution.
"""

import logging
from utilities.plex_path_resolver import (
    path_replace,
    path_replace_reverse, 
    path_replace_movie,
    path_replace_reverse_movie,
    plex_path_resolver
)

logger = logging.getLogger(__name__)

# Show migration info when imported
logger.info("path_mappings now using Plex API with multiple library location support")


class PathMappingsEnhanced:
    """
    ENHANCED: PathMappings replacement with Plex API and multiple library support
    
    This class maintains API compatibility while using the new Plex-based system
    that automatically handles multiple library locations per media type.
    """
    
    def __init__(self):
        logger.info("PathMappings enhanced - using Plex API with multiple library support")
        # Initialize empty lists for compatibility (no longer used)
        self.path_mapping_series = []
        self.path_mapping_movies = []
    
    def update(self):
        """
        ENHANCED: Clear Plex API cache instead of updating static mappings
        No longer needed as Plex API handles paths dynamically
        """
        logger.info("Path mappings update called - clearing Plex API cache for fresh library data")
        plex_path_resolver.clear_cache()
        # Keep empty lists since we don't use static path mappings anymore
        self.path_mapping_series = []
        self.path_mapping_movies = []
    
    def path_replace(self, original_path: str) -> str:
        """ENHANCED: Dynamic path resolution via Plex API with multiple library support"""
        return path_replace(original_path)
    
    def path_replace_reverse(self, processed_path: str) -> str:
        """ENHANCED: No reverse mapping needed with Plex API"""
        return path_replace_reverse(processed_path)
    
    def path_replace_movie(self, original_path: str) -> str:
        """ENHANCED: Dynamic movie path resolution via Plex API"""
        return path_replace_movie(original_path)
    
    def path_replace_reverse_movie(self, processed_path: str) -> str:
        """ENHANCED: No reverse mapping needed with Plex API"""
        return path_replace_reverse_movie(processed_path)


# Enhanced compatibility instance
path_mappings = PathMappingsEnhanced()

# Expose functions for direct import
__all__ = [
    'path_mappings',
    'path_replace',
    'path_replace_reverse',
    'path_replace_movie', 
    'path_replace_reverse_movie'
]
