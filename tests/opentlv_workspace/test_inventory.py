# SPDX-FileCopyrightText: 2026 Marek Cingel
# SPDX-License-Identifier: MIT

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from opentlv_workspace.inventory import (
    INVENTORY_FILE,
    InventoryError,
    InventoryResult,
    Repository,
    load_inventory,
    read_inventory,
    validate_inventory,
)
from tests.support import (
    REPOSITORY_ROOT,
    VALID_ENTRIES,
    entry,
    inventory_text,
    write_text,
)

PREFIX = f"{INVENTORY_FILE}: "


def messages(result: InventoryResult) -> list[str]:
    return [str(diagnostic) for diagnostic in result.diagnostics]


def problems(*entries: object, host_directory: str | None = None) -> list[str]:
    data = {"version": 1, "repositories": list(entries)}
    return messages(validate_inventory(data, host_directory=host_directory))


class InventoryFileTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / INVENTORY_FILE

    def read(self, text: str | bytes) -> InventoryResult:
        if isinstance(text, bytes):
            self.path.write_bytes(text)
        else:
            write_text(self.path, text)
        return read_inventory(self.path, source=INVENTORY_FILE)

    def assertProblems(self, result: InventoryResult, *fragments: str) -> None:
        found = messages(result)
        for fragment in fragments:
            self.assertTrue(any(fragment in item for item in found), found)

    def test_repository_inventory_is_valid(self) -> None:
        result = read_inventory(REPOSITORY_ROOT / INVENTORY_FILE)
        self.assertEqual(messages(result), [])
        self.assertGreater(len(result.repositories), 0)

    def test_valid_inventory_keeps_order(self) -> None:
        result = self.read(inventory_text(VALID_ENTRIES))
        self.assertEqual(messages(result), [])
        self.assertEqual(
            result.repositories,
            (
                Repository("github.com", "OpenTLV", ".github", ".github"),
                Repository("github.com", "OpenTLV", "opentlv", "opentlv"),
            ),
        )

    def test_load_inventory_raises_with_diagnostics(self) -> None:
        write_text(self.path, "version = 1\n")
        with self.assertRaises(InventoryError) as context:
            load_inventory(self.path)
        self.assertEqual(len(context.exception.diagnostics), 1)
        self.assertIn("missing required key 'repositories'", str(context.exception))

    def test_missing_file(self) -> None:
        result = read_inventory(self.path, source=INVENTORY_FILE)
        self.assertEqual(
            messages(result),
            [
                PREFIX + "file not found; "
                "the inventory must exist at the repository root"
            ],
        )

    def test_invalid_toml(self) -> None:
        result = self.read("version = 1\n[[repositories]\n")
        self.assertProblems(result, PREFIX + "invalid TOML:", "line 2")

    def test_invalid_utf8(self) -> None:
        result = self.read(b"version = 1\n# \xff\n")
        self.assertProblems(result, "not valid UTF-8 at byte 14")

    def test_reports_every_problem_in_one_run(self) -> None:
        bad_host = entry(host="GitHub.com")
        bad_owner = entry(owner="-bad", name="good", directory="good")
        result = self.read(inventory_text([bad_host, bad_owner]))
        self.assertProblems(result, "entry 1: host:", "entry 2: owner:")
        self.assertEqual(result.repositories, ())


class TopLevelTest(unittest.TestCase):
    def test_unknown_key(self) -> None:
        data = {"version": 1, "repositories": [entry()], "extra": True}
        self.assertEqual(
            messages(validate_inventory(data)),
            [PREFIX + "extra: unknown key; allowed keys are version, repositories"],
        )

    def test_missing_version(self) -> None:
        result = validate_inventory({"repositories": [entry()]})
        self.assertEqual(messages(result), [PREFIX + "missing required key 'version'"])

    def test_version_must_be_integer(self) -> None:
        for version in (True, "1", 1.0):
            with self.subTest(version=version):
                data = {"version": version, "repositories": [entry()]}
                found = messages(validate_inventory(data))
                self.assertEqual(len(found), 1)
                self.assertTrue(found[0].startswith(PREFIX + "version: must be an "))

    def test_unsupported_version_stops_validation(self) -> None:
        data = {"version": 2, "repositories": [{"url": "x"}]}
        self.assertEqual(
            messages(validate_inventory(data)),
            [PREFIX + "version: unsupported version 2; this tool supports version 1"],
        )

    def test_repositories_must_be_array_of_tables(self) -> None:
        for value in ({"host": "github.com"}, ["github.com/OpenTLV/x"], "x"):
            with self.subTest(value=value):
                data = {"version": 1, "repositories": value}
                self.assertEqual(
                    messages(validate_inventory(data)),
                    [
                        PREFIX + "repositories: must be an array of tables, "
                        "written as [[repositories]] sections"
                    ],
                )

    def test_repositories_must_not_be_empty(self) -> None:
        self.assertEqual(
            problems(), [PREFIX + "repositories: must contain at least one entry"]
        )


class EntryTest(unittest.TestCase):
    def assertRejected(self, item: object, fragment: str, **kwargs: str) -> None:
        found = problems(item, **kwargs)
        self.assertTrue(any(fragment in message for message in found), found)

    def test_valid_entry(self) -> None:
        self.assertEqual(problems(entry()), [])

    def test_missing_and_unknown_keys(self) -> None:
        item = entry(url="https://github.com/OpenTLV/example.git")
        del item["directory"]
        self.assertEqual(
            problems(item),
            [
                PREFIX + "entry 1: missing required key 'directory'",
                PREFIX + "entry 1: url: unknown key; "
                "allowed keys are host, owner, name, directory",
            ],
        )

    def test_key_order(self) -> None:
        item = {
            "owner": "OpenTLV",
            "host": "github.com",
            "name": "example",
            "directory": "example",
        }
        self.assertEqual(
            problems(item),
            [
                PREFIX + "entry 1: keys must be written in the order "
                "host, owner, name, directory"
            ],
        )

    def test_values_must_be_non_empty_strings(self) -> None:
        cases = {"host": "", "owner": 5, "name": ["a"], "directory": True}
        for key, value in cases.items():
            with self.subTest(key=key):
                self.assertRejected(
                    entry(**{key: value}), f"entry 1: {key}: must be a non-empty string"
                )

    def test_host(self) -> None:
        hosts = (
            "GitHub.com",
            "https://github.com",
            "github.com:443",
            "git@github.com",
            "github.com/OpenTLV",
            "-github.com",
            "github..com",
        )
        for host in hosts:
            with self.subTest(host=host):
                self.assertRejected(entry(host=host), "is not a lowercase DNS host")
        self.assertEqual(problems(entry(host="git.example-host.org")), [])

    def test_owner(self) -> None:
        for owner in ("-OpenTLV", "OpenTLV-", "Open_TLV", "Open.TLV", "Öpen"):
            with self.subTest(owner=owner):
                self.assertRejected(
                    entry(owner=owner), "only ASCII letters, digits, and hyphens"
                )

    def test_name(self) -> None:
        cases = {
            ".": "is not a repository name",
            "..": "is not a repository name",
            "opentlv.git": "must not end with '.git'",
            "opentlv.GIT": "must not end with '.git'",
            "open tlv": "may contain only ASCII letters",
            "open/tlv": "may contain only ASCII letters",
        }
        for name, fragment in cases.items():
            with self.subTest(name=name):
                self.assertRejected(entry(name=name), f"name: {name!r} {fragment}")
        self.assertEqual(problems(entry(name="Open_TLV.lib-2", directory="lib")), [])

    def test_directory_must_be_single_relative_component(self) -> None:
        for directory in ("/abs", "C:\\abs", "C:abs", "../up", "a/b", "a\\b"):
            with self.subTest(directory=directory):
                self.assertRejected(
                    entry(directory=directory),
                    "must be a single directory name under the parent directory",
                )
        for directory in (".", ".."):
            with self.subTest(directory=directory):
                self.assertRejected(entry(directory=directory), "not '.' or '..'")

    def test_directory_portability(self) -> None:
        cases = {
            "-opentlv": "must not start with '-'",
            "opentlv.": "must not end with '.'",
            "open tlv": "may contain only ASCII letters",
            "opentlv*": "may contain only ASCII letters",
            "CON": "Windows reserved device name",
            "nul": "Windows reserved device name",
            "Com1.txt": "Windows reserved device name",
            "lpt9.tar.gz": "Windows reserved device name",
        }
        for directory, fragment in cases.items():
            with self.subTest(directory=directory):
                self.assertRejected(entry(directory=directory), fragment)
        for directory in ("console", "COM10", "nul_", ".github", "con-tools"):
            with self.subTest(directory=directory):
                self.assertEqual(problems(entry(directory=directory)), [])

    def test_duplicate_identity_is_case_insensitive(self) -> None:
        first = entry(name="example", directory="one")
        second = entry(owner="opentlv", name="EXAMPLE", directory="two")
        self.assertEqual(
            problems(first, second),
            [
                PREFIX + "entry 2 (github.com/opentlv/EXAMPLE): duplicates the "
                "identity of entry 1; identities are compared case-insensitively"
            ],
        )

    def test_directory_collision_is_case_insensitive(self) -> None:
        first = entry(name="a", directory="Shared")
        second = entry(name="b", directory="shared")
        self.assertEqual(
            problems(first, second),
            [
                PREFIX + "entry 2 (github.com/OpenTLV/b): directory: 'shared' "
                "collides with the directory of entry 1; directories are "
                "compared case-insensitively"
            ],
        )

    def test_host_repository_is_never_managed(self) -> None:
        item = entry(owner="opentlv", name="OpenTLV-Workspace", directory="copy")
        self.assertEqual(
            problems(item),
            [
                PREFIX + "entry 1 (github.com/opentlv/OpenTLV-Workspace): "
                "identifies the host repository github.com/OpenTLV/opentlv-workspace, "
                "which is never a managed repository"
            ],
        )

    def test_host_default_directory_is_reserved(self) -> None:
        self.assertRejected(
            entry(directory="OpenTLV-Workspace"), "is the host checkout directory"
        )

    def test_actual_host_directory_is_reserved(self) -> None:
        self.assertRejected(
            entry(directory="Example"),
            "is the host checkout directory",
            host_directory="example",
        )
        self.assertEqual(problems(entry(), host_directory="workspace"), [])

    def test_order(self) -> None:
        first = entry(owner="OpenTLV", name="b", directory="b")
        second = entry(owner="opentlv", name="A", directory="a")
        self.assertEqual(
            problems(first, second),
            [
                PREFIX + "entry 2 (github.com/opentlv/A): is out of order; sort "
                "entries by host, owner, and name, ignoring case: "
                "github.com/opentlv/A, github.com/OpenTLV/b"
            ],
        )

    def test_order_compares_host_then_owner_then_name(self) -> None:
        entries = [
            entry(host="example.org", owner="z", name="z", directory="d1"),
            entry(host="github.com", owner="A", name="z", directory="d2"),
            entry(host="github.com", owner="b", name="a", directory="d3"),
        ]
        self.assertEqual(problems(*entries), [])


if __name__ == "__main__":
    unittest.main()
