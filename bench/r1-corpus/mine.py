#!/usr/bin/env python3
"""Mine intent-drift defects out of real git history.

For each repo: read the agent config at HEAD, extract PATH referents it declares,
find the ones that do not exist, then walk history to the commit that removed
each one.  A defect is only reported when the config file is BYTE-IDENTICAL at
that commit and its parent -- that makes the parent a perfect control: same repo,
same config, one difference in the tree.

Emits candidates only.  Every candidate is hand-reviewed and independently
re-confirmed before it enters the corpus.
"""
import json
import os
import re
import subprocess
import sys

CONFIGS = [
    "CLAUDE.md", "AGENTS.md", ".cursorrules", ".clauderules",
    ".github/copilot-instructions.md", "CONVENTIONS.md",
]

# a token that looks like a repo-relative path to a concrete file
PATHY = re.compile(r"^[A-Za-z0-9._][A-Za-z0-9._/@-]*$")
EXTS = (
    ".sh", ".bash", ".py", ".js", ".ts", ".mjs", ".cjs", ".rb", ".go", ".rs",
    ".toml", ".yaml", ".yml", ".json", ".md", ".txt", ".cfg", ".ini", ".xml",
    ".sql", ".tsx", ".jsx", ".mk", ".gradle", ".tf", ".proto", ".php", ".java",
)
# interpreter prefixes: the *next* token is the script
RUNNERS = {"bash", "sh", "zsh", "python", "python3", "node", "ruby", "perl",
           "deno", "bun", "uv", "poetry", "go", "cargo", "make", "just"}


def git(repo, *args, text=True):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True,
                          text=text, timeout=180)


def ok(repo, *args):
    return git(repo, *args).returncode == 0


def extract_referents(body):
    """Return {path: (lineno, line)} for every path-shaped referent declared."""
    out = {}
    for i, line in enumerate(body.splitlines(), 1):
        toks = []
        # backticked spans
        for span in re.findall(r"`([^`\n]{1,200})`", line):
            parts = span.split()
            toks.extend(parts)
            # `bash scripts/x.sh` -> also take the arg after a runner
            for a, b in zip(parts, parts[1:]):
                if a.split("/")[-1] in RUNNERS:
                    toks.append(b)
        # bare ./foo/bar.sh in prose
        toks.extend(re.findall(r"(?<![\w`])(\./[A-Za-z0-9._/-]+)", line))
        for t in toks:
            t = t.strip().strip("\"'(),;:").rstrip(".")
            if t.startswith("./"):
                t = t[2:]
            if not t or not PATHY.match(t):
                continue
            if t.startswith("/") or "*" in t or ".." in t:
                continue
            head_dir = t.split("/")[0]
            extless_ok = "/" in t and head_dir in (
                "scripts", "bin", "tools", "hooks", ".githooks", "ci", "cmd",
                "script", "utils", "dev", "devtools", "make", "packages",
                "crates", "apps", "services", "modules", "docs", "src", "lib",
                "test", "tests", "config", "internal", "pkg",
            )
            if not (t.endswith(EXTS) or ("/" in t and "." in t.split("/")[-1])
                    or extless_ok):
                continue
            if t.count("/") > 6 or len(t) > 120:
                continue
            # skip obvious non-repo referents
            if t.split("/")[0] in ("node_modules", "http:", "https:", "target",
                                   "dist", "build", "vendor", ".venv", "venv"):
                continue
            out.setdefault(t, (i, line.strip()))
    return out


def blob_id(repo, rev, path):
    r = git(repo, "rev-parse", f"{rev}:{path}")
    return r.stdout.strip() if r.returncode == 0 else None


def mine(repo, slug):
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    if not head:
        return []
    found = []
    for cfg in CONFIGS:
        r = git(repo, "show", f"HEAD:{cfg}")
        if r.returncode != 0:
            continue
        refs = extract_referents(r.stdout)
        for path, (lineno, line) in refs.items():
            if ok(repo, "cat-file", "-e", f"HEAD:{path}"):
                continue  # referent resolves -- not drift
            # the commit that most recently removed it (renames count as deletes)
            d = git(repo, "log", "--no-renames", "--diff-filter=D",
                    "--format=%H", "-1", "--", path)
            defect = d.stdout.strip().splitlines()
            if not defect:
                # never existed under this name: the drift arrived with the
                # DECLARATION, not with a tree change.  Control is the commit
                # before the declaration landed (assertion absent -> no finding).
                a = git(repo, "log", "--no-renames", "--diff-filter=AM",
                        "--format=%H", "--", cfg)
                intro = None
                for sha in a.stdout.split():
                    body = git(repo, "show", f"{sha}:{cfg}").stdout
                    if path in body:
                        intro = sha
                    else:
                        break
                if intro:
                    par = git(repo, "rev-parse", f"{intro}^").stdout.strip()
                    found.append({
                        "repo": slug, "config": cfg, "referent": path,
                        "declared_line": lineno, "declared_text": line[:300],
                        "defect_commit": intro, "parent_commit": par,
                        "config_untouched": False, "never_existed": True,
                        "head": head,
                        "defect_date": git(repo, "log", "-1", "--format=%cI", intro).stdout.strip(),
                        "defect_subject": git(repo, "log", "-1", "--format=%s", intro).stdout.strip()[:200],
                    })
                continue
            C = defect[0]
            par = git(repo, "rev-parse", f"{C}^").stdout.strip()
            if not par:
                continue
            if not ok(repo, "cat-file", "-e", f"{par}:{path}"):
                continue
            if ok(repo, "cat-file", "-e", f"{C}:{path}"):
                continue
            # was the declaration present, and the config untouched, at C?
            b_par, b_c = blob_id(repo, par, cfg), blob_id(repo, C, cfg)
            if b_par is None:
                continue  # config did not exist yet at the parent
            cfg_body = git(repo, "show", f"{par}:{cfg}").stdout
            if path not in cfg_body:
                continue
            found.append({
                "repo": slug,
                "config": cfg,
                "referent": path,
                "declared_line": lineno,
                "declared_text": line[:300],
                "defect_commit": C,
                "parent_commit": par,
                "config_untouched": b_par == b_c,
                "config_blob_parent": b_par,
                "config_blob_defect": b_c,
                "head": head,
                "defect_date": git(repo, "log", "-1", "--format=%cI", C).stdout.strip(),
                "defect_subject": git(repo, "log", "-1", "--format=%s", C).stdout.strip()[:200],
            })
    return found


if __name__ == "__main__":
    repo, slug = sys.argv[1], sys.argv[2]
    try:
        for rec in mine(repo, slug):
            print(json.dumps(rec))
    except Exception as e:
        print(f"# ERR {slug}: {e}", file=sys.stderr)
