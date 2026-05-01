from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .cky_parser import CKYParser
from .grammar import CNF_GRAMMAR


@dataclass(frozen=True)
class ValidationExplanation:
    is_valid: bool
    message: str
    tokens: list[str]
    unknown_tokens: list[str]


def explain_result(result: dict, grammar: dict) -> str:
    """Return a short explanation for a CKY parser result."""

    tokens = result.get("tokens", [])
    unknown_words = result.get("unknown_words", [])

    if not tokens:
        return "Invalid input: no words were provided."

    if unknown_words:
        words = ", ".join(unknown_words)
        return f"Invalid sentence: unknown word(s): {words}."

    if result.get("valid", False):
        return "Valid Level 2 sentence: it matches the supported CFG."

    if len(tokens) == 1:
        return "Invalid sentence: a single word is incomplete for this Level 2 CFG."

    first_categories = _categories(tokens[0], grammar)
    second_categories = _categories(tokens[1], grammar)
    last_categories = _categories(tokens[-1], grammar)

    if _has_category(first_categories, "V"):
        return "Invalid sentence: Level 2 declarative sentences cannot start with a verb."

    if _has_category(first_categories, "N") and _has_category(second_categories, "Det"):
        return "Invalid sentence: noun followed by determiner is the wrong noun phrase order."

    if _has_category(first_categories, "Det") and _has_category(second_categories, "V"):
        return "Invalid sentence: a determiner followed by a verb does not form a valid noun phrase."

    if _has_category(first_categories, "Adj"):
        return "Invalid sentence: an adjective cannot start a supported Level 2 sentence."

    if _has_category(last_categories, "Det"):
        return "Invalid sentence: a determiner cannot appear at the end of this CFG pattern."

    return "Invalid sentence: all words are known, but the order does not match the Level 2 CFG."


def explain_sentence(sentence: str, grammar: dict[str, Any] | None = None) -> str:
    grammar = grammar or CNF_GRAMMAR
    parser = CKYParser(grammar)
    return explain_result(parser.parse(sentence), grammar)


def _categories(token: str, grammar: dict) -> set[str]:
    return set(grammar["lexical"].get(token, set()))


def _has_category(categories: set[str], category: str) -> bool:
    return category in categories
