from .base_hub_connection import BaseHubConnection
from ..helpers import Helpers


class AuthHubConnection(BaseHubConnection):
    def __init__(self, auth_function, headers=None, **kwargs):
        if headers is None:
            self.headers = dict()
        else:
            self.headers = headers
        self.auth_function = auth_function
        super(AuthHubConnection, self).__init__(headers=headers, **kwargs)

    def start(self):
        try:
            Helpers.get_logger().debug("Starting connection ...")
            self.token = self.auth_function()
            Helpers.get_logger()\
                .debug("auth function result {0}".format(self.token))
            self.headers["Authorization"] = "Bearer " + self.token
            return super(AuthHubConnection, self).start()
        except Exception as ex:
            Helpers.get_logger().warning(self.__class__.__name__)
            Helpers.get_logger().warning(str(ex))
            raise ex
