from __future__ import annotations

import streamlit as st

from app.cky_parser import parse_sentence
from app.explainer import explain_result
from app.parse_tree import build_parse_tree, render_parse_tree
from app.tokenizer import tokenize

st.set_page_config(
    page_title="CFG CKY Grammar Validator",
    page_icon="C",
    layout="centered",
)

st.title("CFG-Based Sentence Grammar Validator Using the CKY Algorithm")
st.caption(
    "A scoped CFG validator for Level 2 declarative sentence patterns only."
)

sentence = st.text_input(
    "Enter a sentence",
    value="The cat sleeps.",
    help="Supported scope: simple declarative sentences with NP and VP structure.",
)

if sentence.strip():
    try:
        tokens = tokenize(sentence)
        result = parse_sentence(sentence)
        explanation = explain_result(tokens, result)
        verdict = "VALID" if result.is_valid else "INVALID"

        st.subheader("Result")
        st.write(f"Verdict: {verdict}")
        st.write(explanation.message)

        st.subheader("Tokens")
        st.code(repr(tokens), language="python")

        if result.is_valid:
            st.subheader("Parse Tree")
            tree = build_parse_tree(result)
            st.code(render_parse_tree(tree), language="text")
        else:
            st.info("No parse tree is shown for invalid sentences.")
    except ValueError as exc:
        st.error(str(exc))

st.subheader("Supported Patterns")
st.markdown(
    "- `S -> NP VP`\n"
    "- `NP -> Det N`\n"
    "- `NP -> Det Adj N`\n"
    "- `NP -> Pronoun`\n"
    "- `NP -> ProperNoun`\n"
    "- `VP -> Verb`\n"
    "- `VP -> Verb NP`"
)
