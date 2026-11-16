"""`gonk.py seed --change` files only the named changes, and refuses a name not in flight.

dax-seed runs a checkout's own gonk.py with --change and refuses a plain seed, so this flag is
what lets Dax seed this repository.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = "## 1. Work\n\n- [ ] 1.1 Do {name} (Requirement)\n"


class SeedChange(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo)
        shutil.copytree(ROOT / ".gonk", self.repo / ".gonk",
                        ignore=shutil.ignore_patterns("local.toml", "state"))
        (self.repo / "artifacts").mkdir()
        for name in ("alpha", "beta"):
            change = self.repo / "openspec" / "changes" / name
            change.mkdir(parents=True)
            (change / "proposal.md").write_text(f"## Why\n\n{name}\n", encoding="utf-8")
            (change / "tasks.md").write_text(TASKS.format(name=name), encoding="utf-8")

    def seed(self, *flags: str) -> subprocess.CompletedProcess:
        argv = [sys.executable, str(ROOT / "tools" / "gonk.py"), "--repo", str(self.repo),
                "seed", "--dry-run", *flags]
        return subprocess.run(argv, capture_output=True, text=True)

    def test_without_change_every_change_is_seeded(self) -> None:
        out = self.seed()
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("alpha 1.1", out.stdout)
        self.assertIn("beta 1.1", out.stdout)

    def test_change_seeds_only_that_change(self) -> None:
        out = self.seed("--change", "beta")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("beta 1.1", out.stdout)
        self.assertNotIn("alpha 1.1", out.stdout)

    def test_a_change_not_in_flight_is_refused(self) -> None:
        out = self.seed("--change", "gamma")
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("no change in flight named gamma", out.stderr)


if __name__ == "__main__":
    unittest.main()
