# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marek Cingel

"""Offline bootstrap checks; all Git operations run in system temporary directories."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "scripts"))
import bootstrap


class RepositoryIdentityTests(unittest.TestCase):
    def test_supported_aliases(self):
        for url in (
            "https://github.com/OpenTLV/opentlv.git",
            "https://github.com/opentlv/OpenTLV/",
            "https://github.com:443/OpenTLV/opentlv",
            "git@github.com:OpenTLV/opentlv.git",
            "ssh://git@github.com/OpenTLV/opentlv.git",
            "ssh://git@github.com:22/OpenTLV/opentlv",
        ):
            with self.subTest(url=url):
                self.assertEqual(
                    bootstrap.repository_identity(url), ("github.com", "opentlv", "opentlv")
                )

    def test_other_repositories_and_hosts_are_not_aliases(self):
        for url in (
            "https://github.com/another/opentlv.git",
            "https://github.com/OpenTLV/another.git",
            "https://github.com.example/OpenTLV/opentlv.git",
            "https://github.com@other.example/OpenTLV/opentlv.git",
            "https://github.com:8443/OpenTLV/opentlv.git",
            "ssh://other@github.com/OpenTLV/opentlv.git",
            "https://github.com/OpenTLV/opentlv?other",
            "https://github.com:invalid/OpenTLV/opentlv.git",
            "github.com/opentlv/opentlv",
        ):
            with self.subTest(url=url):
                self.assertNotEqual(
                    bootstrap.repository_identity(url), ("github.com", "opentlv", "opentlv")
                )

    def test_destinations_match_workspace_roots(self):
        config = json.loads((WORKSPACE / "opentlv.code-workspace").read_text(encoding="utf-8"))
        expected = {(WORKSPACE / item["path"]).resolve() for item in config["folders"]}
        expected.remove(WORKSPACE)
        actual = {(WORKSPACE.parent / repo.directory).resolve() for repo in bootstrap.REPOSITORIES}
        self.assertEqual(actual, expected)


@unittest.skipUnless(shutil.which("git"), "Git is required for offline integration tests")
class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="opentlv bootstrap test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "workspace checkout"
        (self.workspace / "scripts").mkdir(parents=True)
        shutil.copy2(WORKSPACE / "scripts/bootstrap.py", self.workspace / "scripts/bootstrap.py")
        shutil.copy2(WORKSPACE / "opentlv.code-workspace", self.workspace / "opentlv.code-workspace")
        self.destination = self.root / "opentlv"
        self.other_cwd = self.root / "unrelated directory"
        self.other_cwd.mkdir()
        self.source = self.root / "source repository"
        self.git = shutil.which("git")
        self.env = os.environ.copy()
        for key in tuple(self.env):
            if key.startswith("GIT_"):
                del self.env[key]
        self.env.update(
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=str(self.root / "gitconfig"),
            GIT_ALLOW_PROTOCOL="file",
            GIT_TERMINAL_PROMPT="0",
        )
        self.repositories = len(bootstrap.REPOSITORIES)
        for index, repo in enumerate(bootstrap.REPOSITORIES):
            source = self.source if index == 0 else self.root / f"source {repo.directory}"
            self.run_git("init", source)
            self.run_git("-C", source, "symbolic-ref", "HEAD", "refs/heads/main")
            (source / "tracked.txt").write_text("initial\n", encoding="utf-8")
            self.run_git("-C", source, "add", "tracked.txt")
            self.run_git(
                "-C", source, "-c", "user.name=Bootstrap Test",
                "-c", "user.email=bootstrap@example.invalid", "commit", "-m", "Initial",
            )
            for url in (repo.https_url, repo.ssh_url):
                self.run_git("config", "--global", "--add", f"url.{source.as_uri()}.insteadOf", url)

    def run_git(self, *args):
        return subprocess.run(
            [self.git, *map(str, args)], cwd=self.root, env=self.env,
            check=True, capture_output=True, text=True, encoding="utf-8",
        ).stdout.strip()

    def run_bootstrap(self, *args, env=None):
        return subprocess.run(
            [sys.executable, "-B", str(self.workspace / "scripts/bootstrap.py"), *args],
            cwd=self.other_cwd, env=self.env if env is None else env,
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )

    def clone(self):
        result = self.run_bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_initial_clone_from_other_directory_with_spaces(self):
        result = self.clone()
        self.assertEqual((self.destination / "tracked.txt").read_text(), "initial\n")
        self.assertIn(f"{self.repositories} cloned, 0 skipped, 0 failed", result.stdout)
        self.assertIn(f'code "{(self.workspace / "opentlv.code-workspace").as_posix()}"', result.stdout)
        self.assertEqual(
            self.run_git("-C", self.destination, "config", "--local", "--get", "remote.origin.url"),
            bootstrap.REPOSITORIES[0].https_url,
        )

    def test_ssh_protocol(self):
        result = self.run_bootstrap("--protocol", "ssh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.run_git("-C", self.destination, "config", "--local", "--get", "remote.origin.url"),
            bootstrap.REPOSITORIES[0].ssh_url,
        )
        result = self.run_bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"0 cloned, {self.repositories} skipped, 0 failed", result.stdout)

    def test_repeat_preserves_branch_index_and_local_changes_without_fetching(self):
        self.clone()
        self.run_git("-C", self.destination, "checkout", "-b", "local-work")
        tracked = self.destination / "tracked.txt"
        tracked.write_text("staged\n", encoding="utf-8")
        self.run_git("-C", self.destination, "add", "tracked.txt")
        tracked.write_text("unstaged\n", encoding="utf-8")
        (self.destination / "untracked.txt").write_text("keep me\n", encoding="utf-8")
        head = self.run_git("-C", self.destination, "rev-parse", "HEAD")
        status = self.run_git("-C", self.destination, "status", "--porcelain")
        index = (self.destination / ".git/index").read_bytes()
        self.source.rename(self.root / "source unavailable")
        result = self.run_bootstrap("--protocol", "ssh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"0 cloned, {self.repositories} skipped, 0 failed", result.stdout)
        self.assertEqual((self.destination / ".git/index").read_bytes(), index)
        self.assertEqual(self.run_git("-C", self.destination, "rev-parse", "HEAD"), head)
        self.assertEqual(self.run_git("-C", self.destination, "branch", "--show-current"), "local-work")
        self.assertEqual(self.run_git("-C", self.destination, "status", "--porcelain"), status)
        self.assertEqual(tracked.read_text(), "unstaged\n")
        self.assertEqual((self.destination / "untracked.txt").read_text(), "keep me\n")

    def test_unrelated_repository_is_preserved(self):
        self.clone()
        self.run_git("-C", self.destination, "remote", "set-url", "origin", "https://github.com/other/project.git")
        config = (self.destination / ".git/config").read_bytes()
        result = self.run_bootstrap()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONFLICT", result.stderr)
        self.assertEqual((self.destination / ".git/config").read_bytes(), config)
        self.assertEqual((self.destination / "tracked.txt").read_text(), "initial\n")

    def test_directory_without_checkout_is_not_reused(self):
        self.destination.mkdir()
        result = self.run_bootstrap()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONFLICT", result.stderr)
        self.assertEqual(list(self.destination.iterdir()), [])

    def test_file_destination_is_preserved(self):
        self.destination.write_text("keep me", encoding="utf-8")
        result = self.run_bootstrap()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONFLICT", result.stderr)
        self.assertEqual(self.destination.read_text(), "keep me")

    def test_populated_directory_is_preserved(self):
        self.destination.mkdir()
        marker = self.destination / "local.txt"
        marker.write_text("local work", encoding="utf-8")
        result = self.run_bootstrap()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONFLICT", result.stderr)
        self.assertEqual(marker.read_text(), "local work")
        self.assertEqual(list(self.destination.iterdir()), [marker])

    def test_linked_worktree_with_detached_head_is_skipped(self):
        self.run_git("-C", self.source, "remote", "add", "origin", bootstrap.REPOSITORIES[0].https_url)
        self.run_git("-C", self.source, "worktree", "add", "--detach", self.destination, "main")
        (self.destination / "tracked.txt").write_text("local work", encoding="utf-8")
        result = self.run_bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 skipped", result.stdout)
        self.assertTrue((self.destination / ".git").is_file())
        self.assertEqual(self.run_git("-C", self.destination, "rev-parse", "--abbrev-ref", "HEAD"), "HEAD")
        self.assertEqual((self.destination / "tracked.txt").read_text(), "local work")

    def test_parent_checkout_is_not_mistaken_for_destination(self):
        self.run_git("init", self.root)
        self.run_git("-C", self.root, "remote", "add", "origin", bootstrap.REPOSITORIES[0].https_url)
        self.destination.mkdir()
        result = self.run_bootstrap()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not the root", result.stderr)

    def test_checkout_without_origin_is_preserved(self):
        self.clone()
        self.run_git("-C", self.destination, "remote", "remove", "origin")
        result = self.run_bootstrap()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONFLICT", result.stderr)
        self.assertEqual(self.run_git("-C", self.destination, "remote"), "")

    def test_clone_failure_is_reported_without_script_cleanup(self):
        self.source.rename(self.root / "source unavailable")
        result = self.run_bootstrap()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Clone failed", result.stderr)
        self.assertIn("Inspect", result.stderr)
        self.assertIn("1 failed", result.stdout)
        self.assertNotIn("Open the workspace:", result.stdout)

    def test_missing_git(self):
        env = dict(self.env, PATH="")
        result = self.run_bootstrap(env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Git was not found", result.stderr)
        self.assertFalse(self.destination.exists())

    def test_invalid_protocol(self):
        result = self.run_bootstrap("--protocol", "ftp")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice", result.stderr)
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
