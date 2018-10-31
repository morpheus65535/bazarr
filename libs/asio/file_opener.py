class FileOpener(object):
    def __init__(self, file_path, parameters=None):
        self.file_path = file_path
        self.parameters = parameters

        self.file = None

    def __enter__(self):
        self.file = ASIO.get_handler().open(
            self.file_path,
            self.parameters.handlers.get(ASIO.get_handler())
        )

        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.file:
            return

        self.file.close()
        self.file = None
