import socket
import ssl
import base64
import threading
import os
import struct
import urllib.parse as parse
from typing import Optional, Callable, Union
from signalrcore.helpers import Helpers


THREAD_NAME = "Signalrcore websocket client"
WINDOW_SIZE = 1024


class NoHeaderException(Exception):
    """Error reading messages from socket, empty content
    """
    pass


class SocketHandshakeError(Exception):
    """Error during connection

    Args:
        msg (str): message
    """
    def __init__(self, msg: str):
        super().__init__(msg)


class SocketClosedError(Exception):
    """Socket closed by the server fin opcode: 129, masked len 3

    Args:
        data (bytes): raw bytes sent by the server
    """
    def __init__(self, data: Optional[bytes] = None):  # pragma: no cover
        self.data = data
        super().__init__("Socket closed by the the server")


class WebSocketClient(object):
    """Minimal websocket client

    Args:
        url (str): Websocket url
        headers (Optional[dict]): additional headers
        verify_ssl (bool): Verify SSL y/n
        on_message (callable): on message callback
        on_error (callable): on error callback
        on_open (callable): on open callback
        on_close (callable): on close callback
    """
    def __init__(
            self,
            url: str,
            is_binary: bool = False,
            headers: Optional[dict] = None,
            proxies: dict = {},
            verify_ssl: bool = True,
            enable_trace: bool = False,
            on_message: Callable = None,
            on_open: Callable = None,
            on_error: Callable = None,
            on_close: Callable = None):
        self.is_trace_enabled = enable_trace
        self.proxies = proxies
        self.url = url
        self.is_binary = is_binary
        self.headers = headers or {}
        self.verify_ssl = verify_ssl
        self.sock = None
        self.ssl_context = ssl.create_default_context()\
            if verify_ssl else\
            ssl._create_unverified_context()
        self.logger = Helpers.get_logger()
        self.recv_thread = None
        self.on_message = on_message
        self.on_close = on_close
        self.on_error = on_error
        self.on_open = on_open
        self.running = False
        self.is_closing = False

    def connect(self):
        parsed_url = parse.urlparse(self.url)
        host, port = parsed_url.hostname, parsed_url.port

        is_secure_connection = parsed_url.scheme in ("wss", "https")

        if not port:
            port = 80
            if is_secure_connection:
                port = 443

        proxy_info = None
        if is_secure_connection\
                and self.proxies.get("https", None) is not None:
            proxy_info = parse.urlparse(self.proxies.get("https"))

        if not is_secure_connection\
                and self.proxies.get("http", None) is not None:
            proxy_info = parse.urlparse(self.proxies.get("http"))

        if proxy_info is not None:
            host = proxy_info.hostname,
            port = proxy_info.port

        raw_sock = socket.create_connection((host, port))

        if is_secure_connection:
            raw_sock = self.ssl_context.wrap_socket(
                raw_sock,
                server_hostname=host)

        self.sock = raw_sock

        # Perform the WebSocket handshake
        key = base64.b64encode(os.urandom(16)).decode("utf-8")
        relative_reference = parsed_url.path
        if parsed_url.query:
            relative_reference = f"{parsed_url.path}?{parsed_url.query}"
        request_headers = [
            f"GET {relative_reference} HTTP/1.1",
            f"Host: {parsed_url.hostname}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Key: {key}",
            "Sec-WebSocket-Version: 13"
        ]
        for k, v in self.headers.items():
            request_headers.append(f"{k}: {v}")

        request = "\r\n".join(request_headers) + "\r\n\r\n"
        req = request.encode("utf-8")

        if self.is_trace_enabled:
            self.logger.debug(f"[TRACE] - {req}")

        self.sock.sendall(req)

        # Read handshake response
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self.sock.recv(WINDOW_SIZE)

            if not chunk:
                raise SocketHandshakeError(
                    "Connection closed during handshake")

            response += chunk

        if self.is_trace_enabled:
            self.logger.debug(f"[TRACE] - {response}")

        if b"101" not in response:
            raise SocketHandshakeError(
                f"Handshake failed: {response.decode()}")

        self.running = True
        self.recv_thread = threading.Thread(
            target=self._recv_loop,
            name=THREAD_NAME)
        self.recv_thread.daemon = True
        self.recv_thread.start()

    def is_connection_closed(self):
        return self.recv_thread is None or not self.recv_thread.is_alive()

    def _recv_loop(self):
        self.on_open()
        try:
            while self.running:
                message = self._recv_frame()

                if self.on_message:
                    self.on_message(self, message)
        except (OSError, Exception) as e:
            self.running = False

            # is closing and no header indicates
            # that socket has not received anything
            has_no_content = type(e) is NoHeaderException

            # is closing and errno indicates
            # that file descriptor points to a closed file
            has_closed_fd = type(e) is OSError and e.errno == 9

            # closed by the server
            connection_closed = has_closed_fd or type(e) is SocketClosedError

            if connection_closed and not self.is_closing:
                raise e  # pragma: no cover

            if (has_closed_fd or has_no_content) and self.is_closing:
                return

            if self.logger:
                self.logger.error(f"Receive error: {e}")

            self.on_error(e)

    def _recv_frame(self):
        # Very basic, single-frame, unfragmented
        try:
            header = self.sock.recv(2)
        except ssl.SSLError as ex:
            self.logger.error(ex)
            header = None

        if header is None or len(header) < 2:
            raise NoHeaderException()

        fin_opcode = header[0]
        masked_len = header[1]

        if self.logger:
            self.logger.debug(
                f"fin opcode: {fin_opcode}, masked len: {masked_len}")

        if fin_opcode == 8:
            raise SocketClosedError(header)
        payload_len = masked_len & 0x7F
        if payload_len == 126:
            payload_len = struct.unpack(">H", self.sock.recv(2))[0]
        elif payload_len == 127:
            payload_len = struct.unpack(">Q", self.sock.recv(8))[0]

        if masked_len & 0x80:
            masking_key = self.sock.recv(4)
            masked_data = self.sock.recv(payload_len)
            data = bytes(
                b ^ masking_key[i % 4]
                for i, b in enumerate(masked_data))
        else:
            data = self.sock.recv(payload_len)

        if self.is_trace_enabled:
            self.logger.debug(f"[TRACE] - {data}")

        if self.is_binary:
            return data

        return data.decode("utf-8")

    def send(
            self,
            message: Union[str, bytes],
            opcode=0x1):
        if self.is_connection_closed():
            raise SocketClosedError()

        # Text or binary opcode (no fragmentation)
        payload = message.encode("utf-8")\
            if type(message) is str else message
        header = bytes([0x80 | opcode])
        length = len(payload)
        if length <= 125:
            header += bytes([0x80 | length])
        elif length <= 65535:
            header += bytes([0x80 | 126]) + struct.pack(">H", length)
        else:
            header += bytes([0x80 | 127]) + struct.pack(">Q", length)

        # Mask the payload
        masking_key = os.urandom(4)
        masked_payload = bytes(
            b ^ masking_key[i % 4]
            for i, b in enumerate(payload))
        frame = header + masking_key + masked_payload
        self.sock.sendall(frame)

    def dispose(self):
        if self.sock:
            self.sock.close()

        is_same_thread = threading.current_thread().name == THREAD_NAME

        if self.recv_thread and not is_same_thread:
            self.recv_thread.join()
            self.recv_thread = None

    def close(self):
        try:
            self.is_closing = True
            self.running = False

            self.logger.debug("Start closing socket")

            self.dispose()

            self.on_close()

            self.logger.debug("socket closed successfully")
        except Exception as ex:  # pragma: no cover
            self.logger.error(ex)  # pragma: no cover
            self.on_error(ex)  # pragma: no cover
        finally:
            self.is_closing = False
