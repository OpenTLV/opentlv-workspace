# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marek Cingel

"""Record GitHub-hosted CI timing evidence; never dispatch or modify a run."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import time
from urllib.request import Request, urlopen

API = "https://api.github.com/repos/OpenTLV/opentlv-workspace"


def get(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "OpenTLV-workspace-CI"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    with urlopen(Request(API + path, headers=headers), timeout=60) as response:
        return json.load(response)


def seconds(start, end):
    return (datetime.fromisoformat(end.replace("Z", "+00:00"))
            - datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds()


def attempt_jobs(run_id, attempt):
    jobs, page = [], 1
    while True:
        batch = get(f"/actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100&page={page}")
        jobs.extend(batch["jobs"])
        if len(batch["jobs"]) < 100:
            return jobs
        page += 1


def completed_jobs(context, names, successful=False):
    """Retry delayed metadata, always querying the same run and attempt."""
    if not names or len(set(names)) != len(names):
        raise ValueError("Expected unique job names")
    for retry in range(6):
        jobs = attempt_jobs(context["run_id"], context["run_attempt"])
        selected = [job for job in jobs if job["name"] in names]
        if (len(selected) == len(names) and {job["name"] for job in selected} == set(names)
                and all(job.get("status") == "completed" and job.get("completed_at")
                        and job.get("conclusion") in ("success", "failure", "cancelled", "skipped",
                                                     "timed_out", "action_required", "neutral", "stale")
                        and (job.get("started_at") or job.get("conclusion") == "skipped")
                        for job in selected)):
            break
        if retry == 5:
            raise ValueError("Missing or incomplete same-attempt job metadata")
        time.sleep(5)
    for job in selected:
        if (str(job.get("run_attempt")) != context["run_attempt"]
                or str(job.get("run_id")) != context["run_id"]
                or job.get("head_sha") != context["sha"]):
            raise ValueError("Job identity differs from requested run/attempt/commit")
        if successful and job.get("conclusion") != "success":
            raise ValueError(f"Required job did not pass: {job['name']}")
    return selected


def current(names):
    context = {key: os.environ["GITHUB_" + key.upper()]
               for key in ("run_id", "run_attempt", "sha")}
    checkout_commit = context["sha"]
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
        # The Jobs API identifies the PR head; checkout tests the merge commit.
        context["sha"] = os.environ["TIMING_HEAD_SHA"]
    run = get(f"/actions/runs/{context['run_id']}/attempts/{context['run_attempt']}")
    if (str(run["run_attempt"]) != context["run_attempt"] or run["head_sha"] != context["sha"]
            or str(run["id"]) != context["run_id"]):
        raise ValueError("Run identity changed")
    jobs = completed_jobs(context, names)
    measured = [{"name": job["name"], "conclusion": job["conclusion"],
                 "seconds": seconds(job["started_at"], job["completed_at"])
                 if job["conclusion"] != "skipped" else 0, "url": job["html_url"]} for job in jobs]
    return {"run_id": int(context["run_id"]), "attempt": int(context["run_attempt"]),
            "event": run["event"], "commit": run["head_sha"], "checkout_commit": checkout_commit,
            "url": run["html_url"],
            "scope": "named predecessor jobs; excludes collecting gate",
            "jobs": measured, "started_at": run["run_started_at"],
            "wall_seconds": seconds(run["run_started_at"], max(job["completed_at"] for job in jobs)),
            "job_seconds": sum(job["seconds"] for job in measured)}


def collect(run_id):
    run = get(f"/actions/runs/{run_id}")
    if run["status"] != "completed" or run["conclusion"] != "success":
        raise ValueError(f"Run {run_id} is not successfully completed")
    jobs, page = [], 1
    while True:
        batch = get(f"/actions/runs/{run_id}/attempts/{run['run_attempt']}/jobs?per_page=100&page={page}")
        jobs.extend(batch["jobs"])
        if len(batch["jobs"]) < 100:
            break
        page += 1
    measured = []
    for job in jobs:
        if job["conclusion"] not in ("success", "skipped"):
            raise ValueError(f"Run contains an unsuccessful job: {job['name']}")
        measured.append({"name": job["name"], "conclusion": job["conclusion"],
                         "seconds": seconds(job["started_at"], job["completed_at"])
                         if job["conclusion"] == "success" else 0,
                         "url": job["html_url"]})
    return {"run_id": run_id, "attempt": run["run_attempt"], "event": run["event"],
            "commit": run["head_sha"], "url": run["html_url"], "jobs": measured,
            "started_at": run["run_started_at"],
            "wall_seconds": seconds(run["run_started_at"], max(
                job["completed_at"] for job in jobs if job["conclusion"] == "success")),
            "job_seconds": sum(job["seconds"] for job in measured)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", type=int, action="append")
    mode.add_argument("--current", action="store_true")
    parser.add_argument("--job", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {"schema": 1, "repository": "OpenTLV/opentlv-workspace",
              "runs": [current(args.job)] if args.current else [collect(run) for run in args.run]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for run in report["runs"]:
        print(f"{run['run_id']}: {run['wall_seconds']}s elapsed, {run['job_seconds']}s summed job time")


if __name__ == "__main__":
    main()
