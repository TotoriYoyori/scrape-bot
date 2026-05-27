from __future__ import annotations

from typing import TYPE_CHECKING

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By

from src.scraper.primitives import ScrapeBotRoutine

from . import locators
from .schema import BS4_BOOK, BookRecord
from .settings import AudibleRoutineSettings

if TYPE_CHECKING:
    from src.scraper.bot import ScrapeBot


class AudibleRoutine(ScrapeBotRoutine):
    """Imperative Audible scrape routine executed by ScrapeBot."""

    name = "audible"
    description = "Scrapes Audible book listings by category and subcategory."
    BASE_URL = "https://www.audible.co.uk/search"

    def __init__(
        self,
        *,
        target_category: str | None = None,
        max_records: int | None = None,
        settings: AudibleRoutineSettings | None = None,
    ) -> None:
        self.target_category = target_category
        self.max_records = max_records
        self.settings = settings or AudibleRoutineSettings()
        self.records_written = 0

    def execute(self, bot: ScrapeBot) -> None:
        self.records_written = 0

        bot.browser.open(self.BASE_URL)
        self._follow_redirect_if_present(bot)
        self._accept_cookie_banner_if_present(bot)

        categories = self._get_categories(bot)
        category_names = [category.text for category in categories]
        self._validate_target_category(category_names)
        bot.logger.info("Targeting %d categories.", len(category_names))

        for index, category_name in enumerate(category_names):
            if self.target_category and category_name != self.target_category:
                continue

            bot.logger.info(
                "Scraping category [%d/%d]: %s",
                index + 1,
                len(category_names),
                category_name,
            )

            try:
                self._apply_options(bot)
                bot.browser.safe_click(self._get_categories(bot)[index])
                keep_going = self._scrape_subcategories(bot, category_name)
                if not keep_going:
                    bot.logger.info("Max books reached; stopping entire scrape.")
                    return

                if self.target_category:
                    bot.logger.info(
                        "Finished target category '%s'.", self.target_category
                    )
                    return
            except (NoSuchElementException, TimeoutException) as exc:
                bot.logger.error(
                    "Failed to process category '%s': %s", category_name, exc
                )
            finally:
                self._go_back_to_all_categories(bot)

    def _follow_redirect_if_present(self, bot: ScrapeBot) -> None:
        redirect = bot.browser.locate(locators.REDIRECT_LINK)
        if redirect is None:
            return

        bot.logger.info("Page redirect element found.")
        bot.browser.mouse_to(redirect)
        bot.browser.redirect_click(redirect)

    def _accept_cookie_banner_if_present(self, bot: ScrapeBot) -> None:
        accept_button = bot.browser.locate(locators.COOKIE_ACCEPT_BUTTON)
        if accept_button is None:
            return

        bot.logger.info("Cookie consent banner found.")
        bot.browser.safe_click(accept_button)

    def _validate_target_category(self, category_names: list[str]) -> None:
        if self.target_category is None:
            return
        if self.target_category in category_names:
            return

        raise ValueError(
            f"Target category '{self.target_category}' was not found. "
            f"Available categories: {category_names}"
        )

    def _get_categories(self, bot: ScrapeBot):
        categories = bot.browser.locate_all(locators.CATEGORIES)

        return categories[:-2]

    def _get_subcategories(self, bot: ScrapeBot):
        return bot.browser.locate_all(locators.SUBCATEGORY)

    def _go_back_to_subcategories(self, bot: ScrapeBot) -> None:
        breadcrumb = bot.browser.locate(locators.BREADCRUMB)
        if breadcrumb is not None:
            items = breadcrumb.find_elements(By.TAG_NAME, "li")
            if len(items) > 1:
                bot.browser.safe_click(items[1])

    def _go_back_to_all_categories(self, bot: ScrapeBot) -> None:
        all_categories = bot.browser.require_clickable(locators.ALL_CATEGORIES)
        bot.browser.safe_click(all_categories)

    def _apply_options(self, bot: ScrapeBot) -> None:
        audiobook_filter = bot.browser.locate(locators.AUDIOBOOK_FILTER)
        if audiobook_filter is not None and not audiobook_filter.is_selected():
            audiobook_link = bot.browser.require_clickable(locators.AUDIOBOOK_LINK)
            bot.browser.safe_click(audiobook_link)

    def _scrape_subcategories(self, bot: ScrapeBot, category_name: str) -> bool:
        total = len(self._get_subcategories(bot))
        bot.logger.info("  Found %d subcategories in '%s'.", total, category_name)

        for index in range(total):
            if not self._should_scrape(category_name, index):
                bot.logger.debug(
                    "  Skipping subcategory index %d in '%s'.", index, category_name
                )
                continue

            try:
                subcategories = self._get_subcategories(bot)
                if index >= len(subcategories):
                    bot.logger.warning(
                        "  Subcategory list changed; stopping early at index %d.", index
                    )
                    break

                subcategory = subcategories[index]
                subcategory_name = subcategory.text
                bot.browser.safe_click(subcategory)

                keep_going = self._scrape_all_pages(
                    bot, category_name, subcategory_name
                )
                if not keep_going:
                    return False
            except (NoSuchElementException, TimeoutException) as exc:
                bot.logger.error(
                    "  Failed on subcategory %d of '%s': %s", index, category_name, exc
                )
            except IndexError:
                bot.logger.error(
                    "Index error while scraping subcategories.", exc_info=True
                )
            finally:
                self._go_back_to_subcategories(bot)

        return True

    def _scrape_all_pages(
        self, bot: ScrapeBot, category_name: str, subcategory_name: str
    ) -> bool:
        bot.logger.info(
            "  Starting scrape on category '%s' / subcategory '%s'.",
            category_name,
            subcategory_name,
        )
        total_pages = self._get_pages(bot)

        for page_num in range(1, total_pages + 1):
            bot.logger.debug("    Page %d / %d", page_num, total_pages)
            html = self._get_page_html(bot)
            if html is None:
                bot.logger.warning("    Page %d failed to load; skipping.", page_num)
                continue

            books = bot.parser.parse_records(
                html,
                BS4_BOOK,
                context={
                    "category": category_name,
                    "subcategory": subcategory_name,
                },
            )

            records_to_write = self._limit_records(books)
            if records_to_write:
                bot.writer.write(records_to_write)
                self.records_written += len(records_to_write)
                bot.logger.info(
                    "    Written %d / %s books so far.",
                    self.records_written,
                    self.max_records if self.max_records is not None else "unlimited",
                )
                if self._record_limit_reached():
                    bot.logger.info("    max_books limit reached; stopping scrape.")
                    return False
            elif books and self._record_limit_reached():
                bot.logger.info("    max_books limit reached; stopping scrape.")
                return False
            else:
                bot.logger.warning("    No books extracted on page %d.", page_num)

            if page_num < total_pages and not self._go_to_next_page(bot):
                bot.logger.info("    Next page button not found; stopping early.")
                break

        return True

    def _get_pages(self, bot: ScrapeBot) -> int:
        page_elements = bot.browser.locate_all(locators.PAGE_NUMBERS)
        page_numbers = [
            element.text for element in page_elements if element.text.strip().isdigit()
        ]
        if not page_numbers:
            bot.logger.warning(
                "  Could not determine page count: no numeric page elements found. Scraping one page."
            )
            return 1
        return int(page_numbers[-1])

    def _get_page_html(self, bot: ScrapeBot) -> str | None:
        html = bot.browser.html()
        if self.settings.PAGE_LOAD_SENTINEL not in html:
            bot.logger.debug("    Main content missing; waiting and retrying.")
            bot.timing.sleep(self.settings.PAGE_RETRY_DELAY)
            bot.browser.refresh()
            html = bot.browser.html()

        if self.settings.PAGE_LOAD_SENTINEL not in html:
            return None

        return html

    def _go_to_next_page(self, bot: ScrapeBot) -> bool:
        next_button = bot.browser.locate(locators.NEXT_BUTTON)
        if next_button is None:
            return False
        bot.browser.safe_click(next_button)
        bot.timing.sleep(1)
        return True

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
