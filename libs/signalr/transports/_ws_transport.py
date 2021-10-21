import json
import sys


if sys.version_info[0] < 3:
    from urlparse import urlparse, urlunparse
else:
    from urllib.parse import urlparse, urlunparse

from websocket import create_connection
from ._transport import Transport


class WebSocketsTransport(Transport):
    def __init__(self, session, connection):
        Transport.__init__(self, session, connection)
        self.ws = None
        self.__requests = {}

    def _get_name(self):
        return 'webSockets'

    @staticmethod
    def __get_ws_url_from(url):
        parsed = urlparse(url)
        scheme = 'wss' if parsed.scheme == 'https' else 'ws'
        url_data = (scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)

        return urlunparse(url_data)

    def start(self):
        ws_url = self.__get_ws_url_from(self._get_url('connect'))

        self.ws = create_connection(ws_url,
                                    header=self.__get_headers(),
                                    cookie=self.__get_cookie_str(),
                                    enable_multithread=True)
        self._session.get(self._get_url('start'))

        def _receive():
            notification = self.ws.recv()
            self._handle_notification(notification)

        return _receive

    def send(self, data):
        self.ws.send(json.dumps(data))
        #thread.sleep() #TODO: inveistage if we should sleep here or not

    def close(self):
        self.ws.close()

    def accept(self, negotiate_data):
        return bool(negotiate_data['TryWebSockets'])

    class HeadersLoader(object):
        def __init__(self, headers):
            self.headers = headers

    def __get_headers(self):
        headers = self._session.headers
        loader = WebSocketsTransport.HeadersLoader(headers)

        if self._session.auth:
            self._session.auth(loader)

        return ['%s: %s' % (name, headers[name]) for name in headers]

    def __get_cookie_str(self):
        return '; '.join([
                             '%s=%s' % (name, value)
                             for name, value in self._session.cookies.items()
                             ])
