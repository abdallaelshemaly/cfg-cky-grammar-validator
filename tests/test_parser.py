from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "sentence",
    [
        "the cat runs",
        "a dog eats fish",
        "the big dog runs",
        "he runs",
        "john sees mary",
    ],
)
def test_parser_accepts_valid_level2_sentences(parse_sentence, sentence):
    analysis = parse_sentence(sentence)
    assert analysis["valid"] is True


@pytest.mark.parametrize(
    "sentence",
    [
        "cat the runs",
        "the eats cat",
        "runs the cat",
        "the cat",
        "the elephant runs",
    ],
)
def test_parser_rejects_invalid_level2_sentences(parse_sentence, sentence):
    analysis = parse_sentence(sentence)
    assert analysis["valid"] is False
