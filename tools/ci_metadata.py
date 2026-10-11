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
    parser.add_argument("--notes", type=Path)
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
    if args.notes:
        core = json.loads((ROOT / "ci/core-sdk.json").read_text())
        args.notes.parent.mkdir(parents=True, exist_ok=True)
        args.notes.write_text(f"""\n## 下载与安装 / Download and installation

版本 {value}，架构 x86_64，内置 core {core['version']}。按自己的发行版选择附件；模型单独下载。

Version {value}, x86_64, bundled core {core['version']}. Choose the asset for your distribution; download models separately.

| 发行版 / Distribution | 安装 / Install |
| --- | --- |
| Debian 13 | `sudo apt install ./phono-fcitx5-addon-x86_64-{value}-debian13.deb` |
| Ubuntu 24.04 | `sudo apt install ./phono-fcitx5-addon-x86_64-{value}-ubuntu2404.deb` |
| Fedora 43 | `sudo dnf install ./phono-fcitx5-addon-x86_64-{value}-fedora43.rpm` |
| openSUSE Tumbleweed | `sudo zypper install ./phono-fcitx5-addon-x86_64-{value}-opensuse-tumbleweed.rpm` |
| Arch Linux | `sudo pacman -U ./phono-fcitx5-addon-x86_64-{value}-arch.pkg.tar.zst` |

模型：[W4A8](https://huggingface.co/afirelily/phonop2c_v2_2_base_w4a8_model) 或 [W8A8](https://huggingface.co/afirelily/phonop2c_v2_2_base_w8a8_model)。在 Fcitx5 的 Phono 设置中将 `ModelDirectory` 指向包含 `config.json`、`bins/` 与 `vocabs/` 的目录。配置保存在 `~/.config/fcitx5/conf/phono.conf`；模型缺失时保留 libime 词典候选。

Models: [W4A8](https://huggingface.co/afirelily/phonop2c_v2_2_base_w4a8_model) or [W8A8](https://huggingface.co/afirelily/phonop2c_v2_2_base_w8a8_model). Set `ModelDirectory` in Fcitx5's Phono settings to the directory containing `config.json`, `bins/` and `vocabs/`. Configuration is stored at `~/.config/fcitx5/conf/phono.conf`; libime dictionary candidates remain available when the model is missing.
""", encoding='utf-8')
    print(f"Validated addon {value}; {len(matrix)} distribution(s)")


if __name__ == "__main__":
    main()
