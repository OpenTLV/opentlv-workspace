#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marek Cingel


"""Clone missing workspace repositories without updating existing checkouts."""

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Repository:
    directory: str
    https_url: str
    ssh_url: str


REPOSITORIES = (
    Repository(
        directory="opentlv",
        https_url="https://github.com/OpenTLV/opentlv.git",
        ssh_url="git@github.com:OpenTLV/opentlv.git",
    ),
    Repository(
        directory="opentlv-docs",
        https_url="https://github.com/OpenTLV/opentlv-docs.git",
        ssh_url="git@github.com:OpenTLV/opentlv-docs.git",
    ),
    Repository(
        directory="opentlv-cli",
        https_url="https://github.com/OpenTLV/opentlv-cli.git",
        ssh_url="git@github.com:OpenTLV/opentlv-cli.git",
    ),
    Repository(
        directory="opentlv-lua",
        https_url="https://github.com/OpenTLV/opentlv-lua.git",
        ssh_url="git@github.com:OpenTLV/opentlv-lua.git",
    ),
)


def repository_identity(url):
    """Recognize GitHub HTTPS and SSH aliases without accepting other hosts."""
    if url.lower().startswith("git@github.com:"):
        url = "ssh://git@github.com/" + url.split(":", 1)[1]
    try:
        parsed = urlsplit(url)
        if (
            parsed.hostname != "github.com"
            or parsed.scheme not in ("https", "ssh")
            or parsed.query
            or parsed.fragment
            or parsed.port not in (None, 443 if parsed.scheme == "https" else 22)
            or (parsed.scheme == "ssh" and parsed.username != "git")
        ):
            return ("literal", url)
    except ValueError:
        return ("literal", url)
    path = parsed.path.rstrip("/")
    if path.lower().endswith(".git"):
        path = path[:-4]
    parts = path.strip("/").split("/")
    if len(parts) != 2 or any(part in ("", ".", "..") for part in parts):
        return ("literal", url)
    return ("github.com", parts[0].lower(), parts[1].lower())


def run_git(git, *args):
    return subprocess.run(
        [git, *map(str, args)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout.strip()


def check_existing(git, destination, repository):
    if not destination.is_dir():
        raise ValueError("destination exists and is not a directory")
    try:
        root = run_git(git, "-C", destination, "rev-parse", "--show-toplevel")
        if Path(root).resolve() != destination.resolve():
            raise ValueError("destination is not the root of a Git checkout")
        # Read stored URLs, not transport URLs expanded by Git's insteadOf rules.
        origins = run_git(
            git, "-C", destination, "config", "--local", "--get-all", "remote.origin.url"
        ).splitlines()
    except subprocess.CalledProcessError as error:
        raise ValueError("destination is not a Git checkout with an origin remote") from error
    expected = repository_identity(repository.https_url)
    if not origins or any(repository_identity(url) != expected for url in origins):
        raise ValueError("origin does not identify the expected repository")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--protocol",
        choices=("https", "ssh"),
        default="https",
        help="clone transport (default: https); existing checkouts are never updated",
    )
    args = parser.parse_args(argv)
    git = shutil.which("git")
    if git is None:
        print("ERROR: Git was not found. Install Git and add it to PATH.", file=sys.stderr)
        return 1

    workspace = Path(__file__).resolve().parent.parent
    cloned = skipped = failed = 0
    for repository in REPOSITORIES:
        destination = workspace.parent / repository.directory
        if os.path.lexists(destination):
            try:
                check_existing(git, destination, repository)
            except (ValueError, OSError) as error:
                print(
                    f"CONFLICT: {destination}: {error}. "
                    "Inspect the destination and resolve the conflict before retrying.",
                    file=sys.stderr,
                )
                failed += 1
            else:
                print(f"SKIPPED: {destination} (existing checkout left unchanged)")
                skipped += 1
            continue

        url = repository.https_url if args.protocol == "https" else repository.ssh_url
        try:
            # Reserve the missing destination so a concurrently created path is not reused.
            destination.mkdir()
        except OSError as error:
            print(f"ERROR: Cannot create {destination}: {error}", file=sys.stderr)
            failed += 1
            continue
        print(f"CLONING: {url} -> {destination}", flush=True)
        try:
            run_git(git, "clone", "--", url, destination)
        except (OSError, subprocess.CalledProcessError) as error:
            detail = (
                error.stderr.strip()
                if isinstance(error, subprocess.CalledProcessError)
                else str(error)
            )
            print(
                f"ERROR: Clone failed for {destination}: {detail}\n"
                "Check repository access and network connectivity. "
                f"Inspect {destination} before retrying; no cleanup is performed by this script.",
                file=sys.stderr,
            )
            failed += 1
        else:
            print(f"CLONED: {destination}")
            cloned += 1

    print(f"Summary: {cloned} cloned, {skipped} skipped, {failed} failed.")
    if failed:
        print("Resolve the reported errors and rerun bootstrap.", file=sys.stderr)
        return 1
    print("Open the workspace:")
    print(f'code "{(workspace / "opentlv.code-workspace").as_posix()}"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
