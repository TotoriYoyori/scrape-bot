# ----- Built-in
import csv
import logging
import time

# ----- Third-party
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# ----- Self-created
from .crawler import AudibleCrawler
from .controller import AudibleController

logger = logging.getLogger(__name__)

# Seconds to wait before retrying a page that did not load correctly
PAGE_RETRY_DELAY = 2

# CSV field order — explicit so output columns are always consistent
CSV_FIELDNAMES = [
    "name",
    "author",
    "narrator",
    "runtime",
    "release_date",
    "language",
    "stars",
    "price",
    "category",
    "subcategory"
]

# Subcategory indices to skip per category, due to known Audible redirects
# or pages that do not follow the standard listing structure.
# Stored here (not buried in a method) so they can be updated without
# touching any logic code.
SKIP_MAP: dict[str, list[int]] = {
    "Biographies & Memoirs": [2, 5],
    "Literature & Fiction": [10, 11],
    "History": [5],
    "Mystery, Thriller & Suspense": [3],
    "Romance": [1, 7, 8],
    "Sports & Outdoors": [0, 3, 23],
}


class AudibleScraper:
    """
    Orchestrates an Audible scraping run using AudibleController (Selenium)
    and AudibleCrawler (BeautifulSoup).

    Navigates every category and subcategory, extracts audiobook records from
    each page, and writes results incrementally to a CSV file.

    Usage as a context manager is recommended so the underlying WebDriver is
    always closed cleanly:

    Example:
        >>> with AudibleScraper("https://www.audible.com/search", "output.csv") as scraper:
        >>>    scraper.scrape()

    :param base_url: Audible search or browse URL to start from.
    :type base_url: str
    :param output_csv: Path of the CSV file to write results into.
    :type output_csv: str
    """

    def __init__(
        self,
        base_url: str,
        output_csv: str = "flatfiles/export/export_audible_scrape.csv",
        max_books: int | None = None,
    ) -> None:
        """
        Initialize the scraper with a browser controller and output path.

        :param base_url: URL to open at the start of the scraping run.
        :param output_csv: Destination CSV file path, relative to wherever this scraper is called.
        :param max_books: Stop writing after this many books have been collected.
            Useful for smoke-testing without running a full scrape. ``None`` means
            no limit (default).
        """
        self.robot = AudibleController(base_url)
        self.output_csv = output_csv
        self.max_books = max_books
        self._header_written = False
        self._books_written = 0

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------
    def __enter__(self) -> "AudibleScraper":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.robot.close()
        return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def scrape(self, target_category: str | None = None) -> None:
        """
        Scrape either all categories or a single specified category.

        :param target_category: If provided, only this category will be scraped.
        :type target_category: str | None
        """
        if self.robot.has_redirect_popup():
            self.robot.get_redirect().click()

        categories = self.robot.get_all_categories()
        cat_names = [cat.text for cat in categories]

        logger.info("Targetting %d categories.", len(cat_names))

        for index, cat_name in enumerate(cat_names):
            if target_category and cat_name != target_category:
                continue

            logger.info(
                "Scraping category [%d/%d]: %s",
                index + 1,
                len(cat_names),
                cat_name,
            )

            try:
                self.robot.apply_options()
                self.robot.get_all_categories()[index].click()
                keep_going = self._scrape_subcategories(cat_name)
                if not keep_going:
                    logger.info("Max books reached — stopping entire scrape.")
                    return

                # 👉 If single category mode, stop after first match
                if target_category:
                    logger.info("Finished target category '%s'.", target_category)
                    return
            except (NoSuchElementException, TimeoutException) as exc:
                logger.error("Failed to process category '%s': %s", cat_name, exc)
            finally:
                self.robot.go_back_cat()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _scrape_subcategories(self, category_name: str) -> bool | None:
        """
        Iterate over all subcategories of the currently active category
        and scrape each one.

        :param category_name: Human-readable category name, used for skip-map lookup.
        :type category_name: str
        """
        total = len(self.robot.get_subcategories())
        logger.info(
            "  Found %d subcategories in '%s'.",
            total,
            category_name
        )

        for index in range(total):
            if not self._should_scrape(category_name, index):
                logger.debug(
                    "  Skipping subcategory index %d in '%s'.", index, category_name
                )
                continue

            try:
                # Re-fetch subcategory list — DOM may have been re-rendered after navigation
                subcategories = self.robot.get_subcategories()
                if index >= len(subcategories):
                    logger.warning("  Subcategory list changed — stopping early at index %d.", index)
                    break

                subcat_element = subcategories[index]
                subcat_name = subcat_element.text
                subcat_element.click()

                keep_going = self._scrape_all_pages(category_name, subcat_name)
                if not keep_going:
                    return False

            except (NoSuchElementException, TimeoutException) as exc:
                logger.error(
                    "  Failed on subcategory %d of '%s': %s",
                    index,
                    category_name,
                    exc
                )
            except IndexError:
                logger.error("Index error crash?")
            finally:
                # Always return to category view so the next subcategory can be reached
                self.robot.go_back_sub()

        return True

    def _scrape_all_pages(self, category_name: str, subcategory_name: str) -> bool | None:
        """
        Scrape every page of results within the currently active subcategory.

        :param category_name: Category name, used only for log messages.
        :type category_name: str
        """
        logging.info("  Starting scrape on category '%s' / subcategory '%s'.",
                     category_name, subcategory_name)
        try:
            total_pages = self.robot.get_pages()
        except (ValueError, TimeoutException) as exc:
            logger.warning(
                "  Could not determine page count: %s. Scraping one page.", exc
            )
            total_pages = 1

        for page_num in range(1, total_pages + 1):
            logger.debug("    Page %d / %d", page_num, total_pages)
            html = self._get_page_html()

            if html is None:
                logger.warning("    Page %d failed to load — skipping.", page_num)
                continue

            books = AudibleCrawler(html).extract_books()
            if books:
                books = [
                    {**book, "category": category_name, "subcategory": subcategory_name}
                    for book in books
                ]
                keep_going = self._write_csv(books)
                if not keep_going:
                    logger.info("    max_books limit reached — stopping scrape.")
                    return False
            else:
                logger.warning("    No books extracted on page %d.", page_num)

            # Stop paginating if we are on the last page
            if page_num < total_pages:
                if not self.robot.go_to_next_page():
                    logger.info("    Next page button not found — stopping early.")
                    break

        return True

    def _get_page_html(self) -> str | None:
        """
        Return the current page source, retrying once after a short delay
        if the main content container is absent.

        :return: Raw HTML string, or None if the page still fails after one retry.
        :rtype: str | None
        """
        html = self.robot.driver.page_source
        if "adbl-impression-container" not in html:
            logger.debug("    Main content missing — waiting and retrying.")
            time.sleep(PAGE_RETRY_DELAY)
            self.robot.driver.refresh()
            html = self.robot.driver.page_source

        if "adbl-impression-container" not in html:
            return None
        return html

    def _write_csv(self, books: list[dict]) -> bool:
        """
        Append a list of book records to the output CSV file.
        Writes the header row automatically on the first call.

        When ``max_books`` is set, only writes up to the remaining quota and
        returns ``False`` once the limit is reached so callers can stop early.

        :param books: List of book record dicts, as returned by AudibleCrawler.extract_books().
        :type books: list[dict]
        :return: ``False`` if the ``max_books`` limit has been reached, ``True`` otherwise.
        :rtype: bool
        """
        if not books:
            return True

        if self.max_books is not None:
            remaining = self.max_books - self._books_written
            if remaining <= 0:
                return False
            books = books[:remaining]

        with open(self.output_csv, "a", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(
                fh, fieldnames=CSV_FIELDNAMES, extrasaction="ignore"
            )
            if not self._header_written:
                writer.writeheader()
                self._header_written = True
            writer.writerows(books)

        self._books_written += len(books)
        logger.info(
            "    Written %d / %s books so far.",
            self._books_written,
            self.max_books if self.max_books is not None else "unlimited",
        )

        return self.max_books is None or self._books_written < self.max_books

    @staticmethod
    def _should_scrape(category_name: str, index: int) -> bool:
        """
        Determine whether a subcategory at the given index should be scraped,
        based on the known-problematic index list in SKIP_MAP.

        :param category_name: The parent category name.
        :type category_name: str
        :param index: Zero-based index of the subcategory in the current listing.
        :type index: int
        :return: True if the subcategory should be scraped, False if it should be skipped.
        :rtype: bool
        """
        return index not in SKIP_MAP.get(category_name, [])
