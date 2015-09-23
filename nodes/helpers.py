import time

from nodes import exceptions


def lazy_property(method):
    name = '_lazy_' + method.__name__

    @property
    def lazyproperty(self):
        if not hasattr(self, name):
            setattr(self, name, method(self))
        return getattr(self, name)

    return lazyproperty


def wait_for(condition, timeout=150, interval=5):
    start_time = int(time.time())
    while True:
        try:
            if condition():
                return
        except Exception:
            pass

        if int(time.time()) - start_time >= timeout:
            break

        time.sleep(interval)
    raise exceptions.TimeoutException(message="Timeout")
