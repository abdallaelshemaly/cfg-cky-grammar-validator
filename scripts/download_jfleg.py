from __future__ import annotations

from pathlib import Path

import pandas as pd
from datasets import load_dataset


def main() -> None:
    """Download raw JFLEG examples for manual inspection.

    This project does not treat JFLEG as a direct Level 2 benchmark. The output
    of this script is intended only as a source of candidate examples that can
    later be reviewed and filtered by hand.
    """

    dataset = load_dataset("jhu-clsp/jfleg")
    rows = []
    for split_name, split_data in dataset.items():
        for item in split_data:
            rows.append(
                {
                    "sentence": item["sentence"],
                    "corrections": " || ".join(item["corrections"]),
                    "split": split_name,
                }
            )

    output_path = Path(__file__).resolve().parents[1] / "data" / "jfleg_raw.csv"
    pd.DataFrame(rows).to_csv(output_path, index=False)
    print(f"Saved {len(rows)} raw JFLEG rows to {output_path}")


if __name__ == "__main__":
    main()
