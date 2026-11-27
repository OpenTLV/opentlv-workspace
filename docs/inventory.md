<!--
SPDX-FileCopyrightText: 2026 Marek Cingel
SPDX-License-Identifier: MIT
-->

# Managed repository inventory

[`repositories.toml`](../repositories.toml) at the repository root is the
single authoritative list of the repositories that the workspace manages.
Workspace tools and configuration read their repository list from it and
must not keep a separate one. This document defines the file format, the
meaning and rules of each field, and how to change the inventory.

## Host and managed repositories

The workspace checkout is the host. It is never an inventory entry and
never a clone target. Each managed repository is checked out next to the
host, in the directory that its entry names:

```text
<parent>/
├── <workspace checkout>/   the host, under any directory name
└── <directory>/            one per inventory entry
```

`<parent>` is the directory that contains the host checkout. Tools resolve
entries against it, never against the current working directory, so the
result is the same wherever a command is run from.

The inventory identifies repositories and their checkout directories only.
It does not record branches, revisions, remotes, or build settings.

## File format

The inventory is a [TOML 1.0] document encoded in UTF-8. Python reads it
with the standard library `tomllib` module, so tools need no third-party
packages.

The top level has exactly these keys:

| Key | Type | Rules |
| --- | --- | --- |
| `version` | Integer | Inventory format version. The current version is `1`. |
| `repositories` | Array of tables | One table per managed repository. At least one entry. |

Each entry has exactly these keys, all non-empty strings:

| Key | Meaning | Rules |
| --- | --- | --- |
| `host` | Host name of the Git server | Lowercase DNS host name without a scheme, port, or user name, such as `github.com`. |
| `owner` | Account or organization that owns the repository | ASCII letters, digits, and hyphens. Must not start or end with a hyphen. |
| `name` | Repository name on the host | ASCII letters, digits, `.`, `_`, and `-`. Must not be `.` or `..`, and must not end with `.git`. |
| `directory` | Checkout directory under `<parent>` | See [checkout directory](#checkout-directory). |

Unknown keys, at the top level or in an entry, make the inventory invalid.
A tool rejects the whole file rather than ignoring a key it does not know.

## Repository identity

The `host`, `owner`, and `name` fields together identify a repository, for
example `github.com/OpenTLV/opentlv`. Write each value as the host displays
it. Identities are compared case-insensitively, because host names and
GitHub owner and repository names are case-insensitive. Two entries must not
have the same identity.

The identity does not depend on the transport. The inventory contains no
URLs, and tools derive the remote URL from the identity when they need one:

| Transport | Remote URL |
| --- | --- |
| HTTPS | `https://<host>/<owner>/<name>.git` |
| SSH | `git@<host>:<owner>/<name>.git` |

To check whether an existing checkout belongs to an entry, a tool reduces
its remote URL to an identity first. An HTTPS URL and an SSH URL for the
same repository, with or without the `.git` suffix, have the same identity.

No entry may identify the host repository,
`github.com/OpenTLV/opentlv-workspace`.

## Checkout directory

`directory` is the name of the managed checkout under `<parent>`. It is
usually the repository name, but it is stated explicitly, so tools never
derive it. The value must work as a directory name on Linux, macOS, and
Windows:

- It is a single path component. It contains no `/` or `\`, has no drive
  letter, and is not `.` or `..`.
- It uses only ASCII letters, digits, `.`, `_`, and `-`. It must not start
  with `-`, which Git and other tools could read as an option, and must not
  end with `.`, which Windows removes.
- It is not a Windows reserved device name, such as `CON`, `NUL`, `COM1`, or
  `LPT1`, with or without an extension.
- It is unique among entries when compared case-insensitively, because the
  default file systems on Windows and macOS are case-insensitive.
- It is not `opentlv-workspace`, the default directory name of the host
  checkout. Because the host can be cloned under any name, tools also reject
  an entry whose directory matches the actual host directory,
  case-insensitively.

## Ordering

Entries are sorted in ascending order by `host`, then `owner`, then `name`,
each compared after conversion to lowercase. Within an entry, write the keys
in the order `host`, `owner`, `name`, `directory`. The fixed order keeps
tool output deterministic and inventory changes easy to review. Tools that
report on repositories process them in inventory order.

## Versioning

`version` identifies the set of keys and rules in this document. Adding,
removing, or renaming a key, or changing a rule so that a valid inventory
becomes invalid or changes meaning, requires a new version. A tool rejects a
version it does not support instead of guessing.

## Editor workspace

[`opentlv.code-workspace`](../opentlv.code-workspace) at the repository root
is a multi-root VS Code workspace derived from the inventory. Its `folders`
array contains exactly these roots, in this order:

1. The host, with the name `opentlv-workspace` and the path `.`. The name
   stays the same under any host directory name.
2. One root per inventory entry, in [inventory order](#ordering), with the
   entry's `directory` as the name and `../<directory>` as the path.

VS Code resolves relative paths against the directory that contains the
workspace file, so the roots resolve wherever the host is checked out. The
file is plain JSON without comments, and `folders` is its only key. It
contains no settings, tasks, launch configurations, or extension
recommendations, so it never overrides a component's own build or editor
configuration and holds no machine-specific paths. Keep personal settings in
VS Code user settings.

A managed root whose checkout is missing appears in VS Code as a missing
folder. The other roots still open.

## Changing the inventory

Which repositories the workspace manages is a scope decision. Propose a
change in an issue before editing the inventory. In the pull request:

1. Add, change, or remove the entry in `repositories.toml`, keeping the
   [ordering](#ordering).
2. Update every consumer of the inventory in the same pull request, so no
   configuration lists a different set of repositories. This includes the
   roots of the [editor workspace](#editor-workspace).
3. Record the change in the [changelog](../CHANGELOG.md).
4. Run the [validation](#validation) and fix every reported problem.

## Validation

`scripts/check_inventory.py` checks the inventory against every rule in
this document and checks that the editor workspace lists exactly the roots
that the inventory requires:

```sh
python scripts/check_inventory.py
```

The script uses only the Python standard library, reads only
`repositories.toml` and `opentlv.code-workspace` in the host checkout, and
needs no network access and no managed checkouts. It finds the host
checkout from its own location, so it gives the same result from any
working directory, and it compares entries with the actual host directory
name. Pass `--root <path>` to check another host checkout.

The script prints one line for each problem, naming the file, the entry or
root, and the rule that failed, and reports every problem in one run. The
exit status is `0` if both files are valid, `1` if it finds a problem, and
`2` for a usage error. While the inventory is invalid, the script checks
only the structure of the editor workspace, because the expected roots are
unknown.

The `check-inventory` pre-commit hook runs the script when the inventory,
the editor workspace, or a workspace script changes. See
[contributor tooling](tooling.md#running-the-checks).

[TOML 1.0]: https://toml.io/en/v1.0.0
