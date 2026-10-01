"""Download the MALT dataset (metr-evals/malt-public) from Hugging Face into data/malt-public/.

The dataset is gated: accept the terms at
https://huggingface.co/datasets/metr-evals/malt-public, then authenticate with
`uv run hf auth login` or by setting HF_TOKEN.

Usage:
    uv run scripts/download_malt.py                      # default config only (~4 GB)
    uv run scripts/download_malt.py --configs vague_cot summarize
    uv run scripts/download_malt.py --all                # every config (~28 GB)
"""

import argparse
from pathlib import Path

from huggingface_hub import snapshot_download

REPO_ID = "metr-evals/malt-public"
# Config name -> directory in the repo (from the dataset card's `configs` block).
# The `default` config lives in data/; the repo's default/ directory isn't referenced by any config.
CONFIG_DIRS = {
    "default": "data",
    "irrelevant_detail": "irrelevant_detail",
    "language_mixing": "language_mixing",
    "summarize": "summarize",
    "vague_cot": "vague_cot",
}
LOCAL_DIR = Path(__file__).resolve().parent.parent / "data" / "malt-public"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--configs", nargs="+", choices=CONFIG_DIRS, default=["default"])
    parser.add_argument("--all", action="store_true", help="download every config")
    args = parser.parse_args()

    configs = list(CONFIG_DIRS) if args.all else args.configs
    patterns = ["README.md", "LICENSE"] + [f"{CONFIG_DIRS[c]}/*.parquet" for c in configs]
    path = snapshot_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        local_dir=LOCAL_DIR,
        allow_patterns=patterns,
    )
    print(f"Downloaded {', '.join(configs)} to {path}")


if __name__ == "__main__":
    main()
