---
name: prompt-verify-pass
description: Verify every concrete claim in socom's next-session prompt against the repo. Walk the prompt, extract claims, run the matching probe, and annotate each with VERIFIED / REWRITTEN / HYPOTHESIS. Fails closed on any un-labelled claim. Use at closeout before pushing the prompt, on any mid-session prompt rewrite, and retroactively when a next session refutes a claim. Triggers on "verify prompt claims", "closeout prompt verify", "/prompt-verify <path>", and any edit to `prompts/next-session-*.md`.
---

# Prompt Verify Pass

**Ported from Akili** (`/root/Akili/.claude/skills/prompt-verify-pass/SKILL.md`),
adapted to socom's claim types. The discipline, the three labels and the
fail-closed rule are Akili's and are unchanged. The probe table and the
regression tests are socom's, drawn from real misses.

## The framing — non-negotiable

Rank 1 of socom's own constitution, `verify-never-claim`:

> No task is done until concrete proof is shown. *"It should work"* is a
> violation: run the check, paste the output. **Evidence from a different
> session, or from before the final change, does not count — re-run after the
> last edit.**

A next-session prompt is a **claim about the repository**. Every concrete claim
is verified at write time or labelled un-verifiable. The next session trusts
labelled claims and re-probes only the unlabelled ones — that is the entire
point, and it fails the moment one claim slips through unlabelled.

⚠️ socom is the repo that filed `decisions/0004` Class A — *"reports what it
WROTE, not what took EFFECT."* A prompt that carries a number forward instead of
re-measuring it is the same defect, committed by the author rather than the tool.

## When to invoke

- **At closeout, before pushing the prompt.** Mandatory.
- **On any mid-session rewrite** of `prompts/next-session-*.md`.
- **Retroactively**, when a session refutes a claim a prior prompt marked
  VERIFIED — to find what the pass missed, then guard it (see §Telemetry).

## The three labels

Every concrete claim earns exactly one. Nothing escapes without one.

| Label | When | Annotation |
|---|---|---|
| **VERIFIED** | a probe confirmed it at write time | `(verified <sha>)`, `(L<n> @ <sha>)`, `(measured: <value>)` |
| **REWRITTEN** | the probe refuted it — **fix the body first**, then label | the claim is rewritten; no separate marker |
| **HYPOTHESIS** | cost estimate, operator preference, recommendation, or anything not probe-able | `(hypothesis — operator-driven)` |

**REWRITTEN never means "slap a label on a wrong claim."** It means the prompt
body changed to match what the probe returned.

## The probe table — socom's claim types

| Claim in the prompt | Probe | Annotation |
|---|---|---|
| A file or directory exists | `[ -f <path> ]` / `ls <dir>` | `(verified <sha>)` |
| A bucket row's ID **and state** | `grep -nE '^- \`<ID>\` \*\*(READY\|DONE) P[01]' buckets/<f>.md` | `(L<n> @ <sha>)` |
| Bucket **counts** ("7 DONE P0 / 1 READY P0 / 9 READY P1") | `grep -cE '^- \`DEF-.*(DONE P0\|READY P0\|READY P1)' buckets/defects.md` | `(measured: N)` |
| A decision exists / its status | `ls decisions/` + `sed -n '3p' decisions/000N-*.md` | `(verified <sha>)` |
| A commit SHA | `git cat-file -e <sha>` | `(verified <sha>)` |
| CI is green on a SHA | `gh run list -L1 --json conclusion,headSha` | `(measured: success @ <sha>)` |
| Suite numbers ("unit 348 / r1corpus 146") | **run them** — `python3 tests/unit.py \| tail -1` | `(measured: 348 passed)` |
| `gate full` / `build.py --check` | `./bin/socom gate full`, `python3 build.py --check` | `(measured: PASS)` |
| **Public artifact bytes / build digest** | `curl -w 'bytes=%{size_download}'` + `cmp` against `bin/socom` + `./bin/socom version` | `(measured: <bytes>, <digest>)` |
| A code reference `file.py:N` | `sed -n '<N>p' src/socom/<file>` — the line must be **non-blank** and contain the cited symbol | `(mechanism verified: <one-liner>)` |
| Proof tier | `ls bench/exposure/` — a dated sheet, or it is still D0 | `(measured: D0, template only)` |
| Cost, effort, "should", "recommend", "~2h" | not probe-able | `(hypothesis — operator-driven)` |

## Workflow

1. **Read the prompt end to end.** Note every concrete claim.
2. **Extract into a working list** — claim text, claim type, probe command.
3. **Run the probes.** In parallel where independent. Record each result.
4. **Label.** PASS → annotate. REFUTED → rewrite the body, *then* annotate.
   Not probe-able → `(hypothesis — operator-driven)`.
5. **Run the grep gate** (below). It must not be short.
6. **Commit and push** — only after the gate passes.

### The grep gate

```sh
grep -cE '\(verified |\(L[0-9]+ @|\(measured: |\(mechanism verified: |\(hypothesis' \
  prompts/next-session-*.md
```

The count must equal the number of concrete-claim lines. If it is short, find the
unlabelled lines and either label them or delete the assertion.

## Fail closed

Refuse to declare the pass clean if:

- any concrete-claim line lacks a label after step 4;
- any VERIFIED claim re-probes to refute — the annotation lied, which is worse
  than no annotation;
- the grep count is below the visible concrete-claim count;
- **any number that moves when `bin/socom` moves was carried instead of
  re-measured** (see Test 1).

## Regression tests — real misses, socom's own

### Test 1 — the carried byte count (2026-08-05, three times)
**Claim:** *"public curl URL — 200, 408964 bytes."*
**Probe:** `curl -w 'bytes=%{size_download}'` + `cmp` against `bin/socom`.
**Result:** 408964 → **411152** (after `socom version` shipped) → **421735**
(after the three P0 repairs). The prompt header carried the stale number across
two builds; `bench/exposure/README.md` was still citing `408964` at `d23fa0c`
three builds later, inside the preflight a participant is told to trust.
**Guard:** any artifact number is re-measured every pass. Never carried. The
prompt now says so in its own header.

### Test 2 — the severity claim refuted in the wild in two minutes
**Claim:** `DEF-QUICKSTART-REPORTS-ADOPTION-IN-NON-GIT-REPO-01` — *"the non-git
version needs an unusual setup."*
**Probe:** none was run; it was reasoned.
**Result:** the operator hit it by accident on their own machine, following
`PILOT.md` verbatim, inside two minutes.
**Guard:** a severity or reachability claim is a claim. Either probe it — can I
reach this state by following the documented path? — or label it
`(hypothesis — operator-driven)`.

### Test 3 — the citation that pointed at a blank line
**Claim:** `lifecycle.py:920-947 (adoption_rung)` in `decisions/0004`.
**Probe:** `sed -n '920p' src/socom/lifecycle.py` → **empty**; the `def` is at
`922`.
**Result:** REWRITTEN to `922-947` before commit.
**Guard:** every `file.py:N` is `sed -n 'Np'`-ed and must be non-blank *and*
contain the cited symbol. A citation that does not resolve is worse than none —
it looks checked.

### Test 4 — "filed" for something never filed
**Claim:** a note in `bench/exposure/README.md` reading *"Filed; harmless here."*
**Probe:** `grep` the buckets for the row.
**Result:** no such row existed. REWRITTEN to *"Not filed (cosmetic)."*
**Guard:** *"filed"*, *"fixed"*, *"recorded"*, *"tested"* are claims about the
repo, not prose. Each gets a `grep`. This is Class A in the author's own writing.

## Claim ledger — the author's working artifact, not committed

```
claim                                   | label      | probe result
---                                     | ---        | ---
"421735 bytes, build 1bc70ac4f16c"      | VERIFIED   | curl+cmp+version, re-run
"7 DONE P0 / 1 READY P0 / 9 READY P1"   | VERIFIED   | grep -c, measured
"needs an unusual setup"                | REWRITTEN  | reproduced in 2 min in the wild
"lifecycle.py:920 adoption_rung"        | REWRITTEN  | line 920 blank; def at 922
"~2h for the labelling column"          | HYPOTHESIS | no spike run
```

## Telemetry — a miss becomes the next guard

If a session refutes a claim this pass marked VERIFIED:

1. File a `WORKFLOW-PROMPT-VERIFY-MISS-<NN>` row in `buckets/`.
2. Add the missed claim type as a row in the probe table above.
3. Add it as a numbered regression test here.

The four tests above are that loop already having run once.
