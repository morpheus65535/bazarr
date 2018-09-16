_error_codes = {
    'NoTextError': 0,
    'FormatError': 1,
    'FileLoadError': 2,
    'DuplicateLangError': 3,
    'NeedLoadProfileError': 4,
    'CantDetectError': 5,
    'CantOpenTrainData': 6,
    'TrainDataFormatError': 7,
    'InitParamError': 8,
}

ErrorCode = type('ErrorCode', (), _error_codes)


class LangDetectException(Exception):
    def __init__(self, code, message):
        super(LangDetectException, self).__init__(message)
        self.code = code

    def get_code(self):
        return self.code
