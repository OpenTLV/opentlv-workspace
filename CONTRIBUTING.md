# Contributing to OpenTLV Workspace

Thank you for your interest in contributing to OpenTLV.

This repository maintains the shared Visual Studio Code development workspace for the OpenTLV ecosystem.

All project spaces, including issues, pull requests, and reviews, are governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
Follow its reporting instructions to report unacceptable behavior privately rather than opening a public issue.

## Scope

Contributions should focus on improving the development experience across independent OpenTLV repositories.

Examples include:

- Updating the multi-root workspace configuration.
- Adding new OpenTLV repositories.
- Improving workspace documentation.
- Maintaining recommended development settings.

Changes to OpenTLV Core, language bindings, or tools should be submitted to their respective repositories.

## Issues

For suspected security vulnerabilities, follow the [security policy](SECURITY.md) and report privately.
Do not disclose vulnerabilities through public issues, discussions, or pull requests.

Search [existing issues](https://github.com/OpenTLV/opentlv-workspace/issues) before opening a new one.
Use the [issue chooser](https://github.com/OpenTLV/opentlv-workspace/issues/new/choose) to select:

- **Bug** for problems with workspace configuration, setup, or development tooling. Include your operating system, VS Code version, reproduction steps, and expected and actual behavior. Workspace revision, relevant extensions, logs, and additional context are optional.
- **Chore** for workspace maintenance, improvements, tooling, CI, or documentation. Describe the motivation, proposed changes, and acceptance criteria. Validation and additional context are optional.
- **Blank issue** for topics that do not fit either form, with a free-form title and description.

Report component-specific build or runtime issues in the repository that owns the component.
OpenTLV Core and the bindings currently included with it use the [OpenTLV issue tracker](https://github.com/OpenTLV/opentlv/issues).

## Guidelines

1. Prefer native Visual Studio Code functionality.
2. Avoid introducing custom tooling when established solutions exist.
3. Keep workspace configuration portable across operating systems.
4. Use relative paths when referencing sibling repositories.
5. Do not introduce dependencies on the workspace into individual projects.
6. Keep changes minimal and focused.

## Source License Headers

Include an MIT SPDX identifier and copyright notice at the beginning of project source files, including scripts and tests. Use the comment syntax supported by the file's language.

For Python, shell, or PowerShell:

```python
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marek Cingel
```

For C, C++, Rust, JavaScript, or TypeScript:

```c
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Marek Cingel
```

Use the equivalent comment syntax for other languages. Preserve required leading directives, such as shebangs and encoding declarations; in Python, place the header before the module docstring and imports.

Do not insert comments into formats that do not support them, such as JSON, or replace third-party license notices. Generated files should receive headers through their generator where appropriate. The full license text is in [LICENSE](LICENSE).

## Pull Requests

Complete the [pull request template](.github/PULL_REQUEST_TEMPLATE.md) when submitting a change:

- **Description:** explain the problem and the resulting behavior or maintenance improvement.
- **Related Issue:** link relevant issues; use `Closes #<number>` only when the pull request resolves the issue.
- **Type:** select bug fix, maintenance, tooling/CI, or documentation as applicable.
- **Testing:** list completed local checks and their results separately from pending checks that require merging or verification on GitHub. If no checks were run, explain why.
- **Checklist:** confirm scope, documentation, changelog, and validation. For documentation or changelog items that do not apply, replace the checkbox with `N/A` and briefly explain why.

Before submitting a pull request:

- Verify that the workspace configuration is valid.
- Confirm that referenced paths follow the documented repository layout.
- Update the README when changing workspace behavior.
- Update the changelog for notable changes.

## Pre-commit Checks

Contributor tooling is optional for running bootstrap. Install it in a virtual environment from the workspace repository:

```bash
python -m venv .venv
```

Activate it with `.venv\Scripts\Activate.ps1` in PowerShell or `source .venv/bin/activate` in Bash, then run:

```bash
python -m pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files
```

Git is required. The first run downloads the pinned hook environments and may take longer; Markdownlint's Node environment is managed by pre-commit. Hook installation applies only to this repository. Bootstrap does not install dependencies or activate hooks.

Checks use `pre-commit-hooks` and `markdownlint-cli` to cover whitespace, final newlines, YAML and JSON syntax, Python syntax, Markdown, and large files (500 KiB by default). Markdownlint uses `.markdownlint.json`. The JSON hook excludes `.code-workspace` files because they may contain JSONC comments; workspace syntax is reviewed manually.

A small local hook checks the SPDX and copyright header in Python sources (`.py` and `.pyi`), including scripts and tests. It allows a leading shebang and Python encoding declaration, reports errors without changing files, and requires no additional dependencies. Extend it when sources in other languages are introduced; the general source-header policy above still applies.

Some hooks modify files to fix formatting. Review and stage the changes, then rerun the checks. Third-party and generated directories (`vendor/`, `third_party/`, `generated/`) are excluded. Text-rewriting hooks additionally exclude identified binary files, `.bin`/`.dat` files, and `tests/fixtures/binary/`; extend these exclusions if new binary fixtures are added.

Validate changes to the hook configuration with:

```bash
pre-commit validate-config
pre-commit run --all-files
```

Run the bootstrap tests separately after changing Python files. Record the operating systems actually tested. The large-file hook checks every selected file, including already committed files, so the size limit also applies in CI.

## Bootstrap Validation

Run the offline bootstrap checks from the workspace repository:

```bash
python -B tests/test_bootstrap.py -v
```

The tests run copies of the script against local Git repositories in system temporary directories, outside the development workspace. They disable network Git protocols and cover cloning, repeated runs, existing checkout preservation, conflicts, and failures. Python and Git are required; no third-party Python packages are needed. Report which operating systems were tested.

## Continuous Integration

The [Workspace CI workflow](.github/workflows/ci.yml) runs on pull requests, pushes to `main`, and manual dispatches:

- **Pre-commit:** runs the existing hooks on Linux, using `requirements-dev.txt` for contributor dependencies.
- **Bootstrap:** runs the existing offline tests on Linux, Windows, and macOS with Python 3.11 and Git, without third-party Python dependencies.

Each job checks out only this workspace repository. Bootstrap tests use local Git fixtures in temporary directories and disable network Git protocols; no sibling `opentlv` checkout is required or cloned. The workflow uses read-only repository permissions, does not persist checkout credentials, and does not commit or push hook fixes. A failed check fails its job; review the reported diff and apply any fixes locally.

Local validation uses the pre-commit and bootstrap commands above. Report local results separately from GitHub Actions results; declaring a platform in the workflow does not mean it has already passed there.

## Development Independence

Each OpenTLV repository owns its build system, tests, dependencies, and releases.

The workspace must not become a prerequisite for developing or distributing any OpenTLV component.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
