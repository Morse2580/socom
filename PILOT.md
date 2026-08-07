# SOCOM pilot guide — start testing in 5 minutes

**Status: v0.1 — a supervised pilot, not production.** You are stress-testing the
*human residues* (does a gate annoy you into bypassing it? does a metric mislead
you?), not a finished product. That is the point. The fastest way to make SOCOM
real is to run it on one repo you care about and report where it lied or got in
your way.

This guide is written so you can read it yourself **or** paste it to Claude Code and
say *"walk me through this on this repo"* — see [With Claude Code](#with-claude-code).

---

## Is it safe? (read this first)

**Yes, for a supervised pilot on one repo.** Concretely:

- SOCOM is **additive and non-destructive**: it plants files (never clobbers your
  edits), wires git hooks that run *your own* commands, and builds an index. It does
  **not** delete your code, does **not** auto-push, and does **not** run any AI worker
  unless you explicitly pass `--exec`.
- **Exactly what it writes that is already yours** — the whole list, so the claim
  above is checkable rather than trusted:
  - `core.hooksPath`, the one git setting it sets. **If your repo already has
    hooks, SOCOM refuses and changes nothing** — because repointing them would
    not *fail* your existing hooks, it would silently *stop* them. That covers
    both ways a repo can have hooks: `core.hooksPath` already pointing somewhere
    (husky sets it to `.husky/_`), **and** real hooks sitting in the default
    `.git/hooks/` with `core.hooksPath` unset — which is where **lefthook**
    installs, and where a hand-written hook lives. An unset `core.hooksPath`
    means "use the default location", not "no hooks". SOCOM records the prior
    value either way.
  - a **marked block** in `.gitignore` (its own machine-local runtime state, so
    `git add -A` can't sweep it into your commit) and, if you use prettier, in
    `.prettierignore` (its own generated files, so adopting SOCOM can't turn a
    green format check red). Everything outside the `# >>> socom` markers is
    left byte-for-byte alone.
  - **nothing on your remote.** The blackboard is local until you say otherwise:
    `blackboard.sync` is planted **false**, and `claim`/`attest`/`resolve` write
    only to `.socom/` under your working tree. Set it to `true` and SOCOM pushes
    its own ref (`refs/socom/blackboard`, no branch, no source) to the remote you
    name — announcing that remote by URL before each write. Until then it never
    touches a remote your colleagues share.
- **There is a way back, and it stays back:** `socom unadopt` restores
  `core.hooksPath` to whatever it was before (or unsets it) and drops SOCOM's
  local git config. It also **records that you left**, so no later `precond`,
  `doctor` or heal quietly re-arms the hooks — only an explicit `socom adopt`
  does, and it tells you it is clearing that record. It deliberately does **not**
  delete the planted files — it lists them, so removing them stays your call.
  (`socom uninstall` is a different thing: it removes the binary from your PATH
  and touches no repo.)
- It **degrades loudly**: when it can't do something honestly (detect your test
  command, certify retrieval), it says so and stops — it never fabricates.

**Three things to keep OFF / not trust during the pilot** (we're telling you because
the tool's own audit did):

1. **Leave `spawn --exec` and `monarch recover --exec` OFF.** The auto-orchestration
   loop has not been validated in production yet. Use `spawn` in its default
   (print-the-command) mode only.
2. **Treat the metrics (`value`, `cycle`, trust) as advisory.** The ledger is a plain
   file; the numbers are not yet tamper-evident.
3. **`pre-commit` is a *warning* (amber), not a block.** Only `pre-push` and CI
   actually stop you.

Everything else in the 5-minute path below is safe to run on a real repo.

---

## The 5-minute path

```sh
# 1. Get the tool (one self-contained file — read it, it's plain Python)
curl -fsSLO https://raw.githubusercontent.com/Morse2580/socom/main/bin/socom
chmod +x socom && ./socom install        # copies onto ~/.local/bin, no sudo
rm socom                                 # the download is disposable after install

# 2. In a repo you care about, climb the whole on-ramp in one command
cd ~/your-repo
socom quickstart
```

`quickstart` will:
- plant the substrate + wire git hooks,
- **auto-bind your gate checks to your real test command** (Make / npm / pytest /
  cargo / go) — or tell you exactly what to edit if it can't detect one,
- build a knowledge index and **answer a question from canon live** so you see
  retrieval work,
- check whether your AI runtime is ready,
- end on a `value` readout and your adoption rung.

If it stalls at **T2 ("checks unbound")**, that's honest — it found no test command
and refused to invent one. Bind it yourself and re-run:

```sh
# example: a Terraform repo
#   edit socom.yaml -> checks.fast: "terraform -chdir=infra fmt -check -recursive"
socom compile
socom gate fast        # now runs YOUR check — watch it catch real issues
```

That's the core loop. A bound gate that catches something real (a failing test, a
formatting drift) and then goes green after you fix it — **that is the value.**

---

## What to actually test (and what to skip)

| Try this | What it proves |
|---|---|
| `socom quickstart` on 2–3 different repos (one with tests, one without) | the on-ramp + the honest degrade |
| Bind a real check, break it, run `socom gate fast` | a gate catching a real slip |
| `socom query "how do I ..."` | retrieval over canon (works at L0 immediately) |
| `socom contract verify <promise.xml>` | falsifiable done-ness on a real contract |
| `socom value` / `socom greet` | where you are on the adoption ladder |
| **Skip for now:** `spawn --exec`, `monarch recover --exec` | not pilot-ready |

---

## What to report back (this is the actual experiment)

The residuality model says the failure modes are *human*, not code. So watch yourself,
and tell us:

- **Did you reach for `git commit --no-verify`?** When, and why? (a gate too slow, a
  false positive, deadline panic — all valuable)
- **Did a gate fire a FALSE POSITIVE?** Even one on a bad day kills adoption — we need it.
- **Did a metric mislead you** — did `value`/`cycle` say something you didn't trust?
- **Where did discovery stall?** What did you have to read the source to understand?
- **Did you "game" a gate** (satisfy the check without doing the work)? Be honest — that
  tells us the gate is theater.

File these as GitHub issues, or just paste them back. Negative findings are the most
useful: a tester who bypassed a gate teaches more than one who didn't.

---

## The blackboard trial — the one measurement that decides everything

The blackboard (`claim` / `attest` / `findings` / `resolve`) exists to test one
claim, published and never measured by anyone: *"five senior engineers can
plausibly oversee thirty."* If that is true, it is true because a warning
reaches the agent about to need it. If it is false, no amount of substrate
fixes it.

**The metric is `saves`.** After any `claim` that returned findings, tally one
of three outcomes in `bench/blackboard-tally.csv`:

- **A — save.** The agent narrowed, abandoned, or changed approach *because of*
  a finding.
- **B — noise.** Findings returned, ignored, no effect.
- **C — silent.** No findings existed for those paths.

**Count by hand.** Building a saves-counter is scaffolding: if A never happens,
no instrumentation would have made it happen. A spreadsheet is the correct
tool, and two weeks is the window.

**Secondary: findings-per-claim over time.** If it rises monotonically, the
blackboard is becoming noise before it becomes useful — Hearsay-II's control
problem, and the first thing to watch for.

**Setting:** three or more people running concurrent agents on a shared repo.
The thesis is a claim about *teams* and is untestable solo.

⚠️ **This trial is the one case that needs the opt-in.** Set
`blackboard.sync: true` in `socom.yaml` on every participating clone, or each
person gets a private notebook, every `claim` tallies **C — silent**, and the
measurement reads as "no saves" for a reason that has nothing to do with the
thesis. Publishing is off by default precisely so that turning it on is a
decision someone made.

### The kill criterion, written before the build

**Two weeks with concurrent agents and zero category-A saves means stop.** Not
"add drift", not "improve retrieval", not "put it in a graph" — stop, and
record that the supervision bottleneck is not where the thesis places it. After
six prior attempts, a falsified thesis is worth more than a seventh artifact.

Writing this down *first* is the one procedural difference between this and
everything that came before it. It is here so the decision gets made on
evidence in fourteen days rather than on enthusiasm today.

---

## With Claude Code

SOCOM is built for Claude Code. After `socom quickstart`, your repo has a generated
`CLAUDE.md` and `.claude/agents/` — Claude Code reads them automatically. To make
discovery effortless, open the repo in Claude Code and paste:

> Read CLAUDE.md and AGENTS.md, then give me a 5-line tour of what SOCOM set up in
> this repo. Then: pick one real check I should bind for this codebase, bind it in
> socom.yaml, run `socom compile`, and run `socom gate fast` so I can see it work.
> Do not touch `spawn --exec` or `monarch`. Explain each step as you go.

Claude Code will discover the substrate, bind a real gate, and demonstrate a catch —
the whole 5-minute path, guided. Ask it follow-ups like *"what does the residuality
gate check?"* or *"show me what `value` is measuring and whether I should trust it."*

---

## The honest bottom line

You are piloting a **mature substrate** (gates, contracts, residuality, retrieval) that
already catches real bugs, wrapped around an **unproven orchestration layer** we're
asking you to leave off. Test the substrate hard, report where it annoyed or misled
you, and you'll be stressing exactly the residues that decide whether v0.1 graduates.
