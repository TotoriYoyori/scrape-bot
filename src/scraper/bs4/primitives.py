from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


# =============== BEAUTIFUL SOUP LOCATOR PRIMITIVE ===============
class BS4Locator(BaseModel):
    """CSS selector rule for finding an HTML element.

    A locator keeps element search separate from field extraction rules. It
    lets parser code try one main CSS selector and optional backup selectors in
    order until one matches an element.

    Examples:
        >>> locator = BS4Locator(
        ...     selector=".title",
        ...     fallback_selectors=("h1", "[data-testid='title']"),
        ... )
        >>> assert locator.selectors == (".title", "h1", "[data-testid='title']")
    """

    selector: Annotated[str, Field(min_length=1)]
    fallback_selectors: tuple[Annotated[str, Field(min_length=1)], ...] = ()

    model_config = ConfigDict(frozen=True)

    @property
    def selectors(self) -> tuple[str, ...]:
        return self.selector, *self.fallback_selectors


# =============== BEAUTIFUL SOUP FIELD PRIMITIVES ===============
class BS4TextField(BaseModel):
    """Text extraction rule for one output field.

    Locate a text field and normalize its values. If regex_pattern is set,
    extract the matched value from the text.

    Examples:
        >>> field = BS4TextField(
        ...     locator=BS4Locator(selector=".author"),
        ...     remove_prefix="By ",
        ...     remove_suffix=".",
        ...     default="Unknown",
        ... )
        >>> assert field.locator.selector == ".author"

        >>> regex_field = BS4TextField(
        ...     locator=BS4Locator(selector=".price"),
        ...     regex_pattern=r"(\\d+\\.\\d+)",
        ... )
        >>> assert regex_field.regex_pattern == r"(\\d+\\.\\d+)"
    """

    locator: BS4Locator
    regex_pattern: Annotated[str, Field(min_length=1)] | None = None
    remove_prefix: str | None = None
    remove_suffix: str | None = None
    default: str | None = None

    model_config = ConfigDict(frozen=True)


# =============== BEAUTIFUL SOUP RECORD SCHEMA ===============
class BS4RecordSchema(BaseModel):
    """Rule for reading repeated records from HTML.

    Use this when a page has repeated blocks, such as book cards or search
    results. Each matched block is read into one model instance.

    Examples:
        >>> class Book(BaseModel):
        ...     title: str | None
        >>> schema = BS4RecordSchema(
        ...     record_container=BS4Locator(selector=".book"),
        ...     model=Book,
        ...     skip_if_missing=("title",),
        ...     fields={
        ...         "title": BS4TextField(locator=BS4Locator(selector="h3")),
        ...     },
        ... )
        >>> assert schema.record_container.selector == ".book"
        >>> assert schema.model is Book
        >>> assert tuple(schema.fields) == ("title", )
    """

    record_container: BS4Locator
    model: type[BaseModel]
    skip_if_missing: tuple[str, ...] = ()
    fields: dict[str, BS4TextField]

    model_config = ConfigDict(frozen=True)

    @field_validator("skip_if_missing")
    @classmethod
    def validate_skip_fields(
        cls,
        skip_if_missing: tuple[str, ...],
        info: ValidationInfo,
    ) -> tuple[str, ...]:
        model = info.data["model"]
        model_fields = set(model.model_fields)
        unknown_skip_fields = sorted(set(skip_if_missing) - model_fields)
        if unknown_skip_fields:
            raise ValueError(
                "BS4RecordSchema skip fields must exist on the model"
                f" ({unknown_skip_fields})"
            )

        return skip_if_missing

    @field_validator("fields")
    @classmethod
    def validate_fields(
        cls,
        fields: dict[str, BS4TextField],
        info: ValidationInfo,
    ) -> dict[str, BS4TextField]:
        model = info.data["model"]
        model_fields = set(model.model_fields)
        unknown_fields = sorted(set(fields) - model_fields)
        if unknown_fields:
            raise ValueError(
                "BS4RecordSchema fields must exist on the model"
                f" ({unknown_fields})"
            )

        return fields
