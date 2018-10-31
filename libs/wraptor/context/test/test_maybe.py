from threading import Thread

from wraptor.context import maybe

def test_basic():
    with maybe(lambda: False):
        assert False

    check = False
    with maybe(lambda: True):
        check = True
    assert check

def test_threads():
    def worker(arr, index):
        for i in range(5):
            with maybe(lambda: i == 3):
                arr[index] = True

    workers = 100
    arr = [False for i in range(workers)]
    threads = [Thread(target=worker, args=(arr, i)) for i in range(workers)]
    [t.start() for t in threads]
    [t.join() for t in threads]

    assert all(arr)
