from selenium.common.exceptions import WebDriverException


class SeleniumFallbackClickError(WebDriverException):
    """Raised when an intercepted click cannot be completed with JavaScript."""

    default_message = "Click was intercepted and JavaScript fallback failed."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)


class SeleniumLoadClickError(WebDriverException):
    """Raised when a load-triggering click does not complete within retries."""

    default_message = "Load-triggering click did not complete within retry limit."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)
