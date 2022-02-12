class AnticaptchaException(Exception):
    def __init__(self, error_id, error_code, error_description, *args):
        super(AnticaptchaException, self).__init__(
            "[{}:{}]{}".format(error_code, error_id, error_description)
        )
        self.error_description = error_description
        self.error_id = error_id
        self.error_code = error_code


AnticatpchaException = AnticaptchaException


class InvalidWidthException(AnticaptchaException):
    def __init__(self, width):
        self.width = width
        msg = "Invalid width (%s). Can be one of these: 100, 50, 33, 25." % (
            self.width,
        )
        super(InvalidWidthException, self).__init__("AC-1", 1, msg)


class MissingNameException(AnticaptchaException):
    def __init__(self, cls):
        self.cls = cls
        msg = 'Missing name data in {0}. Provide {0}.__init__(name="X") or {0}.serialize(name="X")'.format(
            str(self.cls)
        )
        super(MissingNameException, self).__init__("AC-2", 2, msg)
