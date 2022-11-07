import uuid
from .hub.base_hub_connection import BaseHubConnection
from .hub.auth_hub_connection import AuthHubConnection
from .transport.websockets.reconnection import \
    IntervalReconnectionHandler, RawReconnectionHandler, ReconnectionType
from .helpers import Helpers
from .messages.invocation_message import InvocationMessage
from .protocol.json_hub_protocol import JsonHubProtocol
from .subject import Subject


class HubConnectionBuilder(object):
    """
    Hub connection class, manages handshake and messaging

    Args:
        hub_url: SignalR core url

    Raises:
        HubConnectionError: Raises an Exception if url is empty or None
    """

    def __init__(self):
        self.hub_url = None
        self.hub = None
        self.options = {
            "access_token_factory": None
        }
        self.token = None
        self.headers = dict()
        self.negotiate_headers = None
        self.has_auth_configured = None
        self.protocol = None
        self.reconnection_handler = None
        self.keep_alive_interval = None
        self.verify_ssl = True
        self.enable_trace = False  # socket trace
        self.skip_negotiation = False  # By default do not skip negotiation
        self.running = False

    def with_url(
            self,
            hub_url: str,
            options: dict = None):
        """Configure the hub url and options like negotiation and auth function

        def login(self):
            response = requests.post(
                self.login_url,
                json={
                    "username": self.email,
                    "password": self.password
                    },verify=False)
            return response.json()["token"]

        self.connection = HubConnectionBuilder()\
            .with_url(self.server_url,
            options={
                "verify_ssl": False,
                "access_token_factory": self.login,
                "headers": {
                    "mycustomheader": "mycustomheadervalue"
                }
            })\
            .configure_logging(logging.ERROR)\
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 10,
                "reconnect_interval": 5,
                "max_attempts": 5
            }).build()

        Args:
            hub_url (string): Hub URL
            options ([dict], optional): [description]. Defaults to None.

        Raises:
            ValueError: If url is invalid
            TypeError: If options are not a dict or auth function
                is not callable

        Returns:
            [HubConnectionBuilder]: configured connection
        """
        if hub_url is None or hub_url.strip() == "":
            raise ValueError("hub_url must be a valid url.")

        if options is not None and type(options) != dict:
            raise TypeError(
                "options must be a dict {0}.".format(self.options))

        if options is not None \
                and "access_token_factory" in options.keys()\
                and not callable(options["access_token_factory"]):
            raise TypeError(
                "access_token_factory must be a function without params")

        if options is not None:
            self.has_auth_configured = \
                "access_token_factory" in options.keys()\
                and callable(options["access_token_factory"])

            self.skip_negotiation = "skip_negotiation" in options.keys()\
                and options["skip_negotiation"]

        self.hub_url = hub_url
        self.hub = None
        self.options = self.options if options is None else options
        return self

    def configure_logging(
            self, logging_level, socket_trace=False, handler=None):
        """Configures signalr logging

        Args:
            logging_level ([type]): logging.INFO | logging.DEBUG ...
                from python logging class
            socket_trace (bool, optional): Enables socket package trace.
                Defaults to False.
            handler ([type], optional):  Custom logging handler.
                Defaults to None.

        Returns:
            [HubConnectionBuilder]: Instance hub with logging configured
        """
        Helpers.configure_logger(logging_level, handler)
        self.enable_trace = socket_trace
        return self

    def with_hub_protocol(self, protocol):
        """Changes transport protocol
            from signalrcore.protocol.messagepack_protocol\
                import MessagePackHubProtocol

            HubConnectionBuilder()\
            .with_url(self.server_url, options={"verify_ssl":False})\
                ...
            .with_hub_protocol(MessagePackHubProtocol())\
                ...
            .build()
        Args:
            protocol (JsonHubProtocol|MessagePackHubProtocol):
                protocol instance

        Returns:
            HubConnectionBuilder: instance configured
        """
        self.protocol = protocol
        return self

    def build(self):
        """Configures the connection hub

        Raises:
            TypeError: Checks parameters an raises TypeError
                if one of them is wrong

        Returns:
            [HubConnectionBuilder]: [self object for fluent interface purposes]
        """
        if self.protocol is None:
            self.protocol = JsonHubProtocol()

        if "headers" in self.options.keys()\
                and type(self.options["headers"]) is dict:
            self.headers.update(self.options["headers"])

        if self.has_auth_configured:
            auth_function = self.options["access_token_factory"]
            if auth_function is None or not callable(auth_function):
                raise TypeError(
                    "access_token_factory is not function")
        if "verify_ssl" in self.options.keys()\
                and type(self.options["verify_ssl"]) is bool:
            self.verify_ssl = self.options["verify_ssl"]

        return AuthHubConnection(
                headers=self.headers,
                auth_function=auth_function,
                url=self.hub_url,
                protocol=self.protocol,
                keep_alive_interval=self.keep_alive_interval,
                reconnection_handler=self.reconnection_handler,
                verify_ssl=self.verify_ssl,
                skip_negotiation=self.skip_negotiation,
                enable_trace=self.enable_trace)\
            if self.has_auth_configured else\
            BaseHubConnection(
                url=self.hub_url,
                protocol=self.protocol,
                keep_alive_interval=self.keep_alive_interval,
                reconnection_handler=self.reconnection_handler,
                headers=self.headers,
                verify_ssl=self.verify_ssl,
                skip_negotiation=self.skip_negotiation,
                enable_trace=self.enable_trace)
            
    def with_automatic_reconnect(self, data: dict):
        """Configures automatic reconnection
            https://devblogs.microsoft.com/aspnet/asp-net-core-updates-in-net-core-3-0-preview-4/

            hub = HubConnectionBuilder()\
            .with_url(self.server_url, options={"verify_ssl":False})\
            .configure_logging(logging.ERROR)\
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 10,
                "reconnect_interval": 5,
                "max_attempts": 5
            })\
            .build()

        Args:
            data (dict): [dict with autmatic reconnection parameters]

        Returns:
            [HubConnectionBuilder]: [self object for fluent interface purposes]
        """
        reconnect_type = data.get("type", "raw")

        # Infinite reconnect attempts
        max_attempts = data.get("max_attempts", None)

        # 5 sec interval
        reconnect_interval = data.get("reconnect_interval", 5)

        keep_alive_interval = data.get("keep_alive_interval", 15)

        intervals = data.get("intervals", [])  # Reconnection intervals

        self.keep_alive_interval = keep_alive_interval

        reconnection_type = ReconnectionType[reconnect_type]

        if reconnection_type == ReconnectionType.raw:
            self.reconnection_handler = RawReconnectionHandler(
                reconnect_interval,
                max_attempts
            )
        if reconnection_type == ReconnectionType.interval:
            self.reconnection_handler = IntervalReconnectionHandler(
                intervals
            )
        return self
