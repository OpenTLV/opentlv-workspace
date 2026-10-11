# Security Policy

## Scope

This policy covers security concerns in the optional OpenTLV VS Code
workspace, including its configuration, development tooling, and repository
workflows. Examples include unsafe command execution, unintended disclosure
of credentials, or insecure handling of untrusted workspace content.

Vulnerabilities in OpenTLV Core, language bindings, or other components
should be reported according to the security policy of the repository that
owns the component. For OpenTLV Core and the bindings currently included
with it, follow the [OpenTLV security policy](https://github.com/OpenTLV/opentlv/blob/main/SECURITY.md).

## Supported Revision

Security fixes target the latest `main` branch of this repository. Older
commits, tags, and other branches do not receive separate security fixes.
This policy does not define support for releases of OpenTLV components.

## Reporting a Vulnerability

**Please do not disclose vulnerabilities through public GitHub issues,
discussions, or pull requests.**

Report suspected vulnerabilities privately to the responsible maintainer,
Marek Cingel, through the contact information on
<https://github.com/marekcingel>. Mark the report as security-sensitive.

### What to Include

- The affected workspace revision, preferably a commit hash.
- The affected file, configuration, tool, or workflow.
- A description of the vulnerability and its potential impact.
- Minimal reproduction steps or a proof of concept.
- Relevant workspace configuration, operating system, VS Code version,
  and extension or tool versions.
- A suggested mitigation or fix, if available.

Remove credentials and unrelated personal information from logs and
configuration excerpts before sharing them.

### Report Handling

The maintainer will review the report and may request additional information
to reproduce the behavior and assess its impact. Confirmed vulnerabilities
will be addressed on `main`, with fixes and disclosure coordinated with the
reporter where possible.

Reports will be handled privately while they are investigated. Information
will be shared only as needed to investigate, remediate, and coordinate
disclosure. Response and resolution times depend on the severity, complexity,
and maintainer availability; no fixed response time is guaranteed.
