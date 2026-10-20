# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marek Cingel

"""Exercise portal source assembly, without component tests or site publication."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("portal", "cli", "lua", "work-dir", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--core", type=Path)
    parser.add_argument("--mode", choices=("sibling", "remote"), required=True)
    args = parser.parse_args()
    portal = args.work_dir.resolve()
    if portal.exists():
        raise ValueError("Portal smoke requires a new disposable directory")
    portal.mkdir(parents=True)
    # Only the disposable portal receives generated assembly or remote sources.
    for directory in ("tools", "docs"):
        shutil.copytree(args.portal / directory, portal / directory,
                        ignore=shutil.ignore_patterns("__pycache__"))
    for name in ("docs-sources.json", "mkdocs.yml"):
        shutil.copyfile(args.portal / name, portal / name)
    for name in tuple(os.environ):
        if name.startswith("OPENTLV_"):
            del os.environ[name]
    os.environ["OPENTLV_DOCS_CHANNEL"] = "development"
    sys.path.insert(0, str(portal / "tools/docs"))
    import assembly
    from ci import check_navigation

    if args.mode == "sibling":
        if not args.core:
            raise ValueError("Sibling preview requires an explicit Core checkout")
        os.environ["OPENTLV_DOCS_LOCAL"] = "1"
        for name in ("core", "cli", "lua"):
            os.environ[f"OPENTLV_{name.upper()}_DIR"] = str(getattr(args, name).resolve())
    else:
        core = next(item for item in assembly.sources.manifest(portal) if item["id"] == "core")
        assembly.sources.fetch(portal, core["revision"])
        os.environ["OPENTLV_DOCS_SOURCE_ROOT"] = str(portal / "build/sources")
        os.environ["OPENTLV_DOCS_LOCK"] = str(portal / "build/sources.lock.json")
    selected = assembly.selected_sources(portal)
    if {item["id"] for _, item in selected if item["included"]} != {"core", "cli", "lua"}:
        raise ValueError("Portal must assemble all three workspace documentation sources")
    if args.mode == "sibling":
        for root, item in selected:
            expected = getattr(args, item["id"]).resolve()
            if root.resolve() != expected:
                raise ValueError(f"Wrong sibling documentation source: {item['id']}")
    assembly.assemble(portal, selected)
    output = portal / "build/assembled"
    check_navigation(output / "docs", (output / "navigation.json").read_text(encoding="utf-8"))
    metadata = json.loads((output / "source-revision.json").read_text(encoding="utf-8"))
    for item in metadata["sources"]:
        if not item.get("included") or not item.get("commit"):
            raise ValueError("Missing documentation source provenance")
    args.output.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print("Portal source assembly and navigation passed.")


if __name__ == "__main__":
    main()
