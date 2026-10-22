# Workspace integration quality gates

The workspace validates the development environment and the integration of
independently maintained repositories. It remains optional for building any
component. Opening the editor does not configure or build anything.

## Pull Request CI

[workspace-pr.yml](../.github/workflows/workspace-pr.yml) targets PRs into main and checks:

- Pre-commit configuration, formatting, licensing and syntax on Linux.
- Workspace roots, repository URLs, immutable integration revisions, bootstrap
  consistency and shared settings.
- Offline bootstrap behavior on Linux, Windows and macOS.
- Selection and failure handling in the workspace integration runner.

These checks do not build components. The workspace file currently uses strict
JSON, a subset of VS Code JSONC. Comments require updating both the validator and
the bootstrap test parser. Shared settings are intentionally empty; adding build
settings requires defining and testing their integration contract.

## Main CI

[workspace-main.yml](../.github/workflows/workspace-main.yml) handles pushes to
`main` with **Main smoke** and the aggregate gate. Main smoke
validates workspace configuration and runs offline bootstrap tests on Linux
with Python and Git. It installs no contributor dependencies, clones no
components and performs no native builds. It checks the merged workspace's
configuration and setup behavior; it does not revalidate component compatibility.

## Full CI and supported combinations

[integration.json](../integration.json) identifies the exact Core, CLI, Lua, Python, Rust, Go
and portal revisions selected for integration CI. These are test inputs, not an
ecosystem release version or a replacement for component dependency manifests.
Update pins deliberately and validate both scenarios together.
The initial Core, CLI and Lua pins match the source revisions declared by the
pinned portal. The manifest intentionally does not follow moving main branches.

Python is pinned to initial scaffold `9d612e8ea4b43f3b7dc56b7bc5cc506356be2cbd`.
Both Full scenarios check out this revision and record its repository, configured
and actual commit, and dirty state. The Full and Release gates reject missing,
foreign, changed or dirty Python sources just like other manifest repositories.
The sibling layout exposes Core at `../opentlv` from the Python checkout.
The remote scenario has no sibling Core checkout.

This is checkout coverage only: the old Python pin has no standalone build
configuration, so Full does not build or import it, report a Python Core
dependency, or add it to portal source assembly. The
[current Python development guide](https://github.com/OpenTLV/opentlv-python/blob/main/docs/development/python.md)
owns its standalone build and Core selection contract. Adding Python build/import
smoke and effective Core selection verification requires a separate reviewed
manifest and runner update against that contract. Keep API, packaging and
behavioral tests in the component repository. Current component status does not
change the evidence established by the older workspace pins.

Rust is pinned to `d4ba3ff27ff2a0a5934bdc9cb4bf54019c2274bc`, the final
`opentlv-rust` revision of the
[Rust migration](https://github.com/OpenTLV/opentlv-rust/issues/7). Both Full
scenarios record its checkout identity like the other repositories, then run
`cargo run --locked -p opentlv --example quick_start` with the toolchain set by
`RUSTUP_TOOLCHAIN` (the workflow installs Rust's pinned stable 1.99.1) and a
fresh Cargo target directory in the scenario's work directory. The runner reads
every `core-selection.json` written by the `opentlv-sys` build script and
requires a clean Core resolved inside that target directory at exactly the
commit locked in `opentlv-sys/core/core-artifact.json`. The report records the
quick start output and the effective Rust Core dependency with its declared
lock and selection mode.

Rust uses its locked Core in both scenarios. Its local Core override,
`OPENTLV_CORE_SOURCE`, is development-only and rejected in CI, so the sibling
scenario does not substitute the manifest's Core for Rust; the gate requires
the effective Rust Core to equal the lock and the declared lock to agree across
scenarios. Building Rust against a sibling Core remains a local development
workflow owned by the
[Rust development guide](https://github.com/OpenTLV/opentlv-rust/blob/main/docs/development/rust.md#local-workspace-development).
The pinned portal predates the Rust documentation source, so the workspace
documentation smoke does not assemble Rust manuals; the portal's own CI covers
them. Keep API, FFI, ABI, packaging and behavioral tests in the Rust
repository and Core behavioral tests in Core.

| Scenario | CLI and Lua Core selection | Documentation sources |
| --- | --- | --- |
| `sibling` | Both consumers use the manifest's Core checkout through `FETCHCONTENT_SOURCE_DIR_OPENTLV_CORE`. | Portal preview explicitly selects the same Core, CLI and Lua siblings. |
| `remote` | Each consumer uses its own `cmake/Core.cmake` pin. Installed-package discovery is disabled. | Portal tooling fetches and locks the revisions from its own `docs-sources.json`. |

Full CI currently validates Ubuntu 24.04, Ninja, Release, static Core and Lua 5.4.
CLI and Lua use separate build trees because their Core options differ.
Bootstrap remains tested on three platforms; this does not claim native
integration validation on all three. Shared libraries, installed packages, other
Lua ABIs and compiler matrices remain component-owned coverage.

The runner checks that the selected Core source appears in the compiler commands
and that remote fallback resolves the exact declared commit. It verifies CLI
startup and a small fixed-format input, loads the freshly built Lua module, runs
the Rust quick start against its locked Core, and assembles portal sources and
navigation through portal-owned functions.
It does not run CTest, Busted, Cargo tests, CLI regression suites, Core example
checks, browser tests, Doxygen, a complete site build or deployment.

Different component pins are allowed and reported separately. The sibling
scenario tests one shared Core revision; the remote scenario does not claim that
all consumers use that same revision. Where a consumer also declares a
verified-artifact Core pin, it must agree with the source pin. Artifact metadata
is not required for source-only consumers.

During the initial 2026-10-20 assessment, Core `5e0aae9c`, CLI `4ed2fd05`
and Lua `b4700655` built together, but portal `7e641f1f` omitted their new
`development/quality-gates.md`, `cli/quality-gates.md` and
`lua/quality-gates.md` pages from navigation. That combination fails the
documentation smoke and is not the supported pinned baseline. Fix navigation
in the portal before selecting that newer combination; do not relax the
workspace gate to accept it.

[workspace-full.yml](../.github/workflows/workspace-full.yml) runs only through
manual dispatch or a reusable call from Release Gate. PR and Main workflows do
not trigger Full, regardless of changed paths. Full locks the workspace commit
and manifest, runs both scenarios and validates both reports before its gate
can pass. Standalone Full can run on a candidate branch.

### Go migration handoff

Go Full smoke builds the standalone module and runs `examples/quick_start` through
its component-owned `scripts/go.py` helper with Go 1.22.2. Sibling mode passes
`--core-source` explicitly; remote mode supplies no override and requires the
clean immutable commit from Go's `core-source.json` under the scenario build tree.
The runner verifies the resulting receipt against Git identity and actual native
compiler commands. The Full/Release gate requires Go output, checkout and Core
provenance in both scenarios; it rejects missing or mismatched evidence.

The source transfer preserves the baseline public API, cgo bridge and module path.
Standalone module renaming/versioning remains Go #4, component CI remains Go #3,
and native behavior stays Core-owned. Workspace smoke does not duplicate Go's
behavioral suite or add `go.work`, cgo settings or automatic sibling detection.

**Merge prerequisite:** the current `integration.json` Go pin `5366306` is the
original scaffold. The prepared Go #1/#2 implementation must be committed and
made fetchable first; replace that pin with its exact reviewed commit before
merging this workspace change or running hosted Full. Do not use a moving branch,
claim the scaffold builds, or treat a dirty local checkout as release evidence.
Local smoke may exercise the prepared standalone source independently in both
selection modes, but cannot validate an immutable Go revision that does not yet
exist. The final pin and both hosted scenarios complete workspace #40.

## Release Gate

[workspace-release.yml](../.github/workflows/workspace-release.yml) is manually
dispatched from main with one input: `tag`, in canonical `vMAJOR.MINOR.PATCH`
format. A workspace version identifies a verified integration snapshot.
It does not synchronize component versions or publish component binaries.

The gate:

1. Requires the exact dispatch commit and workflow revision, a clean checkout
   on main, an absent tag/release and a dated, nonempty closed changelog section
   for the requested version. An optional Unreleased section must be empty.
2. Locks the bytes of `integration.json` and every repository revision it selects.
3. Calls Full locally in the same workflow run and attempt, on that exact SHA.
4. Requires successful preflight and both Full scenarios, including the Full
   aggregate, with matching source, manifest, run, attempt and workflow identity.
5. Archives tracked workspace files at that commit and creates
   `release-manifest.json`, `integration-evidence.json` and `SHA256SUMS`.
   The manifest records every selected repository revision; the evidence
   records effective remote dependencies and portal source revisions.
6. Creates GitHub Artifact Attestations for all four assets in an assembly job
   with no repository write permission.
7. In a separate publication job, recomputes checksums, compares the archive to
   the exact committed tree, revalidates all evidence and same-attempt job
   results, and cryptographically verifies every asset's provenance.
   Verification binds the signer workflow and source commit and checks the
   certificate's run/attempt identity. See
   [GitHub CLI attestation verification](https://cli.github.com/manual/gh_attestation_verify).
8. Creates the workspace tag with a create-only API request, then publishes the
   verified snapshot assets in a GitHub Release.

The output tar contains workspace sources and its locked integration manifest,
not vendored component repositories or component binaries. Component source
identities remain reproducible from the manifest and report.
No downstream workflow is dispatched. Pins cannot change during verification.
A reused report from another run or attempt, including the same commit, fails.

Use **Re-run all jobs** for a retry before publication: rerunning only failed
jobs cannot reuse artifacts from an earlier attempt. Existing tags/releases
are never overwritten. If publication fails after tag creation, the verified
tag remains; investigate and recover deliberately rather than bypassing the
gate or force-moving it.

The implementation does not authorize a release from the current open
changelog. Actual tag creation/publication can wait for the next planned
Workspace release. Hosted OIDC, attestation and publication acceptance remain
unverified until that release; local mocked regressions are not hosted evidence.

## Maintaining the integration manifest

Workspace maintainers own the tested combination in `integration.json`.
Review its distance from upstream development at least monthly, and after
component releases, dependency-contract changes or portal source-pin updates.
This is a maintainer process; no scheduled updater or downstream CI dispatch
is installed.

1. Select candidate Core, CLI, Lua, Python, Rust and portal revisions after reviewing their
   component-owned quality-gate results where available. For Python,
   explicitly record whether coverage is still limited to checkout identity. Resolve refs to full commit SHAs once
   and record the old/new revisions and upstream evidence in an update PR.
2. Check the candidate portal's source manifest and navigation against the
   proposed siblings. Its remote documentation pins and the consumers' remote
   Core pins may differ from the sibling Core; document those differences.
3. Update `integration.json` in a dedicated workspace PR. Changes to this file
   require a manual Full CI run on the candidate branch and both successful
   scenario reports before maintainer approval. This is a review policy;
   PR CI does not launch or enforce that manual run.
4. Review both reports for the exact candidate source commits, effective Core
   dependencies and portal source commits. Link the successful hosted run for
   the PR revision. A successful run of the old baseline is not candidate
   evidence.
5. If integration fails, keep the last validated pins and track the failure in
   the owning component's issue tracker. Link that issue and the failed run in
   the update PR, name the follow-up owner and next review date, and retry after
   the component fix merges. Do not silently drop a component or relax checks.
6. After merge, retain the update PR and its validation evidence as the pin
   history. Main smoke checks the merged workspace setup; it does not replace
   the pre-merge compatibility evidence.

A green pinned run proves only that selected combination. It says nothing
about newer upstream heads. When a monthly review retains the same pins,
record why and the next review date in the tracking issue or update PR so
compatibility work does not remain indefinitely deferred.

## Required merge check

Configure the branch ruleset to require the PR check **Workspace integration
gate**. The other entry points expose **Workspace main gate**, **Workspace full
gate** and **Workspace release gate**. Every aggregate uses `always()` and
requires all its dependencies to succeed; failed, cancelled, missing and
unexpectedly skipped checks fail. Full additionally validates the report
inventory and exact identities.

Repository files define checks but cannot make them required in GitHub branch
settings. Confirm the required PR check and demonstrate a real failure blocking
merge before marking enforcement complete. A green PR validates workspace
contracts, not the complete repository combination.

## Local validation

Fast checks use the contributor environment described in
[CONTRIBUTING.md](../CONTRIBUTING.md#pre-commit-checks):

```sh
python -B scripts/integration.py fast
python -B -m unittest discover -s tests -p test_integration.py -v
python -B -m unittest discover -s tests -p test_quality.py -v
python -B tests/test_bootstrap.py -v
python -m pre_commit run --all-files --show-diff-on-failure
```

Full checks additionally need CMake 3.24+, Ninja, a compatible C/C++ toolchain,
Git, Lua 5.4 and its development headers, and Rust 1.82 or newer through
rustup (CI sets `RUSTUP_TOOLCHAIN=1.99.1`). On Windows, keep the work directory
short: the Rust build clones and builds Core deep inside its Cargo target. Install the small portal assembly
dependency set into an isolated Python environment:

```sh
python -m pip install -r requirements-integration.txt
python -B scripts/integration.py full --mode sibling --work-dir build/sibling --report build/results/sibling.json --lua lua5.4 --lua-include /usr/include/lua5.4
python -B scripts/integration.py full --mode remote --work-dir build/remote --report build/results/remote.json --lua lua5.4 --lua-include /usr/include/lua5.4
```

Each invocation requires a new work directory. It never resets or removes an
existing checkout or build. Without `--source-root`, it creates disposable
checkouts of the manifest revisions, with the history and tags required by
component version metadata. Network access is needed for source
dependencies and the remote documentation scenario.

For side-by-side development with existing sibling repositories:

```sh
python -B scripts/integration.py full --mode sibling --source-root .. --work-dir build/local-sibling --report build/results/local-sibling.json --lua lua5.4 --lua-include /usr/include/lua5.4
```

This explicit mode accepts different HEADs and local changes, records configured
and actual revisions plus dirty state, and marks the report `local_development`.
All manifest repositories, including `opentlv-python` and `opentlv-rust`, must exist under
`--source-root`; bootstrap can create missing siblings.
It never fetches, switches branches or writes build output into those siblings.
Portal output is created from a disposable copy. A local-development report is
not evidence that the pinned CI combination passed.

On Windows, run from an MSVC developer shell and supply `--lua` with the
interpreter path, `--lua-include` with the matching headers and `--lua-library`
with the matching DLL import library. The smoke runner uses Ninja on all hosts.

## Evidence and performance

Each Full CI job uploads an attempt-specific JSON report with source repositories, configured and
actual revisions, dirty state, effective Core dependencies, portal provenance,
tool versions in the command output, per-command times and overall elapsed time.
A failed invocation writes a failed report when execution reached the runner.
Raw integration reports are retained for 14 days. Missing reports fail the
upload step. The Full gate rejects local-development or dirty-workspace reports;
only clean hosted checkouts of the exact selected revision can authorize release.

The previous workflow built no components and duplicated no component tests.
Its three-platform bootstrap matrix is retained because Git and filesystem
behavior differ between platforms. Full CI adds two Linux integration jobs,
without multiplying component compiler, ABI or sanitizer matrices.
Pip downloads and pinned pre-commit environments are cached. Native build trees and source checkouts are fresh to
keep dependency selection observable; cross-run binary reuse is not enabled.
Independent jobs run concurrently, and superseded PR runs are cancelled.

The [baseline timing snapshot](ci-baseline.json) records three successful
pre-alignment main runs: 68, 75 and 76 seconds elapsed (median 75), and
127, 143 and 146 summed job seconds (median 143).
Collect new hosted runs after pushing this change:

```sh
python -B scripts/ci_timings.py --run RUN_ID --output build/ci-after.json
```

Compare the median elapsed time and summed job time for the same event type and
scenario, keeping Main smoke, manual Full, PR validation and Release separate.
For before/after main measurements, report the change in coverage as well:
the old workflow ran pre-commit and three-platform bootstrap; Main smoke now
runs configuration and Linux bootstrap checks.
Elapsed time includes scheduling between jobs; summed job time is not a billing
estimate. The completed-run collector queries the recorded attempt and rejects failed
runs. Each workflow also uploads `--current` timings for named predecessor jobs,
excluding the collecting aggregate itself. That scope is explicitly recorded;
it is not equivalent to completed-run elapsed time. The collector retries
missing metadata six times at five-second intervals, never changes attempts,
and rejects partial or duplicate results. Failed-job timings may be recorded
without granting a passing gate. Use `GH_TOKEN` for authenticated hosted queries.

The new workflows' hosted timings, hosted integration results and required-check
enforcement must be recorded after GitHub execution. Local smoke durations are
not a substitute for a hosted before/after comparison.

## Test ownership

Workspace owns configuration consistency, bootstrap behavior, dependency
selection, integration orchestration and representative combination smoke tests.
Components own unit and integration tests, API behavior, language correctness,
memory safety, sanitizers, fuzzing and mutation testing. The portal owns its
assembly implementation and publication guards; workspace only exercises those
existing contracts with selected repositories.

If a smoke exposes a component bug, put the behavioral regression test in that
component. Add a workspace regression only when the failure concerns workspace
selection, orchestration or reporting.
