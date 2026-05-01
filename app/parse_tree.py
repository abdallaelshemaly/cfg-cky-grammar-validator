from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .cky_parser import BinaryDerivation, LeafDerivation, ParseResult, UnaryDerivation


@dataclass(frozen=True)
class ParseTree:
    label: str
    children: Tuple["ParseTree", ...] = field(default_factory=tuple)
    token: str | None = None

    def to_bracketed(self) -> str:
        if self.token is not None:
            return f"({self.label} {self.token})"

        children = " ".join(child.to_bracketed() for child in self.children)
        return f"({self.label} {children})"


def build_parse_tree(result: ParseResult, symbol: str | None = None) -> ParseTree:
    if not result.tokens:
        raise ValueError("Cannot build a parse tree for an empty token sequence.")

    symbol = symbol or result.start_symbol
    span = (0, len(result.tokens), symbol)
    if span not in result.backpointers:
        raise ValueError(f"No parse tree is available for symbol {symbol}.")

    return _build_subtree(result, 0, len(result.tokens), symbol)


def render_parse_tree(tree: ParseTree) -> str:
    return tree.to_bracketed()


def _build_subtree(result: ParseResult, start: int, end: int, symbol: str) -> ParseTree:
    derivation = result.backpointers[(start, end, symbol)]

    if isinstance(derivation, LeafDerivation):
        return ParseTree(label=symbol, token=derivation.token)

    if isinstance(derivation, UnaryDerivation):
        child = _build_subtree(result, start, end, derivation.child)
        return ParseTree(label=symbol, children=(child,))

    if isinstance(derivation, BinaryDerivation):
        left_child = _build_subtree(result, start, derivation.split, derivation.left)
        right_child = _build_subtree(result, derivation.split, end, derivation.right)
        return ParseTree(label=symbol, children=(left_child, right_child))

    raise TypeError(f"Unsupported derivation type: {type(derivation)!r}")
