from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from selenium.webdriver.common.by import By

from src.scraper.bs4 import (
    BS4Locator,
    BS4RecordSchema,
    BS4TextField,
)
from src.scraper.selenium import SeleniumLocator


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


# =============== AUDIBLE SELECTOR SCHEMA ===============
class AudibleSelector:
    # ===== Browser interaction selectors
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

    # ===== HTML parsing schema
    books = BS4RecordSchema(
        record_container=BS4Locator(
            selector=".productListItem",
            fallback_selectors=(".bc-list-item",),
        ),
        model=BookRecord,
        skip_if_missing=("name",),
        fields={
            "name": BS4TextField(locator=BS4Locator(selector="h3")),
            "author": BS4TextField(
                locator=BS4Locator(selector=".authorLabel"),
                remove_prefix="By:",
            ),
            "narrator": BS4TextField(
                locator=BS4Locator(selector=".narratorLabel"),
                remove_prefix="Narrated by:",
            ),
            "runtime": BS4TextField(
                locator=BS4Locator(selector=".runtimeLabel"),
                remove_prefix="Length:",
            ),
            "release_date": BS4TextField(
                locator=BS4Locator(selector=".releaseDateLabel"),
                remove_prefix="Release date:",
            ),
            "language": BS4TextField(
                locator=BS4Locator(selector=".languageLabel"),
                remove_prefix="Language:",
            ),
            "stars": BS4TextField(
                locator=BS4Locator(selector=".ratingsLabel"),
                remove_prefix="Ratings:",
            ),
            "price": BS4TextField(
                locator=BS4Locator(selector="#adbl-buy-box"),
                regex_pattern=r"(\d+,?\d+\.\d+)",
                default="Free",
            ),
        },
    )
