# coding=utf-8

"""State that the full league sync job writes and the event stream reads.

The jobs queue imports a job by its file path, as bazarr.sportarr.sync.leagues,
while the rest of Bazarr imports sportarr.sync.leagues. Those are two module
objects with their own globals. This module is always imported by its absolute
name, sportarr.sync.state, so both copies of the job share one state. Never
import it relatively.
"""

# When the last full league sync that read every league and every event list
# started, on the monotonic clock. A change that was skipped before this time
# is covered.
last_complete_sync_started_at = 0.0
# When the last full league sync started, complete or not.
last_sync_started_at = 0.0
# Why the last full league sync did not read everything, or None.
last_incomplete_sync_reason = None
