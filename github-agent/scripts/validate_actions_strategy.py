#!/usr/bin/env python3
from __future__ import annotations
import argparse, re, sys
from pathlib import Path
PROTECTED_WORDS=("release","deploy","publish")
DEBUG_WORDS=("debug","diagnostic","one-shot","oneshot","tmp-")
def block(text,key):
    lines=text.splitlines(keepends=True); start=next((i for i,l in enumerate(lines) if re.match(rf"^{re.escape(key)}:\s*(?:#.*)?$",l.rstrip("\n"))),None)
    if start is None:return None
    end=len(lines)
    for i in range(start+1,len(lines)):
        if lines[i].strip() and not lines[i].startswith((" ","\t","#")):end=i;break
    return "".join(lines[start:end])
def validate(path):
    if not path.exists():return []
    text=path.read_text(encoding="utf-8"); m=re.search(r"(?m)^name:\s*(.+?)\s*$",text); name=m.group(1).strip().strip("'\"") if m else path.stem; hay=f"{name} {path.name}".lower(); protected=any(w in hay for w in PROTECTED_WORDS); debug=any(w in hay for w in DEBUG_WORDS); errors=[]
    on=block(text,"on")
    if on is None:errors.append("missing top-level on:")
    else:
        if "workflow_dispatch:" not in on:errors.append("missing workflow_dispatch recovery entry point")
        if debug and any(t in on for t in ("\n  push:","\n  pull_request:","\n  schedule:")):errors.append("debug/diagnostic workflow may only use workflow_dispatch")
    if block(text,"permissions") is None:errors.append("missing top-level permissions:")
    concurrency=block(text,"concurrency")
    if concurrency is None:errors.append("missing top-level concurrency:")
    else:
        cm=re.search(r"(?m)^\s+cancel-in-progress:\s*(.+?)\s*$",concurrency)
        if cm is None:errors.append("concurrency is missing cancel-in-progress")
        else:
            value=cm.group(1).strip()
            if protected and value!="false":errors.append("release/deploy/publish workflow must use cancel-in-progress: false")
            elif not protected and value=="false":errors.append("ordinary workflow must cancel superseded work; use true or a PR-aware expression")
    lines=text.splitlines(keepends=True); js=next((i for i,l in enumerate(lines) if re.match(r"^jobs:\s*(?:#.*)?$",l.rstrip("\n"))),None)
    if js is None:errors.append("missing jobs:");return errors
    starts=[i for i in range(js+1,len(lines)) if re.match(r"^  [A-Za-z0-9_.-]+:\s*(?:#.*)?$",lines[i].rstrip("\n"))]
    for n,start in enumerate(starts):
        end=starts[n+1] if n+1<len(starts) else len(lines); job="".join(lines[start:end])
        if re.search(r"(?m)^    uses:",job):continue
        if "runs-on:" in job and not re.search(r"(?m)^    timeout-minutes:\s*\d+",job):errors.append(f"job '{re.match(r'^  ([A-Za-z0-9_.-]+):',lines[start]).group(1)}' is missing timeout-minutes")
    return errors
def main():
    p=argparse.ArgumentParser();p.add_argument("paths",nargs="+",type=Path);args=p.parse_args();violations=[]
    for path in args.paths:
        if path.suffix not in {".yml",".yaml"}:continue
        errors=validate(path)
        if errors:violations.append(f"{path}:");violations.extend(f"  - {e}" for e in errors)
    if violations:print("GitHub Agent v4 policy violations:",file=sys.stderr);print("\n".join(violations),file=sys.stderr);return 1
    print("GitHub Agent v4 policy check passed.");return 0
if __name__=="__main__":raise SystemExit(main())
