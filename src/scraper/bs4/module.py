import re
from typing import Any

from bs4 import BeautifulSoup
from bs4.element import PageElement, Tag

from src.scraper.primitives import ScrapeBotModule
from src.scraper.bs4.primitives import (
    BS4Locator,
    BS4RecordSchema,
    BS4TextField,
)
from src.scraper.bs4.settings import BeautifulSoupConfig


# =============== BEAUTIFUL SOUP MODULE ===============
class BeautifulSoupModule(ScrapeBotModule):
    """Parser module that adapts BeautifulSoup for scraper routines."""

    name = "parser"

    def __init__(self, config: BeautifulSoupConfig | None = None) -> None:
        self.config = config or BeautifulSoupConfig()

    # ===== Soup Construction Helper
    def soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, self.config.PARSER)

    # ===== Thin wrapper around BeautifulSoup's CSS selection
    @staticmethod
    def _select_all(scope: Tag | BeautifulSoup, locator: BS4Locator) -> list[Tag]:
        for selector in locator.selectors:
            elements = scope.select(selector)
            if elements:
                return elements

        return []

    @staticmethod
    def _select_one(
        scope: Tag | BeautifulSoup,
        locator: BS4Locator,
    ) -> Tag | None:
        for selector in locator.selectors:
            element = scope.select_one(selector)
            if element is not None:
                return element

        return None

    # ===== Generic record parsing helpers
    def parse_records(
        self,
        html: str,
        schema: BS4RecordSchema,
        *,
        context: dict[str, Any] | None = None,
    ) -> list[Any]:
        soup = self.soup(html)
        records: list[Any] = []

        for container in self._select_all(soup, schema.record_container):
            values = dict(context or {})
            for field_name in schema.skip_if_missing:
                if field_name in values:
                    continue
                field = schema.fields.get(field_name)
                if field is not None:
                    values[field_name] = self.extract_field(container, field)

            if self._missing_skip_field(values, schema.skip_if_missing):
                continue

            for field_name, field in schema.fields.items():
                if field_name in values:
                    continue
                values[field_name] = self.extract_field(container, field)

            records.append(schema.model(**values))

        return records

    def extract_field(
        self,
        scope: Tag,
        field: BS4TextField,
    ) -> str | None:
        element = self._select_one(scope, field.locator)
        if element is None:
            return field.default

        text = self._extract_text(element)
        if text is None:
            return field.default
        if field.regex_pattern:
            matches = re.findall(field.regex_pattern, text)
            return matches[0] if matches else field.default
        if field.remove_prefix and text is not None:
            text = text.replace(field.remove_prefix, "").strip()
        if field.remove_suffix and text is not None:
            text = text.removesuffix(field.remove_suffix).strip()

        return text or field.default

    def _extract_text(self, element: PageElement) -> str | None:
        if not hasattr(element, "get_text"):
            return None

        text = element.get_text(
            self.config.TEXT_SEPARATOR,
            strip=self.config.STRIP_TEXT,
        )
        return text or None

    @staticmethod
    def _missing_skip_field(
        values: dict[str, Any],
        skip_if_missing: tuple[str, ...],
    ) -> bool:
        return any(not values.get(field_name) for field_name in skip_if_missing)
