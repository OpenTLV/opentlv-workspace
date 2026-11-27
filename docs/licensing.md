<!--
SPDX-FileCopyrightText: 2026 Marek Cingel
SPDX-License-Identifier: MIT
-->

# Licensing metadata

This repository follows the [REUSE Specification 3.3]. Every file states its
copyright holders and license as SPDX tags, and the `reuse` pre-commit hook
rejects files without them. See [contributor tooling](tooling.md) for how to
install and run the hook.

## License

The repository is distributed under the MIT License. `LICENSE` holds the
license notice. `LICENSES/MIT.txt` holds the same text under its SPDX
identifier, as the REUSE Specification requires. Keep the two files
identical.

## File headers

Every file that supports comments carries an SPDX header in its own comment
syntax, followed by a blank line:

```text
# SPDX-FileCopyrightText: 2026 Marek Cingel
# SPDX-License-Identifier: MIT
```

Markdown files use an HTML comment, which GitHub does not render:

```markdown
<!--
SPDX-FileCopyrightText: 2026 Marek Cingel
SPDX-License-Identifier: MIT
-->
```

- Name the actual author or rights holder and the year of the contribution.
  Do not copy the example's name or year onto someone else's work.
- Keep shebang lines and encoding declarations first, with the header
  directly after them.
- When editing a file, keep its existing copyright lines. Add your own
  `SPDX-FileCopyrightText` line for a substantial contribution.
- Contributors keep the copyright in their contributions. An MIT
  contribution does not assign copyright to another person or to the
  OpenTLV organization.

## Files without comment syntax

`REUSE.toml` covers files that cannot carry a header: JSON configuration,
such as `.pymarkdown`, and files that a tool regenerates completely, such as
the uv-generated `requirements-*.txt` locks. It lists each file by its exact
path.

Do not add glob patterns to `REUSE.toml`. A pattern would attribute files
to the listed holders before anyone has written them, and new files without
metadata would pass the check. For a new file that cannot carry a header,
either add its exact path to an annotation that names its actual holders,
or add a `<file>.license` sidecar that contains the SPDX tags. When someone
else substantially changes a listed file, move the path to its own
annotation that lists every holder.

The REUSE Specification exempts `LICENSE`, the texts under `LICENSES/`,
`REUSE.toml`, and `.license` sidecars. Files that Git ignores are not
checked.

## Third-party material

The repository contains no third-party source code, images, or documents.
Before adding any:

1. Confirm that its license permits redistribution and is compatible with
   the MIT License. Do not add material whose redistribution rights are
   unknown.
2. Keep its upstream copyright and license notices unchanged.
3. Add its license text to `LICENSES/` under the SPDX identifier, for
   example `LICENSES/Apache-2.0.txt`.
4. Record its source, revision, and modifications in the pull request and,
   where its license requires, in the files.

Contributor tools are installed from PyPI and are not redistributed here.
Their licenses do not apply to the files they check.

## Checking the metadata

The `reuse` hook runs `reuse lint` on every commit. To run it alone:

```sh
pre-commit run reuse --all-files
```

The check fails when a file lacks copyright or license information, when a
license identifier is invalid or has no text in `LICENSES/`, or when a
license text in `LICENSES/` is unused. It also checks untracked files that
Git does not ignore.

[REUSE Specification 3.3]: https://reuse.software/spec-3.3/
