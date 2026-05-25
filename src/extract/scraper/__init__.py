from __future__ import annotations

import importlib
import sys

from src.scraper import *  # noqa: F403
from src.scraper import __all__

_ALIASES = [
    "bot",
    "logger",
    "logger.module",
    "logger.palette",
    "logger.settings",
    "bs4",
    "bs4.module",
    "bs4.settings",
    "selenium",
    "selenium.module",
    "selenium.settings",
    "timing",
    "timing.module",
    "timing.settings",
    "routines",
    "routines.audible",
    "routines.schema",
    "routines.settings",
]

for _alias in _ALIASES:
    sys.modules[f"{__name__}.{_alias}"] = importlib.import_module(
        f"src.scraper.{_alias}"
    )

del importlib, sys, _ALIASES, _alias
