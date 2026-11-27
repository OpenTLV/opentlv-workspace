# SPDX-FileCopyrightText: 2026 Marek Cingel
# SPDX-License-Identifier: MIT

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from opentlv_workspace.consistency import check_workspace
from tests.support import (
    REPOSITORY_ROOT,
    VALID_ENTRIES,
    entry,
    inventory_text,
    make_host,
    workspace_text,
)

NOT_COMPARED = (
    "opentlv.code-workspace: roots not compared with the inventory "
    "until the inventory is valid"
)


class CheckWorkspaceTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.parent = Path(self._tmp.name)

    def problems(self, root: Path) -> list[str]:
        return [str(diagnostic) for diagnostic in check_workspace(root)]

    def test_repository_checkout_is_consistent(self) -> None:
        self.assertEqual(self.problems(REPOSITORY_ROOT), [])

    def test_sibling_checkouts_are_not_required(self) -> None:
        root = make_host(self.parent)
        self.assertEqual(list(self.parent.iterdir()), [root])
        self.assertEqual(self.problems(root), [])

    def test_host_under_another_directory_name(self) -> None:
        root = make_host(self.parent / "a" / "b", name="my workspace")
        self.assertEqual(self.problems(root), [])

    def test_entry_matching_actual_host_directory(self) -> None:
        entries = [*VALID_ENTRIES, entry(name="tools", directory="Checkout")]
        root = make_host(
            self.parent,
            name="checkout",
            inventory=inventory_text(entries),
            workspace=workspace_text(entries),
        )
        self.assertEqual(
            self.problems(root),
            [
                "repositories.toml: entry 3 (github.com/OpenTLV/tools): "
                "directory: 'Checkout' is the host checkout directory; "
                "choose a different directory",
                NOT_COMPARED,
            ],
        )

    def test_inventory_entry_without_editor_root(self) -> None:
        entries = [*VALID_ENTRIES, entry(name="tools", directory="tools")]
        root = make_host(self.parent, inventory=inventory_text(entries))
        self.assertEqual(
            self.problems(root),
            [
                "opentlv.code-workspace: folders: missing the managed root "
                "{'name': 'tools', 'path': '../tools'}"
            ],
        )

    def test_editor_root_without_inventory_entry(self) -> None:
        entries = [*VALID_ENTRIES, entry(name="tools", directory="tools")]
        root = make_host(self.parent, workspace=workspace_text(entries))
        self.assertEqual(
            self.problems(root),
            [
                "opentlv.code-workspace: folders: root 4 (../tools): is not in "
                "the inventory; add an inventory entry first, or remove the root"
            ],
        )

    def test_missing_files(self) -> None:
        root = self.parent / "empty"
        root.mkdir()
        self.assertEqual(
            self.problems(root),
            [
                "repositories.toml: file not found; "
                "the inventory must exist at the repository root",
                "opentlv.code-workspace: file not found; "
                "the workspace file must exist at the repository root",
                NOT_COMPARED,
            ],
        )


if __name__ == "__main__":
    unittest.main()
