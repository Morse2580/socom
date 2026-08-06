---
name: ship-and-verify
description: Drive a socom change from edited source to pushed-CI-green-and-re-preflighted. Rebuild bin/socom from src, run the gate BY HAND (socom's own checkout has no hooks wired), commit direct to main, watch CI, then re-measure the public curl artifact a participant would download. Encodes the cycle run 4x in one session so the 5th is not hand-rolled. Triggers on "ship this", "ship and verify", "push it", "commit and push", "take this to CI green", and any time a src/socom edit is ready to land.
---

# Ship and Verify — socom

**Ported from Akili** (`/root/Akili/.claude/skills/ship-and-verify/SKILL.md`).
The *shape* is Akili's — serial externally-timed gates, driven by the model, not
a workflow. Every mechanic is socom's, because none of Akili's apply: there are
no worktrees, no `glab`, no MRs, no merge train, no deploy tag and no pixel step
here. socom commits **directly to `main`**.

The cycle: **edited source → rebuilt artifact → gate PASS → main → CI green →
the public artifact re-measured.** The last step is the one people skip and it
is the only one a participant ever touches.

## Preconditions

- `pwd` is `/root/socom`. It is a **SIBLING** of `/root/Akili`, not inside it —
  Akili's `CLAUDE.md` does not govern here.
- `git pull --ff-only` first, and `git status --porcelain` is empty of anything
  you did not intend to ship.
- You edited `src/socom/*.py`. **Never edit `bin/socom`** — it is the assembled
  artifact, and `python3 build.py --check` is a CI gate that will catch you.

## Step 1 — Rebuild, and prove the rebuild

```sh
python3 build.py && python3 build.py --check
```

`--check` must say *up to date*. A src edit without a rebuild is committed-artifact
drift; CI fails on it, but a full local gate run wastes minutes first.

## Step 2 — Run the gate YOURSELF

```sh
./bin/socom gate full
```

⚠️ **socom's own checkout has `core.hooksPath` UNSET** *(verified: `git config
core.hooksPath` → rc=1)*. Nothing runs automatically. The tool that plants gates
in adopted repos does not enforce them on itself, so the discipline is manual and
there is no safety net if you skip it.

`gate full` chains `tests/smoke.sh` (which itself chains `tests/unit.py`,
`tests/orchestration_e2e.py`), `xmlcheck`, `ledgercheck`, `mcp`, `r1corpus`,
`context verify`, `index`. For a fast inner loop run `python3 tests/unit.py`
alone; run `gate full` before **every** push.

## Step 3 — Commit direct to main

One commit, real body: what the defect was, what the repair is, and the evidence
that separates them. If it closes a bucket row, the row is edited in the same
commit and carries its own re-run output — see `bucket-ledger-reconcile`.

## Step 4 — Push and watch

```sh
git push
gh run watch $(gh run list -L1 --json databaseId -q '.[0].databaseId') --exit-status
gh run list -L1 --json conclusion,headSha -q '.[0].conclusion + " @ " + .[0].headSha[0:7]'
```

Read the conclusion back rather than assuming the watcher's exit code told you.

## Step 5 — Re-preflight the PUBLIC artifact (the load-bearing step)

`bin/socom` on `main` **is the product**. A participant runs `curl`, not your
working tree.

```sh
curl -fsSL -o /tmp/socom.post \
  https://raw.githubusercontent.com/Morse2580/socom/main/bin/socom \
  -w 'http=%{http_code} bytes=%{size_download}\n'
chmod +x /tmp/socom.post && cmp /tmp/socom.post bin/socom && /tmp/socom.post version
```

Expect `http=200`, `cmp` silent, and a `build <digest>` line — the digest is
`sha256(bin/socom)[:12]`, so it names the artifact a participant actually ran.

⚠️ **The byte count and digest change on ANY merge touching `bin/socom`.** They
are re-measured every ship and **never carried**. Both live in
`bench/exposure/README.md` and in the next-session prompt; update both, or the
preflight a participant is told to trust is a stale number.

## Failure modes seen in the wild (all of these, in one session)

- **A SHA cited inside the commit that creates it.** A placeholder SHA was
  written into the prompt, then committed — the SHA never existed. *A claim about
  a commit cannot be written inside that commit.* Cite it from a later one.
- **`--amend` orphaning a SHA you already cited.** The corrected SHA was amended
  away seconds later. Prove reachability, don't eyeball:
  `git merge-base --is-ancestor <sha> HEAD; echo rc=$?` — `rc=0` or it is not on
  `main`.
- **Line numbers moving under a citation.** `core.py:154` became `:169` in a
  refactor the same day. `sed -n '<N>p'` every `file.py:N` before quoting it, and
  prefer the symbol — the line number is not durable.
- **The artifact byte count carried instead of re-measured.** It went stale across
  three builds inside `bench/exposure/README.md`. This is `prompt-verify-pass`
  regression Test 1, and it recurs because the number looks like documentation.
- **Editing `bin/socom` directly.** Green locally, red in CI on `build.py --check`.

## The bound

CI green is not "the change works." It is *the suites that exist passed*. What
makes a repair real is a test that FAILS against the pre-fix tree — build one
with `git archive HEAD | tar -x -C <dir>` before you claim the row is closed.
