from src.scraper.selenium.module import SeleniumModule
from src.scraper.selenium.primitives import SeleniumLocator
from src.scraper.selenium.settings import SeleniumBrowserConfig

__all__ = [
    # ===== Selenium's browser module
    "SeleniumModule",
    "SeleniumBrowserConfig",
    # ===== Selenium's browser primitives
    "SeleniumLocator",
]
