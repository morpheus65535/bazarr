from collections import namedtuple
import json


def app_body_only(environ, start_response):  # pragma: no cover
    cl = environ.get("CONTENT_LENGTH", None)
    if cl is not None:
        cl = int(cl)
    body = environ["wsgi.input"].read(cl)
    cl = str(len(body))
    start_response("200 OK", [("Content-Length", cl), ("Content-Type", "text/plain"),])
    return [body]


def app(environ, start_response):  # pragma: no cover
    cl = environ.get("CONTENT_LENGTH", None)
    if cl is not None:
        cl = int(cl)
    request_body = environ["wsgi.input"].read(cl)
    cl = str(len(request_body))
    meta = {
        "method": environ["REQUEST_METHOD"],
        "path_info": environ["PATH_INFO"],
        "script_name": environ["SCRIPT_NAME"],
        "query_string": environ["QUERY_STRING"],
        "content_length": cl,
        "scheme": environ["wsgi.url_scheme"],
        "remote_addr": environ["REMOTE_ADDR"],
        "remote_host": environ["REMOTE_HOST"],
        "server_port": environ["SERVER_PORT"],
        "server_name": environ["SERVER_NAME"],
        "headers": {
            k[len("HTTP_") :]: v for k, v in environ.items() if k.startswith("HTTP_")
        },
    }
    response = json.dumps(meta).encode("utf8") + b"\r\n\r\n" + request_body
    start_response(
        "200 OK",
        [("Content-Length", str(len(response))), ("Content-Type", "text/plain"),],
    )
    return [response]


Echo = namedtuple(
    "Echo",
    (
        "method path_info script_name query_string content_length scheme "
        "remote_addr remote_host server_port server_name headers body"
    ),
)


def parse_response(response):
    meta, body = response.split(b"\r\n\r\n", 1)
    meta = json.loads(meta.decode("utf8"))
    return Echo(body=body, **meta)
