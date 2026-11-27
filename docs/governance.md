# Repository governance

This record describes how changes reach `main` in OpenTLV/opentlv-workspace
and which GitHub settings maintainers have verified. It applies the
organization [governance baseline] and [adoption guide]. Dated entries are
evidence from the stated day, not a guarantee of current settings.

## Community defaults

The repository inherits the organization's contribution, conduct, security,
and support policies, all five issue forms, and the pull request template.
There are no local overrides. Adding a local community file or any local
`.github/ISSUE_TEMPLATE` content replaces the inherited default, so record
such a change here.

On 2026-11-27, the [community profile] linked the shared code of conduct,
contribution guidelines, and pull request template, and the local README and
license. The repository had no local `.github` directory.

| Issue form | Default in this repository |
| --- | --- |
| Bug report | `bug` label |
| Feature request | `enhancement` label |
| Task | `Task` organization issue type |
| Chore | `chore` label |
| Epic | `Epic` organization issue type |

On 2026-11-27, the [repository labels] included `bug`, `enhancement`,
`chore`, and `documentation`, which the shared forms and contribution
guidelines use. Issue #1 received the `Task` organization issue type. The
remaining GitHub default labels are kept for triage.

## Merging to main

Use a pull request with signed commits and resolve review conversations
before merging. Use a regular merge commit to preserve the branch history.

The `main` ruleset follows the [governance baseline]:

- It targets only `refs/heads/main`, requires signed commits and a pull
  request, permits only merge commits, and blocks force pushes and branch
  deletion.
- The solo-maintainer configuration requires zero approving reviews and
  requires conversation resolution. Code Owner approval, last-push approval,
  and linear history are disabled. The bypass list is empty.
- Required status checks are not configured because the repository has no
  workflows. When project CI first reports on a pull request, verify the
  exact check names and source app IDs, then require the applicable checks
  and an up-to-date branch.

On 2026-11-27, the [ruleset inventory including organization rules] and the
[effective rules for main] were empty. The `main` ruleset is not yet active.
The initial commit `6737439` on `main` had a verified signature.

## Actions and dependency security

| Control | Intended setting | Status on 2026-11-27 |
| --- | --- | --- |
| Allowed actions | Organization policy; actions pinned to full commit SHAs | Unavailable to inspect without authentication |
| Default `GITHUB_TOKEN` | Read access; Actions cannot create or approve pull requests | Unavailable to inspect without authentication |
| Fork workflows | Approval required for external contributors | Unavailable to inspect without authentication |
| Workflows | None until workspace implementation begins | No [workflows] |
| Dependency graph | Enabled | [Dependency graph export] returned |
| Dependabot alerts and security updates | Enabled | Unavailable to inspect without authentication |
| Secret scanning and push protection | Enabled | Unavailable to inspect without authentication |
| Private vulnerability reporting | Enabled | [Private vulnerability reporting] returned `enabled: false` |

Follow the [secret protection procedure] and the [private reporting routes]
when verifying these settings.

## Licensing

The repository is distributed under the [MIT License](../LICENSE) with the
notice `Copyright (c) 2026 Marek Cingel`. Contributors keep the copyright in
their contributions. GitHub detected the license as `MIT` on
2026-11-27. The repository contains no third-party material. Record the
provenance and license of any external material when it is added.

[adoption guide]: https://github.com/OpenTLV/.github/blob/main/docs/adoption.md
[governance baseline]: https://github.com/OpenTLV/.github/blob/main/docs/governance.md
[secret protection procedure]: https://github.com/OpenTLV/.github/blob/main/docs/adoption.md#secret-scanning-and-push-protection
[private reporting routes]: https://github.com/OpenTLV/.github/blob/main/docs/adoption.md#private-reporting-routes-and-verification
[community profile]: https://api.github.com/repos/OpenTLV/opentlv-workspace/community/profile
[repository labels]: https://github.com/OpenTLV/opentlv-workspace/labels
[ruleset inventory including organization rules]: https://api.github.com/repos/OpenTLV/opentlv-workspace/rulesets?includes_parents=true
[effective rules for main]: https://api.github.com/repos/OpenTLV/opentlv-workspace/rules/branches/main
[workflows]: https://api.github.com/repos/OpenTLV/opentlv-workspace/actions/workflows
[Dependency graph export]: https://api.github.com/repos/OpenTLV/opentlv-workspace/dependency-graph/sbom
[Private vulnerability reporting]: https://api.github.com/repos/OpenTLV/opentlv-workspace/private-vulnerability-reporting
