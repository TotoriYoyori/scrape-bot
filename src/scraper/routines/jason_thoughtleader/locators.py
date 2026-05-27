from selenium.webdriver.common.by import By

from src.scraper.selenium import SeleniumLocator

COOKIE_ACCEPT_BUTTON = SeleniumLocator(
    by_method=By.CSS_SELECTOR,
    locator_name='[data-control-name="ga-cookie.consent.accept.v4"]',
)
LOGIN_BUTTON = SeleniumLocator(
    by_method=By.PARTIAL_LINK_TEXT,
    locator_name="登录",
)
EMAIL_INPUT = SeleniumLocator(
    by_method=By.CSS_SELECTOR,
    locator_name='input[type="email"][autocomplete="username webauthn"]',
)
PASSWORD_INPUT = SeleniumLocator(
    by_method=By.CSS_SELECTOR,
    locator_name='input[type="password"][autocomplete="current-password"]',
)
LOGIN_SUBMIT_BUTTON = SeleniumLocator(
    by_method=By.XPATH,
    locator_name=(
        '(//input[@type="password" and @autocomplete="current-password"]'
        '/following::button[@type="button"])[1]'
    ),
)
START_POST_BUTTON = SeleniumLocator(
    by_method=By.CSS_SELECTOR,
    locator_name=".truncate .t-normal",
)
POST_TEXTBOX = SeleniumLocator(
    by_method=By.CSS_SELECTOR,
    locator_name='[role="textbox"]',
)
POST_SUBMIT_BUTTON = SeleniumLocator(
    by_method=By.CLASS_NAME,
    locator_name="share-box_actions",
)
MY_NETWORK_BUTTON = SeleniumLocator(
    by_method=By.CSS_SELECTOR,
    locator_name='[title="My Network"]',
)
CONNECTABLE_BUTTONS = SeleniumLocator(
    by_method=By.CSS_SELECTOR,
    locator_name='[aria-label^="Invite"]',
)
