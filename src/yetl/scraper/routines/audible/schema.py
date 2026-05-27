from typing import Annotated

from pydantic import Field

from yetl.scraper.bs4 import (
    BS4Locator,
    BS4RecordSchema,
    BS4TextField,
)
from yetl.scraper.primitives import ScrapeBotRoutineRecord


# =============== AUDIBLE BOOK RECORD SCHEMA ===============
class BookRecord(ScrapeBotRoutineRecord):
    """One Audible book listing record extracted from the live site.

    Example:
        >>> book_record = BookRecord(
        ...     name="Atomic    Enterprise\\n ",
        ...     author="Ｊａｓｏｎ\\xa0K.\\xa0Ｍｉｌｌｅｒ\\u200b",
        ...     narrator="Jon Mills",
        ...     runtime="4 hrs and 10 mins",
        ...     release_date="13-04-26",
        ...     language="English",
        ...     stars="   ",
        ...     price="11.26",
        ...     category="Business & Careers",
        ...     subcategory="Business Development & Entrepreneurship",
        ... )
        >>> assert book_record.name == "Atomic Enterprise"
        >>> assert book_record.author == "Jason K. Miller"
        >>> assert book_record.stars is None
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


# =============== AUDIBLE BOOK RECORD HTML SCHEMA ===============
BS4_BOOK = BS4RecordSchema(
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
            trim_prefix="By:",
        ),
        "narrator": BS4TextField(
            locator=BS4Locator(selector=".narratorLabel"),
            trim_prefix="Narrated by:",
        ),
        "runtime": BS4TextField(
            locator=BS4Locator(selector=".runtimeLabel"),
            trim_prefix="Length:",
        ),
        "release_date": BS4TextField(
            locator=BS4Locator(selector=".releaseDateLabel"),
            trim_prefix="Release date:",
        ),
        "language": BS4TextField(
            locator=BS4Locator(selector=".languageLabel"),
            trim_prefix="Language:",
        ),
        "stars": BS4TextField(
            locator=BS4Locator(selector=".ratingsLabel"),
            trim_prefix="Ratings:",
        ),
        "price": BS4TextField(
            locator=BS4Locator(selector="#adbl-buy-box"),
            regex_pattern=r"(\d+,?\d+\.\d+)",
            default="Free",
        ),
    },
)
