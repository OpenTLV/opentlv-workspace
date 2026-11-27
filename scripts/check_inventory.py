# SPDX-FileCopyrightText: 2026 Marek Cingel
# SPDX-License-Identifier: MIT

"""Validate the managed repository inventory and the editor workspace.

Checks repositories.toml against the rules in docs/inventory.md and checks
that opentlv.code-workspace lists exactly the roots that the inventory
requires. Reads only files in the host checkout and works offline.

Exit status: 0 if both files are valid, 1 if a problem is found, and 2 for a
usage error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from opentlv_workspace.consistency import check_workspace

DEFAULT_ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate repositories.toml and opentlv.code-workspace "
            "in a workspace checkout."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="host checkout to check (default: the checkout of this script)",
    )
    args = parser.parse_args(argv)
    if not args.root.is_dir():
        parser.error(f"--root {args.root} is not a directory")

    diagnostics = check_workspace(args.root)
    for diagnostic in diagnostics:
        print(f"error: {diagnostic}", file=sys.stderr)
    if diagnostics:
        print(
            f"{len(diagnostics)} problem(s) found; "
            "see docs/inventory.md for the rules.",
            file=sys.stderr,
        )
        return 1
    print("Inventory and editor workspace are consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
