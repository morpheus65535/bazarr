# coding=utf-8
from __future__ import absolute_import

import math
import time
import threading
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RateLimitEntry:
    name: str
    remaining: int
    reset_in_seconds: int
    captured_at: float = field(default_factory=time.time)

    @property
    def reset_at(self) -> float:
        return self.captured_at + self.reset_in_seconds


@dataclass
class RateLimitPolicy:
    name: str
    quota: int
    window_seconds: int


@dataclass
class _WindowState:
    quota: int
    remaining: int
    reset_at: float

    @property
    def ratio(self) -> float:
        return self.remaining / max(self.quota, 1)


def parse_ratelimit(header: Optional[str]) -> List[RateLimitEntry]:
    """Parse Ratelimit: "default";r=50;t=30, "burst";r=10;t=5"""
    if not header:
        return []
    entries = []
    for item in header.split(","):
        parts = item.strip().split(";")
        if not parts:
            continue
        name = parts[0].strip().strip('"')
        params = {}
        for p in parts[1:]:
            if "=" in p:
                k, v = p.split("=", 1)
                params[k.strip()] = v.strip()
        try:
            entries.append(RateLimitEntry(
                name=name,
                remaining=int(params["r"]),
                reset_in_seconds=int(params["t"]),
            ))
        except (KeyError, ValueError):
            logger.debug("global_rate_limiter: could not parse Ratelimit item %r", item)
    return entries


def parse_policy(header: Optional[str]) -> List[RateLimitPolicy]:
    """Parse Ratelimit-Policy: "burst";q=100;w=60"""
    if not header:
        return []
    policies = []
    for item in header.split(","):
        parts = item.strip().split(";")
        if not parts:
            continue
        name = parts[0].strip().strip('"')
        params = {}
        for p in parts[1:]:
            if "=" in p:
                k, v = p.split("=", 1)
                params[k.strip()] = v.strip()
        try:
            policies.append(RateLimitPolicy(
                name=name,
                quota=int(params["q"]),
                window_seconds=int(params["w"]),
            ))
        except (KeyError, ValueError):
            logger.debug("global_rate_limiter: could not parse Ratelimit-Policy item %r", item)
    return policies


# Sentinel key used for X-RateLimit-* / x-ratelimit-* window state
_X_RATELIMIT_KEY = "x-ratelimit"


def _parse_x_ratelimit_state(headers) -> Optional["_WindowState"]:
    """
    Parse informal X-RateLimit-* headers used by many APIs and GitHub.

    Header names are case-insensitive (requests uses CaseInsensitiveDict).
    X-RateLimit-Reset is an absolute UTC epoch timestamp, unlike Cloudflare's
    relative t= value.

    Covers:
      X-RateLimit-Limit / x-ratelimit-limit
      X-RateLimit-Remaining / x-ratelimit-remaining
      X-RateLimit-Reset / x-ratelimit-reset     (epoch seconds)
      Retry-After                                (seconds, 429 only — handled in http.py)
    """
    remaining_str = headers.get("X-RateLimit-Remaining")
    reset_str = headers.get("X-RateLimit-Reset")
    limit_str = headers.get("X-RateLimit-Limit")

    if remaining_str is None or reset_str is None:
        return None

    try:
        remaining = int(remaining_str)
        reset_at = float(reset_str)
        quota = int(limit_str) if limit_str else max(remaining, 1)
        return _WindowState(quota=quota, remaining=remaining, reset_at=reset_at)
    except (ValueError, TypeError):
        logger.debug("global_rate_limiter: could not parse X-RateLimit-* headers")
        return None


class DomainThrottler:
    """
    Global per-domain rate limit state tracker.

    Parses Ratelimit / Ratelimit-Policy response headers and
    applies proactive throttling before each request so we stay inside the
    quota window.
    """

    def __init__(self):
        # domain -> policy_name -> _WindowState
        self._states: Dict[str, Dict[str, _WindowState]] = {}
        self._lock = threading.Lock()

    def on_response(self, domain: str, response) -> None:
        """Update internal state from response headers."""
        headers = response.headers

        # IETF draft: Ratelimit + Ratelimit-Policy
        entries = parse_ratelimit(headers.get("Ratelimit"))
        policies = {
            p.name: p
            for p in parse_policy(headers.get("Ratelimit-Policy"))
        }

        now = time.time()
        with self._lock:
            domain_states = self._states.setdefault(domain, {})

            for entry in entries:
                policy = policies.get(entry.name)
                if policy is None:
                    continue
                domain_states[entry.name] = _WindowState(
                    quota=policy.quota,
                    remaining=entry.remaining,
                    reset_at=now + entry.reset_in_seconds,
                )

            # Informal X-RateLimit-* / x-ratelimit-* (common APIs + GitHub)
            x_state = _parse_x_ratelimit_state(headers)
            if x_state is not None:
                domain_states[_X_RATELIMIT_KEY] = x_state

    def throttle(self, domain: str) -> None:
        """Block if needed to stay within the most constrained active window."""
        with self._lock:
            states = dict(self._states.get(domain, {}))

        now = time.time()
        for name, state in states.items():
            if now >= state.reset_at:
                # Window already expired — drop stale entry
                with self._lock:
                    self._states.get(domain, {}).pop(name, None)
                continue

            seconds_until_reset = max(state.reset_at - now, 0.1)

            if state.remaining == 0:
                logger.warning(
                    "[%s][%s] quota exhausted, waiting %.1fs for window reset",
                    domain, name, seconds_until_reset,
                )
                time.sleep(seconds_until_reset)
            elif state.ratio < 0.10:
                # Spread the remaining budget evenly across the reset window
                delay = seconds_until_reset / max(state.remaining, 1)
                logger.debug(
                    "[%s][%s] proactive throttle: %d remaining, delay %.3fs",
                    domain, name, state.remaining, delay,
                )
                time.sleep(delay)
            elif state.ratio < 0.25:
                time.sleep(0.2)

    def clear(self, domain: str) -> None:
        with self._lock:
            self._states.pop(domain, None)

    def clear_all(self) -> None:
        with self._lock:
            self._states.clear()


# Module-level singleton shared across all providers / sessions
_throttler = DomainThrottler()


def get_throttler() -> DomainThrottler:
    return _throttler
