SignalR reconnect regression tests
=================================

Run from the repository root using Bazarr's bundled dependencies:

    PYTHONPATH=custom_libs:libs python -m unittest discover -s custom_libs/signalrcore/tests -p 'test_*.py'

The manual Linux probe implements Radarr HTTP negotiation, WebSocket upgrade
and the SignalR JSON handshake on loopback. It loads the actual Radarr client
class and bundled transport without loading production configuration or the
database. UI notifications and scheduling are stubbed. Run each scenario in a
separate process because the original retry threads outlive stop():

    python custom_libs/signalrcore/tests/reproduce_radarr_outage.py --mode outage --duration 8
    python custom_libs/signalrcore/tests/reproduce_radarr_outage.py --mode refused --duration 5
    python custom_libs/signalrcore/tests/reproduce_radarr_outage.py --mode flap --duration 5
    python custom_libs/signalrcore/tests/reproduce_radarr_outage.py --mode cold --duration 5
    python custom_libs/signalrcore/tests/reproduce_radarr_outage.py --real-time --duration 20

Use --repo to test another checkout, including v1.3.1. Default timers are
accelerated to 0.05s for checker polling/keepalive and 0.3s for deferred retries;
--real-time preserves the configured production timers. The probe reports
per-second /proc thread counts, RSS, virtual size, FDs and process CPU time.
It separately counts deferred retry workers. Total counts include the in-process
mock server. The safety cap is 180 Python threads. This is a short controlled
probe, not a host PID exhaustion or 12-hour endurance test.

Before the fix, v1.3.1 grew from two threads to 123 (119 deferred retry workers)
in an eight-second accelerated HTTP-503 outage. With production timers it
accumulated 15 retry sleepers in 20 seconds. TCP refusal reproduced the same
mechanism without FD growth. Initial connection failure and rapid successful
reconnections did not demonstrate accumulating retry workers in these runs.

After the fix, the mock outage reconnects on recovery without creating deferred
retry workers; explicit stop while offline stops the checker. Host-wide PID
exhaustion cannot be attributed to Bazarr from these tests alone.
