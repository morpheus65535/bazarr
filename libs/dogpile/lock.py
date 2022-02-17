import logging
import time

log = logging.getLogger(__name__)


class NeedRegenerationException(Exception):
    """An exception that when raised in the 'with' block,
    forces the 'has_value' flag to False and incurs a
    regeneration of the value.

    """


NOT_REGENERATED = object()


class Lock:
    """Dogpile lock class.

    Provides an interface around an arbitrary mutex
    that allows one thread/process to be elected as
    the creator of a new value, while other threads/processes
    continue to return the previous version
    of that value.

    :param mutex: A mutex object that provides ``acquire()``
     and ``release()`` methods.
    :param creator: Callable which returns a tuple of the form
     (new_value, creation_time).  "new_value" should be a newly
     generated value representing completed state.  "creation_time"
     should be a floating point time value which is relative
     to Python's ``time.time()`` call, representing the time
     at which the value was created.  This time value should
     be associated with the created value.
    :param value_and_created_fn: Callable which returns
     a tuple of the form (existing_value, creation_time).  This
     basically should return what the last local call to the ``creator()``
     callable has returned, i.e. the value and the creation time,
     which would be assumed here to be from a cache.  If the
     value is not available, the :class:`.NeedRegenerationException`
     exception should be thrown.
    :param expiretime: Expiration time in seconds.  Set to
     ``None`` for never expires.  This timestamp is compared
     to the creation_time result and ``time.time()`` to determine if
     the value returned by value_and_created_fn is "expired".
    :param async_creator: A callable.  If specified, this callable will be
     passed the mutex as an argument and is responsible for releasing the mutex
     after it finishes some asynchronous value creation.  The intent is for
     this to be used to defer invocation of the creator callable until some
     later time.

    """

    def __init__(
        self,
        mutex,
        creator,
        value_and_created_fn,
        expiretime,
        async_creator=None,
    ):
        self.mutex = mutex
        self.creator = creator
        self.value_and_created_fn = value_and_created_fn
        self.expiretime = expiretime
        self.async_creator = async_creator

    def _is_expired(self, createdtime):
        """Return true if the expiration time is reached, or no
        value is available."""

        return not self._has_value(createdtime) or (
            self.expiretime is not None
            and time.time() - createdtime > self.expiretime
        )

    def _has_value(self, createdtime):
        """Return true if the creation function has proceeded
        at least once."""
        return createdtime > 0

    def _enter(self):
        value_fn = self.value_and_created_fn

        try:
            value = value_fn()
            value, createdtime = value
        except NeedRegenerationException:
            log.debug("NeedRegenerationException")
            value = NOT_REGENERATED
            createdtime = -1

        generated = self._enter_create(value, createdtime)

        if generated is not NOT_REGENERATED:
            generated, createdtime = generated
            return generated
        elif value is NOT_REGENERATED:
            # we called upon the creator, and it said that it
            # didn't regenerate.  this typically means another
            # thread is running the creation function, and that the
            # cache should still have a value.  However,
            # we don't have a value at all, which is unusual since we just
            # checked for it, so check again (TODO: is this a real codepath?)
            try:
                value, createdtime = value_fn()
                return value
            except NeedRegenerationException:
                raise Exception(
                    "Generation function should "
                    "have just been called by a concurrent "
                    "thread."
                )
        else:
            return value

    def _enter_create(self, value, createdtime):
        if not self._is_expired(createdtime):
            return NOT_REGENERATED

        _async = False

        if self._has_value(createdtime):
            has_value = True
            if not self.mutex.acquire(False):
                log.debug("creation function in progress elsewhere, returning")
                return NOT_REGENERATED
        else:
            has_value = False
            log.debug("no value, waiting for create lock")
            self.mutex.acquire()

        try:
            log.debug("value creation lock %r acquired" % self.mutex)

            if not has_value:
                # we entered without a value, or at least with "creationtime ==
                # 0".   Run the "getter" function again, to see if another
                # thread has already generated the value while we waited on the
                # mutex,  or if the caller is otherwise telling us there is a
                # value already which allows us to use async regeneration. (the
                # latter is used by the multi-key routine).
                try:
                    value, createdtime = self.value_and_created_fn()
                except NeedRegenerationException:
                    # nope, nobody created the value, we're it.
                    # we must create it right now
                    pass
                else:
                    has_value = True
                    # caller is telling us there is a value and that we can
                    # use async creation if it is expired.
                    if not self._is_expired(createdtime):
                        # it's not expired, return it
                        log.debug("Concurrent thread created the value")
                        return value, createdtime

                    # otherwise it's expired, call creator again

            if has_value and self.async_creator:
                # we have a value we can return, safe to use async_creator
                log.debug("Passing creation lock to async runner")

                # so...run it!
                self.async_creator(self.mutex)
                _async = True

                # and return the expired value for now
                return value, createdtime

            # it's expired, and it's our turn to create it synchronously, *or*,
            # there's no value at all, and we have to create it synchronously
            log.debug(
                "Calling creation function for %s value",
                "not-yet-present" if not has_value else "previously expired",
            )
            return self.creator()
        finally:
            if not _async:
                self.mutex.release()
                log.debug("Released creation lock")

    def __enter__(self):
        return self._enter()

    def __exit__(self, type_, value, traceback):
        pass
