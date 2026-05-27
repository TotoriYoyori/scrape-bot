import time

from selenium import webdriver
from selenium.common import WebDriverException
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.scraper.primitives import ScrapeBotModule
from src.scraper.selenium.exceptions import (
    SeleniumFallbackClickError,
    SeleniumLoadClickError,
)
from src.scraper.selenium.primitives import SeleniumLocator
from src.scraper.selenium.settings import SeleniumBrowserConfig


# =============== SELENIUM MODULE ===============
class SeleniumModule(ScrapeBotModule):
    """Browser module that adapts Selenium for extra resilience in scraper routines.

    Args:
        config: Optional browser configuration. When omitted, the default
            Selenium browser config is used.

    Attributes:
        config: Active Selenium browser configuration.
        driver: Chrome WebDriver owned by this module.
        wait: WebDriverWait instance configured from ``config``.

    Example:
        >>> browser = SeleniumModule(config=SeleniumBrowserConfig(HEADLESS=True))
        >>> assert isinstance(browser.driver, ChromeWebDriver)
        >>> browser.close()
    """

    name = "browser"

    def __init__(self, config: SeleniumBrowserConfig | None = None) -> None:
        self.config = config or SeleniumBrowserConfig()

        self.driver = self._build_driver()
        self.wait = self._build_wait()

    # ===== Driver and Wait Construction Helper
    def _build_driver(self) -> ChromeWebDriver:
        options = Options()
        for field_name, field in self.config.model_fields.items():
            field_value = getattr(self.config, field_name)
            chrome_option = (field.json_schema_extra or {}).get("chrome_option")
            if not chrome_option or not field_value:
                continue

            match chrome_option["method"]:
                case "add_argument":
                    value = chrome_option["value"].format(value=field_value)
                    options.add_argument(value)
                case "add_experimental_option":
                    options.add_experimental_option(
                        chrome_option["key"],
                        chrome_option["value"],
                    )

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        return webdriver.Chrome(options=options)

    def _build_wait(self) -> WebDriverWait:
        return WebDriverWait(
            self.driver,
            timeout=self.config.TIMEOUT,
            poll_frequency=self.config.POLL_FREQUENCY,
        )

    # ===== Thin wrapper around Selenium's Driver
    def open(self, url: str) -> None:
        self.driver.get(url)

    def close(self) -> None:
        self.driver.quit()

    def html(self) -> str:
        return self.driver.page_source

    def refresh(self) -> None:
        self.driver.refresh()

    def back(self) -> None:
        self.driver.back()

    def find(self, locator: SeleniumLocator) -> WebElement:
        return self.driver.find_element(*locator.as_tuple())

    def find_all(self, locator: SeleniumLocator) -> list[WebElement]:
        return self.driver.find_elements(*locator.as_tuple())

    # ===== More resilient Selenium's search and return wrapper
    def locate(self, locator: SeleniumLocator) -> WebElement | None:
        try:
            return self.wait.until(EC.visibility_of_element_located(locator.as_tuple()))
        except TimeoutException:
            return None

    def locate_all(self, locator: SeleniumLocator) -> list[WebElement]:
        try:
            return self.wait.until(
                EC.visibility_of_all_elements_located(locator.as_tuple())
            )
        except TimeoutException:
            return []

    def require_presence(self, locator: SeleniumLocator) -> WebElement:
        return self.wait.until(EC.presence_of_element_located(locator.as_tuple()))

    def require_clickable(self, locator: SeleniumLocator) -> WebElement:
        return self.wait.until(EC.element_to_be_clickable(locator.as_tuple()))

    def require_interactable(self, locator: SeleniumLocator) -> WebElement:
        return self.wait.until(
            lambda driver: next(
                (
                    element
                    for element in driver.find_elements(*locator.as_tuple())
                    if element.is_displayed() and element.is_enabled()
                ),
                False,
            )
        )

    # ===== Resilient Selenium clicking methods
    def redirect_click(self, element: WebElement) -> None:
        for _ in range(self.config.REDIRECT_CLICK_RETRY_LIMIT):
            try:
                self.wait.until(EC.element_to_be_clickable(element))
                self.safe_click(element)
                self.wait.until(EC.invisibility_of_element(element))

                return
            except (TimeoutException, StaleElementReferenceException):
                continue

        raise SeleniumLoadClickError()

    def safe_click(self, element: WebElement) -> None:
        def javascript_click() -> None:
            try:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", element
                )
                self.driver.execute_script("arguments[0].click();", element)
            except WebDriverException as exc:
                raise SeleniumFallbackClickError() from exc

        try:
            element.click()
        except ElementClickInterceptedException:
            javascript_click()

    # ===== Manual human behavior Selenium methods
    def mouse_to(self, element: WebElement) -> None:
        ActionChains(self.driver).move_to_element(element).perform()

    def scroll_to(self, element: WebElement, y_offset: int = 0) -> None:
        scroll_origin = ScrollOrigin.from_element(element)
        ActionChains(self.driver).scroll_from_origin(
            scroll_origin, 0, y_offset
        ).perform()

    def type_to(self, element: WebElement, text: str) -> None:
        element.clear()
        for char in text:
            element.send_keys(char)
            if self.config.TYPE_DELAY > 0:
                time.sleep(self.config.TYPE_DELAY)
