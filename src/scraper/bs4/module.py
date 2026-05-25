from bs4 import BeautifulSoup

from src.scraper.primitives import ScrapeBotModule


class BeautifulSoupModule(ScrapeBotModule):
    """Generic BeautifulSoup helper module."""

    name = "parser"

    @staticmethod
    def soup(html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")


def create_html_parser() -> BeautifulSoupModule:
    return BeautifulSoupModule()
