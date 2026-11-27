<!--
SPDX-FileCopyrightText: 2026 Marek Cingel
SPDX-License-Identifier: MIT
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Recorded the active `main` ruleset, the signed merge history, and enabled private vulnerability reporting in the governance record. (#1)

### Added

- Documented the sibling checkout layout, ownership of the inventory, the editor workspace, and managed checkouts, how to clone the managed repositories and open `opentlv.code-workspace`, and an inventory change procedure that updates the editor roots and validates them with `scripts/check_inventory.py`. (#25)
- Added `scripts/check_inventory.py`, a standard-library check that validates `repositories.toml` against the documented inventory rules and verifies that `opentlv.code-workspace` lists exactly the roots the inventory requires, with actionable diagnostics, offline `unittest` regression tests, and pre-commit hooks for both. (#24)
- Added `opentlv.code-workspace`, a portable multi-root VS Code workspace with the host and the managed sibling repositories OpenTLV/opentlv and OpenTLV/.github as roots. The roots use relative paths derived from the inventory, and the file contains no settings or machine-specific configuration. (#23)
- Added `repositories.toml`, the authoritative inventory of the managed sibling repositories OpenTLV/opentlv and OpenTLV/.github, with a documented format that records each repository's transport-independent identity and checkout directory and excludes the workspace repository itself. (#22)
- Added a development guide, linked from the README, that covers clean checkout setup on Linux, macOS, and Windows, the local quality checks, and the steps for preparing a change. (#16)
- Added SPDX copyright and license metadata to every file, following the REUSE Specification 3.3, with a pinned `reuse lint` pre-commit check that rejects files without metadata and contributor guidance for file headers and third-party material. (#15)
- Added hash-locked contributor tools and pre-commit checks for file size, merge conflicts, private keys, whitespace, line endings, JSON, TOML, YAML, Markdown, and Python, with commands for local and CI use. (#14)
- Added repository-wide editor settings, LF line-ending normalization with binary file handling, and ignore rules for local environments, caches, and reports. (#13)
- Documented the repository layout, the Python 3.11 minimum for workspace scripts and contributor tooling, and clean checkout setup that separates runtime from contributor dependencies. (#12)
- Documented how to contribute, report vulnerabilities privately, and merge changes under the repository's governance settings. (#1)
