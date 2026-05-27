import logging

from yetl.scraper.primitives import ScrapeBotModule
from yetl.scraper.logger.palette import LOGGER_PALETTE_REGISTRY
from yetl.scraper.logger.settings import (
    LOGGER_LEVELS,
    LoggerConfig,
)


# =============== LEVEL COLOR FORMATTER ===============
class LevelColorFormatter(logging.Formatter):
    """Formatter that colors log messages by level.

    Python logging calls ``format`` for each log record. This formatter uses
    that hook to choose the color for the record level before rendering text.

    Args:
        formats: Mapping of numeric logging level to format string.

    Examples:
        >>> formatter = LevelColorFormatter({logging.DEBUG: "%(message)s"})
        >>> assert logging.DEBUG in formatter.formatters
    """

    def __init__(self, formats: dict[int, str]) -> None:
        super().__init__()
        self.formatters = {
            level: logging.Formatter(log_format)
            for level, log_format in formats.items()
        }

    def format(self, record: logging.LogRecord) -> str:
        formatter = self.formatters.get(
            record.levelno,
            self.formatters[logging.INFO],
        )

        return formatter.format(record)


# =============== LOGGER MODULE ===============
class LoggerModule(ScrapeBotModule):
    """ScrapeBot module that wraps Python logging.

    The module owns the active logger and installs one color-aware console handler.

    Args:
        config: Optional logger configuration. When omitted, ``LoggerConfig``
            reads its default values and supported environment variables.

    Examples:
        >>> logger = LoggerModule()
        >>> assert logger.config.NAME == "ScrapeBot"
    """

    name = "logger"

    def __init__(self, config: LoggerConfig | None = None) -> None:
        self.config = config or LoggerConfig()

        self._formatter = self._build_formatter()
        self._logger = self._build_logger()

    # ===== Logger's and Formatter's construction helper
    def _build_formatter(self) -> LevelColorFormatter:
        palette = LOGGER_PALETTE_REGISTRY[self.config.PALETTE]
        template = self.config.FORMAT_TEMPLATE

        formats = {
            level_value: (
                getattr(palette, level_name.lower()).ansi
                + template
                + palette.reset.ansi
            )
            for level_name, level_value in LOGGER_LEVELS.items()
        }

        return LevelColorFormatter(formats)

    def _build_logger(self) -> logging.Logger:
        def scrape_bot_handlers():
            for handler in logger.handlers:
                if getattr(handler, "_scrape_bot_custom", False):
                    yield handler

        logger = logging.getLogger(self.config.NAME)
        logger.setLevel(LOGGER_LEVELS[self.config.LEVEL])
        logger.propagate = self.config.PROPAGATE

        console_handler = next(scrape_bot_handlers(), None)

        if console_handler is None:
            console_handler = logging.StreamHandler()
            console_handler._scrape_bot_custom = True
            logger.addHandler(console_handler)

        console_handler.setLevel(LOGGER_LEVELS[self.config.LEVEL])
        console_handler.setFormatter(self._formatter)

        return logger

    # ===== Thin wrapper around Logger
    def debug(self, message: str, *args, **kwargs) -> None:
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        self._logger.critical(message, *args, **kwargs)
