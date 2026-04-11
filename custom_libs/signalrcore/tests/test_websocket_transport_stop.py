"""Regression tests for WebsocketTransport.stop() FD leak fix.

The original stop() only closed the WebSocket when state == connected,
leaking the file descriptor in all other states. The fix ensures _ws.close()
runs regardless of state.
"""
import sys
import unittest
from unittest.mock import MagicMock, patch

# Stub msgpack before any signalrcore imports — the messagepack_protocol
# module does `import msgpack` at the top level, and msgpack is an optional
# dependency that may not be installed in the test environment.
if 'msgpack' not in sys.modules:
    sys.modules['msgpack'] = MagicMock()

from signalrcore.transport.websockets.connection import ConnectionState
from signalrcore.transport.websockets.websocket_transport import WebsocketTransport


def _make_transport(**overrides):
    """Create a WebsocketTransport with mocked internals."""
    with patch.object(WebsocketTransport, '__init__', lambda self, **kw: None):
        t = WebsocketTransport()
    t.state = overrides.get('state', ConnectionState.disconnected)
    t._ws = overrides.get('ws', MagicMock())
    t.handshake_received = overrides.get('handshake', False)
    t.connection_checker = MagicMock()
    return t


class TestStopClosesWebSocket(unittest.TestCase):
    """stop() must close _ws in every state to prevent FD leaks."""

    # -- Per-state coverage (every ConnectionState value) --

    def test_stop_when_connected(self):
        t = _make_transport(state=ConnectionState.connected, handshake=True)
        t.stop()
        t.connection_checker.stop.assert_called_once()
        t._ws.close.assert_called_once()
        self.assertEqual(t.state, ConnectionState.disconnected)
        self.assertFalse(t.handshake_received)

    def test_stop_when_connecting(self):
        t = _make_transport(state=ConnectionState.connecting, handshake=False)
        t.stop()
        t.connection_checker.stop.assert_not_called()
        t._ws.close.assert_called_once()
        self.assertEqual(t.state, ConnectionState.disconnected)
        self.assertFalse(t.handshake_received)

    def test_stop_when_reconnecting(self):
        t = _make_transport(state=ConnectionState.reconnecting, handshake=False)
        t.stop()
        t.connection_checker.stop.assert_not_called()
        t._ws.close.assert_called_once()
        self.assertEqual(t.state, ConnectionState.disconnected)
        self.assertFalse(t.handshake_received)

    def test_stop_when_disconnected(self):
        t = _make_transport(state=ConnectionState.disconnected, handshake=False)
        t.stop()
        t.connection_checker.stop.assert_not_called()
        t._ws.close.assert_called_once()
        self.assertEqual(t.state, ConnectionState.disconnected)

    # -- ws=None safety --

    def test_stop_with_no_websocket(self):
        t = _make_transport(ws=None, handshake=True)
        t.stop()  # must not raise
        self.assertEqual(t.state, ConnectionState.disconnected)
        self.assertFalse(t.handshake_received)

    def test_stop_with_no_websocket_when_connected(self):
        """Edge case: state is connected but _ws was never assigned."""
        t = _make_transport(state=ConnectionState.connected, ws=None, handshake=True)
        t.stop()  # must not raise
        t.connection_checker.stop.assert_called_once()
        self.assertEqual(t.state, ConnectionState.disconnected)
        self.assertFalse(t.handshake_received)

    # -- Idempotency --

    def test_stop_is_idempotent(self):
        t = _make_transport(state=ConnectionState.connected, handshake=True)
        t.stop()
        t.stop()
        # Second call: state is already disconnected, checker not called again
        t.connection_checker.stop.assert_called_once()
        self.assertEqual(t._ws.close.call_count, 2)
        self.assertFalse(t.handshake_received)

    def test_stop_three_times(self):
        t = _make_transport(state=ConnectionState.connecting)
        for _ in range(3):
            t.stop()
        self.assertEqual(t._ws.close.call_count, 3)
        self.assertEqual(t.state, ConnectionState.disconnected)

    # -- Robustness: close() raising should not break state reset --

    def test_stop_still_resets_state_when_close_raises(self):
        t = _make_transport(state=ConnectionState.connected, handshake=True)
        t._ws.close.side_effect = OSError("socket already closed")
        with self.assertRaises(OSError):
            t.stop()
        # Even though close() raised, connection_checker.stop() ran first
        t.connection_checker.stop.assert_called_once()

    # -- All states covered exhaustively --

    def test_stop_closes_ws_in_every_state(self):
        """Parameterised check: _ws.close() is called for every ConnectionState."""
        for state in ConnectionState:
            with self.subTest(state=state.name):
                t = _make_transport(state=state)
                t.stop()
                t._ws.close.assert_called_once()
                self.assertEqual(t.state, ConnectionState.disconnected)
                self.assertFalse(t.handshake_received)


if __name__ == '__main__':
    unittest.main()
