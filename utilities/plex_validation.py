#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plex file validation and diagnostics system
Replaces path mapping diagnostics with comprehensive Plex API validation
"""

import logging
from typing import Dict, List, Optional
from utilities.plex_file_operations import get_plex_file_operations, PlexFileOperationError
from plex.operations import get_plex_server

logger = logging.getLogger(__name__)


def validate_plex_file_access() -> Dict:
    """
    Comprehensive validation of Plex file access
    
    Returns:
        Validation report with all diagnostics
    """
    report = {
        'status': 'unknown',
        'message': '',
        'libraries': [],
        'recommendations': [],
        'path_mapping_needed': False,
        'total_locations': 0,
        'accessible_locations': 0
    }
    
    try:
        # Get Plex server connection
        plex = get_plex_server()
        file_ops = get_plex_file_operations()
        
        # Validate each library
        for section in plex.library.sections():
            if hasattr(section, 'locations'):  # Only media libraries have locations
                library_validation = file_ops.validate_library_access(section)
                report['libraries'].append(library_validation)
                
                report['total_locations'] += library_validation['total_count']
                report['accessible_locations'] += library_validation['accessible_count']
        
        # Generate overall status and recommendations
        if report['accessible_locations'] == report['total_locations'] and report['total_locations'] > 0:
            report['status'] = 'perfect'
            report['message'] = 'Perfect! All library locations accessible through Plex API. Path mappings eliminated!'
            report['recommendations'] = [
                'Your setup is optimal - no configuration needed',
                'All subtitle operations will use direct Plex API access',
                'Path mappings have been completely eliminated'
            ]
        elif report['accessible_locations'] > 0:
            report['status'] = 'partial'
            report['message'] = f'⚠️ {report["accessible_locations"]}/{report["total_locations"]} library locations accessible'
            report['recommendations'] = [
                'Some libraries are accessible, others may need attention',
                'Check file permissions and mount points',
                'Consider using Plex Docker container for better filesystem integration'
            ]
        else:
            report['status'] = 'failed'
            report['message'] = '❌ No library locations accessible through Plex API'
            report['recommendations'] = [
                'Check Plex server filesystem permissions',
                'Verify Bazarr and Plex have access to the same filesystem',
                'Consider running Bazarr in the same container/environment as Plex'
            ]
            
    except Exception as e:
        report['status'] = 'error'
        report['message'] = f'❌ Cannot connect to Plex server: {e}'
        report['recommendations'] = [
            'Check Plex server connection and authentication',
            'Verify Plex server is running and accessible',
            'Check authentication tokens and permissions'
        ]
    
    return report


def get_sample_files_from_libraries(limit: int = 5) -> List[Dict]:
    """
    Get sample files from each library to test accessibility
    
    Args:
        limit: Maximum number of files to test per library
        
    Returns:
        List of file test results
    """
    sample_files = []
    
    try:
        plex = get_plex_server()
        file_ops = get_plex_file_operations()
        
        for section in plex.library.sections():
            if hasattr(section, 'locations'):
                try:
                    # Get some media items from this library
                    items = section.search(limit=limit)
                    
                    for item in items:
                        try:
                            file_path = file_ops.get_file_path(item)
                            accessible = file_ops.is_accessible(file_path)
                            
                            sample_files.append({
                                'library': section.title,
                                'title': item.title,
                                'path': file_path,
                                'accessible': accessible,
                                'type': section.type
                            })
                        except PlexFileOperationError as e:
                            sample_files.append({
                                'library': section.title,
                                'title': item.title,
                                'path': 'N/A',
                                'accessible': False,
                                'error': str(e),
                                'type': section.type
                            })
                except Exception as e:
                    logger.warning(f"Could not sample files from library {section.title}: {e}")
                    
    except Exception as e:
        logger.error(f"Failed to get sample files: {e}")
    
    return sample_files


def generate_migration_report() -> Dict:
    """
    Generate a comprehensive report on the path mapping elimination
    
    Returns:
        Migration report with before/after comparison
    """
    report = {
        'migration_status': 'Path Mappings Eliminated',
        'new_system': 'Plex API Direct Access',
        'benefits': [
            '✅ Zero configuration required for compatible setups',
            '✅ Automatic file path resolution through Plex',
            '✅ No more manual path mapping setup',
            '✅ Container-friendly architecture',
            '✅ Direct filesystem validation',
            '✅ Simplified troubleshooting'
        ],
        'technical_changes': [
            'Replaced path_mappings module with plex_file_operations',
            'All file access now goes through Plex API',
            'Automatic path validation and accessibility testing',
            'Legacy compatibility maintained for existing code'
        ],
        'validation_results': validate_plex_file_access(),
        'sample_files': get_sample_files_from_libraries(3)
    }
    
    return report


def print_migration_summary():
    """Print a summary of the path mapping elimination"""
    report = generate_migration_report()
    
    print("\n" + "="*60)
    print("BAZARR PATH MAPPING ELIMINATION COMPLETE")
    print("="*60)
    
    print(f"\nVALIDATION RESULTS:")
    validation = report['validation_results']
    print(f"   Status: {validation['status'].upper()}")
    print(f"   {validation['message']}")
    print(f"   Libraries: {len(validation['libraries'])}")
    print(f"   Accessible Locations: {validation['accessible_locations']}/{validation['total_locations']}")
    
    print(f"\n🎯 BENEFITS:")
    for benefit in report['benefits']:
        print(f"   {benefit}")
    
    print(f"\n⚙️ TECHNICAL CHANGES:")
    for change in report['technical_changes']:
        print(f"   • {change}")
    
    if validation['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in validation['recommendations']:
            print(f"   • {rec}")
    
    print("\n" + "="*60)
    print("Path mappings are now eliminated!")
    print("="*60 + "\n")


if __name__ == "__main__":
    print_migration_summary()
