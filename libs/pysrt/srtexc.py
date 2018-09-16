"""
Exception classes
"""


class Error(Exception):
    """
    Pysrt's base exception
    """
    pass


class InvalidTimeString(Error):
    """
    Raised when parser fail on bad formated time strings
    """
    pass


class InvalidItem(Error):
    """
    Raised when parser fail to parse a sub title item
    """
    pass


class InvalidIndex(InvalidItem):
    """
    Raised when parser fail to parse a sub title index
    """
    pass
