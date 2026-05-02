from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


PARSER_MODULE_NAMES = ["app.cky_parser", "app.parser", "app.cky"]


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


def _load_tokenizer_function():
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


def _load_grammar_value():
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

    raise ImportError("Could not find a grammar dictionary in app.grammar.")


def _load_allowed_words() -> set[str]:
    grammar_module = importlib.import_module("app.grammar")
    words = getattr(grammar_module, "ALLOWED_WORDS", set())
    return {str(word).strip().lower() for word in words if str(word).strip()}


def _instantiate_parser(grammar):
    module = _import_first(PARSER_MODULE_NAMES)

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
            if name in grammar_kwargs:
                matched_kwargs[name] = grammar_kwargs[name]

        constructor_attempts = []
        if matched_kwargs:
            constructor_attempts.append(("kwargs", matched_kwargs))
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

    raise ImportError("Could not find a usable CKY parser implementation.")


def _run_parser(parser_target, sentence: str, tokens: list[str], grammar):
    if callable(parser_target) and not hasattr(parser_target, "parse"):
        callables = [parser_target]
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
            getattr(parser_target, name)
            for name in method_names
            if callable(getattr(parser_target, name, None))
        ]

    attempts = [
        (tokens, grammar),
        (sentence, grammar),
        (tokens,),
        (sentence,),
    ]

    for candidate in callables:
        for args in attempts:
            try:
                return candidate(*args)
            except TypeError:
                continue

    raise TypeError("Could not call the CKY parser with a supported signature.")


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


def _call_with_context(candidate, context: dict[str, object]):
    try:
        signature = inspect.signature(candidate)
    except (TypeError, ValueError):
        signature = None

    if signature is not None:
        kwargs = {}
        for name, parameter in signature.parameters.items():
            if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
                continue
            if parameter.kind == inspect.Parameter.VAR_KEYWORD:
                continue
            if name in context:
                kwargs[name] = context[name]
                continue
            if parameter.default is inspect._empty:
                kwargs = None
                break

        if kwargs is not None:
            try:
                return candidate(**kwargs)
            except TypeError:
                pass

    positional_attempts = [
        (context["sentence"],),
        (context["tokens"],),
        (context["raw_result"],),
        (context["sentence"], context["raw_result"]),
        (context["tokens"], context["raw_result"]),
        (context["sentence"], context["valid"]),
        (context["sentence"], context["tokens"], context["raw_result"]),
        (
            context["sentence"],
            context["tokens"],
            context["raw_result"],
            context["unknown_words"],
        ),
    ]

    for args in positional_attempts:
        try:
            return candidate(*args)
        except TypeError:
            continue

    raise TypeError("Could not call explainer with a supported signature.")


def _normalize_explanation(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("explanation", "message", "reason"):
            if key in value and value[key]:
                return str(value[key])
    for attr in ("explanation", "message", "reason"):
        if hasattr(value, attr):
            attribute = getattr(value, attr)
            if attribute:
                return str(attribute)
    return str(value)


def _load_explainer_callable(grammar):
    module = importlib.import_module("app.explainer")

    preferred_functions = [
        "explain_sentence",
        "explain",
        "get_explanation",
        "build_explanation",
        "make_explanation",
    ]
    for name in preferred_functions:
        candidate = getattr(module, name, None)
        if callable(candidate):
            return candidate

    for name, candidate in inspect.getmembers(module, inspect.isfunction):
        if candidate.__module__ != module.__name__:
            continue
        lowered = name.lower()
        if "explain" in lowered or "message" in lowered or "reason" in lowered:
            return candidate

    for _, cls in inspect.getmembers(module, inspect.isclass):
        if cls.__module__ != module.__name__:
            continue
        if "explain" not in cls.__name__.lower():
            continue

        constructor_attempts = [tuple(), (grammar,)]
        for args in constructor_attempts:
            try:
                instance = cls(*args)
                break
            except TypeError:
                instance = None
        if instance is None:
            continue

        for method_name in preferred_functions:
            method = getattr(instance, method_name, None)
            if callable(method):
                return method

        for name, method in inspect.getmembers(instance, callable):
            lowered = name.lower()
            if "explain" in lowered or "message" in lowered or "reason" in lowered:
                return method

    raise ImportError("Could not find a usable explainer in app.explainer.")


@pytest.fixture(scope="session")
def tokenizer():
    return _load_tokenizer_function()


@pytest.fixture(scope="session")
def grammar():
    return _load_grammar_value()


@pytest.fixture(scope="session")
def allowed_words():
    return _load_allowed_words()


@pytest.fixture
def parse_sentence(tokenizer, grammar, allowed_words):
    def _parse(sentence: str) -> dict[str, object]:
        tokens = tokenizer(sentence)
        if isinstance(tokens, str):
            token_list = tokens.split()
        else:
            token_list = list(tokens)

        normalized_tokens = [
            str(token).strip().lower() for token in token_list if str(token).strip()
        ]
        unknown_words = [
            token for token in normalized_tokens if token not in allowed_words
        ]

        if unknown_words:
            return {
                "sentence": sentence,
                "tokens": normalized_tokens,
                "valid": False,
                "raw_result": None,
                "unknown_words": unknown_words,
            }

        parser_target = _instantiate_parser(grammar)
        try:
            raw_result = _run_parser(parser_target, sentence, normalized_tokens, grammar)
        except Exception as exc:
            return {
                "sentence": sentence,
                "tokens": normalized_tokens,
                "valid": False,
                "raw_result": {"error": str(exc)},
                "unknown_words": [],
            }

        return {
            "sentence": sentence,
            "tokens": normalized_tokens,
            "valid": _extract_valid(raw_result),
            "raw_result": raw_result,
            "unknown_words": [],
        }

    return _parse


@pytest.fixture
def explain_sentence(parse_sentence, grammar):
    explainer = _load_explainer_callable(grammar)

    def _explain(sentence: str) -> str:
        analysis = parse_sentence(sentence)
        context = {
            "sentence": sentence,
            "text": sentence,
            "input_text": sentence,
            "tokens": analysis["tokens"],
            "words": analysis["tokens"],
            "token_list": analysis["tokens"],
            "raw_result": analysis["raw_result"],
            "result": analysis["raw_result"],
            "parse_result": analysis["raw_result"],
            "parser_result": analysis["raw_result"],
            "analysis": analysis["raw_result"],
            "parse_output": analysis["raw_result"],
            "valid": analysis["valid"],
            "is_valid": analysis["valid"],
            "unknown_words": analysis["unknown_words"],
            "invalid_words": analysis["unknown_words"],
            "out_of_vocab_words": analysis["unknown_words"],
        }
        explanation = _call_with_context(explainer, context)
        return _normalize_explanation(explanation)

    return _explain
