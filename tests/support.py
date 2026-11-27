# SPDX-FileCopyrightText: 2026 Marek Cingel
# SPDX-License-Identifier: MIT

"""Helpers that build inventories and host checkouts in temporary directories."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent

VALID_ENTRIES: tuple[Mapping[str, str], ...] = (
    {
        "host": "github.com",
        "owner": "OpenTLV",
        "name": ".github",
        "directory": ".github",
    },
    {
        "host": "github.com",
        "owner": "OpenTLV",
        "name": "opentlv",
        "directory": "opentlv",
    },
)


def entry(**overrides: object) -> dict[str, object]:
    """Return a valid entry with selected fields replaced."""
    value: dict[str, object] = {
        "host": "github.com",
        "owner": "OpenTLV",
        "name": "example",
        "directory": "example",
    }
    value.update(overrides)
    return value


def inventory_text(entries: Iterable[Mapping[str, str]], *, version: int = 1) -> str:
    """Render an inventory with string fields in the documented layout."""
    lines = [f"version = {version}"]
    for item in entries:
        lines.extend(["", "[[repositories]]"])
        lines.extend(f"{key} = {json.dumps(value)}" for key, value in item.items())
    return "\n".join(lines) + "\n"


def workspace_text(entries: Iterable[Mapping[str, str]]) -> str:
    """Render the editor workspace that matches ``entries``."""
    folders = [{"name": "opentlv-workspace", "path": "."}]
    for item in entries:
        directory = item["directory"]
        folders.append({"name": directory, "path": f"../{directory}"})
    return json.dumps({"folders": folders}, indent=2) + "\n"


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text with LF line endings on every platform."""
    path.write_text(text, encoding="utf-8", newline="\n")


def make_host(
    parent: Path,
    *,
    name: str = "opentlv-workspace",
    inventory: str | None = None,
    workspace: str | None = None,
) -> Path:
    """Create a host checkout with an inventory and an editor workspace."""
    root = parent / name
    root.mkdir(parents=True)
    if inventory is None:
        inventory = inventory_text(VALID_ENTRIES)
    if workspace is None:
        workspace = workspace_text(VALID_ENTRIES)
    write_text(root / "repositories.toml", inventory)
    write_text(root / "opentlv.code-workspace", workspace)
    return root
