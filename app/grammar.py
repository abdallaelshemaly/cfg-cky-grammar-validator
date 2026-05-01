from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple


CNF_GRAMMAR = {
    "binary": {
        ("NP", "VP"): {"S"},
        ("Det", "N"): {"NP"},
        ("Det", "AdjN"): {"NP"},
        ("Adj", "N"): {"AdjN"},
        ("V", "NP"): {"VP"},
    },
    "unary": {
        "N": {"NP"},
        "Pron": {"NP"},
        "Name": {"NP"},
        "V": {"VP"},
    },
    "lexical": {
        "the": {"Det"},
        "a": {"Det"},
        "cat": {"N"},
        "dog": {"N"},
        "fish": {"N"},
        "boy": {"N"},
        "girl": {"N"},
        "apple": {"N"},
        "runs": {"V"},
        "eats": {"V"},
        "likes": {"V"},
        "sees": {"V"},
        "big": {"Adj"},
        "small": {"Adj"},
        "hungry": {"Adj"},
        "he": {"Pron"},
        "she": {"Pron"},
        "they": {"Pron"},
        "john": {"Name"},
        "mary": {"Name"},
    },
}

ALLOWED_WORDS = set(CNF_GRAMMAR["lexical"].keys())


@dataclass
class CFGGrammar:
    start_symbol: str
    lexical_rules: Mapping[str, frozenset[str]]
    unary_rules: Mapping[str, frozenset[str]]
    binary_rules: Mapping[Tuple[str, str], frozenset[str]]

    @classmethod
    def level2(cls) -> "CFGGrammar":
        return cls(
            start_symbol="S",
            lexical_rules=_freeze_rule_map(CNF_GRAMMAR["lexical"]),
            unary_rules=_freeze_rule_map(CNF_GRAMMAR["unary"]),
            binary_rules=_freeze_binary_rule_map(CNF_GRAMMAR["binary"]),
        )

    def lexical_categories(self, token: str) -> frozenset[str]:
        return self.lexical_rules.get(token, frozenset())

    def unary_parents(self, child: str) -> frozenset[str]:
        return self.unary_rules.get(child, frozenset())

    def binary_parents(self, left: str, right: str) -> frozenset[str]:
        return self.binary_rules.get((left, right), frozenset())

    def knows_token(self, token: str) -> bool:
        return token in self.lexical_rules

    def supported_patterns(self) -> list[str]:
        return [
            "S -> NP VP",
            "NP -> Det N",
            "NP -> Det AdjN",
            "AdjN -> Adj N",
            "NP -> N",
            "NP -> Pron",
            "NP -> Name",
            "VP -> V",
            "VP -> V NP",
        ]


def _freeze_rule_map(rule_map: Mapping[str, set[str]]) -> dict[str, frozenset[str]]:
    return {key: frozenset(values) for key, values in rule_map.items()}


def _freeze_binary_rule_map(
    rule_map: Mapping[Tuple[str, str], set[str]]
) -> dict[Tuple[str, str], frozenset[str]]:
    return {key: frozenset(values) for key, values in rule_map.items()}


_DEFAULT_GRAMMAR = CFGGrammar.level2()


def get_default_grammar() -> CFGGrammar:
    return _DEFAULT_GRAMMAR
