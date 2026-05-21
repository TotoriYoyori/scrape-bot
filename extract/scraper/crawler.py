# ----- Built-in
import re
import logging

# ----- Third-party
from bs4 import BeautifulSoup

# ----- Logging Setup
logger = logging.getLogger(__name__)


# --------------------
class AudibleCrawler:
    """
    Parses Audible audiobook listing pages using BeautifulSoup.
    Accepts raw HTML and extracts structured audiobook records.

    Can be unit-tested without a browser as it accepts raw HTML string.

    :param html: Raw HTML string of an Audible listing page.
    :type html: str

    Example:
        >>> crawler = AudibleCrawler(page_html)
        >>> books = crawler.extract_books()
        >>> for book in books:
        ...     print(book["name"], book["price"])
    """

    def __init__(self, html: str) -> None:
        """
        Parse and store a BeautifulSoup tree from raw HTML.

        :param html: Raw HTML string to parse.
        :param category: Audible category of the HTML currently parsed as a soup.
        :type html: str
        """
        self.soup = BeautifulSoup(html, "html.parser")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_books(self) -> list[dict]:
        """
        Extract all audiobook records from the current page HTML.

        Each record contains: name, author, narrator, runtime, release_date,
        language, stars, and price.  Records are assembled by aligning
        positional lists, so the page must be fully loaded before calling this.

        :return: List of dicts, one per audiobook on the page.
        :rtype: list[dict]
        """
        names = self._get_names()
        authors = self._get_authors()
        narrators = self._get_narrators()
        runtimes = self._get_runtimes()
        releases = self._get_releases()
        languages = self._get_languages()
        ratings = self._get_ratings()
        prices = self._get_prices()

        field_lists = {
            "name": names,
            "author": authors,
            "narrator": narrators,
            "runtime": runtimes,
            "release_date": releases,
            "language": languages,
            "stars": ratings,
            "price": prices,
        }

        # Validate all lists are the same length to catch silent misalignments
        lengths = {field: len(values) for field, values in field_lists.items()}
        if len(set(lengths.values())) != 1:
            logger.warning(
                "Field list length mismatch — data may be misaligned. Counts: %s",
                lengths,
            )

        count = len(names)
        books = []
        for i in range(count):
            books.append(
                {
                    field: (values[i] if i < len(values) else None)
                    for field, values in field_lists.items()
                }
            )

        return books

    # ------------------------------------------------------------------
    # Private extraction helpers
    # ------------------------------------------------------------------

    def _get_names(self) -> list[str]:
        """
        Extract audiobook titles from h3 headings, skipping the page header.

        :return: List of title strings.
        :rtype: list[str]
        """
        books = self.soup.select(".bc-list-item h3")
        return [item.get_text().replace("\n", "").strip() for item in books]

    def _get_authors(self) -> list[str]:
        """
        Extract author names, stripping the 'Written by:' label.

        :return: List of author name strings.
        :rtype: list[str]
        """
        items = self.soup.select(".authorLabel")
        return [
            item.get_text().replace("\n", "").replace("By:", "").strip()
            for item in items
        ]

    def _get_narrators(self) -> list[str]:
        """
        Extract narrator names, stripping the 'Narrated by:' label.

        :return: List of narrator name strings.
        :rtype: list[str]
        """
        items = self.soup.select(".narratorLabel")
        return [
            item.get_text().replace("\n", "").replace("Narrated by:", "").strip()
            for item in items
        ]

    def _get_runtimes(self) -> list[str]:
        """
        Extract audiobook runtimes, stripping the 'Length:' label.

        :return: List of runtime strings (e.g. '10 hrs and 23 mins').
        :rtype: list[str]
        """
        items = self.soup.select(".runtimeLabel")
        return [
            item.get_text().replace("\n", "").replace("Length:", "").strip()
            for item in items
        ]

    def _get_releases(self) -> list[str]:
        """
        Extract release dates, stripping the 'Release Date:' label.

        :return: List of release date strings.
        :rtype: list[str]
        """
        items = self.soup.select(".releaseDateLabel")
        return [
            item.get_text().replace("\n", "").replace("Release date:", "").strip()
            for item in items
        ]

    def _get_languages(self) -> list[str]:
        """
        Extract languages, stripping the 'Language:' label.

        :return: List of language strings.
        :rtype: list[str]
        """
        items = self.soup.select(".languageLabel")
        return [
            item.get_text().replace("\n", "").replace("Language:", "").strip()
            for item in items
        ]

    def _get_ratings(self) -> list[str]:
        """
        Extract star ratings, stripping the 'Ratings:' label.

        :return: List of rating strings.
        :rtype: list[str]
        """
        items = self.soup.select(".ratingsLabel")
        return [
            item.get_text().replace("\n", "").replace("Ratings:", "").strip()
            for item in items
        ]

    def _get_prices(self) -> list[str]:
        """
        Extract prices from the buy box. Returns 'Free' when no numeric
        price is found.

        :return: List of price strings (e.g. '14.95' or 'Free').
        :rtype: list[str]
        """
        buy_boxes = self.soup.find_all(id="adbl-buy-box")
        prices = []
        for box in buy_boxes:
            matches = re.findall(r"(\d+,?\d+\.\d+)", box.get_text())
            prices.append(matches[0] if matches else "Free")
        return prices
