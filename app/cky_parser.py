from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Union

from .grammar import CNF_GRAMMAR
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
    table: List[List[set[str]]]
    back: List[List[dict[str, BackPointer]]]
    unknown_words: List[str]
    start_symbol: str = "S"

    @property
    def chart(self) -> List[List[set[str]]]:
        n = len(self.tokens)
        chart = [[set() for _ in range(n + 1)] for _ in range(n)]
        for start in range(n):
            for end in range(start, n):
                chart[start][end + 1] = self.table[start][end]
        return chart

    @property
    def backpointers(self) -> Dict[Tuple[int, int, str], BackPointer]:
        pointers: Dict[Tuple[int, int, str], BackPointer] = {}
        for start, row in enumerate(self.back):
            for end, cell in enumerate(row):
                for symbol, pointer in cell.items():
                    if isinstance(pointer, BinaryDerivation):
                        pointer = BinaryDerivation(
                            split=pointer.split + 1,
                            left=pointer.left,
                            right=pointer.right,
                        )
                    pointers[(start, end + 1, symbol)] = pointer
        return pointers

    @property
    def is_valid(self) -> bool:
        if not self.tokens:
            return False
        return self.start_symbol in self.table[0][len(self.tokens) - 1]


class CKYParser:
    def __init__(self, grammar: dict[str, Any]):
        self.binary_rules = grammar["binary"]
        self.lexical_rules = grammar["lexical"]
        self.unary_rules = grammar.get("unary", {})
        self.start_symbol = "S"

    def parse(self, sentence_or_tokens):
        if isinstance(sentence_or_tokens, str):
            tokens = tokenize(sentence_or_tokens)
        elif isinstance(sentence_or_tokens, list):
            tokens = sentence_or_tokens
        else:
            raise TypeError("parse() expects a sentence string or a list of tokens")

        return self.parse_tokens(tokens)

    def parse_tokens(self, tokens: List[str]) -> dict[str, Any]:
        n = len(tokens)
        table: List[List[set[str]]] = [[set() for _ in range(n)] for _ in range(n)]
        back: List[List[dict[str, BackPointer]]] = [[{} for _ in range(n)] for _ in range(n)]
        unknown_words = [token for token in tokens if token not in self.lexical_rules]

        if n == 0:
            return {
                "valid": False,
                "tokens": tokens,
                "table": table,
                "back": back,
                "unknown_words": unknown_words,
            }

        for index, token in enumerate(tokens):
            for category in self.lexical_rules.get(token, set()):
                table[index][index].add(category)
                back[index][index][category] = LeafDerivation(token=token)
            self._apply_unary_closure(table, back, index, index)

        for span_length in range(2, n + 1):
            for start in range(0, n - span_length + 1):
                end = start + span_length - 1
                for split in range(start, end):
                    for left_symbol in table[start][split]:
                        for right_symbol in table[split + 1][end]:
                            parents = self.binary_rules.get((left_symbol, right_symbol), set())
                            for parent in parents:
                                if parent in table[start][end]:
                                    continue
                                table[start][end].add(parent)
                                back[start][end][parent] = BinaryDerivation(
                                    split=split,
                                    left=left_symbol,
                                    right=right_symbol,
                                )

                if table[start][end]:
                    self._apply_unary_closure(table, back, start, end)

        return {
            "valid": self.start_symbol in table[0][n - 1],
            "tokens": tokens,
            "table": table,
            "back": back,
            "unknown_words": unknown_words,
        }

    def _apply_unary_closure(
        self,
        table: List[List[set[str]]],
        back: List[List[dict[str, BackPointer]]],
        start: int,
        end: int,
    ) -> None:
        agenda = list(table[start][end])

        while agenda:
            child = agenda.pop()
            for parent in self.unary_rules.get(child, set()):
                if parent in table[start][end]:
                    continue
                table[start][end].add(parent)
                back[start][end][parent] = UnaryDerivation(child=child)
                agenda.append(parent)


def parse_sentence(sentence: str, grammar: dict[str, Any] | None = None) -> ParseResult:
    parser = CKYParser(grammar or CNF_GRAMMAR)
    return _to_parse_result(parser.parse(sentence))


def parse_tokens(tokens: List[str], grammar: dict[str, Any] | None = None) -> ParseResult:
    parser = CKYParser(grammar or CNF_GRAMMAR)
    return _to_parse_result(parser.parse_tokens(tokens))


def _to_parse_result(parse_data: dict[str, Any]) -> ParseResult:
    return ParseResult(
        tokens=parse_data["tokens"],
        table=parse_data["table"],
        back=parse_data["back"],
        unknown_words=parse_data["unknown_words"],
    )
