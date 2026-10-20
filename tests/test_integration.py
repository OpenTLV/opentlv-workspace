# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marek Cingel

"""Regressions for workspace selection, dependency identity and merge gates."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import integration


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("integration.json", "opentlv.code-workspace", "requirements-dev.txt",
                     ".pre-commit-config.yaml", ".gitattributes", "requirements-integration.txt",
                     ".github/workflows/ci.yml"):
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
        manifest = integration.load_manifest(self.root)
        del manifest["repositories"]["lua"]
        self.write("integration.json", manifest)
        with self.assertRaises(ValueError):
            integration.validate_workspace(self.root)

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

    def test_full_ci_defaults_to_required(self):
        for paths in ([], ["scripts/bootstrap.py"], ["integration.json"], ["README.md"],
                      ["CONTRIBUTING.md"], [".github/workflows/ci.yml"], ["new-file"],
                      ["CHANGELOG.md", "tests/new_test.py"]):
            with self.subTest(paths=paths):
                self.assertTrue(integration.needs_full(paths))
        self.assertFalse(integration.needs_full(["CHANGELOG.md", "SECURITY.md"]))

    def test_rename_into_editorial_path_still_requires_full_ci(self):
        def git(*args):
            return subprocess.check_output(
                ["git", "-C", str(self.root), "-c", "user.name=Workspace Test",
                 "-c", "user.email=workspace@example.invalid", "-c", "commit.gpgsign=false",
                 *args], stderr=subprocess.STDOUT, text=True).strip()

        git("init")
        (self.root / "integration-script.py").write_text("print('integration')\n", encoding="utf-8")
        git("add", "integration-script.py")
        git("commit", "-m", "Initial integration file")
        before = git("rev-parse", "HEAD")
        (self.root / "integration-script.py").rename(self.root / "SECURITY.md")
        git("add", "-A", "--", "integration-script.py", "SECURITY.md")
        git("commit", "-m", "Move to editorial path")
        paths = integration.changed_paths(before, git("rev-parse", "HEAD"), self.root)
        self.assertEqual(set(paths), {"integration-script.py", "SECURITY.md"})
        self.assertTrue(integration.needs_full(paths))

    def test_gate_fails_closed_on_skips_failures_and_cancellation(self):
        integration.check_gate("success", "success", "true", "success")
        integration.check_gate("success", "success", "false", "skipped")
        for fast, bootstrap, required, full in (
            ("failure", "success", "false", "skipped"),
            ("success", "cancelled", "false", "skipped"),
            ("skipped", "success", "true", "success"),
            ("success", "success", "", "skipped"),
            ("success", "success", "true", "skipped"),
            ("success", "success", "true", "cancelled"),
            ("success", "success", "true", "failure"),
            ("success", "success", "false", "failure"),
        ):
            with self.subTest(fast=fast, bootstrap=bootstrap, required=required, full=full):
                with self.assertRaises(ValueError):
                    integration.check_gate(fast, bootstrap, required, full)

    def test_real_workflow_gate_agrees_with_python_policy(self):
        # The required check deliberately does not execute PR Python code.
        # Exercise its actual shell, including failure/skip combinations.
        import shutil
        import yaml
        if sys.platform == "win32" or not shutil.which("bash"):
            self.skipTest("Workflow shell is exercised on Linux Fast CI")
        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
        script = workflow["jobs"]["integration-gate"]["steps"][0]["run"]
        import os
        for fast, bootstrap, required, full in (
            ("success", "success", "true", "success"),
            ("success", "success", "false", "skipped"),
            ("failure", "success", "false", "skipped"),
            ("success", "cancelled", "true", "success"),
            ("success", "success", "true", "skipped"),
            ("success", "success", "", "skipped"),
            ("success", "success", "true", "failure"),
            ("success", "success", "true", "cancelled"),
        ):
            with self.subTest(fast=fast, bootstrap=bootstrap, required=required, full=full):
                env = dict(os.environ, FAST=fast, BOOTSTRAP=bootstrap,
                           FULL_REQUIRED=required, FULL=full)
                result = subprocess.run(["bash", "-e", "-c", script], env=env,
                                        capture_output=True)
                try:
                    integration.check_gate(fast, bootstrap, required, full)
                    expected = 0
                except ValueError:
                    expected = 1
                self.assertEqual(result.returncode, expected)

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
