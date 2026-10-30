# OpenTLV Workspace

Official Visual Studio Code multi-root workspace for developing the OpenTLV ecosystem.

This repository provides the shared editor configuration and workspace documentation for working with the `opentlv`, `opentlv-cli`, `opentlv-lua`, `opentlv-python`, `opentlv-rust`, `opentlv-go`, `opentlv-js`, `opentlv-docs`, `.github`, and `opentlv-testlab` repositories.

## Overview

The workspace opens eleven repositories: `opentlv-workspace`, `opentlv`, `opentlv-docs`, `opentlv-cli`, `opentlv-lua`, `opentlv-python`, `opentlv-rust`, `opentlv-go`, `opentlv-js`, `.github`, and `opentlv-testlab`. Core owns the C core, C++ API and its in-tree bindings. The standalone CLI, Lua, Python and Rust repositories own their implementations, tests, packaging and technical documentation. The Go migration preserves the existing binding in a standalone module with explicit Core selection. The JavaScript repository owns its standalone Emscripten build, bridge, wrappers, tests and examples. The Docs repository owns portal navigation, introductions, assembly and publication; assembling technical sources does not transfer their component ownership. The public `.github` repository is the home for organization-wide community defaults. The TestLab repository owns differential testing against external libraries, cross-language binding verification and compatibility testing of released packages.

The workspace uses native Visual Studio Code functionality to work with multiple repositories in a single editor window.

**The workspace is optional.** It owns bootstrap, shared editor configuration, sibling layout and workspace integration checks. Each component owns its build, test and release workflows and can be developed without this repository. Follow the [owner-maintained development documentation](#development-documentation) for current setup, capabilities and release status.

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

The script clones the missing `OpenTLV/opentlv`, `OpenTLV/opentlv-docs`, `OpenTLV/opentlv-cli`, `OpenTLV/opentlv-lua`, `OpenTLV/opentlv-python`, `OpenTLV/opentlv-rust`, `OpenTLV/opentlv-go`, `OpenTLV/opentlv-js`, `OpenTLV/.github`, and `OpenTLV/opentlv-testlab` repositories next to `opentlv-workspace` using HTTPS by default. To use SSH instead, with GitHub SSH access configured:

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
git clone git@github.com:OpenTLV/opentlv-rust.git
git clone git@github.com:OpenTLV/opentlv-go.git
git clone git@github.com:OpenTLV/opentlv-js.git
git clone git@github.com:OpenTLV/.github.git
git clone git@github.com:OpenTLV/opentlv-testlab.git
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
├── opentlv-rust/
├── opentlv-go/
├── opentlv-js/
├── .github/
├── opentlv-testlab/
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
| `opentlv-python` | `../opentlv-python` | `opentlv-python` | Standalone Python binding, tests, packaging and documentation |
| `opentlv-rust` | `../opentlv-rust` | `opentlv-rust` | Standalone Rust crates, tests, packaging and documentation |
| `opentlv-go` | `../opentlv-go` | `opentlv-go` | Standalone Go binding, cgo bridge, tests and examples |
| `opentlv-js` | `../opentlv-js` | `opentlv-js` | Standalone JavaScript binding, Emscripten build, tests and examples |
| `.github` | `../.github` | `.github` | Organization-wide community defaults |
| `opentlv-testlab` | `../opentlv-testlab` | `opentlv-testlab` | Independent differential, cross-language and compatibility testing |

The [Core repository guide](https://github.com/OpenTLV/opentlv) describes Core and links its technical documentation. Standalone CLI, Lua, Python and Rust select Core through their own build systems; opening sibling checkouts does not select a dependency.

### Community Repository

The public [OpenTLV/.github](https://github.com/OpenTLV/.github) checkout lives at
`../.github`, alongside `opentlv-workspace`. It is a separate Git repository;
`opentlv-workspace/.github/` still holds this repository's workflows and templates.
Bootstrap clones the default branch for development, while integration CI uses
the exact `community` revision in [integration.json](integration.json).

The reviewed pin includes corrected attribution and the shared contribution,
conduct, security and support policies and templates delivered in
[#48](https://github.com/OpenTLV/opentlv-workspace/issues/48). Repository-local
community files take precedence over organization defaults. Each repository
retains its own LICENSE, SPDX/REUSE metadata, build/test instructions and CI;
these are not distributed through community defaults. Marek Cingel retains
copyright in his original contributions, and contributor and third-party notices
must be preserved. OpenTLV is the GitHub organization, not a legal copyright holder.

Both Full scenarios record the community checkout identity. It has no runtime
smoke, Core dependency or portal source. See the
[bootstrap pin and handoff](docs/integration.md#community-repository-bootstrap).

### TestLab Repository

The public [OpenTLV/opentlv-testlab](https://github.com/OpenTLV/opentlv-testlab) checkout lives at
`../opentlv-testlab`. It is the independent laboratory for differential testing against
external libraries, cross-language binding verification and compatibility testing of
released packages. Its external test dependencies and differential-test execution belong
to TestLab, not to Core, the binding repositories or this workspace.

Both Full scenarios record the TestLab checkout identity. They do not run its tests, and it
has no Core dependency or portal source. See the
[bootstrap pin](docs/integration.md#testlab-repository-bootstrap).

### Lua and Local Core Development

Keep `opentlv-lua` and `opentlv` next to each other as shown above. This makes the Core checkout available at `../opentlv` relative to the Lua repository and opens both repositories for side-by-side editing.

Opening the workspace does not configure or build Lua. Follow the [Lua development guide](https://github.com/OpenTLV/opentlv-lua/blob/main/docs/development.md) to explicitly select local Core, configure Lua headers and load the module. It also owns installed or pinned remote Core selection and LuaRocks instructions. The [testing guide](https://github.com/OpenTLV/opentlv-lua/blob/main/docs/testing.md) owns runtime prerequisites and the complete CI runner.

The Lua build must remain usable without this workspace or a sibling Core checkout. Its dependency configuration belongs in `opentlv-lua`, not in shared VS Code settings.

### Python and Local Core Development

Keep `opentlv-python` and `opentlv` as sibling checkouts. From `opentlv-python`, the local Core source is at `../opentlv`; both repositories are visible in the editor. Bootstrap prepares this layout without changing existing checkouts or configuring dependencies.

Follow the [Python local workspace guide](https://github.com/OpenTLV/opentlv-python/blob/main/docs/development/python.md#local-workspace-development) for its environment, installation and explicit Core selection. The workspace supplies no Python environment, import path or CMake override. Python remains independently buildable without this workspace or a sibling Core checkout; dependency selection belongs to the Python repository.

The workspace's [integration manifest](integration.json) selects Python `v0.1.0`, but Workspace coverage remains limited to checkout identity and documentation assembly. Python runtime, packaging and behavioral tests stay in the component repository. See the [integration coverage limits](docs/integration.md#full-ci-and-supported-combinations) before interpreting a workspace CI result.

### Rust and Local Core Development

Keep `opentlv-rust` and `opentlv` as sibling checkouts. From `opentlv-rust`, the local Core source is at `../opentlv`; both repositories are visible in the editor. Bootstrap prepares this layout without changing existing checkouts or configuring dependencies.

Follow the [Rust local workspace guide](https://github.com/OpenTLV/opentlv-rust/blob/main/docs/development/rust.md#local-workspace-development) to build against the sibling Core: it selects the checkout explicitly through the absolute `OPENTLV_CORE_SOURCE` path. That override is for development only; Rust CI and verified builds reject it and use the Core locked in `opentlv-sys/core/core-artifact.json`.

The workspace supplies no Cargo configuration, `[patch]` section, environment variables such as `OPENTLV_CORE_SOURCE` or `OPENTLV_LIB_DIR`, or CMake override. Selecting a local Core checkout belongs to the standalone Rust build contract owned by [`opentlv-rust`](https://github.com/OpenTLV/opentlv-rust). Rust remains buildable through its own Cargo workspace without this workspace or a sibling Core checkout, and Core does not depend on Rust.

### Go and Local Core Development

Keep `opentlv-go` and `opentlv` as sibling checkouts. From `opentlv-go`, the local Core source is at `../opentlv`; opening both roots enables side-by-side editing without selecting a dependency.

The [Go development guide](https://github.com/OpenTLV/opentlv-go/blob/main/docs/development/go.md) owns its build contract. From `opentlv-go`, use:

```sh
python3 scripts/go.py -- build ./...
python3 scripts/go.py --core-source ../opentlv --build-dir build/local -- run ./examples/quick_start
```

The first command uses Go's immutable `core-source.json` dependency; the second explicitly builds against the sibling checkout. Use `python` on Windows with a GCC/MinGW compiler matching Go's target. The helper selects matching native headers and library, disables ambient Go workspaces and records effective Core identity in `core-selection.json`. Opening the editor does not select Core.

The workspace supplies no `go.work`, cgo flags or library paths. Go remains buildable outside this workspace. See the [migration handoff](docs/integration.md#go-migration-handoff) for the required immutable Go pin before hosted Full validation.

### JavaScript and Local Core Development

The [JavaScript build guide](https://github.com/OpenTLV/opentlv-js#standalone-build)
owns the Emscripten 4.0.10 / Node 22 toolchain and Core dependency contract.
From `opentlv-js`, configure a fresh build directory:

```sh
emcmake cmake -S . -B build/sibling -G Ninja -DCMAKE_BUILD_TYPE=Release -DFETCHCONTENT_SOURCE_DIR_OPENTLV_CORE="$PWD/../opentlv"
cmake --build build/sibling --parallel 2
ctest --test-dir build/sibling --output-on-failure
```

Omit the override and use another fresh build directory for the independently
pinned Core. The JS build verifies its source lock or records the explicit local
selection in `core-selection.json`. Opening the workspace does not select Core.
See the [JavaScript migration handoff](docs/integration.md#javascript-migration-handoff)
for the exact integration pins and the bounded runtime/Docs checks.

## Development Documentation

Use each owner's documentation for current prerequisites, build commands, supported capabilities and release status:

- [Core setup](https://github.com/OpenTLV/opentlv/blob/main/docs/getting-started/README.md), [contributing](https://github.com/OpenTLV/opentlv/blob/main/CONTRIBUTING.md) and [development workflow](https://github.com/OpenTLV/opentlv/blob/main/docs/development/workflow.md): Core and in-tree bindings.
- [CLI development](https://github.com/OpenTLV/opentlv-cli/blob/main/docs/development.md) and [command guide](https://github.com/OpenTLV/opentlv-cli/blob/main/docs/README.md): standalone CLI setup and usage.
- [Lua development](https://github.com/OpenTLV/opentlv-lua/blob/main/docs/development.md), [API](https://github.com/OpenTLV/opentlv-lua/blob/main/docs/api.md) and [testing](https://github.com/OpenTLV/opentlv-lua/blob/main/docs/testing.md): standalone Lua setup, usage and CI.
- [Python development](https://github.com/OpenTLV/opentlv-python/blob/main/docs/development/python.md), [usage](https://github.com/OpenTLV/opentlv-python/blob/main/docs/guides/python.md) and [quality gates](https://github.com/OpenTLV/opentlv-python/blob/main/docs/quality-gates.md): standalone Python setup, usage and CI.
- [Rust development](https://github.com/OpenTLV/opentlv-rust/blob/main/docs/development/rust.md), [usage](https://github.com/OpenTLV/opentlv-rust/blob/main/docs/guides/rust.md) and [quality gates](https://github.com/OpenTLV/opentlv-rust/blob/main/docs/quality-gates.md): standalone Rust setup, usage and CI.
- [Docs repository](https://github.com/OpenTLV/opentlv-docs): portal builds, tests and publication.
- [Go development](https://github.com/OpenTLV/opentlv-go/blob/main/docs/development/go.md), [usage](https://github.com/OpenTLV/opentlv-go/blob/main/docs/guides/go.md) and [migration contract](https://github.com/OpenTLV/opentlv-go/blob/main/MIGRATION.md): standalone setup, explicit Core override and source provenance.
- [JS repository](https://github.com/OpenTLV/opentlv-js): standalone build/dependency contract and migration evidence; see the [local workflow](#javascript-and-local-core-development).
- [TestLab repository](https://github.com/OpenTLV/opentlv-testlab): independent differential, cross-language and compatibility testing.

For changes to this workspace repository, see [CONTRIBUTING.md](CONTRIBUTING.md).

Optional contributor tooling is described in [Pre-commit Checks](CONTRIBUTING.md#pre-commit-checks). Bootstrap itself still requires only Python and Git.

## Workspace Integration CI

Four workflows separate PR validation, lightweight Main smoke, manual Full integration and a manual Release Gate. PR checks configuration, formatting, offline bootstrap and orchestration without building components. Main checks configuration and bootstrap on Linux. Full builds CLI and Lua against sibling and remote Core revisions, builds and runs the Rust quick start against Rust's own locked Core in both scenarios, and checks portal assembly/navigation. Go builds its standalone module and runs its quick start using an explicit sibling Core in sibling mode and its own immutable Core pin in remote mode. Python has checkout and documentation coverage; TestLab has checkout coverage only. JS builds with Emscripten 4.0.10 and Node 22, runs its smoke and parse example against explicit sibling or pinned Core, and participates in portal assembly. Release reruns Full on the exact dispatch commit before publishing an attested integration snapshot; component releases remain independent.

[integration.json](integration.json) pins the repository combination used by CI; it does not select component release versions or change bootstrap behavior. See [integration quality gates](docs/integration.md) for supported configurations, local commands, revision evidence, the required merge check and performance measurements.

Maintainers review pins at least monthly and after relevant upstream changes through the [manifest update process](docs/integration.md#maintaining-the-integration-manifest). Passing the pinned combination does not establish compatibility with newer upstream heads.

## Development Principles

- Use native VS Code multi-root workspace functionality.
- Keep `opentlv`, `opentlv-cli`, `opentlv-lua`, `opentlv-python`, `opentlv-rust`, `opentlv-go`, `opentlv-js`, `opentlv-docs`, `.github`, and `opentlv-testlab` independent of the workspace repository.
- Use the build and package tools documented by each component owner.
- Keep build, test, and release workflows with the components they serve.
- Keep build artifacts and local configuration outside version control.

## Security

Report suspected vulnerabilities privately by following the [security policy](SECURITY.md).
It defines the workspace scope, supported revision, and reporting process.

## Code of Conduct

Participation in this project's community is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
It describes community standards and how to report unacceptable behavior privately.

## License

Original project files are licensed under MIT; see [LICENSE](LICENSE).
The adapted Contributor Covenant in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
retains its authors and CC BY 4.0 license. Other contributors retain their own
copyright; automated checks do not assign it to the original author.
