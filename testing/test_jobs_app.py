# coding=utf-8
"""
Test job functions for stress testing the jobs queue.
These functions are designed to be called by the jobs queue system.
"""

import time
import logging


def test_job_function(duration_seconds, job_name, **kwargs):
    """Test job that sleeps for the specified duration. Used for stress testing.
    
    Args:
        duration_seconds: How long the job should run
        job_name: Name of the job (for logging)
        **kwargs: Accepts additional kwargs (like job_id) that jobs_queue adds automatically
    """
    logging.info(f"BAZARR Test job '{job_name}' starting, will run for {duration_seconds}s")
    time.sleep(duration_seconds)
    logging.info(f"BAZARR Test job '{job_name}' completed after {duration_seconds}s")
    return True
