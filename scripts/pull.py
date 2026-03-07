"""
Pulls raw samples of 10k each from the [cited in README] datasets used in this project.
In the final version of the training data, a lot of the example outputs are tuned, and they are all merged into a single 

HuggingFace seems to have disabled this functionality.
Currently trying to see how to work around it
"""

import json
from datasets import load_dataset

targets = {
    "mediasum": ("nbroad/mediasum", None, "train"),
    "dialogsum": ("knkarthick/dialogsum", None, "train"),
    "squality": ("mattercalm/squality", None, "train"),
    "msmarco_corpus": ("Hyukkyu/beir-msmarco", "corpus", "train"),
}

for name, (repo, config, split) in targets.items():
    # load with generic loader (no trust_remote_code)
    if config:
        ds = load_dataset(repo, config, split=split)
    else:
        ds = load_dataset(repo, split=split)

    # take first 10k (shuffling in memory)
    small = ds.shuffle(seed=42).select(range(10_000))

    out = f"{name}_10k.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for example in small:
            f.write(json.dumps(example) + "\n")
