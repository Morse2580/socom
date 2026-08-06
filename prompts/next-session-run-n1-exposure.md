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

REWRITTEN 2026-08-05 (fifth pass, at 9e9cb79 — the three P0s are FIXED).
  REWRITTEN defects ......... **7 DONE P0 / 0 READY P0** / 7 READY P1
  REWRITTEN public artifact . 411152 -> **421735** bytes, build b80c5efc6013 ->
            **1bc70ac4f16c**, http=200, byte-identical to bin/socom
  VERIFIED  suites .......... unit **348** / r1corpus 146 / gate full PASS /
            build.py --check clean / CI success on 9e9cb79
  VERIFIED  the fixes ....... 14 of the 21 new assertions FAIL against a
            `git archive HEAD` of the pre-fix tree — the tests pin the defects
  UNCHANGED build.md ........ 1 READY (R1) + 8 BLOCKED
  UNCHANGED EV row .......... EV-NONAUTHOR-EXPOSURE-01 READY P0, STILL UNRUN
  UNCHANGED proof tier ...... D0. Three repairs moved nothing. That is the point.

RE-VERIFIED 2026-08-05 (sixth pass, at e642787 — the field run + 0004).
  VERIFIED  defects ......... 7 DONE P0 / 0 READY P0 / **9** READY P1
  VERIFIED  build.md ........ 1 READY (R1) + 8 BLOCKED, unchanged
  VERIFIED  EV row .......... EV-NONAUTHOR-EXPOSURE-01 READY P0, STILL UNRUN
  VERIFIED  decisions ....... 0001 + 0002 + 0003 + **0004** (4 files)
  VERIFIED  suites .......... unit 348 / r1corpus 146 / gate full PASS
  VERIFIED  public URL ...... http=200, 421735 bytes, cmp-identical, 1bc70ac4f16c,
            digest reproduced by shasum -a 256 (NO code shipped since 2fd2b5d)
  VERIFIED  session-end ..... PASS — handoff filled, prompt claim-verified
  ADDED     decisions ....... **0005** Accepted — the population question is
            CLOSED; the amendment was conceded in full and still refused
  UNCHANGED proof tier ...... D0 — after three P0 repairs, eleven field findings,
            one decision document and a protocol line. Six passes of this header
            now say the same thing: only the run moves it.

REWRITTEN 2026-08-05 (seventh pass, at 099c45a — ONE NEW P0, found in the wild).
  REWRITTEN defects ......... 7 DONE P0 / **1 READY P0** / 9 READY P1
            DEF-HANDWRITTEN-CLAUDE-MD-WEDGES-THE-LADDER-01 — clear it FIRST
  VERIFIED  decisions ....... 0001 + 0002 + 0003 + 0004 + **0005** (5 files)
  VERIFIED  the wedge ....... REPRODUCED deterministically; `--force` clobber
            measured ("Do not delete" -> 0 occurrences)
  VERIFIED  suites .......... unit 348 / r1corpus 146 / gate full PASS
  VERIFIED  public URL ...... 421735 bytes, 1bc70ac4f16c (no code since 2fd2b5d)
  UNCHANGED EV row .......... EV-NONAUTHOR-EXPOSURE-01 READY P0, STILL UNRUN
  UNCHANGED proof tier ...... D0

REWRITTEN 2026-08-06 (eighth pass, at df924f9 — the wedge P0 is FIXED, and
nothing else was done). Every line re-run, not carried:
  REWRITTEN defects ......... **8 DONE P0 / 0 READY P0** / 9 READY P1
            (measured: 8/0/9 via grep -cE). The P0 section below is now history.
  REWRITTEN public artifact . 421735 -> **427138** bytes, build 1bc70ac4f16c ->
            **77d2b1855dca**, http=200, cmp byte-identical to bin/socom
  REWRITTEN suites .......... unit 348 -> **367** / r1corpus 146 / gate full PASS
            / build.py --check clean / CI **success @ df924f9**
  REWRITTEN code cites ...... the fix MOVED both lines the old header cited.
            write_generated is now `core.py:197` (its HR2 guard at `:209`);
            adoption_rung is `lifecycle.py:947`, its new branch at `:958-963`.
            core.py:137 is now `def is_generated` — the old cite would have
            resolved to a real line and meant nothing. Re-`sed` before quoting.
            ⚠️ These moved TWICE in one day (once for the fix, once for the
            duplication collapse at `868386b`). Treat every line number in this
            prompt as stale and re-`sed` it; the symbol is the durable cite.
  VERIFIED  the fix ......... 5 of 9 new smoke assertions FAIL against a
            `git archive HEAD` of the pre-fix tree; the 19 unit assertions do
            not load there at all (the helpers did not exist)
  VERIFIED  build.md ........ 1 READY (R1) + 8 BLOCKED, unchanged
  VERIFIED  decisions ....... 0001-0005 (5 files), unchanged
  UNCHANGED EV row .......... EV-NONAUTHOR-EXPOSURE-01 READY P0, STILL UNRUN
            (L15 @ df924f9)
  UNCHANGED proof tier ...... D0 — eight P0 repairs now. The queue in front of
            the run is EMPTY. There is nothing left to clear first.
  HYPOTHESIS none.

REWRITTEN 2026-08-06 (ninth pass, at f842bac — ONE NEW P0, found by reflex).
  REWRITTEN defects ......... 8 DONE P0 / **1 READY P0** / 9 READY P1
            (measured: 8/1/9 via grep -cE). The queue was empty for exactly
            ONE commit. DEF-SUBCOMMAND-HELP-MUTATES-STATE-01.
  VERIFIED  the new defect .. MEASURED on ae42d0c4c71a in a throwaway repo:
            `claim --help` acquires a lease literally named "--help" (and `-h`
            the same); `compile --help` plants 33 files; `release --help`
            releases the bogus lease; `attest --help` errors cleanly.
            Top-level `socom --help` is FINE — which is why it went unseen.
  VERIFIED  skills .......... 4 in `.claude/skills/`, auto-discovered
            (`git ls-files .claude/skills/`); the prompt now points at them
  REWRITTEN public artifact . 427138 -> **427639** bytes, 77d2b1855dca ->
            **ae42d0c4c71a**. I first wrote this line as UNCHANGED and the
            probe refuted it: bin/socom moved at 868386b (the duplication
            collapse). Regression Test 1 of prompt-verify-pass, on the author,
            in the same session that ported the skill naming it.
  UNCHANGED suites .......... unit 370 / r1corpus 146 / gate full PASS
  UNCHANGED EV row .......... EV-NONAUTHOR-EXPOSURE-01 READY P0, STILL UNRUN
  UNCHANGED proof tier ...... D0
  HYPOTHESIS the `--help` repair "looks small" — dispatch-level intercept, no
            spike run. (hypothesis — operator-driven)
-->

# Next session — run the n=1 exposure. One small P0 sits in front of it.

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

**Four skills ship in this repo** and are auto-discovered — nothing to install
*(verified: `git ls-files .claude/skills/` lists all four at `f842bac`)*.
Use them instead of hand-rolling their procedures:

- `ship-and-verify` — the push loop: `build.py` → `gate full` **by hand** →
  commit to `main` → `gh run watch` → **re-measure the public curl artifact**.
  Its failure-mode list is real and was paid for; read it before citing a SHA
  or a line number.
- `bucket-ledger-reconcile` — before writing ANY state table or flipping a row
  `DONE`. `DONE` = Changed + Pinned (a test that fails against the pre-fix tree)
  + Effect (the row's acceptance re-run, output in the row). Not "I edited it".
- `prompt-verify-pass` — mandatory at closeout and on any edit to this file.
- `reap-shells` — stale background shells; §5 covers socom's own reaper, which
  owns `spawn`'d workers (hand-killing them corrupts the tally).

⚠️ **The doctrine skills were deliberately NOT ported** (root-gate,
residuality-gate, seam-coupling-gate, capability-composability-gate,
explain-plain). They live in `/root/Akili/.claude/skills/` and still govern —
`0001`, `0005` and `evidence.md` all cite the root gate and its `D0` tier, which
**nothing in this repo defines.** If you need the tier vocabulary, read it there;
do not re-derive it, and do not port it as a side quest.

## The P0 that was in front of this is CLEARED (2026-08-06, `df924f9`)

`DEF-HANDWRITTEN-CLAUDE-MD-WEDGES-THE-LADDER-01` is **DONE**. A repo with a
hand-written `CLAUDE.md` — socom's own stated audience — could not leave `T1`,
because `compile` refused to clobber the file (HR2, correct) and the rung read
that same missing header as *"run `socom compile`"*. socom printed the step it
had just refused, forever. **Do not re-derive it; the row has the full account.**

The repair, in one line: the refusal keeps HR2 and gains an exit that is not the
clobber. socom's half lands in `CLAUDE.socom.md`, the user's file is left
byte-identical, and `compile` prints the ONE line the *user* adds —
`@CLAUDE.socom.md` — which socom does not write. `compiled_view()` (`core.py:169`)
is now the single answer to *"which file is socom's"* *(mechanism verified:
`sed -n '169p'` is the `def compiled_view` line; `adoption_rung` reads it at
`lifecycle.py:958`)*, and the rung exits `T1` on
*"socom's instructions are reachable"* rather than *"socom owns CLAUDE.md"*.
`--force` is unchanged: still available, still destroys the file *(measured:
`Do not delete` → 0 occurrences, post-fix)*. It simply stopped being the only exit.

⚠️ **Two limits recorded on purpose, in case they resurface as "bugs":**
the `@` import is a **Claude Code** mechanism, so `AGENTS.md` gets a sidecar but
**no import line** — AGENTS.md has none, and printing one would be `0004` Class A
committed by the author. And the `imported` state is a **file test, not an effect
test**: socom checks the line is present and never claims the file was loaded.

**That was the eighth P0.** It moved the proof tier by **nothing**, exactly as
the seven before it did.

## …and a ninth was filed the same day, by reflex

`DEF-SUBCOMMAND-HELP-MUTATES-STATE-01` **READY P0** *(measured: 8 DONE P0 /
**1** READY P0 / 9 READY P1 via `grep -cE`)*. **No subcommand handles `--help`,
so the universal "explain, don't act" reflex makes socom act.** `claim --help`
acquires a lease literally named `--help`; `compile --help` plants 33 files;
`-h` behaves the same. Top-level `socom --help` is fine, which is why it was
never looked at. *(measured 2026-08-06, build `ae42d0c4c71a`, throwaway repo.)*

It fires **at** the stall point, not after it — `<cmd> --help` is the first thing
a stranger types at an unfamiliar subcommand, and the answer to a request for an
explanation is a state mutation. The row has the full scope and the acceptance.

⚠️ **Decide, don't drift.** Either clear it first — the repair looks like a
dispatch-level intercept of `--help`/`-h` before any `cmd_*` runs *(hypothesis —
operator-driven; no spike run)* — or accept it as a known defect a participant
may hit and **go and run the exposure anyway**. What must not happen is a third
session that repairs P0s and calls that the work. Eight repairs have moved D0 by
zero, and this row does not change that arithmetic.

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

Verified 2026-08-06 (re-run at `f842bac`): `http=200`, **427639 bytes**, `cmp`
byte-identical to `bin/socom`, `--help` prints the command list, and `version`
reports build **`ae42d0c4c71a`** (last commit touching `bin/socom`: `868386b`) *(measured: curl -w + cmp +
`socom version`)*. **Also confirm the participant is on
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

## The 5-substrate breakage sweep — 2026-08-05, three P0s filed and FIXED

Five agents, five isolated shallow clones, one ecosystem each (Node/express ·
Go/cobra · Rust/fd · Python/click · no-build/github-gitignore), each given only
the public `curl` URL, **forbidden** from reading socom's source to work around a
failure or installing a toolchain to keep going. Build `b80c5efc6013`.

**Zero crashes, zero hangs, 20+ subcommands. The tool is robust.** What it has is
claims outrunning capability — and three that mutate state the user never agreed
to. Those three were **READY P0** in `defects.md`, each REPRODUCED by the primary
session (local bare remote; nothing outbound), not taken on agent report — and
all three are **DONE** as of `2fd2b5d`, with the re-run evidence in each row:

- `DEF-CLAIM-PUSHES-TO-HOST-REMOTE-01` — `claim` pushed `refs/socom/blackboard`
  to the **adopted repo's own origin**, unprompted. **FIXED:** `blackboard.sync`
  now defaults to false and `init` plants it false; `bb_push` names the remote
  and its URL on stderr before every write. ⚠️ **A multi-clone trial (Phase 3a)
  must now set `blackboard.sync: true`** or every participant gets a private
  notebook and every claim tallies `C — silent`. `PILOT.md` says so where the
  trial is described.
- `DEF-PRECOND-SILENTLY-REVERSES-UNADOPT-01` — `unadopt` worked; the next
  `precond` silently re-set `core.hooksPath` and scored it `PASS / 1 healed /
  0 blockers`. Found independently by two agents. **FIXED:** `unadopt` records
  `socom.unadopted`, `_wire_hooks` (the single writer) honours it so no caller
  can heal around it, and only an explicit `adopt` clears it. A heal that writes
  the host's git config is now counted AND named as a warning.
- `DEF-RELEASE-NEVER-RELEASES-01` — both forms exited **0** saying "no live lease
  held" while `claim --scan` listed the lease before and after. **FIXED, and the
  row's own diagnosis was incomplete:** identity was `hostname-<ppid>`, so every
  one-shot invocation was a different author — the common case, because one shell
  per command is how an agent runtime drives this tool. Identity is now derived
  from the working tree, and `release` refuses loudly (naming the holder, exit 1)
  rather than reporting a silent success.

⚠️ **The P0 cap moved 4 → 7 and is now 7 DONE / 0 open. That is not a licence to
grow it** — see the §Note in `defects.md`. The same sweep produced a much longer
list and every other finding went to P1 or nowhere. **Nothing about these three
repairs moved the proof tier**; the row below is still the work.

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

## What the 2026-08-05 field run found — read `decisions/0004`, do not re-derive it

socom was run on **three real repos across two machines** (build `1bc70ac4f16c`):
`httpie/cli` @ `5b604c3`, `cargo-applications`, `monarch-hris-platform`. Eleven
findings. `0004` names the two classes they belong to and **repairs neither**.

- **Class A — socom reports what it WROTE, not what took EFFECT.** Nine surfaces.
  `T6 — operational` fires on `vectors.json` existing while `eval.json`'s real
  `passed` boolean is never read; `✓ gates now run YOUR tests` printed over a
  command that returned **127 on 3 of 3 repos**; `kept your statusLine` defers to
  a file socom wrote 30 s earlier. Indicted by socom's own **rank-1** principle,
  `verify-never-claim` — which `quickstart` **prints**, as result #4 of its demo
  query, in the same run where it violates it.
- **Class B — socom writes what it does not own, and no code represents "own".**
  `core.hooksPath`, the remote, the working directory, `.claude/settings.json`,
  the binary's location. `core.py:141` is the one place ownership IS tested, and
  the one place socom behaved correctly.
- **`0002`'s class is their intersection**, not a third thing.

⚠️ **The A/B is the strongest evidence on file for the metric row**, measured not
inferred: with a detectable test command → `100% · T6`, `doctor clean`, `gate
fast` **RED**; without one → `33% · T2`, `doctor` exit 1. The right-hand column
is socom working as designed. The left is the defect, and it is the **common**
case.

⚠️ **`0004`'s appendix has the proposed repairs, including a ~2h labelling column
that is IN-BUCKET and still HELD** — five of its six surfaces are what `PILOT.md`
asks the participant. Cheapness is not the test; whether a repair deletes a
finding is.

⚠️ **Step 3 of `bench/exposure/README.md` is new and load-bearing.** Confirm
`git rev-parse --show-toplevel` before the participant runs anything. The
operator adopted a **non-git scratch directory** by accident on 2026-08-05,
following `PILOT.md` verbatim, and read the result as socom repeating itself.
That is the one finding of eleven that **voids** the measurement instead of
informing it — and it needs no code change, only that line.

## Do NOT do these

- **Do not run a sixth agent cohort.** One ran 2026-08-03 (cold-run, ~30 defects)
  and a second ran 2026-08-05 (5-substrate breakage sweep, 3 P0s). Both were
  falsification and neither moved the D-tier by a millimetre — agents do not
  quit, and the stall point is the measurement. A third buys nothing.
- **The three new P0s are already repaired (`2fd2b5d`, CI green). Do not treat
  that as the session.** They were filed as pre-exposure because a participant
  hitting them is burned on something already written down; that debt is paid and
  the only thing left in the way of the run is the run.
- **Do not work the P1 defects.** Seven are filed now, all cheaper and more
  interesting than the exposure, and they measure nothing.
  `DEF-STATUS-CLAIMS-UNLABELLED-01` is P1 **on purpose** — `PILOT.md` asks *"did
  a metric mislead you?"*, so repairing it first deletes a finding the
  participant is meant to generate (`0001` §Amendment 1 rule 3).
- **Do not treat the wedge repair as the session, and do not polish it.** It
  landed at `df924f9` with CI green, 19 unit + 9 smoke assertions, and 5 of the 9
  failing against the pre-fix tree *(measured: `git archive HEAD` of the pre-fix
  tree + the new `tests/smoke.sh`; CI `success @ df924f9`)*. It is finished. The sidecar shape is
  deliberately minimal; improving it is another morning that moves D0 by nothing.
- **Do not build any capability.** Everything except R1 reads BLOCKED.
- **Do not build R1 either**, unless the exposure has happened. If you do, ship
  it **standalone** — own binary, zero adoption, zero git-config writes, no
  `.socom/` — so the two hypotheses stay separable.
- **Do not run another agent cohort.** It cannot move the D-tier.
- **Do not run a second participant to get a nicer answer.** `n=1` is what the
  root gate authorised; a confident *yes* is what §14.4's five-after-R1 is for.
- **Do not re-argue whether the exposure is needed. `0005` closed it 2026-08-05.**
  The strongest form of the argument — socom's *user* is an agent, so a human
  engineer is the wrong population — was put, **conceded in full**, and still
  refused: the root gate named *adoption*, adoption is a decision, and an agent
  that runs `socom claim` because `CLAUDE.md` says so is producing compliance by
  construction — the exact half the metric discards. Ten agents across two
  cohorts have already demonstrated it: seven P0 rows, D0 moved by nothing.
  ⚠️ The one thing `0005` DID license is an **agent-behaviour A/B** (same repo,
  same task, one variable: socom present or absent) — author-runnable, no
  recruit, and explicitly **supporting, not blocking**. Efficacy is not adoption.
  Run it by hand if you want it; **building** a harness for it is capability.
- **Do not repair either class in `decisions/0004` — including the cheap half.**
  The labelling column is ~2 hours and in-bucket, and it is held anyway, because
  it deletes five of the findings the sheet exists to collect. The classes are
  named so they are not re-derived, not so they are worked.
- **Do not adopt a standard, and do not re-run the standards research.** Seven
  were evaluated 2026-08-05 and none survived; `decisions/0003` records each
  verdict with its primary-source citation. A well-argued external critique is
  the most legitimate-looking reason yet to not run the exposure — it is still
  not a reason. Reopens only at fork > 0.

- **Do not calm the first-contact output first — it was proposed, measured and
  DEFERRED by the operator on 2026-08-05.** The instinct is right and the numbers
  are real: `quickstart` on a fresh repo prints **92 lines / 7.6 KB**, **33
  absolute paths in full**, an ASCII logo, and the rung meter **twice**, before
  the user has done anything. Measured on build `1bc70ac4f16c`, throwaway git
  repo, one Python file. Keep those numbers — they are the pre-exposure baseline
  for whatever gets fixed afterwards. **The decision was to run the exposure
  first and fix what the participant actually stopped on**, because taste picks
  the wrong line to cut and §4 of `bench/exposure/TEMPLATE.md` was written to
  capture precisely this reaction. ⚠️ Distinguish the two halves if it resurfaces:
  output VOLUME is not the finding, but the ENTRY SHAPE it describes (files
  planted, `core.hooksPath` rewritten) **is** what §4 measures — changing that
  before the run deletes the measurement.
  ⚠️ **A React/Ink rewrite was evaluated the same day and REFUTED on its own
  goal.** It was proposed to make the tool "calmer to install"; it does the
  opposite. socom installs today as ONE file — `curl` 427639 bytes of stdlib
  Python, `chmod +x`, run — and Ink requires a Node runtime, `npm install`,
  `node_modules` and a bundle step, so the install grows from one curl to
  "install Node first" and **the 30-second preflight above stops existing**. It
  is also a ~7,000-line cross-language rewrite, i.e. capability, not polish. The
  design guidance that motivated it (ANSI degradation, non-TTY output,
  light/dark, machine-readable modes) is framework-agnostic and applies to the
  single Python file unchanged — nothing about it needs Node. Do not re-derive
  this; if the CLI is ever restyled, it is restyled in place.

## Cheaper alternative if no engineer is reachable this week

Test the *premise* instead of the tool: ask three engineers to describe their
last painful session driving AI agents on a real repo. Twenty minutes each, no
install, no `PILOT.md`. If the pain they describe is not the pain socom
addresses, tool quality is irrelevant and that is worth knowing before R1.

## State — verified 2026-08-05, re-probe anything you lean on

| Thing | State |
|---|---|
| socom `main` | state below re-verified at `df924f9` (the wedge P0 fix, CI `success @ df924f9`); the closeout commit that lands this prompt sits on top of it. `git log --oneline -3` and re-probe rather than trusting either SHA. Clean, pushed, CI green. |
| Buckets | `defects.md` **8 DONE P0 + 1 READY P0** (`DEF-SUBCOMMAND-HELP-MUTATES-STATE-01`, filed 2026-08-06) **+ 9** READY P1 *(measured: 8/1/9 via `grep -cE`)* · `build.md` 1 READY (R1) + **8** BLOCKED *(measured: 1/8)* · `evidence.md` `EV-NONAUTHOR-EXPOSURE-01` READY P0, **unrun** *(L15 @ `df924f9`)* |
| Proof tier | **D0 — ASSUMED**, unchanged since 2026-08-01 *(measured: `bench/exposure/` holds README + TEMPLATE only, no dated sheet)* |
| Suite | `unit: 367 passed, 0 failed` · `r1corpus: 146 passed, 0 failed` · `gate full: PASS` · `build.py --check` clean *(measured: all four re-run at `df924f9`)* |
| Exposure prep | `bench/exposure/{README,TEMPLATE}.md` landed *(verified `df924f9`)*; URL preflighted at **427639** bytes, build **`ae42d0c4c71a`** *(re-measured at `f842bac`)* *(measured: `curl -w` + `cmp` vs `bin/socom` + `socom version`)*; sheet has a build-under-test row fed by `socom version`. ⚠️ **Re-measure both — never carry them.** |
| Decisions | `0001` exposure-before-capability · `0002` unresolvable-enforcement-must-record (**HELD**) · `0003` no-standard-binds-a-fork (Accepted, adopts nothing) · **`0004`** two-boundaries-socom-does-not-represent (Accepted, diagnosis only, repairs nothing) · **`0005`** the-user-is-an-agent-the-adopter-is-not (Accepted — the population question is CLOSED) *(measured: 5 files in `decisions/`)* |

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
