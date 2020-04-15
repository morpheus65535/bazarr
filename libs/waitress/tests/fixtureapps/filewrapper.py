import io
import os

here = os.path.dirname(os.path.abspath(__file__))
fn = os.path.join(here, "groundhog1.jpg")


class KindaFilelike(object):  # pragma: no cover
    def __init__(self, bytes):
        self.bytes = bytes

    def read(self, n):
        bytes = self.bytes[:n]
        self.bytes = self.bytes[n:]
        return bytes


class UnseekableIOBase(io.RawIOBase):  # pragma: no cover
    def __init__(self, bytes):
        self.buf = io.BytesIO(bytes)

    def writable(self):
        return False

    def readable(self):
        return True

    def seekable(self):
        return False

    def read(self, n):
        return self.buf.read(n)


def app(environ, start_response):  # pragma: no cover
    path_info = environ["PATH_INFO"]
    if path_info.startswith("/filelike"):
        f = open(fn, "rb")
        f.seek(0, 2)
        cl = f.tell()
        f.seek(0)
        if path_info == "/filelike":
            headers = [
                ("Content-Length", str(cl)),
                ("Content-Type", "image/jpeg"),
            ]
        elif path_info == "/filelike_nocl":
            headers = [("Content-Type", "image/jpeg")]
        elif path_info == "/filelike_shortcl":
            # short content length
            headers = [
                ("Content-Length", "1"),
                ("Content-Type", "image/jpeg"),
            ]
        else:
            # long content length (/filelike_longcl)
            headers = [
                ("Content-Length", str(cl + 10)),
                ("Content-Type", "image/jpeg"),
            ]
    else:
        with open(fn, "rb") as fp:
            data = fp.read()
        cl = len(data)
        f = KindaFilelike(data)
        if path_info == "/notfilelike":
            headers = [
                ("Content-Length", str(len(data))),
                ("Content-Type", "image/jpeg"),
            ]
        elif path_info == "/notfilelike_iobase":
            headers = [
                ("Content-Length", str(len(data))),
                ("Content-Type", "image/jpeg"),
            ]
            f = UnseekableIOBase(data)
        elif path_info == "/notfilelike_nocl":
            headers = [("Content-Type", "image/jpeg")]
        elif path_info == "/notfilelike_shortcl":
            # short content length
            headers = [
                ("Content-Length", "1"),
                ("Content-Type", "image/jpeg"),
            ]
        else:
            # long content length (/notfilelike_longcl)
            headers = [
                ("Content-Length", str(cl + 10)),
                ("Content-Type", "image/jpeg"),
            ]

    start_response("200 OK", headers)
    return environ["wsgi.file_wrapper"](f, 8192)
