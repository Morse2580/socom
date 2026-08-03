#!/usr/bin/env python3
"""Re-verify every gold candidate under a STRICT existence predicate and
recompute declaration line numbers against the PARENT's config (not HEAD's).

Existence predicate: `git ls-tree <rev> -- <path>` non-empty.  This is correct
for blobs AND trees; `git cat-file -e` is not (it rejects trailing slashes and
cannot express "this directory exists").
"""
import json
import subprocess


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True,
                          text=True, timeout=180)


def exists(repo, rev, path):
    p = path.rstrip("/")
    r = git(repo, "ls-tree", rev, "--", p)
    return r.returncode == 0 and bool(r.stdout.strip())


def declaration_sites(body, referent):
    """Every line of `body` that declares `referent`. Returns [(lineno, text)]."""
    out = []
    for i, line in enumerate(body.splitlines(), 1):
        if referent in line or referent.rstrip("/") in line:
            out.append((i, line.strip()))
    return out


recs = [json.loads(l) for l in open("candidates2.jsonl")]
gold = [r for r in recs if r.get("config_untouched")]
out = []
for r in gold:
    d = "repos/" + r["repo"].replace("/", "_")
    par, C, path, cfg = r["parent_commit"], r["defect_commit"], r["referent"], r["config"]
    # strict re-verification of the whole pair
    checks = {
        "referent_at_parent": exists(d, par, path),
        "referent_at_defect": exists(d, C, path),
        "referent_at_head": exists(d, "HEAD", path),
        "config_at_parent": exists(d, par, cfg),
        "config_at_defect": exists(d, C, cfg),
    }
    body = git(d, "show", f"{par}:{cfg}").stdout
    sites = declaration_sites(body, path)
    kind = "tree" if git(d, "ls-tree", par, "--", path.rstrip("/")
                         ).stdout.split()[1:2] == ["tree"] else "blob"
    r2 = dict(r)
    r2.update({
        "strict": checks,
        "declaration_sites": sites,
        "referent_kind": kind,
        "valid_pair": (checks["referent_at_parent"] and not checks["referent_at_defect"]
                       and not checks["referent_at_head"] and checks["config_at_parent"]
                       and checks["config_at_defect"] and bool(sites)),
    })
    out.append(r2)

with open("gold-verified.jsonl", "w") as f:
    for r in out:
        f.write(json.dumps(r) + "\n")

good = [r for r in out if r["valid_pair"]]
bad = [r for r in out if not r["valid_pair"]]
print(f"valid pairs under strict predicate: {len(good)}/{len(out)} "
      f"across {len({r['repo'] for r in good})} repos")
for r in bad:
    print("  DROPPED", r["repo"], r["referent"], r["strict"], "sites=", len(r["declaration_sites"]))
