# Original work Copyright 2013 Arnaud Porterie
# Modified work Copyright 2016 Frazer McLean
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import collections
import functools
import threading
import time
import sys
from textwrap import dedent

try:
    import asyncio
except ImportError:
    asyncio = None

__author__ = 'Frazer McLean <frazer@frazermclean.co.uk>'
__version__ = '1.2.0.post0'
__license__ = 'Apache'
__description__ = 'Simple python rate limiting object'

PY35 = sys.version_info >= (3, 5)


class RateLimiter(object):
    """Provides rate limiting for an operation with a configurable number of
    requests for a time period.
    """

    def __init__(self, max_calls, period=1.0, callback=None):
        """Initialize a RateLimiter object which enforces as much as max_calls
        operations on period (eventually floating) number of seconds.
        """
        if period <= 0:
            raise ValueError('Rate limiting period should be > 0')
        if max_calls <= 0:
            raise ValueError('Rate limiting number of calls should be > 0')

        # We're using a deque to store the last execution timestamps, not for
        # its maxlen attribute, but to allow constant time front removal.
        self.calls = collections.deque()

        self.period = period
        self.max_calls = max_calls
        self.callback = callback
        self._lock = threading.Lock()
        self._alock = None

        # Lock to protect creation of self._alock
        self._init_lock = threading.Lock()

    def _init_async_lock(self):
        with self._init_lock:
            if self._alock is None:
                self._alock = asyncio.Lock()

    def __call__(self, f):
        """The __call__ function allows the RateLimiter object to be used as a
        regular function decorator.
        """
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            with self:
                return f(*args, **kwargs)
        return wrapped

    def __enter__(self):
        with self._lock:
            # We want to ensure that no more than max_calls were run in the allowed
            # period. For this, we store the last timestamps of each call and run
            # the rate verification upon each __enter__ call.
            if len(self.calls) >= self.max_calls:
                until = time.time() + self.period - self._timespan
                if self.callback:
                    t = threading.Thread(target=self.callback, args=(until,))
                    t.daemon = True
                    t.start()
                sleeptime = until - time.time()
                if sleeptime > 0:
                    time.sleep(sleeptime)
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._lock:
            # Store the last operation timestamp.
            self.calls.append(time.time())

            # Pop the timestamp list front (ie: the older calls) until the sum goes
            # back below the period. This is our 'sliding period' window.
            while self._timespan >= self.period:
                self.calls.popleft()

    if PY35:
        # We have to exec this due to syntax errors on earlier versions.
        aenter_code = dedent("""
            async def __aenter__(self):
                if self._alock is None:
                    self._init_async_lock()
                    
                with await self._alock:
                    # We want to ensure that no more than max_calls were run in the allowed
                    # period. For this, we store the last timestamps of each call and run
                    # the rate verification upon each __enter__ call.
                    if len(self.calls) >= self.max_calls:
                        until = time.time() + self.period - self._timespan
                        if self.callback:
                            asyncio.ensure_future(self.callback(until))
                        sleeptime = until - time.time()
                        if sleeptime > 0:
                            await asyncio.sleep(sleeptime)
                    return self

            """)
        exec(aenter_code)

        __aexit__ = asyncio.coroutine(__exit__)

    @property
    def _timespan(self):
        return self.calls[-1] - self.calls[0]
