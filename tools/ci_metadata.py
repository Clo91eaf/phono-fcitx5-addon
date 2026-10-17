#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate package versions and select the daily or full delivery matrix."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    {"target": "debian13", "image": "debian:13", "max_glibc": "2.41"},
    {"target": "ubuntu2404", "image": "ubuntu:24.04", "max_glibc": "2.39"},
    {"target": "fedora43", "image": "fedora:43", "max_glibc": "2.42"},
    {"target": "opensuse-tumbleweed", "image": "registry.opensuse.org/opensuse/tumbleweed:latest", "max_glibc": "native"},
    {"target": "arch", "image": "archlinux:base", "max_glibc": "native"},
]


def version():
    value = re.search(r"project\(phono-fcitx5-addon VERSION (\d+\.\d+\.\d+)\b",
                      (ROOT / "CMakeLists.txt").read_text()).group(1)
    if tomllib.loads((ROOT / "pixi.toml").read_text())["workspace"]["version"] != value:
        raise ValueError("CMake and Pixi package versions differ")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag")
    parser.add_argument("--default-branch")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    value = version()
    if args.tag:
        if args.tag != f"v{value}":
            raise ValueError(f"Release tag must be v{value}")
        if not args.default_branch:
            raise ValueError("A release requires the repository default branch")
        subprocess.run(["git", "merge-base", "--is-ancestor", "HEAD", f"origin/{args.default_branch}"],
                       cwd=ROOT, check=True)
    matrix = TARGETS if args.full or args.tag else [next(t for t in TARGETS if t['target'] == 'ubuntu2404')]
    if output := os.environ.get("GITHUB_OUTPUT"):
        with open(output, 'a') as stream:
            stream.write(f"version={value}\nmatrix={json.dumps({'include':matrix})}\n")
    print(f"Validated addon {value}; {len(matrix)} distribution(s)")


if __name__ == "__main__":
    main()
