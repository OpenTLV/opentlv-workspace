# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marek Cingel

"""Bind integration evidence to one immutable workspace and Actions attempt."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from integration import ROOT, SHA, load_manifest, require
from bootstrap import repository_identity

REPOSITORY = "OpenTLV/opentlv-workspace"
RELEASE_WORKFLOW = ".github/workflows/workspace-release.yml"
FULL_WORKFLOW = ".github/workflows/workspace-full.yml"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def execution():
    return {key: os.environ.get("GITHUB_" + key.upper(), "")
            for key in ("repository", "run_id", "run_attempt", "workflow_ref",
                        "workflow_sha", "event_name", "sha", "ref")}


def validate_execution(context):
    require(context["repository"] == REPOSITORY, "Unexpected workspace repository")
    require(SHA.fullmatch(context["sha"]) and context["workflow_sha"] == context["sha"],
            "Workflow and workspace commits must agree")
    for key in ("run_id", "run_attempt"):
        require(context[key].isdigit() and int(context[key]) > 0, f"Missing Actions {key}")
    require(context["event_name"] == "workflow_dispatch", "Full requires manual dispatch")
    require(context["ref"].startswith("refs/heads/"), "Select a branch, not a tag")
    require(context["workflow_ref"] in (
        f"{REPOSITORY}/{path}@{context['ref']}" for path in (FULL_WORKFLOW, RELEASE_WORKFLOW)),
        "Unexpected workflow identity")


def request(root=ROOT):
    context = execution()
    validate_execution(context)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    require(commit == context["sha"], "Checkout differs from requested commit")
    require(not subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, text=True).strip(),
        "Hosted evidence requires a clean workspace")
    return {"schema": 1, "execution": context, "manifest_sha256": digest(root / "integration.json"),
            "integration": load_manifest(root)}


def validate_request(value, root=ROOT):
    require(value == request(root), "Request differs from this checkout or Actions attempt")


def validate_report(report, mode, locked):
    require(report.get("schema") == 2 and report.get("status") == "passed"
            and report.get("mode") == mode, "Missing or failed Full CI scenario")
    require(report.get("local_development") is False and report.get("workspace_dirty") is False,
            "Local or dirty results cannot authorize integration")
    require(report.get("execution") == locked["execution"], "Stale or foreign integration report")
    require(report.get("workspace_commit") == locked["execution"]["sha"]
            and report.get("manifest_sha256") == locked["manifest_sha256"], "Integration input drift")
    require(report.get("checks") == dict.fromkeys(("cli", "lua", "documentation"), "passed"),
            "Incomplete smoke evidence")
    require(report.get("steps") and all(step.get("returncode") == 0 for step in report["steps"]),
            "Missing or unsuccessful commands")
    require(all(isinstance(report.get(key), str) and report[key].strip()
                for key in ("cli_version", "lua_version"))
            and set(report.get("tools", {})) == {"git", "cmake", "ninja", "lua"}
            and all(report["tools"].values()), "Missing runtime or tool evidence")
    require(isinstance(report.get("seconds"), (int, float)) and report["seconds"] > 0,
            "Missing integration timing")
    repos = locked["integration"]["repositories"]
    expected = set(repos) if mode == "sibling" else set(repos) - {"core"}
    require(set(report["sources"]) == expected, "Wrong source inventory")
    for key in expected:
        item = report["sources"][key]
        require(item["commit"] == item["configured_revision"] == repos[key]["revision"]
                and item["dirty"] is False
                and repository_identity(item["repository"])
                == repository_identity(repos[key]["repository"]), f"Wrong {key} source")
    require(set(report["core_dependencies"]) == {"cli", "lua"}, "Missing Core dependencies")
    for item in report["core_dependencies"].values():
        require(SHA.fullmatch(item["declared_pin"]) and item["dirty"] is False
                and item["mode"] == mode
                and repository_identity(item["repository"])
                == repository_identity(repos["core"]["repository"]), "Invalid Core dependency")
        require(item["commit"] == (repos["core"]["revision"] if mode == "sibling"
                                  else item["declared_pin"]), "Wrong effective Core revision")
    docs = report["documentation"]["sources"]
    require(len(docs) == 3 and {item["id"] for item in docs} == {"core", "cli", "lua"},
            "Missing or duplicate documentation source")
    for item in docs:
        require(item["included"] is True and item["dirty"] is False
                and repository_identity(item["repository"])
                == repository_identity(repos[item["id"]]["repository"]), "Invalid documentation source")
        expected_commit = repos[item["id"]]["revision"] if mode == "sibling" else item["revision"]
        require(SHA.fullmatch(expected_commit) and item["commit"] == expected_commit,
                "Wrong documentation source revision")


def validate_evidence(evidence, locked):
    require(evidence.get("schema") == 1 and evidence.get("request") == locked,
            "Evidence belongs to another request")
    require(set(evidence["reports"]) == {"sibling", "remote"}, "Missing integration scenario")
    for mode, report in evidence["reports"].items():
        validate_report(report, mode, locked)
    for key in set(locked["integration"]["repositories"]) - {"core"}:
        require(evidence["reports"]["sibling"]["sources"][key]
                == evidence["reports"]["remote"]["sources"][key]
                or all(evidence["reports"]["sibling"]["sources"][key][field]
                       == evidence["reports"]["remote"]["sources"][key][field]
                       for field in ("commit", "repository", "configured_revision", "dirty")),
                "Scenario sources disagree")
    for key in ("cli", "lua"):
        require(evidence["reports"]["sibling"]["core_dependencies"][key]["declared_pin"]
                == evidence["reports"]["remote"]["core_dependencies"][key]["declared_pin"],
                "Scenario dependency declarations disagree")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("lock", "verify"))
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--reports", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "lock":
        write(args.request, request())
        return
    locked = read(args.request)
    validate_request(locked)
    require(args.reports and args.output, "Reports and output are required")
    require({path.name for path in args.reports.iterdir()} == {"sibling.json", "remote.json"},
            "Unexpected integration artifact inventory")
    evidence = {"schema": 1, "request": locked,
                "reports": {mode: read(args.reports / f"{mode}.json")
                            for mode in ("sibling", "remote")}}
    validate_evidence(evidence, locked)
    write(args.output, evidence)


if __name__ == "__main__":
    main()
