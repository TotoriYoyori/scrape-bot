from src.scraper.logger.primitives import (
    LoggerPalette,
    NamedANSIColor,
)

# =============== USER-FRIENDLY MAKE YOUR OWN PRESET ===============
def _hex_to_ansi(hex_code: str) -> str:
    hex_code = hex_code.removeprefix("#")

    red = int(hex_code[0:2], 16)
    green = int(hex_code[2:4], 16)
    blue = int(hex_code[4:6], 16)

    return f"\x1b[38;2;{red};{green};{blue}m"


def create_logger_palette(
    *,
    debug: tuple[str, str],
    info: tuple[str, str],
    warning: tuple[str, str],
    error: tuple[str, str],
    critical: tuple[str, str],
) -> LoggerPalette:
    """Create a logger palette from hex colors and readable names.

    Args:
        debug: Hex color and readable name for debug messages.
        info: Hex color and readable name for info messages.
        warning: Hex color and readable name for warning messages.
        error: Hex color and readable name for error messages.
        critical: Hex color and readable name for critical messages.

    Examples:
        >>> palette = create_logger_palette(
        ...     debug=("#00ff9f", "mint"),
        ...     info=("#00b8ff", "cyan"),
        ...     warning=("#ffd700", "gold"),
        ...     error=("#ff003c", "red"),
        ...     critical=("#bd00ff", "violet"),
        ... )
        >>> assert palette.debug.ansi == "\\x1b[38;2;0;255;159m"
    """
    return LoggerPalette(
        debug=NamedANSIColor(ansi=_hex_to_ansi(debug[0]), color_name=debug[1]),
        info=NamedANSIColor(ansi=_hex_to_ansi(info[0]), color_name=info[1]),
        warning=NamedANSIColor(ansi=_hex_to_ansi(warning[0]), color_name=warning[1]),
        error=NamedANSIColor(ansi=_hex_to_ansi(error[0]), color_name=error[1]),
        critical=NamedANSIColor(ansi=_hex_to_ansi(critical[0]), color_name=critical[1]),
    )


# =============== PRESET LOGGER PALETTE ===============
BasicPalette = create_logger_palette(
    debug=("#8fd19e", "green"),
    info=("#8ab4f8", "blue"),
    warning=("#ffe082", "yellow"),
    error=("#f28b82", "red"),
    critical=("#c3a6ff", "purple"),
)


CyberpunkPalette = create_logger_palette(
    debug=("#9fffe0", "neon mint"),
    info=("#9be7ff", "electric cyan"),
    warning=("#a7b4ff", "ultraviolet"),
    error=("#d9a6ff", "neon violet"),
    critical=("#f0a6ff", "magenta"),
)


ViceCityPalette = create_logger_palette(
    debug=("#8bdfff", "pool blue"),
    info=("#8ab4f8", "deep blue"),
    warning=("#ffd3df", "pink"),
    error=("#ffb6c8", "salmon pink"),
    critical=("#d8b4e2", "lavender purple"),
)


# =============== LOGGER PALETTE REGISTRY ===============
LOGGER_PALETTE_REGISTRY: dict[str, LoggerPalette] = {
    "basic": BasicPalette,
    "vice": ViceCityPalette,
    "cyberpunk": CyberpunkPalette,
}


def preview_logger_palette(palette: str) -> None:
    """Print a color preview for a registered logger palette.

    Args:
        palette: Registered palette name, such as ``basic`` or ``cyberpunk``.

    Examples:
        >>> assert "basic" in LOGGER_PALETTE_REGISTRY
    """
    normalized = palette.strip().lower()
    if normalized not in LOGGER_PALETTE_REGISTRY:
        raise ValueError(
            f"'{palette}' is not a valid logger palette. "
            f"Must be one of: {sorted(LOGGER_PALETTE_REGISTRY)}"
        )

    LOGGER_PALETTE_REGISTRY[normalized].list_colors()
