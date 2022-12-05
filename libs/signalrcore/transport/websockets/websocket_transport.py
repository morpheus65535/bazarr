import websocket
import threading
import requests
import traceback
import time
import ssl
from .reconnection import ConnectionStateChecker
from .connection import ConnectionState
from ...messages.ping_message import PingMessage
from ...hub.errors import HubError, HubConnectionError, UnAuthorizedHubError
from ...protocol.messagepack_protocol import MessagePackHubProtocol
from ...protocol.json_hub_protocol import JsonHubProtocol
from ..base_transport import BaseTransport
from ...helpers import Helpers

class WebsocketTransport(BaseTransport):
    def __init__(self,
            url="",
            headers=None,
            keep_alive_interval=15,
            reconnection_handler=None,
            verify_ssl=False,
            skip_negotiation=False,
            enable_trace=False,
            **kwargs):
        super(WebsocketTransport, self).__init__(**kwargs)
        self._ws = None
        self.enable_trace = enable_trace
        self._thread = None
        self.skip_negotiation = skip_negotiation
        self.url = url
        if headers is None:
            self.headers = dict()
        else:
            self.headers = headers
        self.handshake_received = False
        self.token = None  # auth
        self.state = ConnectionState.disconnected
        self.connection_alive = False
        self._thread = None
        self._ws = None
        self.verify_ssl = verify_ssl
        self.connection_checker = ConnectionStateChecker(
            lambda: self.send(PingMessage()),
            keep_alive_interval
        )
        self.reconnection_handler = reconnection_handler

        if len(self.logger.handlers) > 0:
            websocket.enableTrace(self.enable_trace, self.logger.handlers[0])
    
    def is_running(self):
        return self.state != ConnectionState.disconnected

    def stop(self):
        if self.state == ConnectionState.connected:
            self.connection_checker.stop()
            self._ws.close()
            self.state = ConnectionState.disconnected
            self.handshake_received = False

    def start(self):
        if not self.skip_negotiation:
            self.negotiate()

        if self.state == ConnectionState.connected:
            self.logger.warning("Already connected unable to start")
            return False

        self.state = ConnectionState.connecting
        self.logger.debug("start url:" + self.url)
        
        self._ws = websocket.WebSocketApp(
            self.url,
            header=self.headers,
            on_message=self.on_message,
            on_error=self.on_socket_error,
            on_close=self.on_close,
            on_open=self.on_open,
            )
            
        self._thread = threading.Thread(
            target=lambda: self._ws.run_forever(
                sslopt={"cert_reqs": ssl.CERT_NONE}
                if not self.verify_ssl else {}
            ))
        self._thread.daemon = True
        self._thread.start()
        return True

    def negotiate(self):
        negotiate_url = Helpers.get_negotiate_url(self.url)
        self.logger.debug("Negotiate url:{0}".format(negotiate_url))

        response = requests.post(
            negotiate_url, headers=self.headers, verify=self.verify_ssl)
        self.logger.debug(
            "Response status code{0}".format(response.status_code))

        if response.status_code != 200:
            raise HubError(response.status_code)\
                if response.status_code != 401 else UnAuthorizedHubError()

        data = response.json()

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
            self.state = ConnectionState.connected
            if self.reconnection_handler is not None:
                self.reconnection_handler.reconnecting = False
                if not self.connection_checker.running:
                    self.connection_checker.start()
        else:
            self.logger.error(msg.error)
            self.on_socket_error(self._ws, msg.error)
            self.stop()
            self.state = ConnectionState.disconnected
        return messages

    def on_open(self, _):
        self.logger.debug("-- web socket open --")
        msg = self.protocol.handshake_message()
        self.send(msg)

    def on_close(self, callback, close_status_code, close_reason):
        self.logger.debug("-- web socket close --")
        self.logger.debug(close_status_code)
        self.logger.debug(close_reason)
        self.state = ConnectionState.disconnected
        if self._on_close is not None and callable(self._on_close):
            self._on_close()
        if callback is not None and callable(callback):
            callback()

    def on_reconnect(self):
        self.logger.debug("-- web socket reconnecting --")
        self.state = ConnectionState.disconnected
        if self._on_close is not None and callable(self._on_close):
            self._on_close()

    def on_socket_error(self, app, error):
        """
        Args:
            _: Required to support websocket-client version equal or greater than 0.58.0
            error ([type]): [description]

        Raises:
            HubError: [description]
        """
        self.logger.debug("-- web socket error --")
        self.logger.error(traceback.format_exc(10, True))
        self.logger.error("{0} {1}".format(self, error))
        self.logger.error("{0} {1}".format(error, type(error)))
        self._on_close()
        self.state = ConnectionState.disconnected
        #raise HubError(error)

    def on_message(self, app, raw_message):
        self.logger.debug("Message received{0}".format(raw_message))
        if not self.handshake_received:
            messages = self.evaluate_handshake(raw_message)
            if self._on_open is not None and callable(self._on_open):
                self.state = ConnectionState.connected
                self._on_open()

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
                if type(self.protocol) == MessagePackHubProtocol else
                0x1)
            self.connection_checker.last_message = time.time()
            if self.reconnection_handler is not None:
                self.reconnection_handler.reset()
        except (
                websocket._exceptions.WebSocketConnectionClosedException,
                OSError) as ex:
            self.handshake_received = False
            self.logger.warning("Connection closed {0}".format(ex))
            self.state = ConnectionState.disconnected
            if self.reconnection_handler is None:
                if self._on_close is not None and\
                        callable(self._on_close):
                    self._on_close()
                raise ValueError(str(ex))
            # Connection closed
            self.handle_reconnect()
        except Exception as ex:
            raise ex

    def handle_reconnect(self):
        if not self.reconnection_handler.reconnecting and self._on_reconnect is not None and \
                callable(self._on_reconnect):
            self._on_reconnect()
        self.reconnection_handler.reconnecting = True
        try:
            self.stop()
            self.start()
        except Exception as ex:
            self.logger.error(ex)
            sleep_time = self.reconnection_handler.next()
            threading.Thread(
                target=self.deferred_reconnect,
                args=(sleep_time,)
            ).start()

    def deferred_reconnect(self, sleep_time):
        time.sleep(sleep_time)
        try:
            if not self.connection_alive:
                self.send(PingMessage())
        except Exception as ex:
            self.logger.error(ex)
            self.reconnection_handler.reconnecting = False
            self.connection_alive = False