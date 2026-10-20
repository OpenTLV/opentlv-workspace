# Workspace integration quality gates

The workspace validates the development environment and the integration of
independently maintained repositories. It remains optional for building any
component. Opening the editor does not configure or build anything.

## Fast CI

Every pull request, push to `main`, and manual run checks:

- Pre-commit configuration, formatting, licensing and syntax on Linux.
- Workspace roots, repository URLs, immutable integration revisions, bootstrap
  consistency and shared settings.
- Offline bootstrap behavior on Linux, Windows and macOS.
- Selection and failure handling in the workspace integration runner.

These checks do not build components. The workspace file currently uses strict
JSON, a subset of VS Code JSONC. Comments require updating both the validator and
the bootstrap test parser. Shared settings are intentionally empty; adding build
settings requires defining and testing their integration contract.

## Full CI and supported combinations

[integration.json](../integration.json) identifies the exact Core, CLI, Lua and
portal revisions selected for integration CI. These are test inputs, not an
ecosystem release version or a replacement for component dependency manifests.
Update pins deliberately and validate both scenarios together.
The initial Core, CLI and Lua pins match the source revisions declared by the
pinned portal. The manifest intentionally does not follow moving main branches.

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
startup and a small fixed-format input, loads the freshly built Lua module, and
assembles portal sources and navigation through portal-owned functions.
It does not run CTest, Busted, CLI regression suites, Core example checks, browser
tests, Doxygen, a complete site build or deployment.

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

Full CI runs after Fast CI on every main push and manual dispatch. On pull
requests it is required by default, including changes to scripts, tests,
workflows, dependency pins, README, CONTRIBUTING and unknown paths. Only an
explicit list of editorial files in `scripts/integration.py` can skip it.
An empty change set also requires Full CI.

## Required merge check

Configure the branch ruleset to require **Workspace integration gate**.
It runs even when dependencies fail or are skipped. It accepts Full CI being
skipped only when the successful selector explicitly classified the change as
editorial. Failure, cancellation, missing selector output and unexpected skips
fail the gate.
GitHub treats a directly skipped job as successful for required-check purposes;
the explicit aggregate check avoids relying on that behavior. See
[GitHub's condition documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-jobs-with-conditions).

Repository files define the check but cannot make it required in GitHub branch
settings. Confirm that setting and a real PR failure before marking merge
enforcement complete. No downstream workflows are dispatched and no binary
release pipeline is introduced.

## Local validation

Fast checks use the contributor environment described in
[CONTRIBUTING.md](../CONTRIBUTING.md#pre-commit-checks):

```sh
python -B scripts/integration.py fast
python -B -m unittest discover -s tests -p test_integration.py -v
python -B tests/test_bootstrap.py -v
python -m pre_commit run --all-files --show-diff-on-failure
```

Full checks additionally need CMake 3.24+, Ninja, a compatible C/C++ toolchain,
Git, Lua 5.4 and its development headers. Install the small portal assembly
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
It never fetches, switches branches or writes build output into those siblings.
Portal output is created from a disposable copy. A local-development report is
not evidence that the pinned CI combination passed.

On Windows, run from an MSVC developer shell and supply `--lua` with the
interpreter path, `--lua-include` with the matching headers and `--lua-library`
with the matching DLL import library. The smoke runner uses Ninja on all hosts.

## Evidence and performance

Each Full CI job uploads a JSON report with source repositories, configured and
actual revisions, dirty state, effective Core dependencies, portal provenance,
tool versions in the command output, per-command times and overall elapsed time.
A failed invocation writes a failed report when execution reached the runner.
Reports are retained for 14 days. Missing reports fail the upload step.

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
scenario, keeping full-integration runs separate from editorial Fast-only PRs.
Elapsed time includes scheduling between jobs; summed job time is not a billing
estimate. The script queries the jobs from the recorded run attempt and rejects
failed runs. Use `GH_TOKEN` only if public API rate limits require it.

The new workflow's hosted timings, hosted integration results and required-check
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
