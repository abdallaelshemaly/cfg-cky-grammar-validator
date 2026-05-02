from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import pandas as pd


def _load_callable(module_names: list[str], function_names: list[str]):
    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue

        for function_name in function_names:
            candidate = getattr(module, function_name, None)
            if callable(candidate):
                return candidate

    raise ImportError(
        f"Could not find any of {function_names} in modules: {', '.join(module_names)}"
    )


def _load_tokenizer():
    return _load_callable(
        ["app.tokenizer"],
        ["tokenize", "tokenize_sentence"],
    )


def _load_parser():
    return _load_callable(
        ["app.cky_parser", "app.parser", "app.cky"],
        ["cky_parse", "parse", "parse_sentence"],
    )


def _load_grammar_argument():
    try:
        grammar_module = importlib.import_module("app.grammar")
    except ImportError:
        return None

    for name in ("GRAMMAR", "CFG", "RULES", "PARSER_GRAMMAR"):
        if hasattr(grammar_module, name):
            return getattr(grammar_module, name)

    return None


def _run_parser(parser, sentence: str, tokens: list[str]):
    grammar = _load_grammar_argument()
    attempts = []

    if grammar is not None:
        attempts.extend(
            [
                (tokens, grammar),
                (sentence, grammar),
            ]
        )

    attempts.extend(
        [
            (tokens,),
            (sentence,),
        ]
    )

    for args in attempts:
        try:
            return parser(*args)
        except TypeError:
            continue

    signature = inspect.signature(parser)
    raise TypeError(f"Unsupported parser signature for evaluator: {signature}")


def evaluate_dataset(csv_path: str) -> dict:
    dataframe = pd.read_csv(csv_path)
    tokenizer = _load_tokenizer()
    parser = _load_parser()

    result_rows = []

    for _, row in dataframe.iterrows():
        sentence = str(row["sentence"]).strip()
        expected_label = str(row["label"]).strip().upper()
        tokens = tokenizer(sentence)
        result = _run_parser(parser, sentence, tokens)

        is_valid = isinstance(result, dict) and result.get("valid") is True
        predicted_label = "VALID" if is_valid else "INVALID"
        is_correct = predicted_label == expected_label

        result_rows.append(
            {
                "sentence": sentence,
                "expected_label": expected_label,
                "predicted_label": predicted_label,
                "correct": is_correct,
            }
        )

    results_df = pd.DataFrame(result_rows)
    total = len(results_df)
    correct = int(results_df["correct"].sum()) if total else 0
    accuracy = (correct / total) if total else 0.0

    return {
        "accuracy": accuracy,
        "total": total,
        "correct": correct,
        "results": results_df,
    }
