import asyncio
import signal
import ssl
import threading

try:
    import aiohttp
except ImportError:  # pragma: no cover
    aiohttp = None

from . import client
from . import exceptions
from . import packet
from . import payload

async_signal_handler_set = False


def async_signal_handler():
    """SIGINT handler.

    Disconnect all active async clients.
    """
    async def _handler():
        asyncio.get_event_loop().stop()
        for c in client.connected_clients[:]:
            if c.is_asyncio_based():
                await c.disconnect()
        else:  # pragma: no cover
            pass

    asyncio.ensure_future(_handler())


class AsyncClient(client.Client):
    """An Engine.IO client for asyncio.

    This class implements a fully compliant Engine.IO web client with support
    for websocket and long-polling transports, compatible with the asyncio
    framework on Python 3.5 or newer.

    :param logger: To enable logging set to ``True`` or pass a logger object to
                   use. To disable logging set to ``False``. The default is
                   ``False``. Note that fatal errors are logged even when
                   ``logger`` is ``False``.
    :param json: An alternative json module to use for encoding and decoding
                 packets. Custom json modules must have ``dumps`` and ``loads``
                 functions that are compatible with the standard library
                 versions.
    :param request_timeout: A timeout in seconds for requests. The default is
                            5 seconds.
    :param http_session: an initialized ``aiohttp.ClientSession`` object to be
                         used when sending requests to the server. Use it if
                         you need to add special client options such as proxy
                         servers, SSL certificates, etc.
    :param ssl_verify: ``True`` to verify SSL certificates, or ``False`` to
                       skip SSL certificate verification, allowing
                       connections to servers with self signed certificates.
                       The default is ``True``.
    """
    def is_asyncio_based(self):
        return True

    async def connect(self, url, headers=None, transports=None,
                      engineio_path='engine.io'):
        """Connect to an Engine.IO server.

        :param url: The URL of the Engine.IO server. It can include custom
                    query string parameters if required by the server.
        :param headers: A dictionary with custom headers to send with the
                        connection request.
        :param transports: The list of allowed transports. Valid transports
                           are ``'polling'`` and ``'websocket'``. If not
                           given, the polling transport is connected first,
                           then an upgrade to websocket is attempted.
        :param engineio_path: The endpoint where the Engine.IO server is
                              installed. The default value is appropriate for
                              most cases.

        Note: this method is a coroutine.

        Example usage::

            eio = engineio.Client()
            await eio.connect('http://localhost:5000')
        """
        global async_signal_handler_set
        if not async_signal_handler_set and \
                threading.current_thread() == threading.main_thread():

            try:
                asyncio.get_event_loop().add_signal_handler(
                    signal.SIGINT, async_signal_handler)
                async_signal_handler_set = True
            except NotImplementedError:  # pragma: no cover
                self.logger.warning('Signal handler is unsupported')

        if self.state != 'disconnected':
            raise ValueError('Client is not in a disconnected state')
        valid_transports = ['polling', 'websocket']
        if transports is not None:
            if isinstance(transports, str):
                transports = [transports]
            transports = [transport for transport in transports
                          if transport in valid_transports]
            if not transports:
                raise ValueError('No valid transports provided')
        self.transports = transports or valid_transports
        self.queue = self.create_queue()
        return await getattr(self, '_connect_' + self.transports[0])(
            url, headers or {}, engineio_path)

    async def wait(self):
        """Wait until the connection with the server ends.

        Client applications can use this function to block the main thread
        during the life of the connection.

        Note: this method is a coroutine.
        """
        if self.read_loop_task:
            await self.read_loop_task

    async def send(self, data):
        """Send a message to a client.

        :param data: The data to send to the client. Data can be of type
                     ``str``, ``bytes``, ``list`` or ``dict``. If a ``list``
                     or ``dict``, the data will be serialized as JSON.

        Note: this method is a coroutine.
        """
        await self._send_packet(packet.Packet(packet.MESSAGE, data=data))

    async def disconnect(self, abort=False):
        """Disconnect from the server.

        :param abort: If set to ``True``, do not wait for background tasks
                      associated with the connection to end.

        Note: this method is a coroutine.
        """
        if self.state == 'connected':
            await self._send_packet(packet.Packet(packet.CLOSE))
            await self.queue.put(None)
            self.state = 'disconnecting'
            await self._trigger_event('disconnect', run_async=False)
            if self.current_transport == 'websocket':
                await self.ws.close()
            if not abort:
                await self.read_loop_task
            self.state = 'disconnected'
            try:
                client.connected_clients.remove(self)
            except ValueError:  # pragma: no cover
                pass
        self._reset()

    def start_background_task(self, target, *args, **kwargs):
        """Start a background task.

        This is a utility function that applications can use to start a
        background task.

        :param target: the target function to execute.
        :param args: arguments to pass to the function.
        :param kwargs: keyword arguments to pass to the function.

        This function returns an object compatible with the `Thread` class in
        the Python standard library. The `start()` method on this object is
        already called by this function.

        Note: this method is a coroutine.
        """
        return asyncio.ensure_future(target(*args, **kwargs))

    async def sleep(self, seconds=0):
        """Sleep for the requested amount of time.

        Note: this method is a coroutine.
        """
        return await asyncio.sleep(seconds)

    def create_queue(self):
        """Create a queue object."""
        q = asyncio.Queue()
        q.Empty = asyncio.QueueEmpty
        return q

    def create_event(self):
        """Create an event object."""
        return asyncio.Event()

    def _reset(self):
        if self.http:  # pragma: no cover
            asyncio.ensure_future(self.http.close())
        super()._reset()

    async def _connect_polling(self, url, headers, engineio_path):
        """Establish a long-polling connection to the Engine.IO server."""
        if aiohttp is None:  # pragma: no cover
            self.logger.error('aiohttp not installed -- cannot make HTTP '
                              'requests!')
            return
        self.base_url = self._get_engineio_url(url, engineio_path, 'polling')
        self.logger.info('Attempting polling connection to ' + self.base_url)
        r = await self._send_request(
            'GET', self.base_url + self._get_url_timestamp(), headers=headers,
            timeout=self.request_timeout)
        if r is None:
            self._reset()
            raise exceptions.ConnectionError(
                'Connection refused by the server')
        if r.status < 200 or r.status >= 300:
            self._reset()
            try:
                arg = await r.json()
            except aiohttp.ClientError:
                arg = None
            raise exceptions.ConnectionError(
                'Unexpected status code {} in server response'.format(
                    r.status), arg)
        try:
            p = payload.Payload(encoded_payload=(await r.read()).decode(
                'utf-8'))
        except ValueError:
            raise exceptions.ConnectionError(
                'Unexpected response from server') from None
        open_packet = p.packets[0]
        if open_packet.packet_type != packet.OPEN:
            raise exceptions.ConnectionError(
                'OPEN packet not returned by server')
        self.logger.info(
            'Polling connection accepted with ' + str(open_packet.data))
        self.sid = open_packet.data['sid']
        self.upgrades = open_packet.data['upgrades']
        self.ping_interval = int(open_packet.data['pingInterval']) / 1000.0
        self.ping_timeout = int(open_packet.data['pingTimeout']) / 1000.0
        self.current_transport = 'polling'
        self.base_url += '&sid=' + self.sid

        self.state = 'connected'
        client.connected_clients.append(self)
        await self._trigger_event('connect', run_async=False)

        for pkt in p.packets[1:]:
            await self._receive_packet(pkt)

        if 'websocket' in self.upgrades and 'websocket' in self.transports:
            # attempt to upgrade to websocket
            if await self._connect_websocket(url, headers, engineio_path):
                # upgrade to websocket succeeded, we're done here
                return

        self.write_loop_task = self.start_background_task(self._write_loop)
        self.read_loop_task = self.start_background_task(
            self._read_loop_polling)

    async def _connect_websocket(self, url, headers, engineio_path):
        """Establish or upgrade to a WebSocket connection with the server."""
        if aiohttp is None:  # pragma: no cover
            self.logger.error('aiohttp package not installed')
            return False
        websocket_url = self._get_engineio_url(url, engineio_path,
                                               'websocket')
        if self.sid:
            self.logger.info(
                'Attempting WebSocket upgrade to ' + websocket_url)
            upgrade = True
            websocket_url += '&sid=' + self.sid
        else:
            upgrade = False
            self.base_url = websocket_url
            self.logger.info(
                'Attempting WebSocket connection to ' + websocket_url)

        if self.http is None or self.http.closed:  # pragma: no cover
            self.http = aiohttp.ClientSession()

        # extract any new cookies passed in a header so that they can also be
        # sent the the WebSocket route
        cookies = {}
        for header, value in headers.items():
            if header.lower() == 'cookie':
                cookies = dict(
                    [cookie.split('=', 1) for cookie in value.split('; ')])
                del headers[header]
                break
        self.http.cookie_jar.update_cookies(cookies)

        try:
            if not self.ssl_verify:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                ws = await self.http.ws_connect(
                    websocket_url + self._get_url_timestamp(),
                    headers=headers, ssl=ssl_context)
            else:
                ws = await self.http.ws_connect(
                    websocket_url + self._get_url_timestamp(),
                    headers=headers)
        except (aiohttp.client_exceptions.WSServerHandshakeError,
                aiohttp.client_exceptions.ServerConnectionError,
                aiohttp.client_exceptions.ClientConnectionError):
            if upgrade:
                self.logger.warning(
                    'WebSocket upgrade failed: connection error')
                return False
            else:
                raise exceptions.ConnectionError('Connection error')
        if upgrade:
            p = packet.Packet(packet.PING, data='probe').encode()
            try:
                await ws.send_str(p)
            except Exception as e:  # pragma: no cover
                self.logger.warning(
                    'WebSocket upgrade failed: unexpected send exception: %s',
                    str(e))
                return False
            try:
                p = (await ws.receive()).data
            except Exception as e:  # pragma: no cover
                self.logger.warning(
                    'WebSocket upgrade failed: unexpected recv exception: %s',
                    str(e))
                return False
            pkt = packet.Packet(encoded_packet=p)
            if pkt.packet_type != packet.PONG or pkt.data != 'probe':
                self.logger.warning(
                    'WebSocket upgrade failed: no PONG packet')
                return False
            p = packet.Packet(packet.UPGRADE).encode()
            try:
                await ws.send_str(p)
            except Exception as e:  # pragma: no cover
                self.logger.warning(
                    'WebSocket upgrade failed: unexpected send exception: %s',
                    str(e))
                return False
            self.current_transport = 'websocket'
            self.logger.info('WebSocket upgrade was successful')
        else:
            try:
                p = (await ws.receive()).data
            except Exception as e:  # pragma: no cover
                raise exceptions.ConnectionError(
                    'Unexpected recv exception: ' + str(e))
            open_packet = packet.Packet(encoded_packet=p)
            if open_packet.packet_type != packet.OPEN:
                raise exceptions.ConnectionError('no OPEN packet')
            self.logger.info(
                'WebSocket connection accepted with ' + str(open_packet.data))
            self.sid = open_packet.data['sid']
            self.upgrades = open_packet.data['upgrades']
            self.ping_interval = int(open_packet.data['pingInterval']) / 1000.0
            self.ping_timeout = int(open_packet.data['pingTimeout']) / 1000.0
            self.current_transport = 'websocket'

            self.state = 'connected'
            client.connected_clients.append(self)
            await self._trigger_event('connect', run_async=False)

        self.ws = ws
        self.write_loop_task = self.start_background_task(self._write_loop)
        self.read_loop_task = self.start_background_task(
            self._read_loop_websocket)
        return True

    async def _receive_packet(self, pkt):
        """Handle incoming packets from the server."""
        packet_name = packet.packet_names[pkt.packet_type] \
            if pkt.packet_type < len(packet.packet_names) else 'UNKNOWN'
        self.logger.info(
            'Received packet %s data %s', packet_name,
            pkt.data if not isinstance(pkt.data, bytes) else '<binary>')
        if pkt.packet_type == packet.MESSAGE:
            await self._trigger_event('message', pkt.data, run_async=True)
        elif pkt.packet_type == packet.PING:
            await self._send_packet(packet.Packet(packet.PONG, pkt.data))
        elif pkt.packet_type == packet.CLOSE:
            await self.disconnect(abort=True)
        elif pkt.packet_type == packet.NOOP:
            pass
        else:
            self.logger.error('Received unexpected packet of type %s',
                              pkt.packet_type)

    async def _send_packet(self, pkt):
        """Queue a packet to be sent to the server."""
        if self.state != 'connected':
            return
        await self.queue.put(pkt)
        self.logger.info(
            'Sending packet %s data %s',
            packet.packet_names[pkt.packet_type],
            pkt.data if not isinstance(pkt.data, bytes) else '<binary>')

    async def _send_request(
            self, method, url, headers=None, body=None,
            timeout=None):  # pragma: no cover
        if self.http is None or self.http.closed:
            self.http = aiohttp.ClientSession()
        http_method = getattr(self.http, method.lower())

        try:
            if not self.ssl_verify:
                return await http_method(
                    url, headers=headers, data=body,
                    timeout=aiohttp.ClientTimeout(total=timeout), ssl=False)
            else:
                return await http_method(
                    url, headers=headers, data=body,
                    timeout=aiohttp.ClientTimeout(total=timeout))

        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            self.logger.info('HTTP %s request to %s failed with error %s.',
                             method, url, exc)

    async def _trigger_event(self, event, *args, **kwargs):
        """Invoke an event handler."""
        run_async = kwargs.pop('run_async', False)
        ret = None
        if event in self.handlers:
            if asyncio.iscoroutinefunction(self.handlers[event]) is True:
                if run_async:
                    return self.start_background_task(self.handlers[event],
                                                      *args)
                else:
                    try:
                        ret = await self.handlers[event](*args)
                    except asyncio.CancelledError:  # pragma: no cover
                        pass
                    except:
                        self.logger.exception(event + ' async handler error')
                        if event == 'connect':
                            # if connect handler raised error we reject the
                            # connection
                            return False
            else:
                if run_async:
                    async def async_handler():
                        return self.handlers[event](*args)

                    return self.start_background_task(async_handler)
                else:
                    try:
                        ret = self.handlers[event](*args)
                    except:
                        self.logger.exception(event + ' handler error')
                        if event == 'connect':
                            # if connect handler raised error we reject the
                            # connection
                            return False
        return ret

    async def _read_loop_polling(self):
        """Read packets by polling the Engine.IO server."""
        while self.state == 'connected':
            self.logger.info(
                'Sending polling GET request to ' + self.base_url)
            r = await self._send_request(
                'GET', self.base_url + self._get_url_timestamp(),
                timeout=max(self.ping_interval, self.ping_timeout) + 5)
            if r is None:
                self.logger.warning(
                    'Connection refused by the server, aborting')
                await self.queue.put(None)
                break
            if r.status < 200 or r.status >= 300:
                self.logger.warning('Unexpected status code %s in server '
                                    'response, aborting', r.status)
                await self.queue.put(None)
                break
            try:
                p = payload.Payload(encoded_payload=(await r.read()).decode(
                    'utf-8'))
            except ValueError:
                self.logger.warning(
                    'Unexpected packet from server, aborting')
                await self.queue.put(None)
                break
            for pkt in p.packets:
                await self._receive_packet(pkt)

        self.logger.info('Waiting for write loop task to end')
        await self.write_loop_task
        if self.state == 'connected':
            await self._trigger_event('disconnect', run_async=False)
            try:
                client.connected_clients.remove(self)
            except ValueError:  # pragma: no cover
                pass
            self._reset()
        self.logger.info('Exiting read loop task')

    async def _read_loop_websocket(self):
        """Read packets from the Engine.IO WebSocket connection."""
        while self.state == 'connected':
            p = None
            try:
                p = await asyncio.wait_for(
                    self.ws.receive(),
                    timeout=self.ping_interval + self.ping_timeout)
                p = p.data
                if p is None:  # pragma: no cover
                    await self.queue.put(None)
                    break  # the connection is broken
            except asyncio.TimeoutError:
                self.logger.warning(
                    'Server has stopped communicating, aborting')
                await self.queue.put(None)
                break
            except aiohttp.client_exceptions.ServerDisconnectedError:
                self.logger.info(
                    'Read loop: WebSocket connection was closed, aborting')
                await self.queue.put(None)
                break
            except Exception as e:
                self.logger.info(
                    'Unexpected error receiving packet: "%s", aborting',
                    str(e))
                await self.queue.put(None)
                break
            try:
                pkt = packet.Packet(encoded_packet=p)
            except Exception as e:  # pragma: no cover
                self.logger.info(
                    'Unexpected error decoding packet: "%s", aborting', str(e))
                await self.queue.put(None)
                break
            await self._receive_packet(pkt)

        self.logger.info('Waiting for write loop task to end')
        await self.write_loop_task
        if self.state == 'connected':
            await self._trigger_event('disconnect', run_async=False)
            try:
                client.connected_clients.remove(self)
            except ValueError:  # pragma: no cover
                pass
            self._reset()
        self.logger.info('Exiting read loop task')

    async def _write_loop(self):
        """This background task sends packages to the server as they are
        pushed to the send queue.
        """
        while self.state == 'connected':
            # to simplify the timeout handling, use the maximum of the
            # ping interval and ping timeout as timeout, with an extra 5
            # seconds grace period
            timeout = max(self.ping_interval, self.ping_timeout) + 5
            packets = None
            try:
                packets = [await asyncio.wait_for(self.queue.get(), timeout)]
            except (self.queue.Empty, asyncio.TimeoutError,
                    asyncio.CancelledError):
                self.logger.error('packet queue is empty, aborting')
                break
            if packets == [None]:
                self.queue.task_done()
                packets = []
            else:
                while True:
                    try:
                        packets.append(self.queue.get_nowait())
                    except self.queue.Empty:
                        break
                    if packets[-1] is None:
                        packets = packets[:-1]
                        self.queue.task_done()
                        break
            if not packets:
                # empty packet list returned -> connection closed
                break
            if self.current_transport == 'polling':
                p = payload.Payload(packets=packets)
                r = await self._send_request(
                    'POST', self.base_url, body=p.encode(),
                    headers={'Content-Type': 'application/octet-stream'},
                    timeout=self.request_timeout)
                for pkt in packets:
                    self.queue.task_done()
                if r is None:
                    self.logger.warning(
                        'Connection refused by the server, aborting')
                    break
                if r.status < 200 or r.status >= 300:
                    self.logger.warning('Unexpected status code %s in server '
                                        'response, aborting', r.status)
                    self._reset()
                    break
            else:
                # websocket
                try:
                    for pkt in packets:
                        if pkt.binary:
                            await self.ws.send_bytes(pkt.encode())
                        else:
                            await self.ws.send_str(pkt.encode())
                        self.queue.task_done()
                except (aiohttp.client_exceptions.ServerDisconnectedError,
                        BrokenPipeError, OSError):
                    self.logger.info(
                        'Write loop: WebSocket connection was closed, '
                        'aborting')
                    break
        self.logger.info('Exiting write loop task')
