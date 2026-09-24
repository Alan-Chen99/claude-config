import os
import pathlib
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from lib import ages  # noqa: E402
import prune  # noqa: E402


class TestAges(unittest.TestCase):
    def test_suffixes(self):
        self.assertEqual(ages.seconds("6h"), 21600)
        self.assertEqual(ages.seconds("14d"), 1209600)
        self.assertEqual(ages.seconds("2w"), 1209600)

    def test_bad_spec(self):
        with self.assertRaises(ValueError):
            ages.seconds("14 days")


class TestSelect(unittest.TestCase):
    def test_only_old_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            old = root / "app-2020-01-01.log"
            new = root / "app-2026-09-01.log"
            old.write_text("x")
            new.write_text("x")
            stale = time.time() - 30 * 86400
            os.utime(old, (stale, stale))
            picked = prune.select(root, ages.seconds("14d"))
            self.assertEqual([p.name for p in picked], [old.name])


if __name__ == "__main__":
    unittest.main()
