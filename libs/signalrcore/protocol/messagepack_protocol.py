import json
import msgpack
from .base_hub_protocol import BaseHubProtocol
from ..messages.handshake.request import HandshakeRequestMessage
from ..messages.handshake.response import HandshakeResponseMessage
from ..messages.invocation_message\
    import InvocationMessage, InvocationClientStreamMessage  # 1
from ..messages.stream_item_message import StreamItemMessage  # 2
from ..messages.completion_message import CompletionMessage  # 3
from ..messages.stream_invocation_message import StreamInvocationMessage  # 4
from ..messages.cancel_invocation_message import CancelInvocationMessage  # 5
from ..messages.ping_message import PingMessage  # 6
from ..messages.close_message import CloseMessage  # 7
from ..helpers import Helpers


class MessagePackHubProtocol(BaseHubProtocol):

    _priority = [
        "type",
        "headers",
        "invocation_id",
        "target",
        "arguments",
        "item",
        "result_kind",
        "result",
        "stream_ids"
    ]

    def __init__(self):
        super(MessagePackHubProtocol, self).__init__(
            "messagepack", 1, "Text", chr(0x1E))
        self.logger = Helpers.get_logger()

    def parse_messages(self, raw):
        try:
            messages = []
            offset = 0
            while offset < len(raw):
                length = msgpack.unpackb(raw[offset: offset + 1])
                values = msgpack.unpackb(raw[offset + 1: offset + length + 1])
                offset = offset + length + 1
                message = self._decode_message(values)
                messages.append(message)
        except Exception as ex:
            Helpers.get_logger().error("Parse messages Error {0}".format(ex))
            Helpers.get_logger().error("raw msg '{0}'".format(raw))
        return messages

    def decode_handshake(self, raw_message):
        try:
            has_various_messages = 0x1E in raw_message
            handshake_data = raw_message[0: raw_message.index(0x1E)] if has_various_messages else raw_message
            messages = self.parse_messages(raw_message[raw_message.index(0x1E) + 1:]) if has_various_messages else []
            data = json.loads(handshake_data)
            return HandshakeResponseMessage(data.get("error", None)), messages
        except Exception as ex:
            if type(raw_message) is str:
                data = json.loads(raw_message[0: raw_message.index("}") + 1])
                return HandshakeResponseMessage(data.get("error", None)), []
            Helpers.get_logger().error(raw_message)
            Helpers.get_logger().error(ex)
            raise ex

    def encode(self, message):
        if type(message) is HandshakeRequestMessage:
            content = json.dumps(message.__dict__)
            return content + self.record_separator

        msg = self._encode_message(message)
        encoded_message = msgpack.packb(msg)
        varint_length = self._to_varint(len(encoded_message))
        return varint_length + encoded_message

    def _encode_message(self, message):
        result = []

        # sort attributes
        for attribute in self._priority:
            if hasattr(message, attribute):
                if (attribute == "type"):
                    result.append(getattr(message, attribute).value)
                else:
                    result.append(getattr(message, attribute))
        return result

    def _decode_message(self, raw):
        # {} {"error"}
        # [1, Headers, InvocationId, Target, [Arguments], [StreamIds]]
        # [2, Headers, InvocationId, Item]
        # [3, Headers, InvocationId, ResultKind, Result]
        # [4, Headers, InvocationId, Target, [Arguments], [StreamIds]]
        # [5, Headers, InvocationId]
        # [6]
        # [7, Error, AllowReconnect?]

        if raw[0] == 1:  # InvocationMessage
            if len(raw[5]) > 0:
                return InvocationClientStreamMessage(
                    headers=raw[1],
                    stream_ids=raw[5],
                    target=raw[3],
                    arguments=raw[4])
            else:
                return InvocationMessage(
                    headers=raw[1],
                    invocation_id=raw[2],
                    target=raw[3],
                    arguments=raw[4])

        elif raw[0] == 2:  # StreamItemMessage
            return StreamItemMessage(
                headers=raw[1],
                invocation_id=raw[2],
                item=raw[3])

        elif raw[0] == 3:  # CompletionMessage
            result_kind = raw[3]
            if result_kind == 1:
                return CompletionMessage(
                    headers=raw[1],
                    invocation_id=raw[2],
                    result=None,
                    error=raw[4])

            elif result_kind == 2:
                return CompletionMessage(
                    headers=raw[1], invocation_id=raw[2],
                    result=None, error=None)

            elif result_kind == 3:
                return CompletionMessage(
                    headers=raw[1], invocation_id=raw[2],
                    result=raw[4], error=None)
            else:
                raise Exception("Unknown result kind.")

        elif raw[0] == 4:  # StreamInvocationMessage
            return StreamInvocationMessage(
                headers=raw[1], invocation_id=raw[2],
                target=raw[3], arguments=raw[4])  # stream_id missing?

        elif raw[0] == 5:  # CancelInvocationMessage
            return CancelInvocationMessage(
                headers=raw[1], invocation_id=raw[2])

        elif raw[0] == 6:  # PingMessageEncoding
            return PingMessage()

        elif raw[0] == 7:  # CloseMessageEncoding
            return CloseMessage(error=raw[1])  # AllowReconnect is missing
        print(".......................................")
        print(raw)
        print("---------------------------------------")
        raise Exception("Unknown message type.")

    def _to_varint(self, value):
        buffer = b''

        while True:

            byte = value & 0x7f
            value >>= 7

            if value:
                buffer += bytes((byte | 0x80, ))
            else:
                buffer += bytes((byte, ))
                break

        return buffer
