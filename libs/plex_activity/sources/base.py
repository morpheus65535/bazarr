from pyemitter import Emitter
from threading import Thread
import logging

log = logging.getLogger(__name__)


class Source(Emitter):
    name = None

    def __init__(self):
        self.thread = Thread(target=self._run_wrapper)

    def start(self):
        self.thread.start()

    def run(self):
        pass

    def _run_wrapper(self):
        try:
            self.run()
        except Exception as ex:
            log.error('Exception raised in "%s" activity source: %s', self.name, ex, exc_info=True)
