#!/usr/bin/env python3
"""Hunt the two remaining near-miss sub-classes.

C  wrapper-command : config names `make X` / `npm run X` / `just X`.  No FILE
                     called X exists, but the TARGET does.  A detector that
                     resolves command words against the filesystem fires here.

D  temporal        : config says "never edit X"; X exists; every edit to X
                     PREDATES the commit that introduced the rule.  The rule was
                     never violated -- a detector that checks "was X ever
                     touched?" fires here.
"""
import json
import re
import subprocess
import sys


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True,
                          text=True, timeout=180)


def exists(repo, rev, p):
    r = git(repo, "ls-tree", rev, "--", p.rstrip("/"))
    return r.returncode == 0 and bool(r.stdout.strip())


CONFIGS = ["CLAUDE.md", "AGENTS.md", ".cursorrules",
           ".github/copilot-instructions.md"]
NOEDIT = re.compile(
    r"(never\s+edit|do\s*not\s+edit|don't\s+edit|never\s+modify|do\s*not\s+modify"
    r"|auto-?generated|generated\s+file|never\s+hand-?edit)", re.I)
CMD = re.compile(r"`(?:(make|just)\s+([A-Za-z0-9][\w:.-]*)"
                 r"|npm\s+run\s+([\w:.-]+)|yarn\s+([\w:.-]+)|pnpm\s+run\s+([\w:.-]+))`")
PATH_IN_LINE = re.compile(r"`([A-Za-z0-9._][A-Za-z0-9._/-]*\.[A-Za-z0-9]{1,6})`")

d = "repos/" + sys.argv[1]
slug = sys.argv[1].replace("_", "/", 1)
head = git(d, "rev-parse", "HEAD").stdout.strip()

for cfg in CONFIGS:
    r = git(d, "show", f"HEAD:{cfg}")
    if r.returncode != 0:
        continue
    body = r.stdout

    # ---- C: wrapper commands ----
    mk = git(d, "show", "HEAD:Makefile").stdout
    pj = git(d, "show", "HEAD:package.json").stdout
    ju = git(d, "show", "HEAD:justfile").stdout or git(d, "show", "HEAD:Justfile").stdout
    try:
        scripts = set(json.loads(pj).get("scripts", {})) if pj else set()
    except Exception:
        scripts = set()
    mk_targets = set(re.findall(r"^([A-Za-z0-9][\w.-]*)\s*:(?!=)", mk, re.M))
    ju_recipes = set(re.findall(r"^([A-Za-z0-9][\w-]*)\s*:", ju, re.M))
    for i, line in enumerate(body.splitlines(), 1):
        for m in CMD.finditer(line):
            tool, tgt, npm, yarn, pnpm = m.groups()
            name = tgt or npm or yarn or pnpm
            if not name:
                continue
            via = None
            if tool == "make" and name in mk_targets:
                via = "Makefile target"
            elif tool == "just" and name in ju_recipes:
                via = "justfile recipe"
            elif (npm or yarn or pnpm) and name in scripts:
                via = "package.json script"
            if via and not exists(d, "HEAD", name):
                print(json.dumps({
                    "kind": "nearmiss_wrapper", "repo": slug, "config": cfg,
                    "head": head, "line": i, "text": line.strip()[:200],
                    "command": m.group(0).strip("`"), "target": name,
                    "resolves_via": via}))

    # ---- D: temporal no-edit rule ----
    for i, line in enumerate(body.splitlines(), 1):
        if not NOEDIT.search(line):
            continue
        for p in PATH_IN_LINE.findall(line):
            if not exists(d, "HEAD", p):
                continue  # that's a defect, not a near-miss
            # when did the rule land?
            intro = None
            for sha in git(d, "log", "--no-renames", "--diff-filter=AM",
                           "--format=%H", "--", cfg).stdout.split():
                if line.strip() in git(d, "show", f"{sha}:{cfg}").stdout:
                    intro = sha
                else:
                    break
            if not intro:
                continue
            rule_date = git(d, "log", "-1", "--format=%cI", intro).stdout.strip()
            last_edit = git(d, "log", "-1", "--format=%cI", "--", p).stdout.strip()
            n_edits = git(d, "rev-list", "--count", "HEAD", "--", p).stdout.strip()
            if last_edit and rule_date and last_edit < rule_date and int(n_edits or 0) > 1:
                print(json.dumps({
                    "kind": "nearmiss_temporal", "repo": slug, "config": cfg,
                    "head": head, "line": i, "text": line.strip()[:200],
                    "protected_path": p, "rule_commit": intro,
                    "rule_date": rule_date, "last_edit_date": last_edit,
                    "edits_total": n_edits}))
