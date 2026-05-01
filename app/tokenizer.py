from __future__ import annotations

import re
from typing import List

TOKEN_PATTERN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")


def tokenize(sentence: str) -> List[str]:
    """Convert a sentence into lowercase word tokens.

    The tokenizer is intentionally simple because the project only targets a
    narrow, controlled subset of English.
    """

    if not sentence or not sentence.strip():
        raise ValueError("Input sentence is empty.")

    tokens = TOKEN_PATTERN.findall(sentence.lower())
    if not tokens:
        raise ValueError("Input sentence does not contain recognizable word tokens.")

    return tokens
