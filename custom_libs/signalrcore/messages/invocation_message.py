from .base_message import BaseHeadersMessage
"""

An `Invocation` message is a JSON object with the following properties:

* `type` - A `Number` with the literal value 1, indicating that this message
    is an Invocation.
* `invocationId` - An optional `String` encoding the `Invocation ID`
    for a message.
* `target` - A `String` encoding the `Target` name, as expected by the Callee's
    Binder
* `arguments` - An `Array` containing arguments to apply to the method
    referred to in Target. This is a sequence of JSON `Token`s,
        encoded as indicated below in the "JSON Payload Encoding" section

Example:

```json
{
    "type": 1,
    "invocationId": "123",
    "target": "Send",
    "arguments": [
        42,
        "Test Message"
    ]
}
```
Example (Non-Blocking):

```json
{
    "type": 1,
    "target": "Send",
    "arguments": [
        42,
        "Test Message"
    ]
}
```

"""


class InvocationMessage(BaseHeadersMessage):
    def __init__(
            self,
            invocation_id,
            target,
            arguments, **kwargs):
        super(InvocationMessage, self).__init__(1, **kwargs)
        self.invocation_id = invocation_id
        self.target = target
        self.arguments = arguments

    def __repr__(self):
        repr_str =\
            "InvocationMessage: invocation_id {0}, target {1}, arguments {2}"
        return repr_str.format(self.invocation_id, self.target, self.arguments)


class InvocationClientStreamMessage(BaseHeadersMessage):
    def __init__(
            self,
            stream_ids,
            target,
            arguments,
            **kwargs):
        super(InvocationClientStreamMessage, self).__init__(1, **kwargs)
        self.target = target
        self.arguments = arguments
        self.stream_ids = stream_ids

    def __repr__(self):
        repr_str =\
            "InvocationMessage: stream_ids {0}, target {1}, arguments {2}"
        return repr_str.format(
            self.stream_ids, self.target, self.arguments)
