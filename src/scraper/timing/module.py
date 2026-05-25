import random
import time
from collections.abc import Callable
from typing import TypeVar

from src.scraper.primitives import ScrapeBotModule
from src.scraper.timing.settings import TimingConfig

T = TypeVar("T")


# =============== TIMING MODULE ===============
class TimingModule(ScrapeBotModule):
    """Generic timing behavior for scrape routines.

    Args:
        config: Optional timing configuration. When omitted, ``TimingConfig``
            reads its default values and supported environment variables.

    Examples:
        >>> timing = TimingModule()
        >>> assert timing.config.RETRY_ATTEMPTS == 2
    """

    name = "timing"

    def __init__(self, config: TimingConfig | None = None) -> None:
        self.config = config or TimingConfig()

    # ===== Thin wrapper around time
    def sleep(self, seconds: float | None = None) -> None:
        sleep_seconds = self.config.SLEEP_BASE if seconds is None else seconds

        time.sleep(sleep_seconds)

    # ===== Human behavior timing helpers
    def smart_sleep(
        self,
        min_seconds: float | None = None,
        max_seconds: float | None = None,
    ) -> None:
        sleep_min_seconds = self.config.SLEEP_MIN if min_seconds is None else min_seconds
        sleep_max_seconds = self.config.SLEEP_MAX if max_seconds is None else max_seconds

        time.sleep(random.uniform(sleep_min_seconds, sleep_max_seconds))

    # ===== Retry helpers
    def retry(
        self,
        action: Callable[[], T],
        *,
        attempts: int | None = None,
        delay_seconds: float | None = None,
    ) -> T:
        retry_attempts = self.config.RETRY_ATTEMPTS if attempts is None else attempts
        retry_delay_seconds = self.config.RETRY_DELAY_SECONDS if delay_seconds is None else delay_seconds

        last_error: Exception | None = None
        for _ in range(retry_attempts):
            try:
                return action()
            except Exception as exc:
                last_error = exc
                self.sleep(retry_delay_seconds)

        if last_error is not None:
            raise last_error

        raise RuntimeError("retry() called with no attempts.")
