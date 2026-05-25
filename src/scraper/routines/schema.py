from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from selenium.webdriver.common.by import By

from src.scraper.selenium import SeleniumLocator


# =============== AUDIBLE SELECTOR SCHEMA ===============
class AudibleSelector:
    cookie_accept_button = SeleniumLocator(
        by_method=By.CSS_SELECTOR,
        locator_name="#truste-consent-button",
    )
    redirect_link = SeleniumLocator(
        by_method=By.CSS_SELECTOR,
        locator_name="#notification-banner-message .bc-link",
    )
    categories = SeleniumLocator(
        by_method=By.CLASS_NAME,
        locator_name="refinementFormLink",
    )
    subcategory_container = SeleniumLocator(
        by_method=By.CLASS_NAME,
        locator_name="bc-spacing-medium",
    )
    breadcrumb = SeleniumLocator(
        by_method=By.CLASS_NAME,
        locator_name="categories",
    )
    all_categories = SeleniumLocator(
        by_method=By.LINK_TEXT,
        locator_name="All Categories",
    )
    page_numbers = SeleniumLocator(
        by_method=By.CLASS_NAME,
        locator_name="pageNumberElement",
    )
    next_button = SeleniumLocator(
        by_method=By.CLASS_NAME,
        locator_name="nextButton",
    )
    audiobook_filter = SeleniumLocator(
        by_method=By.NAME,
        locator_name="feature_twelve_browse-bin",
    )
    audiobook_link = SeleniumLocator(
        by_method=By.LINK_TEXT,
        locator_name="Audiobook",
    )


# =============== AUDIBLE BOOK RECORD SCHEMA ===============
class BookRecord(BaseModel):
    """One Audible book listing record extracted from the live site.

    Example:
        >>> book_record = BookRecord(
        ...     name="Atomic    Enterprise   ",
        ...     author="Jason K. Miller",
        ...     narrator="Jon Mills",
        ...     runtime="4 hrs and 10 mins",
        ...     release_date="13-04-26",
        ...     language="English",
        ...     stars="Not rated yet",
        ...     price="11.26",
        ...     category="Business & Careers",
        ...     subcategory="Business Development & Entrepreneurship",
        ... )
        >>> assert book_record.name == "Atomic Enterprise"
    """

    name: str | None
    author: str | None
    narrator: str | None
    runtime: str | None
    release_date: str | None
    language: str | None
    stars: str | None
    price: str | None

    category: Annotated[str, Field(min_length=1)]
    subcategory: Annotated[str, Field(min_length=1)]

    model_config = ConfigDict(frozen=True)

    @field_validator("*", mode="before")
    @classmethod
    def normalize_text(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value

        normalized = re.sub(r"\s+", " ", value).strip()
        return normalized or None
