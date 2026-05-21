import os
import pandas as pd
import logging

from settings import settings
from .scraper import AudibleScraper

# ----- Logging Setups
logging.basicConfig(level=logging.INFO)


# ----- Public API
def extract_audible_csv(file_path: str) -> pd.DataFrame:
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        raise FileNotFoundError


def scrape_site(category_name: str, output_path: str) -> None:
    with AudibleScraper(
        base_url=settings.AUDIBLE_BASE_URL,
        output_csv=output_path,
    ) as scraper:
        scraper.scrape(category_name)
