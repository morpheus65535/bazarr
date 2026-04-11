from .base_message import BaseMessage
"""
A `Ping` message is a JSON object with the following properties:

* `type` - A `Number` with the literal value `6`,
    indicating that this message is a `Ping`.

Example
```json
{
    "type": 6
}
```
"""


class PingMessage(BaseMessage):
    def __init__(
            self, **kwargs):
        super(PingMessage, self).__init__(6, **kwargs)
