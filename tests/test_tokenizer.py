from __future__ import annotations


def test_tokenizer_lowercases_and_removes_punctuation(tokenizer):
    assert list(tokenizer("The cat runs.")) == ["the", "cat", "runs"]


def test_tokenizer_normalizes_extra_spaces(tokenizer):
    assert list(tokenizer("  The   cat   runs   ")) == ["the", "cat", "runs"]
