from __future__ import annotations

import pandas as pd
import pytest

from app import evaluator as evaluator_module


def test_evaluate_dataset_computes_accuracy(tmp_path, monkeypatch):
    dataset_path = tmp_path / "dataset.csv"
    pd.DataFrame(
        [
            {"sentence": "the cat runs", "label": "VALID"},
            {"sentence": "cat the runs", "label": "INVALID"},
            {"sentence": "the dog runs", "label": "VALID"},
        ]
    ).to_csv(dataset_path, index=False)

    monkeypatch.setattr(
        evaluator_module,
        "_load_tokenizer",
        lambda: (lambda sentence: sentence.lower().split()),
    )
    monkeypatch.setattr(evaluator_module, "_load_parser", lambda: object())

    def fake_run_parser(_parser, sentence, _tokens):
        return {"valid": sentence == "the cat runs"}

    monkeypatch.setattr(evaluator_module, "_run_parser", fake_run_parser)

    evaluation = evaluator_module.evaluate_dataset(str(dataset_path))

    assert evaluation["total"] == 3
    assert evaluation["correct"] == 2
    assert evaluation["accuracy"] == pytest.approx(2 / 3)

    results = evaluation["results"]
    assert list(results.columns) == [
        "sentence",
        "expected_label",
        "predicted_label",
        "correct",
    ]
    assert results["predicted_label"].tolist() == ["VALID", "INVALID", "INVALID"]
    assert results["correct"].tolist() == [True, True, False]
