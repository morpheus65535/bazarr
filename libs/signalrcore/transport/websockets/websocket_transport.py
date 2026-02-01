import traceback
import time
from typing import Optional
from .reconnection import ConnectionStateChecker
from ...messages.ping_message import PingMessage
from ...hub.errors import HubError, UnAuthorizedHubError
from ...protocol.messagepack_protocol import MessagePackHubProtocol
from ..base_transport import BaseTransport, TransportState
from ...helpers import Helpers, RequestHelpers
from .websocket_client import WebSocketClient, SocketClosedError


class WebsocketTransport(BaseTransport):
    _ws: Optional[WebSocketClient]

    def __init__(
            self,
            url="",
            headers=None,
            keep_alive_interval=15,
            verify_ssl=False,
            skip_negotiation=False,
            enable_trace=False,
            proxies: dict = {},
            **kwargs):
        super(WebsocketTransport, self).__init__(**kwargs)
        self._ws = None
        self.enable_trace = enable_trace
        self.skip_negotiation = skip_negotiation
        self.url = url
        self.proxies = proxies
        if headers is None:
            self.headers = dict()
        else:
            self.headers = headers
        self.handshake_received = False
        self.token = None  # auth
        self.connection_alive = False
        self._ws = None
        self.verify_ssl = verify_ssl
        self.connection_checker = ConnectionStateChecker(
            lambda: self.send(PingMessage()),
            keep_alive_interval
        )
        self.manually_closing = False

    def dispose(self):
        if self.is_connected():
            self.connection_checker.stop()
            self._ws.close()

    def stop(self):
        self.manually_closing = True
        self.dispose()
        self._set_state(TransportState.disconnected)
        self.handshake_received = False

    def is_trace_enabled(self) -> bool:
        return self._ws.is_trace_enabled

    def start(self, reconnection: bool = False):
        if not self.skip_negotiation:
            self.negotiate()

        if self.is_connected():
            self.logger.warning("Already connected unable to start")
            return False

        if reconnection:
            self._set_state(TransportState.reconnecting)
        else:
            self._set_state(TransportState.connecting)

        self.logger.debug("start url:" + self.url)

        self._ws = WebSocketClient(
            self.url,
            headers=self.headers,
            is_binary=type(self.protocol) is MessagePackHubProtocol,
            verify_ssl=self.verify_ssl,
            on_message=self.on_message,
            on_error=self.on_socket_error,
            on_close=self.on_socket_close,
            on_open=self.on_socket_open,
            enable_trace=self.enable_trace
            )

        self._ws.connect()
        return True

    def negotiate(self):
        negotiate_url = Helpers.get_negotiate_url(self.url)
        self.logger.debug("Negotiate url:{0}".format(negotiate_url))

        status_code, data = RequestHelpers.post(
            negotiate_url,
            headers=self.headers,
            proxies=self.proxies,
            verify_ssl=self.verify_ssl)

        self.logger.debug(
            "Response status code {0}".format(status_code))

        if status_code != 200:
            raise HubError(status_code)\
                if status_code != 401 else UnAuthorizedHubError()

        if "connectionId" in data.keys():
            self.url = Helpers.encode_connection_id(
                self.url, data["connectionId"])

        # Azure
        if 'url' in data.keys() and 'accessToken' in data.keys():
            Helpers.get_logger().debug(
                "Azure url, reformat headers, token and url {0}".format(data))
            self.url = data["url"]\
                if data["url"].startswith("ws") else\
                Helpers.http_to_websocket(data["url"])
            self.token = data["accessToken"]
            self.headers = {"Authorization": "Bearer " + self.token}

    def evaluate_handshake(self, message):
        self.logger.debug("Evaluating handshake {0}".format(message))
        msg, messages = self.protocol.decode_handshake(message)
        if msg.error is None or msg.error == "":
            self.handshake_received = True
            self._set_state(TransportState.connected)
            if self.reconnection_handler is not None:
                self.reconnection_handler.reconnecting = False
                if not self.connection_checker.running:
                    self.connection_checker.start()
        else:
            self.logger.error(msg.error)
            self.on_socket_error(msg.error)
            self.stop()
        return messages

    def on_open(self):
        self.logger.debug("-- web socket open --")
        msg = self.protocol.handshake_message()
        self.handshake_received = False
        self.send(msg)

    def on_close(self):
        self.logger.debug("-- web socket close --")
        self._set_state(TransportState.disconnected)

    def on_socket_error(self, error: Exception):  # pragma: no cover
        """
        Args:
            error (Exception): websocket error

        Raises:
            HubError: [description]
        """
        self.logger.debug("-- web socket error --")
        self.logger.error(traceback.format_exc(10, True))
        self.logger.error("{0} {1}".format(self, error))
        self.logger.error("{0} {1}".format(error, type(error)))
        self._set_state(TransportState.disconnected)
        # raise HubError(error)

    def on_socket_close(self):
        if self.reconnection_handler is not None\
                and not self.is_reconnecting():
            self.handle_reconnect()
            return
        self.on_close()

    def on_socket_open(self):
        self.on_open()

    def on_message(self, app, raw_message):
        self.logger.debug("Message received {0}".format(raw_message))
        if not self.handshake_received:
            messages = self.evaluate_handshake(raw_message)
            self._set_state(TransportState.connected)

            if len(messages) > 0:
                return self._on_message(messages)

            return []

        return self._on_message(
            self.protocol.parse_messages(raw_message))

    def send(self, message):
        self.logger.debug("Sending message {0}".format(message))
        try:
            self._ws.send(
                self.protocol.encode(message),
                opcode=0x2
                if type(self.protocol) is MessagePackHubProtocol else
                0x1)
            self.connection_checker.last_message = time.time()
            if self.reconnection_handler is not None:
                self.reconnection_handler.reset()
        except (OSError, SocketClosedError) as ex:  # pragma: no cover
            self.handshake_received = False  # pragma: no cover
            self.logger.warning("Connection closed {0}".format(ex))
            # pragma: no cover
            if self.reconnection_handler is None:  # pragma: no cover
                self._set_state(TransportState.disconnected)
                # pragma: no cover
                raise ValueError(str(ex))  # pragma: no cover
            # Connection closed
            self.handle_reconnect()  # pragma: no cover
        except Exception as ex:  # pragma: no cover
            raise ex  # pragma: no cover

    def handle_reconnect(self):
        if self.is_reconnecting() or self.manually_closing:
            return  # pragma: no cover

        self.reconnection_handler.reconnecting = True
        self._set_state(TransportState.reconnecting)
        try:
            self._ws.dispose()
            self.start(reconnection=True)
        except Exception as ex:
            self.logger.error(ex)
            sleep_time = self.reconnection_handler.next()
            self.deferred_reconnect(sleep_time)

    def deferred_reconnect(self, sleep_time):
        time.sleep(sleep_time)
        try:
            if not self.connection_alive:
                if not self.connection_checker.running:
                    self.send(PingMessage())
        except Exception as ex:
            self.logger.error(ex)
            self.reconnection_handler.reconnecting = False
            self.connection_alive = False
