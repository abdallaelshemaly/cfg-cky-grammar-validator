from __future__ import annotations

import argparse

from app.evaluator import evaluate_dataset, summarize_results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate the CFG validator on a CSV dataset."
    )
    parser.add_argument(
        "--dataset",
        default="data/manual_level2_dataset.csv",
        help="Path to a CSV file with sentence and label columns.",
    )
    args = parser.parse_args()

    results = evaluate_dataset(args.dataset)
    summary = summarize_results(results)

    print(f"Dataset: {args.dataset}")
    print(f"Total examples: {summary.total}")
    print(f"Correct predictions: {summary.correct}")
    print(f"Accuracy: {summary.accuracy:.2%}")


if __name__ == "__main__":
    main()
