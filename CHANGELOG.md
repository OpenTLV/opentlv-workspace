# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Corrected the workspace copyright attribution to Marek Cingel, matching the OpenTLV repository. (#11)
- README now reflects the two-repository workspace and current component locations, with clarified setup instructions and links to OpenTLV development documentation. (#9)

### Added

- Optional Python bootstrap script to clone missing workspace repositories over HTTPS or SSH while preserving existing checkouts and reporting destination conflicts. (#13)
- Security policy for workspace configuration, tooling, and workflows, with private reporting guidance and links from the README and contribution guidelines. (#7)
- Code of Conduct based on the OpenTLV community policy, linked from the README and contribution guidelines. (#5)
- Pull request template for workspace changes, with contribution guidance for issue references, validation, and review checklists. (#3)
- Bug and Chore issue forms tailored to the workspace, with blank issues enabled and contribution guidance for choosing a reporting option. (#1)
- Visual Studio Code multi-root workspace configuration (`opentlv.code-workspace`).
- OpenTLV Core folder (`../opentlv`) in the workspace.
- README with prerequisites, setup steps, and the expected directory layout.
- Contribution guidelines.
- Markdownlint configuration and `.gitignore` for local editor and OS files.
