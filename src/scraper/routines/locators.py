from selenium.webdriver.common.by import By

from src.scraper.selenium import SeleniumLocator


# =============== AUDIBLE SELENIUM LOCATORS ===============
COOKIE_ACCEPT_BUTTON = SeleniumLocator(
    by_method=By.CSS_SELECTOR,
    locator_name="#truste-consent-button",
)
REDIRECT_LINK = SeleniumLocator(
    by_method=By.CSS_SELECTOR,
    locator_name="#notification-banner-message .bc-link",
)
CATEGORIES = SeleniumLocator(
    by_method=By.CLASS_NAME,
    locator_name="refinementFormLink",
)
SUBCATEGORY_CONTAINER = SeleniumLocator(
    by_method=By.CLASS_NAME,
    locator_name="bc-spacing-medium",
)
BREADCRUMB = SeleniumLocator(
    by_method=By.CLASS_NAME,
    locator_name="categories",
)
ALL_CATEGORIES = SeleniumLocator(
    by_method=By.LINK_TEXT,
    locator_name="All Categories",
)
PAGE_NUMBERS = SeleniumLocator(
    by_method=By.CLASS_NAME,
    locator_name="pageNumberElement",
)
NEXT_BUTTON = SeleniumLocator(
    by_method=By.CLASS_NAME,
    locator_name="nextButton",
)
AUDIOBOOK_FILTER = SeleniumLocator(
    by_method=By.NAME,
    locator_name="feature_twelve_browse-bin",
)
AUDIOBOOK_LINK = SeleniumLocator(
    by_method=By.LINK_TEXT,
    locator_name="Audiobook",
)
