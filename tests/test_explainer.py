from app.explainer import explain_sentence


def test_explainer_reports_valid_sentence() -> None:
    explanation = explain_sentence("She reads the book.")
    assert explanation.is_valid
    assert "S -> NP VP" in explanation.message


def test_explainer_reports_unknown_tokens() -> None:
    explanation = explain_sentence("Robots dance.")
    assert not explanation.is_valid
    assert "does not recognize" in explanation.message
