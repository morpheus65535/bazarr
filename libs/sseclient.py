#!/usr/bin/env python
"""client library for iterating over http Server Sent Event (SSE) streams"""
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

import codecs
import re
import time
import warnings

import six

import requests

__version__ = '0.0.27'

# Technically, we should support streams that mix line endings.  This regex,
# however, assumes that a system will provide consistent line endings.
end_of_field = re.compile(r'\r\n\r\n|\r\r|\n\n')


class SSEClient(object):
    def __init__(self, url, last_id=None, retry=3000, session=None, chunk_size=1024, **kwargs):
        self.url = url
        self.last_id = last_id
        self.retry = retry
        self.chunk_size = chunk_size

        # Optional support for passing in a requests.Session()
        self.session = session

        # Any extra kwargs will be fed into the requests.get call later.
        self.requests_kwargs = kwargs

        # The SSE spec requires making requests with Cache-Control: nocache
        if 'headers' not in self.requests_kwargs:
            self.requests_kwargs['headers'] = {}
        self.requests_kwargs['headers']['Cache-Control'] = 'no-cache'

        # The 'Accept' header is not required, but explicit > implicit
        self.requests_kwargs['headers']['Accept'] = 'text/event-stream'

        # Keep data here as it streams in
        self.buf = ''

        self._connect()

    def _connect(self):
        if self.last_id:
            self.requests_kwargs['headers']['Last-Event-ID'] = self.last_id

        # Use session if set.  Otherwise fall back to requests module.
        requester = self.session or requests
        self.resp = requester.get(self.url, stream=True, **self.requests_kwargs)
        self.resp_iterator = self.iter_content()
        encoding = self.resp.encoding or self.resp.apparent_encoding
        self.decoder = codecs.getincrementaldecoder(encoding)(errors='replace')

        # TODO: Ensure we're handling redirects.  Might also stick the 'origin'
        # attribute on Events like the Javascript spec requires.
        self.resp.raise_for_status()

    def iter_content(self):
        def generate():
            while True:
                if hasattr(self.resp.raw, '_fp') and \
                        hasattr(self.resp.raw._fp, 'fp') and \
                        hasattr(self.resp.raw._fp.fp, 'read1'):
                    chunk = self.resp.raw._fp.fp.read1(self.chunk_size)
                else:
                    # _fp is not available, this means that we cannot use short
                    # reads and this will block until the full chunk size is
                    # actually read
                    chunk = self.resp.raw.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk

        return generate()

    def _event_complete(self):
        return re.search(end_of_field, self.buf) is not None

    def __iter__(self):
        return self

    def __next__(self):
        while not self._event_complete():
            try:
                next_chunk = next(self.resp_iterator)
                if not next_chunk:
                    raise EOFError()
                self.buf += self.decoder.decode(next_chunk)

            except (StopIteration, requests.RequestException, EOFError, six.moves.http_client.IncompleteRead) as e:
                print(e)
                time.sleep(self.retry / 1000.0)
                self._connect()

                # The SSE spec only supports resuming from a whole message, so
                # if we have half a message we should throw it out.
                head, sep, tail = self.buf.rpartition('\n')
                self.buf = head + sep
                continue

        # Split the complete event (up to the end_of_field) into event_string,
        # and retain anything after the current complete event in self.buf
        # for next time.
        (event_string, self.buf) = re.split(end_of_field, self.buf, maxsplit=1)
        msg = Event.parse(event_string)

        # If the server requests a specific retry delay, we need to honor it.
        if msg.retry:
            self.retry = msg.retry

        # last_id should only be set if included in the message.  It's not
        # forgotten if a message omits it.
        if msg.id:
            self.last_id = msg.id

        return msg

    if six.PY2:
        next = __next__


class Event(object):

    sse_line_pattern = re.compile('(?P<name>[^:]*):?( ?(?P<value>.*))?')

    def __init__(self, data='', event='message', id=None, retry=None):
        assert isinstance(data, six.string_types), "Data must be text"
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry

    def dump(self):
        lines = []
        if self.id:
            lines.append('id: %s' % self.id)

        # Only include an event line if it's not the default already.
        if self.event != 'message':
            lines.append('event: %s' % self.event)

        if self.retry:
            lines.append('retry: %s' % self.retry)

        lines.extend('data: %s' % d for d in self.data.split('\n'))
        return '\n'.join(lines) + '\n\n'

    @classmethod
    def parse(cls, raw):
        """
        Given a possibly-multiline string representing an SSE message, parse it
        and return a Event object.
        """
        msg = cls()
        for line in raw.splitlines():
            m = cls.sse_line_pattern.match(line)
            if m is None:
                # Malformed line.  Discard but warn.
                warnings.warn('Invalid SSE line: "%s"' % line, SyntaxWarning)
                continue

            name = m.group('name')
            if name == '':
                # line began with a ":", so is a comment.  Ignore
                continue
            value = m.group('value')

            if name == 'data':
                # If we already have some data, then join to it with a newline.
                # Else this is it.
                if msg.data:
                    msg.data = '%s\n%s' % (msg.data, value)
                else:
                    msg.data = value
            elif name == 'event':
                msg.event = value
            elif name == 'id':
                msg.id = value
            elif name == 'retry':
                msg.retry = int(value)

        return msg

    def __str__(self):
        return self.data
