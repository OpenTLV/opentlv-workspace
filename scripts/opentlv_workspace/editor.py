# SPDX-FileCopyrightText: 2026 Marek Cingel
# SPDX-License-Identifier: MIT

"""Check that the multi-root VS Code workspace matches the inventory.

The required roots are defined in the "Editor workspace" section of
docs/inventory.md.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path, PurePosixPath, PureWindowsPath

from opentlv_workspace.diagnostics import Diagnostic
from opentlv_workspace.inventory import Report, Repository

WORKSPACE_FILE = "opentlv.code-workspace"
HOST_ROOT_NAME = "opentlv-workspace"
HOST_ROOT_PATH = "."
FOLDER_KEYS = ("name", "path")

Folder = dict[str, str]


def expected_folders(repositories: Sequence[Repository]) -> list[Folder]:
    """Return the ``folders`` array that the inventory requires."""
    folders = [{"name": HOST_ROOT_NAME, "path": HOST_ROOT_PATH}]
    for repository in repositories:
        folders.append(
            {"name": repository.directory, "path": f"../{repository.directory}"}
        )
    return folders


def check_editor_workspace(
    path: Path,
    repositories: Sequence[Repository] | None,
    *,
    source: str | None = None,
) -> list[Diagnostic]:
    """Check the workspace file at ``path``.

    The file structure is always checked. The roots are compared with
    ``repositories`` only when it is not ``None``; pass ``None`` when the
    inventory is invalid, because the expected roots are then unknown.
    """
    source = str(path) if source is None else source
    try:
        text = path.read_bytes().decode("utf-8")
        data = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except FileNotFoundError:
        message = "file not found; the workspace file must exist at the repository root"
    except OSError as error:
        message = f"cannot read the file: {error.strerror or error}"
    except UnicodeDecodeError as error:
        message = f"not valid UTF-8 at byte {error.start}; save the file as UTF-8"
    except _DuplicateKeyError as error:
        message = f"duplicate JSON key {error.key!r}"
    except json.JSONDecodeError as error:
        message = (
            f"invalid JSON at line {error.lineno}, column {error.colno}: "
            f"{error.msg}; the file must be plain JSON without comments or "
            "trailing commas"
        )
    else:
        return validate_editor_workspace(data, repositories, source=source)
    return [Diagnostic(source, None, message)]


def validate_editor_workspace(
    data: object,
    repositories: Sequence[Repository] | None,
    *,
    source: str = WORKSPACE_FILE,
) -> list[Diagnostic]:
    """Validate parsed workspace data; see :func:`check_editor_workspace`."""
    diagnostics: list[Diagnostic] = []

    def report(location: str | None, message: str) -> None:
        diagnostics.append(Diagnostic(source, location, message))

    if not isinstance(data, dict):
        report(None, "the top level must be a JSON object")
        return diagnostics
    for key in data:
        if key != "folders":
            report(
                key,
                "unknown key; the file contains only 'folders'. Keep settings, "
                "tasks, launch configurations, and extension recommendations "
                "out of the shared workspace",
            )
    if "folders" not in data:
        report(None, "missing required key 'folders'")
        return diagnostics
    folders = data["folders"]
    if not isinstance(folders, list):
        report("folders", "must be an array of root objects")
        return diagnostics

    actual: list[Folder] = []
    for index, folder in enumerate(folders, start=1):
        if _check_folder(folder, f"folders: root {index}", report):
            actual.append(folder)

    if diagnostics or repositories is None:
        return diagnostics
    _compare_roots(actual, expected_folders(repositories), report)
    return diagnostics


def _check_folder(folder: object, location: str, report: Report) -> bool:
    if not isinstance(folder, dict):
        report(location, "must be an object with the keys 'name' and 'path'")
        return False
    valid = True
    for key in folder:
        if key not in FOLDER_KEYS:
            report(
                f"{location}: {key}", "unknown key; a root has only 'name' and 'path'"
            )
            valid = False
    for key in FOLDER_KEYS:
        if key not in folder:
            report(location, f"missing required key {key!r}")
            valid = False
        elif not isinstance(folder[key], str) or not folder[key]:
            report(f"{location}: {key}", "must be a non-empty string")
            valid = False
    return valid


def _compare_roots(
    actual: Sequence[Folder], expected: Sequence[Folder], report: Report
) -> None:
    expected_by_path = {folder["path"]: folder for folder in expected}
    seen: set[str] = set()
    for index, folder in enumerate(actual, start=1):
        path = folder["path"]
        location = f"folders: root {index} ({path})"
        if path in seen:
            report(location, "duplicates an earlier root with the same path")
            continue
        seen.add(path)
        wanted = expected_by_path.get(path)
        if wanted is None:
            report(location, _extra_root_message(path, expected_by_path))
        elif folder["name"] != wanted["name"]:
            report(
                location,
                f"has the name {folder['name']!r}; expected {wanted['name']!r}",
            )

    for folder in expected:
        if folder["path"] in seen:
            continue
        kind = "host" if folder["path"] == HOST_ROOT_PATH else "managed"
        report(
            "folders",
            f"missing the {kind} root "
            f"{{'name': {folder['name']!r}, 'path': {folder['path']!r}}}",
        )

    actual_paths = [folder["path"] for folder in actual]
    expected_paths = [folder["path"] for folder in expected]
    same_roots = sorted(actual_paths) == sorted(expected_paths)
    if same_roots and actual_paths != expected_paths:
        report(
            "folders",
            "roots are out of order; list the host root first, then the managed "
            f"roots in inventory order: {', '.join(expected_paths)}",
        )


def _extra_root_message(path: str, expected_by_path: dict[str, Folder]) -> str:
    normalized = path.replace("\\", "/").rstrip("/")
    if normalized != path and normalized in expected_by_path:
        return (
            f"write the path as {normalized!r}, "
            "with forward slashes and no trailing slash"
        )
    if PurePosixPath(path).is_absolute() or PureWindowsPath(path).anchor:
        return (
            "uses an absolute path; roots use paths relative to the workspace "
            "file, such as '../<directory>'"
        )
    return "is not in the inventory; add an inventory entry first, or remove the root"


class _DuplicateKeyError(ValueError):
    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result
