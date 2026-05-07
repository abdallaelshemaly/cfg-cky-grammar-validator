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
    table = result.get("table", [])

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

    if _invalid_multi_adj_np(tokens, grammar):
        return (
            "Invalid sentence: noun phrases with more than one adjective before a noun "
            "are not supported in Level 2. Use only one adjective before a noun."
        )

    if _has_category(first_categories, "Adj"):
        return "Invalid sentence: an adjective cannot start a supported Level 2 sentence."

    if _has_category(last_categories, "Det"):
        return "Invalid sentence: a determiner cannot appear at the end of this CFG pattern."

    if _extra_words_after_valid_prefix(table):
        return (
            "Invalid sentence: a valid Level 2 sentence fragment appears at the beginning, "
            "but extra words remain after the VP."
        )

    if _looks_like_np_vp_split(table):
        return (
            "Invalid sentence: the sentence resembles NP + VP, but the two parts do not "
            "combine into a complete Level 2 sentence."
        )

    return "Invalid sentence: all words are known, but the order does not match the Level 2 CFG."


def explain_sentence(sentence: str, grammar: dict[str, Any] | None = None) -> str:
    grammar = grammar or CNF_GRAMMAR
    parser = CKYParser(grammar)
    return explain_result(parser.parse(sentence), grammar)


def _invalid_multi_adj_np(tokens: list[str], grammar: dict) -> bool:
    n = len(tokens)
    for i in range(n - 2):
        if _has_category(_categories(tokens[i], grammar), "Det"):
            adj_count = 0
            j = i + 1
            while j < n and _has_category(_categories(tokens[j], grammar), "Adj"):
                adj_count += 1
                j += 1
            if adj_count >= 2 and j < n and _has_category(_categories(tokens[j], grammar), "N"):
                return True
    return False


def _extra_words_after_valid_prefix(table: list[list[set[str]]]) -> bool:
    if not table:
        return False
    prefix_row = table[0]
    for end in range(len(prefix_row) - 1):
        if "S" in prefix_row[end]:
            return True
    return False


def _looks_like_np_vp_split(table: list[list[set[str]]]) -> bool:
    if not table:
        return False
    n = len(table)
    for split in range(n - 1):
        if "NP" in table[0][split] and "VP" in table[split + 1][n - 1]:
            return True
    return False


def _categories(token: str, grammar: dict) -> set[str]:
    return set(grammar["lexical"].get(token, set()))


def _has_category(categories: set[str], category: str) -> bool:
    return category in categories
