import logging
import re
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =============== NAMED ANSI COLOR ===============
class NamedANSIColor(BaseModel):
    """ANSI color code with a readable name.

    Logger palettes use this to keep the raw terminal escape code together
    with a name that is easier to show in previews and debugging output.

    Args:
        ansi: Terminal color escape code, or the reset escape code.
        color_name: Short readable name for the color.

    Raises:
        ValueError: If ``ansi`` is not a supported color or reset code.
        ValueError: If ``color_name`` is empty.

    Examples:
        >>> color = NamedANSIColor(ansi="\\x1b[32;20m", color_name="green")
        >>> assert str(color) == "\\x1b[32;20m"
    """

    _ANSI_COLOR_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^\x1b\[(?:0|(?:3[0-7]|9[0-7])(?:;(?:1|20))?|38;2;(?:25[0-5]|2[0-4]\d|1?\d?\d);"
        r"(?:25[0-5]|2[0-4]\d|1?\d?\d);(?:25[0-5]|2[0-4]\d|1?\d?\d))m$"
    )

    ansi: str = Field(description="ANSI foreground color or reset escape sequence.")
    color_name: str = Field(min_length=1, description="Human-readable color name.")

    model_config = ConfigDict(frozen=True)

    @field_validator("ansi")
    @classmethod
    def validate_ansi(cls, value: str) -> str:
        if not cls._ANSI_COLOR_PATTERN.match(value):
            raise ValueError(
                f"'{value}' is not a valid ANSI foreground color or reset sequence. "
                "Expected formats include '\\x1b[<30-37>m', '\\x1b[<90-97>m', "
                "'\\x1b[<30-37>;1m', '\\x1b[<30-37>;20m', "
                "'\\x1b[38;2;<0-255>;<0-255>;<0-255>m', or '\\x1b[0m'."
            )

        return value

    def __str__(self) -> str:
        return self.ansi


# =============== LOGGER PALETTE ===============
class LoggerPalette(BaseModel):
    """Color choices for each logger level.

    Logger formatters use this model to look up the terminal color for a
    record level such as ``debug`` or ``error``.

    Args:
        debug: Color used for debug messages.
        info: Color used for info messages.
        ...

    Examples:
        >>> palette = LoggerPalette(
        ...     debug=NamedANSIColor(ansi="\\x1b[32;20m", color_name="green"),
        ...     info=NamedANSIColor(ansi="\\x1b[34;20m", color_name="blue"),
        ...     warning=NamedANSIColor(ansi="\\x1b[33;20m", color_name="yellow"),
        ...     error=NamedANSIColor(ansi="\\x1b[31;20m", color_name="red"),
        ...     critical=NamedANSIColor(ansi="\\x1b[31;1m", color_name="bold red"),
        ... )
        >>> assert palette.error.color_name == "red"
    """

    debug: NamedANSIColor
    info: NamedANSIColor
    warning: NamedANSIColor
    error: NamedANSIColor
    critical: NamedANSIColor
    reset: NamedANSIColor = NamedANSIColor(ansi="\x1b[0m", color_name="reset")

    model_config = ConfigDict(frozen=True)

    def list_colors(self) -> None:
        print(f"{'Name':<12} {'Color':<12} {'Raw Value':<20} Preview")
        print("-" * 60)
        for field_name in self.model_fields:
            if field_name == "reset":
                continue

            color = getattr(self, field_name)
            preview = f"{color.ansi}{chr(0x2588) * 4}{self.reset.ansi}"
            print(
                f"{field_name.upper():<12} {color.color_name:<12} {repr(color.ansi):<20} {preview}"
            )
