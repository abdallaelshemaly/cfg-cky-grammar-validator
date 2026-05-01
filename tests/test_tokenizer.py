import pytest

from app.tokenizer import tokenize


def test_tokenizer_normalizes_case_and_punctuation() -> None:
    assert tokenize("The red cat sleeps.") == ["the", "red", "cat", "sleeps"]


def test_tokenizer_handles_proper_names() -> None:
    assert tokenize("Mary likes John!") == ["mary", "likes", "john"]


def test_tokenizer_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        tokenize("   ")
