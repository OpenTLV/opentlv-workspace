<!--
SPDX-FileCopyrightText: 2026 Marek Cingel
SPDX-License-Identifier: MIT
-->

# OpenTLV Workspace

OpenTLV Workspace will provide a shared development environment for OpenTLV
repositories. This repository is being set up. Its tooling currently
validates the [managed repository inventory](docs/inventory.md) and the
multi-root editor workspace.

The [repository layout and Python support](docs/layout.md) document
defines where workspace files belong, which Python versions are supported,
and how to set up a clean checkout.

## Development

The [development guide](docs/development.md) describes how to set up a clean
checkout, install the pinned contributor tools, and run the local quality
checks. [Contributor tooling](docs/tooling.md) lists every check and how to
update the tool pins.

## Contributing

For a bug, proposal, or maintenance task, start with the
[issue chooser](https://github.com/OpenTLV/opentlv-workspace/issues/new/choose).
Follow the shared [contribution guidelines] for branch names, commit messages,
pull requests, labels, and changelog entries. The [code of conduct] applies
to project discussions and reviews.

For usage questions, consult the [support guide].
Report a suspected vulnerability privately through the [security policy].

The [repository governance record](docs/governance.md) describes how changes
reach `main` and which GitHub settings maintainers have verified.
Notable changes are listed in the [changelog](CHANGELOG.md).

## License

OpenTLV Workspace is distributed under the [MIT License](LICENSE). Each
file carries SPDX copyright and license metadata, as described in
[licensing metadata](docs/licensing.md).

[contribution guidelines]: https://github.com/OpenTLV/.github/blob/main/CONTRIBUTING.md
[code of conduct]: https://github.com/OpenTLV/.github/blob/main/CODE_OF_CONDUCT.md
[support guide]: https://github.com/OpenTLV/.github/blob/main/SUPPORT.md
[security policy]: https://github.com/OpenTLV/opentlv-workspace/security/policy
