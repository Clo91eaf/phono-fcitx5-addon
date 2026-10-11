"""Configure the addon with Pixi dependencies and the host Fcitx/libime ABI."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
arguments = ["cmake", "-S", str(ROOT), "-B", str(ROOT / "build/pixi"), "-G", "Ninja",
             "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_INSTALL_PREFIX=/usr",
             "-DCMAKE_TOOLCHAIN_FILE="]
prefix = os.environ.get("CONDA_PREFIX")
if not prefix:
    raise SystemExit("Run through pixi run config")
prefixes = [prefix]
sdk = os.environ.get("PHONO_SDK_PREFIX", str(ROOT / ".sdk/phono-core"))
if (Path(sdk) / "lib/cmake/phono-core/phono-coreConfig.cmake").is_file():
    prefixes.insert(0, sdk)
elif not sys.argv[1:]:
    raise SystemExit("Run pixi run fetch-core, or set PHONO_SDK_PREFIX to an installed core SDK")
arguments.append("-DCMAKE_PREFIX_PATH=" + ";".join(prefixes))
arguments.extend(sys.argv[1:])
subprocess.run(arguments, check=True)
