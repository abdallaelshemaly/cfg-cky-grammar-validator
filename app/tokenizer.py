from __future__ import annotations

import re
from typing import List

PUNCTUATION_PATTERN = re.compile(r"[^a-z\s]")
SPACE_PATTERN = re.compile(r"\s+")


def tokenize(sentence: str) -> List[str]:
    """Lowercase, clean punctuation, normalize spaces, and split into tokens."""

    normalized = sentence.lower().strip()
    normalized = PUNCTUATION_PATTERN.sub(" ", normalized)
    normalized = SPACE_PATTERN.sub(" ", normalized).strip()
    return normalized.split() if normalized else []
