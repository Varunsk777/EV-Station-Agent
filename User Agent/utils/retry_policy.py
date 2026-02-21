import time
from typing import Callable


class RetryPolicy:
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor

    def execute(self, func: Callable, *args, **kwargs):
        delay = self.initial_delay

        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                if attempt == self.max_attempts:
                    raise e

                time.sleep(delay)
                delay *= self.backoff_factor