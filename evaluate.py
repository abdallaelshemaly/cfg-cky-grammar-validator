from __future__ import annotations

from pathlib import Path

from app.evaluator import evaluate_dataset


def main() -> None:
    dataset_path = Path("data/final_dataset.csv")
    output_path = Path("data/evaluation_results.csv")

    evaluation = evaluate_dataset(str(dataset_path))

    print(f"Total: {evaluation['total']}")
    print(f"Correct: {evaluation['correct']}")
    print(f"Accuracy: {evaluation['accuracy']:.4f}")

    evaluation["results"].to_csv(output_path, index=False)


if __name__ == "__main__":
    main()
