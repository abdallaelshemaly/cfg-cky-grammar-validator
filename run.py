from __future__ import annotations

import argparse

from app.cky_parser import parse_sentence
from app.explainer import explain_result
from app.parse_tree import build_parse_tree, render_parse_tree
from app.tokenizer import tokenize


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a sentence with the scoped CFG + CKY parser."
    )
    parser.add_argument("sentence", help="Sentence to validate.")
    args = parser.parse_args()

    tokens = tokenize(args.sentence)
    result = parse_sentence(args.sentence)
    explanation = explain_result(tokens, result)

    verdict = "VALID" if result.is_valid else "INVALID"
    print(f"Sentence: {args.sentence}")
    print(f"Tokens: {tokens}")
    print(f"Verdict: {verdict}")
    print(f"Explanation: {explanation.message}")

    if result.is_valid:
        tree = build_parse_tree(result)
        print(f"Parse tree: {render_parse_tree(tree)}")


if __name__ == "__main__":
    main()
