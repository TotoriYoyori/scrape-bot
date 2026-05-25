from __future__ import annotations

from src.scraper.bs4 import BeautifulSoupModule, create_html_parser
from src.scraper.logger import LoggerModule
from src.scraper.primitives import ScrapeBotRoutine
from src.scraper.selenium import SeleniumModule
from src.scraper.timing import TimingModule
from src.scraper.writer import CsvWriterModule, create_csv_writer


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
        self.parser: BeautifulSoupModule = parser or create_html_parser()
        self.writer: CsvWriterModule = writer or create_csv_writer()
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
