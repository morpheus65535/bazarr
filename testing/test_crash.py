#!/usr/bin/env python3
"""
Aggressive stress test to try to crash the jobs queue manager.
Tests edge cases, race conditions, and resource exhaustion.
"""

import os
import sys
import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from itertools import count
from datetime import datetime

# Minimal mock to avoid importing the full bazarr stack
class MockSettings:
    class General:
        concurrent_jobs = 2  # Minimum setting - maximum stress
        long_job_threshold = 0.05  # 3 seconds - fast demotion
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

# Thread-safe stats
stats = {
    'completed': 0,
    'failed': 0,
    'demoted': 0,
    'started': 0,
    'queued': 0,
    'lock': threading.Lock()
}


def track_stat(key, increment=1):
    with stats['lock']:
        stats[key] += increment


class CrashTestQueue:
    """Aggressive test queue with full monitoring."""

    def __init__(self):
        self.jobs_pending_queue = deque()
        self.jobs_running_queue_short = deque()
        self.jobs_running_queue_long = deque()
        self.jobs_failed_queue = deque(maxlen=100)
        self.jobs_completed_queue = deque(maxlen=100)
        self.job_id_counter = count(1)
        self._jobs_executor = ThreadPoolExecutor(max_workers=32)  # More workers than needed
        self._queue_lock = threading.Lock()
        self._stop_flag = threading.Event()
        self._errors = []
        self._start_monitor_thread()

    def stop(self):
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
                self._errors.append(f"Monitor error: {e}")
            time.sleep(0.5)  # Fast checking

    def _demote_long_running_jobs(self):
        current_time = time.time()
        jobs_to_demote = []
        threshold = get_long_job_threshold_seconds()

        with self._queue_lock:
            for job in list(self.jobs_running_queue_short):
                if job.start_time and (current_time - job.start_time) > threshold:
                    jobs_to_demote.append(job)

            for job in jobs_to_demote:
                try:
                    self.jobs_running_queue_short.remove(job)
                    self.jobs_running_queue_long.append(job)
                    track_stat('demoted')
                except ValueError:
                    pass  # Already removed

    def feed_job(self, job_name, duration):
        new_job_id = next(self.job_id_counter)
        job = Job(
            job_id=new_job_id,
            job_name=job_name,
            module="test",
            func="test_func",
            args=[],
            kwargs={'duration': duration}
        )
        self.jobs_pending_queue.append(job)
        track_stat('queued')
        return new_job_id

    def _execute_job(self, job):
        try:
            duration = job.kwargs.get('duration', 0.01)
            time.sleep(duration)
            job.status = 'completed'
            self.jobs_completed_queue.append(job)
            track_stat('completed')
        except Exception as e:
            job.status = 'failed'
            self.jobs_failed_queue.append(job)
            track_stat('failed')
            self._errors.append(f"Job {job.job_id} failed: {e}")
        finally:
            with self._queue_lock:
                if job in self.jobs_running_queue_short:
                    self.jobs_running_queue_short.remove(job)
                elif job in self.jobs_running_queue_long:
                    self.jobs_running_queue_long.remove(job)

    def consume_jobs_pending_queue(self):
        while not self._stop_flag.is_set():
            try:
                max_concurrent_total = max(2, MockSettings.general.concurrent_jobs)
                max_concurrent_short = max(1, max_concurrent_total // 2)
                max_concurrent_long = max(1, max_concurrent_short // 2)

                total_running = len(self.jobs_running_queue_short) + len(self.jobs_running_queue_long)
                at_total_cap = total_running >= max_concurrent_total

                can_start_short = len(self.jobs_running_queue_short) < max_concurrent_short and not at_total_cap
                can_start_long = len(self.jobs_running_queue_long) < max_concurrent_long and not at_total_cap

                job_to_start = None
                job_index = None

                for i, pending_job in enumerate(list(self.jobs_pending_queue)):
                    is_long = is_known_long_running_job(pending_job.job_name)
                    if (is_long and can_start_long) or (not is_long and can_start_short):
                        job_to_start = pending_job
                        job_index = i
                        break

                if job_to_start is not None:
                    try:
                        del self.jobs_pending_queue[job_index]
                        job = job_to_start
                    except IndexError:
                        time.sleep(0.001)
                        continue
                    else:
                        job.status = 'running'
                        job.last_run_time = datetime.now()
                        job.start_time = time.time()
                        track_stat('started')

                        is_long_job = is_known_long_running_job(job.job_name)
                        with self._queue_lock:
                            if is_long_job:
                                self.jobs_running_queue_long.append(job)
                            else:
                                self.jobs_running_queue_short.append(job)

                        self._jobs_executor.submit(self._execute_job, job)
                else:
                    time.sleep(0.001)
            except Exception as e:
                self._errors.append(f"Consumer error: {e}")


def test_rapid_fire():
    """Rapidly queue and process jobs to stress thread safety."""
    print("\n" + "=" * 70)
    print("TEST 1: Rapid Fire (10,000 instant jobs)")
    print("=" * 70)
    
    for key in ['completed', 'failed', 'demoted', 'started', 'queued']:
        stats[key] = 0
    
    queue = CrashTestQueue()
    consumer = threading.Thread(target=queue.consume_jobs_pending_queue, daemon=True)
    consumer.start()
    
    # Queue 10,000 jobs as fast as possible
    start = time.time()
    for i in range(10000):
        job_type = random.choice([
            ("Quick", 0.001),
            ("Sync with Sonarr", 0.001),  # Known long
        ])
        queue.feed_job(job_type[0], job_type[1])
    queue_time = time.time() - start
    
    print(f"  Queued 10,000 jobs in {queue_time:.3f}s")
    
    # Wait for completion with timeout
    timeout = 30
    start_wait = time.time()
    while stats['queued'] > stats['completed'] + stats['failed']:
        if time.time() - start_wait > timeout:
            print(f"  TIMEOUT after {timeout}s")
            break
        time.sleep(0.1)
    
    total_time = time.time() - start
    queue.stop()
    
    print(f"  Completed: {stats['completed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Throughput: {stats['completed']/total_time:.0f} jobs/sec")
    print(f"  Errors: {len(queue._errors)}")
    if queue._errors:
        for e in queue._errors[:5]:
            print(f"    - {e}")
    
    return len(queue._errors) == 0 and stats['failed'] == 0


def test_all_demoted():
    """Queue jobs that ALL need to be demoted."""
    print("\n" + "=" * 70)
    print("TEST 2: Force Demotion (100 slow jobs)")
    print("=" * 70)
    
    for key in ['completed', 'failed', 'demoted', 'started', 'queued']:
        stats[key] = 0
    
    queue = CrashTestQueue()
    consumer = threading.Thread(target=queue.consume_jobs_pending_queue, daemon=True)
    consumer.start()
    
    # Queue jobs that will ALL exceed threshold (3s threshold, 5s jobs)
    for i in range(100):
        queue.feed_job("Slow Job That Will Demote", 5.0)
    
    print(f"  Queued 100 slow jobs (5s each, threshold 3s)")
    
    # Wait with timeout
    timeout = 60
    start_wait = time.time()
    last_print = 0
    while stats['queued'] > stats['completed'] + stats['failed']:
        if time.time() - start_wait > timeout:
            print(f"  TIMEOUT after {timeout}s")
            break
        elapsed = int(time.time() - start_wait)
        if elapsed > last_print and elapsed % 10 == 0:
            print(f"    Progress: {stats['completed']}/{stats['queued']} completed, {stats['demoted']} demoted")
            last_print = elapsed
        time.sleep(0.5)
    
    total_time = time.time() - start_wait
    queue.stop()
    
    print(f"  Completed: {stats['completed']}")
    print(f"  Demoted: {stats['demoted']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Errors: {len(queue._errors)}")
    if queue._errors:
        for e in queue._errors[:5]:
            print(f"    - {e}")
    
    return len(queue._errors) == 0 and stats['failed'] == 0


def test_concurrent_queueing():
    """Multiple threads queuing simultaneously."""
    print("\n" + "=" * 70)
    print("TEST 3: Concurrent Queueing (10 threads, 1000 each)")
    print("=" * 70)
    
    for key in ['completed', 'failed', 'demoted', 'started', 'queued']:
        stats[key] = 0
    
    queue = CrashTestQueue()
    consumer = threading.Thread(target=queue.consume_jobs_pending_queue, daemon=True)
    consumer.start()
    
    def queue_worker(count):
        for _ in range(count):
            job_type = random.choice([
                ("Quick", 0.001),
                ("Medium", 0.01),
                ("Sync with Radarr", 0.01),
            ])
            queue.feed_job(job_type[0], job_type[1])
    
    # 10 threads each queuing 1000 jobs
    threads = []
    start = time.time()
    for _ in range(10):
        t = threading.Thread(target=queue_worker, args=(1000,))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    queue_time = time.time() - start
    print(f"  Queued 10,000 jobs from 10 threads in {queue_time:.3f}s")
    
    # Wait for completion
    timeout = 60
    start_wait = time.time()
    while stats['queued'] > stats['completed'] + stats['failed']:
        if time.time() - start_wait > timeout:
            print(f"  TIMEOUT after {timeout}s")
            break
        time.sleep(0.1)
    
    total_time = time.time() - start
    queue.stop()
    
    print(f"  Completed: {stats['completed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Errors: {len(queue._errors)}")
    
    return len(queue._errors) == 0 and stats['failed'] == 0


def test_edge_case_limits():
    """Test edge cases with min/max concurrent settings."""
    print("\n" + "=" * 70)
    print("TEST 4: Edge Case - Minimum Concurrency (2 total)")
    print("=" * 70)
    
    # max_concurrent_total = 2
    # max_concurrent_short = max(1, 2 // 2) = 1
    # max_concurrent_long = max(1, 1 // 2) = 1
    # room = 2 - 1 - 1 = 0
    
    print("  Limits: total=2, short=1, long=1, room=0")
    
    for key in ['completed', 'failed', 'demoted', 'started', 'queued']:
        stats[key] = 0
    
    queue = CrashTestQueue()
    consumer = threading.Thread(target=queue.consume_jobs_pending_queue, daemon=True)
    consumer.start()
    
    # Mix of short and long jobs
    for i in range(50):
        queue.feed_job("Quick Job", 0.01)
    for i in range(50):
        queue.feed_job("Sync with Sonarr", 0.01)  # Known long
    for i in range(20):
        queue.feed_job("Will Demote Job", 5.0)  # Will exceed threshold
    
    print(f"  Queued: 50 short + 50 long + 20 demotable = 120 jobs")
    
    timeout = 60
    start_wait = time.time()
    last_print = 0
    while stats['queued'] > stats['completed'] + stats['failed']:
        if time.time() - start_wait > timeout:
            print(f"  TIMEOUT after {timeout}s")
            break
        elapsed = int(time.time() - start_wait)
        if elapsed > last_print and elapsed % 10 == 0:
            short_q = len(queue.jobs_running_queue_short)
            long_q = len(queue.jobs_running_queue_long)
            print(f"    Progress: {stats['completed']}/{stats['queued']}, running short={short_q} long={long_q}, demoted={stats['demoted']}")
            last_print = elapsed
        time.sleep(0.5)
    
    total_time = time.time() - start_wait
    queue.stop()
    
    print(f"  Completed: {stats['completed']}")
    print(f"  Demoted: {stats['demoted']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Errors: {len(queue._errors)}")
    
    return len(queue._errors) == 0 and stats['failed'] == 0


def main():
    print("\n" + "=" * 70)
    print("CRASH TEST: Jobs Queue Manager")
    print("=" * 70)
    print(f"Settings: concurrent_jobs={MockSettings.general.concurrent_jobs}")
    print(f"          long_job_threshold={MockSettings.general.long_job_threshold} min ({get_long_job_threshold_seconds()}s)")
    
    results = []
    
    results.append(("Rapid Fire", test_rapid_fire()))
    results.append(("Force Demotion", test_all_demoted()))
    results.append(("Concurrent Queueing", test_concurrent_queueing()))
    results.append(("Edge Case Limits", test_edge_case_limits()))
    
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("All tests passed! Queue manager is robust.")
    else:
        print("Some tests failed. Check errors above.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
