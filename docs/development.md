<!--
SPDX-FileCopyrightText: 2026 Marek Cingel
SPDX-License-Identifier: MIT
-->

# Developing the workspace

This guide takes a contributor from a clean checkout to passing local
checks and a ready pull request. It applies only to OpenTLV/opentlv-workspace.
The shared [contribution guidelines] define branch names, commit messages,
pull requests, labels, and changelog entries for every OpenTLV repository.

Setting up the workspace needs no component builds, toolchains, or
dependencies of a managed repository. The workspace never builds, tests, or
installs them; see [repository layout](layout.md).

## Prerequisites

- [Git](https://git-scm.com/).
- A supported CPython release with `pip` and `venv`. The minimum is
  CPython 3.11; see [Python support](layout.md#python-support).
- Network access to GitHub to clone, and to PyPI to install the pinned
  contributor tools. The checks themselves run offline.

On Windows, the `python` command can be an alias that opens the Microsoft
Store. Use the `py` launcher described in [Using Python on Windows] if
`python --version` does not print a version. On Debian and Ubuntu, install
the `python3-venv` package, or the package for the specific version, such
as `python3.11-venv`.

## Set up a clean checkout

Clone the repository and check the interpreter:

```sh
git clone https://github.com/OpenTLV/opentlv-workspace.git
cd opentlv-workspace
python --version
```

Create a virtual environment in `.venv/`, which Git ignores, and activate
it:

| Shell | Commands |
| --- | --- |
| Linux and macOS | `python -m venv .venv` then `. .venv/bin/activate` |
| Windows PowerShell | `python -m venv .venv` then `.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `python -m venv .venv` then `.venv\Scripts\activate.bat` |
| Git Bash on Windows | `python -m venv .venv` then `. .venv/Scripts/activate` |

If PowerShell refuses to run the activation script, allow local scripts for
the current session with
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`. See
[about Execution Policies].

With the environment active, install the hash-locked tools, verify their
dependencies, and install the Git hook:

```sh
python -m pip install --require-hashes --only-binary=:all: -r requirements-dev.txt
python -m pip check
pre-commit install
```

The install changes nothing outside `.venv/`. `pre-commit install` adds a
hook to `.git/hooks/` that runs the checks on every commit. The hook runs
the tools from the active environment, so activate it before committing,
including from an editor.

## Run the local checks

Run every check on the whole repository:

```sh
pre-commit run --all-files
```

A clean checkout passes every check. Hooks for file types that the
repository does not contain yet, such as Python files and symbolic links,
report `(no files to check)`.

- pre-commit selects files that Git tracks. Stage new files with `git add`
  before a full run so that they are checked. The `reuse` check is the
  exception and also checks untracked files that Git does not ignore.
- A hook that fixes a file, such as trailing whitespace or a missing final
  newline, fails the run. Review the change, stage it, and run the checks
  again.
- To run one check, pass its hook ID, for example
  `pre-commit run reuse --all-files`.

[Contributor tooling](tooling.md#running-the-checks) lists every hook and
its configuration. Before opening a pull request, also run
`git diff --check origin/main` to find whitespace errors that the change
introduces.

The repository has no CI workflows yet, so these local checks are the only
automated validation. Record the checks you ran and their results in the
pull request.

## Make a change

1. Create a branch from the current `main` as described in the
   [contribution guidelines].
2. Follow the [formatting and line endings](layout.md#formatting-and-line-endings)
   settings. An editor with [EditorConfig](https://editorconfig.org/)
   support applies most of them.
3. Give each new file an SPDX header, or list it in `REUSE.toml` if it
   cannot carry one. See [licensing metadata](licensing.md).
4. Add notable changes to the `Unreleased` section of the
   [changelog](../CHANGELOG.md). Write each entry as a single line, prepend
   it to its category, and end it with the issue number, for example `(#16)`.
5. Run the [local checks](#run-the-local-checks), sign your commits, and
   open a pull request that follows the shared template. The
   [governance record](governance.md#merging-to-main) describes how changes
   reach `main`.

## Reference

| Document | Covers |
| --- | --- |
| [Repository layout and Python support](layout.md) | Where files belong, supported Python versions, and the runtime and contributor dependency contracts |
| [Contributor tooling](tooling.md) | Pinned tools, every pre-commit hook, CI commands, and how to update the pins |
| [Licensing metadata](licensing.md) | SPDX file headers, `REUSE.toml`, and third-party material |
| [Repository governance](governance.md) | Inherited community policies, merge rules, and verified GitHub settings |

The organization's [contribution guidelines], [code of conduct], [support
guide], and [security policy] apply unchanged. This repository has no local
community files that replace them.

[contribution guidelines]: https://github.com/OpenTLV/.github/blob/main/CONTRIBUTING.md
[code of conduct]: https://github.com/OpenTLV/.github/blob/main/CODE_OF_CONDUCT.md
[support guide]: https://github.com/OpenTLV/.github/blob/main/SUPPORT.md
[security policy]: https://github.com/OpenTLV/opentlv-workspace/security/policy
[Using Python on Windows]: https://docs.python.org/3/using/windows.html
[about Execution Policies]: https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_execution_policies
