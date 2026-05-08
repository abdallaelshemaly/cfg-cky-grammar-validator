from __future__ import annotations

import importlib
import importlib.machinery
import inspect
import pprint
import sys
import types
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
CURRENT_FILE = Path(__file__).resolve()


def _ensure_project_package_imports() -> None:
    current_module = sys.modules.get("app")
    current_module_file = getattr(current_module, "__file__", None)
    project_app_dir = ROOT_DIR / "app"

    if (
        current_module_file
        and Path(current_module_file).resolve() == CURRENT_FILE
        and project_app_dir.exists()
    ):
        package = types.ModuleType("app")
        package.__file__ = str(project_app_dir / "__init__.py")
        package.__package__ = "app"
        package.__path__ = [str(project_app_dir)]
        package.__spec__ = importlib.machinery.ModuleSpec(
            name="app",
            loader=None,
            is_package=True,
        )
        sys.modules["app"] = package


_ensure_project_package_imports()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.explainer import explain_result
from app.grammar import CNF_GRAMMAR


def _import_first(module_names: list[str]):
    for module_name in module_names:
        try:
            return importlib.import_module(module_name)
        except ImportError:
            continue
    raise ImportError(f"Could not import any of: {', '.join(module_names)}")


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
        if inspect.isfunction(candidate):
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
            sample = candidate("the cat runs")
        except Exception:
            continue
        if isinstance(sample, (list, tuple)) and all(
            isinstance(token, str) for token in sample
        ):
            return candidate

    available = [name for _, name, _ in ranked_candidates]
    raise ImportError(
        "Could not find a usable tokenizer function in app.tokenizer. "
        f"Available functions: {available}"
    )


def _looks_like_grammar(value) -> bool:
    return isinstance(value, dict) and bool(value)


def _call_if_zero_arg(candidate):
    if not callable(candidate):
        return None

    try:
        signature = inspect.signature(candidate)
    except (TypeError, ValueError):
        return None

    required_params = [
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
    if required_params:
        return None

    try:
        return candidate()
    except Exception:
        return None


def _load_grammar():
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


def _load_allowed_words() -> set[str]:
    grammar_module = importlib.import_module("app.grammar")
    allowed_words = getattr(grammar_module, "ALLOWED_WORDS", set())
    return {str(word).strip().lower() for word in allowed_words if str(word).strip()}


def _load_parser_instance():
    module = _import_first(["app.cky_parser", "app.parser", "app.cky"])
    grammar = _load_grammar()

    parser_class = getattr(module, "CKYParser", None)
    if parser_class is None:
        for name, candidate in inspect.getmembers(module, inspect.isclass):
            if candidate.__module__ != module.__name__:
                continue
            if "cky" in name.lower() or "parser" in name.lower():
                parser_class = candidate
                break

    if parser_class is None:
        raise ImportError("Could not find CKYParser in the parser module.")

    grammar_kwargs = {}
    if grammar is not None:
        grammar_kwargs["grammar"] = grammar
        grammar_kwargs["cfg"] = grammar
        grammar_kwargs["rules"] = grammar

    init_signature = inspect.signature(parser_class)
    matched_kwargs = {}
    for name in init_signature.parameters:
        if name == "self":
            continue
        if name in grammar_kwargs:
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
        f"Could not instantiate CKYParser with signature {init_signature}."
    )


def _run_parse(parser, sentence: str, tokens: list[str]):
    method_names = [
        "parse",
        "parse_sentence",
        "cky_parse",
        "validate",
        "validate_sentence",
        "check",
    ]

    methods = []
    for name in method_names:
        candidate = getattr(parser, name, None)
        if callable(candidate):
            methods.append((name, candidate))

    if not methods:
        raise AttributeError("CKYParser does not expose a usable parse method.")

    grammar = _load_grammar()
    attempts = []
    if grammar is not None:
        attempts.extend([(tokens, grammar), (sentence, grammar)])
    attempts.extend([(tokens,), (sentence,)])

    for _, method in methods:
        for args in attempts:
            try:
                return method(*args)
            except TypeError:
                continue

    method_signature = inspect.signature(methods[0][1])
    raise TypeError(f"Unsupported parser signature for Streamlit app: {method_signature}")


def _extract_valid(result) -> bool:
    if isinstance(result, bool):
        return result
    if isinstance(result, dict):
        return result.get("valid") is True
    if hasattr(result, "valid"):
        return bool(getattr(result, "valid"))
    return bool(result)


def _extract_explanation(result, is_valid: bool) -> str:
    if isinstance(result, dict):
        for key in ("explanation", "message", "reason"):
            value = result.get(key)
            if value:
                return str(value)

    for attr in ("explanation", "message", "reason"):
        value = getattr(result, attr, None)
        if value:
            return str(value)

    if is_valid:
        return "The sentence matches the Level 2 CFG rules."
    return "The sentence does not match the Level 2 CFG rules."


def _extract_tree(result):
    if isinstance(result, dict):
        for key in ("parse_tree", "tree", "parseTree", "derivation"):
            value = result.get(key)
            if value:
                return value

    for attr in ("parse_tree", "tree", "parseTree", "derivation"):
        value = getattr(result, attr, None)
        if value:
            return value

    if isinstance(result, (list, tuple, str)):
        return result

    return None


def _build_tree_from_result(result):
    parse_tree = _extract_tree(result)
    if parse_tree is not None:
        return parse_tree

    parse_tree_module = importlib.import_module("app.parse_tree")

    if hasattr(result, "back") and hasattr(result, "tokens"):
        tokens = getattr(result, "tokens", [])
        if tokens:
            try:
                return parse_tree_module.build_parse_tree(result)
            except Exception:
                return None
        return None

    if isinstance(result, dict):
        back = result.get("back")
        tokens = result.get("tokens", [])
        if isinstance(back, list) and tokens:
            start_symbol = result.get("start_symbol", "S")
            try:
                return parse_tree_module.build_tree(
                    back,
                    0,
                    len(tokens) - 1,
                    start_symbol,
                )
            except Exception:
                return None

    return None


def _format_tree_node(tree, indent: int = 0) -> str:
    if isinstance(tree, str):
        return tree

    if isinstance(tree, (list, tuple)):
        if not tree:
            return "()"

        label = str(tree[0])
        children = list(tree[1:])
        if not children:
            return f"({label})"

        if all(not isinstance(child, (list, tuple)) for child in children):
            child_text = " ".join(str(child) for child in children)
            return f"({label} {child_text})"

        child_lines = []
        child_indent = indent + 2
        for child in children:
            child_lines.append(" " * child_indent + _format_tree_node(child, child_indent))
        return f"({label}\n" + "\n".join(child_lines) + "\n" + " " * indent + ")"

    return str(tree)


def _tree_to_text(tree) -> str:
    if tree is None:
        return ""

    if isinstance(tree, str):
        return tree

    if hasattr(tree, "pformat") and callable(getattr(tree, "pformat")):
        try:
            return tree.pformat()
        except TypeError:
            try:
                return tree.pformat(margin=100000)
            except TypeError:
                pass

    if isinstance(tree, (list, tuple)):
        try:
            parse_tree_module = importlib.import_module("app.parse_tree")
            return parse_tree_module.format_tree(tree)
        except Exception:
            return _format_tree_node(tree)

    if isinstance(tree, dict):
        return pprint.pformat(tree, sort_dicts=False)

    return str(tree)


def _display_cky_table(parse_result):
    """
    Display the CKY parsing table as a styled pandas DataFrame.
    parse_result: an instance of ParseResult from cky_parser (or a dict with 'table' and 'tokens').
    """
    # Extract table and tokens
    if hasattr(parse_result, "table") and hasattr(parse_result, "tokens"):
        table = parse_result.table
        tokens = parse_result.tokens
    elif isinstance(parse_result, dict) and "table" in parse_result and "tokens" in parse_result:
        table = parse_result["table"]
        tokens = parse_result["tokens"]
    else:
        st.info("CKY table not available for this sentence (parser result format unknown).")
        return

    n = len(tokens)
    if n == 0:
        st.info("Empty sentence: no table to display.")
        return

    # Create a matrix of strings (sets of non-terminals)
    # The table is list of lists: table[start][end] where 0<=start<=end<n
    # We'll build an n x n matrix, leaving lower triangle and i>j empty.
    data = [["" for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            cell_set = table[i][j]
            if cell_set:
                # Format as comma-separated sorted list
                data[i][j] = ", ".join(sorted(cell_set))
            else:
                data[i][j] = "∅"

    # Create column labels as token index + token text
    col_labels = [f"{i}: {tokens[i]}" for i in range(n)]
    # Row labels similar but also show span start index
    row_labels = [f"{i} ↴" for i in range(n)]

    df = pd.DataFrame(data, index=row_labels, columns=col_labels)

    # Apply styling: make empty/∅ cells gray, highlight non-empty cells
    def style_cell(val):
        if val == "∅" or val == "":
            return "background-color: #f0f0f0; color: #888;"
        else:
            return "background-color: #c8e6c9; color: #1b5e20; font-weight: bold;"

    styled_df = df.style.applymap(style_cell)
    st.write("**CKY Parsing Table** (upper triangle; rows = start index, columns = end index)")
    st.dataframe(styled_df, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="CFG-Based Sentence Grammar Validator", layout="centered")

    st.title("CFG-Based Sentence Grammar Validator")
    st.write(
        "Level 2 CFG only: simple declarative sentences, NP, VP, adjectives, "
        "pronouns, and proper names."
    )

    sentence = st.text_input("Sentence", placeholder="Enter a sentence")

    if st.button("Check Grammar"):
        if not sentence.strip():
            st.warning("Please enter a sentence.")
            return

        try:
            tokenizer = _load_tokenizer()
            parser = _load_parser_instance()

            tokens = tokenizer(sentence)
            if isinstance(tokens, str):
                tokens = tokens.split()
            else:
                tokens = list(tokens)

            normalized_tokens = [str(token).strip().lower() for token in tokens if str(token).strip()]
            allowed_words = _load_allowed_words()
            unknown_words = [token for token in normalized_tokens if token not in allowed_words]

            result = _run_parse(parser, sentence, tokens)
            is_valid = _extract_valid(result)
            explanation = explain_result(result, CNF_GRAMMAR)
            parse_tree = _build_tree_from_result(result) if is_valid else None
        except Exception as exc:
            st.error(f"Could not analyze the sentence: {exc}")
            return

        if unknown_words:
            is_valid = False
            explanation = (
                "These words are outside the Level 2 vocabulary: "
                + ", ".join(unknown_words)
            )
            parse_tree = None

        if is_valid:
            st.success("VALID")
        else:
            st.error("INVALID")

        st.write("Tokens:")
        st.code(str(tokens))

        st.write("Explanation:")
        st.write(explanation)

        if is_valid:
            st.subheader("Parse Tree")
            if parse_tree is not None:
                st.code(_tree_to_text(parse_tree), language="text")
            else:
                st.info("Parse tree is not available from the current parser output.")

            # Display CKY table for valid sentences
            st.subheader("CKY Parsing Table")
            try:
                _display_cky_table(result)
            except Exception as e:
                st.warning(f"Could not render CKY table: {e}")


if __name__ == "__main__":
    main()