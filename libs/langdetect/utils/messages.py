from os import path


class Messages(object):
    MESSAGES_FILENAME = path.join(path.dirname(__file__), 'messages.properties')

    def __init__(self):
        self.messages = {}
        with open(self.MESSAGES_FILENAME, 'r') as f:
            for line in f:
                key, _, value = line.strip().partition('=')
                self.messages[key] = value.encode().decode('unicode_escape')

    def get_string(self, key):
        return self.messages.get(key, '!%s!' % key)


_messages = None
def get_string(key):
    global _messages
    if _messages is None:
        _messages = Messages()
    return _messages.get_string(key)
