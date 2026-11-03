"""Regression coverage for bounded retries during a prolonged SignalR outage."""
import threading
import unittest
from unittest.mock import Mock, patch

from signalrcore.protocol.json_hub_protocol import JsonHubProtocol
from signalrcore.transport.websockets.connection import ConnectionState
from signalrcore.transport.websockets.reconnection import RawReconnectionHandler
from signalrcore.transport.websockets.websocket_transport import WebsocketTransport

TRANSPORT = 'signalrcore.transport.websockets.websocket_transport'


class ReconnectRegression(unittest.TestCase):
    def make_transport(self):
        transport = WebsocketTransport(
            protocol=JsonHubProtocol(),
            reconnection_handler=RawReconnectionHandler(180, None),
        )
        transport.logger = Mock()
        transport._on_reconnect = Mock()
        transport._ws = Mock()
        return transport

    def test_failed_pings_respect_retry_interval_without_creating_threads(self):
        transport = self.make_transport()
        transport.start = Mock(side_effect=ConnectionError('offline'))
        with patch(TRANSPORT + '.time.monotonic', return_value=100) as clock, \
                patch(TRANSPORT + '.threading.Thread') as thread:
            for _ in range(100):
                transport.handle_reconnect()
            self.assertEqual(transport.start.call_count, 1)
            thread.assert_not_called()
            clock.return_value = 281
            transport.handle_reconnect()
            self.assertEqual(transport.start.call_count, 2)
            thread.assert_not_called()
        transport._on_reconnect.assert_called_once()

    def test_stop_offline_stops_checker_and_prevents_retry(self):
        transport = self.make_transport()
        transport.state = ConnectionState.disconnected
        transport.connection_checker.running = True
        transport.start = Mock()
        transport.stop()
        self.assertFalse(transport.connection_checker.running)
        transport._ws.close.assert_called_once()
        transport.handle_reconnect()
        transport.start.assert_not_called()

    def test_recovery_preserves_checker_and_allows_explicit_restart(self):
        transport = self.make_transport()
        transport.connection_checker.running = True
        transport.negotiate = Mock(side_effect=[ConnectionError('offline'), None, None])
        with patch(TRANSPORT + '.time.monotonic', return_value=100) as clock, \
                patch(TRANSPORT + '.threading.Thread'), \
                patch(TRANSPORT + '.websocket.WebSocketApp'):
            transport.handle_reconnect()
            self.assertTrue(transport.connection_checker.running)
            clock.return_value = 281
            transport.handle_reconnect()
            self.assertEqual(transport.state, ConnectionState.connecting)
            transport.stop()
            transport.start()
            self.assertFalse(transport._stopped)

    def test_stop_during_negotiation_does_not_open_another_socket(self):
        transport = self.make_transport()
        # Model stop() being called by another thread while negotiate blocks.
        transport.negotiate = Mock(side_effect=transport.stop)
        with patch(TRANSPORT + '.websocket.WebSocketApp') as websocket_app:
            transport.handle_reconnect()
        websocket_app.assert_not_called()
        self.assertTrue(transport._stopped)

    def test_concurrent_attempt_does_not_negotiate(self):
        transport = self.make_transport()
        transport.start = Mock()
        transport._reconnect_lock.acquire()
        try:
            transport.handle_reconnect()
        finally:
            transport._reconnect_lock.release()
        transport.start.assert_not_called()


if __name__ == '__main__':
    unittest.main()
