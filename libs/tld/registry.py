from typing import Dict

__author__ = 'Artur Barseghyan'
__copyright__ = '2013-2020 Artur Barseghyan'
__license__ = 'MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later'
__all__ = (
    'Registry',
)


class Registry(type):

    REGISTRY = {}  # type: Dict[str, Registry]

    def __new__(mcs, name, bases, attrs):
        new_cls = type.__new__(mcs, name, bases, attrs)
        # Here the name of the class is used as key but it could be any class
        # parameter.
        if getattr(new_cls, '_uid', None):
            mcs.REGISTRY[new_cls._uid] = new_cls
        return new_cls

    @property
    def _uid(cls) -> str:
        return getattr(cls, 'uid', cls.__name__)

    @classmethod
    def reset(mcs) -> None:
        mcs.REGISTRY = {}

    @classmethod
    def get(mcs, key, default=None):
        return mcs.REGISTRY.get(key, default)

    @classmethod
    def items(mcs):
        return mcs.REGISTRY.items()

    # @classmethod
    # def get_registry(mcs) -> Dict[str, Type]:
    #     return dict(mcs.REGISTRY)
    #
    # @classmethod
    # def pop(mcs, uid) -> None:
    #     mcs.REGISTRY.pop(uid)
