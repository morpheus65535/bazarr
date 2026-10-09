# coding=utf-8

import time
import threading
import uuid


_TTL_SECONDS = 3600  # 1 hour


class _SubtitleCache:
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()

    def _purge_expired(self):
        now = time.monotonic()
        expired = []
        for key, entry in self._cache.items():
            try:
                _, expiry = entry
            except (TypeError, ValueError):
                expired.append(key)
                continue
            try:
                is_expired = now >= expiry
            except TypeError:
                expired.append(key)
                continue
            if is_expired:
                expired.append(key)
        for k in expired:
            del self._cache[k]

    def store(self, subtitle):
        """Store a subtitle object and return its cache key (UUID string)."""
        key = str(uuid.uuid4())
        expiry = time.monotonic() + _TTL_SECONDS
        with self._lock:
            self._purge_expired()
            self._cache[key] = (subtitle, expiry)
        return key

    def get(self, key):
        """Return the subtitle object for the given key, or None if not found/expired."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            try:
                subtitle, expiry = entry
            except (TypeError, ValueError):
                # Malformed cache entry
                del self._cache[key]
                return None
            try:
                is_expired = time.monotonic() >= expiry
            except TypeError:
                del self._cache[key]
                return None
            if is_expired:
                del self._cache[key]
                return None
            return subtitle


subtitle_cache = _SubtitleCache()
