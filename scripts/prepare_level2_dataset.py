from __future__ import annotations

import ast
import csv
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
MANUAL_DATASET_PATH = DATA_DIR / "manual_level2_dataset.csv"
JFLEG_RAW_PATH = DATA_DIR / "jfleg_raw.csv"
FINAL_DATASET_PATH = DATA_DIR / "final_dataset.csv"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.grammar import ALLOWED_WORDS


BANNED_WORDS = {
    "because",
    "while",
    "although",
    "and",
    "but",
    "if",
    "when",
    "before",
    "after",
}

SENTENCE_COLUMNS = ("sentence", "text", "original", "input")
CORRECTION_COLUMNS = ("corrections", "correction", "references")
LABEL_COLUMNS = ("label",)


def normalize_text(text: object) -> str:
    value = "" if text is None else str(text).lower()
    value = re.sub(r"[^\w\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def tokenize(text: str) -> list[str]:
    return text.split() if text else []


def get_first_value(row: dict[str, str], columns: Iterable[str]) -> str:
    for column in columns:
        value = row.get(column)
        if value is not None and str(value).strip():
            return str(value)
    return ""


def parse_corrections(value: object) -> list[str]:
    if value is None:
        return []

    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item).strip()]

    text = str(value).strip()
    if not text:
        return []

    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return [text]

    if isinstance(parsed, (list, tuple)):
        return [str(item) for item in parsed if str(item).strip()]

    if parsed is None:
        return []

    return [str(parsed)]


def build_label(original: str, correction: str) -> str:
    return "VALID" if original == correction else "INVALID"


def normalize_label(value: object) -> str:
    label = normalize_text(value).upper()
    if label == "VALID":
        return "VALID"
    if label == "INVALID":
        return "INVALID"
    raise ValueError(f"Unsupported label value: {value!r}")


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def prepare_manual_rows(path: Path) -> list[dict[str, str]]:
    prepared_rows: list[dict[str, str]] = []

    for row in load_csv_rows(path):
        sentence = normalize_text(get_first_value(row, SENTENCE_COLUMNS))
        if not sentence:
            continue

        raw_label = get_first_value(row, LABEL_COLUMNS)
        if raw_label:
            label = normalize_label(raw_label)
        else:
            corrections = parse_corrections(get_first_value(row, CORRECTION_COLUMNS))
            if not corrections:
                raise ValueError(
                    "Manual dataset row is missing both a label and corrections."
                )
            first_correction = normalize_text(corrections[0])
            label = build_label(sentence, first_correction)

        prepared_rows.append({"sentence": sentence, "label": label})

    return prepared_rows


def prepare_jfleg_rows(path: Path, allowed_words: set[str]) -> list[dict[str, str]]:
    prepared_rows: list[dict[str, str]] = []

    for row in load_csv_rows(path):
        original = normalize_text(get_first_value(row, SENTENCE_COLUMNS))
        if not original:
            continue

        tokens = tokenize(original)
        if not 2 <= len(tokens) <= 6:
            continue
        if any(token in BANNED_WORDS for token in tokens):
            continue
        if any(token not in allowed_words for token in tokens):
            continue

        corrections = parse_corrections(get_first_value(row, CORRECTION_COLUMNS))
        if not corrections:
            continue

        first_correction = normalize_text(corrections[0])
        label = build_label(original, first_correction)
        prepared_rows.append({"sentence": original, "label": label})

    return prepared_rows


def deduplicate_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    seen_sentences: set[str] = set()
    unique_rows: list[dict[str, str]] = []

    for row in rows:
        sentence = row["sentence"]
        if sentence in seen_sentences:
            continue
        seen_sentences.add(sentence)
        unique_rows.append(row)

    return unique_rows


def write_final_dataset(path: Path, rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sentence", "label"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    allowed_words = {
        normalized
        for word in ALLOWED_WORDS
        for normalized in [normalize_text(word)]
        if normalized
    }

    manual_rows = prepare_manual_rows(MANUAL_DATASET_PATH)
    jfleg_rows = prepare_jfleg_rows(JFLEG_RAW_PATH, allowed_words)
    final_rows = deduplicate_rows([*manual_rows, *jfleg_rows])

    write_final_dataset(FINAL_DATASET_PATH, final_rows)

    label_counts = Counter(row["label"] for row in final_rows)
    print(f"Total rows: {len(final_rows)}")
    print(f"VALID: {label_counts.get('VALID', 0)}")
    print(f"INVALID: {label_counts.get('INVALID', 0)}")


if __name__ == "__main__":
    main()
