# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marek Cingel

"""Validate workspace contracts and run bounded cross-repository smoke tests."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

import bootstrap

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r"[0-9a-f]{40}")
COMPONENTS = {"core": "opentlv", "cli": "opentlv-cli",
              "lua": "opentlv-lua", "python": "opentlv-python", "rust": "opentlv-rust",
              "docs": "opentlv-docs"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_manifest(root=ROOT):
    data = json.loads((root / "integration.json").read_text(encoding="utf-8"))
    require(data.get("schema") == 1, "Unsupported integration manifest schema")
    repos = data.get("repositories")
    require(isinstance(repos, dict) and set(repos) == set(COMPONENTS),
            "Integration manifest must identify Core, CLI, Lua, Python, Rust and docs")
    for key, directory in COMPONENTS.items():
        item = repos[key]
        require(isinstance(item, dict), f"Invalid repository: {key}")
        require(item.get("directory") == directory, f"Invalid directory for {key}")
        require(item.get("repository") == f"https://github.com/OpenTLV/{directory}.git",
                f"Unexpected repository for {key}")
        require(isinstance(item.get("revision"), str) and SHA.fullmatch(item["revision"]),
                f"{key} requires a full lowercase commit SHA")
    return data


def validate_workspace(root=ROOT):
    data = load_manifest(root)
    config = json.loads((root / "opentlv.code-workspace").read_text(encoding="utf-8"))
    expected = {"opentlv-workspace": "."}
    expected.update({item["directory"]: "../" + item["directory"]
                     for item in data["repositories"].values()})
    folders = config.get("folders")
    require(isinstance(folders, list) and len(folders) == len(expected),
            "Workspace must contain exactly the documented roots")
    require(all(isinstance(item, dict) and set(item) == {"name", "path"} for item in folders),
            "Workspace roots must have a name and a relative path")
    actual = {item["name"]: item["path"] for item in folders}
    require(actual == expected and len(actual) == len(folders),
            "Workspace roots differ from the integration manifest")
    require(config.get("settings") == {},
            "Shared build settings need an explicit integration contract")
    require({repo.directory: repo.https_url for repo in bootstrap.REPOSITORIES}
            == {item["directory"]: item["repository"] for item in data["repositories"].values()},
            "Bootstrap and integration repository lists differ")
    for repo in bootstrap.REPOSITORIES:
        require(bootstrap.repository_identity(repo.ssh_url)
                == bootstrap.repository_identity(repo.https_url),
                f"Bootstrap transports disagree for {repo.directory}")
    for path in ("requirements-dev.txt", ".pre-commit-config.yaml", ".gitattributes",
                 "requirements-integration.txt", *(
                     f".github/workflows/workspace-{tier}.yml"
                     for tier in ("pr", "main", "full", "release"))):
        require((root / path).is_file(), f"Missing tooling configuration: {path}")
    return data


def select_full(event):
    require(event in ("pull_request", "push", "workflow_dispatch", "workflow_call"),
            "Unsupported CI event")
    return event in ("workflow_dispatch", "workflow_call")


def check_gate(results):
    require(bool(results) and all(result == "success" for result in results),
            "Required checks are missing, failed, cancelled or skipped")


class Runner:
    def __init__(self, report):
        self.report = report

    def run(self, args, *, cwd=None, env=None):
        args = [str(arg) for arg in args]
        print("+ " + subprocess.list2cmdline(args), flush=True)
        started = time.monotonic()
        result = subprocess.run(args, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                errors="replace", timeout=1200)
        print(result.stdout, end="", flush=True)
        step = {"command": args, "seconds": round(time.monotonic() - started, 3),
                "returncode": result.returncode}
        if result.returncode:
            step["output_tail"] = result.stdout[-8000:]
        self.report["steps"].append(step)
        require(result.returncode == 0, f"Command failed ({result.returncode}): {args[0]}")
        return result.stdout.strip()

    def checkout(self, item, parent):
        destination = parent / item["directory"]
        require(not destination.exists(), f"Refusing to reuse checkout: {destination}")
        self.run(["git", "init", destination])
        self.run(["git", "-C", destination, "remote", "add", "origin", item["repository"]])
        # Component version metadata requires complete ancestry and release tags.
        self.run(["git", "-C", destination, "fetch", "--tags", "origin", item["revision"]])
        self.run(["git", "-C", destination, "checkout", "--detach", "FETCH_HEAD"])
        evidence = self.identity(destination)
        require(evidence["commit"] == item["revision"] and not evidence["dirty"],
                f"Checkout differs from manifest: {destination}")
        return destination

    def identity(self, path):
        require(path.is_dir(), f"Missing source directory: {path}")
        top = self.run(["git", "-C", path, "rev-parse", "--show-toplevel"])
        require(Path(top).resolve() == path.resolve(), f"Not a checkout root: {path}")
        return {
            "path": str(path),
            "repository": self.run(["git", "-C", path, "config", "--get", "remote.origin.url"]),
            "commit": self.run(["git", "-C", path, "rev-parse", "HEAD"]),
            "dirty": bool(self.run(["git", "-C", path, "status", "--porcelain",
                                   "--untracked-files=all"])),
        }


def core_pin(source):
    text = (source / "cmake/Core.cmake").read_text(encoding="utf-8")
    pins = re.findall(r"^\s*GIT_TAG\s+([0-9a-f]{40})\s*(?:#.*)?$", text, re.MULTILINE)
    require(len(pins) == 1, f"Expected one immutable Core pin in {source}")
    artifact_path = source / "cmake/core-artifact.json"
    # Source integration also supports revisions predating binary-artifact CI.
    # If a component declares both kinds of dependency, they must agree.
    if artifact_path.exists():
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        require(artifact.get("repository") == "OpenTLV/opentlv"
                and artifact.get("commit") == pins[0], f"Core source/artifact pins differ in {source}")
    return pins[0]


def cmake_arguments(mode, core=None):
    args = [
        "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "-DFETCHCONTENT_TRY_FIND_PACKAGE_MODE=NEVER",
        "-DCMAKE_FIND_USE_PACKAGE_REGISTRY=OFF",
        "-DCMAKE_FIND_USE_SYSTEM_PACKAGE_REGISTRY=OFF",
        "-DOPENTLV_BUILD_SHARED_LIBS=OFF", "-DOPENTLV_BUILD_CXX=ON",
    ]
    args += [f"-D{option}=OFF" for option in (
        "OPENTLV_BUILD_TESTS", "OPENTLV_BUILD_EXAMPLES", "OPENTLV_BUILD_DOCS",
        "OPENTLV_BUILD_BENCHMARKS", "OPENTLV_BUILD_FUZZING", "OPENTLV_BUILD_PYTHON",
        "OPENTLV_BUILD_WASM", "OPENTLV_BUILD_LUA", "OPENTLV_BUILD_CLI",
        "OPENTLV_CLI_BUILD_TESTS", "OPENTLV_BUILD_LUA_TESTS")]
    if mode == "sibling":
        require(core is not None, "Sibling integration needs an explicit Core directory")
        args.append(f"-DFETCHCONTENT_SOURCE_DIR_OPENTLV_CORE={core.as_posix()}")
    return args


def assert_core_compiled(build, core):
    commands = json.loads((build / "compile_commands.json").read_text(encoding="utf-8"))
    sources = [Path(item["file"]).resolve() for item in commands]
    expected = (core / "tlv/src").resolve()
    require(any(expected in source.parents for source in sources),
            "Build did not compile the selected Core sources")


def component_smoke(runner, key, source, core, args, env):
    build = args.work_dir / key
    pin = core_pin(source)
    command = ["cmake", "-S", source, "-B", build, "-G", "Ninja"]
    command += cmake_arguments(args.mode, core)
    if key == "lua":
        require(shutil.which(args.lua), f"Lua interpreter unavailable: {args.lua}")
        if args.lua_include:
            command.append(f"-DLUA_INCLUDE_DIR={args.lua_include.as_posix()}")
        if args.lua_library:
            command.append(f"-DLUA_LIBRARY={args.lua_library.as_posix()}")
    runner.run(command, env=env)
    selected = core if args.mode == "sibling" else build / "_deps/opentlv_core-src"
    identity = runner.identity(selected)
    if args.mode == "remote":
        require(identity["commit"] == pin and not identity["dirty"],
                f"{key} remote fallback did not use its exact Core pin")
    assert_core_compiled(build, selected)
    runner.report["core_dependencies"][key] = dict(identity, declared_pin=pin, mode=args.mode)
    target = "otlv" if key == "cli" else "opentlv_lua"
    runner.run(["cmake", "--build", build, "--target", target, "--parallel", str(args.jobs)], env=env)
    if key == "cli":
        binary = build / "src" / ("otlv.exe" if os.name == "nt" else "otlv")
        version = runner.run([binary, "--version"], env=env)
        require(version, "CLI version output is empty")
        runner.run([binary, "dump", "--format", "fixed", "--hex", "01024869"], env=env)
        runner.report["cli_version"] = version
    else:
        lua_env = dict(env)
        # No default module search paths: require() must load this build.
        for name in tuple(lua_env):
            if name.startswith(("LUA_PATH", "LUA_CPATH", "LUA_INIT")):
                del lua_env[name]
        lua_env["LUA_PATH"] = f"{source.as_posix()}/lua/?.lua;{source.as_posix()}/lua/?/init.lua"
        extension = "dll" if os.name == "nt" else "so"
        lua_env["LUA_CPATH"] = f"{build.as_posix()}/?.{extension}"
        version = runner.run([args.lua, "-e",
                              'local m=require("opentlv"); assert(m==require("opentlv._core")); '
                              'assert(type(m.version())=="string"); print(_VERSION); print(m.version())'],
                             env=lua_env)
        runner.report["lua_version"] = version
    runner.report["checks"][key] = "passed"


def full(args, runner, manifest):
    require(not args.work_dir.exists(), "Use a new work directory; existing output is never removed")
    args.work_dir.mkdir(parents=True)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("OPENTLV_", "FETCHCONTENT_", "CMAKE_PREFIX_PATH", "LUA_INIT"))}
    env["GIT_TERMINAL_PROMPT"] = "0"
    sources = {"core": None}
    require(not args.source_root or args.mode == "sibling",
            "--source-root is only supported for explicit local sibling development")
    for key, item in manifest["repositories"].items():
        if key == "core" and args.mode == "remote":
            continue  # Each consumer and the portal fetch their own Core pin.
        source = (args.source_root / item["directory"] if args.source_root
                  else runner.checkout(item, args.work_dir / "sources"))
        identity = runner.identity(source)
        require(bootstrap.repository_identity(identity["repository"])
                == bootstrap.repository_identity(item["repository"]), f"Wrong repository: {source}")
        runner.report["sources"][key] = dict(identity, configured_revision=item["revision"])
        sources[key] = source
    runner.report["tools"] = {
        "cmake": runner.run(["cmake", "--version"]),
        "ninja": runner.run(["ninja", "--version"]),
        "lua": runner.run([args.lua, "-v"]),
        "git": runner.run(["git", "--version"]),
    }
    # Python and Rust are pinned to repository scaffolds. Their checkout identities
    # are recorded above; build smoke awaits component-owned build contracts.
    for key in ("cli", "lua"):
        component_smoke(runner, key, sources[key], sources["core"], args, env)
    docs_report = args.work_dir / "docs.json"
    docs_command = [sys.executable, "-B", ROOT / "scripts/docs_smoke.py",
                    "--portal", sources["docs"],
                    "--cli", sources["cli"], "--lua", sources["lua"],
                    "--mode", args.mode, "--output", docs_report,
                    "--work-dir", args.work_dir / "portal"]
    if args.mode == "sibling":
        docs_command += ["--core", sources["core"]]
    runner.run(docs_command, env=env)
    runner.report["documentation"] = json.loads(docs_report.read_text(encoding="utf-8"))
    runner.report["checks"]["documentation"] = "passed"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("fast")
    plan = sub.add_parser("plan")
    plan.add_argument("--event", choices=("pull_request", "push", "workflow_dispatch", "workflow_call"),
                      default="workflow_dispatch")
    gate = sub.add_parser("gate")
    gate.add_argument("--result", action="append", required=True)
    integration = sub.add_parser("full")
    integration.add_argument("--mode", choices=("sibling", "remote"), required=True)
    integration.add_argument("--work-dir", type=Path, required=True)
    integration.add_argument("--source-root", type=Path)
    integration.add_argument("--lua", default="lua5.4")
    integration.add_argument("--lua-include", type=Path)
    integration.add_argument("--lua-library", type=Path)
    integration.add_argument("--jobs", type=int, default=2)
    integration.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "gate":
        check_gate(args.result)
        return
    manifest = validate_workspace()
    if args.command == "fast":
        print("Workspace configuration, repository references and tooling configuration are consistent.")
        return
    if args.command == "plan":
        value = str(select_full(args.event)).lower()
        print(f"full={value}")
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
                output.write(f"full={value}\n")
        return
    for name in ("work_dir", "source_root", "lua_include", "lua_library", "report"):
        value = getattr(args, name)
        if value is not None:
            setattr(args, name, value.resolve())
    require(args.jobs > 0, "--jobs must be positive")
    report = {"schema": 2, "status": "failed", "mode": args.mode,
              "local_development": bool(args.source_root),
              "manifest_sha256": hashlib.sha256((ROOT / "integration.json").read_bytes()).hexdigest(),
              "workspace_commit": subprocess.check_output(
                  ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
              "execution": {key: os.environ.get("GITHUB_" + key.upper(), "")
                            for key in ("repository", "run_id", "run_attempt", "workflow_ref",
                                        "workflow_sha", "event_name", "sha", "ref")},
              "workspace_dirty": bool(subprocess.check_output(
                  ["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=all"],
                  text=True).strip()),
              "sources": {}, "core_dependencies": {}, "steps": [], "checks": {}}
    started = time.monotonic()
    try:
        full(args, Runner(report), manifest)
        report["status"] = "passed"
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        report["seconds"] = round(time.monotonic() - started, 3)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
