# ----- Built-in
import logging
import time

# ----- Third-party
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException

# ----- Logging Setup and Constants
logger = logging.getLogger(__name__)


# --------------------
class AudibleController:
    """
    A Selenium-based controller for the Audible website. This controller depends on
    Audible's DOM structure and may break if them layout changes. It locates and interacts with page elements.

    :param link: URL of the Audible page to load.
    :type link: str

    Can be called using a context manager to ensure WebDriver is always closed, like so:
    Example:
        >>> with AudibleController("https://www.audible.com/search") as controller:
        >>>     categories = controller.get_all_categories()

    Or can be called without context manager, like so:
    Example:
        >>> controller = AudibleController("https://www.audible.com/search")
        >>> categories = controller.get_all_categories()
        >>> for cat in categories:
        ...     print(cat.text)
        >>> controller.close()
    """

    def __init__(self, link: str) -> None:
        """
        Initialize the Chrome WebDriver and open the given Audible link.

        :param link: Audible URL to open in the browser.
        :type link: str
        """
        options = Options()
        # options.add_argument("--headless=new")
        # options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=options)
        self.driver.get(link)
        self._wait = WebDriverWait(self.driver, timeout=10)

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "AudibleController":
        """Return self so the controller can be used in a ``with`` statement."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Ensure the WebDriver is always quit, even if an exception occurred."""
        self.close()
        return False  # Do not suppress exceptions

    def close(self) -> None:
        """
        Quit the WebDriver and release all associated resources.
        Safe to call multiple times.
        """
        try:
            self.driver.quit()
        except Exception as e:
            logger.debug(f"{e}\n\nDriver was already closed or could not be quit cleanly.")

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------
    def has_redirect_popup(self) -> bool:
        try:
            self._wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#notification-banner-message .bc-link"))
            )
        except TimeoutException:
            return False

        logger.info("Page redirect element found ...")
        return True

    def get_redirect(self) -> WebElement:
        return self.driver.find_element(By.CSS_SELECTOR, "#notification-banner-message .bc-link")

    def get_all_categories(self) -> list[WebElement]:
        """
        Retrieve all main category elements from the Audible page.
        Skips the last two elements, which are not concrete categories.

        :raises TimeoutException: If the category elements do not appear within the timeout.
        :return: List of Selenium WebElement objects representing categories.
        """
        self._wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "refinementFormLink"))
        )
        all_categories = self.driver.find_elements(By.CLASS_NAME, "refinementFormLink")
        return all_categories[:-2]

    def get_subcategories(self) -> list[WebElement]:
        """
        Retrieve all subcategory elements under the currently active category.

        :raises TimeoutException: If the subcategory container does not appear within the timeout.
        :return: List of Selenium WebElement objects representing subcategories.
        :rtype: list[WebElement]
        """
        self._wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "bc-spacing-medium"))
        )
        container = self.driver.find_element(By.CLASS_NAME, "bc-spacing-medium")
        return container.find_elements(By.CLASS_NAME, "refinementFormLink")

    def go_back_sub(self) -> None:
        """
        Navigate from the current subcategory back to its parent category.

        :raises TimeoutException: If the category breadcrumb does not appear within the timeout.
        """
        self._wait.until(EC.presence_of_element_located((By.CLASS_NAME, "categories")))
        breadcrumb = self.driver.find_element(By.CLASS_NAME, "categories")
        items = breadcrumb.find_elements(By.TAG_NAME, "li")
        items[1].click()

    def go_back_cat(self) -> None:
        """
        Navigate back to the main categories page via the 'All Categories' link.

        :raises TimeoutException: If the link does not appear within the timeout.
        """
        self._wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "All Categories")))
        self.driver.find_element(By.LINK_TEXT, "All Categories").click()

    # ------------------------------------------------------------------
    # Page state helpers
    # ------------------------------------------------------------------

    def total_loot(self) -> int:
        """
        Count the number of audiobook items currently displayed on the page.

        :return: Total number of product list items found.
        :rtype: int
        """
        return len(self.driver.find_elements(By.CLASS_NAME, "productListItem"))

    def get_pages(self) -> int:
        """
        Retrieve the total number of result pages available for the current listing.

        :raises TimeoutException: If pagination elements do not appear within the timeout.
        :raises ValueError: If no page number elements are found.
        :return: Total number of pages.
        :rtype: int
        """
        self._wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "pageNumberElement"))
        )
        page_elements = self.driver.find_elements(By.CLASS_NAME, "pageNumberElement")
        page_numbers = [el.text for el in page_elements if el.text.strip().isdigit()]

        if not page_numbers:
            raise ValueError(
                "Could not determine page count — no numeric page elements found."
            )

        return int(page_numbers[-1])

    def _safe_click(self, element) -> None:
        """
        Try normal click first; if intercepted, fallback to JS click.
        """
        try:
            element.click()
        except ElementClickInterceptedException:
            logger.debug("Click intercepted — using JS click instead.")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            self.driver.execute_script("arguments[0].click();", element)

    def go_to_next_page(self) -> bool:
        """
        Click the 'next page' button if it exists.

        :return: True if navigation succeeded, False if there is no next page.
        """
        try:
            next_btn = self._wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "nextButton"))
            )
            self._safe_click(next_btn)
            time.sleep(1)  # optional: wait for page load
            return True

        except (NoSuchElementException, TimeoutException):
            logger.debug("No next page button found — likely on the last page.")
            return False


    def apply_options(self) -> None:
        """
        Apply Audible-specific filtering options, specifically selecting the
        'Audiobook' format filter if it is not already active.

        :raises TimeoutException: If the filter element does not appear within the timeout.
        """
        self._wait.until(
            EC.presence_of_element_located((By.NAME, "feature_twelve_browse-bin"))
        )
        if not self.driver.find_element(
            By.NAME, "feature_twelve_browse-bin"
        ).is_selected():
            self._wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Audiobook")))
            self.driver.find_element(By.LINK_TEXT, "Audiobook").click()
