#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Death by Captcha HTTP and socket API clients.

There are two types of Death by Captcha (DBC hereinafter) API: HTTP and
socket ones.  Both offer the same functionalily, with the socket API
sporting faster responses and using way less connections.

To access the socket API, use SocketClient class; for the HTTP API, use
HttpClient class.  Both are thread-safe.  SocketClient keeps a persistent
connection opened and serializes all API requests sent through it, thus
it is advised to keep a pool of them if you're script is heavily
multithreaded.

Both SocketClient and HttpClient give you the following methods:

get_user()
    Returns your DBC account details as a dict with the following keys:

    "user": your account numeric ID; if login fails, it will be the only
        item with the value of 0;
    "rate": your CAPTCHA rate, i.e. how much you will be charged for one
        solved CAPTCHA in US cents;
    "balance": your DBC account balance in US cents;
    "is_banned": flag indicating whether your account is suspended or not.

get_balance()
    Returns your DBC account balance in US cents.

get_captcha(cid)
    Returns an uploaded CAPTCHA details as a dict with the following keys:

    "captcha": the CAPTCHA numeric ID; if no such CAPTCHAs found, it will
        be the only item with the value of 0;
    "text": the CAPTCHA text, if solved, otherwise None;
    "is_correct": flag indicating whether the CAPTCHA was solved correctly
        (DBC can detect that in rare cases).

    The only argument `cid` is the CAPTCHA numeric ID.

get_text(cid)
    Returns an uploaded CAPTCHA text (None if not solved).  The only argument
    `cid` is the CAPTCHA numeric ID.

report(cid)
    Reports an incorrectly solved CAPTCHA.  The only argument `cid` is the
    CAPTCHA numeric ID.  Returns True on success, False otherwise.

upload(captcha)
    Uploads a CAPTCHA.  The only argument `captcha` can be either file-like
    object (any object with `read` method defined, actually, so StringIO
    will do), or CAPTCHA image file name.  On successul upload you'll get
    the CAPTCHA details dict (see get_captcha() method).

    NOTE: AT THIS POINT THE UPLOADED CAPTCHA IS NOT SOLVED YET!  You have
    to poll for its status periodically using get_captcha() or get_text()
    method until the CAPTCHA is solved and you get the text.

decode(captcha, timeout=DEFAULT_TIMEOUT)
    A convenient method that uploads a CAPTCHA and polls for its status
    periodically, but no longer than `timeout` (defaults to 60 seconds).
    If solved, you'll get the CAPTCHA details dict (see get_captcha()
    method for details).  See upload() method for details on `captcha`
    argument.

Visit http://www.deathbycaptcha.com/user/api for updates.

"""

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
import urllib
import urllib2
try:
    from json import read as json_decode, write as json_encode
except ImportError:
    try:
        from json import loads as json_decode, dumps as json_encode
    except ImportError:
        from simplejson import loads as json_decode, dumps as json_encode


# API version and unique software ID
API_VERSION = 'DBC/Python v4.6'

# Default CAPTCHA timeout and decode() polling interval
DEFAULT_TIMEOUT = 60
DEFAULT_TOKEN_TIMEOUT = 120
POLLS_INTERVAL = [1, 1, 2, 3, 2, 2, 3, 2, 2]
DFLT_POLL_INTERVAL = 3

# Base HTTP API url
HTTP_BASE_URL = 'http://api.dbcapi.me/api'

# Preferred HTTP API server's response content type, do not change
HTTP_RESPONSE_TYPE = 'application/json'

# Socket API server's host & ports range
SOCKET_HOST = 'api.dbcapi.me'
SOCKET_PORTS = range(8123, 8131)


def _load_image(captcha):
    if hasattr(captcha, 'read'):
        img = captcha.read()
    elif type(captcha) == bytearray:
        img = captcha
    else:
        img = ''
        try:
            captcha_file = open(captcha, 'rb')
        except Exception:
            raise
        else:
            img = captcha_file.read()
            captcha_file.close()
    if not len(img):
        raise ValueError('CAPTCHA image is empty')
    elif imghdr.what(None, img) is None:
        raise TypeError('Unknown CAPTCHA image type')
    else:
        return img


class AccessDeniedException(Exception):
    pass


class Client(object):

    """Death by Captcha API Client."""

    def __init__(self, username, password):
        self.is_verbose = False
        self.userpwd = {'username': username, 'password': password}

    def _log(self, cmd, msg=''):
        if self.is_verbose:
            print '%d %s %s' % (time.time(), cmd, msg.rstrip())
        return self

    def close(self):
        pass

    def connect(self):
        pass

    def get_user(self):
        """Fetch user details -- ID, balance, rate and banned status."""
        raise NotImplementedError()

    def get_balance(self):
        """Fetch user balance (in US cents)."""
        return self.get_user().get('balance')

    def get_captcha(self, cid):
        """Fetch a CAPTCHA details -- ID, text and correctness flag."""
        raise NotImplementedError()

    def get_text(self, cid):
        """Fetch a CAPTCHA text."""
        return self.get_captcha(cid).get('text') or None

    def report(self, cid):
        """Report a CAPTCHA as incorrectly solved."""
        raise NotImplementedError()

    def upload(self, captcha):
        """Upload a CAPTCHA.

        Accepts file names and file-like objects.  Returns CAPTCHA details
        dict on success.

        """
        raise NotImplementedError()

    def decode(self, captcha=None, timeout=None, **kwargs):
        """
        Try to solve a CAPTCHA.

        See Client.upload() for arguments details.

        Uploads a CAPTCHA, polls for its status periodically with arbitrary
        timeout (in seconds), returns CAPTCHA details if (correctly) solved.
        """
        if not timeout:
            if not captcha:
                timeout = DEFAULT_TOKEN_TIMEOUT
            else:
                timeout = DEFAULT_TIMEOUT

        deadline = time.time() + (max(0, timeout) or DEFAULT_TIMEOUT)
        uploaded_captcha = self.upload(captcha, **kwargs)
        if uploaded_captcha:
            intvl_idx = 0  # POLL_INTERVAL index
            while deadline > time.time() and not uploaded_captcha.get('text'):
                intvl, intvl_idx = self._get_poll_interval(intvl_idx)
                time.sleep(intvl)
                pulled = self.get_captcha(uploaded_captcha['captcha'])
                if pulled['captcha'] == uploaded_captcha['captcha']:
                    uploaded_captcha = pulled
            if uploaded_captcha.get('text') and \
                    uploaded_captcha.get('is_correct'):
                return uploaded_captcha

    def _get_poll_interval(self, idx):
        """Returns poll interval and next index depending on index provided"""

        if len(POLLS_INTERVAL) > idx:
            intvl = POLLS_INTERVAL[idx]
        else:
            intvl = DFLT_POLL_INTERVAL
        idx += 1

        return intvl, idx


class HttpClient(Client):

    """Death by Captcha HTTP API client."""

    def __init__(self, *args):
        Client.__init__(self, *args)
        self.opener = urllib2.build_opener(urllib2.HTTPRedirectHandler())

    def _call(self, cmd, payload=None, headers=None):
        if headers is None:
            headers = {}
        headers['Accept'] = HTTP_RESPONSE_TYPE
        headers['User-Agent'] = API_VERSION
        if hasattr(payload, 'items'):
            payload = urllib.urlencode(payload)
            self._log('SEND', '%s %d %s' % (cmd, len(payload), payload))
        else:
            self._log('SEND', '%s' % cmd)
        if payload is not None:
            headers['Content-Length'] = len(payload)
        try:
            response = self.opener.open(urllib2.Request(
                HTTP_BASE_URL + '/' + cmd.strip('/'),
                data=payload,
                headers=headers
            )).read()
        except urllib2.HTTPError, err:
            if 403 == err.code:
                raise AccessDeniedException('Access denied, please check'
                                            ' your credentials and/or balance')
            elif 400 == err.code or 413 == err.code:
                raise ValueError("CAPTCHA was rejected by the service, check"
                                 " if it's a valid image")
            elif 503 == err.code:
                raise OverflowError("CAPTCHA was rejected due to service"
                                    " overload, try again later")
            else:
                raise err
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

    def upload(self, captcha=None, **kwargs):
        boundary = binascii.hexlify(os.urandom(16))
        banner = kwargs.get('banner', '')
        if banner:
            kwargs['banner'] = 'base64:' + base64.b64encode(_load_image(banner))
        body = '\r\n'.join(('\r\n'.join((
            '--%s' % boundary,
            'Content-Disposition: form-data; name="%s"' % k,
            'Content-Type: text/plain',
            'Content-Length: %d' % len(str(v)),
            '',
            str(v)
        ))) for k, v in self.userpwd.items())

        body += '\r\n'.join(('\r\n'.join((
            '--%s' % boundary,
            'Content-Disposition: form-data; name="%s"' % k,
            'Content-Type: text/plain',
            'Content-Length: %d' % len(str(v)),
            '',
            str(v)
        ))) for k, v in kwargs.items())

        if captcha:
            img = _load_image(captcha)
            body += '\r\n'.join((
                '',
                '--%s' % boundary,
                'Content-Disposition: form-data; name="captchafile"; '
                    'filename="captcha"',
                'Content-Type: application/octet-stream',
                'Content-Length: %d' % len(img),
                '',
                img,
                '--%s--' % boundary,
                ''
            ))

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
            except socket.error, err:
                if (err.args[0] not in
                        (errno.EAGAIN, errno.EWOULDBLOCK, errno.EINPROGRESS)):
                    self.close()
                    raise err
        return self.socket

    def __del__(self):
        self.close()

    def _sendrecv(self, sock, buf):
        self._log('SEND', buf)
        fds = [sock]
        buf += self.TERMINATOR
        response = ''
        intvl_idx = 0
        while True:
            intvl, intvl_idx = self._get_poll_interval(intvl_idx)
            rds, wrs, exs = select.select((not buf and fds) or [],
                                          (buf and fds) or [],
                                          fds,
                                          intvl)
            if exs:
                raise IOError('select() failed')
            try:
                if wrs:
                    while buf:
                        buf = buf[wrs[0].send(buf):]
                elif rds:
                    while True:
                        s = rds[0].recv(256)
                        if not s:
                            raise IOError('recv(): connection lost')
                        else:
                            response += s
            except socket.error, err:
                if (err.args[0] not in
                        (errno.EAGAIN, errno.EWOULDBLOCK, errno.EINPROGRESS)):
                    raise err
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
        for _ in range(2):
            if not self.socket and cmd != 'login':
                self._call('login', self.userpwd.copy())
            self.socket_lock.acquire()
            try:
                sock = self.connect()
                response = self._sendrecv(sock, request)
            except IOError, err:
                sys.stderr.write(str(err) + "\n")
                self.close()
            except socket.error, err:
                sys.stderr.write(str(err) + "\n")
                self.close()
                raise IOError('Connection refused')
            else:
                break
            finally:
                self.socket_lock.release()

        if response is None:
            raise IOError('Connection lost or timed out during API request')

        try:
            response = json_decode(response)
        except Exception:
            raise RuntimeError('Invalid API response')

        if not response.get('error'):
            return response

        error = response['error']
        if error in ('not-logged-in', 'invalid-credentials'):
            raise AccessDeniedException('Access denied, check your credentials')
        elif 'banned' == error:
            raise AccessDeniedException('Access denied, account is suspended')
        elif 'insufficient-funds' == error:
            raise AccessDeniedException(
                'CAPTCHA was rejected due to low balance')
        elif 'invalid-captcha' == error:
            raise ValueError('CAPTCHA is not a valid image')
        elif 'service-overload' == error:
            raise OverflowError(
                'CAPTCHA was rejected due to service overload, try again later')
        else:
            self.socket_lock.acquire()
            self.close()
            self.socket_lock.release()
            raise RuntimeError('API server error occured: %s' % error)

    def get_user(self):
        return self._call('user') or {'user': 0}

    def get_captcha(self, cid):
        return self._call('captcha', {'captcha': cid}) or {'captcha': 0}

    def upload(self, captcha=None, **kwargs):
        data = {}
        if captcha:
            data['captcha'] = base64.b64encode(_load_image(captcha))
        if kwargs:
            banner = kwargs.get('banner', '')
            if banner:
                kwargs['banner'] = base64.b64encode(_load_image(banner))
            data.update(kwargs)
        response = self._call('upload', data)
        if response.get('captcha'):
            uploaded_captcha = dict(
                (k, response.get(k))
                for k in ('captcha', 'text', 'is_correct')
            )
            if not uploaded_captcha['text']:
                uploaded_captcha['text'] = None
            return uploaded_captcha

    def report(self, cid):
        return not self._call('report', {'captcha': cid}).get('is_correct')


if '__main__' == __name__:
    # Put your DBC username & password here:
    # client = HttpClient(sys.argv[1], sys.argv[2])
    client = SocketClient(sys.argv[1], sys.argv[2])
    client.is_verbose = True

    print 'Your balance is %s US cents' % client.get_balance()

    for fn in sys.argv[3:]:
        try:
            # Put your CAPTCHA image file name or file-like object, and optional
            # solving timeout (in seconds) here:
            captcha = client.decode(fn, DEFAULT_TIMEOUT)
        except Exception, e:
            sys.stderr.write('Failed uploading CAPTCHA: %s\n' % (e, ))
            captcha = None

        if captcha:
            print 'CAPTCHA %d solved: %s' % \
                  (captcha['captcha'], captcha['text'])

            # Report as incorrectly solved if needed.  Make sure the CAPTCHA was
            # in fact incorrectly solved!
            # try:
            #    client.report(captcha['captcha'])
            # except Exception, e:
            #    sys.stderr.write('Failed reporting CAPTCHA: %s\n' % (e, ))
