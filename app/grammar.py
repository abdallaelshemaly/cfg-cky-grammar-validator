from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Tuple


@dataclass
class CFGGrammar:
    start_symbol: str
    lexical_rules: Mapping[str, frozenset[str]]
    unary_rules: Mapping[str, frozenset[str]]
    binary_rules: Mapping[Tuple[str, str], frozenset[str]]

    @classmethod
    def level2(cls) -> "CFGGrammar":
        lexical_by_category = {
            "Det": {"a", "an", "my", "that", "the", "this", "your"},
            "Noun": {
                "apple",
                "book",
                "car",
                "cat",
                "child",
                "dog",
                "room",
                "student",
                "teacher",
            },
            "Verb": {
                "finds",
                "helps",
                "likes",
                "reads",
                "runs",
                "sees",
                "sleeps",
                "smiles",
            },
            "Adj": {"big", "happy", "red", "small", "tall", "young"},
            "Pronoun": {"he", "i", "it", "she", "they", "we", "you"},
            "ProperNoun": {"ali", "john", "mary", "noor", "omar", "sara"},
        }

        lexical_rules: Dict[str, set[str]] = {}
        for category, words in lexical_by_category.items():
            for word in words:
                lexical_rules.setdefault(word, set()).add(category)

        unary_rules = _freeze_rule_map(
            {
                "Pronoun": {"NP"},
                "ProperNoun": {"NP"},
                "Noun": {"Nominal"},
                "Verb": {"VP"},
            }
        )

        binary_rules = _freeze_binary_rule_map(
            {
                ("NP", "VP"): {"S"},
                ("Det", "Nominal"): {"NP"},
                ("Det", "AdjNominal"): {"NP"},
                ("Adj", "Noun"): {"AdjNominal"},
                ("Verb", "NP"): {"VP"},
            }
        )

        return cls(
            start_symbol="S",
            lexical_rules=_freeze_rule_map(lexical_rules),
            unary_rules=unary_rules,
            binary_rules=binary_rules,
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
            "NP -> Det Adj N",
            "NP -> Pronoun",
            "NP -> ProperNoun",
            "VP -> Verb",
            "VP -> Verb NP",
        ]


def _freeze_rule_map(rule_map: Mapping[str, Iterable[str]]) -> Dict[str, frozenset[str]]:
    return {key: frozenset(values) for key, values in rule_map.items()}


def _freeze_binary_rule_map(
    rule_map: Mapping[Tuple[str, str], Iterable[str]]
) -> Dict[Tuple[str, str], frozenset[str]]:
    return {key: frozenset(values) for key, values in rule_map.items()}


_DEFAULT_GRAMMAR = CFGGrammar.level2()


def get_default_grammar() -> CFGGrammar:
    return _DEFAULT_GRAMMAR
