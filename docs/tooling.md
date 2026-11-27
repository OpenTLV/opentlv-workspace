<!--
SPDX-FileCopyrightText: 2026 Marek Cingel
SPDX-License-Identifier: MIT
-->

# Contributor tooling

This document describes the pinned contributor tools, the pre-commit checks
they run, and how to update the pins. The [repository layout and Python
support](layout.md) document defines the supported Python versions and the
separation between runtime and contributor dependencies.

## Pinned tools

`requirements-dev.in` lists the direct contributor tools with exact versions.
`requirements-dev.txt` is generated from it and pins every direct and
transitive package to an exact version with SHA-256 hashes of its released
wheels. Do not edit `requirements-dev.txt` by hand.

| Tool | Version | Checks |
| --- | --- | --- |
| [pre-commit] | 4.7.0 | Runs the hooks in `.pre-commit-config.yaml` |
| [pre-commit-hooks] | 6.0.0 | File size, path case conflicts, merge conflict markers, broken symbolic links, private keys, byte order marks, trailing whitespace, final newlines, mixed line endings, JSON and TOML syntax |
| [yamllint] | 1.38.0 | YAML syntax and style, configured in `.yamllint.yaml` |
| [pymarkdownlnt] | 0.9.42 | Markdown style, configured in `.pymarkdown` |
| [REUSE] | 6.3.0 | SPDX copyright and license metadata, configured in file headers and `REUSE.toml` |
| [Ruff] | 0.17.6 | Python syntax, lint, and formatting, configured in `ruff.toml` |

The lock contains only wheels and has no platform-specific entries. It
records the hashes of every published wheel, so a platform is supported when
each locked package has a compatible wheel for it. Contributor tools are never runtime dependencies: workspace scripts
must not import them, and nothing in either set installs dependencies of a
managed repository.

## Installing the tools

Create and activate a virtual environment as described in
[contributor dependencies](layout.md#contributor-dependencies), then install
the lock with hash checking:

```sh
python -m pip install --require-hashes --only-binary=:all: -r requirements-dev.txt
python -m pip check
```

Use a new virtual environment when validating a pin change. pip does not
remove packages that are already installed in an existing environment, so
they could hide a missing requirement.

## Running the checks

Install the Git hook once per clone, then run every check on the whole
repository:

```sh
pre-commit install
pre-commit run --all-files
```

All hooks use `language: system`. They run the tools installed in the
active virtual environment and never download anything. Activate the
environment before committing, including from an editor; a missing tool
fails its hook. pre-commit selects files that Git tracks, so stage new
files with `git add` before a full run. The `reuse` hook is the exception: it
always checks the whole repository, including untracked files that Git does
not ignore.

| Hook | Files | Behavior on failure |
| --- | --- | --- |
| `check-added-large-files` | All | Rejects files larger than 1 MiB |
| `check-case-conflict` | All | Rejects paths that differ only in case |
| `check-merge-conflict` | Text | Rejects conflict marker lines, such as a line of seven `=` signs |
| `check-symlinks` | Symbolic links | Rejects links whose target does not exist |
| `detect-private-key` | Text | Rejects files that contain a private key |
| `fix-byte-order-marker` | Text | Removes a UTF-8 byte order mark |
| `trailing-whitespace` | Text, except `.diff` and `.patch` | Removes trailing whitespace |
| `end-of-file-fixer` | Text | Ends the file with exactly one newline |
| `mixed-line-ending` | Text | Rejects files that mix line ending styles |
| `check-json` | `*.json`, `.pymarkdown`, `opentlv.code-workspace` | Rejects invalid JSON |
| `check-toml` | TOML | Rejects invalid TOML |
| `yamllint` | YAML | Rejects syntax errors and style warnings |
| `pymarkdown` | Markdown | Rejects Markdown style violations |
| `ruff-check` | Python | Rejects syntax errors and lint violations |
| `ruff-format` | Python | Formats the file |
| `check-inventory` | `repositories.toml`, `opentlv.code-workspace`, and Python under `scripts/` | Runs `python scripts/check_inventory.py`, which rejects inventory rule violations and editor roots that do not match the inventory. See [inventory validation](inventory.md#validation) |
| `unittest` | `repositories.toml`, `opentlv.code-workspace`, and Python under `scripts/` and `tests/` | Runs the workspace tests with `python -m unittest discover --start-directory tests --top-level-directory .` and rejects any failure |
| `reuse` | Whole repository | Rejects files without copyright or license information, invalid license identifiers, and missing or unused license texts. See [licensing metadata](licensing.md) |

A hook that modifies a file fails the run. Review the change, stage it, and
run the checks again. To run one hook, pass its ID, for example
`pre-commit run yamllint --all-files`.

### Configuration choices

- Markdown line length (`MD013`) is disabled. Changelog entries are single
  physical lines, and tables contain long links.
- YAML files do not need a `---` document start marker, lines may have up to
  120 characters, and `on` is allowed as a mapping key for GitHub Actions
  workflows.
- Ruff targets Python 3.11, the runtime minimum. Besides the default
  pycodestyle and Pyflakes rules, it checks import order, common bug
  patterns, and syntax that can be upgraded for the target version.
- REUSE is installed with its `charset-normalizer` extra. REUSE detects
  file encodings with `python-magic`, which needs the system libmagic
  library and is never used on Windows. Without libmagic, it falls back to
  `charset-normalizer`, so the check needs no system packages on any
  platform.
- The workspace tests use the standard library `unittest` module, so they
  add no contributor tool pins. The test runner and the `check-inventory`
  hook run with the Python of the active environment, which is the
  interpreter the contributor created the environment with.

## Commands for continuous integration

A CI job can reproduce the local checks with a supported Python and no
other preinstalled tools:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes --only-binary=:all: -r requirements-dev.txt
python -m pip check
pre-commit run --all-files --show-diff-on-failure
```

The commands need network access only to download the locked wheels from
PyPI. The hooks run offline.

The inventory check and the workspace tests need no contributor tools. A
CI job that runs only them, for example on every supported Python version,
can use the system interpreter without a virtual environment:

```sh
python scripts/check_inventory.py
python -m unittest discover --start-directory tests --top-level-directory .
```

## Updating the pins

The lock is generated with [uv], pinned with hashes in
`requirements-lock.txt` and generated from `requirements-lock.in`. Install
it into a separate environment that is not used for the checks:

```sh
python -m venv .cache/lock-generator
. .cache/lock-generator/bin/activate
python -m pip install --require-hashes --only-binary=:all: -r requirements-lock.txt
```

Change the exact version in `requirements-dev.in`, then regenerate the lock:

```sh
uv --no-config pip compile --universal --python-version 3.11 --generate-hashes --only-binary=:all: --upgrade-package <name> --output-file requirements-dev.txt requirements-dev.in
```

Without `--upgrade-package`, the generator keeps existing pins where
possible. Use `--upgrade` instead to refresh every transitive package. Run
the generator without package index environment overrides, so it uses the
default PyPI index. `--python-version` is the runtime minimum; raise it
together with the minimum. To update uv itself, change `requirements-lock.in`
and run the same command with `requirements-lock.in` and
`requirements-lock.txt`.

Before submitting an update:

1. Review the release notes of every changed package and any added
   dependency. Hashes prove that the downloaded files match the reviewed
   ones; they do not prove that a package is trustworthy.
2. Update the versions in the [pinned tools](#pinned-tools) table.
3. Install the new lock into a new virtual environment, then run
   `python -m pip check` and `pre-commit run --all-files`.
4. Regenerate the lock a second time without `--upgrade` options and
   confirm that the file does not change.

New releases of a pinned package version can add files with new hashes.
Regenerate the lock if an install reports a missing hash for a supported
platform.

## Limitations

- The Python interpreter, pip, and `venv` come from the contributor's
  system and are outside the lock.
- A tool installed globally takes effect only if it appears before the
  virtual environment on `PATH`. Activate the environment so that the locked
  tools are used.

[pre-commit]: https://pre-commit.com/
[pre-commit-hooks]: https://github.com/pre-commit/pre-commit-hooks
[yamllint]: https://yamllint.readthedocs.io/
[pymarkdownlnt]: https://pymarkdown.readthedocs.io/
[REUSE]: https://reuse.software/
[Ruff]: https://docs.astral.sh/ruff/
[uv]: https://docs.astral.sh/uv/
