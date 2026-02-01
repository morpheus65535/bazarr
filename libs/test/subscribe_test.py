from test.base_test_case import BaseTestCase, Urls


class TestSendMethod(BaseTestCase):
    server_url = Urls.server_url_ssl

    def test_unsubscribe(self):
        def fake_callback(_):
            pass

        self.connection = self.get_connection()
        self.connection.on("ReceiveMessage", fake_callback)

        self.assertEqual(len(self.connection.handlers), 1)

        self.connection.unsubscribe("ReceiveMessage", fake_callback)

        self.assertEqual(len(self.connection.handlers), 0)
