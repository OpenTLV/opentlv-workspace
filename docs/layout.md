<!--
SPDX-FileCopyrightText: 2026 Marek Cingel
SPDX-License-Identifier: MIT
-->

# Repository layout and Python support

This document defines where workspace files belong and which Python versions
workspace scripts and contributor tooling support. Later changes add files
in these locations and must keep this contract, or update it in the same
pull request.

## Repository layout

| Path | Contents |
| --- | --- |
| `scripts/` | Workspace scripts, run directly with `python scripts/<name>.py` from any working directory. Scripts use only the Python standard library. |
| `scripts/opentlv_workspace/` | Shared modules imported by the scripts. The directory is a plain package, not an installed distribution. |
| `tests/` | Workspace-owned automated tests. They mirror the module structure under `scripts/` and cover workspace scripts only. |
| `tests/fixtures/` | Offline test data, such as inventories and Git repositories created in temporary directories. Tests need no network access. |
| `docs/` | Contributor and maintainer documentation for the workspace. |
| `.github/` | Repository-local GitHub configuration, such as CI workflows. Without local community files, the organization defaults apply. See the [governance record](governance.md). |
| `LICENSES/` | License texts named by their SPDX identifiers, such as `MIT.txt`. See [licensing metadata](licensing.md). |
| Repository root | `README.md`, `CHANGELOG.md`, `LICENSE`, `REUSE.toml`, the managed repository inventory `repositories.toml`, the multi-root VS Code workspace `opentlv.code-workspace`, and repository-wide configuration files for formatting, Git, and contributor tooling. |
| `.venv/` | Optional local contributor environment. It is never committed. |
| `build/` | Local scratch output, such as test logs and reports. It is never committed. |

Managed OpenTLV repositories are cloned next to the workspace checkout, not
inside it. The [managed repository inventory](inventory.md) defines which
repositories are managed and their directory names. For example:

```text
<parent>/
├── opentlv-workspace/   this repository
├── opentlv/             OpenTLV/opentlv
└── .github/             OpenTLV/.github
```

The workspace never builds, tests, or installs dependencies for a managed
repository, and its scripts and tests do not import component code.

## Formatting and line endings

Repository-wide settings at the root keep text files consistent across
platforms:

- `.editorconfig` sets UTF-8, LF line endings, a final newline, no trailing
  whitespace, and space indentation of two columns, or four for Python.
- `.gitattributes` stores text files with LF line endings and checks them
  out with LF on every platform, overriding a local `core.autocrlf`
  setting. Windows batch files use CRLF. Images, archives, wheels, and PDFs
  are marked binary, so Git never converts, diffs, or merges them as text.
- `.gitignore` excludes the local `.venv/` environment, `.env` files, `build/`
  output, Python bytecode, tool caches, and coverage reports. Keep personal
  editor and operating system files in a global excludes file instead.

When adding a binary file type, mark it in `.gitattributes` in the same
pull request. Before opening a pull request, run `git diff --check` against
the base branch to find whitespace errors.

## Python support

The runtime and contributor contracts are separate. They currently share
the same minimum version, and either minimum can be raised independently.

| Contract | Applies to | Minimum | Third-party packages |
| --- | --- | --- | --- |
| Runtime | Running anything under `scripts/` | CPython 3.11 | None |
| Contributor | Running tests and quality tools | CPython 3.11 | Pinned contributor tools, installed only into a virtual environment |

Supported versions are every CPython feature release from the minimum up to
the newest stable release. Pre-release versions and other Python
implementations are not supported. Configuration that targets a Python
version, such as linter and type checker settings, uses the runtime minimum.
Scripts may use standard library modules that are available in the minimum
version. Examples include `tomllib`, which was added in Python 3.11.

### Basis for the minimum

On 2026-11-27, [Python 3.10](https://peps.python.org/pep-0619/) had reached
end of life on 2026-10-01. [Python 3.11](https://peps.python.org/pep-0664/)
was the oldest release still receiving security fixes, with end of life
planned for October 2027.

On the same day, the [PyPI JSON API](https://docs.pypi.org/api/json/) reported
the following `Requires-Python` metadata for the latest releases of candidate
contributor tools. The pinned set is selected separately.

| Tool | Version | `Requires-Python` |
| --- | --- | --- |
| `pre-commit` | 4.7.0 | `>=3.11` |
| `zizmor` | 1.33.1 | `>=3.11` |
| `check-jsonschema` | 0.39.0 | `>=3.11` |
| `pymarkdownlnt` | 0.9.42 | `>=3.11.0` |
| `pytest` | 9.2.0 | `>=3.10` |
| `mypy` | 2.4.1 | `>=3.10` |
| `reuse` | 6.3.0 | `>=3.10` |
| `yamllint` | 1.38.0 | `>=3.10` |
| `codespell` | 2.4.3 | `>=3.9` |
| `ruff` | 0.17.6 | `>=3.7` |
| `actionlint-py` | 1.7.12.25 | `>=3.7` |

Python 3.11 satisfies every listed tool. Python 3.10 would also exclude
several of them.

### Raising a minimum

Raise a minimum in a dedicated pull request when the current minimum
reaches end of life, or when a pinned contributor tool drops it. Update this
document, the configuration that targets the minimum, and the CI test
matrix. Record the change in the changelog.

## Clean checkout setup

Install [Git](https://git-scm.com/) and a supported CPython release, then
clone the repository and check the interpreter:

```sh
git clone https://github.com/OpenTLV/opentlv-workspace.git
cd opentlv-workspace
python --version
```

On Windows, the `python` command can be an alias that opens the Microsoft
Store instead of running an installed interpreter. Use the `py` command
described in [Using Python on Windows].

### Runtime dependencies

Running workspace scripts needs only Git and a supported Python. Run them
with the system interpreter. Nothing is installed from PyPI, and no
virtual environment is required.

### Contributor dependencies

Tests and quality checks use pinned tools that are installed into a local
virtual environment, never into the system interpreter:

```sh
python -m venv .venv
```

On Debian and Ubuntu, `venv` needs the distribution's `python3-venv`
package, or the package for the specific version, such as `python3.11-venv`.

Activate the environment with `source .venv/bin/activate` on Linux and
macOS, or `.venv\Scripts\activate` on Windows. Then install the pinned
tools and run the checks as described in [contributor tooling](tooling.md):

```sh
python -m pip install --require-hashes --only-binary=:all: -r requirements-dev.txt
pre-commit run --all-files
```

Contributor tools must not become runtime dependencies, and neither set may
install dependencies of a managed repository.

[Using Python on Windows]: https://docs.python.org/3/using/windows.html
