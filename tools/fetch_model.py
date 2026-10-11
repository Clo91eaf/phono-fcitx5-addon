#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Fetch the fixed release-test model into this repository's own cache."""
import argparse
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FILES = ["config.json", "bins/pre_model.pte", "bins/post_model.pte", "bins/pinyin_segment.pte",
         "vocabs/chinese_vocab.txt", "vocabs/context_vocab.txt", "vocabs/pinyin_char_vocab.txt",
         "vocabs/pinyin_vocab.txt", "ops_config/pinyin_segment_ops.yaml"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    lock = json.loads((ROOT / "ci/model.json").read_text())
    parser.add_argument("--output", type=Path,
                        default=ROOT / ".cache/models" / lock["revision"])
    args = parser.parse_args()
    for name in FILES:
        target = args.output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or target.stat().st_size == 0:
            urllib.request.urlretrieve(
                f"https://huggingface.co/{lock['repository']}/resolve/{lock['revision']}/{name}", target)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
