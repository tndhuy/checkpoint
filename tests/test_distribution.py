import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_distribution import is_semver, validate


class DistributionTests(unittest.TestCase):
    def test_repository_distribution_is_valid(self):
        self.assertEqual(validate(), [])

    def test_semver_rejects_incomplete_versions(self):
        self.assertTrue(is_semver("0.1.0"))
        self.assertTrue(is_semver("1.2.3-beta.1+codex.local"))
        self.assertFalse(is_semver("0.1"))
        self.assertFalse(is_semver("latest"))


if __name__ == "__main__":
    unittest.main()
