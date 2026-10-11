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

## Development Independence

Each OpenTLV repository owns its build system, tests, dependencies, and releases.

The workspace must not become a prerequisite for developing or distributing any OpenTLV component.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
