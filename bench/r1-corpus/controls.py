#!/usr/bin/env python3
"""Find the non-defect control classes:

  honest  -- every path referent in the config resolves at HEAD, and there are
             ENOUGH of them that a non-vacuity assertion has teeth
  prose   -- a config with ZERO checkable path referents ("nothing to check")
"""
import json
import subprocess
import sys

sys.path.insert(0, ".")
from mine import CONFIGS, extract_referents  # noqa: E402


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True,
                          text=True, timeout=180)


def exists(repo, rev, path):
    r = git(repo, "ls-tree", rev, "--", path.rstrip("/"))
    return r.returncode == 0 and bool(r.stdout.strip())


d = "repos/" + sys.argv[1]
slug = sys.argv[1].replace("_", "/", 1)
head = git(d, "rev-parse", "HEAD").stdout.strip()
ncommits = git(d, "rev-list", "--count", "HEAD").stdout.strip()
first = git(d, "log", "--reverse", "--format=%cI", "-1").stdout.strip()[:10]

for cfg in CONFIGS:
    r = git(d, "show", f"HEAD:{cfg}")
    if r.returncode != 0:
        continue
    refs = extract_referents(r.stdout)
    if not refs:
        print(json.dumps({"kind": "prose", "repo": slug, "config": cfg,
                          "head": head, "commits": ncommits, "first": first,
                          "referents": 0, "lines": len(r.stdout.splitlines())}))
        continue
    missing = [p for p in refs if not exists(d, "HEAD", p)]
    if not missing and len(refs) >= 6:
        print(json.dumps({"kind": "honest", "repo": slug, "config": cfg,
                          "head": head, "commits": ncommits, "first": first,
                          "referents": len(refs),
                          "referent_list": sorted(refs)}))
