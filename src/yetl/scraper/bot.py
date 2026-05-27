from __future__ import annotations

from yetl.scraper.bs4 import BeautifulSoupModule
from yetl.scraper.logger import LoggerModule
from yetl.scraper.primitives import ScrapeBotRoutine
from yetl.scraper.selenium import SeleniumModule
from yetl.scraper.timing import TimingModule
from yetl.scraper.writer import CsvWriterModule


class ScrapeBot:
    """
    Reusable scraping runtime.

    The bot owns generic modules and lifecycle. Website knowledge belongs in
    routines, not here.
    """

    def __init__(
        self,
        *,
        name: str = "ScrapeBot",
        description: str = "Reusable scraping runtime.",
        logger: LoggerModule | None = None,
        browser: SeleniumModule | None = None,
        parser: BeautifulSoupModule | None = None,
        writer: CsvWriterModule | None = None,
        timing: TimingModule | None = None,
    ) -> None:
        # ===== Scrapebot's Instance Metadata
        self.name = name
        self.description = description

        # ===== Module Installation Slots
        self.logger: LoggerModule = logger or LoggerModule()
        self.browser: SeleniumModule = browser or SeleniumModule()
        self.parser: BeautifulSoupModule = parser or BeautifulSoupModule()
        self.writer: CsvWriterModule = writer or CsvWriterModule()
        self.timing: TimingModule = timing or TimingModule()

        # ===== Routine Installation
        self.routine: ScrapeBotRoutine | None = None

    def run(self) -> None:
        if self.routine is None:
            raise RuntimeError("No ScrapeBot routine has been installed.")

        try:
            self.routine.execute(self)
        finally:
            self.close()

    def install_routine(self, routine: ScrapeBotRoutine) -> None:
        self.routine = routine

    def close(self) -> None:
        self.browser.close()
