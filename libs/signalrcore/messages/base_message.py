from .message_type import MessageType


class BaseMessage(object):
    def __init__(self, message_type, **kwargs):
        self.type = MessageType(message_type)


class BaseHeadersMessage(BaseMessage):
    """
        All messages expct ping can carry aditional headers
    """
    def __init__(self, message_type, headers={}, **kwargs):
        super(BaseHeadersMessage, self).__init__(message_type)
        self.headers = headers
