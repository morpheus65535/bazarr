from .base_message import BaseHeadersMessage
"""
A `Completion` message is a JSON object with the following properties

* `type` - A `Number` with the literal value `3`,
    indicating that this message is a `Completion`.
* `invocationId` - A `String` encoding the `Invocation ID` for a message.
* `result` - A `Token` encoding the result value
    (see "JSON Payload Encoding" for details).
    This field is **ignored** if `error` is present.
* `error` - A `String` encoding the error message.

It is a protocol error to include both a `result` and an `error` property
    in the `Completion` message. A conforming endpoint may immediately
    terminate the connection upon receiving such a message.

Example - A `Completion` message with no result or error

```json
{
    "type": 3,
    "invocationId": "123"
}
```

Example - A `Completion` message with a result

```json
{
    "type": 3,
    "invocationId": "123",
    "result": 42
}
```

Example - A `Completion` message with an error

```json
{
    "type": 3,
    "invocationId": "123",
    "error": "It didn't work!"
}
```

Example - The following `Completion` message is a protocol error
    because it has both of `result` and `error`

```json
{
    "type": 3,
    "invocationId": "123",
    "result": 42,
    "error": "It didn't work!"
}
```
"""


class CompletionClientStreamMessage(BaseHeadersMessage):
    def __init__(
            self, invocation_id, **kwargs):
        super(CompletionClientStreamMessage, self).__init__(3, **kwargs)
        self.invocation_id = invocation_id


class CompletionMessage(BaseHeadersMessage):
    def __init__(
            self,
            invocation_id,
            result,
            error,
            **kwargs):
        super(CompletionMessage, self).__init__(3, **kwargs)
        self.invocation_id = invocation_id
        self.result = result
        self.error = error
