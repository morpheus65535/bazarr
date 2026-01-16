#!/usr/bin/env python3
"""
Real IRL Stress Test for Bazarr Jobs Queue

Sends actual jobs through the API to a running Bazarr instance:
- 40 long jobs (90 seconds) - routed to long queue
- 60 short jobs (10 seconds) - routed to short queue
- 20 short jobs that will be demoted (65 seconds) - start in short, demote to long

Watch the Jobs Manager in the UI to see real queue behavior!
"""

import requests
import time
import sys
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Configuration
BAZARR_URL = "http://localhost:6767"
API_KEY = "bazarr"

# Job configuration - YOUR EXACT REQUIREMENTS
JOB_MIX = [
    {"count": 40, "name": "Long Job", "duration": 90, "job_type": "long"},      # Known long -> long queue
    {"count": 60, "name": "Short Job", "duration": 10, "job_type": "short"},    # Short -> short queue
    {"count": 20, "name": "Will Demote", "duration": 65, "job_type": "short"},  # Starts short, gets demoted
]

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
    return {"Content-Type": "application/json", "X-API-KEY": API_KEY}

def get_settings():
    """Get current concurrent_jobs setting."""
    try:
        # Read from config file since API doesn't expose it yet
        import yaml
        with open('/workspaces/bazarr/data/config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return {
            'concurrent_jobs': config.get('general', {}).get('concurrent_jobs', 'unknown'),
            'long_job_threshold': config.get('general', {}).get('long_job_threshold', 15)
        }
    except:
        return {'concurrent_jobs': 'unknown', 'long_job_threshold': 15}

def create_test_job(job_name, duration, job_type):
    """Create a test job via API."""
    try:
        resp = requests.post(
            f"{BAZARR_URL}/api/system/jobs",
            headers=get_headers(),
            params={
                "job_name": job_name,
                "duration": duration,
                "job_type": job_type
            },
            timeout=10
        )
        if resp.status_code == 201:
            return resp.json()
        else:
            print(c(f"Failed to create job: {resp.status_code} - {resp.text[:100]}", Colors.FAIL))
            return None
    except Exception as e:
        print(c(f"Error creating job: {e}", Colors.FAIL))
        return None

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
    except:
        return []

def clear_completed():
    """Clear completed jobs queue."""
    try:
        resp = requests.patch(
            f"{BAZARR_URL}/api/system/jobs",
            headers=get_headers(),
            params={"queueName": "completed"},
            timeout=10
        )
        return resp.status_code == 204
    except:
        return False

def monitor_queue(stop_event):
    """Monitor queue status in real-time."""
    stats = {
        'peak_pending': 0,
        'peak_running': 0,
        'peak_short': 0,
        'peak_long': 0,
    }
    
    while not stop_event.is_set():
        pending = get_jobs("pending")
        running = get_jobs("running")
        completed = get_jobs("completed")
        
        # Count by type in running
        running_short = sum(1 for j in running if not j.get('job_name', '').startswith('Sync with'))
        running_long = sum(1 for j in running if j.get('job_name', '').startswith('Sync with'))
        
        stats['peak_pending'] = max(stats['peak_pending'], len(pending))
        stats['peak_running'] = max(stats['peak_running'], len(running))
        stats['peak_short'] = max(stats['peak_short'], running_short)
        stats['peak_long'] = max(stats['peak_long'], running_long)
        
        now = datetime.now().strftime("%H:%M:%S")
        sys.stdout.write(
            f"\r[{now}] "
            f"Pending: {len(pending):3d} | "
            f"Running: {len(running):2d} (short:{running_short} long:{running_long}) | "
            f"Completed: {len(completed):3d}   "
        )
        sys.stdout.flush()
        
        time.sleep(0.5)
    
    return stats

def run_stress_test():
    """Main stress test."""
    print(c("\n" + "=" * 80, Colors.HEADER))
    print(c("  BAZARR JOBS QUEUE - REAL IRL STRESS TEST", Colors.HEADER + Colors.BOLD))
    print(c("=" * 80 + "\n", Colors.HEADER))
    
    # Check connection
    print(c("🔍 Checking Bazarr connection...", Colors.OKCYAN))
    try:
        resp = requests.get(f"{BAZARR_URL}/api/system/status", headers=get_headers(), timeout=5)
        if resp.status_code != 200:
            print(c(f"❌ Cannot connect (status: {resp.status_code})", Colors.FAIL))
            return
    except requests.exceptions.ConnectionError:
        print(c(f"❌ Cannot connect to Bazarr at {BAZARR_URL}", Colors.FAIL))
        return
    
    print(c(f"✅ Connected to Bazarr\n", Colors.OKGREEN))
    
    # Get settings and show limits
    settings = get_settings()
    concurrent = settings.get('concurrent_jobs', 'unknown')
    threshold = settings.get('long_job_threshold', 15)
    
    if concurrent != 'unknown':
        max_total = max(2, concurrent)
        max_short = max(1, max_total // 2)
        max_long = max(1, max_short // 2)
        room = max_total - max_short - max_long
        
        print(c("📊 Current Settings:", Colors.HEADER))
        print(f"  concurrent_jobs (from UI): {c(concurrent, Colors.OKBLUE)}")
        print(f"  long_job_threshold: {c(f'{threshold} min', Colors.OKBLUE)}")
        print()
        print(c("  Calculated Limits:", Colors.HEADER))
        print(f"    Max Concurrent (total): {c(max_total, Colors.OKBLUE)}")
        print(f"    Max Short:              {c(max_short, Colors.OKBLUE)}")
        print(f"    Max Long:               {c(max_long, Colors.OKBLUE)}")
        print(f"    Room for demotion:      {c(room, Colors.WARNING if room == 0 else Colors.OKBLUE)}")
    print()
    
    # Show job mix
    print(c("📋 Job Mix to Send:", Colors.HEADER))
    total_jobs = 0
    total_time_estimate = 0
    for job_config in JOB_MIX:
        count = job_config["count"]
        name = job_config["name"]
        duration = job_config["duration"]
        job_type = job_config["job_type"]
        total_jobs += count
        
        if job_type == "long":
            queue = "→ LONG queue"
        elif duration > threshold * 60:
            queue = "→ SHORT queue (will DEMOTE to long)"
        else:
            queue = "→ SHORT queue"
        
        print(f"  {count:3d}x {name:15s} ({duration:3d}s) {queue}")
    
    print(f"\n  Total: {c(total_jobs, Colors.OKBLUE)} jobs")
    print()
    
    # Clear completed queue
    print(c("🧹 Clearing completed jobs queue...", Colors.OKCYAN))
    clear_completed()
    
    # Show initial state
    print(c("\n📊 Initial Queue State:", Colors.HEADER))
    for status in ['pending', 'running', 'completed']:
        jobs = get_jobs(status)
        print(f"  {status}: {len(jobs)}")
    print()
    
    # Start monitor thread
    stop_monitor = threading.Event()
    monitor_thread = threading.Thread(target=monitor_queue, args=(stop_monitor,), daemon=True)
    monitor_thread.start()
    
    # Build a mixed list of all jobs to send
    all_jobs_to_send = []
    for job_config in JOB_MIX:
        count = job_config["count"]
        name = job_config["name"]
        duration = job_config["duration"]
        job_type = job_config["job_type"]
        
        for i in range(count):
            all_jobs_to_send.append({
                "job_name": f"{name} #{i+1}",
                "duration": duration,
                "job_type": job_type,
                "category": name  # For tracking
            })
    
    # Shuffle to interleave all job types randomly
    import random
    random.shuffle(all_jobs_to_send)
    
    # Send all jobs in mixed order
    print(c(f"\n🚀 SENDING {total_jobs} JOBS (MIXED ORDER)...", Colors.WARNING + Colors.BOLD))
    print(c("   Jobs are shuffled to simulate real-world mixed arrivals!", Colors.OKCYAN))
    print(c("   Watch the Jobs Manager in the Bazarr UI!", Colors.OKCYAN))
    time.sleep(2)
    
    start_time = time.time()
    jobs_created = []
    
    # Track what we're sending
    sent_counts = {"Long Job": 0, "Short Job": 0, "Will Demote": 0}
    
    print(f"\n  Sending {len(all_jobs_to_send)} mixed jobs...")
    for i, job in enumerate(all_jobs_to_send):
        result = create_test_job(job["job_name"], job["duration"], job["job_type"])
        if result:
            jobs_created.append(result)
            sent_counts[job["category"]] = sent_counts.get(job["category"], 0) + 1
        
        # Progress update every 20 jobs
        if (i + 1) % 20 == 0:
            print(f"    Sent {i+1}/{len(all_jobs_to_send)} jobs...")
        
        time.sleep(0.05)  # Small delay to not overwhelm
    
    queue_time = time.time() - start_time
    print(c(f"\n✅ Sent {len(jobs_created)} jobs in {queue_time:.1f}s", Colors.OKGREEN))
    print(f"   Long: {sent_counts.get('Long Job', 0)}, Short: {sent_counts.get('Short Job', 0)}, "
          f"Will Demote: {sent_counts.get('Will Demote', 0)}")
    
    # Wait for all to complete
    print(c("\n⏳ Waiting for all jobs to complete...", Colors.OKCYAN))
    print("   (Press Ctrl+C to stop monitoring early)\n")
    
    try:
        while True:
            pending = get_jobs("pending")
            running = get_jobs("running")
            
            if len(pending) == 0 and len(running) == 0:
                break
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n   Stopped monitoring (jobs still running in background)")
    
    stop_monitor.set()
    time.sleep(1)
    
    # Final stats
    total_time = time.time() - start_time
    completed = get_jobs("completed")
    
    print(c("\n\n" + "=" * 80, Colors.HEADER))
    print(c("  FINAL RESULTS", Colors.HEADER + Colors.BOLD))
    print(c("=" * 80, Colors.HEADER))
    
    print(f"\n  Jobs created:   {len(jobs_created)}")
    print(f"  Jobs completed: {len(completed)}")
    print(f"  Total time:     {total_time:.1f}s")
    
    if len(completed) > 0:
        # Count by type
        long_completed = sum(1 for j in completed if j.get('job_name', '').startswith('Sync with'))
        short_completed = len(completed) - long_completed
        print(f"\n  Short completions: {short_completed}")
        print(f"  Long completions:  {long_completed}")
    
    print(c("\n✅ Test complete! Check Bazarr logs for demotion messages.", Colors.OKGREEN))
    print()

if __name__ == "__main__":
    run_stress_test()
