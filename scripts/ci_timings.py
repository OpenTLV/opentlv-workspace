# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marek Cingel

"""Record GitHub-hosted CI timing evidence; never dispatch or modify a run."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
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
    parser.add_argument("--run", type=int, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {"schema": 1, "repository": "OpenTLV/opentlv-workspace",
              "runs": [collect(run) for run in args.run]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for run in report["runs"]:
        print(f"{run['run_id']}: {run['wall_seconds']}s elapsed, {run['job_seconds']}s summed job time")


if __name__ == "__main__":
    main()
