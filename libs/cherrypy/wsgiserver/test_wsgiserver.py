from unittest import mock

import six

from cherrypy import wsgiserver


class TestWSGIGateway_u0:
    @mock.patch('cherrypy.wsgiserver.WSGIGateway_10.get_environ',
        lambda self: {'foo': 'bar'})
    def test_decodes_items(self):
        req = mock.MagicMock(path=b'/', qs=b'')
        gw = wsgiserver.WSGIGateway_u0(req=req)
        env = gw.get_environ()
        assert env['foo'] == 'bar'
        assert isinstance(env['foo'], six.text_type)
