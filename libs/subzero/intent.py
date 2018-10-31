# coding=utf-8

import datetime
import threading

lock = threading.Lock()


class TempIntent(object):
    timeout = 1000  # milliseconds
    store = None

    def __init__(self, timeout=1000, store=None):
        self.timeout = timeout
        if store is None:
            raise NotImplementedError

        self.store = store

    def get(self, kind, *keys):
        with lock:
            # iter all requested keys
            for key in keys:
                hit = False

                # skip key if invalid
                if not key:
                    continue

                # valid kind?
                if kind in self.store:
                    now = datetime.datetime.now()
                    key = str(key)

                    # iter all known kinds (previously created)
                    for known_key in self.store[kind].keys():
                        # may need locking, for now just play it safe
                        data = self.store[kind].get(known_key, {})
                        ends = data.get("timeout")
                        if not ends:
                            continue

                        timed_out = False
                        if now > ends:
                            timed_out = True

                        # key and kind in storage, and not timed out = hit
                        if known_key == key and not timed_out:
                            hit = True

                        if timed_out:
                            try:
                                del self.store[kind][key]
                            except:
                                continue

                    if hit:
                        return True
        return False

    def resolve(self, kind, key):
        with lock:
            if kind in self.store and key in self.store[kind]:
                del self.store[kind][key]
                return True
            return False

    def set(self, kind, key, data=None, timeout=None):
        with lock:
            if kind not in self.store:
                self.store[kind] = {}

            key = str(key)
            self.store[kind][key] = {
                "data": data,
                "timeout": datetime.datetime.now() + datetime.timedelta(milliseconds=timeout or self.timeout)
            }

    def has(self, kind, key):
        with lock:
            if kind not in self.store:
                return False
            return key in self.store[kind]

    def cleanup(self):
        now = datetime.datetime.now()
        clear_all = False
        for kind, info in self.store.items():
            for key, intent_data in info.items():
                # legacy intent data, clear everything
                if not isinstance(intent_data, dict):
                    clear_all = True
                    continue

                if now > intent_data["timeout"]:
                    del self.store[kind][key]
        if clear_all:
            self.store.clear()

        self.store.save()

