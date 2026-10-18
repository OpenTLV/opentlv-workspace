# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Document the completed Lua extraction, explicit sibling Core selection and standalone API, build and test instructions. (OpenTLV/opentlv-docs#27)
- Workspace folder names now match their repository names: `workspace` is now `opentlv-workspace`, and the documentation folder is `opentlv-docs`. (#23)
- License validation now covers repository-wide metadata instead of exact Python header matching. REUSE tooling requires Python 3.10+ in an isolated contributor environment; bootstrap dependencies and Python 3.9+ support remain unchanged. (#21)
- Explicit LF line-ending rules now include TOML configuration files. (#21)

### Removed

- Custom `scripts/check_license_headers.py` checker and its local pre-commit hook, replaced by REUSE. (#21)

### Fixed

- Large-file checks now include already committed files, so the size limit is enforced in clean CI checkouts. (#17)
- Added the missing final newline in `opentlv.code-workspace`. (#15)
- Corrected the workspace copyright attribution to Marek Cingel, matching the OpenTLV repository. (#11)
- README now reflects the two-repository workspace and current component locations, with clarified setup instructions and links to OpenTLV development documentation. (#9)

### Added

- Add `opentlv-lua` to the VS Code workspace, HTTPS/SSH bootstrap cloning, and setup documentation with the sibling Core layout. (#28)
- Add `opentlv-cli` to the VS Code workspace, HTTPS/SSH bootstrap cloning, and setup documentation for standalone CLI development. (OpenTLV/opentlv-cli#1)
- OpenTLV documentation folder (`../opentlv-docs`) in the workspace, with existing folders and settings preserved. (#23)
- Bootstrap cloning of the missing `opentlv-docs` repository, keeping bootstrap destinations aligned with the workspace roots, with offline test sources for every bootstrap repository. (#23)
- README setup instructions for the documentation repository, with documentation builds, tests, and publishing left to `opentlv-docs`. (#23)
- Automatic REUSE annotation of workspace Python sources before license validation, with an explicit author and year, a source-header template, and exclusions for third-party, generated, and binary fixture directories. (#21)
- Pinned REUSE pre-commit hook and contributor dependency with Windows-compatible encoding detection, explicit file annotations in `REUSE.toml`, and the MIT license text in `LICENSES/`. (#21)
- Contribution guidance for repository-wide license validation, binary sidecars, third-party notices, and REUSE's limits compared with the source-header convention. (#21)
- Repository line-ending rules in `.gitattributes`, with automatic text detection, explicit LF rules for source, documentation, and configuration files, and binary payload exclusions. (#18)
- Contribution guidance for line endings, binary exclusions, and non-destructive verification of existing checkouts. (#18)
- A read-only GitHub Actions workflow for pull requests, pushes to `main`, and manual runs, with pre-commit checks on Linux and existing offline bootstrap tests on Linux, Windows, and macOS. (#17)
- Contribution guidance for CI scope, isolated bootstrap fixtures, failure handling, and reporting local versus hosted validation. (#17)
- Pinned `pre-commit-hooks` and `markdownlint-cli` hooks for whitespace, final newlines, YAML and JSON syntax, Python syntax, Markdown, and large files, with exclusions for third-party, generated, and binary files as appropriate. (#15)
- A read-only Python SPDX and copyright header check that supports leading shebangs and encoding declarations without additional dependencies. (#15)
- Pinned pre-commit tooling in `requirements-dev.txt` and a `.gitignore` entry for local `.venv/` environments, without changing bootstrap dependencies. (#15)
- Pre-commit installation, activation, scope, and validation guidance in `CONTRIBUTING.md`, linked from the README. Workspace JSONC syntax remains manually reviewed. (#15)
- Contribution guidelines for MIT SPDX and copyright headers in project source files, scripts, and tests, using language-appropriate comment syntax. (#13)
- Optional Python bootstrap script to clone missing workspace repositories over HTTPS or SSH while preserving existing checkouts and reporting destination conflicts. (#13)
- Security policy for workspace configuration, tooling, and workflows, with private reporting guidance and links from the README and contribution guidelines. (#7)
- Code of Conduct based on the OpenTLV community policy, linked from the README and contribution guidelines. (#5)
- Pull request template for workspace changes, with contribution guidance for issue references, validation, and review checklists. (#3)
- Bug and Chore issue forms tailored to the workspace, with blank issues enabled and contribution guidance for choosing a reporting option. (#1)
- Visual Studio Code multi-root workspace configuration (`opentlv.code-workspace`).
- OpenTLV Core folder (`../opentlv`) in the workspace.
- README with prerequisites, setup steps, and the expected directory layout.
- Contribution guidelines.
- Markdownlint configuration and `.gitignore` for local editor and OS files.
