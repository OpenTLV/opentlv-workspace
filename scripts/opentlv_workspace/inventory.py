# SPDX-FileCopyrightText: 2026 Marek Cingel
# SPDX-License-Identifier: MIT

"""Read and validate the managed repository inventory.

The format and rules are defined in docs/inventory.md. Validation collects
every problem it finds instead of stopping at the first one, so a single
run reports everything that needs to be fixed.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from opentlv_workspace.diagnostics import Diagnostic

INVENTORY_FILE = "repositories.toml"
SUPPORTED_VERSION = 1

HOST_IDENTITY = "github.com/OpenTLV/opentlv-workspace"
HOST_DEFAULT_DIRECTORY = "opentlv-workspace"

TOP_LEVEL_KEYS = ("version", "repositories")
ENTRY_KEYS = ("host", "owner", "name", "directory")

Report = Callable[[str | None, str], None]

_HOST_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")
_OWNER = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?")
_NAME = re.compile(r"[A-Za-z0-9._-]+")
_DIRECTORY = re.compile(r"[A-Za-z0-9._-]+")
_WINDOWS_RESERVED_NAMES = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + [f"COM{digit}" for digit in range(1, 10)]
    + [f"LPT{digit}" for digit in range(1, 10)]
)


@dataclass(frozen=True)
class Repository:
    """A managed repository entry."""

    host: str
    owner: str
    name: str
    directory: str

    @property
    def identity(self) -> str:
        """The identity as written, such as ``github.com/OpenTLV/opentlv``."""
        return f"{self.host}/{self.owner}/{self.name}"

    @property
    def identity_key(self) -> str:
        """The identity in the case-insensitive form used for comparison."""
        return self.identity.lower()


@dataclass(frozen=True)
class InventoryResult:
    """The outcome of reading an inventory.

    ``repositories`` holds the well-formed entries in inventory order. It is
    complete only if ``diagnostics`` is empty.
    """

    repositories: tuple[Repository, ...]
    diagnostics: tuple[Diagnostic, ...]

    @property
    def valid(self) -> bool:
        return not self.diagnostics


class InventoryError(Exception):
    """Raised by :func:`load_inventory` for an invalid inventory."""

    def __init__(self, diagnostics: Sequence[Diagnostic]) -> None:
        self.diagnostics = tuple(diagnostics)
        super().__init__("\n".join(str(item) for item in self.diagnostics))


def load_inventory(
    path: Path, *, host_directory: str | None = None
) -> tuple[Repository, ...]:
    """Return the entries of a valid inventory, or raise :class:`InventoryError`."""
    result = read_inventory(path, host_directory=host_directory)
    if not result.valid:
        raise InventoryError(result.diagnostics)
    return result.repositories


def read_inventory(
    path: Path, *, source: str | None = None, host_directory: str | None = None
) -> InventoryResult:
    """Read and validate the inventory file at ``path``.

    ``source`` is the file name used in diagnostics and defaults to
    ``path``. ``host_directory`` is the directory name of the host
    checkout; an entry whose directory matches it is rejected.
    """
    source = str(path) if source is None else source
    try:
        data = tomllib.loads(path.read_bytes().decode("utf-8"))
    except FileNotFoundError:
        return _failure(
            source, "file not found; the inventory must exist at the repository root"
        )
    except OSError as error:
        return _failure(source, f"cannot read the file: {error.strerror or error}")
    except UnicodeDecodeError as error:
        return _failure(
            source, f"not valid UTF-8 at byte {error.start}; save the file as UTF-8"
        )
    except tomllib.TOMLDecodeError as error:
        return _failure(source, f"invalid TOML: {error}")
    return validate_inventory(data, source=source, host_directory=host_directory)


def validate_inventory(
    data: Mapping[str, object],
    *,
    source: str = INVENTORY_FILE,
    host_directory: str | None = None,
) -> InventoryResult:
    """Validate parsed inventory data against the rules in docs/inventory.md."""
    diagnostics: list[Diagnostic] = []

    def report(location: str | None, message: str) -> None:
        diagnostics.append(Diagnostic(source, location, message))

    _check_keys(data, TOP_LEVEL_KEYS, None, report)

    if "version" in data:
        version = data["version"]
        if isinstance(version, bool) or not isinstance(version, int):
            report("version", f"must be an integer, found {_describe(version)}")
        elif version != SUPPORTED_VERSION:
            report(
                "version",
                f"unsupported version {version}; "
                f"this tool supports version {SUPPORTED_VERSION}",
            )
            # The remaining rules belong to the supported version only.
            return InventoryResult((), tuple(diagnostics))

    repositories: list[Repository] = []
    if "repositories" in data:
        entries = data["repositories"]
        if not isinstance(entries, list) or not all(
            isinstance(entry, dict) for entry in entries
        ):
            report(
                "repositories",
                "must be an array of tables, written as [[repositories]] sections",
            )
        elif not entries:
            report("repositories", "must contain at least one entry")
        else:
            for index, entry in enumerate(entries, start=1):
                repository = _validate_entry(entry, index, report)
                if repository is not None:
                    repositories.append(repository)

    _check_host(repositories, host_directory, report)
    _check_uniqueness(repositories, report)
    _check_order(repositories, report)
    return InventoryResult(tuple(repositories), tuple(diagnostics))


def entry_location(index: int, repository: Repository | None = None) -> str:
    """Name an entry by its 1-based position and, if known, its identity."""
    if repository is None:
        return f"entry {index}"
    return f"entry {index} ({repository.identity})"


def _validate_entry(
    entry: Mapping[str, object], index: int, report: Report
) -> Repository | None:
    location = entry_location(index)
    valid = _check_keys(entry, ENTRY_KEYS, location, report)

    values: dict[str, str] = {}
    for key in ENTRY_KEYS:
        if key not in entry:
            continue
        value = entry[key]
        if not isinstance(value, str) or not value:
            report(
                f"{location}: {key}",
                f"must be a non-empty string, found {_describe(value)}",
            )
            valid = False
            continue
        problem = _FIELD_CHECKS[key](value)
        if problem is not None:
            report(f"{location}: {key}", f"{value!r} {problem}")
            valid = False
        values[key] = value

    if not valid:
        return None
    return Repository(**values)


def _check_keys(
    table: Mapping[str, object],
    expected: Sequence[str],
    location: str | None,
    report: Report,
) -> bool:
    valid = True
    prefix = "" if location is None else f"{location}: "
    for key in expected:
        if key not in table:
            report(location, f"missing required key {key!r}")
            valid = False
    for key in table:
        if key not in expected:
            report(
                f"{prefix}{key}",
                f"unknown key; allowed keys are {', '.join(expected)}",
            )
            valid = False
    if valid and list(table) != list(expected):
        report(location, f"keys must be written in the order {', '.join(expected)}")
        valid = False
    return valid


def _host_problem(value: str) -> str | None:
    labels = value.split(".")
    if len(value) > 253 or not all(_HOST_LABEL.fullmatch(item) for item in labels):
        return (
            "is not a lowercase DNS host name; write only the host, such as "
            "'github.com', without a scheme, port, user name, or path"
        )
    return None


def _owner_problem(value: str) -> str | None:
    if not _OWNER.fullmatch(value):
        return (
            "may contain only ASCII letters, digits, and hyphens, "
            "and must not start or end with a hyphen"
        )
    return None


def _name_problem(value: str) -> str | None:
    if not _NAME.fullmatch(value):
        return "may contain only ASCII letters, digits, '.', '_', and '-'"
    if value in (".", ".."):
        return "is not a repository name"
    if value.lower().endswith(".git"):
        return "must not end with '.git'; write the name without the suffix"
    return None


def _directory_problem(value: str) -> str | None:
    if "/" in value or "\\" in value or ":" in value:
        return (
            "must be a single directory name under the parent directory, "
            "without path separators, a drive letter, or an absolute path"
        )
    if value in (".", ".."):
        return "must name a directory next to the host checkout, not '.' or '..'"
    if not _DIRECTORY.fullmatch(value):
        return "may contain only ASCII letters, digits, '.', '_', and '-'"
    if value.startswith("-"):
        return "must not start with '-', which tools could read as an option"
    if value.endswith("."):
        return "must not end with '.', which Windows removes"
    if value.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES:
        return "is a Windows reserved device name; choose another directory name"
    return None


_FIELD_CHECKS: dict[str, Callable[[str], str | None]] = {
    "host": _host_problem,
    "owner": _owner_problem,
    "name": _name_problem,
    "directory": _directory_problem,
}


def _check_host(
    repositories: Sequence[Repository], host_directory: str | None, report: Report
) -> None:
    reserved = {HOST_DEFAULT_DIRECTORY.lower()}
    if host_directory:
        reserved.add(host_directory.lower())
    for index, repository in enumerate(repositories, start=1):
        location = entry_location(index, repository)
        if repository.identity_key == HOST_IDENTITY.lower():
            report(
                location,
                f"identifies the host repository {HOST_IDENTITY}, "
                "which is never a managed repository",
            )
        if repository.directory.lower() in reserved:
            report(
                f"{location}: directory",
                f"{repository.directory!r} is the host checkout directory; "
                "choose a different directory",
            )


def _check_uniqueness(repositories: Sequence[Repository], report: Report) -> None:
    identities: dict[str, int] = {}
    directories: dict[str, int] = {}
    for index, repository in enumerate(repositories, start=1):
        location = entry_location(index, repository)
        first = identities.setdefault(repository.identity_key, index)
        if first != index:
            report(
                location,
                f"duplicates the identity of entry {first}; "
                "identities are compared case-insensitively",
            )
        first = directories.setdefault(repository.directory.lower(), index)
        if first != index:
            report(
                f"{location}: directory",
                f"{repository.directory!r} collides with the directory of entry "
                f"{first}; directories are compared case-insensitively",
            )


def _sort_key(repository: Repository) -> tuple[str, str, str]:
    return (
        repository.host.lower(),
        repository.owner.lower(),
        repository.name.lower(),
    )


def _check_order(repositories: Sequence[Repository], report: Report) -> None:
    for index in range(1, len(repositories)):
        current = repositories[index]
        if _sort_key(current) < _sort_key(repositories[index - 1]):
            expected = ", ".join(
                item.identity for item in sorted(repositories, key=_sort_key)
            )
            report(
                entry_location(index + 1, current),
                "is out of order; sort entries by host, owner, and name, "
                f"ignoring case: {expected}",
            )
            return


def _failure(source: str, message: str) -> InventoryResult:
    return InventoryResult((), (Diagnostic(source, None, message),))


def _describe(value: object) -> str:
    if isinstance(value, bool):
        return f"the boolean {str(value).lower()}"
    if isinstance(value, dict):
        return "a table"
    if isinstance(value, list):
        return "an array"
    if isinstance(value, str):
        return f"the string {value!r}" if value else "an empty string"
    return f"{type(value).__name__} {value!r}"
