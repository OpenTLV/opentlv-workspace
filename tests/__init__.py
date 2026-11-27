# SPDX-FileCopyrightText: 2026 Marek Cingel
# SPDX-License-Identifier: MIT

"""Workspace tests. Run them with ``python -m unittest discover -s tests -t .``.

The scripts directory is added to the import path, as it is when a script
runs, so tests import the shared package the same way the scripts do.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
