import os
import sys
import asyncio

from engineio.static_files import get_static_file


class ASGIApp:
    """ASGI application middleware for Engine.IO.

    This middleware dispatches traffic to an Engine.IO application. It can
    also serve a list of static files to the client, or forward unrelated
    HTTP traffic to another ASGI application.

    :param engineio_server: The Engine.IO server. Must be an instance of the
                            ``engineio.AsyncServer`` class.
    :param static_files: A dictionary with static file mapping rules. See the
                         documentation for details on this argument.
    :param other_asgi_app: A separate ASGI app that receives all other traffic.
    :param engineio_path: The endpoint where the Engine.IO application should
                          be installed. The default value is appropriate for
                          most cases.
    :param on_startup: function to be called on application startup; can be
                       coroutine
    :param on_shutdown: function to be called on application shutdown; can be
                        coroutine

    Example usage::

        import engineio
        import uvicorn

        eio = engineio.AsyncServer()
        app = engineio.ASGIApp(eio, static_files={
            '/': {'content_type': 'text/html', 'filename': 'index.html'},
            '/index.html': {'content_type': 'text/html',
                            'filename': 'index.html'},
        })
        uvicorn.run(app, '127.0.0.1', 5000)
    """
    def __init__(self, engineio_server, other_asgi_app=None,
                 static_files=None, engineio_path='engine.io',
                 on_startup=None, on_shutdown=None):
        self.engineio_server = engineio_server
        self.other_asgi_app = other_asgi_app
        self.engineio_path = engineio_path.strip('/')
        self.static_files = static_files or {}
        self.on_startup = on_startup
        self.on_shutdown = on_shutdown

    async def __call__(self, scope, receive, send):
        if scope['type'] in ['http', 'websocket'] and \
                scope['path'].startswith('/{0}/'.format(self.engineio_path)):
            await self.engineio_server.handle_request(scope, receive, send)
        else:
            static_file = get_static_file(scope['path'], self.static_files) \
                if scope['type'] == 'http' and self.static_files else None
            if static_file:
                await self.serve_static_file(static_file, receive, send)
            elif self.other_asgi_app is not None:
                await self.other_asgi_app(scope, receive, send)
            elif scope['type'] == 'lifespan':
                await self.lifespan(receive, send)
            else:
                await self.not_found(receive, send)

    async def serve_static_file(self, static_file, receive,
                                send):  # pragma: no cover
        event = await receive()
        if event['type'] == 'http.request':
            if os.path.exists(static_file['filename']):
                with open(static_file['filename'], 'rb') as f:
                    payload = f.read()
                await send({'type': 'http.response.start',
                            'status': 200,
                            'headers': [(b'Content-Type', static_file[
                                'content_type'].encode('utf-8'))]})
                await send({'type': 'http.response.body',
                            'body': payload})
            else:
                await self.not_found(receive, send)

    async def lifespan(self, receive, send):
        while True:
            event = await receive()
            if event['type'] == 'lifespan.startup':
                if self.on_startup:
                    try:
                        await self.on_startup() \
                            if asyncio.iscoroutinefunction(self.on_startup) \
                            else self.on_startup()
                    except:
                        await send({'type': 'lifespan.startup.failed'})
                        return
                await send({'type': 'lifespan.startup.complete'})
            elif event['type'] == 'lifespan.shutdown':
                if self.on_shutdown:
                    try:
                        await self.on_shutdown() \
                            if asyncio.iscoroutinefunction(self.on_shutdown) \
                            else self.on_shutdown()
                    except:
                        await send({'type': 'lifespan.shutdown.failed'})
                        return
                await send({'type': 'lifespan.shutdown.complete'})
                return

    async def not_found(self, receive, send):
        """Return a 404 Not Found error to the client."""
        await send({'type': 'http.response.start',
                    'status': 404,
                    'headers': [(b'Content-Type', b'text/plain')]})
        await send({'type': 'http.response.body',
                    'body': b'Not Found'})


async def translate_request(scope, receive, send):
    class AwaitablePayload(object):  # pragma: no cover
        def __init__(self, payload):
            self.payload = payload or b''

        async def read(self, length=None):
            if length is None:
                r = self.payload
                self.payload = b''
            else:
                r = self.payload[:length]
                self.payload = self.payload[length:]
            return r

    event = await receive()
    payload = b''
    if event['type'] == 'http.request':
        payload += event.get('body') or b''
        while event.get('more_body'):
            event = await receive()
            if event['type'] == 'http.request':
                payload += event.get('body') or b''
    elif event['type'] == 'websocket.connect':
        pass
    else:
        return {}

    raw_uri = scope['path'].encode('utf-8')
    if 'query_string' in scope and scope['query_string']:
        raw_uri += b'?' + scope['query_string']
    environ = {
        'wsgi.input': AwaitablePayload(payload),
        'wsgi.errors': sys.stderr,
        'wsgi.version': (1, 0),
        'wsgi.async': True,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'SERVER_SOFTWARE': 'asgi',
        'REQUEST_METHOD': scope.get('method', 'GET'),
        'PATH_INFO': scope['path'],
        'QUERY_STRING': scope.get('query_string', b'').decode('utf-8'),
        'RAW_URI': raw_uri.decode('utf-8'),
        'SCRIPT_NAME': '',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'REMOTE_ADDR': '127.0.0.1',
        'REMOTE_PORT': '0',
        'SERVER_NAME': 'asgi',
        'SERVER_PORT': '0',
        'asgi.receive': receive,
        'asgi.send': send,
        'asgi.scope': scope,
    }

    for hdr_name, hdr_value in scope['headers']:
        hdr_name = hdr_name.upper().decode('utf-8')
        hdr_value = hdr_value.decode('utf-8')
        if hdr_name == 'CONTENT-TYPE':
            environ['CONTENT_TYPE'] = hdr_value
            continue
        elif hdr_name == 'CONTENT-LENGTH':
            environ['CONTENT_LENGTH'] = hdr_value
            continue

        key = 'HTTP_%s' % hdr_name.replace('-', '_')
        if key in environ:
            hdr_value = '%s,%s' % (environ[key], hdr_value)

        environ[key] = hdr_value

    environ['wsgi.url_scheme'] = environ.get('HTTP_X_FORWARDED_PROTO', 'http')
    return environ


async def make_response(status, headers, payload, environ):
    headers = [(h[0].encode('utf-8'), h[1].encode('utf-8')) for h in headers]
    if environ['asgi.scope']['type'] == 'websocket':
        if status.startswith('200 '):
            await environ['asgi.send']({'type': 'websocket.accept',
                                        'headers': headers})
        else:
            await environ['asgi.send']({'type': 'websocket.close'})
        return

    await environ['asgi.send']({'type': 'http.response.start',
                                'status': int(status.split(' ')[0]),
                                'headers': headers})
    await environ['asgi.send']({'type': 'http.response.body',
                                'body': payload})


class WebSocket(object):  # pragma: no cover
    """
    This wrapper class provides an asgi WebSocket interface that is
    somewhat compatible with eventlet's implementation.
    """
    def __init__(self, handler):
        self.handler = handler
        self.asgi_receive = None
        self.asgi_send = None

    async def __call__(self, environ):
        self.asgi_receive = environ['asgi.receive']
        self.asgi_send = environ['asgi.send']
        await self.asgi_send({'type': 'websocket.accept'})
        await self.handler(self)

    async def close(self):
        await self.asgi_send({'type': 'websocket.close'})

    async def send(self, message):
        msg_bytes = None
        msg_text = None
        if isinstance(message, bytes):
            msg_bytes = message
        else:
            msg_text = message
        await self.asgi_send({'type': 'websocket.send',
                              'bytes': msg_bytes,
                              'text': msg_text})

    async def wait(self):
        event = await self.asgi_receive()
        if event['type'] != 'websocket.receive':
            raise IOError()
        return event.get('bytes') or event.get('text')


_async = {
    'asyncio': True,
    'translate_request': translate_request,
    'make_response': make_response,
    'websocket': WebSocket,
}
