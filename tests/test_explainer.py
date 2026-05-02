from __future__ import annotations


def test_explainer_reports_unknown_word(explain_sentence):
    explanation = explain_sentence("the elephant runs").lower()
    assert any(
        phrase in explanation
        for phrase in ["elephant", "unknown", "outside", "vocabulary", "not in", "allowed"]
    )


def test_explainer_reports_valid_sentence(explain_sentence):
    explanation = explain_sentence("the cat runs").lower()
    assert any(
        phrase in explanation
        for phrase in ["valid", "correct", "matches", "grammar", "accepted", "follows", "pattern"]
    )


def test_explainer_reports_verb_first_problem(explain_sentence):
    explanation = explain_sentence("runs the cat").lower()
    assert any(
        phrase in explanation
        for phrase in ["verb", "order", "subject", "noun phrase", "start", "before"]
    )
