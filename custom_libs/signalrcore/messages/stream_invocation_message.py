from .base_message import BaseHeadersMessage
"""
A `StreamInvocation` message is a JSON object with the following properties:

* `type` - A `Number` with the literal value 4, indicating that
    this message is a StreamInvocation.
* `invocationId` - A `String` encoding the `Invocation ID` for a message.
* `target` - A `String` encoding the `Target` name, as expected
    by the Callee's Binder.
* `arguments` - An `Array` containing arguments to apply to
    the method referred to in Target. This is a sequence of JSON
    `Token`s, encoded as indicated below in the
    "JSON Payload Encoding" section.

Example:

```json
{
    "type": 4,
    "invocationId": "123",
    "target": "Send",
    "arguments": [
        42,
        "Test Message"
    ]
}
```
"""


class StreamInvocationMessage(BaseHeadersMessage):
    def __init__(
            self,
            invocation_id,
            target,
            arguments,
            **kwargs):
        super(StreamInvocationMessage, self).__init__(4, **kwargs)
        self.invocation_id = invocation_id
        self.target = target
        self.arguments = arguments
        self.stream_ids = []
