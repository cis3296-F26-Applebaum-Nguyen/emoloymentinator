
from src.bot.search_handler import process_search_request


def test_valid_search():
    result = process_search_request("Python developer")
    assert result == "Received your search request: Python developer"


def test_empty_search():
    result = process_search_request("")
    assert result == "Please provide a job search query."


def test_whitespace_search():
    result = process_search_request("   ")
    assert result == "Please provide a job search query."
