#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import base64
import binascii
import errno
import imghdr
import random
import os
import select
import socket
import sys
import threading
import time

try:
    from json import read as json_decode, write as json_encode
except ImportError:
    try:
        from json import loads as json_decode, dumps as json_encode
    except ImportError:
        from simplejson import loads as json_decode, dumps as json_encode

try:
    from urllib2 import build_opener, HTTPRedirectHandler, Request, HTTPError
    from urllib import urlencode, urlopen
except ImportError:
    from urllib.request import build_opener, HTTPRedirectHandler, Request, urlopen
    from urllib.error import HTTPError
    from urllib.parse import urlencode

# API version and unique software ID
API_VERSION = 'DBC/Python v4.0.11'
SOFTWARE_VENDOR_ID = 0

# Default CAPTCHA timeout and decode() polling interval
DEFAULT_TIMEOUT = 60
POLLS_INTERVAL = 5

# Base HTTP API url
HTTP_BASE_URL = 'http://api.deathbycaptcha.com/api'

# Preferred HTTP API server's response content type, do not change
HTTP_RESPONSE_TYPE = 'application/json'

# Socket API server's host & ports range
SOCKET_HOST = 'api.deathbycaptcha.com'
SOCKET_PORTS = range(8123, 8131)

class AccessDeniedException(Exception):
    pass

class Client(object):
    """Death by Captcha API Client"""

    def __init__(self, username, password):
        self.is_verbose = False
        self.userpwd = {'username': username,
                        'password': password}

    def _load_file(self, captcha):
        if hasattr(captcha, 'read'):
            raw_captcha = captcha.read()
        elif isinstance(captcha, bytearray):
            raw_captcha = captcha
        elif os.path.isfile(captcha):
            raw_captcha = ''
            try:
                f = open(captcha, 'rb')
            except Exception as e:
                raise e
            else:
                raw_captcha = f.read()
                f.close()
        else:
            f_stream = urlopen(captcha)
            raw_captcha = f_stream.read()

        if not len(raw_captcha):
            raise ValueError('CAPTCHA image is empty')
        elif imghdr.what(None, raw_captcha) is None:
            raise TypeError('Unknown CAPTCHA image type')
        else:
            return raw_captcha

    def _log(self, cmd, msg=''):
        if self.is_verbose:
            print('%d %s %s' % (time.time(), cmd, msg.rstrip()))
        return self

    def close(self):
        pass

    def connect(self):
        pass

    def get_user(self):
        """Fetch the user's details dict -- balance, rate and banned status."""
        raise NotImplemented()

    def get_balance(self):
        """Fetch the user's balance (in US cents)."""
        return self.get_user().get('balance')

    def get_captcha(self, cid):
        """Fetch a CAPTCHA details dict -- its ID, text and correctness."""
        raise NotImplemented()

    def get_text(self, cid):
        """Fetch a CAPTCHA text."""
        return self.get_captcha(cid).get('text') or None

    def report(self, cid):
        """Report a CAPTCHA as incorrectly solved."""
        raise NotImplemented()

    def remove(self, cid):
        """Remove an unsolved CAPTCHA."""
        raise NotImplemented()

    def upload(self, captcha):
        """Upload a CAPTCHA.

        Accepts file names and file-like objects.  Returns CAPTCHA details
        dict on success.

        """
        raise NotImplemented()

    def decode(self, captcha, timeout=DEFAULT_TIMEOUT):
        """Try to solve a CAPTCHA.

        See Client.upload() for arguments details.

        Uploads a CAPTCHA, polls for its status periodically with arbitrary
        timeout (in seconds), returns CAPTCHA details if (correctly) solved.

        """
        deadline = time.time() + (max(0, timeout) or DEFAULT_TIMEOUT)
        c = self.upload(captcha)
        if c:
            while deadline > time.time() and not c.get('text'):
                time.sleep(POLLS_INTERVAL)
                c = self.get_captcha(c['captcha'])
            if c.get('text') and c.get('is_correct'):
                return c

class HttpClient(Client):
    """Death by Captcha HTTP API client."""

    def __init__(self, *args):
        Client.__init__(self, *args)
        self.opener = build_opener(HTTPRedirectHandler())

    def _call(self, cmd, payload=None, headers=None):
        if headers is None:
            headers = {}
        headers['Accept'] = HTTP_RESPONSE_TYPE
        headers['User-Agent'] = API_VERSION
        if hasattr(payload, 'items'):
            payload = urlencode(payload)
            self._log('SEND', '%s %d %s' % (cmd, len(payload), payload))
        if payload is not None:
            headers['Content-Length'] = len(payload)
        try:
            response = self.opener.open(Request(
                HTTP_BASE_URL + '/' + cmd.strip('/'),
                data=payload,
                headers=headers
            )).read()
        except HTTPError as e:
            if 403 == e.code:
                raise AccessDeniedException(
                    'Access denied, please check your credentials and/or balance')
            elif 400 == e.code or 413 == e.code:
                raise ValueError("CAPTCHA was rejected by the service, check if it's a valid image")
        else:
            self._log('RECV', '%d %s' % (len(response), response))
            try:
                return json_decode(response)
            except Exception:
                raise RuntimeError('Invalid API response')
        return {}

    def get_user(self):
        return self._call('user', self.userpwd.copy()) or {'user': 0}

    def get_captcha(self, cid):
        return self._call('captcha/%d' % cid) or {'captcha': 0}

    def report(self, cid):
        return not self._call('captcha/%d/report' % cid,
                              self.userpwd.copy()).get('is_correct')

    def remove(self, cid):
        return not self._call('captcha/%d/remove' % cid,
                              self.userpwd.copy()).get('captcha')

    def upload(self, captcha):
        boundary = binascii.hexlify(os.urandom(16))
        data = self.userpwd.copy()
        data['swid'] = SOFTWARE_VENDOR_ID
        body = '\r\n'.join(('\r\n'.join(('--%s' % boundary,
                                         'Content-Disposition: form-data; name="%s"' % k,
                                         'Content-Type: text/plain',
                                         'Content-Length: %d' % len(str(v)),
                                         '',
                                         str(v))))
                           for k, v in data.items())
        captcha = self._load_file(captcha)
        body += '\r\n'.join(('',
                             '--%s' % boundary,
                             'Content-Disposition: form-data; name="captchafile"; filename="captcha"',
                             'Content-Type: application/octet-stream',
                             'Content-Length: %d' % len(captcha),
                             '',
                             captcha,
                             '--%s--' % boundary,
                             ''))
        response = self._call('captcha', body, {
            'Content-Type': 'multipart/form-data; boundary="%s"' % boundary
        }) or {}
        if response.get('captcha'):
            return response

class SocketClient(Client):
    """Death by Captcha socket API client."""

    TERMINATOR = '\r\n'

    def __init__(self, *args):
        Client.__init__(self, *args)
        self.socket_lock = threading.Lock()
        self.socket = None

    def close(self):
        if self.socket:
            self._log('CLOSE')
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass
            finally:
                self.socket.close()
                self.socket = None

    def connect(self):
        if not self.socket:
            self._log('CONN')
            host = (socket.gethostbyname(SOCKET_HOST),
                    random.choice(SOCKET_PORTS))
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(0)
            try:
                self.socket.connect(host)
            except socket.error as e:
                if errno.EINPROGRESS == e[0]:
                    pass
                else:
                    self.close()
                    raise e
        return self.socket

    def __del__(self):
        self.close()

    def _sendrecv(self, sock, buf):
        self._log('SEND', buf)
        fds = [sock]
        buf += self.TERMINATOR
        response = ''
        while True:
            rd, wr, ex = select.select((not buf and fds) or [],
                                       (buf and fds) or [],
                                       fds,
                                       POLLS_INTERVAL)
            if ex:
                raise IOError('select() failed')
            try:
                if wr:
                    while buf:
                        buf = buf[wr[0].send(buf):]
                elif rd:
                    while True:
                        s = rd[0].recv(256)
                        if not s:
                            raise IOError('recv(): connection lost')
                        else:
                            response += s
            except socket.error as e:
                if e[0] not in (errno.EAGAIN, errno.EINPROGRESS):
                    raise e
            if response.endswith(self.TERMINATOR):
                self._log('RECV', response)
                return response.rstrip(self.TERMINATOR)
        raise IOError('send/recv timed out')

    def _call(self, cmd, data=None):
        if data is None:
            data = {}
        data['cmd'] = cmd
        data['version'] = API_VERSION
        request = json_encode(data)

        response = None
        for i in range(2):
            self.socket_lock.acquire()
            try:
                sock = self.connect()
                response = self._sendrecv(sock, request)
            except IOError as e:
                sys.stderr.write(str(e) + "\n")
                self.close()
            except socket.error as e:
                sys.stderr.write(str(e) + "\n")
                self.close()
                raise IOError('Connection refused')
            else:
                break
            finally:
                self.socket_lock.release()

        try:
            if response is None:
                raise IOError('Connection lost timed out during API request')
            try:
                response = json_decode(response)
            except Exception:
                raise RuntimeError('Invalid API response')
            if 'error' in response:
                error = response['error']
                if 'not-logged-in' == error:
                    raise AccessDeniedException('Access denied, check your credentials')
                elif 'banned' == error:
                    raise AccessDeniedException('Access denied, account is suspended')
                elif 'insufficient-funds' == error:
                    raise AccessDeniedException('CAPTCHA was rejected due to low balance')
                elif 'invalid-captcha' == error:
                    raise ValueError('CAPTCHA is not a valid image')
                elif 'service-overload' == error:
                    raise ValueError(
                        'CAPTCHA was rejected due to service overload, try again later')
                else:
                    raise RuntimeError('API server error occured: %s' % error)
        except Exception as e:
            self.socket_lock.acquire()
            self.close()
            self.socket_lock.release()
            raise e
        else:
            return response

    def get_user(self):
        return self._call('user', self.userpwd.copy()) or {'user': 0}

    def get_captcha(self, cid):
        return self._call('captcha', {'captcha': cid}) or {'captcha': 0}

    def upload(self, captcha):
        data = self.userpwd.copy()
        data['captcha'] = base64.b64encode(self._load_file(captcha))
        response = self._call('upload', data)
        if response.get('captcha'):
            return dict((k, response.get(k)) for k in ('captcha', 'text', 'is_correct'))

    def report(self, cid):
        data = self.userpwd.copy()
        data['captcha'] = cid
        return not self._call('report', data).get('is_correct')

    def remove(self, cid):
        data = self.userpwd.copy()
        data['captcha'] = cid
        return not self._call('remove', data).get('captcha')

if '__main__' == __name__:
    import sys

    # Put your DBC username & password here:
    #client = HttpClient(sys.argv[1], sys.argv[2])
    client = SocketClient(sys.argv[1], sys.argv[2])
    client.is_verbose = True

    print('Your balance is %s US cents' % client.get_balance())

    for fn in sys.argv[3:]:
        try:
            # Put your CAPTCHA image file name or file-like object, and optional
            # solving timeout (in seconds) here:
            captcha = client.decode(fn, DEFAULT_TIMEOUT)
        except Exception as e:
            sys.stderr.write('Failed uploading CAPTCHA: %s\n' % (e, ))
            captcha = None

        if captcha:
            print('CAPTCHA %d solved: %s' % (captcha['captcha'], captcha['text']))

            # Report as incorrectly solved if needed.  Make sure the CAPTCHA was
            # in fact incorrectly solved!
            try:
                client.report(captcha['captcha'])
            except Exception as e:
                sys.stderr.write('Failed reporting CAPTCHA: %s\n' % (e, ))
