# mypy: ignore-errors

import collections
import itertools
import json
import random
from threading import Lock
from threading import Thread
import time
import uuid

import pytest

from dogpile.cache import CacheRegion
from dogpile.cache import register_backend
from dogpile.cache.api import CacheBackend
from dogpile.cache.api import CacheMutex
from dogpile.cache.api import CantDeserializeException
from dogpile.cache.api import NO_VALUE
from dogpile.cache.region import _backend_loader
from .assertions import assert_raises_message
from .assertions import eq_


def gen_some_key():
    return f"some_key_{random.randint(1, 100000)}"


class _GenericBackendFixture:
    @classmethod
    def setup_class(cls):
        backend_cls = _backend_loader.load(cls.backend)
        try:
            arguments = cls.config_args.get("arguments", {})
            backend = backend_cls(arguments)
        except ImportError:
            pytest.skip("Backend %s not installed" % cls.backend)
        cls._check_backend_available(backend)

    def teardown_method(self, method):
        some_key = gen_some_key()
        if self._region_inst:
            for key in self._keys:
                self._region_inst.delete(key)
            self._keys.clear()
        elif self._backend_inst:
            self._backend_inst.delete(some_key)

    @classmethod
    def _check_backend_available(cls, backend):
        pass

    region_args = {}
    config_args = {}
    extra_arguments = {}

    _region_inst = None
    _backend_inst = None

    _keys = set()

    def _region(self, backend=None, region_args={}, config_args={}):
        _region_args = {}

        # TODO: maybe we use a class-level naming convention instead
        # of a dict here so that arguments merge naturally

        for cls in reversed(self.__class__.__mro__):
            if "region_args" in cls.__dict__:
                _region_args.update(cls.__dict__["region_args"])

        _region_args.update(**region_args)
        _config_args = self.config_args.copy()
        _config_args.update(config_args)

        def _store_keys(key):
            if existing_key_mangler:
                key = existing_key_mangler(key)
            self._keys.add(key)
            return key

        self._region_inst = reg = CacheRegion(**_region_args)

        existing_key_mangler = self._region_inst.key_mangler
        self._region_inst.key_mangler = _store_keys
        self._region_inst._user_defined_key_mangler = _store_keys

        reg.configure(backend or self.backend, **_config_args)
        return reg

    def _backend(self):
        backend_cls = _backend_loader.load(self.backend)
        _config_args = self.config_args.copy()
        arguments = _config_args.get("arguments", {})
        arguments = {**arguments, **self.extra_arguments}
        self._backend_inst = backend_cls(arguments)
        return self._backend_inst


class _GenericBackendTestSuite(_GenericBackendFixture):
    def test_backend_get_nothing(self):
        backend = self._backend()
        some_key = gen_some_key()
        eq_(backend.get_serialized(some_key), NO_VALUE)

    def test_backend_delete_nothing(self):
        backend = self._backend()
        some_key = gen_some_key()
        backend.delete(some_key)

    def test_backend_set_get_value(self):
        backend = self._backend()
        some_key = gen_some_key()
        backend.set_serialized(some_key, b"some value")
        eq_(backend.get_serialized(some_key), b"some value")

    def test_backend_delete(self):
        backend = self._backend()
        some_key = gen_some_key()
        backend.set_serialized(some_key, b"some value")
        backend.delete(some_key)
        eq_(backend.get_serialized(some_key), NO_VALUE)

    def test_region_is_key_locked(self):
        reg = self._region()
        random_key = str(uuid.uuid1())
        assert not reg.get(random_key)
        eq_(reg.key_is_locked(random_key), False)
        # ensures that calling key_is_locked doesn't acquire the lock
        eq_(reg.key_is_locked(random_key), False)

        mutex = reg.backend.get_mutex(random_key)
        if mutex:
            mutex.acquire()
            eq_(reg.key_is_locked(random_key), True)
            mutex.release()
            eq_(reg.key_is_locked(random_key), False)

    def test_region_set_get_value(self):
        reg = self._region()
        some_key = gen_some_key()
        reg.set(some_key, "some value")
        eq_(reg.get(some_key), "some value")

    def test_region_set_multiple_values(self):
        reg = self._region()
        values = {"key1": "value1", "key2": "value2", "key3": "value3"}
        reg.set_multi(values)
        eq_(values["key1"], reg.get("key1"))
        eq_(values["key2"], reg.get("key2"))
        eq_(values["key3"], reg.get("key3"))

    def test_region_get_zero_multiple_values(self):
        reg = self._region()
        eq_(reg.get_multi([]), [])

    def test_region_set_zero_multiple_values(self):
        reg = self._region()
        reg.set_multi({})

    def test_region_set_zero_multiple_values_w_decorator(self):
        reg = self._region()
        values = reg.get_or_create_multi([], lambda: 0)
        eq_(values, [])

    def test_region_get_or_create_multi_w_should_cache_none(self):
        reg = self._region()
        values = reg.get_or_create_multi(
            ["key1", "key2", "key3"],
            lambda *k: [None, None, None],
            should_cache_fn=lambda v: v is not None,
        )
        eq_(values, [None, None, None])

    def test_region_get_multiple_values(self):
        reg = self._region()
        key1 = "value1"
        key2 = "value2"
        key3 = "value3"
        reg.set("key1", key1)
        reg.set("key2", key2)
        reg.set("key3", key3)
        values = reg.get_multi(["key1", "key2", "key3"])
        eq_([key1, key2, key3], values)

    def test_region_get_nothing_multiple(self):
        reg = self._region()
        reg.delete_multi(["key1", "key2", "key3", "key4", "key5"])
        values = {"key1": "value1", "key3": "value3", "key5": "value5"}
        reg.set_multi(values)
        reg_values = reg.get_multi(
            ["key1", "key2", "key3", "key4", "key5", "key6"]
        )
        eq_(
            reg_values,
            ["value1", NO_VALUE, "value3", NO_VALUE, "value5", NO_VALUE],
        )

    def test_region_get_empty_multiple(self):
        reg = self._region()
        reg_values = reg.get_multi([])
        eq_(reg_values, [])

    def test_region_delete_multiple(self):
        reg = self._region()
        values = {"key1": "value1", "key2": "value2", "key3": "value3"}
        reg.set_multi(values)
        reg.delete_multi(["key2", "key10"])
        eq_(values["key1"], reg.get("key1"))
        eq_(NO_VALUE, reg.get("key2"))
        eq_(values["key3"], reg.get("key3"))
        eq_(NO_VALUE, reg.get("key10"))

    def test_region_set_get_nothing(self):
        reg = self._region()
        some_key = gen_some_key()
        reg.delete_multi([some_key])
        eq_(reg.get(some_key), NO_VALUE)

    def test_region_creator(self):
        reg = self._region()

        def creator():
            return "some value"

        some_key = gen_some_key()
        eq_(reg.get_or_create(some_key, creator), "some value")

    @pytest.mark.time_intensive
    def test_threaded_dogpile(self):
        # run a basic dogpile concurrency test.
        # note the concurrency of dogpile itself
        # is intensively tested as part of dogpile.
        reg = self._region(config_args={"expiration_time": 0.25})
        lock = Lock()
        canary = []
        some_key = gen_some_key()

        def creator():
            ack = lock.acquire(False)
            canary.append(ack)
            time.sleep(0.25)
            if ack:
                lock.release()
            return "some value"

        def f():
            for x in range(5):
                reg.get_or_create(some_key, creator)
                time.sleep(0.5)

        threads = [Thread(target=f) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(canary) > 2
        if not reg.backend.has_lock_timeout():
            assert False not in canary

    @pytest.mark.time_intensive
    def test_threaded_get_multi(self):
        """This test is testing that when we get inside the "creator" for
        a certain key, there are no other "creators" running at all for
        that key.

        With "distributed" locks, this is not 100% the case.

        """
        some_key = gen_some_key()
        reg = self._region(config_args={"expiration_time": 0.25})
        backend_mutex = reg.backend.get_mutex(some_key)
        is_custom_mutex = backend_mutex is not None

        locks = dict((str(i), Lock()) for i in range(11))

        canary = collections.defaultdict(list)

        def creator(*keys):
            assert keys
            ack = [locks[key].acquire(False) for key in keys]

            # print(
            #        ("%s " % thread.get_ident()) + \
            #        ", ".join(sorted("%s=%s" % (key, acq)
            #                    for acq, key in zip(ack, keys)))
            #    )

            for acq, key in zip(ack, keys):
                canary[key].append(acq)

            time.sleep(0.5)

            for acq, key in zip(ack, keys):
                if acq:
                    locks[key].release()
            return ["some value %s" % k for k in keys]

        def f():
            for x in range(5):
                reg.get_or_create_multi(
                    [
                        str(random.randint(1, 10))
                        for i in range(random.randint(1, 5))
                    ],
                    creator,
                )
                time.sleep(0.5)

        f()

        threads = [Thread(target=f) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert sum([len(v) for v in canary.values()]) > 10

        # for non-custom mutex, check that we never had two creators
        # running at once
        if not is_custom_mutex:
            for l in canary.values():
                assert False not in l

    def test_region_delete(self):
        reg = self._region()
        some_key = gen_some_key()
        reg.set(some_key, "some value")
        reg.delete(some_key)
        reg.delete(some_key)
        eq_(reg.get(some_key), NO_VALUE)

    @pytest.mark.time_intensive
    def test_region_expire(self):
        # TODO: ideally tests like these would not be using actual
        # time(); instead, an artificial function where the increment
        # can be controlled would be preferred.  this way tests need not
        # have any delay in running and additionally there is no issue
        # with very slow processing missing a timeout, as is often the
        # case with this particular test

        some_key = gen_some_key()
        expire_time = 1.00

        reg = self._region(config_args={"expiration_time": expire_time})
        counter = itertools.count(1)

        def creator():
            return "some value %d" % next(counter)

        eq_(reg.get_or_create(some_key, creator), "some value 1")
        time.sleep(expire_time + (0.2 * expire_time))
        # expiration is definitely hit
        post_expiration = reg.get(some_key, ignore_expiration=True)
        if post_expiration is not NO_VALUE:
            eq_(post_expiration, "some value 1")

        eq_(reg.get_or_create(some_key, creator), "some value 2")

        # this line needs to run less the expire_time sec before the previous
        # two or it hits the expiration
        eq_(reg.get(some_key), "some value 2")

    def test_decorated_fn_functionality(self):
        # test for any quirks in the fn decoration that interact
        # with the backend.

        reg = self._region()

        counter = itertools.count(1)

        @reg.cache_on_arguments()
        def my_function(x, y):
            return next(counter) + x + y

        # Start with a clean slate
        my_function.invalidate(3, 4)
        my_function.invalidate(5, 6)
        my_function.invalidate(4, 3)

        eq_(my_function(3, 4), 8)
        eq_(my_function(5, 6), 13)
        eq_(my_function(3, 4), 8)
        eq_(my_function(4, 3), 10)

        my_function.invalidate(4, 3)
        eq_(my_function(4, 3), 11)

    def test_exploding_value_fn(self):
        some_key = gen_some_key()
        reg = self._region()

        def boom():
            raise Exception("boom")

        assert_raises_message(
            Exception, "boom", reg.get_or_create, some_key, boom
        )


def raise_cant_deserialize_exception(v):
    raise CantDeserializeException()


class _GenericSerializerTestSuite:
    # Inheriting from this class will make test cases
    # use these serialization arguments
    region_args = {
        "serializer": lambda v: json.dumps(v).encode("ascii"),
        "deserializer": json.loads,
    }

    def test_serializer_cant_deserialize(self):
        region = self._region(
            region_args={
                "serializer": self.region_args["serializer"],
                "deserializer": raise_cant_deserialize_exception,
            }
        )

        value = {"foo": ["bar", 1, False, None]}
        region.set("k", value)
        asserted = region.get("k")
        eq_(asserted, NO_VALUE)

    def test_uses_serializer(self):
        region = self._region()

        backend = region.backend
        value = {"foo": ["bar", 1, False, None]}
        region.set("k", value)

        raw = backend.get_serialized("k")

        assert isinstance(raw, bytes)

        pipe = raw.find(b"|")
        payload = raw[pipe + 1 :]
        eq_(payload, self.region_args["serializer"](value))
        eq_(region._parse_serialized_from_backend(raw).payload, value)

    def test_uses_deserializer(self):
        region = self._region()

        value = {"foo": ["bar", 1, False, None]}
        region.set("k", value)

        asserted = region.get("k")

        eq_(asserted, value)

    # TODO: test set_multi, get_multi


class _GenericMutexTestSuite(_GenericBackendFixture):
    def test_mutex(self):
        backend = self._backend()
        mutex = backend.get_mutex("foo")

        assert not mutex.locked()
        ac = mutex.acquire()
        assert ac
        ac2 = mutex.acquire(False)
        assert mutex.locked()
        assert not ac2
        mutex.release()
        assert not mutex.locked()

        ac3 = mutex.acquire()
        assert ac3
        mutex.release()

    def test_subclass_match(self):
        backend = self._backend()
        mutex = backend.get_mutex("foo")

        assert isinstance(mutex, CacheMutex)

    @pytest.mark.time_intensive
    def test_mutex_threaded(self):
        backend = self._backend()
        backend.get_mutex("foo")

        lock = Lock()
        canary = []

        def f():
            for x in range(5):
                mutex = backend.get_mutex("foo")
                mutex.acquire()
                for y in range(5):
                    ack = lock.acquire(False)
                    canary.append(ack)
                    time.sleep(0.002)
                    if ack:
                        lock.release()
                mutex.release()
                time.sleep(0.02)

        threads = [Thread(target=f) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert False not in canary

    def test_mutex_reentrant_across_keys(self):
        backend = self._backend()
        for x in range(3):
            m1 = backend.get_mutex("foo")
            m2 = backend.get_mutex("bar")
            try:
                m1.acquire()
                assert m2.acquire(False)
                assert not m2.acquire(False)
                m2.release()

                assert m2.acquire(False)
                assert not m2.acquire(False)
                m2.release()
            finally:
                m1.release()

    def test_reentrant_dogpile(self):
        reg = self._region()

        def create_foo():
            return "foo" + reg.get_or_create("bar", create_bar)

        def create_bar():
            return "bar"

        eq_(reg.get_or_create("foo", create_foo), "foobar")
        eq_(reg.get_or_create("foo", create_foo), "foobar")


class MockMutex(object):
    def __init__(self, key):
        self.key = key

    def acquire(self, blocking=True):
        return True

    def release(self):
        return

    def locked(self):
        return False


class MockBackend(CacheBackend):
    def __init__(self, arguments):
        self.arguments = arguments
        self._cache = {}

    def get_mutex(self, key):
        return MockMutex(key)

    def get(self, key):
        try:
            return self._cache[key]
        except KeyError:
            return NO_VALUE

    def get_multi(self, keys):
        return [self.get(key) for key in keys]

    def set(self, key, value):
        self._cache[key] = value

    def set_multi(self, mapping):
        for key, value in mapping.items():
            self.set(key, value)

    def delete(self, key):
        self._cache.pop(key, None)

    def delete_multi(self, keys):
        for key in keys:
            self.delete(key)


register_backend("mock", __name__, "MockBackend")
