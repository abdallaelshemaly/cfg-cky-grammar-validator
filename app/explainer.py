from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .cky_parser import ParseResult, parse_sentence
from .grammar import CFGGrammar, get_default_grammar
from .tokenizer import tokenize


@dataclass(frozen=True)
class ValidationExplanation:
    is_valid: bool
    message: str
    tokens: List[str]
    unknown_tokens: List[str]


def explain_sentence(
    sentence: str,
    grammar: CFGGrammar | None = None,
) -> ValidationExplanation:
    grammar = grammar or get_default_grammar()
    tokens = tokenize(sentence)
    result = parse_sentence(sentence, grammar=grammar)
    return explain_result(tokens, result, grammar=grammar)


def explain_result(
    tokens: List[str],
    result: ParseResult,
    grammar: CFGGrammar | None = None,
) -> ValidationExplanation:
    grammar = grammar or get_default_grammar()
    unknown_tokens = [token for token in tokens if not grammar.knows_token(token)]

    if result.is_valid:
        message = (
            "Valid Level 2 sentence: it matches the supported declarative pattern "
            "S -> NP VP within the scoped CFG."
        )
        return ValidationExplanation(
            is_valid=True,
            message=message,
            tokens=tokens,
            unknown_tokens=[],
        )

    if unknown_tokens:
        message = (
            "Invalid sentence: the limited lexicon does not recognize "
            + ", ".join(sorted(set(unknown_tokens)))
            + "."
        )
        return ValidationExplanation(
            is_valid=False,
            message=message,
            tokens=tokens,
            unknown_tokens=unknown_tokens,
        )

    has_np_prefix = any("NP" in result.chart[0][end] for end in range(1, len(tokens) + 1))
    has_vp_suffix = any("VP" in result.chart[start][len(tokens)] for start in range(len(tokens)))

    if not has_np_prefix:
        message = "Invalid sentence: the opening words do not form a supported noun phrase."
    elif not has_vp_suffix:
        message = "Invalid sentence: the sentence does not contain a supported verb phrase."
    else:
        message = (
            "Invalid sentence: all words are known, but the sequence does not match "
            "the supported Level 2 declarative patterns."
        )

    return ValidationExplanation(
        is_valid=False,
        message=message,
        tokens=tokens,
        unknown_tokens=[],
    )
