import io
import pathlib
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import export  # noqa: E402

ROWS = str(pathlib.Path(__file__).resolve().parent.parent / "data" / "rows.json")


def run(*argv):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        export.main(["--rows", ROWS, *argv])
    return buffer.getvalue().splitlines()


class TestExport(unittest.TestCase):
    def test_header_and_all_rows(self):
        lines = run()
        self.assertEqual(lines[0], "date,reference,amount_cents")
        self.assertEqual(len(lines), 6)

    def test_until_bounds_inclusive(self):
        lines = run("--until", "2026-09-07")
        self.assertEqual(len(lines), 4)
        self.assertTrue(lines[-1].startswith("2026-09-07"))


if __name__ == "__main__":
    unittest.main()
