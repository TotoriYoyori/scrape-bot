import os
import pytest
import re
import pandas as pd
from extract.scraper import AudibleController


@pytest.fixture
def audible_link():
    """Provide the base link for the Audible website."""
    return 'https://www.audible.in/search?'


@pytest.fixture
def output_csv_path():
    """ Provide the path to the CSV file scraped from the Audible website."""
    return 'default_audible.csv'

def test_audible_controller(audible_link: str) -> None:
    mock_controller = AudibleController(audible_link)

    # ----- Test get_all_categories()
    audible_categories = mock_controller.get_all_categories()
    assert isinstance(audible_categories, list)
    assert audible_categories != []

    valid_pattern = re.compile(r"^[A-Za-z\s&',+\-]+$")
    for category in mock_controller.get_all_categories():
        assert valid_pattern.match(category.text), f"Invalid category: {category}"


def output_exists(output_csv_path: str) -> None:
    assert
