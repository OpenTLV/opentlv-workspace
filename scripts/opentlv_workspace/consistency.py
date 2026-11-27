# SPDX-FileCopyrightText: 2026 Marek Cingel
# SPDX-License-Identifier: MIT

"""Check the inventory and the editor workspace of a host checkout together."""

from __future__ import annotations

from pathlib import Path

from opentlv_workspace.diagnostics import Diagnostic
from opentlv_workspace.editor import WORKSPACE_FILE, check_editor_workspace
from opentlv_workspace.inventory import INVENTORY_FILE, read_inventory


def check_workspace(root: Path) -> list[Diagnostic]:
    """Check the inventory and editor workspace in the host checkout ``root``.

    Only files inside ``root`` are read. Managed sibling checkouts do not
    need to exist, and no network access is used.
    """
    root = root.resolve()
    inventory = read_inventory(
        root / INVENTORY_FILE, source=INVENTORY_FILE, host_directory=root.name
    )
    repositories = inventory.repositories if inventory.valid else None
    diagnostics = list(inventory.diagnostics)
    diagnostics.extend(
        check_editor_workspace(
            root / WORKSPACE_FILE, repositories, source=WORKSPACE_FILE
        )
    )
    if repositories is None:
        diagnostics.append(
            Diagnostic(
                WORKSPACE_FILE,
                None,
                "roots not compared with the inventory until the inventory is valid",
            )
        )
    return diagnostics
