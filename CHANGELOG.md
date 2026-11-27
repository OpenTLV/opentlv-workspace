# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Recorded the active `main` ruleset, the signed merge history, and enabled private vulnerability reporting in the governance record. (#1)

### Added

- Added hash-locked contributor tools and pre-commit checks for file size, merge conflicts, private keys, whitespace, line endings, JSON, TOML, YAML, Markdown, and Python, with commands for local and CI use. (#14)
- Added repository-wide editor settings, LF line-ending normalization with binary file handling, and ignore rules for local environments, caches, and reports. (#13)
- Documented the repository layout, the Python 3.11 minimum for workspace scripts and contributor tooling, and clean checkout setup that separates runtime from contributor dependencies. (#12)
- Documented how to contribute, report vulnerabilities privately, and merge changes under the repository's governance settings. (#1)
