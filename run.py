from __future__ import annotations

from app.cky_parser import CKYParser
from app.explainer import explain_result
from app.grammar import CNF_GRAMMAR
from app.parse_tree import build_tree, format_tree
from app.tokenizer import tokenize


def main() -> None:
    sentence = input("Enter a sentence: ")

    tokens = tokenize(sentence)
    parser = CKYParser(CNF_GRAMMAR)
    result = parser.parse_tokens(tokens)
    explanation = explain_result(result, CNF_GRAMMAR)

    print("VALID" if result["valid"] else "INVALID")
    print(f"tokens: {tokens}")
    print(f"explanation: {explanation}")

    if result["valid"]:
        tree = build_tree(result["back"], 0, len(tokens) - 1, "S")
        print("parse tree:")
        print(format_tree(tree))


if __name__ == "__main__":
    main()
