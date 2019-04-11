# coding=utf-8

import types
from subliminal_patch.http import TimeoutSession


def fix_session_bases(obj):
    obj.__class__ = type("PatchedTimeoutSession", (TimeoutSession,),
                         {"request": types.MethodType(TimeoutSession.request, obj)})
    return obj
