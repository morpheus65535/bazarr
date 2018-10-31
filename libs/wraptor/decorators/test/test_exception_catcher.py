from wraptor.decorators import exception_catcher
import threading
import pytest

def test_basic():

    @exception_catcher
    def work():
        raise Exception()

    t = threading.Thread(target=work)
    t.start()
    t.join()

    with pytest.raises(Exception):
        work.check()
