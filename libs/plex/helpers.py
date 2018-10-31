def has_attribute(obj, name):
    try:
        object.__getattribute__(obj, name)
        return True
    except AttributeError:
        return False
