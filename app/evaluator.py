from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .cky_parser import parse_tokens
from .explainer import explain_result
from .grammar import CFGGrammar, get_default_grammar
from .tokenizer import tokenize


@dataclass(frozen=True)
class EvaluationSummary:
    total: int
    correct: int
    accuracy: float


def evaluate_dataset(
    dataset_path: str | Path,
    grammar: CFGGrammar | None = None,
) -> pd.DataFrame:
    grammar = grammar or get_default_grammar()
    frame = pd.read_csv(dataset_path)

    required_columns = {"sentence", "label"}
    missing = required_columns.difference(frame.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Dataset is missing required columns: {missing_list}")

    records = []
    for row in frame.itertuples(index=False):
        sentence = str(row.sentence)
        gold_label = _normalize_label(row.label)

        try:
            tokens = tokenize(sentence)
            result = parse_tokens(tokens, grammar=grammar)
            explanation = explain_result(tokens, result, grammar=grammar)
            predicted_label = "VALID" if result.is_valid else "INVALID"
            parse_error = ""
        except ValueError as exc:
            tokens = []
            predicted_label = "INVALID"
            explanation = None
            parse_error = str(exc)

        records.append(
            {
                "sentence": sentence,
                "gold_label": gold_label,
                "predicted_label": predicted_label,
                "correct": predicted_label == gold_label,
                "tokens": tokens,
                "explanation": explanation.message if explanation else parse_error,
                "notes": getattr(row, "notes", ""),
            }
        )

    return pd.DataFrame.from_records(records)


def summarize_results(results: pd.DataFrame) -> EvaluationSummary:
    total = len(results)
    correct = int(results["correct"].sum()) if total else 0
    accuracy = (correct / total) if total else 0.0
    return EvaluationSummary(total=total, correct=correct, accuracy=accuracy)


def _normalize_label(label: object) -> str:
    normalized = str(label).strip().upper()
    if normalized in {"VALID", "INVALID"}:
        return normalized
    raise ValueError("Labels must be VALID or INVALID.")
