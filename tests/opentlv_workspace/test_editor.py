# SPDX-FileCopyrightText: 2026 Marek Cingel
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from opentlv_workspace.editor import (
    WORKSPACE_FILE,
    check_editor_workspace,
    expected_folders,
    validate_editor_workspace,
)
from opentlv_workspace.inventory import INVENTORY_FILE, Repository, load_inventory
from tests.support import REPOSITORY_ROOT, write_text

PREFIX = f"{WORKSPACE_FILE}: "
REPOSITORIES = (
    Repository("github.com", "OpenTLV", ".github", ".github"),
    Repository("github.com", "OpenTLV", "opentlv", "opentlv"),
)
HOST = {"name": "opentlv-workspace", "path": "."}
GITHUB = {"name": ".github", "path": "../.github"}
OPENTLV = {"name": "opentlv", "path": "../opentlv"}


def problems(data: object, repositories=REPOSITORIES) -> list[str]:
    diagnostics = validate_editor_workspace(data, repositories)
    return [str(diagnostic) for diagnostic in diagnostics]


class RepositoryFilesTest(unittest.TestCase):
    def test_host_first_then_inventory_order(self) -> None:
        self.assertEqual(expected_folders(REPOSITORIES), [HOST, GITHUB, OPENTLV])

    def test_repository_workspace_matches_repository_inventory(self) -> None:
        repositories = load_inventory(REPOSITORY_ROOT / INVENTORY_FILE)
        path = REPOSITORY_ROOT / WORKSPACE_FILE
        diagnostics = check_editor_workspace(path, repositories)
        self.assertEqual([str(item) for item in diagnostics], [])


class FileTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / WORKSPACE_FILE

    def check(self, text: str | None) -> list[str]:
        if text is not None:
            write_text(self.path, text)
        diagnostics = check_editor_workspace(
            self.path, REPOSITORIES, source=WORKSPACE_FILE
        )
        return [str(diagnostic) for diagnostic in diagnostics]

    def test_valid_file(self) -> None:
        text = json.dumps({"folders": [HOST, GITHUB, OPENTLV]})
        self.assertEqual(self.check(text), [])

    def test_missing_file(self) -> None:
        self.assertEqual(
            self.check(None),
            [
                PREFIX + "file not found; "
                "the workspace file must exist at the repository root"
            ],
        )

    def test_invalid_utf8(self) -> None:
        self.path.write_bytes(b'{"folders": ["\xff"]}')
        self.assertEqual(
            self.check(None),
            [PREFIX + "not valid UTF-8 at byte 14; save the file as UTF-8"],
        )

    def test_comments_are_rejected(self) -> None:
        found = self.check('{\n  // roots\n  "folders": []\n}\n')
        self.assertEqual(len(found), 1)
        expected = PREFIX + "invalid JSON at line 2, column 3"
        self.assertTrue(found[0].startswith(expected))
        self.assertTrue(found[0].endswith("without comments or trailing commas"))

    def test_trailing_comma_is_rejected(self) -> None:
        found = self.check('{"folders": [{"name": "opentlv-workspace", "path": "."},]}')
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0].startswith(PREFIX + "invalid JSON"))

    def test_duplicate_keys_are_rejected(self) -> None:
        self.assertEqual(
            self.check('{"folders": [], "folders": []}'),
            [PREFIX + "duplicate JSON key 'folders'"],
        )


class StructureTest(unittest.TestCase):
    def test_top_level_must_be_object(self) -> None:
        self.assertEqual(
            problems([HOST]), [PREFIX + "the top level must be a JSON object"]
        )

    def test_missing_folders(self) -> None:
        self.assertEqual(problems({}), [PREFIX + "missing required key 'folders'"])

    def test_folders_must_be_array(self) -> None:
        self.assertEqual(
            problems({"folders": {}}),
            [PREFIX + "folders: must be an array of root objects"],
        )

    def test_settings_are_rejected(self) -> None:
        data = {"folders": [HOST, GITHUB, OPENTLV], "settings": {"files.eol": "\n"}}
        found = problems(data)
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0].startswith(PREFIX + "settings: unknown key"))

    def test_malformed_roots(self) -> None:
        folders = [
            "../opentlv",
            {"path": "."},
            {"name": "x", "path": "", "uri": "file:///x"},
        ]
        self.assertEqual(
            problems({"folders": folders}),
            [
                PREFIX + "folders: root 1: must be an object with the keys "
                "'name' and 'path'",
                PREFIX + "folders: root 2: missing required key 'name'",
                PREFIX + "folders: root 3: uri: unknown key; "
                "a root has only 'name' and 'path'",
                PREFIX + "folders: root 3: path: must be a non-empty string",
            ],
        )

    def test_without_inventory_only_structure_is_checked(self) -> None:
        drifted = {"folders": [HOST, OPENTLV, OPENTLV]}
        self.assertEqual(problems(drifted, repositories=None), [])
        self.assertEqual(len(problems({"folders": "x"}, repositories=None)), 1)


class RootDriftTest(unittest.TestCase):
    def test_missing_managed_root(self) -> None:
        self.assertEqual(
            problems({"folders": [HOST, OPENTLV]}),
            [
                PREFIX + "folders: missing the managed root "
                "{'name': '.github', 'path': '../.github'}"
            ],
        )

    def test_missing_host_root(self) -> None:
        self.assertEqual(
            problems({"folders": [GITHUB, OPENTLV]}),
            [
                PREFIX + "folders: missing the host root "
                "{'name': 'opentlv-workspace', 'path': '.'}"
            ],
        )

    def test_extra_root(self) -> None:
        extra = {"name": "tools", "path": "../tools"}
        self.assertEqual(
            problems({"folders": [HOST, GITHUB, OPENTLV, extra]}),
            [
                PREFIX + "folders: root 4 (../tools): is not in the inventory; "
                "add an inventory entry first, or remove the root"
            ],
        )

    def test_absolute_root(self) -> None:
        paths = ("/home/user/opentlv", "C:\\work\\opentlv", "C:/work/opentlv")
        for path in paths:
            with self.subTest(path=path):
                folder = {"name": "opentlv", "path": path}
                self.assertEqual(
                    problems({"folders": [HOST, GITHUB, folder]}),
                    [
                        PREFIX + f"folders: root 3 ({path}): uses an absolute "
                        "path; roots use paths relative to the workspace file, "
                        "such as '../<directory>'",
                        PREFIX + "folders: missing the managed root "
                        "{'name': 'opentlv', 'path': '../opentlv'}",
                    ],
                )

    def test_non_canonical_path(self) -> None:
        for path in ("..\\opentlv", "../opentlv/"):
            with self.subTest(path=path):
                folder = {"name": "opentlv", "path": path}
                found = problems({"folders": [HOST, GITHUB, folder]})
                self.assertIn(
                    PREFIX + f"folders: root 3 ({path}): write the path as "
                    "'../opentlv', with forward slashes and no trailing slash",
                    found,
                )

    def test_wrong_name(self) -> None:
        folder = {"name": "OpenTLV", "path": "../opentlv"}
        self.assertEqual(
            problems({"folders": [HOST, GITHUB, folder]}),
            [
                PREFIX + "folders: root 3 (../opentlv): has the name 'OpenTLV'; "
                "expected 'opentlv'"
            ],
        )

    def test_host_name_is_fixed(self) -> None:
        host = {"name": "my-checkout", "path": "."}
        self.assertEqual(
            problems({"folders": [host, GITHUB, OPENTLV]}),
            [
                PREFIX + "folders: root 1 (.): has the name 'my-checkout'; "
                "expected 'opentlv-workspace'"
            ],
        )

    def test_duplicate_root(self) -> None:
        self.assertEqual(
            problems({"folders": [HOST, GITHUB, OPENTLV, OPENTLV]}),
            [
                PREFIX + "folders: root 4 (../opentlv): duplicates an earlier "
                "root with the same path"
            ],
        )

    def test_order(self) -> None:
        self.assertEqual(
            problems({"folders": [HOST, OPENTLV, GITHUB]}),
            [
                PREFIX + "folders: roots are out of order; list the host root "
                "first, then the managed roots in inventory order: "
                "., ../.github, ../opentlv"
            ],
        )


if __name__ == "__main__":
    unittest.main()
