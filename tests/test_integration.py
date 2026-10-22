# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marek Cingel

"""Regressions for workspace selection, dependency identity and merge gates."""

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import integration

# Components pinned to repository scaffolds: checkout identity only, no build smoke.
SCAFFOLDS = ("python",)
# Standalone components with a sibling Core checkout in the editor layout.
STANDALONE = ("python", "rust")


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("integration.json", "opentlv.code-workspace", "requirements-dev.txt",
                     ".pre-commit-config.yaml", ".gitattributes", "requirements-integration.txt",
                     *(f".github/workflows/workspace-{tier}.yml"
                       for tier in ("pr", "main", "full", "release"))):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())

    def write(self, name, data):
        (self.root / name).write_text(json.dumps(data), encoding="utf-8")

    def test_current_workspace_contract(self):
        integration.validate_workspace(self.root)

    def test_reject_moving_revision_wrong_repository_and_escaping_path(self):
        original = integration.load_manifest(self.root)
        for key, value in (("revision", "main"), ("revision", "1234567"),
                           ("repository", "https://github.com/other/opentlv.git"),
                           ("directory", "../../outside")):
            with self.subTest(key=key, value=value):
                manifest = copy.deepcopy(original)
                manifest["repositories"]["core"][key] = value
                self.write("integration.json", manifest)
                with self.assertRaises(ValueError):
                    integration.load_manifest(self.root)

    def test_reject_missing_component(self):
        original = integration.load_manifest(self.root)
        for key in original["repositories"]:
            manifest = copy.deepcopy(original)
            del manifest["repositories"][key]
            self.write("integration.json", manifest)
            with self.subTest(key=key), self.assertRaises(ValueError):
                integration.validate_workspace(self.root)

    def test_scaffold_core_is_a_sibling_without_shared_build_settings(self):
        config = json.loads((self.root / "opentlv.code-workspace").read_text(encoding="utf-8"))
        roots = {item["name"]: (self.root / item["path"]).resolve()
                 for item in config["folders"]}
        for key in STANDALONE:
            with self.subTest(key=key):
                self.assertEqual(roots[f"opentlv-{key}"].parent / "opentlv", roots["opentlv"])
        self.assertEqual(config["settings"], {})

    def test_reject_scaffold_checkout_configuration_drift(self):
        original = integration.load_manifest(self.root)
        for key in STANDALONE:
            for field, value in (("revision", "main"), ("directory", f"../../opentlv-{key}"),
                                 ("repository", f"https://github.com/other/opentlv-{key}.git")):
                manifest = copy.deepcopy(original)
                manifest["repositories"][key][field] = value
                self.write("integration.json", manifest)
                with self.subTest(key=key, field=field), self.assertRaises(ValueError):
                    integration.validate_workspace(self.root)

    def test_full_records_scaffold_checkouts_without_claiming_runtime_coverage(self):
        manifest = integration.load_manifest(self.root)
        by_directory = {item["directory"]: item for item in manifest["repositories"].values()}
        for mode in ("sibling", "remote"):
            with self.subTest(mode=mode):
                args = SimpleNamespace(work_dir=self.root / mode, source_root=None,
                                       mode=mode, lua="lua5.4")
                runner = Mock()
                runner.report = {"sources": {}, "checks": {}}
                runner.checkout.side_effect = lambda item, parent: parent / item["directory"]
                runner.identity.side_effect = lambda path: {
                    "repository": by_directory[path.name]["repository"],
                    "commit": by_directory[path.name]["revision"], "dirty": False,
                }

                def run(command, **kwargs):
                    if command[0] == sys.executable:
                        output = command[command.index("--output") + 1]
                        output.write_text('{"sources": []}', encoding="utf-8")
                    return "tool version"

                runner.run.side_effect = run
                with patch.object(integration, "component_smoke") as smoke, \
                        patch.object(integration, "rust_smoke") as rust:
                    integration.full(args, runner, manifest)
                self.assertEqual([call.args[1] for call in smoke.call_args_list], ["cli", "lua"])
                rust.assert_called_once()
                self.assertEqual(rust.call_args.args[1], args.work_dir / "sources/opentlv-rust")
                self.assertIn("rustc", runner.report["tools"])
                expected = set(manifest["repositories"]) - ({"core"} if mode == "remote" else set())
                self.assertEqual(set(runner.report["sources"]), expected)
                for key in SCAFFOLDS:
                    self.assertEqual(runner.report["sources"][key]["commit"],
                                     manifest["repositories"][key]["revision"])
                    self.assertNotIn(key, runner.report["checks"])
                    self.assertNotIn(f"--{key}", runner.run.call_args.args[0])

    def write_rust_lock(self, source, commit):
        (source / "opentlv-sys/core").mkdir(parents=True, exist_ok=True)
        self.write(str((source / "opentlv-sys/core/core-artifact.json").relative_to(self.root)),
                   {"schema": 1, "repository": "OpenTLV/opentlv", "version": "0.7.1",
                    "commit": commit, "release_tag": None})

    def write_selection(self, target, name, **overrides):
        selected = {"mode": "pinned-git", "verified": False, "repository": "OpenTLV/opentlv",
                    "commit": "c" * 40, "locked_commit": "c" * 40, "dirty": False,
                    "source_dir": str(target / name / "out/core/source")}
        selected.update(overrides)
        (target / name / "out").mkdir(parents=True, exist_ok=True)
        self.write(str((target / name / "out/core-selection.json").relative_to(self.root)), selected)

    def test_rust_lock_must_be_one_immutable_core_commit(self):
        source = self.root / "rust"
        self.write_rust_lock(source, "c" * 40)
        self.assertEqual(integration.rust_pin(source), "c" * 40)
        for commit in ("main", "C" * 40, None):
            self.write_rust_lock(source, commit)
            with self.subTest(commit=commit), self.assertRaises(ValueError):
                integration.rust_pin(source)

    def test_rust_selection_requires_the_exact_lock_inside_the_target(self):
        target = self.root / "target"
        self.write_selection(target, "a")
        self.assertEqual(integration.rust_selection(target, "c" * 40)["commit"], "c" * 40)
        with self.assertRaises(ValueError):
            integration.rust_selection(target, "d" * 40)
        for overrides in ({"commit": "d" * 40}, {"locked_commit": "d" * 40}, {"dirty": True},
                          {"repository": "other/opentlv"},
                          {"source_dir": str(self.root / "sibling/opentlv")},
                          {"mode": "local-source"}):
            with self.subTest(overrides=overrides):
                shutil.rmtree(target)
                self.write_selection(target, "a")
                self.write_selection(target, "b", **overrides)
                with self.assertRaises(ValueError):
                    integration.rust_selection(target, "c" * 40)
        shutil.rmtree(target)
        with self.assertRaises(ValueError):
            integration.rust_selection(target, "c" * 40)

    def test_rust_smoke_uses_its_lock_in_both_scenarios(self):
        source = self.root / "opentlv-rust"
        self.write_rust_lock(source, "c" * 40)
        for mode in ("sibling", "remote"):
            with self.subTest(mode=mode):
                args = SimpleNamespace(work_dir=self.root / mode, mode=mode)
                runner = Mock()
                runner.report = {"core_dependencies": {}, "checks": {}}

                def run(command, *, cwd, env):
                    self.assertEqual(cwd, source)
                    self.assertEqual(env["CARGO_TARGET_DIR"], str(args.work_dir / "rust"))
                    self.assertNotIn("CARGO_BUILD_TARGET", env)
                    self.assertNotIn("RUSTFLAGS", env)
                    self.write_selection(args.work_dir / "rust", "debug/build/opentlv-sys-1")
                    return "Hello, world!"

                runner.run.side_effect = run
                integration.rust_smoke(runner, source, args, {
                    "CARGO_BUILD_TARGET": "x", "RUSTFLAGS": "-C x", "PATH": "p"})
                self.assertEqual(runner.run.call_args.args[0][:2], ["cargo", "run"])
                dependency = runner.report["core_dependencies"]["rust"]
                self.assertEqual((dependency["commit"], dependency["declared_pin"], dependency["mode"]),
                                 ("c" * 40, "c" * 40, mode))
                self.assertEqual(runner.report["checks"]["rust"], "passed")

    def test_reject_duplicate_root_absolute_path_and_build_settings(self):
        original = json.loads((self.root / "opentlv.code-workspace").read_text(encoding="utf-8"))
        variants = []
        config = copy.deepcopy(original)
        config["folders"][-1] = config["folders"][0]
        variants.append(config)
        config = copy.deepcopy(original)
        config["folders"][1]["path"] = "/tmp/opentlv"
        variants.append(config)
        config = copy.deepcopy(original)
        config["settings"]["cmake.sourceDirectory"] = "../opentlv"
        variants.append(config)
        for variant in variants:
            with self.subTest(variant=variant):
                self.write("opentlv.code-workspace", variant)
                with self.assertRaises(ValueError):
                    integration.validate_workspace(self.root)

    def test_reject_bootstrap_drift(self):
        with patch.object(integration.bootstrap, "REPOSITORIES", ()):
            with self.assertRaises(ValueError):
                integration.validate_workspace(self.root)

    def test_event_selection_keeps_main_light_and_manual_full(self):
        for event in ("push", "pull_request"):
            self.assertFalse(integration.select_full(event))
        for event in ("workflow_dispatch", "workflow_call"):
            self.assertTrue(integration.select_full(event))
        with self.assertRaises(ValueError):
            integration.select_full("unknown")

    def test_gate_fails_closed_on_skips_failures_and_cancellation(self):
        integration.check_gate(["success", "success"])
        for results in ([], ["success", ""], ["success", "skipped"],
                        ["failure", "success"], ["success", "cancelled"]):
            with self.assertRaises(ValueError):
                integration.check_gate(results)

    def test_real_workflow_gate_agrees_with_python_policy(self):
        import os
        import shutil
        import yaml
        if sys.platform == "win32" or not shutil.which("bash"):
            self.skipTest("Workflow shell is exercised on Linux PR CI")
        for tier in ("pr", "main", "full", "release"):
            workflow = yaml.safe_load(
                (ROOT / f".github/workflows/workspace-{tier}.yml").read_text(encoding="utf-8"))
            gate = workflow["jobs"]["gate"]
            self.assertEqual(gate["if"], "always()")
            step = gate["steps"][0]
            passing = dict.fromkeys(step["env"], "success")
            cases = [passing] + [dict(passing, **{key: value})
                                 for key in passing for value in ("failure", "cancelled", "skipped", "")]
            for env in cases:
                with self.subTest(tier=tier, env=env):
                    result = subprocess.run(["bash", "-e", "-c", step["run"]],
                                            env=dict(os.environ, **env), capture_output=True)
                    self.assertEqual(result.returncode, 0 if env == passing else 1)

    def test_source_and_artifact_pins_must_agree(self):
        source = self.root / "cli"
        (source / "cmake").mkdir(parents=True)
        (source / "cmake/Core.cmake").write_text("GIT_TAG " + "a" * 40 + " # baseline\n",
                                                encoding="utf-8")
        self.assertEqual(integration.core_pin(source), "a" * 40)
        artifact = {"repository": "OpenTLV/opentlv", "commit": "a" * 40}
        self.write("cli/cmake/core-artifact.json", artifact)
        self.assertEqual(integration.core_pin(source), "a" * 40)
        artifact["commit"] = "b" * 40
        self.write("cli/cmake/core-artifact.json", artifact)
        with self.assertRaises(ValueError):
            integration.core_pin(source)

    def test_remote_fallback_disables_installed_package_discovery(self):
        args = integration.cmake_arguments("remote")
        self.assertIn("-DFETCHCONTENT_TRY_FIND_PACKAGE_MODE=NEVER", args)
        self.assertFalse(any("FETCHCONTENT_SOURCE_DIR" in arg for arg in args))
        self.assertIn("-DOPENTLV_CLI_BUILD_TESTS=OFF", args)
        self.assertIn("-DOPENTLV_BUILD_LUA_TESTS=OFF", args)
        with self.assertRaises(ValueError):
            integration.cmake_arguments("sibling")

    def test_selected_core_must_appear_in_real_compile_commands(self):
        build = self.root / "build"
        build.mkdir()
        core = self.root / "opentlv"
        self.write("build/compile_commands.json", [{"file": str(core / "tlv/src/reader.c")}])
        integration.assert_core_compiled(build, core)
        with self.assertRaises(ValueError):
            integration.assert_core_compiled(build, self.root / "another-core")

    def test_nonzero_smoke_is_not_success(self):
        report = {"steps": []}
        runner = integration.Runner(report)
        with self.assertRaises(ValueError):
            runner.run([sys.executable, "-c", "print('smoke failed'); raise SystemExit(9)"])
        self.assertEqual(report["steps"][0]["returncode"], 9)
        self.assertIn("smoke failed", report["steps"][0]["output_tail"])

    def test_existing_checkout_is_never_reused_or_reset(self):
        sentinel = self.root / "opentlv" / "keep.txt"
        sentinel.parent.mkdir()
        sentinel.write_text("local changes", encoding="utf-8")
        runner = integration.Runner({"steps": []})
        with self.assertRaises(ValueError):
            runner.checkout(integration.load_manifest(self.root)["repositories"]["core"], self.root)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "local changes")

    def test_checkout_preserves_history_and_tags_for_component_versions(self):
        origin = self.root / "origin"
        origin.mkdir()

        def git(*args):
            return subprocess.check_output(
                ["git", "-C", str(origin), "-c", "user.name=Workspace Test",
                 "-c", "user.email=workspace@example.invalid", "-c", "commit.gpgsign=false",
                 "-c", "tag.gpgsign=false", *args],
                stderr=subprocess.STDOUT, text=True).strip()

        git("init")
        git("commit", "--allow-empty", "-m", "First")
        git("tag", "v0.1.0")
        git("commit", "--allow-empty", "-m", "Second")
        commit = git("rev-parse", "HEAD")
        runner = integration.Runner({"steps": []})
        cloned = runner.checkout({"directory": "consumer", "repository": origin.as_uri(),
                                  "revision": commit}, self.root / "managed")
        self.assertEqual(subprocess.check_output(
            ["git", "-C", str(cloned), "rev-list", "--count", "HEAD"], text=True).strip(), "2")
        self.assertEqual(subprocess.check_output(
            ["git", "-C", str(cloned), "tag", "--list"], text=True).strip(), "v0.1.0")
        self.assertFalse((cloned / ".git/shallow").exists())


if __name__ == "__main__":
    unittest.main()
