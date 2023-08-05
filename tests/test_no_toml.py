#!/usr/bin/env python3

import sys
import unittest

sys.path = [a for a in sys.path if "site-packages" not in a]

from basecfg import toml_file  # noqa: E402


class FailureTest(unittest.TestCase):
    def test_file_load_error(self):
        with self.assertRaises(ImportError):
            toml_file("sync")


if __name__ == "__main__":
    unittest.main()
