from app.cky_parser import parse_sentence
from app.parse_tree import build_parse_tree, render_parse_tree


def test_parser_accepts_simple_declarative_sentence() -> None:
    result = parse_sentence("The cat sleeps.")
    assert result.is_valid


def test_parser_accepts_transitive_sentence() -> None:
    result = parse_sentence("John likes Mary.")
    assert result.is_valid

    tree = build_parse_tree(result)
    assert render_parse_tree(tree).startswith("(S ")


def test_parser_rejects_wrong_word_order() -> None:
    result = parse_sentence("Cat the sleeps.")
    assert not result.is_valid


def test_parser_rejects_out_of_scope_structure() -> None:
    result = parse_sentence("Under the tree sleeps.")
    assert not result.is_valid
