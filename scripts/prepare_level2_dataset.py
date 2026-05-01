from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

BLOCKED_WORDS = {
    "after",
    "and",
    "before",
    "because",
    "but",
    "if",
    "in",
    "on",
    "or",
    "under",
    "when",
    "where",
    "with",
}
TOKEN_PATTERN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def looks_like_level2_candidate(tokens: list[str]) -> bool:
    if not 2 <= len(tokens) <= 6:
        return False
    if any(token in BLOCKED_WORDS for token in tokens):
        return False
    return True


def main() -> None:
    """Create candidate rows for manual Level 2 review.

    The output is not an automatically trusted benchmark. It is a shortlist of
    short sentences that may fit the project scope after human review.
    """

    project_root = Path(__file__).resolve().parents[1]
    input_path = project_root / "data" / "jfleg_validation_raw.csv"
    output_path = project_root / "data" / "jfleg_level2_candidates.csv"

    frame = pd.read_csv(input_path)
    candidates = []
    for row in frame.itertuples(index=False):
        tokens = tokenize(str(row.sentence))
        if not looks_like_level2_candidate(tokens):
            continue

        candidates.append(
            {
                "sentence": row.sentence,
                "tokens": " ".join(tokens),
                "candidate_label": "",
                "manual_review_required": True,
                "notes": "Review against supported NP/VP-only Level 2 grammar.",
            }
        )

    pd.DataFrame(candidates).to_csv(output_path, index=False)
    print(f"Saved {len(candidates)} candidate rows to {output_path}")


if __name__ == "__main__":
    main()
