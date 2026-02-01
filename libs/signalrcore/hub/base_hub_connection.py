import uuid
from typing import Callable, List, Union, Optional
from signalrcore.messages.message_type import MessageType
from signalrcore.messages.stream_invocation_message\
    import StreamInvocationMessage
from .errors import HubConnectionError
from signalrcore.helpers import Helpers
from .handlers import StreamHandler, InvocationHandler
from ..transport.websockets.websocket_transport import WebsocketTransport
from ..subject import Subject
from ..messages.invocation_message import InvocationMessage
from collections import defaultdict


class InvocationResult(object):
    def __init__(self, invocation_id) -> None:
        self.invocation_id = invocation_id
        self.message = None


class BaseHubConnection(object):
    def __init__(
            self,
            url,
            protocol,
            headers=None,
            **kwargs):
        if headers is None:
            self.headers = dict()
        else:
            self.headers = headers
        self.logger = Helpers.get_logger()
        self.handlers = defaultdict(list)
        self.stream_handlers = defaultdict(list)

        self._on_error = lambda error: self.logger.info(
            "on_error not defined {0}".format(error))

        self.transport = WebsocketTransport(
            url=url,
            protocol=protocol,
            headers=self.headers,
            on_message=self.on_message,
            **kwargs)

    def start(self) -> None:
        self.logger.debug("Connection started")
        return self.transport.start()

    def stop(self) -> None:
        self.logger.debug("Connection stop")
        return self.transport.stop()

    def on_close(self, callback) -> None:
        """Configures on_close connection callback.
            It will be raised on connection closed event
        connection.on_close(lambda: print("connection closed"))
        Args:
            callback (function): function without params
        """
        self.transport.on_close_callback(callback)

    def on_open(self, callback) -> None:
        """Configures on_open connection callback.
            It will be raised on connection open event
        connection.on_open(lambda: print(
            "connection opened "))
        Args:
            callback (function): function without params
        """
        self.transport.on_open_callback(callback)

    def on_error(self, callback) -> None:
        """Configures on_error connection callback. It will be raised
            if any hub method throws an exception.
        connection.on_error(lambda data:
            print(f"An exception was thrown closed{data.error}"))
        Args:
            callback (function): function with one parameter.
                A CompletionMessage object.
        """
        self._on_error = callback

    def on_reconnect(self, callback) -> None:
        """Configures on_reconnect reconnection callback.
            It will be raised on reconnection event
        connection.on_reconnect(lambda: print(
            "connection lost, reconnection in progress "))
        Args:
            callback (function): function without params
        """
        self.transport.on_reconnect_callback(callback)

    def on(self, event, callback_function: Callable) -> None:
        """Register a callback on the specified event
        Args:
            event (string):  Event name
            callback_function (Function): callback function,
                arguments will be bound
        """
        self.logger.debug("Handler registered started {0}".format(event))
        self.handlers[event].append(callback_function)

    def unsubscribe(self, event, callback_function: Callable) -> None:
        """Removes a callback from the specified event
        Args:
            event (string): Event name
            callback_function (Function): callback function,
                arguments will be bound
        """
        self.logger.debug("Handler removed {0}".format(event))

        self.handlers[event].remove(callback_function)

        if len(self.handlers[event]) == 0:
            del self.handlers[event]

    def send(self, method, arguments, on_invocation=None, invocation_id=None)\
            -> InvocationResult:
        """invokes a server function
        Deprecated: 0.96
            Use invoke instead
        Args:
            method (string): Method name
            arguments (list|Subject): Method parameters
            on_invocation (function, optional): On invocation send callback
                will be raised on send server function ends. Defaults to None.
            invocation_id (string, optional): Override invocation ID.
                Exceptions thrown by the hub will use this ID,
                making it easier to handle with the on_error call.

        Raises:
            HubConnectionError: If hub is not ready to send
            TypeError: If arguments are invalid list or Subject
        """
        return self.invoke(method, arguments, on_invocation, invocation_id)

    def invoke(
            self,
            method: str,
            arguments: Union[List, Subject],
            on_invocation: Optional[Callable] = None,
            invocation_id: Optional[str] = None)\
            -> InvocationResult:
        """invokes a server function

        Args:
            method (string): Method name
            arguments (list|Subject): Method parameters
            on_invocation (function, optional): On invocation send callback
                will be raised on send server function ends. Defaults to None.
            invocation_id (string, optional): Override invocation ID.
                Exceptions thrown by the hub will use this ID,
                making it easier to handle with the on_error call.

        Raises:
            HubConnectionError: If hub is not ready to send
            TypeError: If arguments are invalid list or Subject
        """
        if invocation_id is None:
            invocation_id = str(uuid.uuid4())

        if not self.transport.is_running():
            raise HubConnectionError(
                "Cannot connect to SignalR hub. Unable to transmit messages")

        if type(arguments) is not list and type(arguments) is not Subject:
            raise TypeError("Arguments of a message must be a list or subject")

        result = InvocationResult(invocation_id)

        if type(arguments) is list:
            message = InvocationMessage(
                invocation_id,
                method,
                arguments,
                headers=self.headers)

            if on_invocation:
                self.stream_handlers[message.invocation_id].append(
                    InvocationHandler(
                        message.invocation_id,
                        on_invocation))

            self.transport.send(message)
            result.message = message

        if type(arguments) is Subject:
            arguments.connection = self
            arguments.target = method
            arguments.start()
            result.invocation_id = arguments.invocation_id
            result.message = arguments

        return result

    def on_message(self, messages) -> None:
        for message in messages:
            if message.type == MessageType.invocation_binding_failure:
                self.logger.error(message)
                self._on_error(message)
                continue

            if message.type == MessageType.ping:
                continue

            if message.type == MessageType.invocation:

                fired_handlers = self.handlers.get(message.target, [])

                if len(fired_handlers) == 0:
                    self.logger.debug(
                        f"event '{message.target}' hasn't fired any handler")

                for handler in fired_handlers:
                    handler(message.arguments)

            if message.type == MessageType.close:
                self.logger.info("Close message received from server")
                self.transport.dispose()
                return

            if message.type == MessageType.completion:
                if message.error is not None and len(message.error) > 0:
                    self._on_error(message)

                # Send callbacks
                fired_handlers = self.stream_handlers.get(
                    message.invocation_id, [])

                # Stream callbacks
                for handler in fired_handlers:
                    handler.complete_callback(message)

                # unregister handler
                if message.invocation_id in self.stream_handlers:
                    del self.stream_handlers[message.invocation_id]

            if message.type == MessageType.stream_item:
                fired_handlers = self.stream_handlers.get(
                    message.invocation_id, [])

                if len(fired_handlers) == 0:
                    self.logger.warning(
                        "id '{0}' hasn't fire any stream handler".format(
                            message.invocation_id))

                for handler in fired_handlers:
                    handler.next_callback(message.item)

            if message.type == MessageType.stream_invocation:
                pass

            if message.type == MessageType.cancel_invocation:
                fired_handlers = self.stream_handlers.get(
                    message.invocation_id, [])

                if len(fired_handlers) == 0:
                    self.logger.warning(
                        "id '{0}' hasn't fire any stream handler".format(
                            message.invocation_id))

                for handler in fired_handlers:
                    handler.error_callback(message)

                # unregister handler
                if message.invocation_id in self.stream_handlers:
                    del self.stream_handlers[message.invocation_id]

    def stream(self, event, event_params) -> StreamHandler:
        """Starts server streaming
            connection.stream(
            "Counter",
            [len(self.items), 500])\
            .subscribe({
                "next": self.on_next,
                "complete": self.on_complete,
                "error": self.on_error
            })
        Args:
            event (string): Method Name
            event_params (list): Method parameters

        Returns:
            [StreamHandler]: stream handler
        """
        invocation_id = str(uuid.uuid4())
        stream_obj = StreamHandler(event, invocation_id)
        self.stream_handlers[invocation_id].append(stream_obj)
        self.transport.send(
            StreamInvocationMessage(
                invocation_id,
                event,
                event_params,
                headers=self.headers))
        return stream_obj
