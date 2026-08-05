<!--
CLAIM-VERIFY PASS — 2026-08-05, probed against the tree at the SHA below.
Every concrete claim in this prompt was re-run, not carried over.
  VERIFIED  socom main SHA + clean tree ......... git rev-parse / status
  VERIFIED  buckets: 4 DONE P0 / 7 READY P1 ..... grep -cE '^- `DEF-.*(DONE P0|READY P1)'
  VERIFIED  build.md 1 READY + 8 BLOCKED ........ grep -cE '^- `.*(READY|BLOCKED)'
  VERIFIED  EV-NONAUTHOR-EXPOSURE-01 READY P0 ... grep, still unrun
  VERIFIED  bench/exposure/{README,TEMPLATE}.md . ls
  VERIFIED  decisions/0001 + 0002 + 0003 ........ ls
  VERIFIED  unit 339 passed / r1corpus 146 ...... python3 tests/{unit,r1corpus}.py
  VERIFIED  public curl URL 200, 408964 bytes ... curl -w, cmp against bin/socom
  VERIFIED  proof tier D0, unchanged ............ bench/exposure/ holds the template only
  REWRITTEN row headline read "five engineers" .. reconciled to n=1 this session
  HYPOTHESIS none.

RE-VERIFIED 2026-08-05 (second pass, at d1b090e after the 0003 commit). Every
line above was re-run, not carried: SHA/clean-tree, 4/7/1/8 bucket counts,
EV row still READY P0 unrun, unit 339 / r1corpus 146, curl http=200
bytes=408964 byte-identical to bin/socom. NOTHING MOVED. The standards research
below added one document and zero capability -- which is the point of recording it.

REWRITTEN 2026-08-05 (third pass, at b7b6a32). `socom version` shipped, so
bin/socom changed and the byte count above is SUPERSEDED:
  REWRITTEN public curl URL ... 408964 -> **411152** bytes, still http=200 and
            byte-identical to bin/socom; /tmp/socom.pre version -> b80c5efc6013
  VERIFIED  digest is content-bound  negative control: appending one comment to
            a copy moved it b80c5efc6013 -> d2ef64b7fa0c
  VERIFIED  suites after the change  unit 339 / r1corpus 146, gate full PASS,
            build.py --check up to date, CI success on b7b6a32
  UNCHANGED buckets 4/7/1/8, EV row READY P0 unrun, proof tier D0
⚠️ The byte count changes on ANY merge touching bin/socom. Re-run the preflight;
never carry it forward.

RE-VERIFIED 2026-08-05 (fourth pass, at 5894df9 — the breakage sweep + two scouts).
  REWRITTEN buckets ......... defects now 4 DONE P0 / **3 READY P0** / 7 READY P1
  VERIFIED  build.md ........ 1 READY (R1) + 8 BLOCKED, unchanged
  VERIFIED  EV row .......... EV-NONAUTHOR-EXPOSURE-01 READY P0, STILL UNRUN
  VERIFIED  decisions ....... 0001 + 0002 + 0003 (3 files)
  VERIFIED  suites .......... unit 339 / r1corpus 146 / gate full PASS
  VERIFIED  public URL ...... http=200, 411152 bytes, byte-identical, build b80c5efc6013
  UNCHANGED proof tier ...... D0
-->

# Next session — stop building. Run the n=1 exposure.

**Row:** `EV-NONAUTHOR-EXPOSURE-01` (`buckets/evidence.md`), **READY P0**, `n=1`.
**Governed by** `decisions/0001-exposure-before-capability.md`.
**Record it on the sheet:** copy `bench/exposure/TEMPLATE.md` to
`bench/exposure/<YYYY-MM-DD>-<handle>.md`.

## Where the repo is

**Everything here is relative to `/root/socom`** — a SIBLING of `/root/Akili`,
not inside it. `cd /root/socom && git pull` first; check `pwd` before any edit.
Akili's `CLAUDE.md` does not govern here: no worktrees, no row claims, no `glab`,
no MRs. Commit **directly to `main`**, push, watch with `gh run watch`.
`bin/socom` is BUILT from `src/socom/*.py` — edit the source, run
`python3 build.py`, commit both (`python3 build.py --check` is a CI gate).
socom's own hooks are not wired in its checkout, so run `./bin/socom gate full`
yourself before every push.

## The one thing this session is for

**Put socom in front of one engineer who is not the author, watch in silence,
write down where they stop.** That is the whole session. It is not a coding task
and there is no code deliverable.

The root gate authorised exactly this — *"one non-author engineer, observed"* —
and it has never been done. Five months, six artifacts, zero non-author users,
proof tier **D0**. Every capability row in `buckets/build.md` is BLOCKED on it.

**Everything you need is already prepared.** `bench/exposure/README.md` is the
protocol (recruit → ask → session → record → the one-week second-use check) and
`TEMPLATE.md` is the observer's sheet. Read the README once and run it. Do not
re-derive the protocol, and do not improve the sheet instead of using it.

⚠️ Do not demo it. ⚠️ Do not fix `PILOT.md` first — where it confuses a stranger
IS the finding. ⚠️ Do not substitute an agent: agents can falsify but cannot
confirm, and one cohort already ran (2026-08-03). ⚠️ Do not recruit someone who
owes you a favour — politeness produces a first use and never a second, and
second use is the metric.

**Preflight, 30 seconds, before the session** (a broken first touch burns a
scarce participant on nothing):

```sh
curl -fsSL -o /tmp/socom.pre \
  https://raw.githubusercontent.com/Morse2580/socom/main/bin/socom \
  -w 'http=%{http_code} bytes=%{size_download}\n'
chmod +x /tmp/socom.pre && /tmp/socom.pre --help | head -3 && /tmp/socom.pre version
```

Verified 2026-08-05 (re-run after `b7b6a32`): `http=200`, **411152 bytes**,
byte-identical to `bin/socom`, `--help` prints the command list, and `version`
reports build `b80c5efc6013`. **Also confirm the participant is on
macOS/Linux/WSL** — native Windows is unsupported and finding out mid-session
wastes the run.

⚠️ **Record the `version` output on the sheet.** `socom version` landed
2026-08-05 for exactly this: the digest is a sha256 of the running file, so it
identifies the build a participant actually ran — which the static `0.1` version
string cannot, and which the sheet previously asked for as a *commit* the
participant has no way to know. A result that cannot name its build is not
reproducible evidence. The byte count above **will change on any merge that
touches `bin/socom`** — re-run the preflight, do not trust this number.

## What changed on 2026-08-05

A class sweep and one smoke run, no code. **Three defect rows filed, none
repairable-first**:

- `DEF-UNRESOLVABLE-GATE-LEAVES-NO-TRACE-01` — when a gate cannot run at all,
  socom records nothing, so a repo whose `core.hooksPath` still declares socom's
  gates commits ungated indefinitely and no socom surface can say so. Needs the
  downloaded file moved or cleaned *after* install — takes days.
- `DEF-BLACKBOARD-GRANTS-ON-UNREACHABLE-REMOTE-01` — **highest-severity P1.**
  With an unreachable remote, `claim` **grants** a lease it would have refused,
  and the record it writes is byte-identical to a published one. Measured: two
  sessions both holding the same path, each `--scan` reporting itself as sole
  holder. Needs two concurrent sessions.
- `DEF-QUICKSTART-REPORTS-ADOPTION-IN-NON-GIT-REPO-01` — the adoption percentage
  and rung count what socom **planted**, not what it can **enforce**. Measured in
  an empty non-git dir: `quickstart` says `! hooks NOT wired: not a git repo`,
  then plants 33 files and reports `33% · T2 — compiled`. The non-git case is the
  extreme; the same decoupling fires in a normal git repo whenever check-detection
  fails, and **that version can reach a single participant**. Filed P1
  deliberately unrepaired — `PILOT.md` asks *"did a metric mislead you?"*, so this
  IS a finding the participant should generate.

⚠️ **A `quickstart` was run on the author's own machine (`/home/akili`,
`G1-Stack`) on 2026-08-05. That was a smoke test, NOT the exposure** — it moved
nothing, because the author is not a non-author. It is where the row above came
from. Do not let a second one of these stand in for the run.

The first two share a class: *enforcement whose declaration is durable, whose capability
resolves through a referent socom does not own, and whose resolution failure
degrades open without a trace* — which socom's own `canon/residuality.xml`
`compromise-recording` names, and the code fails. Full sweep (6 instances, 6
sites checked clean, 2 bounded residues) is the appendix of
`decisions/0002-unresolvable-enforcement-must-record.md`.

**0002 is HELD at the gate and must stay held.** The defect is D2; the *fix*
mechanism is D0 and cuts a shell/Python format contract, which the root gate caps
at D1. Do not build it. When it is time, step 1 is a one-hour spike of U1 alone.

⚠️ **0003 sharpened 0002's spike question — read it before the spike, not during.**
`bb_do_claim` (`blackboard.py:488-494`) **already detects** the publish failure and
already returns `result["published"]` + `result["publish_error"]`. socom is not
blind: the gap is **durability, not detection** — the record appended to the shard
is byte-identical either way, while `published` lives only in the in-memory result.
That is a smaller problem than the defect row reads as. But `log_breach`
(`core.py:94`) writes `.socom/gates/breaches.log`, a **local file**, and the party
the record exists to inform is a different session on a different machine — so the
one mechanism socom already has does not reach across the boundary. The spike's
question is therefore: **can the writer half ship alone, or does a durable
`published` flag force the reader-side join immediately?** Answer it; do not assume
it either way.

## What ALSO happened on 2026-08-05 — a standards review, adopted nothing

An external reviewer proposed seven standards for the attestation brief with a
recommended sequencing (git notes + JSON Schema now; SCITT + TUF at first fork).
Four bounded scouts ran, primary sources only, every load-bearing verdict
re-verified directly. **Six of seven refuted or reframed. Nothing adopted. Zero
code.** The verdict is `decisions/0003-no-standard-binds-a-fork.md` (Accepted).

**Do not re-derive this, and do not act on the critique if it resurfaces.** The
three things worth carrying:

1. **No standard can make a party you cannot execute inside enforce your policy.**
   SCITT/RFC 9943 was proposed as delivering fork inheritance; the RFC contains
   **zero** occurrences of `federat*`, the TS *operator* owns the Registration
   Policy (§5.1.1.2), and §12 gives the **relying party** the trust choice, not the
   base an authority. TUF/OCI hit the same wall from another spec family. So
   "fork inheritance" as framed is unachievable — the achievable shape is
   **detect divergence and withdraw trust**. Reopens only at fork > 0.
2. **The one surviving idea is already ratified here.** SCITT §5.1.1.2 ("make the
   registration checks reproducible") is `canon/residuality.xml:95-99`
   compromise-recording, in socom's own words, with the failure condition named.
   An IETF RFC making it normative is **corroboration of the principle** — and an
   indictment of the two open defects that violate it. It is **not** evidence
   about socom, and must never be cited as such.
3. **git notes is not the cheap move** — it does not propagate (zero notes
   references in `git-push(1)`/`git-fetch(1)`), does not survive squash-merge
   (`notes.rewrite.<command>` is *"currently amend or rebase"*; `notes.rewriteRef`
   has no default), and its local-add/separate-push shape reproduces exactly the
   `bb_append`→`bb_push` ordering behind the blackboard defect. Same defect, new
   ref name.

⚠️ **This proves nothing about whether socom is necessary.** The standards fail at
an *adjacent* problem, and socom has the *same* cross-boundary limit it just found
in SCITT and TUF. Necessity is an adoption question at D0. Only the exposure moves it.

⚠️ **The blackboard defect also breaks Phase 3a's instrument.** That trial needs
3+ concurrent people — exactly when it fires — so a low tally could not
distinguish "thesis wrong" from "a participant's remote was refusing and their
leases were invisible." Cross-referenced into `EV-TRIAL-PROTOCOL-CONFOUND-01`.
It does **not** block the n=1 exposure.

**One capability row was filed and then evaluated the same day.**
`BUILD-ACP-RUNTIME-SEAM-01` (BLOCKED **P2**) — socom hand-rolls one vendor
binding per agent (`RUNTIMES` has a single entry) where the Agent Client
Protocol is the standard, adopted across 25+ agents since 2025-08 and never once
mentioned in this repo. It was filed at P1 on the argument that an ACP *proxy*
shape would give zero planted files and zero git-config writes, and so answer the
entry-shape problem. **That argument was probed and refuted the same day** — 3 of
8 gates are git-triggered and ACP has no `git commit`; `.socom/` carries 17 state
directories; the blackboard pushes `refs/socom/blackboard` by design; and
`PILOT.md`'s audience is terminal Claude Code, not an ACP session. The narrow
seam survives (~3 d). **The cheap way to separate `0001`'s two hypotheses is not
that row — it is shipping R1 standalone, which is already the READY row.**
Read the row's `EVALUATED` block before acting on any of it.

## The 5-substrate breakage sweep — 2026-08-05, three P0s filed

Five agents, five isolated shallow clones, one ecosystem each (Node/express ·
Go/cobra · Rust/fd · Python/click · no-build/github-gitignore), each given only
the public `curl` URL, **forbidden** from reading socom's source to work around a
failure or installing a toolchain to keep going. Build `b80c5efc6013`.

**Zero crashes, zero hangs, 20+ subcommands. The tool is robust.** What it has is
claims outrunning capability — and three that mutate state the user never agreed
to. Those three are now **READY P0** in `defects.md`, each REPRODUCED by the
primary session (local bare remote; nothing outbound), not taken on agent report:

- `DEF-CLAIM-PUSHES-TO-HOST-REMOTE-01` — `claim` pushes `refs/socom/blackboard`
  to the **adopted repo's own origin**, unprompted. It only failed on
  `pallets/click` because that agent lacked push rights.
- `DEF-PRECOND-SILENTLY-REVERSES-UNADOPT-01` — `unadopt` works; the next
  `precond` silently re-sets `core.hooksPath` and scores it `PASS / 1 healed /
  0 blockers`. Found independently by two agents. The documented exit is not durable.
- `DEF-RELEASE-NEVER-RELEASES-01` — both forms exit **0** saying "no live lease
  held" while `claim --scan` lists the lease before and after.

⚠️ **The P0 cap moved 4 → 7. That is not a licence to grow it** — see the §Note in
`defects.md`. The same sweep produced a much longer list and every other finding
went to P1 or nowhere.

**The asymmetry worth carrying** (it reframes the already-filed metric row):
socom is **honest when detection FAILS and misleading when detection SUCCEEDS
WRONGLY**. On the no-build repo it binds `true`, prints `unbound — passing` at
every gate, `doctor` exits 1, and it reads **33% · T2** — exactly as the filed row
predicted. On the other four it binds a command that exits 127 (`pytest -q` on a
**Rust** repo), `doctor` says **clean**, it reads **100% · T6 — operational**, and
`git push` is **hard-blocked** because `checks.full` is the pre-push RED band.
Most real repos have a detectable test command, so the second column is the
common case and it is the one nobody had measured.

## What the two scouts found — read before touching R1

1. **The premise is REFUTED as a top-tier developer pain.** No primary source
   (HN, Reddit, GitHub issues, Cursor forum) where a developer complains that an
   instruction file told the agent something false. The loud, repeatedly-sourced
   complaint is the **mechanical inverse** — agents ignoring rules that are still
   **correct**: `anthropics/claude-code#15443` ("ignores explicit CLAUDE.md
   instructions"), `#37888` ("runs explicitly forbidden destructive git
   commands"), Cursor forum (".cursorrules … perhaps only 20-25% effective").
   Drift is real but researcher-discovered (arXiv 2606.09090: 23% of 356 repos,
   **1.27%** of individual references) with **no** developer-voice grounding.
   ⚠️ Caveat kept: no survey has ever *asked* this question, so absence of
   complaint may be an availability effect. You may not assume that — you would
   have to test it. **All three citations verified live.**
2. **Prior art: PARTIAL, and it splits R1 in half.** `giacomo/agents-lint`
   ("Your AGENTS.md is probably lying") already ships **existence**-checking —
   dead paths, dead npm scripts. Verified live: 12★, 2 forks, **no license at
   all**, dormant since 2026-03-26. **Git-history contradiction is its unreleased
   roadmap item and was found in no shipped tool.** Entry shape is a *documented*
   cost, not theoretical: `core.hooksPath` is a single slot — `husky#1574` (open),
   `lefthook#1248` (closed, "Unset core.hookspath"), and lefthook markets *not*
   rewriting it as a differentiator.

**R1's acceptance prose was corrected 2026-08-05 to match its corpus** (`5894df9`)
— 18/19 corpus defects are `paired-parent` (referent EXISTS in both commits; it
was *edited* in violation of a rule), only 1/19 is missing-referent. An
existence-checker scores ≈1/19 and cannot pass. Read the row before implementing.

⚠️ **Open for the operator, NOT actioned:** the field evidence points at the
**enforcement** half (gates/hooks re-asserting a rule at the moment of action —
which is what the loud pain calls for) rather than the **detection** half (R1).
That contradicts `decisions/0001`'s R1-before-blackboard ordering, which is
ratified. Amending it is an operator decision, not a session's. Counter-argument
to keep: nobody has used the gates either, and this sweep showed them bound to
`pytest -q` on a Rust repo and `true` on a repo with no tests.

## The three assessments that should still weaken the instinct to build

1. **Build order/shape (scout, 2026-08-04).** Execution is rigorous; the *order*
   and *entry shape* are wrong for the population socom needs. Planting ~32 files
   and rewriting `core.hooksPath` spends first-contact trust before earning any.
   §4 of the recording sheet now captures the participant's reaction to exactly
   this — free, and it confirms or refutes the assessment.
2. **The adoption model contaminates its own experiment.** A stranger cannot
   evaluate "is drift-detection useful" without also absorbing "will this rewrite
   my git hooks." Two hypotheses, one test, inseparable result.
3. **R1 measured, not guessed.** Against Akili's 815-line `CLAUDE.md`, only 13%
   of 576 statements name a checkable referent, and actual drift is ~0. R1's hard
   problem is precision, not detection.

## Do NOT do these

- **Do not run a sixth agent cohort.** One ran 2026-08-03 (cold-run, ~30 defects)
  and a second ran 2026-08-05 (5-substrate breakage sweep, 3 P0s). Both were
  falsification and neither moved the D-tier by a millimetre — agents do not
  quit, and the stall point is the measurement. A third buys nothing.
- **Do not repair the three new P0s *instead of* running the exposure.** They are
  filed as pre-exposure because a participant hitting them is burned on something
  already written down. Fix them, then run it — not fix them and call it a session.
- **Do not work the P1 defects.** Seven are filed now, all cheaper and more
  interesting than the exposure, and they measure nothing.
  `DEF-STATUS-CLAIMS-UNLABELLED-01` is P1 **on purpose** — `PILOT.md` asks *"did
  a metric mislead you?"*, so repairing it first deletes a finding the
  participant is meant to generate (`0001` §Amendment 1 rule 3).
- **Do not build any capability.** Everything except R1 reads BLOCKED.
- **Do not build R1 either**, unless the exposure has happened. If you do, ship
  it **standalone** — own binary, zero adoption, zero git-config writes, no
  `.socom/` — so the two hypotheses stay separable.
- **Do not run another agent cohort.** It cannot move the D-tier.
- **Do not run a second participant to get a nicer answer.** `n=1` is what the
  root gate authorised; a confident *yes* is what §14.4's five-after-R1 is for.
- **Do not adopt a standard, and do not re-run the standards research.** Seven
  were evaluated 2026-08-05 and none survived; `decisions/0003` records each
  verdict with its primary-source citation. A well-argued external critique is
  the most legitimate-looking reason yet to not run the exposure — it is still
  not a reason. Reopens only at fork > 0.

## Cheaper alternative if no engineer is reachable this week

Test the *premise* instead of the tool: ask three engineers to describe their
last painful session driving AI agents on a real repo. Twenty minutes each, no
install, no `PILOT.md`. If the pain they describe is not the pain socom
addresses, tool quality is irrelevant and that is worth knowing before R1.

## State — verified 2026-08-05, re-probe anything you lean on

| Thing | State |
|---|---|
| socom `main` | state below re-verified at `5894df9` (the R1-prose correction, CI `success`); the closeout commit that lands this prompt sits on top of it. `git log --oneline -3` and re-probe rather than trusting either SHA. Clean, pushed, CI green. |
| Buckets | `defects.md` 4 DONE P0 + **3 READY P0** + **7** READY P1 · `build.md` 1 READY (R1) + **8** BLOCKED · `evidence.md` `EV-NONAUTHOR-EXPOSURE-01` READY P0, **unrun** |
| Proof tier | **D0 — ASSUMED**, unchanged since 2026-08-01 |
| Suite | `unit: 339 passed, 0 failed` · `r1corpus: 146 passed, 0 failed` · `gate full: PASS` · `build.py --check` clean |
| Exposure prep | `bench/exposure/{README,TEMPLATE}.md` landed; URL preflighted at 411152 bytes, build `b80c5efc6013`; sheet has a build-under-test row fed by `socom version` |
| Decisions | `0001` exposure-before-capability · `0002` unresolvable-enforcement-must-record (**HELD**) · `0003` no-standard-binds-a-fork (Accepted, adopts nothing) |

Probes: `./bin/socom gate full` · `python3 build.py --check` ·
`python3 tests/unit.py` · `python3 tests/r1corpus.py` · `grep -c '^- \`' buckets/*.md`

## The bound

The tool is less broken than it was, the class behind two of its defects is now
named and swept, the recording sheet is written, and seven candidate standards
were evaluated against primary sources and none adopted. **None of that moved the
proof tier, because none of it is the blocking claim.** The last one is the
clearest case: a day of rigorous research produced one document, zero capability,
and an explicit note that it says nothing about whether anyone would use this.

A result of *"one person, stopped at step 2, never ran it again"* closes the row
exactly as a positive result would. It is not a failed session.

**One engineer. This week. Watch in silence.**
