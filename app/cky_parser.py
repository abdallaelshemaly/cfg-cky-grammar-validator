from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Union

from .grammar import CFGGrammar, get_default_grammar
from .tokenizer import tokenize


@dataclass(frozen=True)
class LeafDerivation:
    token: str


@dataclass(frozen=True)
class UnaryDerivation:
    child: str


@dataclass(frozen=True)
class BinaryDerivation:
    split: int
    left: str
    right: str


BackPointer = Union[LeafDerivation, UnaryDerivation, BinaryDerivation]


@dataclass
class ParseResult:
    tokens: List[str]
    chart: List[List[set[str]]]
    backpointers: Dict[Tuple[int, int, str], BackPointer]
    start_symbol: str

    @property
    def is_valid(self) -> bool:
        if not self.tokens:
            return False
        return self.start_symbol in self.chart[0][len(self.tokens)]


def parse_sentence(sentence: str, grammar: CFGGrammar | None = None) -> ParseResult:
    return parse_tokens(tokenize(sentence), grammar=grammar)


def parse_tokens(tokens: List[str], grammar: CFGGrammar | None = None) -> ParseResult:
    grammar = grammar or get_default_grammar()
    if not tokens:
        return ParseResult(tokens=[], chart=[], backpointers={}, start_symbol=grammar.start_symbol)

    length = len(tokens)
    chart = [[set() for _ in range(length + 1)] for _ in range(length)]
    backpointers: Dict[Tuple[int, int, str], BackPointer] = {}

    for index, token in enumerate(tokens):
        for category in grammar.lexical_categories(token):
            chart[index][index + 1].add(category)
            backpointers[(index, index + 1, category)] = LeafDerivation(token)
        _apply_unary_closure(chart, backpointers, index, index + 1, grammar)

    for span in range(2, length + 1):
        for start in range(0, length - span + 1):
            end = start + span
            for split in range(start + 1, end):
                left_symbols = chart[start][split]
                right_symbols = chart[split][end]
                if not left_symbols or not right_symbols:
                    continue

                for left_symbol in left_symbols:
                    for right_symbol in right_symbols:
                        for parent in grammar.binary_parents(left_symbol, right_symbol):
                            key = (start, end, parent)
                            if parent in chart[start][end]:
                                continue
                            chart[start][end].add(parent)
                            backpointers[key] = BinaryDerivation(
                                split=split,
                                left=left_symbol,
                                right=right_symbol,
                            )

            if chart[start][end]:
                _apply_unary_closure(chart, backpointers, start, end, grammar)

    return ParseResult(
        tokens=tokens,
        chart=chart,
        backpointers=backpointers,
        start_symbol=grammar.start_symbol,
    )


def _apply_unary_closure(
    chart: List[List[set[str]]],
    backpointers: Dict[Tuple[int, int, str], BackPointer],
    start: int,
    end: int,
    grammar: CFGGrammar,
) -> None:
    agenda = list(chart[start][end])

    while agenda:
        child = agenda.pop()
        for parent in grammar.unary_parents(child):
            key = (start, end, parent)
            if parent in chart[start][end]:
                continue
            chart[start][end].add(parent)
            backpointers[key] = UnaryDerivation(child=child)
            agenda.append(parent)
