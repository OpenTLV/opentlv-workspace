# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marek Cingel

"""Publish a verified workspace snapshot; never publish component artifacts."""

import argparse
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import ci_timings
from quality import (ROOT, REPOSITORY, RELEASE_WORKFLOW, digest, read, request, require,
                     validate_evidence, write)

TAG = r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
FULL_JOBS = ["Release preflight", "Full / Lock combination", "Full / Integration (sibling)",
             "Full / Integration (remote)", "Full / Workspace full gate"]


def run(*args):
    return subprocess.check_output([str(arg) for arg in args], cwd=ROOT, text=True).strip()


def closed_changelog(text, tag):
    require(re.fullmatch(TAG, tag), "Tag must be vMAJOR.MINOR.PATCH without leading zeroes")
    sections = re.split(r"^## ", text, flags=re.MULTILINE)[1:]
    require(bool(sections), "Missing release changelog")
    if sections[0].splitlines()[0].strip() == "[Unreleased]":
        pending = sections.pop(0).splitlines()[1:]
        require(all(not line.strip() or line.startswith("### ") for line in pending),
                "Close Unreleased entries")
    require(bool(sections), "Missing closed release section")
    heading, _, body = sections[0].partition("\n")
    match = re.fullmatch(r"\[v?" + re.escape(tag[1:]) + r"\] - (\d{4}-\d{2}-\d{2})",
                         heading.strip())
    require(match is not None, "Newest closed changelog must match requested tag")
    require(date.fromisoformat(match[1]) <= date.today(), "Release date is in the future")
    require(re.search(r"^- \S", body, re.MULTILINE), "Empty release changelog")


def absent(path):
    try:
        ci_timings.get(path)
    except HTTPError as error:
        if error.code == 404:
            return
        raise
    raise ValueError("Release or tag already exists")


def preflight(tag):
    closed_changelog((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), tag)
    locked = request()
    ctx = locked["execution"]
    require(ctx["ref"] == "refs/heads/main"
            and ctx["workflow_ref"] == f"{REPOSITORY}/{RELEASE_WORKFLOW}@refs/heads/main",
            "Release must dispatch workspace-release.yml from main")
    # Main can advance during a run; the original dispatch commit remains the candidate.
    comparison = ci_timings.get(f"/compare/{ctx['sha']}...main")
    require(comparison["status"] in ("identical", "ahead")
            and comparison["merge_base_commit"]["sha"] == ctx["sha"],
            "Candidate is not on main")
    absent(f"/git/ref/tags/{tag}")
    absent(f"/releases/tags/{tag}")
    require(not run("git", "tag", "--points-at", ctx["sha"]), "Candidate already has a tag")
    return {"schema": 1, "tag": tag, "lock": locked}


def verify_jobs(selected, assembled=False):
    ctx = selected["lock"]["execution"]
    metadata = ci_timings.get(f"/actions/runs/{ctx['run_id']}/attempts/{ctx['run_attempt']}")
    require(str(metadata["id"]) == ctx["run_id"]
            and str(metadata["run_attempt"]) == ctx["run_attempt"]
            and metadata["repository"]["full_name"] == REPOSITORY
            and metadata["head_sha"] == ctx["sha"] and metadata["event"] == "workflow_dispatch"
            and metadata["path"] == RELEASE_WORKFLOW, "Unexpected release workflow execution")
    return ci_timings.completed_jobs(
        ctx, FULL_JOBS + (["Assemble snapshot"] if assembled else []), successful=True)


def snapshot_bytes(selected):
    # Archive only tracked workspace files, including its immutable integration manifest.
    return subprocess.check_output(
        ["git", "archive", "--format=tar", f"--prefix=opentlv-workspace-{selected['tag']}/",
         selected["lock"]["execution"]["sha"]], cwd=ROOT)


def assemble(selected, evidence, output):
    require(selected == preflight(selected["tag"]), "Release request changed")
    validate_evidence(evidence, selected["lock"])
    verify_jobs(selected)
    output.mkdir(parents=True, exist_ok=False)
    snapshot = output / f"opentlv-workspace-{selected['tag']}.tar"
    snapshot.write_bytes(snapshot_bytes(selected))
    write(output / "integration-evidence.json", evidence)
    write(output / "release-manifest.json", {
        "schema": 1, "kind": "workspace-integration-snapshot", "request": selected,
        "repositories": selected["lock"]["integration"]["repositories"],
        "snapshot": {"file": snapshot.name, "sha256": digest(snapshot)},
        "evidence_sha256": digest(output / "integration-evidence.json"),
    })
    checksums = "".join(f"{digest(path)}  {path.name}\n" for path in sorted(output.iterdir()))
    (output / "SHA256SUMS").write_text(checksums, encoding="utf-8")


def validate_payload(directory, tag):
    manifest = read(directory / "release-manifest.json")
    selected = manifest["request"]
    require(manifest.get("schema") == 1 and manifest.get("kind") == "workspace-integration-snapshot"
            and selected["tag"] == tag and selected == preflight(tag), "Release manifest mismatch")
    require(manifest["repositories"] == selected["lock"]["integration"]["repositories"],
            "Released repository revisions changed")
    name = f"opentlv-workspace-{tag}.tar"
    expected = {name, "release-manifest.json", "integration-evidence.json"}
    require({path.name for path in directory.iterdir()} == expected | {"SHA256SUMS"},
            "Unexpected release inventory")
    sums = {}
    for line in (directory / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_.-]+)", line)
        require(match is not None and match[2] not in sums, "Invalid or duplicate checksum")
        sums[match[2]] = match[1]
    require(set(sums) == expected, "Incomplete checksum inventory")
    for filename, checksum in sums.items():
        path = directory / filename
        require(path.is_file() and not path.is_symlink() and digest(path) == checksum,
                f"Modified release asset: {filename}")
    require(manifest["snapshot"] == {"file": name, "sha256": sums[name]}
            and manifest["evidence_sha256"] == sums["integration-evidence.json"], "Manifest digests differ")
    require(hashlib.sha256(snapshot_bytes(selected)).hexdigest() == sums[name],
            "Snapshot differs from exact committed workspace")
    validate_evidence(read(directory / "integration-evidence.json"), selected["lock"])
    return selected


def check_attestation(results, path, selected):
    """Accept only verified gh output, then enforce the certificate's attempt identity."""
    ctx = selected["lock"]["execution"]
    invocation = f"https://github.com/{REPOSITORY}/actions/runs/{ctx['run_id']}/attempts/{ctx['run_attempt']}"
    signer = f"https://github.com/{REPOSITORY}/{RELEASE_WORKFLOW}@refs/heads/main"
    for result in results:
        verified = result.get("verificationResult", {})
        cert = verified.get("signature", {}).get("certificate", {})
        statement = verified.get("statement", {})
        if (cert.get("runInvocationURI") == invocation
                and cert.get("buildSignerURI") == signer
                and cert.get("buildSignerDigest") == ctx["sha"]
                and cert.get("sourceRepositoryURI") == f"https://github.com/{REPOSITORY}"
                and cert.get("sourceRepositoryDigest") == ctx["sha"]
                and cert.get("sourceRepositoryRef") == "refs/heads/main"
                and cert.get("buildTrigger") == "workflow_dispatch"
                and statement.get("predicateType") == "https://slsa.dev/provenance/v1"
                and any(subject.get("digest", {}).get("sha256") == digest(path)
                        for subject in statement.get("subject", []))):
            return
    raise ValueError(f"No attestation from the exact release attempt: {path.name}")


def verify_attestations(directory, selected):
    for path in sorted(directory.iterdir()):
        result = run("gh", "attestation", "verify", path, "--repo", REPOSITORY,
                     "--signer-workflow", f"{REPOSITORY}/{RELEASE_WORKFLOW}",
                     "--signer-digest", selected["lock"]["execution"]["sha"],
                     "--source-digest", selected["lock"]["execution"]["sha"],
                     "--source-ref", "refs/heads/main", "--deny-self-hosted-runners", "--format", "json")
        check_attestation(json.loads(result), path, selected)


def create_tag(selected):
    payload = json.dumps({"ref": "refs/tags/" + selected["tag"],
                          "sha": selected["lock"]["execution"]["sha"]}).encode()
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "OpenTLV-workspace-CI",
               "Authorization": "Bearer " + os.environ["GH_TOKEN"], "Content-Type": "application/json"}
    # POST is create-only: an existing tag fails atomically, never force-move a ref.
    with urlopen(Request(ci_timings.API + "/git/refs", data=payload, headers=headers,
                         method="POST"), timeout=60) as response:
        created = json.load(response)
    require(created["ref"] == "refs/tags/" + selected["tag"]
            and created["object"]["sha"] == selected["lock"]["execution"]["sha"],
            "Unexpected created tag")


def publish(directory, tag):
    selected = validate_payload(directory, tag)
    verify_jobs(selected, assembled=True)
    verify_attestations(directory, selected)
    # Recheck absence after remote verification; creation still rejects races.
    absent(f"/git/ref/tags/{tag}")
    absent(f"/releases/tags/{tag}")
    create_tag(selected)
    run("gh", "release", "create", tag, "--repo", REPOSITORY, "--verify-tag",
        "--title", f"OpenTLV Workspace {tag}", "--notes",
        "Verified workspace integration snapshot. Component releases remain independently versioned.",
        *sorted(directory.iterdir()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "assemble", "publish"))
    parser.add_argument("--tag")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        write(args.output, preflight(args.tag))
    elif args.command == "assemble":
        assemble(read(args.input / "release-request.json"),
                 read(args.input / "integration-evidence.json"), args.output)
    else:
        publish(args.input, args.tag)


if __name__ == "__main__":
    main()
