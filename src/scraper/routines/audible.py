from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By

from src.scraper.bot import ScrapeBot
from src.scraper.primitives import ScrapeBotRoutine
from src.scraper.routines.schema import AudibleSelector, BookRecord
from src.scraper.routines.settings import routine_settings


class AudibleBookParser:
    """Audible-specific page parser."""

    def parse_books(
        self,
        soup: BeautifulSoup,
        *,
        category: str,
        subcategory: str,
    ) -> list[BookRecord]:
        cards = soup.select(".productListItem")
        if not cards:
            cards = soup.select(".bc-list-item")

        records: list[BookRecord] = []
        for card in cards:
            record = self.parse_card(card, category=category, subcategory=subcategory)
            if record.name:
                records.append(record)

        return records

    def parse_card(self, card: Tag, *, category: str, subcategory: str) -> BookRecord:
        return BookRecord(
            name=self._text(card, "h3"),
            author=self._label_text(card, ".authorLabel", "By:"),
            narrator=self._label_text(card, ".narratorLabel", "Narrated by:"),
            runtime=self._label_text(card, ".runtimeLabel", "Length:"),
            release_date=self._label_text(card, ".releaseDateLabel", "Release date:"),
            language=self._label_text(card, ".languageLabel", "Language:"),
            stars=self._label_text(card, ".ratingsLabel", "Ratings:"),
            price=self._price(card),
            category=category,
            subcategory=subcategory,
        )

    @staticmethod
    def _text(card: Tag, selector: str) -> str | None:
        element = card.select_one(selector)
        if element is None:
            return None

        return element.get_text(" ", strip=True)

    def _label_text(self, card: Tag, selector: str, label: str) -> str | None:
        text = self._text(card, selector)
        if text is None:
            return None

        return text.replace(label, "").strip()

    @staticmethod
    def _price(card: Tag) -> str:
        buy_box = card.find(id="adbl-buy-box")
        text = buy_box.get_text(" ", strip=True) if buy_box else card.get_text(" ", strip=True)
        matches = re.findall(r"(\d+,?\d+\.\d+)", text)

        return matches[0] if matches else "Free"


class AudibleRoutine(ScrapeBotRoutine):
    """Imperative Audible scrape routine executed by ScrapeBot."""

    name = "audible"
    description = "Scrapes Audible book listings by category and subcategory."
    BASE_URL = "https://www.audible.co.uk/search"

    def __init__(
        self,
        *,
        base_url: str = BASE_URL,
        target_category: str | None = None,
        max_records: int | None = None,
        parser: AudibleBookParser | None = None,
        selectors: type[AudibleSelector] = AudibleSelector,
    ) -> None:
        self.base_url = base_url
        self.target_category = target_category
        self.max_records = max_records
        self.records_written = 0
        self.parser = parser or AudibleBookParser()
        self.selectors = selectors

    def execute(self, bot: ScrapeBot) -> None:
        bot.browser.open(self.base_url)
        self._follow_redirect_if_present(bot)
        self._accept_cookie_banner_if_present(bot)

        categories = self._get_categories(bot)
        category_names = [category.text for category in categories]
        bot.logger.info("Targeting %d categories.", len(category_names))

        for index, category_name in enumerate(category_names):
            if self.target_category and category_name != self.target_category:
                continue

            bot.logger.info("Scraping category [%d/%d]: %s", index + 1, len(category_names), category_name)

            try:
                self._apply_options(bot)
                bot.browser.safe_click(self._get_categories(bot)[index])
                keep_going = self._scrape_subcategories(bot, category_name)
                if not keep_going:
                    bot.logger.info("Max books reached; stopping entire scrape.")
                    return

                if self.target_category:
                    bot.logger.info("Finished target category '%s'.", self.target_category)
                    return
            except (NoSuchElementException, TimeoutException) as exc:
                bot.logger.error("Failed to process category '%s': %s", category_name, exc)
            finally:
                self._go_back_to_all_categories(bot)

    def _follow_redirect_if_present(self, bot: ScrapeBot) -> None:
        redirect = bot.browser.locate(self.selectors.redirect_link)
        if redirect is None:
            return

        bot.logger.info("Page redirect element found.")
        bot.browser.mouse_to(redirect)
        bot.browser.redirect_click(redirect)

    def _accept_cookie_banner_if_present(self, bot: ScrapeBot) -> None:
        accept_button = bot.browser.locate(self.selectors.cookie_accept_button)
        if accept_button is None:
            return

        bot.logger.info("Cookie consent banner found.")
        bot.browser.safe_click(accept_button)

    def _get_categories(self, bot: ScrapeBot):
        bot.browser.require_presence(self.selectors.categories)
        categories = bot.browser.find_all(self.selectors.categories)

        return categories[:-2]

    def _get_subcategories(self, bot: ScrapeBot):
        bot.browser.require_presence(self.selectors.subcategory_container)
        container = bot.browser.find(self.selectors.subcategory_container)
        return container.find_elements(By.CLASS_NAME, "refinementFormLink")

    def _go_back_to_subcategories(self, bot: ScrapeBot) -> None:
        bot.browser.require_presence(self.selectors.breadcrumb)
        breadcrumb = bot.browser.find(self.selectors.breadcrumb)
        items = breadcrumb.find_elements(By.TAG_NAME, "li")
        if len(items) > 1:
            bot.browser.safe_click(items[1])

    def _go_back_to_all_categories(self, bot: ScrapeBot) -> None:
        all_categories = bot.browser.require_clickable(self.selectors.all_categories)
        bot.browser.safe_click(all_categories)

    def _apply_options(self, bot: ScrapeBot) -> None:
        bot.browser.require_presence(self.selectors.audiobook_filter)
        audiobook_filter = bot.browser.find(self.selectors.audiobook_filter)
        if not audiobook_filter.is_selected():
            audiobook_link = bot.browser.require_clickable(self.selectors.audiobook_link)
            bot.browser.safe_click(audiobook_link)

    def _scrape_subcategories(self, bot: ScrapeBot, category_name: str) -> bool:
        total = len(self._get_subcategories(bot))
        bot.logger.info("  Found %d subcategories in '%s'.", total, category_name)

        for index in range(total):
            if not self._should_scrape(category_name, index):
                bot.logger.debug("  Skipping subcategory index %d in '%s'.", index, category_name)
                continue

            try:
                subcategories = self._get_subcategories(bot)
                if index >= len(subcategories):
                    bot.logger.warning("  Subcategory list changed; stopping early at index %d.", index)
                    break

                subcategory = subcategories[index]
                subcategory_name = subcategory.text
                bot.browser.safe_click(subcategory)

                keep_going = self._scrape_all_pages(bot, category_name, subcategory_name)
                if not keep_going:
                    return False
            except (NoSuchElementException, TimeoutException) as exc:
                bot.logger.error("  Failed on subcategory %d of '%s': %s", index, category_name, exc)
            except IndexError:
                bot.logger.error("Index error while scraping subcategories.", exc_info=True)
            finally:
                self._go_back_to_subcategories(bot)

        return True

    def _scrape_all_pages(self, bot: ScrapeBot, category_name: str, subcategory_name: str) -> bool:
        bot.logger.info("  Starting scrape on category '%s' / subcategory '%s'.", category_name, subcategory_name)
        total_pages = self._get_pages(bot)

        for page_num in range(1, total_pages + 1):
            bot.logger.debug("    Page %d / %d", page_num, total_pages)
            html = self._get_page_html(bot)
            if html is None:
                bot.logger.warning("    Page %d failed to load; skipping.", page_num)
                continue

            soup = bot.parser.soup(html)
            books = self.parser.parse_books(
                soup,
                category=category_name,
                subcategory=subcategory_name,
            )

            records_to_write = self._limit_records(books)
            if records_to_write:
                bot.writer.write(records_to_write, fieldnames=routine_settings.CSV_FIELDNAMES)
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
        try:
            bot.browser.require_presence(self.selectors.page_numbers)
        except TimeoutException as exc:
            bot.logger.warning("  Could not determine page count: %s. Scraping one page.", exc)
            return 1

        page_elements = bot.browser.find_all(self.selectors.page_numbers)
        page_numbers = [element.text for element in page_elements if element.text.strip().isdigit()]
        if not page_numbers:
            bot.logger.warning("  Could not determine page count: no numeric page elements found. Scraping one page.")
            return 1
        return int(page_numbers[-1])

    def _get_page_html(self, bot: ScrapeBot) -> str | None:
        html = bot.browser.html()
        if "adbl-impression-container" not in html:
            bot.logger.debug("    Main content missing; waiting and retrying.")
            bot.timing.sleep(routine_settings.PAGE_RETRY_DELAY)
            bot.browser.refresh()
            html = bot.browser.html()

        if "adbl-impression-container" not in html:
            return None
        return html

    def _go_to_next_page(self, bot: ScrapeBot) -> bool:
        next_button = bot.browser.locate(self.selectors.next_button)
        if next_button is None:
            return False
        bot.browser.safe_click(next_button)
        bot.timing.sleep(1)
        return True

    @staticmethod
    def _should_scrape(category_name: str, index: int) -> bool:
        return index not in routine_settings.SKIP_MAP.get(category_name, [])

    def _limit_records(self, records: list[BookRecord]) -> list[BookRecord]:
        if self.max_records is None:
            return records

        remaining = self.max_records - self.records_written
        if remaining <= 0:
            return []

        return records[:remaining]

    def _record_limit_reached(self) -> bool:
        return self.max_records is not None and self.records_written >= self.max_records
