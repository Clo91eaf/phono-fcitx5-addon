#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Download a versioned core Release SDK and verify its installed version."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def fetch(prefix: Path, downloads: Path) -> None:
    lock = json.loads((ROOT / "ci/core-sdk.json").read_text())
    base = f"https://github.com/{lock['repository']}/releases/download/v{lock['version']}"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = downloads / lock['asset']
    if not archive.is_file():
        urllib.request.urlretrieve(f"{base}/{lock['asset']}", archive)
    prefix.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as package:
        package.extractall(prefix, filter="data")
    if (prefix / "share/phono-core/VERSION").read_text().strip() != lock['version']:
        raise ValueError("Installed core SDK version differs from dependency version")
    print(f"Installed core {lock['version']}: {archive.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, default=ROOT / ".sdk/phono-core")
    parser.add_argument("--downloads", type=Path, default=ROOT / ".sdk/downloads")
    args = parser.parse_args()
    fetch(args.prefix.resolve(), args.downloads.resolve())


if __name__ == "__main__":
    main()
