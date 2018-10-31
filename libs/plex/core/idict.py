from plex.lib.six import string_types

class idict(dict):
    def __init__(self, initial=None):
        if initial:
            self.update(initial)

    def get(self, k, d=None):
        if isinstance(k, string_types):
            k = k.lower()

        if super(idict, self).__contains__(k):
            return self[k]

        return d

    def update(self, E=None, **F):
        if E:
            if hasattr(E, 'keys'):
                # Update with `E` dictionary
                for k in E:
                    self[k] = E[k]
            else:
                # Update with `E` items
                for (k, v) in E:
                    self[k] = v

        # Update with `F` dictionary
        for k in F:
            self[k] = F[k]

    def __contains__(self, k):
        if isinstance(k, string_types):
            k = k.lower()

        return super(idict, self).__contains__(k)

    def __delitem__(self, k):
        if isinstance(k, string_types):
            k = k.lower()

        super(idict, self).__delitem__(k)

    def __getitem__(self, k):
        if isinstance(k, string_types):
            k = k.lower()

        return super(idict, self).__getitem__(k)

    def __setitem__(self, k, value):
        if isinstance(k, string_types):
            k = k.lower()

        super(idict, self).__setitem__(k, value)
