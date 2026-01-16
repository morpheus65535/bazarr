#!/usr/bin/env python3
"""
IRL Stress Test for Bazarr Jobs Queue

This script stress tests a running Bazarr instance by triggering multiple tasks
simultaneously and monitoring the jobs queue behavior in real-time.

IMPORTANT: Run this against a development/test instance, NOT production!

Usage:
    1. Make sure Bazarr is running at http://localhost:6767
    2. Run: python3 stress_test_irl.py

The script will:
    - Get the list of available tasks
    - Trigger multiple tasks simultaneously
    - Monitor the jobs queue and running jobs
    - Report on queue behavior and timing
"""

import requests
import time
import threading
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Configuration
BAZARR_URL = "http://localhost:6767"
API_KEY = "bazarr"  # From data/config/config.yaml auth.apikey

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def c(text, color):
    return f"{color}{text}{Colors.ENDC}"


def get_headers():
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-KEY"] = API_KEY
    return headers


def get_tasks():
    """Get list of available tasks from Bazarr."""
    try:
        resp = requests.get(f"{BAZARR_URL}/api/system/tasks", headers=get_headers(), timeout=10)
        if resp.status_code == 200:
            return resp.json().get("data", [])
        else:
            print(c(f"Failed to get tasks: {resp.status_code}", Colors.FAIL))
            return []
    except Exception as e:
        print(c(f"Error getting tasks: {e}", Colors.FAIL))
        return []


def trigger_task(task_id):
    """Trigger a task to run now."""
    try:
        resp = requests.post(
            f"{BAZARR_URL}/api/system/tasks",
            headers=get_headers(),
            params={"taskid": task_id},
            timeout=10
        )
        return resp.status_code in [200, 204]
    except Exception as e:
        print(c(f"Error triggering task {task_id}: {e}", Colors.FAIL))
        return False


def get_jobs(status=None):
    """Get jobs from the queue."""
    try:
        params = {}
        if status:
            params["status"] = status
        resp = requests.get(
            f"{BAZARR_URL}/api/system/jobs",
            headers=get_headers(),
            params=params,
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get("data", [])
        return []
    except Exception as e:
        return []


def get_settings():
    """Get current settings to show concurrent_jobs value."""
    try:
        resp = requests.get(f"{BAZARR_URL}/api/system/settings", headers=get_headers(), timeout=10)
        if resp.status_code == 200:
            return resp.json().get("data", {})
        return {}
    except:
        return {}


def print_queue_status():
    """Print current queue status."""
    pending = get_jobs("pending")
    running = get_jobs("running")
    
    print(f"  Queue Status: {c(len(pending), Colors.WARNING)} pending, "
          f"{c(len(running), Colors.OKGREEN)} running")
    
    if running:
        print("  Running jobs:")
        for job in running[:5]:  # Show first 5
            print(f"    - {job.get('job_name', 'unknown')[:50]}")
        if len(running) > 5:
            print(f"    ... and {len(running) - 5} more")
    
    return len(pending), len(running)


def monitor_queue(stop_event, interval=1):
    """Continuously monitor the queue until stopped."""
    print(c("\n📊 Starting queue monitor...", Colors.HEADER))
    peak_pending = 0
    peak_running = 0
    
    while not stop_event.is_set():
        pending = get_jobs("pending")
        running = get_jobs("running")
        
        peak_pending = max(peak_pending, len(pending))
        peak_running = max(peak_running, len(running))
        
        now = datetime.now().strftime("%H:%M:%S")
        sys.stdout.write(f"\r[{now}] Pending: {len(pending):3d} (peak: {peak_pending:3d}) | "
                        f"Running: {len(running):3d} (peak: {peak_running:3d})   ")
        sys.stdout.flush()
        
        time.sleep(interval)
    
    print()
    return peak_pending, peak_running


def stress_test_tasks():
    """Main stress test - trigger all available tasks rapidly."""
    print(c("\n" + "=" * 70, Colors.HEADER))
    print(c("  BAZARR JOBS QUEUE - IRL STRESS TEST", Colors.HEADER + Colors.BOLD))
    print(c("=" * 70 + "\n", Colors.HEADER))
    
    # Check if Bazarr is running
    print(c("🔍 Checking Bazarr connection...", Colors.OKCYAN))
    try:
        resp = requests.get(f"{BAZARR_URL}/api/system/status", headers=get_headers(), timeout=5)
        if resp.status_code != 200:
            print(c(f"❌ Cannot connect to Bazarr at {BAZARR_URL} (status: {resp.status_code})", Colors.FAIL))
            print("   Make sure Bazarr is running and accessible.")
            return
    except requests.exceptions.ConnectionError:
        print(c(f"❌ Cannot connect to Bazarr at {BAZARR_URL}", Colors.FAIL))
        print("   Make sure Bazarr is running and accessible.")
        return
    
    print(c(f"✅ Connected to Bazarr at {BAZARR_URL}\n", Colors.OKGREEN))
    
    # Get current settings
    settings = get_settings()
    general = settings.get("general", {})
    concurrent_jobs = general.get("concurrent_jobs", "unknown")
    print(f"  Current concurrent_jobs setting: {c(concurrent_jobs, Colors.OKBLUE)}")
    
    # Show initial queue status
    print(c("\n📋 Initial Queue Status:", Colors.HEADER))
    print_queue_status()
    
    # Get available tasks
    print(c("\n📝 Getting available tasks...", Colors.OKCYAN))
    tasks = get_tasks()
    if not tasks:
        print(c("❌ No tasks found!", Colors.FAIL))
        return
    
    print(f"  Found {c(len(tasks), Colors.OKBLUE)} tasks:")
    for task in tasks:
        running = "🟢 running" if task.get("job_running") else "⚪ idle"
        print(f"    - {task['name']} [{task['job_id']}] {running}")
    
    # Start queue monitor in background
    stop_monitor = threading.Event()
    monitor_thread = threading.Thread(target=monitor_queue, args=(stop_monitor,), daemon=True)
    monitor_thread.start()
    
    # Trigger all tasks multiple times
    print(c("\n🚀 STRESS TEST: Triggering all tasks 3 times each...", Colors.WARNING))
    print(c("   Watch the Jobs Manager in the UI!", Colors.OKCYAN))
    time.sleep(2)
    
    triggered = 0
    for round_num in range(3):
        print(f"\n  Round {round_num + 1}/3:")
        for task in tasks:
            task_id = task["job_id"]
            if trigger_task(task_id):
                triggered += 1
                print(f"    ✓ Triggered: {task['name']}")
            else:
                print(f"    ✗ Failed: {task['name']}")
            time.sleep(0.1)  # Small delay between triggers
        time.sleep(0.5)  # Delay between rounds
    
    print(c(f"\n✅ Triggered {triggered} task executions", Colors.OKGREEN))
    
    # Monitor for a bit
    print(c("\n⏳ Monitoring queue for 30 seconds...", Colors.OKCYAN))
    print("   Press Ctrl+C to stop early\n")
    
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        print("\n   Stopping early...")
    
    stop_monitor.set()
    monitor_thread.join(timeout=2)
    
    # Final status
    print(c("\n📊 Final Queue Status:", Colors.HEADER))
    print_queue_status()
    
    print(c("\n✅ Stress test complete!", Colors.OKGREEN))
    print("   Check the Bazarr UI to see the jobs queue behavior.\n")


def rapid_fire_test():
    """Rapidly trigger the same task many times to test deduplication."""
    print(c("\n" + "=" * 70, Colors.HEADER))
    print(c("  RAPID FIRE TEST - Testing Job Deduplication", Colors.HEADER + Colors.BOLD))
    print(c("=" * 70 + "\n", Colors.HEADER))
    
    tasks = get_tasks()
    if not tasks:
        print(c("❌ No tasks found!", Colors.FAIL))
        return
    
    # Pick the first task
    task = tasks[0]
    print(f"Using task: {c(task['name'], Colors.OKBLUE)}")
    
    # Trigger it 50 times rapidly
    print(c("\n🔥 Triggering same task 50 times in rapid succession...", Colors.WARNING))
    
    start_time = time.time()
    success = 0
    for i in range(50):
        if trigger_task(task["job_id"]):
            success += 1
        sys.stdout.write(f"\r  Triggered: {i+1}/50")
        sys.stdout.flush()
    
    elapsed = time.time() - start_time
    print(f"\n\n  Completed in {elapsed:.2f}s ({50/elapsed:.1f} triggers/sec)")
    print(f"  Success rate: {success}/50")
    
    # Check queue
    time.sleep(1)
    pending = get_jobs("pending")
    running = get_jobs("running")
    print(f"\n  Jobs in queue: {len(pending)} pending, {len(running)} running")
    print("  (Should be significantly less than 50 due to deduplication)")


if __name__ == "__main__":
    print(c("""
╔════════════════════════════════════════════════════════════════════╗
║                    BAZARR IRL STRESS TEST                          ║
║                                                                    ║
║  This will trigger multiple tasks on your running Bazarr instance  ║
║  Open the Bazarr UI -> System -> Jobs Manager to watch the queue   ║
╚════════════════════════════════════════════════════════════════════╝
    """, Colors.HEADER))
    
    print("Choose a test:")
    print("  1. Stress Test (trigger all tasks 3x)")
    print("  2. Rapid Fire (trigger same task 50x)")
    print("  3. Both tests")
    print()
    
    choice = input("Enter choice (1/2/3) or press Enter for 1: ").strip() or "1"
    
    if choice == "1":
        stress_test_tasks()
    elif choice == "2":
        rapid_fire_test()
    elif choice == "3":
        stress_test_tasks()
        print("\n" + "=" * 70 + "\n")
        rapid_fire_test()
    else:
        print("Invalid choice")
