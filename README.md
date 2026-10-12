# OpenTLV Workspace

Official Visual Studio Code multi-root workspace for developing the OpenTLV ecosystem.

This repository provides the shared editor configuration and workspace documentation for working with the `opentlv` and `opentlv-docs` repositories.

## Overview

The workspace currently opens three repositories: `opentlv-workspace`, `opentlv`, and `opentlv-docs`. The `opentlv` repository contains the C core, C++ API, CLI, and language bindings. The `opentlv-docs` repository contains the OpenTLV documentation.

The workspace uses native Visual Studio Code functionality to work with multiple repositories in a single editor window.

**The workspace is optional.** You can open, build, test, and develop `opentlv` without this repository. Component build and release workflows are maintained in `opentlv`. Documentation builds, tests, and publishing are maintained in `opentlv-docs`.

## Prerequisites

- Git
- Visual Studio Code
- Python 3.9+ for the optional bootstrap script (`python3` on systems where `python` is unavailable)
- Development tools required by the OpenTLV components you work on; see [Development Documentation](#development-documentation)

## Getting Started

### Bootstrap

From your chosen parent directory (for example `OpenTLV/`), clone the workspace repository and run:

```bash
git clone https://github.com/OpenTLV/opentlv-workspace.git
python opentlv-workspace/scripts/bootstrap.py
```

The script clones the missing `OpenTLV/opentlv` and `OpenTLV/opentlv-docs` repositories next to `opentlv-workspace` using HTTPS by default. To use SSH instead, with GitHub SSH access configured:

```bash
python opentlv-workspace/scripts/bootstrap.py --protocol ssh
```

Destinations are resolved from the script's location, so the script can be invoked from any working directory. It prints a summary and, on success, the command to open the workspace.

Existing checkouts are skipped only when their root and `origin` identify the expected repository. GitHub HTTPS and SSH URL forms are accepted interchangeably. The script does not fetch, pull, switch branches, or modify local changes in existing checkouts. Conflicting files, directories, or repositories are left untouched and reported with a nonzero exit status.

If cloning fails, inspect the reported destination before retrying. The script does not delete failed clone output. It does not build components or documentation or install dependencies; CLI and bindings remain part of the `opentlv` checkout.

### Manual Setup

From the directory where you keep your projects, create a shared parent directory and clone the repositories into it:

```bash
mkdir OpenTLV
cd OpenTLV
git clone git@github.com:OpenTLV/opentlv-workspace.git
git clone git@github.com:OpenTLV/opentlv.git
git clone git@github.com:OpenTLV/opentlv-docs.git
```

These clone commands use SSH and require GitHub SSH access. If you already have a parent directory for OpenTLV checkouts, use it instead of creating a new one.

The resulting directory structure should look like this:

```text
OpenTLV/
├── opentlv/
├── opentlv-docs/
└── opentlv-workspace/
    └── opentlv.code-workspace
```

While still in the parent directory (`OpenTLV/` in the example), open the workspace:

```bash
code opentlv-workspace/opentlv.code-workspace
```

## Repository Structure

The roots in `opentlv.code-workspace` use paths relative to the workspace repository:

| VS Code Root | Relative Path | Repository | Purpose |
| --- | --- | --- | --- |
| `opentlv-workspace` | `.` | `opentlv-workspace` | Shared VS Code configuration and workspace documentation |
| `opentlv` | `../opentlv` | `opentlv` | C core, C++ API, CLI, and language bindings |
| `opentlv-docs` | `../opentlv-docs` | `opentlv-docs` | OpenTLV documentation |

Components currently live inside `opentlv`:

| Path Within `opentlv` | Component |
| --- | --- |
| `tlv/` | C core |
| `tlv++/` | C++ API |
| `tools/cli/` | Command-line interface |
| `bindings/` | Go, Lua, Python, Rust, and JavaScript/WebAssembly bindings |

CLI and binding development uses this same checkout; separate component repositories are not required.

## Development Documentation

Follow the documentation in `opentlv` for component prerequisites, build commands, and testing:

- [Getting started](https://github.com/OpenTLV/opentlv/blob/main/docs/getting-started/README.md): build setup and language quick starts.
- [Contributing](https://github.com/OpenTLV/opentlv/blob/main/CONTRIBUTING.md) and [development workflow](https://github.com/OpenTLV/opentlv/blob/main/docs/development/workflow.md): contribution checks, testing, and releases.
- [CLI guide](https://github.com/OpenTLV/opentlv/blob/main/docs/cli/README.md): command-line tools.
- [Bindings overview](https://github.com/OpenTLV/opentlv/blob/main/docs/concepts/bindings.md): language integration and links to binding guides.

Follow the [`opentlv-docs`](https://github.com/OpenTLV/opentlv-docs) repository for documentation builds, tests, and publishing.

For changes to this workspace repository, see [CONTRIBUTING.md](CONTRIBUTING.md).

Optional contributor tooling is described in [Pre-commit Checks](CONTRIBUTING.md#pre-commit-checks). Bootstrap itself still requires only Python and Git.

## Development Principles

- Use native VS Code multi-root workspace functionality.
- Keep `opentlv` and `opentlv-docs` buildable and testable without the workspace repository.
- Use the component build and package tools documented in `opentlv`.
- Keep build, test, and release workflows with the components they serve.
- Keep build artifacts and local configuration outside version control.

## Security

Report suspected vulnerabilities privately by following the [security policy](SECURITY.md).
It defines the workspace scope, supported revision, and reporting process.

## Code of Conduct

Participation in this project's community is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
It describes community standards and how to report unacceptable behavior privately.

## License

This repository is licensed under the MIT License. See [LICENSE](LICENSE) for details.
