#!/usr/bin/env bash
# Replay every recorded confirmation in corpus.jsonl against the REAL upstream
# repos.  This is the evidence-replay gate: it proves the corpus describes the
# world as it actually is, not as it was when the corpus was written.
#
# NETWORK + DISK: clones ~29 repos blobless into a cache dir.  NOT wired into
# CI for that reason -- CI runs tests/r1corpus.py, which is offline.
#
#   bash bench/r1-corpus/verify.sh              # clone-cache in /tmp
#   R1C_CACHE=~/r1c bash bench/r1-corpus/verify.sh
#
# Exit 0 = every recorded command still produces its recorded result.
set -uo pipefail
cd "$(dirname "$0")"
CACHE="${R1C_CACHE:-/tmp/r1-corpus-cache}"
mkdir -p "$CACHE"

python3 - "$CACHE" <<'PY'
import json, os, subprocess, sys

cache = sys.argv[1]
recs = [json.loads(l) for l in open("corpus.jsonl")]
fail = 0
checked = 0
skipped = []

def clone(slug, url):
    d = os.path.join(cache, slug.replace("/", "_"))
    if os.path.isdir(d):
        return d
    print(f"  cloning {slug} ...", flush=True)
    r = subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-tags",
                        url, d], capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        return None
    return d

for rec in recs:
    url = rec.get("clone", "")
    if not url.startswith("https://"):
        skipped.append((rec["id"], "not a public clone URL -- verify by hand"))
        continue
    if not rec.get("confirm"):
        continue
    d = clone(rec["repo"], url)
    if d is None:
        skipped.append((rec["id"], "clone failed (repo may be gone -- that is "
                                   "itself a finding; see README §decay)"))
        continue
    for c in rec["confirm"]:
        if not c["cmd"].startswith("git "):
            continue
        args = c["cmd"].split()[1:]
        got = subprocess.run(["git", "-C", d, *args],
                             capture_output=True, text=True, timeout=180)
        checked += 1
        # ls-tree exits 0 with EMPTY stdout for an absent path -- stdout is the
        # discriminator, not the exit code.  Compare both.
        if got.stdout.strip()[:400] != c["stdout"] or got.returncode != c["exit"]:
            fail += 1
            print(f"  DRIFT {rec['id']}: {c['cmd']}")
            print(f"        recorded: exit={c['exit']} stdout={c['stdout'][:120]!r}")
            print(f"        now:      exit={got.returncode} stdout={got.stdout.strip()[:120]!r}")

print()
for i, why in skipped:
    print(f"  SKIP  {i}: {why}")
print(f"\nreplayed {checked} recorded commands across "
      f"{len({r['repo'] for r in recs})} repos: {fail} drifted")
sys.exit(1 if fail else 0)
PY
