# Contributing to OpenTLV Workspace

Thank you for your interest in contributing to OpenTLV.

This repository maintains the shared Visual Studio Code development workspace for the OpenTLV ecosystem.

Follow the [shared contribution guidelines](https://github.com/OpenTLV/.github/blob/main/CONTRIBUTING.md)
and [support directory](https://github.com/OpenTLV/.github/blob/main/SUPPORT.md),
together with the Workspace-specific instructions below.

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

## Line Endings

The repository's [.gitattributes](.gitattributes) uses automatic text detection and LF line endings for text files in both Git and the working tree. Explicit rules cover Python sources, Markdown, JSON, YAML, TOML, text files, the VS Code workspace, and repository metadata. These rules take precedence over `core.autocrlf` and `core.eol`; no global Git configuration changes are required.

Binary files are not normalized. The `.bin` and `.dat` extensions and `tests/fixtures/binary/` are explicitly exempt, including payloads that look like text. Add an explicit `-text` rule when introducing another binary format that Git might otherwise classify as text.

Save text files with LF in your editor. Use `git ls-files --eol` to inspect tracked files and `git diff --check` to check whitespace. Existing working copies may retain CRLF until rewritten; preserve local changes and avoid destructive resets just to refresh line endings. Any normalization-only change must preserve all other bytes and leave sibling repositories untouched.

## Source License Headers

Include an MIT SPDX identifier and copyright notice at the beginning of project source files, including scripts and tests. Use the comment syntax supported by the file's language.

The examples describe Marek Cingel's original 2026 work. Use the actual author
and year for other contributions; MIT contributions do not assign copyright.
The pre-commit hook only checks metadata and never adds a fixed author's notice.
Run `reuse annotate` manually only with the correct ownership and license.

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

### License Validation

[REUSE](https://reuse.software/) checks copyright and SPDX license metadata throughout this repository. Existing `Copyright (c)` notices are supported; source headers do not need to be rewritten as `SPDX-FileCopyrightText`. REUSE checks metadata completeness and license references, not the exact author, year, or header layout required by this project's convention. Passing the check is not a legal review.

[REUSE.toml](REUSE.toml) lists documentation and configuration files that carry their metadata outside the file. Keep these paths explicit so new source files cannot silently bypass the source-header policy. The `aggregate` setting preserves and combines existing metadata rather than replacing it. For files that cannot contain comments, including binary fixtures, use a matching `<filename>.license` sidecar with SPDX and copyright notices or a narrowly scoped entry in `REUSE.toml`; do not alter binary contents to add a header.

Keep license texts referenced by file metadata in [LICENSES](LICENSES/). The MIT text there supplements, and does not replace, the root `LICENSE`. Preserve third-party copyright notices and license identifiers, and supply their corresponding license texts rather than attributing those files to Marek Cingel.

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

Contributor tooling is optional for running bootstrap. REUSE 6.2.0 requires Python 3.10 or newer; Python 3.11 is suitable and no upgrade is needed when using it. Bootstrap still supports Python 3.9 or newer with no third-party dependencies. Install contributor tools in a dedicated virtual environment, separate from Conan and component build environments, from the workspace repository:

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

Checks use `pre-commit-hooks` and `markdownlint-cli` to cover whitespace, final newlines, YAML and JSON syntax, Python syntax, Markdown, and large files (500 KiB by default). Markdownlint uses `.markdownlint.json`. The JSON hook excludes `.code-workspace` files; Fast CI validates our workspace's strict JSON syntax, root paths and integration consistency separately.

The pinned REUSE hook runs the read-only `reuse lint` check across the repository,
not just Python sources or staged files. It rejects missing metadata without
rewriting headers or assigning an author. The hook environment and
`requirements-dev.txt` include `charset-normalizer` for encoding detection on
Windows without a separate libmagic installation.

Add accurate headers yourself or invoke `reuse annotate` explicitly with the
actual author's name, year and license. The optional
[header template](.reuse/templates/source-header.jinja2) places the SPDX identifier
first. Review changes and preserve existing contributor and third-party notices.
REUSE 6.2.0 can move Python encoding declarations below the first two lines;
maintain such headers manually while keeping the files covered by `reuse lint`.

## Bootstrap Validation

Run the offline bootstrap checks from the workspace repository:

```bash
python -B tests/test_bootstrap.py -v
```

The tests run copies of the script against local Git repositories in system temporary directories, outside the development workspace. They disable network Git protocols and cover cloning, repeated runs, existing checkout preservation, conflicts, and failures. Python and Git are required; no third-party Python packages are needed. Report which operating systems were tested.

## Continuous Integration

Workspace CI has four separate entry points:

- [PR](.github/workflows/workspace-pr.yml): pre-commit, configuration, manifest and orchestration regressions, plus offline bootstrap on Linux, Windows and macOS.
- [Main](.github/workflows/workspace-main.yml): configuration and offline bootstrap smoke on Linux, without component downloads or builds.
- [Full](.github/workflows/workspace-full.yml): manual or Release Gate invocation; sibling and remote integration on Ubuntu 24.04 with CLI/Lua, the Rust quick start against its authenticated Core release, Go quick-start and JS runtime smoke, and portal assembly/navigation. Python has checkout and documentation coverage at its released pin; its [standalone build contract](https://github.com/OpenTLV/opentlv-python/blob/main/docs/development/python.md) remains component-owned. See the [selected release combination and coverage](docs/integration.md#full-ci-and-supported-combinations).
- [Release](.github/workflows/workspace-release.yml): manual tag input; same-attempt Full evidence, checksums and attestations before publishing a verified workspace snapshot.

Each workflow has an aggregate gate rejecting failed, cancelled, missing or skipped dependencies. Make the PR check **Workspace integration gate** required in the branch ruleset; YAML alone does not enforce that setting. PR and Main never invoke Full automatically.

Workspace maintainers review integration pins at least monthly and after relevant component releases or contract changes. Follow the [manifest update process](docs/integration.md#maintaining-the-integration-manifest): propose exact candidate SHAs, attach manual Full evidence to the update PR, and track incompatible candidates with their component owners.

Bootstrap uses local fixtures with network Git protocols disabled. Full CI uses disposable checkouts selected by [integration.json](integration.json) and records actual dependency revisions. Validation jobs have read-only repository permissions. Release grants attestation permissions only to assembly and contents-write only to publication. Checkouts never persist credentials.

See [Workspace integration quality gates](docs/integration.md) for local commands, test ownership, supported configurations, selection rules and performance evidence. Keep component test suites in their repositories. Report local results separately from GitHub Actions results; declaring a platform in the workflow does not mean it has already passed there.

## Development Independence

Each OpenTLV repository owns its build system, tests, dependencies, and releases.

The workspace must not become a prerequisite for developing or distributing any OpenTLV component.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
