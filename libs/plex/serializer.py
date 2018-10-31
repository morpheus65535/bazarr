import jsonpickle


class Serializer(object):
    @classmethod
    def encode(cls, value):
        return jsonpickle.encode(value)

    @classmethod
    def decode(cls, value, client=None):
        try:
            result = jsonpickle.decode(value)
            result.client = client

            return result
        except:
            return None
