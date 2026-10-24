# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marek Cingel

"""Adversarial evidence, workflow, timing and release publication regressions."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ci_timings
import quality
import release
import yaml


def fixture():
    ctx = {"repository": quality.REPOSITORY, "run_id": "123", "run_attempt": "2",
           "sha": "a" * 40, "workflow_sha": "a" * 40, "event_name": "workflow_dispatch",
           "ref": "refs/heads/main",
           "workflow_ref": f"{quality.REPOSITORY}/{quality.RELEASE_WORKFLOW}@refs/heads/main"}
    locked = {"schema": 1, "execution": ctx, "manifest_sha256": "b" * 64,
              "integration": quality.load_manifest()}
    repos = locked["integration"]["repositories"]
    reports = {}
    for mode in ("sibling", "remote"):
        reports[mode] = {
            "schema": 2, "status": "passed", "mode": mode, "execution": copy.deepcopy(ctx),
            "local_development": False, "workspace_dirty": False, "workspace_commit": ctx["sha"],
            "manifest_sha256": locked["manifest_sha256"],
            "checks": dict.fromkeys(("cli", "lua", "rust", "go", "documentation"), "passed"),
            "steps": [{"returncode": 0}], "seconds": 1.0,
            "cli_version": "otlv fixture", "lua_version": "Lua fixture",
            "rust_output": "Hello, world!",
            "go_output": "Hello, world!",
            "tools": dict.fromkeys(("git", "cmake", "ninja", "lua", "cargo", "rustc", "go"), "fixture"),
            "sources": {key: {"repository": item["repository"], "commit": item["revision"],
                              "configured_revision": item["revision"], "dirty": False}
                        for key, item in repos.items() if mode == "sibling" or key != "core"},
            "core_dependencies": {
                key: {"repository": repos["core"]["repository"], "mode": mode,
                      "declared_pin": "c" * 40, "dirty": False,
                      "commit": repos["core"]["revision"] if mode == "sibling" else "c" * 40}
                for key in ("cli", "lua", "go")} | {
                "rust": {"repository": repos["core"]["repository"], "mode": mode,
                         "declared_pin": "e" * 40, "dirty": False, "commit": "e" * 40}},
            "documentation": {"sources": [
                {"id": key, "repository": repos[key]["repository"], "included": True, "dirty": False,
                 "commit": repos[key]["revision"], "revision": repos[key]["revision"]}
                for key in quality.DOCUMENTATION_COMPONENTS]},
        }
    return {"schema": 1, "request": locked, "reports": reports}


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.evidence = fixture()
        self.locked = self.evidence["request"]

    def test_valid_combination(self):
        quality.validate_execution(self.locked["execution"])
        quality.validate_evidence(self.evidence, self.locked)

    def test_reject_wrong_workflow_event_repository_and_commit(self):
        for key, value in (("workflow_ref", "other"), ("repository", "other/workspace"),
                           ("workflow_sha", "d" * 40), ("run_attempt", "0"),
                           ("event_name", "push"), ("ref", "refs/tags/v1.0.0")):
            ctx = dict(self.locked["execution"], **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                quality.validate_execution(ctx)

    def test_missing_or_extra_scenario(self):
        for mode in ("missing", "extra"):
            evidence = copy.deepcopy(self.evidence)
            if mode == "missing":
                del evidence["reports"]["remote"]
            else:
                evidence["reports"]["another"] = evidence["reports"]["sibling"]
            with self.assertRaises(ValueError):
                quality.validate_evidence(evidence, self.locked)

    def test_failed_dirty_local_missing_checks_or_wrong_manifest(self):
        for key, value in (("status", "failed"), ("mode", "remote"), ("schema", 1),
                           ("workspace_dirty", True), ("local_development", True),
                           ("manifest_sha256", "c" * 64), ("workspace_commit", "d" * 40),
                           ("checks", {"cli": "passed"}), ("steps", []),
                           ("steps", [{"returncode": 1}]), ("seconds", 0)):
            report = copy.deepcopy(self.evidence["reports"]["sibling"])
            report[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                quality.validate_report(report, "sibling", self.locked)

    def test_stale_attempt_same_commit_is_rejected(self):
        for key, value in (("run_attempt", "1"), ("run_id", "122"),
                           ("workflow_ref", "another-workflow")):
            report = copy.deepcopy(self.evidence["reports"]["sibling"])
            report["execution"][key] = value
            with self.assertRaises(ValueError):
                quality.validate_report(report, "sibling", self.locked)

    def test_wrong_sources_and_core_dependencies(self):
        for section, key, field, value in (
            ("sources", "cli", "commit", "d" * 40),
            ("sources", "lua", "dirty", True),
            ("sources", "docs", "repository", "https://github.com/other/portal"),
            ("sources", "python", "commit", "d" * 40),
            ("sources", "python", "configured_revision", "d" * 40),
            ("sources", "python", "repository", "https://github.com/other/opentlv-python"),
            ("sources", "python", "dirty", True),
            ("sources", "rust", "commit", "d" * 40),
            ("sources", "rust", "configured_revision", "d" * 40),
            ("sources", "rust", "repository", "https://github.com/other/opentlv-rust"),
            ("sources", "rust", "dirty", True),
            ("core_dependencies", "cli", "commit", "d" * 40),
            ("core_dependencies", "lua", "declared_pin", "main"),
            ("core_dependencies", "lua", "mode", "remote"),
            ("core_dependencies", "rust", "commit",
             quality.load_manifest()["repositories"]["core"]["revision"]),
            ("core_dependencies", "rust", "dirty", True),
            ("core_dependencies", "rust", "repository", "https://github.com/other/opentlv.git"),
        ):
            report = copy.deepcopy(self.evidence["reports"]["sibling"])
            report[section][key][field] = value
            with self.subTest(section=section, key=key, field=field), self.assertRaises(ValueError):
                quality.validate_report(report, "sibling", self.locked)

    def test_standalone_checkouts_required_in_both_scenarios(self):
        for key in ("python", "rust", "go", "js"):
            for mode in ("sibling", "remote"):
                report = copy.deepcopy(self.evidence["reports"][mode])
                del report["sources"][key]
                with self.subTest(key=key, mode=mode), self.assertRaises(ValueError):
                    quality.validate_report(report, mode, self.locked)

    def test_scaffold_runtime_success_is_not_part_of_checkout_coverage(self):
        for key in ("python", "js"):
            for mode in ("sibling", "remote"):
                for section in ("checks", "core_dependencies"):
                    report = copy.deepcopy(self.evidence["reports"][mode])
                    report[section][key] = "passed"
                    with self.subTest(key=key, mode=mode, section=section), \
                            self.assertRaises(ValueError):
                        quality.validate_report(report, mode, self.locked)

    def test_js_checkout_identity_required_in_both_scenarios(self):
        for mode in ("sibling", "remote"):
            for field, value in (("commit", "f" * 40), ("configured_revision", "f" * 40),
                                 ("repository", "https://github.com/other/opentlv-js.git"),
                                 ("dirty", True)):
                report = copy.deepcopy(self.evidence["reports"][mode])
                report["sources"]["js"][field] = value
                with self.subTest(mode=mode, field=field), self.assertRaises(ValueError):
                    quality.validate_report(report, mode, self.locked)

    def test_go_checkout_identity_required_in_both_scenarios(self):
        for mode in ("sibling", "remote"):
            for field, value in (("commit", "d" * 40), ("configured_revision", "d" * 40),
                                 ("repository", "https://github.com/other/opentlv-go.git"),
                                 ("dirty", True)):
                report = copy.deepcopy(self.evidence["reports"][mode])
                report["sources"]["go"][field] = value
                with self.subTest(mode=mode, field=field), self.assertRaises(ValueError):
                    quality.validate_report(report, mode, self.locked)

    def test_go_runtime_and_effective_core_are_required(self):
        for mode in ("sibling", "remote"):
            for change in ("check", "dependency", "commit", "dirty", "output", "tool"):
                report = copy.deepcopy(self.evidence["reports"][mode])
                if change == "check":
                    del report["checks"]["go"]
                elif change == "dependency":
                    del report["core_dependencies"]["go"]
                elif change == "commit":
                    report["core_dependencies"]["go"]["commit"] = "f" * 40
                elif change == "dirty":
                    report["core_dependencies"]["go"]["dirty"] = True
                elif change == "output":
                    report["go_output"] = " "
                else:
                    del report["tools"]["go"]
                with self.subTest(mode=mode, change=change), self.assertRaises(ValueError):
                    quality.validate_report(report, mode, self.locked)

    def test_rust_smoke_and_core_lock_are_required_in_both_scenarios(self):
        for mode in ("sibling", "remote"):
            for change in ("check", "dependency", "output", "tool"):
                report = copy.deepcopy(self.evidence["reports"][mode])
                if change == "check":
                    del report["checks"]["rust"]
                elif change == "dependency":
                    del report["core_dependencies"]["rust"]
                elif change == "output":
                    report["rust_output"] = " "
                else:
                    del report["tools"]["rustc"]
                with self.subTest(mode=mode, change=change), self.assertRaises(ValueError):
                    quality.validate_report(report, mode, self.locked)

    def test_scenarios_must_declare_the_same_rust_core_lock(self):
        evidence = copy.deepcopy(self.evidence)
        item = evidence["reports"]["remote"]["core_dependencies"]["rust"]
        item["declared_pin"] = item["commit"] = "f" * 40
        with self.assertRaises(ValueError):
            quality.validate_evidence(evidence, self.locked)

    def test_missing_dirty_duplicate_or_moving_docs_sources(self):
        for field, value in (("dirty", True), ("included", False), ("commit", "d" * 40),
                             ("revision", "main"), ("id", "cli")):
            report = copy.deepcopy(self.evidence["reports"]["remote"])
            report["documentation"]["sources"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                quality.validate_report(report, "remote", self.locked)

    def test_all_documentation_sources_are_required_in_both_scenarios(self):
        for mode in ("sibling", "remote"):
            for key in quality.DOCUMENTATION_COMPONENTS:
                for change in ("missing", "duplicate", "dirty", "wrong_commit", "wrong_repository"):
                    report = copy.deepcopy(self.evidence["reports"][mode])
                    sources = report["documentation"]["sources"]
                    item = next(item for item in sources if item["id"] == key)
                    if change == "missing":
                        sources.remove(item)
                    elif change == "duplicate":
                        sources.append(copy.deepcopy(item))
                    elif change == "dirty":
                        item["dirty"] = True
                    elif change == "wrong_commit":
                        item["commit"] = "f" * 40
                    else:
                        item["repository"] = "https://github.com/other/component"
                    with self.subTest(mode=mode, key=key, change=change), self.assertRaises(ValueError):
                        quality.validate_report(report, mode, self.locked)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.evidence = fixture()
        self.selected = {"schema": 1, "tag": "v1.2.3", "lock": self.evidence["request"]}

    def assembled(self):
        output = self.root / "payload"
        with patch.object(release, "preflight", return_value=self.selected), \
                patch.object(release, "verify_jobs"), \
                patch.object(release, "snapshot_bytes", return_value=b"workspace archive"):
            release.assemble(self.selected, self.evidence, output)
        return output

    def validate(self, directory):
        with patch.object(release, "preflight", return_value=self.selected), \
                patch.object(release, "snapshot_bytes", return_value=b"workspace archive"):
            return release.validate_payload(directory, "v1.2.3")

    def test_closed_changelog_and_canonical_tag(self):
        text = "# Changelog\n\n## [1.2.3] - 2026-01-01\n\n### Added\n\n- Snapshot.\n"
        release.closed_changelog(text, "v1.2.3")
        release.closed_changelog(text.replace("## [1", "## [Unreleased]\n\n## [1"), "v1.2.3")
        for tag in ("1.2.3", "v01.2.3", "v1.2", "v1.2.3/evil", "v2.0.0"):
            with self.assertRaises(ValueError):
                release.closed_changelog(text, tag)
        for bad in (text.replace("- Snapshot.", ""), text.replace("2026-01-01", "2999-01-01"),
                    text.replace("## [1", "## [Unreleased]\n- Pending.\n\n## [1"),
                    text.replace("2026-01-01", "2026-02-30")):
            with self.assertRaises(ValueError):
                release.closed_changelog(bad, "v1.2.3")

    def test_absence_only_accepts_404(self):
        with patch.object(ci_timings, "get", side_effect=HTTPError("", 404, "", {}, None)):
            release.absent("/example")
        with patch.object(ci_timings, "get", return_value={}):
            with self.assertRaises(ValueError):
                release.absent("/example")
        for status in (403, 500):
            with patch.object(ci_timings, "get", side_effect=HTTPError("", status, "", {}, None)):
                with self.assertRaises(HTTPError):
                    release.absent("/example")

    def test_release_api_workflow_identity_and_required_job_inventory(self):
        metadata = {"id": 123, "run_attempt": 2, "repository": {"full_name": quality.REPOSITORY},
                    "head_sha": "a" * 40, "event": "workflow_dispatch", "path": quality.RELEASE_WORKFLOW}
        with patch.object(ci_timings, "get", return_value=metadata), \
                patch.object(ci_timings, "completed_jobs") as jobs:
            release.verify_jobs(self.selected, assembled=True)
            self.assertEqual(jobs.call_args.args[1], release.FULL_JOBS + ["Assemble snapshot"])
            self.assertTrue(jobs.call_args.kwargs["successful"])
        for key, value in (("id", 122), ("run_attempt", 1), ("head_sha", "d" * 40),
                           ("event", "push"), ("path", quality.FULL_WORKFLOW),
                           ("repository", {"full_name": "other/workspace"})):
            with patch.object(ci_timings, "get", return_value=dict(metadata, **{key: value})), \
                    patch.object(ci_timings, "completed_jobs") as jobs:
                with self.assertRaises(ValueError):
                    release.verify_jobs(self.selected)
                jobs.assert_not_called()

    def test_full_request_rejects_changes_in_pins_or_attempt(self):
        locked = self.selected["lock"]
        for mutate in ("attempt", "manifest", "revision"):
            changed = copy.deepcopy(locked)
            if mutate == "attempt":
                changed["execution"]["run_attempt"] = "1"
            elif mutate == "manifest":
                changed["manifest_sha256"] = "c" * 64
            else:
                changed["integration"]["repositories"]["core"]["revision"] = "d" * 40
            with patch.object(quality, "request", return_value=locked):
                with self.assertRaises(ValueError):
                    quality.validate_request(changed)

    def test_payload_round_trip_and_modified_snapshot(self):
        output = self.assembled()
        self.assertEqual(self.validate(output), self.selected)
        (output / "opentlv-workspace-v1.2.3.tar").write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            self.validate(output)

    def test_checksums_reject_traversal_duplicates_and_missing_files(self):
        output = self.assembled()
        sums = output / "SHA256SUMS"
        original = sums.read_text()
        for text in (original + original, "", original.replace("release-manifest", "../release-manifest")):
            sums.write_text(text)
            with self.assertRaises(ValueError):
                self.validate(output)
        sums.write_text(original)
        (output / "extra").write_text("not allowed")
        with self.assertRaises(ValueError):
            self.validate(output)

    def test_recomputed_checksums_do_not_hide_changed_snapshot(self):
        output = self.assembled()
        snapshot = output / "opentlv-workspace-v1.2.3.tar"
        snapshot.write_bytes(b"another committed archive")
        manifest = quality.read(output / "release-manifest.json")
        manifest["snapshot"]["sha256"] = quality.digest(snapshot)
        quality.write(output / "release-manifest.json", manifest)
        (output / "SHA256SUMS").write_text("".join(
            f"{quality.digest(p)}  {p.name}\n" for p in sorted(output.iterdir()) if p.name != "SHA256SUMS"))
        with self.assertRaises(ValueError):
            self.validate(output)

    def attestation(self, path):
        ctx = self.selected["lock"]["execution"]
        cert = {
            "runInvocationURI": f"https://github.com/{quality.REPOSITORY}/actions/runs/123/attempts/2",
            "buildSignerURI": f"https://github.com/{ctx['workflow_ref']}",
            "buildSignerDigest": ctx["sha"], "sourceRepositoryDigest": ctx["sha"],
            "sourceRepositoryURI": f"https://github.com/{quality.REPOSITORY}",
            "sourceRepositoryRef": "refs/heads/main", "buildTrigger": "workflow_dispatch"}
        return [{"verificationResult": {"signature": {"certificate": cert}, "statement": {
            "predicateType": "https://slsa.dev/provenance/v1",
            "subject": [{"digest": {"sha256": quality.digest(path)}}]}}}]

    def test_attestation_requires_signed_same_attempt_and_workflow(self):
        path = self.root / "asset"
        path.write_text("snapshot")
        result = self.attestation(path)
        release.check_attestation(result, path, self.selected)
        for key in result[0]["verificationResult"]["signature"]["certificate"]:
            bad = copy.deepcopy(result)
            bad[0]["verificationResult"]["signature"]["certificate"][key] = "different"
            with self.subTest(key=key), self.assertRaises(ValueError):
                release.check_attestation(bad, path, self.selected)
        path.write_text("changed")
        with self.assertRaises(ValueError):
            release.check_attestation(result, path, self.selected)
        with self.assertRaises(ValueError):
            release.check_attestation([], path, self.selected)

    def test_publication_requires_all_checks_before_tag_mutation(self):
        for failing in ("validate_payload", "verify_jobs", "verify_attestations", "absent"):
            with patch.object(release, "validate_payload", return_value=self.selected) as payload, \
                    patch.object(release, "verify_jobs") as jobs, \
                    patch.object(release, "verify_attestations") as attestation, \
                    patch.object(release, "absent") as absent, \
                    patch.object(release, "create_tag") as tag, patch.object(release, "run") as publish:
                {"validate_payload": payload, "verify_jobs": jobs, "verify_attestations": attestation,
                 "absent": absent}[failing].side_effect = ValueError("rejected")
                with self.assertRaises(ValueError):
                    release.publish(self.root, "v1.2.3")
                tag.assert_not_called()
                publish.assert_not_called()

    def test_successful_publication_order_and_create_only_failure(self):
        order = []
        with patch.object(release, "validate_payload", return_value=self.selected), \
                patch.object(release, "verify_jobs", side_effect=lambda *a, **kw: order.append("jobs")), \
                patch.object(release, "verify_attestations", side_effect=lambda *a: order.append("attest")), \
                patch.object(release, "absent"), \
                patch.object(release, "create_tag", side_effect=lambda *a: order.append("tag")), \
                patch.object(release, "run", side_effect=lambda *a: order.append("release")):
            release.publish(self.root, "v1.2.3")
        self.assertEqual(order, ["jobs", "attest", "tag", "release"])
        with patch.object(release, "validate_payload", return_value=self.selected), \
                patch.object(release, "verify_jobs"), patch.object(release, "verify_attestations"), \
                patch.object(release, "absent"), \
                patch.object(release, "create_tag", side_effect=ValueError("existing tag")), \
                patch.object(release, "run") as publish:
            with self.assertRaises(ValueError):
                release.publish(self.root, "v1.2.3")
            publish.assert_not_called()

    def test_real_archive_contains_committed_manifest_not_dirty_worktree(self):
        def git(*args):
            return subprocess.check_output(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", *args], cwd=self.root, text=True).strip()
        git("init")
        (self.root / ".gitattributes").write_bytes(b"* text eol=lf\n")
        (self.root / "integration.json").write_bytes(b'{"pinned": true}\n')
        git("add", ".gitattributes", "integration.json")
        git("commit", "-m", "Fixture")
        self.selected["lock"]["execution"]["sha"] = git("rev-parse", "HEAD")
        with patch.object(release, "ROOT", self.root):
            first = release.snapshot_bytes(self.selected)
            (self.root / "integration.json").write_text('{"pinned": false}\n')
            self.assertEqual(first, release.snapshot_bytes(self.selected))
        import io
        import tarfile
        with tarfile.open(fileobj=io.BytesIO(first)) as archive:
            self.assertEqual(archive.extractfile(
                "opentlv-workspace-v1.2.3/integration.json").read(), b'{"pinned": true}\n')


class TimingTests(unittest.TestCase):
    def setUp(self):
        self.ctx = fixture()["request"]["execution"]
        self.job = {"name": "Required", "run_id": 123, "run_attempt": 2, "head_sha": "a" * 40,
                    "status": "completed", "conclusion": "success",
                    "started_at": "2026-01-01T00:00:00Z", "completed_at": "2026-01-01T00:01:00Z"}

    def test_delayed_metadata_retries_same_attempt(self):
        with patch.object(ci_timings, "attempt_jobs", side_effect=[[], [self.job]]) as query, \
                patch.object(ci_timings.time, "sleep") as sleep:
            self.assertEqual(ci_timings.completed_jobs(self.ctx, ["Required"]), [self.job])
            self.assertEqual(query.call_args_list[0], query.call_args_list[1])
            sleep.assert_called_once_with(5)

    def test_missing_partial_or_duplicate_jobs_fail_after_bounded_retry(self):
        for jobs in ([], [self.job, self.job], [dict(self.job, status="in_progress")]):
            with patch.object(ci_timings, "attempt_jobs", return_value=jobs) as query, \
                    patch.object(ci_timings.time, "sleep"):
                with self.assertRaises(ValueError):
                    ci_timings.completed_jobs(self.ctx, ["Required"])
                self.assertEqual(query.call_count, 6)

    def test_stale_attempt_wrong_commit_and_failed_required_jobs(self):
        for key, value in (("run_attempt", 1), ("run_id", 122), ("head_sha", "d" * 40),
                           ("conclusion", "failure"), ("conclusion", "skipped"),
                           ("conclusion", "cancelled")):
            with patch.object(ci_timings, "attempt_jobs", return_value=[dict(self.job, **{key: value})]):
                with self.assertRaises(ValueError):
                    ci_timings.completed_jobs(self.ctx, ["Required"], successful=True)

    def test_paginated_attempt_metadata(self):
        with patch.object(ci_timings, "get", side_effect=[{"jobs": [self.job] * 100}, {"jobs": []}]) as get:
            self.assertEqual(len(ci_timings.attempt_jobs("123", "2")), 100)
            self.assertIn("/attempts/2/jobs?per_page=100&page=2", get.call_args.args[0])

    def test_pr_timings_bind_api_head_and_record_tested_merge_separately(self):
        env = {"GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "2", "GITHUB_SHA": "b" * 40,
               "GITHUB_EVENT_NAME": "pull_request", "TIMING_HEAD_SHA": "a" * 40}
        run = {"id": 123, "run_attempt": 2, "head_sha": "a" * 40, "event": "pull_request",
               "html_url": "run", "run_started_at": self.job["started_at"]}
        with patch.dict(os.environ, env), patch.object(ci_timings, "get", return_value=run), \
                patch.object(ci_timings, "completed_jobs",
                             return_value=[dict(self.job, html_url="job")]) as jobs:
            result = ci_timings.current(["Required"])
            self.assertEqual(jobs.call_args.args[0]["sha"], "a" * 40)
            self.assertEqual(result["commit"], "a" * 40)
            self.assertEqual(result["checkout_commit"], "b" * 40)
            self.assertEqual(result["job_seconds"], 60)


class WorkflowTests(unittest.TestCase):
    def test_triggers_ownership_and_privilege_boundaries(self):
        workflows = {tier: yaml.safe_load(
            (ROOT / f".github/workflows/workspace-{tier}.yml").read_text())
            for tier in ("pr", "main", "full", "release")}
        # PyYAML's YAML 1.1 loader treats the Actions "on" key as True.
        self.assertEqual(set(workflows["pr"][True]), {"pull_request"})
        self.assertEqual(set(workflows["main"][True]), {"push"})
        self.assertEqual(set(workflows["full"][True]), {"workflow_dispatch", "workflow_call"})
        self.assertEqual(set(workflows["release"][True]), {"workflow_dispatch"})
        self.assertEqual(set(workflows["release"][True]["workflow_dispatch"]["inputs"]), {"tag"})
        for tier in ("pr", "main"):
            text = json.dumps(workflows[tier])
            self.assertNotIn("workspace-full.yml", text)
            self.assertNotIn("integration.py full", text)
        self.assertEqual(workflows["release"]["jobs"]["full"]["uses"],
                         "./.github/workflows/workspace-full.yml")
        self.assertEqual(workflows["full"]["jobs"]["integration"]["strategy"]["matrix"]["mode"],
                         ["sibling", "remote"])
        jobs = workflows["release"]["jobs"]
        self.assertEqual(jobs["assemble"]["permissions"]["contents"], "read")
        self.assertEqual(jobs["assemble"]["permissions"]["id-token"], "write")
        self.assertEqual(jobs["publish"]["permissions"]["contents"], "write")
        self.assertNotIn("id-token", jobs["publish"]["permissions"])
        self.assertEqual(set(jobs["publish"]["needs"]), {"prepare", "full", "assemble"})
        for workflow in workflows.values():
            self.assertEqual(workflow["permissions"]["contents"], "read")
            self.assertEqual(workflow["jobs"]["gate"]["if"], "always()")


if __name__ == "__main__":
    unittest.main()
