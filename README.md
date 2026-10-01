# monitoring

Investigating the [MALT dataset](https://huggingface.co/datasets/metr-evals/malt-public)
(METR's Manually-Reviewed Agentic Labeled Transcripts).

## Setup

```sh
uv sync
```

## Getting the data

The dataset is gated. Accept the terms on its Hugging Face page, create a read token at
https://huggingface.co/settings/tokens, then:

```sh
uv run hf auth login                 # or: export HF_TOKEN=hf_...
uv run scripts/download_malt.py      # default config, ~4 GB -> data/malt-public/
uv run scripts/download_malt.py --all   # all five configs, ~28 GB
```
