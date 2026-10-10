# Contributing to OpenTLV Workspace

Thank you for your interest in contributing to OpenTLV.

This repository maintains the shared Visual Studio Code development workspace for the OpenTLV ecosystem.

## Scope

Contributions should focus on improving the development experience across independent OpenTLV repositories.

Examples include:

- Updating the multi-root workspace configuration.
- Adding new OpenTLV repositories.
- Improving workspace documentation.
- Maintaining recommended development settings.

Changes to OpenTLV Core, language bindings, or tools should be submitted to their respective repositories.

## Guidelines

1. Prefer native Visual Studio Code functionality.
2. Avoid introducing custom tooling when established solutions exist.
3. Keep workspace configuration portable across operating systems.
4. Use relative paths when referencing sibling repositories.
5. Do not introduce dependencies on the workspace into individual projects.
6. Keep changes minimal and focused.

## Pull Requests

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
