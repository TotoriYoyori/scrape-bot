from __future__ import annotations

from typing import TYPE_CHECKING

from selenium.common.exceptions import TimeoutException

from yetl.scraper.primitives import ScrapeBotRoutine

from . import locators
from .settings import JasonThoughtleaderSettings

if TYPE_CHECKING:
    from yetl.scraper.bot import ScrapeBot


class JasonThoughtleaderRoutine(ScrapeBotRoutine):
    """Proof-of-concept LinkedIn posting routine using the ScrapeBot framework."""

    name = "jason_thoughtleader"
    description = "Logs into LinkedIn and posts configured thought-leader text."

    def __init__(
        self,
        *,
        settings: JasonThoughtleaderSettings | None = None,
        post_text: str | None = None,
        follow_people: bool = False,
    ) -> None:
        self.settings = settings or JasonThoughtleaderSettings()
        self.post_text = post_text or self.settings.POST_TEXT
        self.follow_people = follow_people

        self._bot: ScrapeBot | None = None

    @property
    def bot(self) -> ScrapeBot:
        if self._bot is None:
            raise RuntimeError(
                "JasonThoughtleaderRoutine has not been bound to a ScrapeBot."
            )

        return self._bot

    def reset_state(self) -> None:
        self.bot.browser.open(self.settings.HOME_URL)

    def setup(self) -> None:
        # ===== Accept Optional Cookie Banner
        cookie_button = self.bot.browser.locate(locators.COOKIE_ACCEPT_BUTTON)
        if cookie_button is not None:
            self.bot.browser.mouse_to(cookie_button)
            self.bot.browser.safe_click(cookie_button)

        # ===== Open Login Form
        login_button = self.bot.browser.require_clickable(locators.LOGIN_BUTTON)
        self.bot.browser.mouse_to(login_button)
        self.bot.browser.safe_click(login_button)

        # ===== Fill Credentials
        email_input = self.bot.browser.require_interactable(locators.EMAIL_INPUT)
        self.bot.browser.mouse_to(email_input)
        self.bot.browser.type_to(email_input, self.settings.EMAIL)

        password_input = self.bot.browser.require_interactable(locators.PASSWORD_INPUT)
        self.bot.browser.mouse_to(password_input)
        self.bot.browser.type_to(password_input, self.settings.PASSWORD)

        # ===== Submit Login
        submit_button = self.bot.browser.require_clickable(locators.LOGIN_SUBMIT_BUTTON)
        self.bot.browser.mouse_to(submit_button)
        self.bot.browser.safe_click(submit_button)
        self.bot.logger.info("LinkedIn login submitted.")

    def execute(self, bot: ScrapeBot) -> None:
        # ===== Bind Routine To Bot And Login
        self._bot = bot
        self.reset_state()
        self.setup()

        try:
            # ===== Create New Post
            start_post_button = self.bot.browser.require_clickable(
                locators.START_POST_BUTTON
            )
            self.bot.browser.mouse_to(start_post_button)
            self.bot.browser.safe_click(start_post_button)

            # ===== Fill Post Text
            textbox = self.bot.browser.require_clickable(locators.POST_TEXTBOX)
            self.bot.browser.mouse_to(textbox)
            self.bot.browser.type_to(textbox, self.post_text)

            # ===== Submit Post
            submit_button = self.bot.browser.require_clickable(
                locators.POST_SUBMIT_BUTTON
            )
            self.bot.browser.mouse_to(submit_button)
            self.bot.browser.safe_click(submit_button)
            self.bot.logger.info("LinkedIn post submitted.")

            # ===== Optionally Follow Suggested People
            if self.follow_people:
                self._follow_people()
        except TimeoutException as exc:
            self.bot.logger.error("LinkedIn routine failed: %s", exc)

    def scrape_page(self) -> None:
        return None

    def write(self) -> None:
        return None

    def _follow_people(self) -> None:
        my_network_button = self.bot.browser.require_clickable(
            locators.MY_NETWORK_BUTTON
        )
        self.bot.browser.mouse_to(my_network_button)
        self.bot.browser.safe_click(my_network_button)
        self.bot.logger.info("Visited LinkedIn My Network.")

        connectable_buttons = self.bot.browser.locate_all(locators.CONNECTABLE_BUTTONS)
        for button in connectable_buttons[: self.settings.FOLLOW_LIMIT]:
            self.bot.browser.scroll_to(button)
            self.bot.browser.mouse_to(button)
            self.bot.browser.safe_click(button)
