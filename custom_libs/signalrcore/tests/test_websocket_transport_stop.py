"""Regression tests for WebsocketTransport.stop() FD leak fix.

The original stop() only closed the WebSocket when state == connected,
leaking the file descriptor in all other states. The fix ensures _ws.close()
runs regardless of state.
"""
import unittest
from unittest.mock import MagicMock, patch

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

    def test_stop_when_connected(self):
        t = _make_transport(state=ConnectionState.connected, handshake=True)
        t.stop()
        t.connection_checker.stop.assert_called_once()
        t._ws.close.assert_called_once()
        self.assertEqual(t.state, ConnectionState.disconnected)
        self.assertFalse(t.handshake_received)

    def test_stop_when_connecting(self):
        t = _make_transport(state=ConnectionState.connecting)
        t.stop()
        t.connection_checker.stop.assert_not_called()
        t._ws.close.assert_called_once()
        self.assertEqual(t.state, ConnectionState.disconnected)

    def test_stop_when_disconnected(self):
        t = _make_transport(state=ConnectionState.disconnected)
        t.stop()
        t.connection_checker.stop.assert_not_called()
        t._ws.close.assert_called_once()
        self.assertEqual(t.state, ConnectionState.disconnected)

    def test_stop_with_no_websocket(self):
        t = _make_transport(ws=None)
        t.stop()
        # Must not raise; state must still reset
        self.assertEqual(t.state, ConnectionState.disconnected)
        self.assertFalse(t.handshake_received)

    def test_stop_is_idempotent(self):
        t = _make_transport(state=ConnectionState.connected)
        t.stop()
        t.stop()
        # Second call: state is already disconnected, checker not called again
        t.connection_checker.stop.assert_called_once()
        self.assertEqual(t._ws.close.call_count, 2)


if __name__ == '__main__':
    unittest.main()
