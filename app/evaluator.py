from __future__ import annotations

import importlib
import inspect

import pandas as pd


def _import_first(module_names: list[str]):
    last_error = None
    for module_name in module_names:
        try:
            return importlib.import_module(module_name)
        except ImportError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise ImportError("No module names were provided.")


def _load_tokenizer():
    module = importlib.import_module("app.tokenizer")
    preferred_names = [
        "tokenize",
        "tokenize_sentence",
        "tokenize_text",
        "simple_tokenize",
        "preprocess_and_tokenize",
        "normalize_and_tokenize",
        "split_sentence",
    ]

    for name in preferred_names:
        candidate = getattr(module, name, None)
        if not inspect.isfunction(candidate):
            continue
        try:
            sample = candidate("The cat runs.")
        except Exception:
            continue
        if isinstance(sample, str):
            return lambda text, fn=candidate: fn(text).split()
        if isinstance(sample, (list, tuple)) and all(
            isinstance(token, str) for token in sample
        ):
            return candidate

    ranked_candidates = []
    for name, candidate in inspect.getmembers(module, inspect.isfunction):
        if candidate.__module__ != module.__name__:
            continue
        if name.startswith("_"):
            continue

        score = 0
        lowered = name.lower()
        if "token" in lowered:
            score += 3
        if "split" in lowered or "preprocess" in lowered or "normalize" in lowered:
            score += 1
        ranked_candidates.append((score, name, candidate))

    ranked_candidates.sort(reverse=True)

    for _, _, candidate in ranked_candidates:
        try:
            sample = candidate("The cat runs.")
        except Exception:
            continue
        if isinstance(sample, str):
            return lambda text, fn=candidate: fn(text).split()
        if isinstance(sample, (list, tuple)) and all(
            isinstance(token, str) for token in sample
        ):
            return candidate

    available = [name for _, name, _ in ranked_candidates]
    raise ImportError(
        "Could not find a usable tokenizer function in app.tokenizer. "
        f"Available functions: {available}"
    )


def _load_parser():
    module = _import_first(["app.cky_parser", "app.parser", "app.cky"])
    grammar = _load_grammar_argument()

    parser_class = getattr(module, "CKYParser", None)
    if parser_class is None:
        for name, candidate in inspect.getmembers(module, inspect.isclass):
            if candidate.__module__ != module.__name__:
                continue
            lowered = name.lower()
            if "cky" in lowered or "parser" in lowered:
                parser_class = candidate
                break

    if parser_class is not None:
        grammar_kwargs = {"grammar": grammar, "cfg": grammar, "rules": grammar}
        signature = inspect.signature(parser_class)
        matched_kwargs = {}
        for name in signature.parameters:
            if name == "self":
                continue
            if name in grammar_kwargs and grammar_kwargs[name] is not None:
                matched_kwargs[name] = grammar_kwargs[name]

        constructor_attempts = []
        if matched_kwargs:
            constructor_attempts.append(("kwargs", matched_kwargs))
        if grammar is not None:
            constructor_attempts.append(("args", (grammar,)))
        constructor_attempts.append(("args", tuple()))

        for mode, values in constructor_attempts:
            try:
                if mode == "kwargs":
                    return parser_class(**values)
                return parser_class(*values)
            except TypeError:
                continue

        raise TypeError(
            f"Could not instantiate parser with signature {inspect.signature(parser_class)}."
        )

    preferred_functions = [
        "cky_parse",
        "parse",
        "parse_sentence",
        "validate",
        "validate_sentence",
        "check",
    ]
    for name in preferred_functions:
        candidate = getattr(module, name, None)
        if callable(candidate):
            return candidate

    raise ImportError("Could not find a usable parser implementation.")


def _looks_like_grammar(value) -> bool:
    return isinstance(value, dict) and bool(value)


def _call_if_zero_arg(candidate):
    if not callable(candidate):
        return None

    try:
        signature = inspect.signature(candidate)
    except (TypeError, ValueError):
        return None

    required_parameters = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.default is inspect._empty
        and parameter.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    ]
    if required_parameters:
        return None

    try:
        return candidate()
    except Exception:
        return None


def _load_grammar_argument():
    grammar_module = importlib.import_module("app.grammar")

    preferred_values = (
        "GRAMMAR",
        "LEVEL_2_GRAMMAR",
        "LEVEL2_GRAMMAR",
        "CFG",
        "PARSER_GRAMMAR",
        "grammar",
        "level_2_grammar",
    )
    for name in preferred_values:
        value = getattr(grammar_module, name, None)
        if _looks_like_grammar(value):
            return value

    preferred_factories = (
        "get_grammar",
        "build_grammar",
        "create_grammar",
        "load_grammar",
        "get_level_2_grammar",
        "build_level_2_grammar",
        "create_level_2_grammar",
        "get_level2_grammar",
        "build_level2_grammar",
        "create_level2_grammar",
    )
    for name in preferred_factories:
        value = _call_if_zero_arg(getattr(grammar_module, name, None))
        if _looks_like_grammar(value):
            return value

    named_candidates = []
    for name, value in inspect.getmembers(grammar_module):
        lowered = name.lower()
        if any(keyword in lowered for keyword in ("grammar", "cfg", "rule")):
            if _looks_like_grammar(value):
                named_candidates.append((0, value))
                continue

            produced = _call_if_zero_arg(value)
            if _looks_like_grammar(produced):
                named_candidates.append((1, produced))

    if named_candidates:
        named_candidates.sort(key=lambda item: item[0])
        return named_candidates[0][1]

    for _, value in inspect.getmembers(grammar_module):
        if _looks_like_grammar(value):
            return value

    return None


def _run_parser(parser, sentence: str, tokens: list[str]):
    grammar = _load_grammar_argument()

    if callable(parser) and not hasattr(parser, "parse"):
        callables = [parser]
    else:
        method_names = [
            "parse",
            "parse_sentence",
            "cky_parse",
            "validate",
            "validate_sentence",
            "check",
        ]
        callables = [
            getattr(parser, name)
            for name in method_names
            if callable(getattr(parser, name, None))
        ]

    attempts = []
    if grammar is not None:
        attempts.extend([(tokens, grammar), (sentence, grammar)])
    attempts.extend([(tokens,), (sentence,)])

    for candidate in callables:
        for args in attempts:
            try:
                return candidate(*args)
            except TypeError:
                continue

    signature = inspect.signature(callables[0])
    raise TypeError(f"Unsupported parser signature for evaluator: {signature}")


def _extract_valid(result) -> bool:
    if isinstance(result, bool):
        return result
    if isinstance(result, dict):
        for key in ("valid", "is_valid", "accepted"):
            if key in result:
                return bool(result[key])
    for attr in ("valid", "is_valid", "accepted"):
        if hasattr(result, attr):
            return bool(getattr(result, attr))
    return bool(result)


def evaluate_dataset(csv_path: str) -> dict:
    dataframe = pd.read_csv(csv_path)
    tokenizer = _load_tokenizer()
    parser = _load_parser()

    result_rows = []

    for _, row in dataframe.iterrows():
        sentence = str(row["sentence"]).strip()
        expected_label = str(row["label"]).strip().upper()
        tokens = tokenizer(sentence)
        if isinstance(tokens, str):
            tokens = tokens.split()
        else:
            tokens = list(tokens)
        result = _run_parser(parser, sentence, tokens)

        is_valid = _extract_valid(result)
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
