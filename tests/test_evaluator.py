from app.evaluator import evaluate_dataset, summarize_results


def test_evaluator_scores_small_dataset(tmp_path) -> None:
    dataset_path = tmp_path / "sample.csv"
    dataset_path.write_text(
        "sentence,label\n"
        "The cat sleeps.,VALID\n"
        "Cat the sleeps.,INVALID\n",
        encoding="utf-8",
    )

    results = evaluate_dataset(dataset_path)
    summary = summarize_results(results)

    assert list(results["predicted_label"]) == ["VALID", "INVALID"]
    assert summary.total == 2
    assert summary.correct == 2
    assert summary.accuracy == 1.0
