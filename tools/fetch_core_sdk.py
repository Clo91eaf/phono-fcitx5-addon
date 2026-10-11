#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Download a versioned core Release SDK and verify its published checksum."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def fetch(prefix: Path, downloads: Path) -> None:
    lock = json.loads((ROOT / "ci/core-sdk.json").read_text())
    base = f"https://github.com/{lock['repository']}/releases/download/v{lock['version']}"
    downloads.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(f"{base}/{lock['checksums']}", timeout=60) as response:
        sums = response.read().decode()
    expected = next((line.split()[0] for line in sums.splitlines()
                     if len(line.split()) == 2 and line.split()[1].lstrip('*') == lock['asset']), None)
    if expected is None or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        raise ValueError(f"Missing SDK checksum for {lock['asset']}")
    archive = downloads / lock['asset']
    cached_checksum = None
    if archive.is_file():
        with archive.open('rb') as stream:
            cached_checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
    if cached_checksum != expected.lower():
        urllib.request.urlretrieve(f"{base}/{lock['asset']}", archive)
    with archive.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != expected.lower():
        raise ValueError(f"SDK checksum mismatch: {archive.name}")
    prefix.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as package:
        package.extractall(prefix, filter="data")
    if (prefix / "share/phono-core/VERSION").read_text().strip() != lock['version']:
        raise ValueError("Installed core SDK version differs from dependency version")
    (prefix / "core-sdk.json").write_text(json.dumps({**lock, "sha256": actual}, indent=2) + "\n")
    print(f"Verified core {lock['version']}: {archive.name} ({actual})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, default=ROOT / ".sdk/phono-core")
    parser.add_argument("--downloads", type=Path, default=ROOT / ".sdk/downloads")
    args = parser.parse_args()
    fetch(args.prefix.resolve(), args.downloads.resolve())


if __name__ == "__main__":
    main()
