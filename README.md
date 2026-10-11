# OpenTLV Workspace

Official Visual Studio Code multi-root workspace for developing the OpenTLV ecosystem.

This repository provides a unified development environment for OpenTLV Core, language bindings, and tools while keeping each project independent.

## Overview

OpenTLV is organized into independent repositories with their own development, testing, and release lifecycles.

The workspace uses native Visual Studio Code functionality to work with multiple repositories in a single editor window.

**The workspace is optional.** Every OpenTLV component can be built, tested, and released independently.

## Prerequisites

- Git
- Visual Studio Code
- Development tools required by the individual repositories

## Getting Started

Clone the workspace repository:

```bash
git clone git@github.com:OpenTLV/opentlv-workspace.git
```

Clone OpenTLV Core into the same parent directory:

```bash
git clone git@github.com:OpenTLV/opentlv.git
```

The resulting directory structure should look like this:

```text
OpenTLV/
├── opentlv/
└── opentlv-workspace/
    └── opentlv.code-workspace
```

Open the workspace:

```bash
code opentlv-workspace/opentlv.code-workspace
```

Additional repositories can be cloned alongside Core and added through **File → Add Folder to Workspace**.

## Repository Structure

The workspace is designed to support the following repositories as they become available:

| Repository | Purpose |
|---|---|
| `opentlv` | C core and C++ API |
| `opentlv-cli` | Command-line tools |
| `opentlv-python` | Python bindings |
| `opentlv-rust` | Rust bindings |
| `opentlv-lua` | Lua bindings |
| `opentlv-go` | Go bindings |

Not all repositories are required to use the workspace.

## Development Principles

- Use native VS Code multi-root workspace functionality.
- Keep repositories independently buildable and testable.
- Use each language ecosystem's established build and package tools.
- Do not introduce dependencies on the workspace into individual projects.
- Keep build artifacts and local configuration outside version control.
- Allow bindings and tools to evolve independently of OpenTLV Core.

## Security

Report suspected vulnerabilities privately by following the [security policy](SECURITY.md).
It defines the workspace scope, supported revision, and reporting process.

## Code of Conduct

Participation in this project's community is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
It describes community standards and how to report unacceptable behavior privately.

## License

This repository is licensed under the MIT License. See [LICENSE](LICENSE) for details.
