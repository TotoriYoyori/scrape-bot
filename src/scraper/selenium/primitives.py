from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from selenium.webdriver.common.by import By, ByType

# =============== SELENIUM LOCATOR PRIMITIVE ===============
class SeleniumLocator(BaseModel):
    """Structured Selenium locator used by scraper browser helpers.

    Attributes:
        by_method: Selenium locator strategy, such as ``By.CSS_SELECTOR``.
        locator_name: Locator value used by the selected strategy.

    Example:
        >>> locator = SeleniumLocator(
        ...     by_method=By.CSS_SELECTOR,
        ...     locator_name="#notification-banner-message .bc-link",
        ... )
        >>> assert locator.as_tuple() == (
        ...     By.CSS_SELECTOR,
        ...     "#notification-banner-message .bc-link",
        ... )
    """

    by_method: ByType
    locator_name: Annotated[str, Field(min_length=1)]

    model_config = ConfigDict(frozen=True)

    def as_tuple(self) -> tuple[str, str]:
        return self.by_method, self.locator_name
