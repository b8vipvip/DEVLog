#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

PROTECTED_WORDS = ("release", "deploy", "publish")
INTERNAL_FILES = {"actions-governor.yml", "actions-recovery.yml", "actions-policy-check.yml"}


def block(text: str, key: str):
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if re.match(rf"^{re.escape(key)}:\s*(?:#.*)?$", line.rstrip("\n"))), None)
    if start is None:
        return None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].strip() and not lines[i].startswith((" ", "\t", "#")):
            end = i
            break
    return start, end


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", type=Path)
    args = parser.parse_args()
    path = args.workflow
    if not path.exists() or path.name in INTERNAL_FILES:
        return 0

    text = path.read_text(encoding="utf-8")
    original = text
    name_match = re.search(r"(?m)^name:\s*(.+?)\s*$", text)
    name = name_match.group(1).strip().strip("'\"") if name_match else path.stem
    protected = any(word in f"{name} {path.name}".lower() for word in PROTECTED_WORDS)

    on_block = block(text, "on")
    if on_block:
        lines = text.splitlines(keepends=True)
        start, end = on_block
        if lines[start].strip() == "on:" and "workflow_dispatch:" not in "".join(lines[start:end]):
            lines.insert(end, "  workflow_dispatch:\n")
            text = "".join(lines)

    jobs = block(text, "jobs")
    if jobs:
        lines = text.splitlines(keepends=True)
        insert_at = jobs[0]
        additions = []
        if re.search(r"(?m)^permissions:\s*(?:#.*)?$", text) is None:
            additions.append("permissions:\n  contents: read\n\n")
        if re.search(r"(?m)^concurrency:\s*(?:#.*)?$", text) is None:
            if protected:
                additions.append("concurrency:\n  group: ${{ github.workflow }}-${{ github.repository }}\n  cancel-in-progress: false\n\n")
            else:
                additions.append("concurrency:\n  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}\n  cancel-in-progress: ${{ github.event_name == 'pull_request' }}\n\n")
        lines[insert_at:insert_at] = additions
        text = "".join(lines)

    jobs = block(text, "jobs")
    if jobs:
        lines = text.splitlines(keepends=True)
        start, end = jobs
        starts = [i for i in range(start + 1, end) if re.match(r"^  [A-Za-z0-9_.-]+:\s*(?:#.*)?$", lines[i].rstrip("\n"))]
        inserts = []
        timeout = 120 if protected else 30
        for n, job_start in enumerate(starts):
            job_end = starts[n + 1] if n + 1 < len(starts) else end
            job = "".join(lines[job_start:job_end])
            if "runs-on:" not in job or re.search(r"(?m)^    timeout-minutes:", job) or re.search(r"(?m)^    uses:", job):
                continue
            for i in range(job_start + 1, job_end):
                if re.match(r"^    runs-on:", lines[i]):
                    inserts.append((i + 1, f"    timeout-minutes: {timeout}\n"))
                    break
        for i, payload in reversed(inserts):
            lines.insert(i, payload)
        text = "".join(lines)

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"repaired {path}")
    else:
        print(f"no safe policy repair needed for {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
