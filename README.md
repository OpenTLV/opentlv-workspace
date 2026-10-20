# OpenTLV Workspace

Official Visual Studio Code multi-root workspace for developing the OpenTLV ecosystem.

This repository provides the shared editor configuration and workspace documentation for working with the `opentlv`, `opentlv-cli`, `opentlv-lua`, `opentlv-python`, and `opentlv-docs` repositories.

## Overview

The workspace opens six repositories: `opentlv-workspace`, `opentlv`, `opentlv-docs`, `opentlv-cli`, `opentlv-lua`, and `opentlv-python`. The `opentlv` repository contains the C core, C++ API, and language bindings. The `opentlv-cli` and `opentlv-lua` repositories own the standalone CLI and Lua implementation, tests, packaging and documentation; both have been extracted from Core. The `opentlv-python` repository is the destination for the standalone Python binding; its pinned revision is an initial scaffold, and Python implementation and build instructions still live in Core. The `opentlv-docs` repository assembles and publishes the OpenTLV documentation.

The workspace uses native Visual Studio Code functionality to work with multiple repositories in a single editor window.

**The workspace is optional.** Each component can be developed without this repository. Core build and release workflows are maintained in `opentlv`; standalone CLI development belongs to `opentlv-cli`, standalone Lua development belongs to `opentlv-lua`, and standalone Python build and packaging configuration belongs to `opentlv-python` as it is introduced. Documentation builds, tests, and publishing are maintained in `opentlv-docs`.

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

The script clones the missing `OpenTLV/opentlv`, `OpenTLV/opentlv-docs`, `OpenTLV/opentlv-cli`, `OpenTLV/opentlv-lua`, and `OpenTLV/opentlv-python` repositories next to `opentlv-workspace` using HTTPS by default. To use SSH instead, with GitHub SSH access configured:

```bash
python opentlv-workspace/scripts/bootstrap.py --protocol ssh
```

Destinations are resolved from the script's location, so the script can be invoked from any working directory. It prints a summary and, on success, the command to open the workspace.

Existing checkouts are skipped only when their root and `origin` identify the expected repository. GitHub HTTPS and SSH URL forms are accepted interchangeably. The script does not fetch, pull, switch branches, or modify local changes in existing checkouts. Conflicting files, directories, or repositories are left untouched and reported with a nonzero exit status.

If cloning fails, inspect the reported destination before retrying. The script does not delete failed clone output. It does not build components or documentation or install dependencies.

### Manual Setup

From the directory where you keep your projects, create a shared parent directory and clone the repositories into it:

```bash
mkdir OpenTLV
cd OpenTLV
git clone git@github.com:OpenTLV/opentlv-workspace.git
git clone git@github.com:OpenTLV/opentlv.git
git clone git@github.com:OpenTLV/opentlv-docs.git
git clone git@github.com:OpenTLV/opentlv-cli.git
git clone git@github.com:OpenTLV/opentlv-lua.git
git clone git@github.com:OpenTLV/opentlv-python.git
```

These clone commands use SSH and require GitHub SSH access. If you already have a parent directory for OpenTLV checkouts, use it instead of creating a new one.

The resulting directory structure should look like this:

```text
OpenTLV/
├── opentlv/
├── opentlv-docs/
├── opentlv-cli/
├── opentlv-lua/
├── opentlv-python/
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
| `opentlv` | `../opentlv` | `opentlv` | C core, C++ API, and language bindings |
| `opentlv-docs` | `../opentlv-docs` | `opentlv-docs` | OpenTLV documentation |
| `opentlv-cli` | `../opentlv-cli` | `opentlv-cli` | Standalone CLI, tests and documentation |
| `opentlv-lua` | `../opentlv-lua` | `opentlv-lua` | Standalone Lua binding, tests, packaging and documentation |
| `opentlv-python` | `../opentlv-python` | `opentlv-python` | Standalone Python binding repository; initial scaffold pending extraction |

Components currently live inside `opentlv`:

| Path Within `opentlv` | Component |
| --- | --- |
| `tlv/` | C core |
| `tlv++/` | C++ API |
| `bindings/` | Go, Python, Rust, and JavaScript/WebAssembly bindings |

The in-tree bindings use the Core checkout. Standalone CLI and Lua development uses `opentlv-cli` and `opentlv-lua`, with Core selected by each component's build system.

### Lua and Local Core Development

Keep `opentlv-lua` and `opentlv` next to each other as shown above. This makes the Core checkout available at `../opentlv` relative to the Lua repository and opens both repositories for side-by-side editing.

Opening the workspace does not configure or build Lua. From `opentlv-lua`, explicitly select the sibling Core checkout:

```sh
cmake -S . -B build/local -DCMAKE_BUILD_TYPE=Release \
    -DFETCHCONTENT_SOURCE_DIR_OPENTLV_CORE=/absolute/path/to/opentlv
cmake --build build/local --target opentlv_lua --config Release
ctest --test-dir build/local -C Release --output-on-failure
```

See the [Lua development guide](https://github.com/OpenTLV/opentlv-lua/blob/main/docs/development.md) for Lua headers, module loading, installed or pinned remote Core selection and LuaRocks. The [testing guide](https://github.com/OpenTLV/opentlv-lua/blob/main/docs/testing.md) describes interpreter/Busted prerequisites and the complete CI runner. Missing runtime dependencies can skip tests in ordinary CMake builds.

The Lua build must remain usable without this workspace or a sibling Core checkout. Its dependency configuration belongs in `opentlv-lua`, not in shared VS Code settings.

### Python and Local Core Development

Keep `opentlv-python` and `opentlv` as sibling checkouts. From `opentlv-python`, the local Core source is at `../opentlv`; both repositories are visible in the editor. Bootstrap prepares this layout without changing existing checkouts or configuring dependencies.

The Python revision pinned by this workspace is an initial repository scaffold with no standalone build configuration. Continue using the Python build instructions in the Core checkout until extraction provides a standalone build. Adding this workspace root does not move the in-tree binding or change its development workflow.

Follow [`opentlv-python`](https://github.com/OpenTLV/opentlv-python) for the standalone build and local Core selection contract as it becomes available. The workspace supplies no Python environment, import path or CMake override. Python must remain independently buildable without this workspace or a sibling Core checkout; dependency selection belongs to the Python repository.

## Development Documentation

Follow the documentation in `opentlv` for component prerequisites, build commands, and testing:

- [Getting started](https://github.com/OpenTLV/opentlv/blob/main/docs/getting-started/README.md): build setup and language quick starts.
- [Contributing](https://github.com/OpenTLV/opentlv/blob/main/CONTRIBUTING.md) and [development workflow](https://github.com/OpenTLV/opentlv/blob/main/docs/development/workflow.md): contribution checks, testing, and releases.
- [CLI guide](https://github.com/OpenTLV/opentlv-cli/blob/main/docs/README.md): command-line tools.
- [Bindings overview](https://github.com/OpenTLV/opentlv/blob/main/docs/concepts/bindings.md): language integration and links to binding guides.

Follow the [`opentlv-docs`](https://github.com/OpenTLV/opentlv-docs) repository for documentation builds, tests, and publishing.

Follow [`opentlv-cli`](https://github.com/OpenTLV/opentlv-cli) for standalone CLI setup and development. Opening sibling repositories does not configure a Core dependency; that integration belongs to the CLI project.

Follow the standalone [Lua API guide](https://github.com/OpenTLV/opentlv-lua/blob/main/docs/api.md), [build instructions](https://github.com/OpenTLV/opentlv-lua/blob/main/docs/development.md), and [tests and CI](https://github.com/OpenTLV/opentlv-lua/blob/main/docs/testing.md).

For changes to this workspace repository, see [CONTRIBUTING.md](CONTRIBUTING.md).

Optional contributor tooling is described in [Pre-commit Checks](CONTRIBUTING.md#pre-commit-checks). Bootstrap itself still requires only Python and Git.

## Workspace Integration CI

Four workflows separate PR validation, lightweight Main smoke, manual Full integration and a manual Release Gate. PR checks configuration, formatting, offline bootstrap and orchestration without building components. Main checks configuration and bootstrap on Linux. Full builds CLI and Lua against sibling and remote Core revisions and checks portal assembly/navigation. Python coverage validates its pinned checkout identity in both scenarios; it does not yet build or import Python or verify its Core dependency selection. Release reruns Full on the exact dispatch commit before publishing an attested integration snapshot; component releases remain independent.

[integration.json](integration.json) pins the repository combination used by CI; it does not select component release versions or change bootstrap behavior. See [integration quality gates](docs/integration.md) for supported configurations, local commands, revision evidence, the required merge check and performance measurements.

Maintainers review pins at least monthly and after relevant upstream changes through the [manifest update process](docs/integration.md#maintaining-the-integration-manifest). Passing the pinned combination does not establish compatibility with newer upstream heads.

## Development Principles

- Use native VS Code multi-root workspace functionality.
- Keep `opentlv`, `opentlv-cli`, `opentlv-lua`, `opentlv-python`, and `opentlv-docs` independent of the workspace repository.
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
