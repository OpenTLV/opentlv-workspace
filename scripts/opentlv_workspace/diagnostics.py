# SPDX-FileCopyrightText: 2026 Marek Cingel
# SPDX-License-Identifier: MIT

"""Diagnostics reported by workspace checks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Diagnostic:
    """A problem found in a checked file.

    ``source`` names the file, ``location`` the element within it, such as
    an inventory entry, and ``message`` describes the problem and how to fix
    it.
    """

    source: str
    location: str | None
    message: str

    def __str__(self) -> str:
        if self.location is None:
            return f"{self.source}: {self.message}"
        return f"{self.source}: {self.location}: {self.message}"
