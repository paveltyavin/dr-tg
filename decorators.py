from datetime import timedelta, datetime
from functools import wraps
from time import sleep


class throttle(object):
    def __init__(self, seconds=0, minutes=0, hours=0):
        self.throttle_period = timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        )
        self.time_of_last_call = datetime.now()

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            now = datetime.now()
            time_to_sleep = self.throttle_period - (now - self.time_of_last_call)
            if time_to_sleep.total_seconds() > 0:
                sleep(time_to_sleep.seconds)

            self.time_of_last_call = datetime.now()
            return fn(*args, **kwargs)

        return wrapper
