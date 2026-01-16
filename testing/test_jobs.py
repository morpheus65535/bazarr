#!/usr/bin/env python3
"""
Stress test for the jobs queue system.
Tests the full lifecycle including job execution, demotion, and mixed workloads.
"""

import os
import sys
import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor
from collections import Counter, deque
from itertools import count
from datetime import datetime

# Minimal mock to avoid importing the full bazarr stack
class MockSettings:
    class General:
        concurrent_jobs = 1  # Match UI: max(2,1)=2 total, 1 short, 1 long, 0 room
        long_job_threshold = 0.1  # 6 seconds (0.1 min) for faster testing
    general = General()


class MockEventStream:
    def __call__(self, *args, **kwargs):
        pass


# Setup mocks before importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bazarr'))

sys.modules['app.event_handler'] = type(sys)('app.event_handler')
sys.modules['app.event_handler'].event_stream = MockEventStream()
sys.modules['app.config'] = type(sys)('app.config')
sys.modules['app.config'].settings = MockSettings()

from app.jobs_queue import Job, is_known_long_running_job, get_long_job_threshold_seconds

# Stats tracking
stats = {
    'short_completed': 0,
    'long_completed': 0,
    'demoted': 0,
    'errors': 0,
    'lock': threading.Lock()
}


def track_stat(key, increment=1):
    with stats['lock']:
        stats[key] += increment


class RealisticJobsQueue:
    """Full JobsQueue implementation for realistic testing."""

    def __init__(self):
        self.jobs_pending_queue = deque()
        self.jobs_running_queue_short = deque()
        self.jobs_running_queue_long = deque()
        self.jobs_failed_queue = deque(maxlen=100)
        self.jobs_completed_queue = deque(maxlen=100)
        self.job_id_counter = count(1)
        self._jobs_executor = ThreadPoolExecutor(max_workers=(os.cpu_count() or 2) * 2)
        self._queue_lock = threading.Lock()
        self._stop_flag = threading.Event()
        self._start_monitor_thread()

    def stop(self):
        """Stop the queue processing."""
        self._stop_flag.set()

    @property
    def jobs_running_queue(self):
        return list(self.jobs_running_queue_short) + list(self.jobs_running_queue_long)

    def _start_monitor_thread(self):
        monitor_thread = threading.Thread(target=self._monitor_running_jobs, daemon=True)
        monitor_thread.start()

    def _monitor_running_jobs(self):
        while not self._stop_flag.is_set():
            try:
                self._demote_long_running_jobs()
            except Exception as e:
                print(f"Monitor error: {e}")
            time.sleep(1)  # Check every second for faster testing

    def _demote_long_running_jobs(self):
        current_time = time.time()
        jobs_to_demote = []
        threshold = get_long_job_threshold_seconds()
        hard_cap = (os.cpu_count() or 2) * 2

        with self._queue_lock:
            total_running = len(self.jobs_running_queue_short) + len(self.jobs_running_queue_long)

            for job in list(self.jobs_running_queue_short):
                if job.start_time and (current_time - job.start_time) > threshold:
                    if total_running < hard_cap:
                        jobs_to_demote.append(job)

            for job in jobs_to_demote:
                try:
                    self.jobs_running_queue_short.remove(job)
                    self.jobs_running_queue_long.append(job)
                    track_stat('demoted')
                except ValueError:
                    pass

    def feed_jobs_pending_queue(self, job_name, module, func, args=None, kwargs=None,
                                is_progress=False, is_signalr=False, progress_max=0):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        new_job_id = next(self.job_id_counter)
        self.jobs_pending_queue.append(
            Job(job_id=new_job_id,
                job_name=job_name,
                module=module,
                func=func,
                args=args,
                kwargs=kwargs,
                is_progress=is_progress,
                is_signalr=is_signalr,
                progress_max=progress_max)
        )
        return new_job_id

    def _execute_job(self, job):
        try:
            # Simulate job execution based on job name
            if "quick" in job.job_name.lower():
                time.sleep(random.uniform(0.01, 0.1))  # 10-100ms
            elif "slow" in job.job_name.lower():
                time.sleep(random.uniform(7, 8))  # 7-8 seconds (will be demoted after 6s threshold)
            elif "Sync with" in job.job_name:
                time.sleep(random.uniform(0.5, 2))  # Known long job
            else:
                time.sleep(random.uniform(0.05, 0.5))  # Medium job

            job.status = 'completed'
            job.last_run_time = datetime.now()
            self.jobs_completed_queue.append(job)

            # Track completion
            if job in list(self.jobs_running_queue_long):
                track_stat('long_completed')
            else:
                track_stat('short_completed')

        except Exception as e:
            job.status = 'failed'
            self.jobs_failed_queue.append(job)
            track_stat('errors')
        finally:
            with self._queue_lock:
                if job in self.jobs_running_queue_short:
                    self.jobs_running_queue_short.remove(job)
                elif job in self.jobs_running_queue_long:
                    self.jobs_running_queue_long.remove(job)

    def consume_jobs_pending_queue(self):
        while not self._stop_flag.is_set():
            # Match production code exactly
            max_concurrent_total = max(2, MockSettings.general.concurrent_jobs)
            max_concurrent_short = max(1, max_concurrent_total // 2)
            max_concurrent_long = max(1, max_concurrent_short // 2)
            total_running = len(self.jobs_running_queue_short) + len(self.jobs_running_queue_long)
            at_total_cap = total_running >= max_concurrent_total

            # Short jobs: check short queue AND total cap
            can_start_short = len(self.jobs_running_queue_short) < max_concurrent_short and not at_total_cap
            # Long jobs: check long queue AND total cap
            can_start_long = len(self.jobs_running_queue_long) < max_concurrent_long and not at_total_cap

            job_to_start = None

            for pending_job in list(self.jobs_pending_queue):
                is_long = is_known_long_running_job(pending_job.job_name) and not pending_job.is_signalr
                if (is_long and can_start_long) or (not is_long and can_start_short):
                    job_to_start = pending_job
                    break

            if job_to_start is not None:
                try:
                    # Remove job by identity (not index) - safe if queue was modified
                    self.jobs_pending_queue.remove(job_to_start)
                    job = job_to_start
                except ValueError:
                    # Job was already removed (e.g., cancelled), retry
                    continue
                else:
                    job.status = 'running'
                    job.last_run_time = datetime.now()
                    job.start_time = time.time()

                    is_long_job = is_known_long_running_job(job.job_name) and not job.is_signalr
                    with self._queue_lock:
                        if is_long_job:
                            self.jobs_running_queue_long.append(job)
                        else:
                            self.jobs_running_queue_short.append(job)

                    self._jobs_executor.submit(self._execute_job, job)
            else:
                time.sleep(0.01)


def test_mixed_workload():
    """Test with 300 mixed jobs - quick, slow, and known long-running."""
    print("\n" + "=" * 70)
    print("TEST: Mixed Workload (300 jobs)")
    print("=" * 70)
    
    # Calculate limits matching production code exactly
    max_concurrent_total = max(2, MockSettings.general.concurrent_jobs)
    max_concurrent_short = max(1, max_concurrent_total // 2)
    max_concurrent_long = max(1, max_concurrent_short // 2)
    room = max_concurrent_total - max_concurrent_short - max_concurrent_long
    
    print(f"  Settings from UI: concurrent_jobs={MockSettings.general.concurrent_jobs}")
    print(f"  Calculated limits:")
    print(f"    Max Concurrent (total): {max_concurrent_total}")
    print(f"    Max Short:              {max_concurrent_short}")
    print(f"    Max Long:               {max_concurrent_long}")
    print(f"    Room for demotion:      {room}")
    print(f"    Long job threshold:     {MockSettings.general.long_job_threshold} min ({MockSettings.general.long_job_threshold * 60:.0f}s)")
    print()

    # Reset stats
    for key in ['short_completed', 'long_completed', 'demoted', 'errors']:
        stats[key] = 0

    queue = RealisticJobsQueue()

    # Start consumer thread
    consumer = threading.Thread(target=queue.consume_jobs_pending_queue, daemon=True)
    consumer.start()

    # Job mix configuration
    num_jobs = 300
    job_types = [
        ("Quick Job", 0.75),           # 75% quick jobs (10-100ms)
        ("Medium Job", 0.15),          # 15% medium jobs (50-500ms)
        ("Slow Job (will demote)", 0.02),  # 2% slow jobs (7-8s, will be demoted)
        ("Sync with Sonarr", 0.04),    # 4% known long pattern
        ("Sync with Radarr", 0.04),    # 4% known long pattern
    ]

    print("  Job distribution:")
    for name, pct in job_types:
        is_long = is_known_long_running_job(name)
        queue_type = "-> LONG queue" if is_long else "-> SHORT queue"
        demote_note = " (will be demoted)" if "Slow" in name else ""
        print(f"    {pct*100:5.1f}% {name} {queue_type}{demote_note}")
    print()

    # Generate and queue jobs
    print("  Queueing jobs...", end=" ", flush=True)
    start_queue = time.time()

    job_ids = []
    for i in range(num_jobs):
        # Select job type based on distribution
        r = random.random()
        cumulative = 0
        for name, pct in job_types:
            cumulative += pct
            if r < cumulative:
                job_name = f"{name} #{i}"
                break

        job_id = queue.feed_jobs_pending_queue(
            job_name=job_name,
            module="test",
            func="test_func",
        )
        job_ids.append(job_id)

    queue_time = time.time() - start_queue
    print(f"done ({queue_time:.2f}s, {num_jobs/queue_time:.0f} jobs/sec)")

    # Check for duplicate IDs
    unique_ids = len(set(job_ids))
    if unique_ids != num_jobs:
        print(f"  ERROR: Found {num_jobs - unique_ids} duplicate job IDs!")
        return False

    print(f"  All {num_jobs} job IDs are unique")
    print()

    # Wait for jobs to complete with progress updates
    print("  Processing jobs:")
    start_process = time.time()
    last_update = 0

    while True:
        pending = len(queue.jobs_pending_queue)
        short_running = len(queue.jobs_running_queue_short)
        long_running = len(queue.jobs_running_queue_long)
        completed = len(queue.jobs_completed_queue)
        failed = len(queue.jobs_failed_queue)

        total_done = stats['short_completed'] + stats['long_completed']
        elapsed = time.time() - start_process

        # Update every second
        if elapsed - last_update >= 1:
            print(f"\r    [{elapsed:5.1f}s] Pending: {pending:5d} | "
                  f"Running: {short_running} short + {long_running} long | "
                  f"Completed: {total_done:5d} | "
                  f"Demoted: {stats['demoted']:3d}", end="", flush=True)
            last_update = elapsed

        if pending == 0 and short_running == 0 and long_running == 0:
            break

        if elapsed > 300:  # 5 minute timeout
            print("\n  TIMEOUT!")
            break

        time.sleep(0.1)

    print()  # newline after progress
    process_time = time.time() - start_process

    # Stop the queue
    queue.stop()
    time.sleep(0.5)

    # Final stats
    print()
    print("  Results:")
    print(f"    Total time: {process_time:.1f}s")
    print(f"    Jobs/sec: {num_jobs/process_time:.1f}")
    print()
    print(f"    Short queue completions: {stats['short_completed']}")
    print(f"    Long queue completions: {stats['long_completed']}")
    print(f"    Jobs demoted (short -> long): {stats['demoted']}")
    print(f"    Errors: {stats['errors']}")
    print()

    # Verify results
    total_completed = stats['short_completed'] + stats['long_completed']
    success = True

    if unique_ids != num_jobs:
        print("  FAIL: Duplicate job IDs detected!")
        success = False

    if stats['errors'] > 0:
        print(f"  FAIL: {stats['errors']} job errors!")
        success = False

    if total_completed < num_jobs * 0.99:  # Allow 1% margin for timing
        print(f"  FAIL: Only {total_completed}/{num_jobs} jobs completed!")
        success = False

    # We expect some demotions (the 2% slow jobs)
    expected_demotions = int(num_jobs * 0.02 * 0.5)  # ~50% of slow jobs should be demoted
    if stats['demoted'] < expected_demotions:
        print(f"  WARNING: Expected ~{expected_demotions} demotions, got {stats['demoted']}")

    if success:
        print("  PASS: All jobs processed correctly with proper queue routing")

    return success


def test_rapid_job_submission_during_processing():
    """Test adding jobs while processing is ongoing."""
    print("\n" + "=" * 70)
    print("TEST: Rapid Submission During Processing")
    print("=" * 70)

    for key in ['short_completed', 'long_completed', 'demoted', 'errors']:
        stats[key] = 0

    queue = RealisticJobsQueue()

    consumer = threading.Thread(target=queue.consume_jobs_pending_queue, daemon=True)
    consumer.start()

    all_ids = []
    lock = threading.Lock()
    stop_adding = threading.Event()

    def add_jobs_continuously():
        local_ids = []
        i = 0
        while not stop_adding.is_set():
            job_type = random.choice(["Quick", "Medium", "Sync with Sonarr"])
            job_id = queue.feed_jobs_pending_queue(
                job_name=f"{job_type} #{i}",
                module="test",
                func="test_func",
            )
            local_ids.append(job_id)
            i += 1
            time.sleep(random.uniform(0.0001, 0.001))
        with lock:
            all_ids.extend(local_ids)
        return len(local_ids)

    print("  Starting 10 producer threads while consumer is running...")
    start = time.time()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(add_jobs_continuously) for _ in range(10)]

        # Let it run for 10 seconds
        time.sleep(10)
        stop_adding.set()

        total_added = sum(f.result() for f in futures)

    # Wait for completion
    print(f"  Added {total_added} jobs, waiting for completion...")
    while len(queue.jobs_pending_queue) > 0 or len(queue.jobs_running_queue) > 0:
        time.sleep(0.1)
        if time.time() - start > 60:
            break

    queue.stop()
    elapsed = time.time() - start

    unique_ids = len(set(all_ids))
    duplicates = total_added - unique_ids

    print(f"  Time: {elapsed:.1f}s")
    print(f"  Jobs added: {total_added}")
    print(f"  Unique IDs: {unique_ids}")
    print(f"  Duplicates: {duplicates}")
    print(f"  Completed: {stats['short_completed'] + stats['long_completed']}")
    print(f"  Demoted: {stats['demoted']}")

    if duplicates > 0:
        print("  FAIL: Duplicate IDs during concurrent add/process!")
        return False
    else:
        print("  PASS: No duplicates during concurrent operations")
        return True


def test_id_uniqueness_only():
    """Quick test focusing just on ID uniqueness under extreme load."""
    print("\n" + "=" * 70)
    print("TEST: ID Uniqueness (Quick Check)")
    print("=" * 70)

    queue = RealisticJobsQueue()
    job_ids = []
    lock = threading.Lock()
    barrier = threading.Barrier(100)

    def hammer():
        barrier.wait()
        local_ids = []
        for _ in range(200):
            job_id = queue.feed_jobs_pending_queue(
                job_name="test",
                module="test",
                func="func",
            )
            local_ids.append(job_id)
        with lock:
            job_ids.extend(local_ids)

    threads = [threading.Thread(target=hammer) for _ in range(100)]
    start = time.time()

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    elapsed = time.time() - start
    queue.stop()

    unique = len(set(job_ids))
    total = len(job_ids)
    duplicates = total - unique

    print(f"  Threads: 100, Jobs each: 200, Total: {total}")
    print(f"  Unique IDs: {unique}")
    print(f"  Duplicates: {duplicates}")
    print(f"  Time: {elapsed:.3f}s ({total/elapsed:.0f} jobs/sec)")

    if duplicates > 0:
        print("  FAIL!")
        return False
    else:
        print("  PASS")
        return True


if __name__ == "__main__":
    results = {}

    results["id_uniqueness"] = test_id_uniqueness_only()
    results["mixed_workload"] = test_mixed_workload()
    results["concurrent_submit"] = test_rapid_job_submission_during_processing()

    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n  Total: {passed}/{total} tests passed")

    sys.exit(0 if all(results.values()) else 1)
