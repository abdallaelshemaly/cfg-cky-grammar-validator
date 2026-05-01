from __future__ import annotations

from typing import Any

from .cky_parser import BinaryDerivation, LeafDerivation, ParseResult, UnaryDerivation

Tree = tuple[Any, ...]
ParseTree = Tree


def build_tree(back: list[list[dict[str, Any]]], i: int, j: int, symbol: str) -> Tree:
    """Build one parse tree from CKY backpointers.

    Spans use the inclusive CKY table indexes from CKYParser: i..j.
    """

    pointer = _get_pointer(back, i, j, symbol)
    if pointer is None:
        return (symbol,)

    if isinstance(pointer, LeafDerivation):
        return (symbol, pointer.token)

    if isinstance(pointer, UnaryDerivation):
        return (symbol, build_tree(back, i, j, pointer.child))

    if isinstance(pointer, BinaryDerivation):
        left_tree = build_tree(back, i, pointer.split, pointer.left)
        right_tree = build_tree(back, pointer.split + 1, j, pointer.right)
        return (symbol, left_tree, right_tree)

    if isinstance(pointer, dict):
        return _build_tree_from_dict_pointer(back, i, j, symbol, pointer)

    return (symbol,)


def format_tree(tree: Tree, indent: int = 0) -> str:
    """Format a tuple parse tree as readable bracketed text."""

    padding = " " * indent
    label = str(tree[0]) if tree else ""

    if len(tree) == 1:
        return f"{padding}({label})"

    if len(tree) == 2 and not isinstance(tree[1], tuple):
        return f"{padding}({label} {tree[1]})"

    children = [
        format_tree(child, indent + 2) if isinstance(child, tuple) else f"{' ' * (indent + 2)}{child}"
        for child in tree[1:]
    ]
    return f"{padding}({label}\n" + "\n".join(children) + f"\n{padding})"


def build_parse_tree(result: ParseResult, symbol: str | None = None) -> Tree:
    if not result.tokens:
        raise ValueError("Cannot build a parse tree for an empty token sequence.")

    symbol = symbol or result.start_symbol
    return build_tree(result.back, 0, len(result.tokens) - 1, symbol)


def render_parse_tree(tree: Tree) -> str:
    return format_tree(tree)


def _get_pointer(
    back: list[list[dict[str, Any]]],
    i: int,
    j: int,
    symbol: str,
) -> Any | None:
    if i < 0 or j < 0 or i >= len(back) or j >= len(back[i]):
        return None
    return back[i][j].get(symbol)


def _build_tree_from_dict_pointer(
    back: list[list[dict[str, Any]]],
    i: int,
    j: int,
    symbol: str,
    pointer: dict[str, Any],
) -> Tree:
    pointer_type = pointer.get("type")

    if pointer_type == "lexical":
        return (symbol, pointer.get("token", ""))

    if pointer_type == "unary":
        child = pointer.get("child")
        return (symbol, build_tree(back, i, j, child)) if child else (symbol,)

    if pointer_type == "binary":
        split = pointer.get("split")
        left = pointer.get("left")
        right = pointer.get("right")
        if split is None or not left or not right:
            return (symbol,)
        return (
            symbol,
            build_tree(back, i, split, left),
            build_tree(back, split + 1, j, right),
        )

    return (symbol,)
