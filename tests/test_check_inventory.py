# SPDX-FileCopyrightText: 2026 Marek Cingel
# SPDX-License-Identifier: MIT

"""Run scripts/check_inventory.py as a contributor or CI job would."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.support import (
    REPOSITORY_ROOT,
    VALID_ENTRIES,
    entry,
    inventory_text,
    make_host,
    write_text,
)

SCRIPT = REPOSITORY_ROOT / "scripts" / "check_inventory.py"


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        capture_output=True,
        encoding="utf-8",
        check=False,
    )


class CheckInventoryScriptTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.parent = Path(self._tmp.name)

    def test_repository_checkout_passes_from_another_directory(self) -> None:
        result = run(str(SCRIPT), cwd=self.parent)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout, "Inventory and editor workspace are consistent.\n"
        )
        self.assertEqual(result.stderr, "")

    def test_relocated_copy_checks_its_own_checkout(self) -> None:
        # A copy of the scripts in a host under another name checks the files
        # of that copy, wherever the command runs from.
        root = make_host(self.parent / "nested", name="relocated-host")
        shutil.copytree(
            REPOSITORY_ROOT / "scripts",
            root / "scripts",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        result = run(str(root / "scripts" / "check_inventory.py"), cwd=self.parent)
        self.assertEqual(result.returncode, 0, result.stderr)

        extra = entry(name="relocated-host", directory="Relocated-Host")
        write_text(root / "repositories.toml", inventory_text([*VALID_ENTRIES, extra]))
        result = run("scripts/check_inventory.py", cwd=root)
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "error: repositories.toml: entry 3 (github.com/OpenTLV/relocated-host): "
            "directory: 'Relocated-Host' is the host checkout directory",
            result.stderr,
        )

    def test_failure_lists_problems_and_exit_status(self) -> None:
        workspace = '{"folders": [{"name": "opentlv-workspace", "path": "."}]}\n'
        root = make_host(self.parent, workspace=workspace)
        result = run(str(SCRIPT), "--root", str(root), cwd=self.parent)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr.splitlines(),
            [
                "error: opentlv.code-workspace: folders: missing the managed root "
                "{'name': '.github', 'path': '../.github'}",
                "error: opentlv.code-workspace: folders: missing the managed root "
                "{'name': 'opentlv', 'path': '../opentlv'}",
                "2 problem(s) found; see docs/inventory.md for the rules.",
            ],
        )

    def test_relative_root_argument(self) -> None:
        make_host(self.parent, name="ws")
        result = run(str(SCRIPT), "--root", "ws", cwd=self.parent)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_root_must_be_a_directory(self) -> None:
        missing = self.parent / "missing"
        result = run(str(SCRIPT), "--root", str(missing), cwd=self.parent)
        self.assertEqual(result.returncode, 2)
        self.assertIn("is not a directory", result.stderr)


if __name__ == "__main__":
    unittest.main()
