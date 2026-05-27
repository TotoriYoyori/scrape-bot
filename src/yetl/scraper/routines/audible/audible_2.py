from __future__ import annotations

from typing import TYPE_CHECKING

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By

from yetl.scraper.primitives import ScrapeBotRoutine
from . import locators
from .schema import BS4_BOOK, BookRecord
from .settings import AudibleRoutineSettings

if TYPE_CHECKING:
    from yetl.scraper.bot import ScrapeBot


class AudibleRoutine(ScrapeBotRoutine):
    """Audible scrape routine organized around the ScrapeBotRoutine lifecycle."""

    name = "audible"
    description = "Scrapes Audible book listings by category and subcategory."
    BASE_URL = "https://www.audible.co.uk/search"

    def __init__(
        self,
        *,
        target_category: str,
        max_records: int | None = None,
        settings: AudibleRoutineSettings | None = None,
    ) -> None:
        self.target_category = target_category
        self.max_records = max_records
        self.settings = settings or AudibleRoutineSettings()
        self.records_written = 0

        self.current_subcategory: str | None = None
        self.current_page: int | None = None
        self.pending_records: list[BookRecord] = []
        self.should_stop = False
        self.target_category_index: int | None = None

        self._bot: ScrapeBot | None = None

    @property
    def bot(self) -> ScrapeBot:
        if self._bot is None:
            raise RuntimeError("AudibleRoutine has not been bound to a ScrapeBot.")

        return self._bot

    def reset_state(self) -> None:
        self.records_written = 0
        self.current_subcategory = None
        self.current_page = None
        self.pending_records = []
        self.should_stop = False
        self.target_category_index = None

        self.bot.browser.open(self.BASE_URL)

    def setup(self) -> None:
        # ===== Click Off Cookies
        accept_button = self.bot.browser.locate(locators.COOKIE_ACCEPT_BUTTON)
        if accept_button is not None:
            self.bot.browser.safe_click(accept_button)

        # ===== Hit the Redirect Link
        redirect = self.bot.browser.locate(locators.REDIRECT_LINK)
        if redirect is not None:
            self.bot.browser.redirect_click(redirect)

        # ===== Read Available Categories
        categories = self.bot.browser.locate_all(locators.CATEGORIES)
        category_names = [category.text for category in categories]

        # ===== Validate Target Category
        if self.target_category not in category_names:
            raise ValueError(
                f"Target category '{self.target_category}' was not found. "
                f"Available categories: {category_names}"
            )

        # ===== Prepare Target Category
        self.target_category_index = category_names.index(self.target_category)

        # ===== Announce Ready Target
        self.bot.logger.info(f"Targeting category: {self.target_category}")

    def execute(self, bot: ScrapeBot) -> None:
        # ===== Bind Routine To Bot And Prepare Fresh Run
        self._bot = bot
        self.reset_state()
        self.setup()

        # ===== Announce Scrape Start
        self.bot.logger.info(f"Scraping category: {self.target_category}")

        try:
            # ===== Apply Search Result Filters
            audiobook_filter = self.bot.browser.locate(locators.AUDIOBOOK_FILTER)
            if audiobook_filter is not None and not audiobook_filter.is_selected():
                audiobook_link = self.bot.browser.require_clickable(
                    locators.AUDIOBOOK_LINK
                )
                self.bot.browser.safe_click(audiobook_link)

            # ===== Enter Target Category
            categories = self.bot.browser.locate_all(locators.CATEGORIES)
            if self.target_category_index is None or self.target_category_index >= len(
                categories
            ):
                raise RuntimeError(
                    "Target category index is no longer available after filters."
                )

            self.bot.browser.safe_click(categories[self.target_category_index])

            # ===== Scrape Category Subcategories
            self._scrape_subcategories()

            # ===== Stop Early If Record Limit Was Reached
            if self.should_stop:
                self.bot.logger.info("Max books reached; stopping entire scrape.")
                return

            # ===== Announce Scrape Completion
            self.bot.logger.info("Finished target category '%s'.", self.target_category)
        except (NoSuchElementException, TimeoutException) as exc:
            # ===== Report Recoverable Browser Failures
            self.bot.logger.error(
                "Failed to process category '%s': %s", self.target_category, exc
            )
        finally:
            # ===== Return To Category Index
            all_categories = self.bot.browser.locate(locators.ALL_CATEGORIES)
            if all_categories is not None:
                self.bot.browser.safe_click(all_categories)

    def scrape_page(self) -> None:
        html = self.bot.browser.html()
        if self.settings.PAGE_LOAD_SENTINEL not in html:
            self.bot.logger.debug("    Main content missing; waiting and retrying.")
            self.bot.timing.sleep(self.settings.PAGE_RETRY_DELAY)
            self.bot.browser.refresh()
            html = self.bot.browser.html()

        if self.settings.PAGE_LOAD_SENTINEL not in html:
            self.bot.logger.warning(
                "    Page %s failed to load; skipping.", self.current_page
            )
            self.pending_records = []
            return

        self.pending_records = self.bot.parser.parse_records(
            html,
            BS4_BOOK,
            context={
                "category": self.target_category,
                "subcategory": self.current_subcategory,
            },
        )

    def write(self) -> None:
        records_to_write = self._limit_records(self.pending_records)
        if records_to_write:
            self.bot.writer.write(records_to_write)
            self.records_written += len(records_to_write)
            self.bot.logger.info(
                "    Written %d / %s books so far.",
                self.records_written,
                self.max_records if self.max_records is not None else "unlimited",
            )
            self.should_stop = self._record_limit_reached()
        elif self.pending_records and self._record_limit_reached():
            self.should_stop = True
        else:
            self.bot.logger.warning(
                "    No books extracted on page %s.", self.current_page
            )

        self.pending_records = []

    def _scrape_subcategories(self) -> None:
        subcategories = self.bot.browser.locate_all(locators.SUBCATEGORY)
        total = len(subcategories)
        self.bot.logger.info(
            "  Found %d subcategories in '%s'.", total, self.target_category
        )

        for index in range(total):
            if not self._should_scrape(self.target_category, index):
                self.bot.logger.debug(
                    "  Skipping subcategory index %d in '%s'.",
                    index,
                    self.target_category,
                )
                continue

            try:
                subcategories = self.bot.browser.locate_all(locators.SUBCATEGORY)
                if index >= len(subcategories):
                    self.bot.logger.warning(
                        "  Subcategory list changed; stopping early at index %d.", index
                    )
                    break

                subcategory = subcategories[index]
                self.current_subcategory = subcategory.text
                self.bot.browser.safe_click(subcategory)

                self._scrape_all_pages()
                if self.should_stop:
                    return
            except (NoSuchElementException, TimeoutException) as exc:
                self.bot.logger.error(
                    "  Failed on subcategory %d of '%s': %s",
                    index,
                    self.target_category,
                    exc,
                )
            except IndexError:
                self.bot.logger.error(
                    "Index error while scraping subcategories.", exc_info=True
                )
            finally:
                breadcrumb = self.bot.browser.locate(locators.BREADCRUMB)
                if breadcrumb is not None:
                    items = breadcrumb.find_elements(By.TAG_NAME, "li")
                    if len(items) > 1:
                        self.bot.browser.safe_click(items[1])

    def _scrape_all_pages(self) -> None:
        self.bot.logger.info(
            "  Starting scrape on category '%s' / subcategory '%s'.",
            self.target_category,
            self.current_subcategory,
        )

        total_pages = self._get_pages()
        for page_num in range(1, total_pages + 1):
            self.current_page = page_num
            self.bot.logger.debug("    Page %d / %d", page_num, total_pages)

            self.scrape_page()
            self.write()

            if self.should_stop:
                self.bot.logger.info("    max_books limit reached; stopping scrape.")
                return

            if page_num < total_pages:
                next_button = self.bot.browser.locate(locators.NEXT_BUTTON)
                if next_button is None:
                    self.bot.logger.info(
                        "    Next page button not found; stopping early."
                    )
                    break

                self.bot.browser.safe_click(next_button)
                self.bot.timing.sleep(1)

    def _get_pages(self) -> int:
        page_elements = self.bot.browser.locate_all(locators.PAGE_NUMBERS)
        page_numbers = [
            element.text for element in page_elements if element.text.strip().isdigit()
        ]
        if not page_numbers:
            self.bot.logger.warning(
                "  Could not determine page count: no numeric page elements found. "
                "Scraping one page."
            )
            return 1

        return int(page_numbers[-1])

    def _should_scrape(self, category_name: str, index: int) -> bool:
        return index not in self.settings.SKIP_MAP.get(category_name, [])

    def _limit_records(self, records: list[BookRecord]) -> list[BookRecord]:
        if self.max_records is None:
            return records

        remaining = self.max_records - self.records_written
        if remaining <= 0:
            return []

        return records[:remaining]

    def _record_limit_reached(self) -> bool:
        return self.max_records is not None and self.records_written >= self.max_records
