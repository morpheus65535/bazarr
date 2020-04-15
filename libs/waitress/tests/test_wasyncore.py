from waitress import wasyncore as asyncore
from waitress import compat
import contextlib
import functools
import gc
import unittest
import select
import os
import socket
import sys
import time
import errno
import re
import struct
import threading
import warnings

from io import BytesIO

TIMEOUT = 3
HAS_UNIX_SOCKETS = hasattr(socket, "AF_UNIX")
HOST = "localhost"
HOSTv4 = "127.0.0.1"
HOSTv6 = "::1"

# Filename used for testing
if os.name == "java":  # pragma: no cover
    # Jython disallows @ in module names
    TESTFN = "$test"
else:
    TESTFN = "@test"

TESTFN = "{}_{}_tmp".format(TESTFN, os.getpid())


class DummyLogger(object):  # pragma: no cover
    def __init__(self):
        self.messages = []

    def log(self, severity, message):
        self.messages.append((severity, message))


class WarningsRecorder(object):  # pragma: no cover
    """Convenience wrapper for the warnings list returned on
       entry to the warnings.catch_warnings() context manager.
    """

    def __init__(self, warnings_list):
        self._warnings = warnings_list
        self._last = 0

    @property
    def warnings(self):
        return self._warnings[self._last :]

    def reset(self):
        self._last = len(self._warnings)


def _filterwarnings(filters, quiet=False):  # pragma: no cover
    """Catch the warnings, then check if all the expected
    warnings have been raised and re-raise unexpected warnings.
    If 'quiet' is True, only re-raise the unexpected warnings.
    """
    # Clear the warning registry of the calling module
    # in order to re-raise the warnings.
    frame = sys._getframe(2)
    registry = frame.f_globals.get("__warningregistry__")
    if registry:
        registry.clear()
    with warnings.catch_warnings(record=True) as w:
        # Set filter "always" to record all warnings.  Because
        # test_warnings swap the module, we need to look up in
        # the sys.modules dictionary.
        sys.modules["warnings"].simplefilter("always")
        yield WarningsRecorder(w)
    # Filter the recorded warnings
    reraise = list(w)
    missing = []
    for msg, cat in filters:
        seen = False
        for w in reraise[:]:
            warning = w.message
            # Filter out the matching messages
            if re.match(msg, str(warning), re.I) and issubclass(warning.__class__, cat):
                seen = True
                reraise.remove(w)
        if not seen and not quiet:
            # This filter caught nothing
            missing.append((msg, cat.__name__))
    if reraise:
        raise AssertionError("unhandled warning %s" % reraise[0])
    if missing:
        raise AssertionError("filter (%r, %s) did not catch any warning" % missing[0])


@contextlib.contextmanager
def check_warnings(*filters, **kwargs):  # pragma: no cover
    """Context manager to silence warnings.

    Accept 2-tuples as positional arguments:
        ("message regexp", WarningCategory)

    Optional argument:
     - if 'quiet' is True, it does not fail if a filter catches nothing
        (default True without argument,
         default False if some filters are defined)

    Without argument, it defaults to:
        check_warnings(("", Warning), quiet=True)
    """
    quiet = kwargs.get("quiet")
    if not filters:
        filters = (("", Warning),)
        # Preserve backward compatibility
        if quiet is None:
            quiet = True
    return _filterwarnings(filters, quiet)


def gc_collect():  # pragma: no cover
    """Force as many objects as possible to be collected.

    In non-CPython implementations of Python, this is needed because timely
    deallocation is not guaranteed by the garbage collector.  (Even in CPython
    this can be the case in case of reference cycles.)  This means that __del__
    methods may be called later than expected and weakrefs may remain alive for
    longer than expected.  This function tries its best to force all garbage
    objects to disappear.
    """
    gc.collect()
    if sys.platform.startswith("java"):
        time.sleep(0.1)
    gc.collect()
    gc.collect()


def threading_setup():  # pragma: no cover
    return (compat.thread._count(), None)


def threading_cleanup(*original_values):  # pragma: no cover
    global environment_altered

    _MAX_COUNT = 100

    for count in range(_MAX_COUNT):
        values = (compat.thread._count(), None)
        if values == original_values:
            break

        if not count:
            # Display a warning at the first iteration
            environment_altered = True
            sys.stderr.write(
                "Warning -- threading_cleanup() failed to cleanup "
                "%s threads" % (values[0] - original_values[0])
            )
            sys.stderr.flush()

        values = None

        time.sleep(0.01)
        gc_collect()


def reap_threads(func):  # pragma: no cover
    """Use this function when threads are being used.  This will
    ensure that the threads are cleaned up even when the test fails.
    """

    @functools.wraps(func)
    def decorator(*args):
        key = threading_setup()
        try:
            return func(*args)
        finally:
            threading_cleanup(*key)

    return decorator


def join_thread(thread, timeout=30.0):  # pragma: no cover
    """Join a thread. Raise an AssertionError if the thread is still alive
    after timeout seconds.
    """
    thread.join(timeout)
    if thread.is_alive():
        msg = "failed to join the thread in %.1f seconds" % timeout
        raise AssertionError(msg)


def bind_port(sock, host=HOST):  # pragma: no cover
    """Bind the socket to a free port and return the port number.  Relies on
    ephemeral ports in order to ensure we are using an unbound port.  This is
    important as many tests may be running simultaneously, especially in a
    buildbot environment.  This method raises an exception if the sock.family
    is AF_INET and sock.type is SOCK_STREAM, *and* the socket has SO_REUSEADDR
    or SO_REUSEPORT set on it.  Tests should *never* set these socket options
    for TCP/IP sockets.  The only case for setting these options is testing
    multicasting via multiple UDP sockets.

    Additionally, if the SO_EXCLUSIVEADDRUSE socket option is available (i.e.
    on Windows), it will be set on the socket.  This will prevent anyone else
    from bind()'ing to our host/port for the duration of the test.
    """

    if sock.family == socket.AF_INET and sock.type == socket.SOCK_STREAM:
        if hasattr(socket, "SO_REUSEADDR"):
            if sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR) == 1:
                raise RuntimeError(
                    "tests should never set the SO_REUSEADDR "
                    "socket option on TCP/IP sockets!"
                )
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                if sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT) == 1:
                    raise RuntimeError(
                        "tests should never set the SO_REUSEPORT "
                        "socket option on TCP/IP sockets!"
                    )
            except OSError:
                # Python's socket module was compiled using modern headers
                # thus defining SO_REUSEPORT but this process is running
                # under an older kernel that does not support SO_REUSEPORT.
                pass
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)

    sock.bind((host, 0))
    port = sock.getsockname()[1]
    return port


@contextlib.contextmanager
def closewrapper(sock):  # pragma: no cover
    try:
        yield sock
    finally:
        sock.close()


class dummysocket:  # pragma: no cover
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True

    def fileno(self):
        return 42

    def setblocking(self, yesno):
        self.isblocking = yesno

    def getpeername(self):
        return "peername"


class dummychannel:  # pragma: no cover
    def __init__(self):
        self.socket = dummysocket()

    def close(self):
        self.socket.close()


class exitingdummy:  # pragma: no cover
    def __init__(self):
        pass

    def handle_read_event(self):
        raise asyncore.ExitNow()

    handle_write_event = handle_read_event
    handle_close = handle_read_event
    handle_expt_event = handle_read_event


class crashingdummy:
    def __init__(self):
        self.error_handled = False

    def handle_read_event(self):
        raise Exception()

    handle_write_event = handle_read_event
    handle_close = handle_read_event
    handle_expt_event = handle_read_event

    def handle_error(self):
        self.error_handled = True


# used when testing senders; just collects what it gets until newline is sent
def capture_server(evt, buf, serv):  # pragma no cover
    try:
        serv.listen(0)
        conn, addr = serv.accept()
    except socket.timeout:
        pass
    else:
        n = 200
        start = time.time()
        while n > 0 and time.time() - start < 3.0:
            r, w, e = select.select([conn], [], [], 0.1)
            if r:
                n -= 1
                data = conn.recv(10)
                # keep everything except for the newline terminator
                buf.write(data.replace(b"\n", b""))
                if b"\n" in data:
                    break
            time.sleep(0.01)

        conn.close()
    finally:
        serv.close()
        evt.set()


def bind_unix_socket(sock, addr):  # pragma: no cover
    """Bind a unix socket, raising SkipTest if PermissionError is raised."""
    assert sock.family == socket.AF_UNIX
    try:
        sock.bind(addr)
    except PermissionError:
        sock.close()
        raise unittest.SkipTest("cannot bind AF_UNIX sockets")


def bind_af_aware(sock, addr):
    """Helper function to bind a socket according to its family."""
    if HAS_UNIX_SOCKETS and sock.family == socket.AF_UNIX:
        # Make sure the path doesn't exist.
        unlink(addr)
        bind_unix_socket(sock, addr)
    else:
        sock.bind(addr)


if sys.platform.startswith("win"):  # pragma: no cover

    def _waitfor(func, pathname, waitall=False):
        # Perform the operation
        func(pathname)
        # Now setup the wait loop
        if waitall:
            dirname = pathname
        else:
            dirname, name = os.path.split(pathname)
            dirname = dirname or "."
        # Check for `pathname` to be removed from the filesystem.
        # The exponential backoff of the timeout amounts to a total
        # of ~1 second after which the deletion is probably an error
        # anyway.
        # Testing on an i7@4.3GHz shows that usually only 1 iteration is
        # required when contention occurs.
        timeout = 0.001
        while timeout < 1.0:
            # Note we are only testing for the existence of the file(s) in
            # the contents of the directory regardless of any security or
            # access rights.  If we have made it this far, we have sufficient
            # permissions to do that much using Python's equivalent of the
            # Windows API FindFirstFile.
            # Other Windows APIs can fail or give incorrect results when
            # dealing with files that are pending deletion.
            L = os.listdir(dirname)
            if not (L if waitall else name in L):
                return
            # Increase the timeout and try again
            time.sleep(timeout)
            timeout *= 2
        warnings.warn(
            "tests may fail, delete still pending for " + pathname,
            RuntimeWarning,
            stacklevel=4,
        )

    def _unlink(filename):
        _waitfor(os.unlink, filename)


else:
    _unlink = os.unlink


def unlink(filename):
    try:
        _unlink(filename)
    except OSError:
        pass


def _is_ipv6_enabled():  # pragma: no cover
    """Check whether IPv6 is enabled on this host."""
    if compat.HAS_IPV6:
        sock = None
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.bind(("::1", 0))
            return True
        except socket.error:
            pass
        finally:
            if sock:
                sock.close()
    return False


IPV6_ENABLED = _is_ipv6_enabled()


class HelperFunctionTests(unittest.TestCase):
    def test_readwriteexc(self):
        # Check exception handling behavior of read, write and _exception

        # check that ExitNow exceptions in the object handler method
        # bubbles all the way up through asyncore read/write/_exception calls
        tr1 = exitingdummy()
        self.assertRaises(asyncore.ExitNow, asyncore.read, tr1)
        self.assertRaises(asyncore.ExitNow, asyncore.write, tr1)
        self.assertRaises(asyncore.ExitNow, asyncore._exception, tr1)

        # check that an exception other than ExitNow in the object handler
        # method causes the handle_error method to get called
        tr2 = crashingdummy()
        asyncore.read(tr2)
        self.assertEqual(tr2.error_handled, True)

        tr2 = crashingdummy()
        asyncore.write(tr2)
        self.assertEqual(tr2.error_handled, True)

        tr2 = crashingdummy()
        asyncore._exception(tr2)
        self.assertEqual(tr2.error_handled, True)

    # asyncore.readwrite uses constants in the select module that
    # are not present in Windows systems (see this thread:
    # http://mail.python.org/pipermail/python-list/2001-October/109973.html)
    # These constants should be present as long as poll is available

    @unittest.skipUnless(hasattr(select, "poll"), "select.poll required")
    def test_readwrite(self):
        # Check that correct methods are called by readwrite()

        attributes = ("read", "expt", "write", "closed", "error_handled")

        expected = (
            (select.POLLIN, "read"),
            (select.POLLPRI, "expt"),
            (select.POLLOUT, "write"),
            (select.POLLERR, "closed"),
            (select.POLLHUP, "closed"),
            (select.POLLNVAL, "closed"),
        )

        class testobj:
            def __init__(self):
                self.read = False
                self.write = False
                self.closed = False
                self.expt = False
                self.error_handled = False

            def handle_read_event(self):
                self.read = True

            def handle_write_event(self):
                self.write = True

            def handle_close(self):
                self.closed = True

            def handle_expt_event(self):
                self.expt = True

            # def handle_error(self):
            #     self.error_handled = True

        for flag, expectedattr in expected:
            tobj = testobj()
            self.assertEqual(getattr(tobj, expectedattr), False)
            asyncore.readwrite(tobj, flag)

            # Only the attribute modified by the routine we expect to be
            # called should be True.
            for attr in attributes:
                self.assertEqual(getattr(tobj, attr), attr == expectedattr)

            # check that ExitNow exceptions in the object handler method
            # bubbles all the way up through asyncore readwrite call
            tr1 = exitingdummy()
            self.assertRaises(asyncore.ExitNow, asyncore.readwrite, tr1, flag)

            # check that an exception other than ExitNow in the object handler
            # method causes the handle_error method to get called
            tr2 = crashingdummy()
            self.assertEqual(tr2.error_handled, False)
            asyncore.readwrite(tr2, flag)
            self.assertEqual(tr2.error_handled, True)

    def test_closeall(self):
        self.closeall_check(False)

    def test_closeall_default(self):
        self.closeall_check(True)

    def closeall_check(self, usedefault):
        # Check that close_all() closes everything in a given map

        l = []
        testmap = {}
        for i in range(10):
            c = dummychannel()
            l.append(c)
            self.assertEqual(c.socket.closed, False)
            testmap[i] = c

        if usedefault:
            socketmap = asyncore.socket_map
            try:
                asyncore.socket_map = testmap
                asyncore.close_all()
            finally:
                testmap, asyncore.socket_map = asyncore.socket_map, socketmap
        else:
            asyncore.close_all(testmap)

        self.assertEqual(len(testmap), 0)

        for c in l:
            self.assertEqual(c.socket.closed, True)

    def test_compact_traceback(self):
        try:
            raise Exception("I don't like spam!")
        except:
            real_t, real_v, real_tb = sys.exc_info()
            r = asyncore.compact_traceback()

        (f, function, line), t, v, info = r
        self.assertEqual(os.path.split(f)[-1], "test_wasyncore.py")
        self.assertEqual(function, "test_compact_traceback")
        self.assertEqual(t, real_t)
        self.assertEqual(v, real_v)
        self.assertEqual(info, "[%s|%s|%s]" % (f, function, line))


class DispatcherTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        asyncore.close_all()

    def test_basic(self):
        d = asyncore.dispatcher()
        self.assertEqual(d.readable(), True)
        self.assertEqual(d.writable(), True)

    def test_repr(self):
        d = asyncore.dispatcher()
        self.assertEqual(repr(d), "<waitress.wasyncore.dispatcher at %#x>" % id(d))

    def test_log_info(self):
        import logging

        inst = asyncore.dispatcher(map={})
        logger = DummyLogger()
        inst.logger = logger
        inst.log_info("message", "warning")
        self.assertEqual(logger.messages, [(logging.WARN, "message")])

    def test_log(self):
        import logging

        inst = asyncore.dispatcher()
        logger = DummyLogger()
        inst.logger = logger
        inst.log("message")
        self.assertEqual(logger.messages, [(logging.DEBUG, "message")])

    def test_unhandled(self):
        import logging

        inst = asyncore.dispatcher()
        logger = DummyLogger()
        inst.logger = logger

        inst.handle_expt()
        inst.handle_read()
        inst.handle_write()
        inst.handle_connect()

        expected = [
            (logging.WARN, "unhandled incoming priority event"),
            (logging.WARN, "unhandled read event"),
            (logging.WARN, "unhandled write event"),
            (logging.WARN, "unhandled connect event"),
        ]
        self.assertEqual(logger.messages, expected)

    def test_strerror(self):
        # refers to bug #8573
        err = asyncore._strerror(errno.EPERM)
        if hasattr(os, "strerror"):
            self.assertEqual(err, os.strerror(errno.EPERM))
        err = asyncore._strerror(-1)
        self.assertTrue(err != "")


class dispatcherwithsend_noread(asyncore.dispatcher_with_send):  # pragma: no cover
    def readable(self):
        return False

    def handle_connect(self):
        pass


class DispatcherWithSendTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        asyncore.close_all()

    @reap_threads
    def test_send(self):
        evt = threading.Event()
        sock = socket.socket()
        sock.settimeout(3)
        port = bind_port(sock)

        cap = BytesIO()
        args = (evt, cap, sock)
        t = threading.Thread(target=capture_server, args=args)
        t.start()
        try:
            # wait a little longer for the server to initialize (it sometimes
            # refuses connections on slow machines without this wait)
            time.sleep(0.2)

            data = b"Suppose there isn't a 16-ton weight?"
            d = dispatcherwithsend_noread()
            d.create_socket()
            d.connect((HOST, port))

            # give time for socket to connect
            time.sleep(0.1)

            d.send(data)
            d.send(data)
            d.send(b"\n")

            n = 1000
            while d.out_buffer and n > 0:  # pragma: no cover
                asyncore.poll()
                n -= 1

            evt.wait()

            self.assertEqual(cap.getvalue(), data * 2)
        finally:
            join_thread(t, timeout=TIMEOUT)


@unittest.skipUnless(
    hasattr(asyncore, "file_wrapper"), "asyncore.file_wrapper required"
)
class FileWrapperTest(unittest.TestCase):
    def setUp(self):
        self.d = b"It's not dead, it's sleeping!"
        with open(TESTFN, "wb") as file:
            file.write(self.d)

    def tearDown(self):
        unlink(TESTFN)

    def test_recv(self):
        fd = os.open(TESTFN, os.O_RDONLY)
        w = asyncore.file_wrapper(fd)
        os.close(fd)

        self.assertNotEqual(w.fd, fd)
        self.assertNotEqual(w.fileno(), fd)
        self.assertEqual(w.recv(13), b"It's not dead")
        self.assertEqual(w.read(6), b", it's")
        w.close()
        self.assertRaises(OSError, w.read, 1)

    def test_send(self):
        d1 = b"Come again?"
        d2 = b"I want to buy some cheese."
        fd = os.open(TESTFN, os.O_WRONLY | os.O_APPEND)
        w = asyncore.file_wrapper(fd)
        os.close(fd)

        w.write(d1)
        w.send(d2)
        w.close()
        with open(TESTFN, "rb") as file:
            self.assertEqual(file.read(), self.d + d1 + d2)

    @unittest.skipUnless(
        hasattr(asyncore, "file_dispatcher"), "asyncore.file_dispatcher required"
    )
    def test_dispatcher(self):
        fd = os.open(TESTFN, os.O_RDONLY)
        data = []

        class FileDispatcher(asyncore.file_dispatcher):
            def handle_read(self):
                data.append(self.recv(29))

        FileDispatcher(fd)
        os.close(fd)
        asyncore.loop(timeout=0.01, use_poll=True, count=2)
        self.assertEqual(b"".join(data), self.d)

    def test_resource_warning(self):
        # Issue #11453
        got_warning = False
        while got_warning is False:
            # we try until we get the outcome we want because this
            # test is not deterministic (gc_collect() may not
            fd = os.open(TESTFN, os.O_RDONLY)
            f = asyncore.file_wrapper(fd)

            os.close(fd)

            try:
                with check_warnings(("", compat.ResourceWarning)):
                    f = None
                    gc_collect()
            except AssertionError:  # pragma: no cover
                pass
            else:
                got_warning = True

    def test_close_twice(self):
        fd = os.open(TESTFN, os.O_RDONLY)
        f = asyncore.file_wrapper(fd)
        os.close(fd)

        os.close(f.fd)  # file_wrapper dupped fd
        with self.assertRaises(OSError):
            f.close()

        self.assertEqual(f.fd, -1)
        # calling close twice should not fail
        f.close()


class BaseTestHandler(asyncore.dispatcher):  # pragma: no cover
    def __init__(self, sock=None):
        asyncore.dispatcher.__init__(self, sock)
        self.flag = False

    def handle_accept(self):
        raise Exception("handle_accept not supposed to be called")

    def handle_accepted(self):
        raise Exception("handle_accepted not supposed to be called")

    def handle_connect(self):
        raise Exception("handle_connect not supposed to be called")

    def handle_expt(self):
        raise Exception("handle_expt not supposed to be called")

    def handle_close(self):
        raise Exception("handle_close not supposed to be called")

    def handle_error(self):
        raise


class BaseServer(asyncore.dispatcher):
    """A server which listens on an address and dispatches the
    connection to a handler.
    """

    def __init__(self, family, addr, handler=BaseTestHandler):
        asyncore.dispatcher.__init__(self)
        self.create_socket(family)
        self.set_reuse_addr()
        bind_af_aware(self.socket, addr)
        self.listen(5)
        self.handler = handler

    @property
    def address(self):
        return self.socket.getsockname()

    def handle_accepted(self, sock, addr):
        self.handler(sock)

    def handle_error(self):  # pragma: no cover
        raise


class BaseClient(BaseTestHandler):
    def __init__(self, family, address):
        BaseTestHandler.__init__(self)
        self.create_socket(family)
        self.connect(address)

    def handle_connect(self):
        pass


class BaseTestAPI:
    def tearDown(self):
        asyncore.close_all(ignore_all=True)

    def loop_waiting_for_flag(self, instance, timeout=5):  # pragma: no cover
        timeout = float(timeout) / 100
        count = 100
        while asyncore.socket_map and count > 0:
            asyncore.loop(timeout=0.01, count=1, use_poll=self.use_poll)
            if instance.flag:
                return
            count -= 1
            time.sleep(timeout)
        self.fail("flag not set")

    def test_handle_connect(self):
        # make sure handle_connect is called on connect()

        class TestClient(BaseClient):
            def handle_connect(self):
                self.flag = True

        server = BaseServer(self.family, self.addr)
        client = TestClient(self.family, server.address)
        self.loop_waiting_for_flag(client)

    def test_handle_accept(self):
        # make sure handle_accept() is called when a client connects

        class TestListener(BaseTestHandler):
            def __init__(self, family, addr):
                BaseTestHandler.__init__(self)
                self.create_socket(family)
                bind_af_aware(self.socket, addr)
                self.listen(5)
                self.address = self.socket.getsockname()

            def handle_accept(self):
                self.flag = True

        server = TestListener(self.family, self.addr)
        client = BaseClient(self.family, server.address)
        self.loop_waiting_for_flag(server)

    def test_handle_accepted(self):
        # make sure handle_accepted() is called when a client connects

        class TestListener(BaseTestHandler):
            def __init__(self, family, addr):
                BaseTestHandler.__init__(self)
                self.create_socket(family)
                bind_af_aware(self.socket, addr)
                self.listen(5)
                self.address = self.socket.getsockname()

            def handle_accept(self):
                asyncore.dispatcher.handle_accept(self)

            def handle_accepted(self, sock, addr):
                sock.close()
                self.flag = True

        server = TestListener(self.family, self.addr)
        client = BaseClient(self.family, server.address)
        self.loop_waiting_for_flag(server)

    def test_handle_read(self):
        # make sure handle_read is called on data received

        class TestClient(BaseClient):
            def handle_read(self):
                self.flag = True

        class TestHandler(BaseTestHandler):
            def __init__(self, conn):
                BaseTestHandler.__init__(self, conn)
                self.send(b"x" * 1024)

        server = BaseServer(self.family, self.addr, TestHandler)
        client = TestClient(self.family, server.address)
        self.loop_waiting_for_flag(client)

    def test_handle_write(self):
        # make sure handle_write is called

        class TestClient(BaseClient):
            def handle_write(self):
                self.flag = True

        server = BaseServer(self.family, self.addr)
        client = TestClient(self.family, server.address)
        self.loop_waiting_for_flag(client)

    def test_handle_close(self):
        # make sure handle_close is called when the other end closes
        # the connection

        class TestClient(BaseClient):
            def handle_read(self):
                # in order to make handle_close be called we are supposed
                # to make at least one recv() call
                self.recv(1024)

            def handle_close(self):
                self.flag = True
                self.close()

        class TestHandler(BaseTestHandler):
            def __init__(self, conn):
                BaseTestHandler.__init__(self, conn)
                self.close()

        server = BaseServer(self.family, self.addr, TestHandler)
        client = TestClient(self.family, server.address)
        self.loop_waiting_for_flag(client)

    def test_handle_close_after_conn_broken(self):
        # Check that ECONNRESET/EPIPE is correctly handled (issues #5661 and
        # #11265).

        data = b"\0" * 128

        class TestClient(BaseClient):
            def handle_write(self):
                self.send(data)

            def handle_close(self):
                self.flag = True
                self.close()

            def handle_expt(self):  # pragma: no cover
                # needs to exist for MacOS testing
                self.flag = True
                self.close()

        class TestHandler(BaseTestHandler):
            def handle_read(self):
                self.recv(len(data))
                self.close()

            def writable(self):
                return False

        server = BaseServer(self.family, self.addr, TestHandler)
        client = TestClient(self.family, server.address)
        self.loop_waiting_for_flag(client)

    @unittest.skipIf(
        sys.platform.startswith("sunos"), "OOB support is broken on Solaris"
    )
    def test_handle_expt(self):
        # Make sure handle_expt is called on OOB data received.
        # Note: this might fail on some platforms as OOB data is
        # tenuously supported and rarely used.
        if HAS_UNIX_SOCKETS and self.family == socket.AF_UNIX:
            self.skipTest("Not applicable to AF_UNIX sockets.")

        if sys.platform == "darwin" and self.use_poll:  # pragma: no cover
            self.skipTest("poll may fail on macOS; see issue #28087")

        class TestClient(BaseClient):
            def handle_expt(self):
                self.socket.recv(1024, socket.MSG_OOB)
                self.flag = True

        class TestHandler(BaseTestHandler):
            def __init__(self, conn):
                BaseTestHandler.__init__(self, conn)
                self.socket.send(compat.tobytes(chr(244)), socket.MSG_OOB)

        server = BaseServer(self.family, self.addr, TestHandler)
        client = TestClient(self.family, server.address)
        self.loop_waiting_for_flag(client)

    def test_handle_error(self):
        class TestClient(BaseClient):
            def handle_write(self):
                1.0 / 0

            def handle_error(self):
                self.flag = True
                try:
                    raise
                except ZeroDivisionError:
                    pass
                else:  # pragma: no cover
                    raise Exception("exception not raised")

        server = BaseServer(self.family, self.addr)
        client = TestClient(self.family, server.address)
        self.loop_waiting_for_flag(client)

    def test_connection_attributes(self):
        server = BaseServer(self.family, self.addr)
        client = BaseClient(self.family, server.address)

        # we start disconnected
        self.assertFalse(server.connected)
        self.assertTrue(server.accepting)
        # this can't be taken for granted across all platforms
        # self.assertFalse(client.connected)
        self.assertFalse(client.accepting)

        # execute some loops so that client connects to server
        asyncore.loop(timeout=0.01, use_poll=self.use_poll, count=100)
        self.assertFalse(server.connected)
        self.assertTrue(server.accepting)
        self.assertTrue(client.connected)
        self.assertFalse(client.accepting)

        # disconnect the client
        client.close()
        self.assertFalse(server.connected)
        self.assertTrue(server.accepting)
        self.assertFalse(client.connected)
        self.assertFalse(client.accepting)

        # stop serving
        server.close()
        self.assertFalse(server.connected)
        self.assertFalse(server.accepting)

    def test_create_socket(self):
        s = asyncore.dispatcher()
        s.create_socket(self.family)
        # self.assertEqual(s.socket.type, socket.SOCK_STREAM)
        self.assertEqual(s.socket.family, self.family)
        self.assertEqual(s.socket.gettimeout(), 0)
        # self.assertFalse(s.socket.get_inheritable())

    def test_bind(self):
        if HAS_UNIX_SOCKETS and self.family == socket.AF_UNIX:
            self.skipTest("Not applicable to AF_UNIX sockets.")
        s1 = asyncore.dispatcher()
        s1.create_socket(self.family)
        s1.bind(self.addr)
        s1.listen(5)
        port = s1.socket.getsockname()[1]

        s2 = asyncore.dispatcher()
        s2.create_socket(self.family)
        # EADDRINUSE indicates the socket was correctly bound
        self.assertRaises(socket.error, s2.bind, (self.addr[0], port))

    def test_set_reuse_addr(self):  # pragma: no cover
        if HAS_UNIX_SOCKETS and self.family == socket.AF_UNIX:
            self.skipTest("Not applicable to AF_UNIX sockets.")

        with closewrapper(socket.socket(self.family)) as sock:
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except OSError:
                unittest.skip("SO_REUSEADDR not supported on this platform")
            else:
                # if SO_REUSEADDR succeeded for sock we expect asyncore
                # to do the same
                s = asyncore.dispatcher(socket.socket(self.family))
                self.assertFalse(
                    s.socket.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)
                )
                s.socket.close()
                s.create_socket(self.family)
                s.set_reuse_addr()
                self.assertTrue(
                    s.socket.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)
                )

    @reap_threads
    def test_quick_connect(self):  # pragma: no cover
        # see: http://bugs.python.org/issue10340
        if self.family not in (socket.AF_INET, getattr(socket, "AF_INET6", object())):
            self.skipTest("test specific to AF_INET and AF_INET6")

        server = BaseServer(self.family, self.addr)
        # run the thread 500 ms: the socket should be connected in 200 ms
        t = threading.Thread(target=lambda: asyncore.loop(timeout=0.1, count=5))
        t.start()
        try:
            sock = socket.socket(self.family, socket.SOCK_STREAM)
            with closewrapper(sock) as s:
                s.settimeout(0.2)
                s.setsockopt(
                    socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0)
                )

                try:
                    s.connect(server.address)
                except OSError:
                    pass
        finally:
            join_thread(t, timeout=TIMEOUT)


class TestAPI_UseIPv4Sockets(BaseTestAPI):
    family = socket.AF_INET
    addr = (HOST, 0)


@unittest.skipUnless(IPV6_ENABLED, "IPv6 support required")
class TestAPI_UseIPv6Sockets(BaseTestAPI):
    family = socket.AF_INET6
    addr = (HOSTv6, 0)


@unittest.skipUnless(HAS_UNIX_SOCKETS, "Unix sockets required")
class TestAPI_UseUnixSockets(BaseTestAPI):
    if HAS_UNIX_SOCKETS:
        family = socket.AF_UNIX
    addr = TESTFN

    def tearDown(self):
        unlink(self.addr)
        BaseTestAPI.tearDown(self)


class TestAPI_UseIPv4Select(TestAPI_UseIPv4Sockets, unittest.TestCase):
    use_poll = False


@unittest.skipUnless(hasattr(select, "poll"), "select.poll required")
class TestAPI_UseIPv4Poll(TestAPI_UseIPv4Sockets, unittest.TestCase):
    use_poll = True


class TestAPI_UseIPv6Select(TestAPI_UseIPv6Sockets, unittest.TestCase):
    use_poll = False


@unittest.skipUnless(hasattr(select, "poll"), "select.poll required")
class TestAPI_UseIPv6Poll(TestAPI_UseIPv6Sockets, unittest.TestCase):
    use_poll = True


class TestAPI_UseUnixSocketsSelect(TestAPI_UseUnixSockets, unittest.TestCase):
    use_poll = False


@unittest.skipUnless(hasattr(select, "poll"), "select.poll required")
class TestAPI_UseUnixSocketsPoll(TestAPI_UseUnixSockets, unittest.TestCase):
    use_poll = True


class Test__strerror(unittest.TestCase):
    def _callFUT(self, err):
        from waitress.wasyncore import _strerror

        return _strerror(err)

    def test_gardenpath(self):
        self.assertEqual(self._callFUT(1), "Operation not permitted")

    def test_unknown(self):
        self.assertEqual(self._callFUT("wut"), "Unknown error wut")


class Test_read(unittest.TestCase):
    def _callFUT(self, dispatcher):
        from waitress.wasyncore import read

        return read(dispatcher)

    def test_gardenpath(self):
        inst = DummyDispatcher()
        self._callFUT(inst)
        self.assertTrue(inst.read_event_handled)
        self.assertFalse(inst.error_handled)

    def test_reraised(self):
        from waitress.wasyncore import ExitNow

        inst = DummyDispatcher(ExitNow)
        self.assertRaises(ExitNow, self._callFUT, inst)
        self.assertTrue(inst.read_event_handled)
        self.assertFalse(inst.error_handled)

    def test_non_reraised(self):
        inst = DummyDispatcher(OSError)
        self._callFUT(inst)
        self.assertTrue(inst.read_event_handled)
        self.assertTrue(inst.error_handled)


class Test_write(unittest.TestCase):
    def _callFUT(self, dispatcher):
        from waitress.wasyncore import write

        return write(dispatcher)

    def test_gardenpath(self):
        inst = DummyDispatcher()
        self._callFUT(inst)
        self.assertTrue(inst.write_event_handled)
        self.assertFalse(inst.error_handled)

    def test_reraised(self):
        from waitress.wasyncore import ExitNow

        inst = DummyDispatcher(ExitNow)
        self.assertRaises(ExitNow, self._callFUT, inst)
        self.assertTrue(inst.write_event_handled)
        self.assertFalse(inst.error_handled)

    def test_non_reraised(self):
        inst = DummyDispatcher(OSError)
        self._callFUT(inst)
        self.assertTrue(inst.write_event_handled)
        self.assertTrue(inst.error_handled)


class Test__exception(unittest.TestCase):
    def _callFUT(self, dispatcher):
        from waitress.wasyncore import _exception

        return _exception(dispatcher)

    def test_gardenpath(self):
        inst = DummyDispatcher()
        self._callFUT(inst)
        self.assertTrue(inst.expt_event_handled)
        self.assertFalse(inst.error_handled)

    def test_reraised(self):
        from waitress.wasyncore import ExitNow

        inst = DummyDispatcher(ExitNow)
        self.assertRaises(ExitNow, self._callFUT, inst)
        self.assertTrue(inst.expt_event_handled)
        self.assertFalse(inst.error_handled)

    def test_non_reraised(self):
        inst = DummyDispatcher(OSError)
        self._callFUT(inst)
        self.assertTrue(inst.expt_event_handled)
        self.assertTrue(inst.error_handled)


@unittest.skipUnless(hasattr(select, "poll"), "select.poll required")
class Test_readwrite(unittest.TestCase):
    def _callFUT(self, obj, flags):
        from waitress.wasyncore import readwrite

        return readwrite(obj, flags)

    def test_handle_read_event(self):
        flags = 0
        flags |= select.POLLIN
        inst = DummyDispatcher()
        self._callFUT(inst, flags)
        self.assertTrue(inst.read_event_handled)

    def test_handle_write_event(self):
        flags = 0
        flags |= select.POLLOUT
        inst = DummyDispatcher()
        self._callFUT(inst, flags)
        self.assertTrue(inst.write_event_handled)

    def test_handle_expt_event(self):
        flags = 0
        flags |= select.POLLPRI
        inst = DummyDispatcher()
        self._callFUT(inst, flags)
        self.assertTrue(inst.expt_event_handled)

    def test_handle_close(self):
        flags = 0
        flags |= select.POLLHUP
        inst = DummyDispatcher()
        self._callFUT(inst, flags)
        self.assertTrue(inst.close_handled)

    def test_socketerror_not_in_disconnected(self):
        flags = 0
        flags |= select.POLLIN
        inst = DummyDispatcher(socket.error(errno.EALREADY, "EALREADY"))
        self._callFUT(inst, flags)
        self.assertTrue(inst.read_event_handled)
        self.assertTrue(inst.error_handled)

    def test_socketerror_in_disconnected(self):
        flags = 0
        flags |= select.POLLIN
        inst = DummyDispatcher(socket.error(errno.ECONNRESET, "ECONNRESET"))
        self._callFUT(inst, flags)
        self.assertTrue(inst.read_event_handled)
        self.assertTrue(inst.close_handled)

    def test_exception_in_reraised(self):
        from waitress import wasyncore

        flags = 0
        flags |= select.POLLIN
        inst = DummyDispatcher(wasyncore.ExitNow)
        self.assertRaises(wasyncore.ExitNow, self._callFUT, inst, flags)
        self.assertTrue(inst.read_event_handled)

    def test_exception_not_in_reraised(self):
        flags = 0
        flags |= select.POLLIN
        inst = DummyDispatcher(ValueError)
        self._callFUT(inst, flags)
        self.assertTrue(inst.error_handled)


class Test_poll(unittest.TestCase):
    def _callFUT(self, timeout=0.0, map=None):
        from waitress.wasyncore import poll

        return poll(timeout, map)

    def test_nothing_writable_nothing_readable_but_map_not_empty(self):
        # i read the mock.patch docs.  nerp.
        dummy_time = DummyTime()
        map = {0: DummyDispatcher()}
        try:
            from waitress import wasyncore

            old_time = wasyncore.time
            wasyncore.time = dummy_time
            result = self._callFUT(map=map)
        finally:
            wasyncore.time = old_time
        self.assertEqual(result, None)
        self.assertEqual(dummy_time.sleepvals, [0.0])

    def test_select_raises_EINTR(self):
        # i read the mock.patch docs.  nerp.
        dummy_select = DummySelect(select.error(errno.EINTR))
        disp = DummyDispatcher()
        disp.readable = lambda: True
        map = {0: disp}
        try:
            from waitress import wasyncore

            old_select = wasyncore.select
            wasyncore.select = dummy_select
            result = self._callFUT(map=map)
        finally:
            wasyncore.select = old_select
        self.assertEqual(result, None)
        self.assertEqual(dummy_select.selected, [([0], [], [0], 0.0)])

    def test_select_raises_non_EINTR(self):
        # i read the mock.patch docs.  nerp.
        dummy_select = DummySelect(select.error(errno.EBADF))
        disp = DummyDispatcher()
        disp.readable = lambda: True
        map = {0: disp}
        try:
            from waitress import wasyncore

            old_select = wasyncore.select
            wasyncore.select = dummy_select
            self.assertRaises(select.error, self._callFUT, map=map)
        finally:
            wasyncore.select = old_select
        self.assertEqual(dummy_select.selected, [([0], [], [0], 0.0)])


class Test_poll2(unittest.TestCase):
    def _callFUT(self, timeout=0.0, map=None):
        from waitress.wasyncore import poll2

        return poll2(timeout, map)

    def test_select_raises_EINTR(self):
        # i read the mock.patch docs.  nerp.
        pollster = DummyPollster(exc=select.error(errno.EINTR))
        dummy_select = DummySelect(pollster=pollster)
        disp = DummyDispatcher()
        map = {0: disp}
        try:
            from waitress import wasyncore

            old_select = wasyncore.select
            wasyncore.select = dummy_select
            self._callFUT(map=map)
        finally:
            wasyncore.select = old_select
        self.assertEqual(pollster.polled, [0.0])

    def test_select_raises_non_EINTR(self):
        # i read the mock.patch docs.  nerp.
        pollster = DummyPollster(exc=select.error(errno.EBADF))
        dummy_select = DummySelect(pollster=pollster)
        disp = DummyDispatcher()
        map = {0: disp}
        try:
            from waitress import wasyncore

            old_select = wasyncore.select
            wasyncore.select = dummy_select
            self.assertRaises(select.error, self._callFUT, map=map)
        finally:
            wasyncore.select = old_select
        self.assertEqual(pollster.polled, [0.0])


class Test_dispatcher(unittest.TestCase):
    def _makeOne(self, sock=None, map=None):
        from waitress.wasyncore import dispatcher

        return dispatcher(sock=sock, map=map)

    def test_unexpected_getpeername_exc(self):
        sock = dummysocket()

        def getpeername():
            raise socket.error(errno.EBADF)

        map = {}
        sock.getpeername = getpeername
        self.assertRaises(socket.error, self._makeOne, sock=sock, map=map)
        self.assertEqual(map, {})

    def test___repr__accepting(self):
        sock = dummysocket()
        map = {}
        inst = self._makeOne(sock=sock, map=map)
        inst.accepting = True
        inst.addr = ("localhost", 8080)
        result = repr(inst)
        expected = "<waitress.wasyncore.dispatcher listening localhost:8080 at"
        self.assertEqual(result[: len(expected)], expected)

    def test___repr__connected(self):
        sock = dummysocket()
        map = {}
        inst = self._makeOne(sock=sock, map=map)
        inst.accepting = False
        inst.connected = True
        inst.addr = ("localhost", 8080)
        result = repr(inst)
        expected = "<waitress.wasyncore.dispatcher connected localhost:8080 at"
        self.assertEqual(result[: len(expected)], expected)

    def test_set_reuse_addr_with_socketerror(self):
        sock = dummysocket()
        map = {}

        def setsockopt(*arg, **kw):
            sock.errored = True
            raise socket.error

        sock.setsockopt = setsockopt
        sock.getsockopt = lambda *arg: 0
        inst = self._makeOne(sock=sock, map=map)
        inst.set_reuse_addr()
        self.assertTrue(sock.errored)

    def test_connect_raise_socket_error(self):
        sock = dummysocket()
        map = {}
        sock.connect_ex = lambda *arg: 1
        inst = self._makeOne(sock=sock, map=map)
        self.assertRaises(socket.error, inst.connect, 0)

    def test_accept_raise_TypeError(self):
        sock = dummysocket()
        map = {}

        def accept(*arg, **kw):
            raise TypeError

        sock.accept = accept
        inst = self._makeOne(sock=sock, map=map)
        result = inst.accept()
        self.assertEqual(result, None)

    def test_accept_raise_unexpected_socketerror(self):
        sock = dummysocket()
        map = {}

        def accept(*arg, **kw):
            raise socket.error(122)

        sock.accept = accept
        inst = self._makeOne(sock=sock, map=map)
        self.assertRaises(socket.error, inst.accept)

    def test_send_raise_EWOULDBLOCK(self):
        sock = dummysocket()
        map = {}

        def send(*arg, **kw):
            raise socket.error(errno.EWOULDBLOCK)

        sock.send = send
        inst = self._makeOne(sock=sock, map=map)
        result = inst.send("a")
        self.assertEqual(result, 0)

    def test_send_raise_unexpected_socketerror(self):
        sock = dummysocket()
        map = {}

        def send(*arg, **kw):
            raise socket.error(122)

        sock.send = send
        inst = self._makeOne(sock=sock, map=map)
        self.assertRaises(socket.error, inst.send, "a")

    def test_recv_raises_disconnect(self):
        sock = dummysocket()
        map = {}

        def recv(*arg, **kw):
            raise socket.error(errno.ECONNRESET)

        def handle_close():
            inst.close_handled = True

        sock.recv = recv
        inst = self._makeOne(sock=sock, map=map)
        inst.handle_close = handle_close
        result = inst.recv(1)
        self.assertEqual(result, b"")
        self.assertTrue(inst.close_handled)

    def test_close_raises_unknown_socket_error(self):
        sock = dummysocket()
        map = {}

        def close():
            raise socket.error(122)

        sock.close = close
        inst = self._makeOne(sock=sock, map=map)
        inst.del_channel = lambda: None
        self.assertRaises(socket.error, inst.close)

    def test_handle_read_event_not_accepting_not_connected_connecting(self):
        sock = dummysocket()
        map = {}
        inst = self._makeOne(sock=sock, map=map)

        def handle_connect_event():
            inst.connect_event_handled = True

        def handle_read():
            inst.read_handled = True

        inst.handle_connect_event = handle_connect_event
        inst.handle_read = handle_read
        inst.accepting = False
        inst.connected = False
        inst.connecting = True
        inst.handle_read_event()
        self.assertTrue(inst.connect_event_handled)
        self.assertTrue(inst.read_handled)

    def test_handle_connect_event_getsockopt_returns_error(self):
        sock = dummysocket()
        sock.getsockopt = lambda *arg: 122
        map = {}
        inst = self._makeOne(sock=sock, map=map)
        self.assertRaises(socket.error, inst.handle_connect_event)

    def test_handle_expt_event_getsockopt_returns_error(self):
        sock = dummysocket()
        sock.getsockopt = lambda *arg: 122
        map = {}
        inst = self._makeOne(sock=sock, map=map)

        def handle_close():
            inst.close_handled = True

        inst.handle_close = handle_close
        inst.handle_expt_event()
        self.assertTrue(inst.close_handled)

    def test_handle_write_event_while_accepting(self):
        sock = dummysocket()
        map = {}
        inst = self._makeOne(sock=sock, map=map)
        inst.accepting = True
        result = inst.handle_write_event()
        self.assertEqual(result, None)

    def test_handle_error_gardenpath(self):
        sock = dummysocket()
        map = {}
        inst = self._makeOne(sock=sock, map=map)

        def handle_close():
            inst.close_handled = True

        def compact_traceback(*arg, **kw):
            return None, None, None, None

        def log_info(self, *arg):
            inst.logged_info = arg

        inst.handle_close = handle_close
        inst.compact_traceback = compact_traceback
        inst.log_info = log_info
        inst.handle_error()
        self.assertTrue(inst.close_handled)
        self.assertEqual(inst.logged_info, ("error",))

    def test_handle_close(self):
        sock = dummysocket()
        map = {}
        inst = self._makeOne(sock=sock, map=map)

        def log_info(self, *arg):
            inst.logged_info = arg

        def close():
            inst._closed = True

        inst.log_info = log_info
        inst.close = close
        inst.handle_close()
        self.assertTrue(inst._closed)

    def test_handle_accepted(self):
        sock = dummysocket()
        map = {}
        inst = self._makeOne(sock=sock, map=map)
        inst.handle_accepted(sock, "1")
        self.assertTrue(sock.closed)


class Test_dispatcher_with_send(unittest.TestCase):
    def _makeOne(self, sock=None, map=None):
        from waitress.wasyncore import dispatcher_with_send

        return dispatcher_with_send(sock=sock, map=map)

    def test_writable(self):
        sock = dummysocket()
        map = {}
        inst = self._makeOne(sock=sock, map=map)
        inst.out_buffer = b"123"
        inst.connected = True
        self.assertTrue(inst.writable())


class Test_close_all(unittest.TestCase):
    def _callFUT(self, map=None, ignore_all=False):
        from waitress.wasyncore import close_all

        return close_all(map, ignore_all)

    def test_socketerror_on_close_ebadf(self):
        disp = DummyDispatcher(exc=socket.error(errno.EBADF))
        map = {0: disp}
        self._callFUT(map)
        self.assertEqual(map, {})

    def test_socketerror_on_close_non_ebadf(self):
        disp = DummyDispatcher(exc=socket.error(errno.EAGAIN))
        map = {0: disp}
        self.assertRaises(socket.error, self._callFUT, map)

    def test_reraised_exc_on_close(self):
        disp = DummyDispatcher(exc=KeyboardInterrupt)
        map = {0: disp}
        self.assertRaises(KeyboardInterrupt, self._callFUT, map)

    def test_unknown_exc_on_close(self):
        disp = DummyDispatcher(exc=RuntimeError)
        map = {0: disp}
        self.assertRaises(RuntimeError, self._callFUT, map)


class DummyDispatcher(object):
    read_event_handled = False
    write_event_handled = False
    expt_event_handled = False
    error_handled = False
    close_handled = False
    accepting = False

    def __init__(self, exc=None):
        self.exc = exc

    def handle_read_event(self):
        self.read_event_handled = True
        if self.exc is not None:
            raise self.exc

    def handle_write_event(self):
        self.write_event_handled = True
        if self.exc is not None:
            raise self.exc

    def handle_expt_event(self):
        self.expt_event_handled = True
        if self.exc is not None:
            raise self.exc

    def handle_error(self):
        self.error_handled = True

    def handle_close(self):
        self.close_handled = True

    def readable(self):
        return False

    def writable(self):
        return False

    def close(self):
        if self.exc is not None:
            raise self.exc


class DummyTime(object):
    def __init__(self):
        self.sleepvals = []

    def sleep(self, val):
        self.sleepvals.append(val)


class DummySelect(object):
    error = select.error

    def __init__(self, exc=None, pollster=None):
        self.selected = []
        self.pollster = pollster
        self.exc = exc

    def select(self, *arg):
        self.selected.append(arg)
        if self.exc is not None:
            raise self.exc

    def poll(self):
        return self.pollster


class DummyPollster(object):
    def __init__(self, exc=None):
        self.polled = []
        self.exc = exc

    def poll(self, timeout):
        self.polled.append(timeout)
        if self.exc is not None:
            raise self.exc
        else:  # pragma: no cover
            return []
