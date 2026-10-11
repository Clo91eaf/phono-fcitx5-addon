"""Exercise the SDK release checksum and version boundary without network access."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fetch_core_sdk


class SdkDownload(unittest.TestCase):
    def exercise(self, *, checksum_ok=True, version_ok=True):
        lock = json.loads((ROOT / "ci/core-sdk.json").read_text())
        content = io.BytesIO()
        with tarfile.open(fileobj=content, mode='w:gz') as archive:
            value = (lock['version'] if version_ok else '999.0.0').encode()
            entry = tarfile.TarInfo('share/phono-core/VERSION')
            entry.size = len(value)
            archive.addfile(entry, io.BytesIO(value))
        payload = content.getvalue()
        checksum = hashlib.sha256(payload if checksum_ok else b'other SDK').hexdigest()
        sums = f"{checksum}  {lock['asset']}\n".encode()
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            root = Path(temp)
            def download(url, target):
                Path(target).write_bytes(payload)
            with patch.object(fetch_core_sdk.urllib.request, 'urlopen', return_value=io.BytesIO(sums)), \
                 patch.object(fetch_core_sdk.urllib.request, 'urlretrieve', side_effect=download):
                fetch_core_sdk.fetch(root / 'sdk', root / 'downloads')
            record = json.loads((root / 'sdk/core-sdk.json').read_text())
            self.assertEqual(record['version'], lock['version'])
            self.assertEqual(record['asset'], lock['asset'])
            self.assertEqual(record['sha256'], checksum)

    def test_verified_release_is_recorded(self):
        self.exercise()

    def test_modified_release_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            self.exercise(checksum_ok=False)

    def test_wrong_package_version_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'version differs'):
            self.exercise(version_ok=False)


if __name__ == '__main__':
    unittest.main()
