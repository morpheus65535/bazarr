# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen

__all__ = (
    "loads",
    "load",
    "TOMLDecodeError",
    "dump",
    "dumps",
)

from ._parser import TOMLDecodeError, load, loads
from ._writer import dump, dumps

# Pretend this exception was created here.
TOMLDecodeError.__module__ = __name__
