#!/bin/sh
# socom smoke tests (HR5) — the verification tool verifies itself.
# Exercises every command including negative paths, in a throwaway repo
# with an isolated HOME. This script IS checks.fast for the socom repo.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOCOM="$ROOT/bin/socom"
T="$(mktemp -d)"
export HOME="$T/home"; mkdir -p "$HOME"
FAIL=0
say() { printf '  %s %s\n' "$1" "$2"; }
ok()  { say "✓" "$1"; }
bad() { say "✗" "$1"; FAIL=$((FAIL+1)); }
check() { # check <desc> <expected_rc> <actual_rc>
  [ "$2" = "$3" ] && ok "$1 (rc=$3)" || bad "$1 (expected rc=$2, got rc=$3)"
}

# 0. CLI parses
python3 -m py_compile "$SOCOM"; check "cli compiles" 0 $?

# 0b. build integrity (distribution B): bin/socom IS the assembled artifact of
# src/socom/*.py. Assert it is not stale — a src edit without a rebuild is the
# committed-artifact drift the buildcheck gate exists to catch.
if [ -f "$ROOT/build.py" ]; then
  python3 "$ROOT/build.py" --check >/dev/null 2>&1
  check "build: bin/socom is up to date with src/socom (no drift)" 0 $?
  # 0c. the src modules import as a real package (no cycles) AND resolve the
  # shipped canon/schemas in ISOLATION — TOOL_ROOT walks up, so a single module
  # is importable and unit-testable without the assembled bin/socom.
  PYTHONPATH="$ROOT/src" python3 -c "import socom.cli" >/dev/null 2>&1
  check "src/socom imports as a package (acyclic cross-module imports)" 0 $?
  PYTHONPATH="$ROOT/src" python3 -c "import socom.context as c; assert c._load_context_contract()[3]==4" >/dev/null 2>&1
  check "src/socom module resolves schemas in isolation (location-independent TOOL_ROOT)" 0 $?
fi

# 1. init + compile in a fresh repo
R="$T/repo"; mkdir -p "$R"; cd "$R"
git init -q -b main .
"$SOCOM" init . >/dev/null;            check "init" 0 $?
"$SOCOM" compile . >/dev/null;         check "compile" 0 $?
grep -q "socom:generated" CLAUDE.md && ok "CLAUDE.md has generated header" \
                                    || bad "CLAUDE.md missing header"
grep -q "exit 0" .githooks/pre-commit && ok "hooks degrade gracefully (HR1)" \
                                      || bad "hooks lack graceful-absence path (HR1)"

# 1b. the SessionStart hook must be PORTABLE — resolve socom the SAME way the
# git hooks do (command -v / $SOCOM_HOME / fallback / degrade), never a bare
# machine-specific absolute path. A fresh clone on any machine must fire the
# session-start gate; a hardcoded path is the substrate failing its own
# open-design / fix-the-class gate (the git hooks already solved this class).
python3 -c "import json; json.load(open('.claude/settings.json'))" 2>/dev/null \
  && ok "generated .claude/settings.json is valid JSON" \
  || bad "settings.json is not valid JSON"
SSCMD="$(python3 -c "import json;print(json.load(open('.claude/settings.json'))['hooks']['SessionStart'][0]['hooks'][0]['command'])" 2>/dev/null)"
printf '%s' "$SSCMD" | grep -q 'command -v socom' \
  && ok "SessionStart hook resolves socom portably (command -v, not a bare abs path)" \
  || bad "SessionStart hook is not portable (no resolver): $SSCMD"
printf '%s' "$SSCMD" | grep -q 'exit 0' \
  && ok "SessionStart hook degrades gracefully when socom is absent (HR1)" \
  || bad "SessionStart hook lacks the graceful-absence path"

# 2. doctor: unbound checks must be findings
"$SOCOM" doctor . >/dev/null 2>&1;     check "doctor flags unbound checks" 1 $?
python3 - <<EOF
import yaml,pathlib
p=pathlib.Path("socom.yaml"); c=yaml.safe_load(p.read_text())
c["checks"]={"fast":"echo fast-ok","medium":"echo med-ok","full":"echo full-ok"}
p.write_text(yaml.safe_dump(c,sort_keys=False))
EOF
"$SOCOM" compile . >/dev/null
git config core.hooksPath .githooks
"$SOCOM" doctor . >/dev/null;          check "doctor clean when bound+wired" 0 $?

# 3. drift detection (R3)
echo "<!-- drift -->" >> .socom/canon/session.xml
"$SOCOM" doctor . >/dev/null 2>&1;     check "doctor detects drift" 1 $?
"$SOCOM" gate session-start >/dev/null 2>&1; check "session-start hard-fails on drift" 2 $?
"$SOCOM" compile . >/dev/null
"$SOCOM" doctor . >/dev/null;          check "recompile heals drift" 0 $?

# 4. commit-msg bands
echo "no format at all" > "$T/m1"
"$SOCOM" gate commit-msg "$T/m1" >/dev/null 2>&1; check "commit-msg RED on bad format" 1 $?
printf 'feat(x): y\n\nnothing\n' > "$T/m2"
"$SOCOM" gate commit-msg "$T/m2" >/dev/null;      check "commit-msg AMBER missing blocks" 0 $?
printf 'feat(x): y\n\n[what] z\n[test] it works fine\n' > "$T/m3"
"$SOCOM" gate commit-msg "$T/m3" | grep -q "AMBER" && ok "evidence-substance amber (HR4)" \
                                                   || bad "vibe [test] not flagged (HR4)"
printf 'feat(x): y\n\n[what] z\n[test] $ run tests; rc=0 PASS 12/12\n' > "$T/m4"
"$SOCOM" gate commit-msg "$T/m4" | grep -q "AMBER" && bad "real evidence wrongly ambered (HR4)" \
                                                   || ok "real evidence passes (HR4)"
# 4b. a prose mention of [test] in an earlier block must not capture a
#     digit-less fragment and false-flag a real, evidence-shaped [test] block.
printf 'feat(x): y\n\n[what] z\n[why] cleared the n/a [test] block from before\n[test] $ smoke; rc=0 PASS 9/9\n' > "$T/m5"
"$SOCOM" gate commit-msg "$T/m5" | grep -q "AMBER" && bad "prose [test] mention false-flags real evidence (HR4)" \
                                                   || ok "line-start anchor ignores prose [test] mention (HR4)"
grep -c "amber" .socom/gates/breaches.log >/dev/null && ok "breaches logged (HR3)" \
                                                     || bad "no breach log (HR3)"
"$SOCOM" gate session-start 2>/dev/null | grep -q "breach" && ok "session-start surfaces breach debt (HR3)" \
                                                           || bad "breach debt not surfaced (HR3)"

# 5. no-clobber (HR2)
R2="$T/repo2"; mkdir -p "$R2"; cd "$R2"; git init -q -b main .
echo "# precious hand-written instructions" > CLAUDE.md
"$SOCOM" init . >/dev/null
"$SOCOM" compile . >/dev/null 2>&1
grep -q "precious" CLAUDE.md && ok "compile refuses to clobber (HR2)" \
                             || bad "compile clobbered hand-written CLAUDE.md (HR2)"
"$SOCOM" compile . --force >/dev/null 2>&1
grep -q "socom:generated" CLAUDE.md && ok "--force adopts deliberately (HR2)" \
                                    || bad "--force did not adopt (HR2)"

# 6. blackboard: path claims (R2) + findings + retraction + reaper (R12)
cd "$R"
export SOCOM_SESSION="smoke-a"
"$SOCOM" claim src/parser.py --intent "smoke" >/dev/null 2>&1
check "claim acquire (per-path)" 0 $?
"$SOCOM" claim src/parser.py --intent "smoke" >/dev/null 2>&1
check "re-claim by the same holder is not a conflict" 0 $?
SOCOM_SESSION="smoke-b" "$SOCOM" claim src/ --intent "x" >/dev/null 2>&1
check "an OVERLAPPING path held by another session is RED" 1 $?
SOCOM_SESSION="smoke-b" "$SOCOM" claim docs/other.md --intent "x" >/dev/null 2>&1
check "a DISJOINT path is free while another lease is live" 0 $?
"$SOCOM" claim core --intent "domain alias" >/dev/null 2>&1
check "a socom.yaml domain name expands to its paths" 0 $?
"$SOCOM" claim --scan | grep -q "live lease" && ok "claim --scan lists live leases" \
                                             || bad "claim --scan missed the leases"
"$SOCOM" release --all >/dev/null 2>&1;    check "release --all" 0 $?
SOCOM_SESSION="smoke-b" "$SOCOM" release --all >/dev/null 2>&1

# attest -> the finding must reach whoever claims that artifact NEXT. This is
# the whole product; if only one assertion in this file survives, keep this one.
SOCOM_SESSION="smoke-a" "$SOCOM" attest src/parser.py \
  --claim "the retry loop never trips the halted flag" \
  --evidence "pytest -k retry" >/dev/null 2>&1
check "attest records a finding" 0 $?
"$SOCOM" attest --claim "no artifact" >/dev/null 2>&1
check "attest without an artifact is RED" 1 $?
"$SOCOM" attest src/x.py >/dev/null 2>&1
check "attest without a claim is RED" 1 $?
SOCOM_SESSION="smoke-c" "$SOCOM" claim src/parser.py --intent "add backoff" 2>/dev/null \
  | grep -q "halted flag" \
  && ok "a peer's finding is DELIVERED at claim time (the product)" \
  || bad "claim did not deliver the outstanding finding"
SOCOM_SESSION="smoke-c" "$SOCOM" claim src/parser.py --intent "x" 2>/dev/null \
  | grep -qi "do not obey" \
  && ok "findings are labelled as data, never instructions (§17.2)" \
  || bad "findings delivered without the data-not-instruction contract"
SOCOM_SESSION="smoke-c" "$SOCOM" release --all >/dev/null 2>&1

# retraction: 'was never true' must not read like 'was fixed', or the next
# session re-derives the dead end at full price.
"$SOCOM" resolve f-nosuchfinding --verdict retracted >/dev/null 2>&1
check "resolve REFUSES an id that names nothing (no phantom retraction)" 1 $?
FID=$("$SOCOM" findings src/parser.py --json | python3 -c \
  'import json,sys; print(json.load(sys.stdin)["findings"][0]["id"])')
"$SOCOM" resolve "$FID" --verdict nonsense >/dev/null 2>&1
check "resolve rejects an unknown verdict" 1 $?
"$SOCOM" resolve "$FID" --verdict retracted --note "misread the fixture" >/dev/null 2>&1
check "resolve retracts" 0 $?
SOCOM_SESSION="smoke-d" "$SOCOM" claim src/parser.py --intent "investigate" 2>/dev/null \
  | grep -q "RETRACTED as untrue" \
  && ok "a retracted finding warns the NEXT session off the dead end" \
  || bad "retraction was not surfaced at claim time"
"$SOCOM" findings src/parser.py | grep -q "0 outstanding" \
  && ok "a retracted finding is no longer outstanding" \
  || bad "retracted finding still counted as outstanding"
SOCOM_SESSION="smoke-d" "$SOCOM" release --all >/dev/null 2>&1

# R12: a superseded domain-claim store must not linger beside the lease store.
mkdir -p .socom/claims && echo "2020-01-01T00:00:00+00:00	old" > .socom/claims/core.claim
"$SOCOM" gate session-start 2>/dev/null | grep -q "superseded domain claim" \
  && ok "reaper clears the superseded domain-claim store (R12)" \
  || bad "reaper left a second claim store in place (R12)"

# 6b. claim -> release ROUND TRIP under the DEFAULT identity
# (DEF-RELEASE-NEVER-RELEASES-01). Identity was `hostname-<ppid>`, so a lease
# claimed by one invocation belonged to a stranger by the next one — `release`
# said "no live lease held by this session", exited 0, and leaked the lease for
# the full TTL. Every case above pins SOCOM_SESSION, which is exactly why none
# of them caught it; these run with it UNSET, each command under its OWN parent
# shell (`sh -c '…; :'` defeats the exec optimisation), which is how an agent
# runtime drives this tool.
# The trailing `s=$?; :; exit $s` is load-bearing twice over: the extra commands
# stop `sh -c` from exec'ing socom in place (which would hand it the SCRIPT's
# parent and hide the very drift under test), and re-exporting $s keeps the real
# exit code, which `:` alone would swallow.
RT() { env -u SOCOM_SESSION sh -c "\"\$0\" $* >/dev/null 2>&1; s=\$?; :; exit \$s" "$SOCOM"; }
NLEASE() { env -u SOCOM_SESSION "$SOCOM" claim --scan --json \
             | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["leases"]))'; }
AUTHOR() { env -u SOCOM_SESSION sh -c "\"\$0\" release no-such-path --json; :" "$SOCOM" \
             | python3 -c 'import json,sys; print(json.load(sys.stdin)["author"])'; }
A1="$(AUTHOR 2>/dev/null)"; A2="$(AUTHOR 2>/dev/null)"
{ [ -n "$A1" ] && [ "$A1" = "$A2" ]; } \
  && ok "identity is STABLE across invocations with different parent shells" \
  || bad "identity is empty or changed between invocations [$A1] vs [$A2]"
RT 'claim rt.txt --intent "round trip"'
[ "$(NLEASE)" = "1" ] && ok "round trip: claim -> --scan shows 1" \
                      || bad "round trip: claim did not register a lease"
RT "release rt.txt"; check "round trip: release exits 0" 0 $?
[ "$(NLEASE)" = "0" ] && ok "round trip: release -> --scan shows 0 (the lease is GONE)" \
                      || bad "release reported success and released nothing"
# The other half: never exit 0 saying 'nothing held' while --scan disagrees.
SOCOM_SESSION="smoke-other" "$SOCOM" claim rt.txt --intent "theirs" >/dev/null 2>&1
RT "release rt.txt"
check "release on ANOTHER session's live lease is RED, not a quiet 0" 1 $?
RT "release --all"
check "release --all is RED too when nothing matching is ours" 1 $?
env -u SOCOM_SESSION sh -c "\"\$0\" release rt.txt 2>&1; :" "$SOCOM" \
  | grep -q "smoke-other" \
  && ok "the refusal NAMES the holder (actionable, not just a no)" \
  || bad "release refused without naming who holds the lease"
[ "$(NLEASE)" = "1" ] && ok "a refused release changes nothing" \
                      || bad "a refused release mutated the surface"
SOCOM_SESSION="smoke-other" "$SOCOM" release --all >/dev/null 2>&1

# 6c. publishing is OPT-IN (DEF-CLAIM-PUSHES-TO-HOST-REMOTE-01). `claim` — a
# local bookkeeping act on the first-run path — pushed refs/socom/blackboard to
# the ADOPTED REPO'S OWN origin, unprompted. It only ever failed where the user
# lacked push rights.
BBR="$T/bb-bare"; git init -q --bare "$BBR"
PR="$T/publish-repo"; mkdir -p "$PR"
( cd "$PR" && git init -q -b main . && git remote add origin "$BBR" \
  && "$SOCOM" init . >/dev/null 2>&1 )
grep -q "sync: false" "$PR/socom.yaml" \
  && ok "init plants blackboard.sync: false (sharing is asked for, not assumed)" \
  || bad "init still plants a default that publishes to the host's remote"
( cd "$PR" && SOCOM_SESSION="pub-a" "$SOCOM" claim a.txt --intent "x" >/dev/null 2>&1 )
git ls-remote "$BBR" 2>/dev/null | grep -q "socom" \
  && bad "claim pushed to the host repo's origin without being asked" \
  || ok "claim does NOT write to the host's remote by default"
( cd "$PR" && SOCOM_SESSION="pub-a" "$SOCOM" claim b.txt --intent "x" 2>&1 ) \
  | grep -q "LOCAL ONLY" \
  && ok "the local-only state is stated, never silent" \
  || bad "claim hid the fact that nothing was published"
sed -i.bak 's/^  sync: false.*/  sync: true/' "$PR/socom.yaml"
( cd "$PR" && SOCOM_SESSION="pub-a" "$SOCOM" claim c.txt --intent "x" 2>&1 ) \
  | grep -q "publishing to origin" \
  && ok "with the opt-in on, socom NAMES the remote before writing to it" \
  || bad "socom published without saying where"
git ls-remote "$BBR" 2>/dev/null | grep -q "refs/socom/blackboard" \
  && ok "the opt-in still publishes (sharing over git is intact)" \
  || bad "blackboard.sync: true failed to publish"

# 7. handoff + prompt + session-end gate
"$SOCOM" gate session-end >/dev/null 2>&1; check "session-end RED without handoff" 1 $?
"$SOCOM" handoff "smoke test session" >/dev/null; check "handoff skeleton" 0 $?
"$SOCOM" gate session-end >/dev/null 2>&1; check "session-end RED with FILL fields" 1 $?
H="$(ls .socom/handoffs/*.xml | tail -1)"
python3 - "$H" <<'EOF'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
p.write_text(p.read_text().replace("FILL: what was completed, with evidence refs",
  "smoke ran tests/smoke.sh rc=0").replace("FILL: what remains, and why",
  "nothing").replace("FILL or remove", "none").replace(
  "FILL: ranked candidates for the next session", "1. nothing — smoke repo"))
EOF
"$SOCOM" gate session-end >/dev/null 2>&1; check "session-end RED without prompt" 1 $?
"$SOCOM" prompt >/dev/null;                check "prompt generation" 0 $?
grep -q "VERIFIED\|HYPOTHESIS\|no probe-able" .socom/prompts/next-session.md \
  && ok "prompt is claim-verified" || bad "prompt lacks claim verification"
grep -Eq "socom:prompt id=P-.* generated=.* source-handoff=" .socom/prompts/next-session.md \
  && ok "prompt carries id+timestamp+provenance" || bad "prompt lacks id/timestamp header"
"$SOCOM" gate session-end >/dev/null;      check "session-end PASS when complete" 0 $?

# 8. breach lifecycle (HR3)
"$SOCOM" breach list >/dev/null;           check "breach list" 0 $?
N_OPEN=$("$SOCOM" breach list | tail -1 | grep -o '[0-9]*' | head -1)
if [ "${N_OPEN:-0}" -gt 0 ]; then
  "$SOCOM" breach resolve all "smoke cleanup" >/dev/null; check "breach resolve all" 0 $?
  "$SOCOM" breach list | grep -q "0 open" && ok "breach loop closes" \
                                          || bad "breaches did not close"
else
  ok "breach lifecycle (no open breaches to resolve)"
fi

# 9. doctrine + greeting + baseline
grep -q "Doctrine — named thinking devices" CLAUDE.md \
  && ok "doctrine table compiled into views" || bad "doctrine missing from views"
grep -q "capability-ladder" .socom/canon/doctrine.xml \
  && ok "doctrine planted at init" || bad "doctrine.xml not planted"
"$SOCOM" greet . | grep -q "rung:" && ok "greeting shows adoption rung" \
                                   || bad "greeting lacks rung"

# 9b. adopt — one-shot: fresh clone -> live gates (IH-3). The dormant-gates
# class: core.hooksPath was only PRINTED/healed-in-precond, so a fresh clone's
# LOCAL gates slept until something healed them. `socom adopt` composes
# init+compile+wire (routing the wire through the same _wire_hooks helper as
# doctor/precond — single source) and reports the rung; idempotent; a non-git
# dir warns (CI re-asserts) but never crashes. Uses its own throwaway repos so
# the main test repo's wiring is untouched.
AR="$T/adopt-repo"; mkdir -p "$AR"; ( cd "$AR" && git init -q -b main . )
( cd "$AR" && "$SOCOM" adopt . >/dev/null 2>&1 ); check "adopt bootstraps a fresh git repo" 0 $?
[ "$(git -C "$AR" config core.hooksPath)" = ".githooks" ] \
  && ok "adopt wires core.hooksPath — local gates live" \
  || bad "adopt did not wire hooks: [$(git -C "$AR" config core.hooksPath)]"
[ -f "$AR/CLAUDE.md" ] && [ -f "$AR/socom.yaml" ] \
  && ok "adopt planted + compiled (CLAUDE.md + socom.yaml present)" \
  || bad "adopt left the repo uncompiled"
( cd "$AR" && "$SOCOM" adopt . >/dev/null 2>&1 ); check "adopt is idempotent (safe re-run)" 0 $?
[ "$(git -C "$AR" config core.hooksPath)" = ".githooks" ] \
  && ok "adopt idempotent: hooks still wired after re-run" \
  || bad "adopt re-run lost the hooks wiring"
( cd "$AR" && "$SOCOM" adopt . 2>&1 | grep -q "rung:" ) \
  && ok "adopt reports the adoption rung (reuses adoption_rung)" \
  || bad "adopt did not report a rung"
ANG="$T/adopt-nongit"; mkdir -p "$ANG"
( cd "$ANG" && "$SOCOM" adopt . >/dev/null 2>&1 ); check "adopt in a non-git dir warns but never crashes" 0 $?

# 9c. the exit is DURABLE (DEF-PRECOND-SILENTLY-REVERSES-UNADOPT-01).
# unadopt restored core.hooksPath and erased every trace of itself, so the next
# `precond` read the unwired repo as drift, re-armed the hooks, and scored the
# reversal `1 healed` under PASS. An exit a later command silently undoes is
# worse than no exit: the user believes they left.
UR="$T/unadopt-repo"; mkdir -p "$UR"; ( cd "$UR" && git init -q -b main . )
( cd "$UR" && "$SOCOM" adopt . >/dev/null 2>&1 )
( cd "$UR" && "$SOCOM" unadopt . >/dev/null 2>&1 ); check "unadopt" 0 $?
[ -z "$(git -C "$UR" config core.hooksPath || true)" ] \
  && ok "unadopt unsets core.hooksPath" \
  || bad "unadopt left hooks wired: [$(git -C "$UR" config core.hooksPath)]"
[ -n "$(git -C "$UR" config socom.unadopted || true)" ] \
  && ok "unadopt records the exit durably (socom.unadopted)" \
  || bad "unadopt left no record — the next heal cannot tell it from drift"
( cd "$UR" && "$SOCOM" precond >/dev/null 2>&1 )
[ -z "$(git -C "$UR" config core.hooksPath || true)" ] \
  && ok "precond does NOT re-arm hooks after unadopt (the exit holds)" \
  || bad "precond silently reversed unadopt: [$(git -C "$UR" config core.hooksPath)]"
( cd "$UR" && "$SOCOM" precond 2>&1 | grep -q "UNADOPTED" ) \
  && ok "precond REPORTS the unadopted state instead of healing it" \
  || bad "precond stayed silent about an unadopted repo"
( cd "$UR" && "$SOCOM" doctor 2>&1 | grep -qi "unadopted" ) \
  && ok "doctor reports unadopted as INFO, not as a defect to fix" \
  || bad "doctor did not distinguish unadopted from never-adopted"
( cd "$UR" && "$SOCOM" adopt . >/dev/null 2>&1 )
[ "$(git -C "$UR" config core.hooksPath)" = ".githooks" ] \
  && ok "an explicit re-adopt is the way back in (and clears the record)" \
  || bad "adopt could not re-wire an unadopted repo"
[ -z "$(git -C "$UR" config socom.unadopted || true)" ] \
  && ok "re-adopt clears the exit record (only adopt may)" \
  || bad "re-adopt left the unadopted record in place"
# A heal that writes the HOST'S OWN git config is never a quiet PASS.
git -C "$UR" config --unset core.hooksPath
( cd "$UR" && "$SOCOM" precond 2>&1 | grep -q "WROTE GIT CONFIG" ) \
  && ok "a git-config heal is named as a config write, not a silent 'healed'" \
  || bad "precond wrote git config without saying so"

# 9e. the hand-written CLAUDE.md wedge (DEF-HANDWRITTEN-CLAUDE-MD-WEDGES-THE-
#     LADDER-01). A repo that already has a CLAUDE.md is socom's OWN stated
#     audience — it has one because it drives Claude Code. compile refused to
#     clobber it (HR2, correct) and the rung read that same absence as
#     "run `socom compile`", so the tool printed the step it had just refused,
#     forever. Observed in the wild: four compiles and one adopt, byte-identical.
#     This is the acceptance, black-box, in the order a stranger meets it.
WR="$T/wedge-repo"; mkdir -p "$WR"; ( cd "$WR" && git init -q -b main . )
printf '# My rules\n\nDo not delete anything.\n' > "$WR/CLAUDE.md"
( cd "$WR" && "$SOCOM" init . >/dev/null 2>&1 )
( cd "$WR" && "$SOCOM" compile >/dev/null 2>&1 ); check "compile on a repo that owns its CLAUDE.md" 0 $?
grep -q "Do not delete anything." "$WR/CLAUDE.md" \
  && ok "compile did NOT touch the user's CLAUDE.md (HR2 holds)" \
  || bad "compile clobbered a hand-written CLAUDE.md"
[ -f "$WR/CLAUDE.socom.md" ] \
  && ok "compile left socom's half beside it (CLAUDE.socom.md)" \
  || bad "compile refused with no exit but --force"
WNEXT="$( cd "$WR" && "$SOCOM" greet 2>&1 | grep '^ *next:' )"
printf '%s' "$WNEXT" | grep -q 'socom compile' \
  && bad "the rung still prints the step compile just REFUSED: [$WNEXT]" \
  || ok "the rung never prints a next: step this run already refused"
printf '%s' "$WNEXT" | grep -q '@CLAUDE.socom.md' \
  && ok "next: names the one line the USER adds (socom does not write it)" \
  || bad "next: does not name a satisfiable step: [$WNEXT]"
( cd "$WR" && "$SOCOM" doctor 2>&1 | grep -q "hand-written or tampered" ) \
  && bad "doctor still calls the user's own file tampered" \
  || ok "doctor no longer reports the user's own CLAUDE.md as tampered"
# The user adds the line. The ladder moves, and their file is still theirs.
printf '@CLAUDE.socom.md\n' >> "$WR/CLAUDE.md"
( cd "$WR" && "$SOCOM" greet 2>&1 | grep -q 'rung: T1' ) \
  && bad "the rung stayed at T1 after the import — still wedged" \
  || ok "one line the user writes advances the rung past T1"
grep -q "Do not delete anything." "$WR/CLAUDE.md" \
  && ok "...and the user's own instructions survived the advance" \
  || bad "advancing the rung cost the user their CLAUDE.md"
# --force stays available and stays destructive. It just stops being the ONLY exit.
WF="$T/wedge-force"; mkdir -p "$WF"; ( cd "$WF" && git init -q -b main . )
printf '# My rules\n\nDo not delete anything.\n' > "$WF/CLAUDE.md"
( cd "$WF" && "$SOCOM" init . >/dev/null 2>&1 )
( cd "$WF" && "$SOCOM" compile --force >/dev/null 2>&1 )
grep -q "Do not delete anything." "$WF/CLAUDE.md" \
  && bad "--force stopped overwriting — the escape hatch changed meaning" \
  || ok "--force still adopts the file by DESTROYING it (unchanged, on purpose)"

"$SOCOM" baseline . >/dev/null;            check "baseline" 0 $?
python3 - <<'EOF' && ok "chunk ids unique + full-path (STORAGE identity)" || bad "chunk identity violated"
import json, sys
ids = [json.loads(l)["id"] for l in open(".socom/index/chunks.jsonl")]
assert len(set(ids)) == len(ids), "duplicate chunk ids"
assert any("/principle." in i for i in ids), "ancestor ids missing from paths"
EOF
[ -f .socom/index/baseline.json ] && ok "baseline.json written" || bad "no baseline.json"

# 10. L1 retrieval against the baseline contract
"$SOCOM" embed . >/dev/null;               check "embed builds L1 index" 0 $?
"$SOCOM" query "how do I prove work is finished" | grep -q "L1/bm25" \
  && ok "query serves from L1" || bad "query not using L1"
"$SOCOM" eval . >/dev/null 2>&1; EV=$?
[ "$EV" = "0" ] || [ "$EV" = "1" ] && ok "eval runs contract (rc=$EV)" \
                                   || bad "eval crashed (rc=$EV)"
mv .socom/index/vectors.json /tmp/socom-smoke-v.json
"$SOCOM" query "prove work done" 2>&1 | grep -q "degraded to L0" \
  && ok "query degrades loudly to L0 floor (R6)" || bad "silent/failed degrade (R6)"
mv /tmp/socom-smoke-v.json .socom/index/vectors.json
# lifecycle filter: a retired artifact must never surface
cat > .socom/promises/retired-thing.xml <<EOF
<memory socom="0.1" id="M-old" state="retired">
  <decoded-rule embed="true">zebra quokka xylophone unique retired content</decoded-rule>
</memory>
EOF
"$SOCOM" embed . >/dev/null
"$SOCOM" query "zebra quokka xylophone" 2>/dev/null | grep -q "retired-thing" \
  && bad "retired artifact surfaced (lifecycle filter)" \
  || ok "retired artifacts never surface (lifecycle filter)"
rm .socom/promises/retired-thing.xml && "$SOCOM" embed . >/dev/null

# 10c. cycle — the eval rollup (ledger -> scored cycle: pass@1/pass@k by seat)
"$SOCOM" cycle >/dev/null 2>&1; check "cycle degrades loudly without ledger" 1 $?
# value (readout) — C1: never errors, even on a bare substrate (no ledger yet).
"$SOCOM" value >/dev/null 2>&1; check "value exits 0 on a bare substrate (readout, not a gate)" 0 $?
"$SOCOM" value | grep -q "runs scored    not yet measured" \
  && ok "value degrades loudly without a ledger (not a silent zero)" \
  || bad "value did not report 'not yet measured' for runs"
# value C1 hardening (regression): a row that is valid JSON but missing the
# `promise` key (manual edit / partial producer) must NOT crash the readout.
mkdir -p .socom/ledger
printf '{"ts":"2026-06-10","seat":"builder","verdict":"kept","attempt":1}\n' > .socom/ledger/runs.jsonl
"$SOCOM" value >/dev/null 2>&1; check "value tolerates a schema-incomplete ledger row (C1, no crash)" 0 $?
rm -rf .socom/ledger
mkdir -p .socom/ledger
cat > .socom/ledger/runs.jsonl <<EOF
{"ts":"2026-06-10T01:00:00Z","seat":"builder","promise":"P-A","contract":"C-A","gate_band":"fast","exit_code":0,"duration_s":100,"attempt":1,"verdict":"kept"}
{"ts":"2026-06-10T02:00:00Z","seat":"builder","promise":"P-B","contract":"C-B","gate_band":"fast","exit_code":1,"duration_s":50,"attempt":1,"verdict":"broken"}
{"ts":"2026-06-10T03:00:00Z","seat":"builder","promise":"P-B","contract":"C-B","gate_band":"fast","exit_code":0,"duration_s":80,"attempt":2,"verdict":"kept"}
{"ts":"2026-06-10T04:00:00Z","seat":"reviewer","promise":"P-C","gate_band":"fast","exit_code":1,"duration_s":30,"attempt":1,"verdict":"broken"}
EOF
CY="$("$SOCOM" cycle --cycle)"
echo "$CY" | grep -q "pass@1 1/3" && echo "$CY" | grep -q "pass@k 2/3" \
  && ok "cycle summary pass@1 1/3, pass@k 2/3 (hand-count)" \
  || bad "cycle summary wrong:
$CY"
echo "$CY" | grep -Eq "seat builder .*pass@1 1/2 .*pass@k 2/2" \
  && ok "cycle pass@1/pass@k BY SEAT (builder 1/2, 2/2)" || bad "builder seat numbers wrong"
echo "$CY" | grep -Eq "seat reviewer .*pass@1 0/1 .*pass@k 0/1" \
  && ok "cycle scores reviewer seat (0/1, 0/1)" || bad "reviewer seat numbers wrong"
echo "$CY" | grep -q "P-B" && echo "$CY" | grep -q "P-C" \
  && ok "cycle surfaces hotspots (P-B, P-C)" || bad "hotspots missing"
# value C2: with a ledger present, value's pass@1 routes through the SAME
# _cycle_rollup as cycle — both must read pass@1 33.3% (1 of 3 promises). No
# parallel math: if these ever disagree, one of them is lying.
VAL="$("$SOCOM" value)"
echo "$VAL" | grep -Eq "runs scored    pass@1 33.3% .* 3 promises, 4 runs" \
  && ok "value pass@1 matches cycle (33.3%, via shared _cycle_rollup)" \
  || bad "value runs line wrong:
$VAL"
# gate tie-in, BOTH directions (contract): bind checks.eval, flip the threshold
"$SOCOM" gate eval >/dev/null 2>&1; check "gate eval unknown before binding" 1 $?
python3 - "$SOCOM" <<'PYEOF'
import sys, yaml, pathlib
p = pathlib.Path("socom.yaml"); c = yaml.safe_load(p.read_text())
c["checks"]["eval"] = f"{sys.argv[1]} cycle --gate --threshold 90"
p.write_text(yaml.safe_dump(c, sort_keys=False))
PYEOF
"$SOCOM" gate eval >/dev/null 2>&1; check "gate eval RED below threshold (90)" 1 $?
python3 - "$SOCOM" <<'PYEOF'
import sys, yaml, pathlib
p = pathlib.Path("socom.yaml"); c = yaml.safe_load(p.read_text())
c["checks"]["eval"] = f"{sys.argv[1]} cycle --gate --threshold 10"
p.write_text(yaml.safe_dump(c, sort_keys=False))
PYEOF
"$SOCOM" gate eval >/dev/null 2>&1; check "gate eval PASS above threshold (10)" 0 $?
rm -rf .socom/ledger .socom/cycles

# 10d. lesson — experience earned from cycle hotspots (the eval->lesson bridge)
"$SOCOM" lesson candidates >/dev/null 2>&1; check "lesson candidates degrades without cycle" 1 $?
mkdir -p .socom/ledger
cat > .socom/ledger/runs.jsonl <<EOF
{"ts":"2026-06-10T01:00:00Z","seat":"builder","promise":"P-HOT","gate_band":"fast","exit_code":1,"duration_s":50,"attempt":1,"verdict":"broken"}
{"ts":"2026-06-10T02:00:00Z","seat":"builder","promise":"P-HOT","gate_band":"fast","exit_code":1,"duration_s":60,"attempt":2,"verdict":"broken"}
{"ts":"2026-06-10T03:00:00Z","seat":"builder","promise":"P-HOT","gate_band":"fast","exit_code":0,"duration_s":70,"attempt":3,"verdict":"kept"}
{"ts":"2026-06-10T04:00:00Z","seat":"reviewer","promise":"P-COLD","gate_band":"fast","exit_code":1,"duration_s":30,"attempt":1,"verdict":"broken"}
{"ts":"2026-06-10T05:00:00Z","seat":"reviewer","promise":"P-COLD","gate_band":"fast","exit_code":1,"duration_s":30,"attempt":2,"verdict":"broken"}
EOF
"$SOCOM" cycle >/dev/null
"$SOCOM" lesson candidates --domain data-pipeline | grep -q "2 candidate(s) born" \
  && ok "lesson candidates born from cycle hotspots (P-HOT, P-COLD)" || bad "candidates not born from hotspots"
[ -f .socom/lessons/L-P-HOT.xml ] && [ -f .socom/lessons/L-P-COLD.xml ] \
  && ok "lesson artifacts written + parse" || bad "lesson files missing"
python3 -c "import xml.etree.ElementTree as ET; ET.parse('.socom/lessons/L-P-HOT.xml')" \
  && ok "born lesson is well-formed XML" || bad "born lesson malformed"
"$SOCOM" lesson candidates | grep -q "0 candidate(s) born" \
  && ok "lesson candidates idempotent (re-run births none)" || bad "candidates not idempotent"
"$SOCOM" lesson promote L-P-HOT >/dev/null
"$SOCOM" lesson list --state active | grep -q "L-P-HOT" \
  && ok "lesson promote provisional->active + list --state filters" || bad "promote/list-filter failed"
"$SOCOM" lesson retire L-P-COLD --reason "fixed" >/dev/null
grep -q 'state="retired"' .socom/lessons/L-P-COLD.xml && [ -f .socom/lessons/L-P-COLD.xml ] \
  && ok "lesson retire -> retired, preserved on disk (never deleted)" || bad "retire/preserve failed"
"$SOCOM" index . >/dev/null 2>&1; "$SOCOM" embed >/dev/null 2>&1
LQ="$("$SOCOM" query "promise keeps failing assessment encode the guard" 2>&1)"
if echo "$LQ" | grep -q "L-P-HOT" && ! echo "$LQ" | grep -q "L-P-COLD"; then
  ok "active lesson retrieved, retired filtered (lifecycle)"
else
  bad "retrieval/lifecycle wrong"
fi
rm -rf .socom/ledger .socom/cycles .socom/lessons

# 10d2. contract — the validation contract made testable (verify runs <check> <run>)
"$SOCOM" contract verify >/dev/null 2>&1; check "contract verify usage without file" 1 $?
mkdir -p .socom/promises
cat > .socom/promises/contract-fix.xml <<'EOF'
<promise id="P-CT" state="open"><contract ref="C-CT" state="ratified">
  <goal>verify executes auto checks, flags manual ones</goal>
  <check id="1" assessor="gate:task-completion"><run>true</run><expect>auto check passes</expect></check>
  <check id="2" assessor="gate:task-completion"><run>false</run><expect>auto check fails</expect></check>
  <check id="3" assessor="reviewer"><expect>human reads the diff</expect></check>
</contract></promise>
EOF
CV="$("$SOCOM" contract verify .socom/promises/contract-fix.xml 2>&1)"; CVR=$?
[ "$CVR" = 1 ] && ok "contract verify exits nonzero when an auto check fails (rc=$CVR)" \
              || bad "contract verify rc wrong (expected 1, got $CVR)"
echo "$CV" | grep -q "check 1 .* PASS" && echo "$CV" | grep -q "check 2 .* FAIL" \
  && echo "$CV" | grep -q "check 3 .* MANUAL" \
  && ok "contract verify reports PASS / FAIL / MANUAL per check" || bad "contract verify report wrong:
$CV"
# passing-only + manual -> exit 0 (manual never auto-passed, but never fails the run)
cat > .socom/promises/contract-ok.xml <<'EOF'
<promise id="P-OK" state="open"><contract ref="C-OK" state="ratified">
  <goal>only an auto-passing check plus a manual one</goal>
  <check id="1" assessor="gate:task-completion"><run>true</run><expect>passes</expect></check>
  <check id="2" assessor="reviewer"><expect>human judgment</expect></check>
</contract></promise>
EOF
"$SOCOM" contract verify .socom/promises/contract-ok.xml >/dev/null 2>&1
check "contract verify PASSes when no auto check fails (manual pending)" 0 $?
"$SOCOM" contract show .socom/promises/contract-ok.xml | grep -q "only an auto-passing check" \
  && ok "contract show prints the goal + checks" || bad "contract show wrong"

# --record (#6f): a verify outcome becomes a real ledger row — the first
# automatic producer for the run ledger (cycle/lesson otherwise see synthetic).
rm -rf .socom/ledger
cat > .socom/promises/contract-rec.xml <<'EOF'
<promise id="P-REC" state="open"><promiser seat="builder" participant="x"/>
  <contract ref="C-REC" state="ratified">
  <goal>a recordable, fully-auto verify</goal>
  <check id="1" assessor="gate:task-completion"><run>true</run><expect>passes</expect></check>
</contract></promise>
EOF
"$SOCOM" contract verify .socom/promises/contract-rec.xml >/dev/null 2>&1
[ ! -f .socom/ledger/runs.jsonl ] \
  && ok "contract verify without --record writes no ledger row" \
  || bad "verify wrote a ledger row without --record"
"$SOCOM" contract verify .socom/promises/contract-rec.xml --record >/dev/null 2>&1
[ -f .socom/ledger/runs.jsonl ] && [ "$(wc -l < .socom/ledger/runs.jsonl)" -eq 1 ] \
  && grep -q '"verdict": "kept"' .socom/ledger/runs.jsonl \
  && grep -q '"seat": "builder"' .socom/ledger/runs.jsonl \
  && ok "contract verify --record appends a kept ledger row" \
  || bad "record row wrong: $(cat .socom/ledger/runs.jsonl 2>&1)"
"$SOCOM" contract verify .socom/promises/contract-rec.xml --record >/dev/null 2>&1
[ "$(wc -l < .socom/ledger/runs.jsonl)" -eq 2 ] \
  && grep -q '"attempt": 2' .socom/ledger/runs.jsonl \
  && ok "contract verify --record increments attempt per promise" \
  || bad "attempt not incremented"
cat > .socom/promises/contract-rec-m.xml <<'EOF'
<promise id="P-RECM" state="open"><promiser seat="builder" participant="x"/>
  <contract ref="C-RECM" state="ratified">
  <goal>auto-pass plus a manual check pending</goal>
  <check id="1" assessor="gate:task-completion"><run>true</run><expect>passes</expect></check>
  <check id="2" assessor="reviewer"><expect>human reads the diff</expect></check>
</contract></promise>
EOF
REC_BEFORE=$(wc -l < .socom/ledger/runs.jsonl)
RECM="$("$SOCOM" contract verify .socom/promises/contract-rec-m.xml --record 2>&1)"
REC_AFTER=$(wc -l < .socom/ledger/runs.jsonl)
echo "$RECM" | grep -qi "withheld" && [ "$REC_BEFORE" = "$REC_AFTER" ] \
  && ok "contract verify --record withholds the row while a manual check is pending" \
  || bad "manual-pending record not withheld (before=$REC_BEFORE after=$REC_AFTER)"
cat > .socom/promises/contract-rec-empty.xml <<'EOF'
<promise id="P-RECE" state="open"><promiser seat="builder" participant="x"/>
  <contract ref="C-RECE" state="ratified"><goal>no checks at all</goal></contract></promise>
EOF
REC_BEFORE=$(wc -l < .socom/ledger/runs.jsonl)
RECE="$("$SOCOM" contract verify .socom/promises/contract-rec-empty.xml --record 2>&1)"
REC_AFTER=$(wc -l < .socom/ledger/runs.jsonl)
echo "$RECE" | grep -qi "no auto check ran" && [ "$REC_BEFORE" = "$REC_AFTER" ] \
  && ok "contract verify --record withholds a vacuous 'kept' when no auto check ran" \
  || bad "zero-check record not withheld (before=$REC_BEFORE after=$REC_AFTER)"
"$SOCOM" cycle >/dev/null 2>&1; check "cycle consumes the verify-recorded rows (round-trip)" 0 $?

# 10c-ter. ledger concurrency — the flock (IH-4). _append_ledger_row does
# read -> compute-attempt -> append; without an exclusive lock two seats
# recording at once (multi-agent is the stated goal) read the same tail, assign
# a DUPLICATE attempt (breaking cycle's pass@1/pass@k), and can interleave a torn
# row. The flock serializes the critical section. 20 concurrent records against
# ONE promise/contract must yield exactly 20 rows, attempts 1..20 unique, all
# schema-valid. Proven red->green: the unlocked writer dups attempts, the locked
# one does not.
rm -f .socom/ledger/runs.jsonl
ci=1; while [ "$ci" -le 20 ]; do
  "$SOCOM" contract verify .socom/promises/contract-rec.xml --record >/dev/null 2>&1 &
  ci=$((ci+1))
done
wait
LCN=$(wc -l < .socom/ledger/runs.jsonl 2>/dev/null | tr -d ' ')
[ "$LCN" = "20" ] && ok "ledger flock: 20 concurrent records -> exactly 20 rows (no lost write)" \
                  || bad "ledger flock: expected 20 rows, got $LCN (lost/interleaved write)"
python3 -c "import json,sys; a=sorted(json.loads(l)['attempt'] for l in open('.socom/ledger/runs.jsonl') if l.strip()); sys.exit(0 if a==list(range(1,21)) else 1)" \
  && ok "ledger flock: attempts 1..20 unique + contiguous (no duplicate attempt)" \
  || bad "ledger flock: attempts not contiguous-unique under concurrency (race)"
python3 "$ROOT/tests/ledgercheck.py" .socom/ledger/runs.jsonl >/dev/null 2>&1 \
  && ok "ledger flock: every concurrent row schema-valid (no torn line)" \
  || bad "ledger flock: a row torn/invalid under concurrency"

# task-completion gate records its assessment BY DEFAULT (#6f-2): the gate an
# agent already runs to mark done fills the ledger without a manual flag — the
# canonical "a gate assessed the promise" event. checks.fast is bound (echo
# fast-ok) so the gate reaches the record path; an unbound gate records nothing.
rm -rf .socom/ledger
cat > .socom/promises/contract-gate.xml <<'EOF'
<promise id="P-GATE" state="open" domain="cli"><promiser seat="builder" participant="x"/>
  <contract ref="C-GATE" state="ratified"><goal>recorded at the done gate</goal>
  <check id="1" assessor="gate"><run>true</run><expect>x</expect></check></contract></promise>
EOF
"$SOCOM" gate task-completion .socom/promises/contract-gate.xml >/dev/null 2>&1
[ -f .socom/ledger/runs.jsonl ] && [ "$(wc -l < .socom/ledger/runs.jsonl)" -eq 1 ] \
  && grep -q '"verdict": "kept"' .socom/ledger/runs.jsonl \
  && grep -q '"promise": "P-GATE"' .socom/ledger/runs.jsonl \
  && ok "gate task-completion records a kept ledger row for the promise" \
  || bad "gate did not record: $(cat .socom/ledger/runs.jsonl 2>&1)"
"$SOCOM" gate task-completion .socom/promises/contract-gate.xml >/dev/null 2>&1
[ "$(wc -l < .socom/ledger/runs.jsonl)" -eq 2 ] && grep -q '"attempt": 2' .socom/ledger/runs.jsonl \
  && ok "gate task-completion increments attempt across done-attempts" \
  || bad "gate attempt not incremented"
GB=$(wc -l < .socom/ledger/runs.jsonl); "$SOCOM" gate task-completion >/dev/null 2>&1
GA=$(wc -l < .socom/ledger/runs.jsonl)
[ "$GB" = "$GA" ] && ok "gate task-completion without a promise writes no row (unchanged)" \
                  || bad "gate wrote a row without a promise arg"
GB=$(wc -l < .socom/ledger/runs.jsonl); "$SOCOM" gate task-completion /no/such.xml >/dev/null 2>&1; GBR=$?
GA=$(wc -l < .socom/ledger/runs.jsonl)
[ "$GB" = "$GA" ] && [ "$GBR" = 0 ] \
  && ok "gate task-completion with a bogus promise warns but still passes" \
  || bad "gate mishandled a bogus promise arg (rc=$GBR before=$GB after=$GA)"
# a DIRECTORY arg must not crash the gate into a false RED (OSError, not ParseError)
"$SOCOM" gate task-completion .socom >/dev/null 2>&1
[ $? = 0 ] && ok "gate task-completion with a directory arg warns but still passes (no crash)" \
           || bad "gate crashed/blocked on a directory promise arg"
"$SOCOM" cycle >/dev/null 2>&1; check "cycle round-trips the gate-recorded rows" 0 $?
rm -rf .socom/ledger .socom/cycles

# 10d-bis. ledgercheck — the run-ledger schema gate (IH-2). The measurement
# spine (.socom/ledger/runs.jsonl) was guarded by NOTHING: xmlcheck is XML-only,
# and `cycle` only catches JSON-decode errors — a row that is valid JSON but
# missing `verdict` or carrying gate_band:"purple" sailed through and silently
# REDs the eval cycle. ledgercheck parses the field contract FROM
# schemas/ledger.xml (single source) and fails any bad row; absent ledger PASSES
# (fail-open on absence, fail-closed on corruption). Wired into medium+full+CI.
LC="python3 $ROOT/tests/ledgercheck.py"
LCGOOD='{"ts":"2026-06-13T20:14:00Z","seat":"builder","promise":"P-1","contract":"C-1","gate_band":"red","exit_code":0,"duration_s":357,"attempt":1,"verdict":"kept"}'
$LC "$T/lc-absent.jsonl" >/dev/null 2>&1
check "ledgercheck: absent ledger PASSES (fail-open on absence)" 0 $?
printf '%s\n%s\n' "$LCGOOD" "$LCGOOD" > "$T/lc-good.jsonl"
$LC "$T/lc-good.jsonl" >/dev/null 2>&1
check "ledgercheck: valid rows PASS" 0 $?
printf '%s\n' '{"ts":"x","seat":"builder","promise":"P-1","contract":"C-1","gate_band":"red","exit_code":0,"duration_s":1,"attempt":1}' > "$T/lc-key.jsonl"
$LC "$T/lc-key.jsonl" >/dev/null 2>&1
check "ledgercheck: missing required key (verdict) FAILS" 1 $?
printf '%s\n' '{"ts":"x","seat":"builder","promise":"P-1","contract":"C-1","gate_band":"purple","exit_code":0,"duration_s":1,"attempt":1,"verdict":"maybe"}' > "$T/lc-enum.jsonl"
$LC "$T/lc-enum.jsonl" >/dev/null 2>&1
check "ledgercheck: bad enum value FAILS" 1 $?
printf '%s\nnot json{\n' "$LCGOOD" > "$T/lc-json.jsonl"
$LC "$T/lc-json.jsonl" >/dev/null 2>&1
check "ledgercheck: malformed JSON line FAILS" 1 $?

# 10d-ter. context — the CTX-1 context-envelope gate. Context made a first-class
# artifact: `socom context verify` exits 0 iff every targeted envelope is
# schema-valid (schemas/context.xml, single-sourced field contract + invariant)
# AND within its declared input budget (input_tokens <= budget_tokens). Fail-open
# on an absent target/no envelopes, fail-closed on malformed / missing-field /
# over-budget. The verb IS the gate the bands run (the tool verifies itself);
# wired into medium+full+CI.
CXOK='<context socom="0.1" id="CTX-1" promise="P-1" seat="builder" ts="2026-06-20T12:00:00Z" budget_tokens="8000" input_tokens="3200"/>'
"$SOCOM" context verify "$T/no-such-context.xml" >/dev/null 2>&1
check "context verify: absent target PASSES (fail-open on absence)" 0 $?
printf '%s\n' "$CXOK" > "$T/cx-good.xml"
"$SOCOM" context verify "$T/cx-good.xml" >/dev/null 2>&1
check "context verify: schema-valid in-budget envelope PASSES" 0 $?
"$SOCOM" context show "$T/cx-good.xml" | grep -q "3200 / 8000" \
  && ok "context show prints consumed/declared budget" || bad "context show wrong"
printf '%s\n' '<context socom="0.1" id="CTX-2" promise="P-1" seat="builder" ts="2026-06-20T12:00:00Z" budget_tokens="1000" input_tokens="3200"/>' > "$T/cx-over.xml"
CXO="$("$SOCOM" context verify "$T/cx-over.xml" 2>&1)"; CXOR=$?
{ [ "$CXOR" = 1 ] && echo "$CXO" | grep -q "invariant violated"; } \
  && ok "context verify: OVER-BUDGET envelope FAILS (input>budget)" \
  || bad "context verify over-budget not caught (rc=$CXOR)"
printf '%s\n' '<context socom="0.1" id="CTX-3" seat="builder" ts="2026-06-20T12:00:00Z" budget_tokens="1000" input_tokens="500"/>' > "$T/cx-miss.xml"
"$SOCOM" context verify "$T/cx-miss.xml" >/dev/null 2>&1
check "context verify: missing required field (promise) FAILS" 1 $?
printf '%s\n' '<context socom="0.1" id="CTX-4" promise="P-1" seat="builder" ts="x" budget_tokens="oops" input_tokens="500"/>' > "$T/cx-int.xml"
"$SOCOM" context verify "$T/cx-int.xml" >/dev/null 2>&1
check "context verify: non-int token field FAILS" 1 $?
printf 'not xml <<<\n' > "$T/cx-malformed.xml"
"$SOCOM" context verify "$T/cx-malformed.xml" >/dev/null 2>&1
check "context verify: malformed XML FAILS" 1 $?
printf '%s\n' '<envelope socom="0.1" id="CTX-5"/>' > "$T/cx-wrongroot.xml"
"$SOCOM" context verify "$T/cx-wrongroot.xml" >/dev/null 2>&1
check "context verify: wrong root element FAILS" 1 $?
# carry-over closures: a negative token count is a false-PASS hole (negative
# input trivially <= budget), and a wrong contract version must be rejected.
printf '%s\n' '<context socom="0.1" id="CTX-6" promise="P-1" seat="builder" ts="t" budget_tokens="1000" input_tokens="-50"/>' > "$T/cx-neg.xml"
"$SOCOM" context verify "$T/cx-neg.xml" >/dev/null 2>&1
check "context verify: a NEGATIVE input_tokens FAILS (>= 0 lower bound)" 1 $?
printf '%s\n' '<context socom="9.9-bogus" id="CTX-7" promise="P-1" seat="builder" ts="t" budget_tokens="1000" input_tokens="500"/>' > "$T/cx-ver.xml"
"$SOCOM" context verify "$T/cx-ver.xml" >/dev/null 2>&1
check "context verify: a mismatched socom= contract version FAILS" 1 $?
CXD="$T/ctxdir"; mkdir -p "$CXD"; printf '%s\n' "$CXOK" > "$CXD/a.xml"; cp "$T/cx-over.xml" "$CXD/b.xml"
"$SOCOM" context verify "$CXD" >/dev/null 2>&1
check "context verify: a dir with ANY invalid envelope FAILS" 1 $?
rm -f "$CXD/b.xml"
"$SOCOM" context verify "$CXD" >/dev/null 2>&1
check "context verify: a dir of only-valid envelopes PASSES" 0 $?

# 10d-quater. context CTX-2 — MEASURED + COMPRESSIBLE input. input_tokens is no
# longer hand-authored: `measure` writes per-ref counts from the live artifacts,
# `verify` RE-MEASURES them and fails on any mismatch (un-forgeable), and
# `compress` drops the lowest-relevance inputs (l0_score vs the promise goal) until
# the sum fits budget. measure/compress MUTATE and are NOT gates; verify stays pure.
# inputs live INSIDE the repo — refs are repo-contained (path-traversal is refused).
CX2D="ctx2inputs"; mkdir -p "$CX2D" .socom/promises
i=0; while [ "$i" -lt 3 ]; do printf 'residuality gate saltzer schroeder complete mediation least privilege fail safe\n'; i=$((i+1)); done > "$CX2D/relevant.txt"
i=0; while [ "$i" -lt 30 ]; do printf 'unrelated lorem ipsum filler cats weather trivia nonsense padding words here\n'; i=$((i+1)); done > "$CX2D/filler.txt"
cat > .socom/promises/P-CX2.xml <<'EOF'
<promise id="P-CX2" state="open"><contract ref="C-CX2" state="ratified"><goal>residuality gate saltzer schroeder protection principles complete mediation</goal></contract></promise>
EOF
mkE() { cat > "$1" <<EOF2
<?xml version="1.0" encoding="UTF-8"?>
<context socom="0.1" id="$2" promise="P-CX2" seat="builder" ts="2026-06-20T12:00:00Z" budget_tokens="$3" input_tokens="0">
  <inputs><input ref="$CX2D/relevant.txt" tokens="0"/><input ref="$CX2D/filler.txt" tokens="0"/></inputs>
</context>
EOF2
}
mkE "$T/cx2-a.xml" CX2A 100000
"$SOCOM" context measure "$T/cx2-a.xml" 2>&1 | grep -q "input_tokens=" \
  && ok "context measure writes token counts from the live refs" || bad "measure did not write counts"
"$SOCOM" context verify "$T/cx2-a.xml" >/dev/null 2>&1
check "context verify: a measured envelope PASSES (declared == re-measured)" 0 $?
sed 's/input_tokens="[0-9]*"/input_tokens="7"/' "$T/cx2-a.xml" > "$T/cx2-lie.xml"
"$SOCOM" context verify "$T/cx2-lie.xml" >/dev/null 2>&1
check "context verify: a forged input_tokens FAILS (re-measure mismatch)" 1 $?
cat > "$T/cx2-missing.xml" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<context socom="0.1" id="CX2M" promise="P-CX2" seat="builder" ts="t" budget_tokens="100000" input_tokens="5"><inputs><input ref="$CX2D/nope.txt" tokens="5"/></inputs></context>
EOF
"$SOCOM" context verify "$T/cx2-missing.xml" >/dev/null 2>&1
check "context verify: an unreadable input ref FAILS (degrade loudly)" 1 $?
"$SOCOM" context verify "$T/cx-good.xml" >/dev/null 2>&1
check "context verify: a CTX-1 no-<inputs> envelope still PASSES (backward-compat)" 0 $?
mkE "$T/cx2-big.xml" CX2B 100
"$SOCOM" context measure "$T/cx2-big.xml" >/dev/null
"$SOCOM" context verify "$T/cx2-big.xml" >/dev/null 2>&1
check "context verify: an over-budget measured envelope FAILS" 1 $?
COUT="$("$SOCOM" context compress "$T/cx2-big.xml" 2>&1)"; CCR=$?
{ [ "$CCR" = 0 ] && echo "$COUT" | grep -q "filler.txt"; } \
  && ok "context compress drops the least-relevant input (filler, keeps relevant)" \
  || bad "compress dropped wrong/none (rc=$CCR): $COUT"
"$SOCOM" context verify "$T/cx2-big.xml" >/dev/null 2>&1
check "context verify: PASSES after compress brings it within budget" 0 $?
"$SOCOM" context compress "$T/cx2-a.xml" 2>&1 | grep -q "already within budget" \
  && ok "context compress is a no-op when already within budget" || bad "compress no-op path wrong"
# path containment: a ref escaping the repo tree (absolute / out-of-repo) is
# refused — measure/verify never read an arbitrary file (path-traversal blocker).
cat > "$T/cx2-escape.xml" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<context socom="0.1" id="CX2E" promise="P-CX2" seat="builder" ts="t" budget_tokens="100000" input_tokens="9"><inputs><input ref="/etc/hosts" tokens="9"/></inputs></context>
EOF
"$SOCOM" context verify "$T/cx2-escape.xml" >/dev/null 2>&1
check "context verify: an out-of-repo (absolute) ref is refused — path containment" 1 $?
rm -f .socom/promises/P-CX2.xml
rm -rf "$CX2D"

# 10d-quinquies. context emit — the PRODUCER (CTX-3 slice). Closes the loop the
# gate was missing: emit writes a measured, schema-valid envelope from the live
# refs, so `context verify` has real input instead of fail-opening on emptiness.
rm -rf .socom/context
printf 'hello context producer\n' > "$R/emit-a.txt"
printf 'a second loaded artifact, somewhat longer than the first one here\n' > "$R/emit-b.txt"
EOUT="$("$SOCOM" context emit --promise P-EMIT --seat builder --budget 100000 \
        --input emit-a.txt --input emit-b.txt 2>&1)"; ER=$?
{ [ "$ER" = 0 ] && echo "$EOUT" | grep -q "input_tokens="; } \
  && ok "context emit writes a measured envelope (exit 0)" || bad "emit failed (rc=$ER): $EOUT"
EFILE="$(ls .socom/context/CTX-*-001.xml 2>/dev/null | head -1)"
[ -n "$EFILE" ] && ok "context emit auto-generates a CTX-<date>-001 id" \
  || bad "emit did not auto-id into .socom/context"
"$SOCOM" context verify .socom/context >/dev/null 2>&1
check "context emit -> verify PASSES (producer feeds the gate honestly)" 0 $?
"$SOCOM" context emit --promise P-EMIT --seat builder --budget 100000 --input emit-a.txt >/dev/null 2>&1
ls .socom/context/CTX-*-002.xml >/dev/null 2>&1 \
  && ok "context emit increments the daily sequence (…-002)" || bad "emit did not increment seq"
# emit RECORDS truth; it is not a gate. An over-budget work unit is written
# honestly (exit 0, loud warning), and the read-only verify gate is what fails it.
EOVR="$("$SOCOM" context emit --promise P-EMIT --seat builder --budget 5 \
        --input emit-b.txt --id CTX-OVER-1 2>&1)"; EOR=$?
{ [ "$EOR" = 0 ] && echo "$EOVR" | grep -q "WARNING"; } \
  && ok "context emit: over-budget writes honestly + warns, exit 0 (producer, not gate)" \
  || bad "emit over-budget wrong (rc=$EOR): $EOVR"
"$SOCOM" context verify .socom/context/CTX-OVER-1.xml >/dev/null 2>&1
check "context verify FAILS the over-budget envelope emit recorded" 1 $?
# degrade loudly: an unreadable input ref is refused, with NO file written (the
# --out stays in-repo so this exercises the REF refusal, not output containment).
"$SOCOM" context emit --promise P-EMIT --seat builder --budget 100 \
   --input no-such.txt --id CTX-BAD-1 >/dev/null 2>&1
check "context emit: an unreadable input ref is refused (exit nonzero)" 1 $?
[ -f .socom/context/CTX-BAD-1.xml ] && bad "emit wrote a file despite a bad ref" \
  || ok "context emit: no envelope written when a ref is refused"
"$SOCOM" context emit --promise P-EMIT --seat builder --budget 100 \
   --input /etc/hosts --id CTX-ESC-1 >/dev/null 2>&1
check "context emit: an out-of-repo (absolute) input ref is refused — containment" 1 $?
"$SOCOM" context emit --seat builder --budget 100 --input emit-a.txt >/dev/null 2>&1
check "context emit: a missing required flag (--promise) is refused" 1 $?
SOCOM_SEAT=reviewer "$SOCOM" context emit --promise P-ENV --budget 100000 \
   --input emit-a.txt --id CTX-ENV-1 >/dev/null 2>&1
{ [ -f .socom/context/CTX-ENV-1.xml ] && grep -q 'seat="reviewer"' .socom/context/CTX-ENV-1.xml; } \
  && ok "context emit: seat falls back to \$SOCOM_SEAT" || bad "emit \$SOCOM_SEAT fallback wrong"
# OUTPUT path containment — symmetric with the --input checks above. A crafted
# --id that escapes the repo, or an out-of-repo --out, must be refused with no
# file written outside the tree (the write-side path-traversal blocker).
"$SOCOM" context emit --promise P-ESC --seat builder --budget 100 \
   --input emit-a.txt --id "../../../tmp/socom-escape-$$" >/dev/null 2>&1
ESCR=$?; [ "$ESCR" != 0 ] && [ ! -f "/tmp/socom-escape-$$.xml" ] \
  && ok "context emit: a repo-escaping --id is refused, nothing written outside" \
  || { bad "emit --id escaped containment (rc=$ESCR)"; rm -f "/tmp/socom-escape-$$.xml"; }
"$SOCOM" context emit --promise P-ESC --seat builder --budget 100 \
   --input emit-a.txt --out "/tmp/socom-out-escape-$$.xml" >/dev/null 2>&1
OESR=$?; [ "$OESR" != 0 ] && [ ! -f "/tmp/socom-out-escape-$$.xml" ] \
  && ok "context emit: an out-of-repo --out is refused, nothing written outside" \
  || { bad "emit --out escaped containment (rc=$OESR)"; rm -f "/tmp/socom-out-escape-$$.xml"; }
# Duplicate scalar flag is ambiguous intent — degrade loudly, not last-wins.
"$SOCOM" context emit --promise P-1 --promise P-2 --seat builder --budget 100 \
   --input emit-a.txt --id CTX-DUP-1 >/dev/null 2>&1
check "context emit: a duplicated scalar flag (--promise twice) is refused" 1 $?
# Zero-input work unit is legal: a CTX-1-style envelope (no <inputs>) that verifies.
"$SOCOM" context emit --promise P-ZERO --seat builder --budget 100 --id CTX-ZERO-1 >/dev/null 2>&1
{ [ -f .socom/context/CTX-ZERO-1.xml ] \
  && ! grep -q "<inputs>" .socom/context/CTX-ZERO-1.xml \
  && "$SOCOM" context verify .socom/context/CTX-ZERO-1.xml >/dev/null 2>&1; } \
  && ok "context emit: a zero-input envelope is legal and verifies (CTX-1 style)" \
  || bad "emit zero-input envelope wrong"
rm -rf .socom/context

# 10d-sexies. the REAL LOOP (earn CTX-4): low-friction env-var emit + the opt-in
# `verify --require <promise>` assertion. --require is fail-CLOSED on an
# unfulfilled promise, while the default verify stays fail-OPEN on an empty dir.
SOCOM_PROMISE=P-REAL SOCOM_SEAT=builder "$SOCOM" context emit --budget 100000 \
   --input emit-a.txt >/dev/null 2>&1
{ ls .socom/context/CTX-*-001.xml >/dev/null 2>&1 \
  && grep -q 'promise="P-REAL"' .socom/context/CTX-*-001.xml; } \
  && ok "context emit: promise/seat fall back to \$SOCOM_PROMISE/\$SOCOM_SEAT" \
  || bad "emit env-var fallback wrong"
"$SOCOM" context verify --require P-REAL >/dev/null 2>&1
check "context verify --require: a fulfilled promise PASSES" 0 $?
"$SOCOM" context verify --require P-REAL,P-GHOST >/dev/null 2>&1
check "context verify --require: an unfulfilled promise FAILS (fail-closed)" 1 $?
"$SOCOM" context verify --require >/dev/null 2>&1
check "context verify --require: a dangling --require (no value) is refused (R6)" 1 $?
# review fixes (degrade loudly): a comma-only value yields no ids, a typo'd flag
# must not become a positional target, and ids/promises are whitespace-trimmed.
"$SOCOM" context verify --require "," >/dev/null 2>&1
check "context verify --require: a comma-only value (no ids) is refused (R6)" 1 $?
"$SOCOM" context verify --requre P-REAL >/dev/null 2>&1
check "context verify: an unknown flag (typo) is refused, not silently dropped (R6)" 1 $?
"$SOCOM" context verify --require " P-REAL " >/dev/null 2>&1
check "context verify --require: ids are whitespace-trimmed (' P-REAL ' matches)" 0 $?
rm -rf .socom/context
# the bridge to CTX-4: --require makes ABSENCE a failure, but the DEFAULT stays
# fail-open so the existing band/CI does not break on a producer-less repo.
"$SOCOM" context verify >/dev/null 2>&1
check "context verify (default): empty dir still fail-OPEN (unchanged posture)" 0 $?
"$SOCOM" context verify --require P-REAL >/dev/null 2>&1
check "context verify --require: empty dir FAILS (opt-in teeth, not default)" 1 $?

rm -rf .socom/promises

# 10e. precond — velocity-first work-readiness pre-flight (the published gate)
"$SOCOM" precond >/dev/null 2>&1; check "precond passes on a healthy repo" 0 $?
rm -rf .socom/promises
"$SOCOM" precond --no-heal >/dev/null 2>&1; check "precond --no-heal BLOCKS missing dir" 1 $?
[ -d .socom/promises ] && bad "precond --no-heal healed (must not)" \
                       || ok "precond --no-heal asserts without fixing"
"$SOCOM" precond | grep -q "healed" && ok "precond auto-heals missing substrate dir" \
                                    || bad "precond did not heal"
[ -d .socom/promises ] && ok "precond heal recreated the dir" || bad "dir not recreated"
"$SOCOM" precond builder >/dev/null 2>&1; check "precond warns (no claim) but never blocks" 0 $?

# 10f. introspect — handoff evidence -> replayable assertions + lesson candidates
rm -f .socom/handoffs/H-*.xml
"$SOCOM" introspect >/dev/null 2>&1; check "introspect degrades loudly without a handoff" 1 $?
cat > .socom/handoffs/H-T1.xml <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<handoff id="H-T1" date="2026-06-14T00:00:00Z">
  <evidence>
    <command exit="0">echo ok</command>
    <command exit="1" note="expected — forced-fail test">false</command>
    <command exit="1">boom</command>
  </evidence>
</handoff>
EOF
"$SOCOM" introspect H-T1.xml | grep -q "3 new assertion(s)" \
  && ok "introspect captures one assertion per evidence command" \
  || bad "introspect did not capture 3 assertions"
[ "$(wc -l < .socom/assertions/log.jsonl)" -eq 3 ] \
  && ok "assertion log has 3 JSONL rows" || bad "assertion log row count wrong"
python3 -c "import json; [json.loads(l) for l in open('.socom/assertions/log.jsonl')]" \
  && ok "assertion rows are well-formed JSON" || bad "assertion rows malformed"
[ -f .socom/lessons/L-A-H-T1-2.xml ] \
  && grep -q 'source="introspect"' .socom/lessons/L-A-H-T1-2.xml \
  && ok "captured failure births provisional lesson (source=introspect)" \
  || bad "unexpected-fail assertion did not birth a lesson"
[ -f .socom/lessons/L-A-H-T1-1.xml ] \
  && bad "noted expected-fail wrongly birthed a lesson" \
  || ok "noted expected-fail records but births no lesson"
"$SOCOM" introspect H-T1.xml | grep -q "0 new assertion(s)" \
  && ok "introspect idempotent (re-run captures none)" || bad "introspect not idempotent"
cat > .socom/handoffs/H-T2.xml <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<handoff id="H-T2" date="2026-06-14T00:00:00Z"><done/></handoff>
EOF
"$SOCOM" introspect H-T2.xml >/dev/null 2>&1; check "introspect never blocks on a no-evidence handoff" 0 $?
"$SOCOM" introspect H-T2.xml | grep -q "no assertions to capture" \
  && ok "no-evidence handoff -> no assertions (non-blocking)" || bad "no-evidence path wrong"
rm -rf .socom/assertions .socom/lessons .socom/handoffs/H-T1.xml .socom/handoffs/H-T2.xml

# 11. forge verbs
"$SOCOM" forge list | grep -q "ci-status" && ok "forge lists canon verbs" \
                                          || bad "forge verbs missing"
"$SOCOM" forge ci-status >/dev/null 2>&1; check "unbound forge verb fails honestly" 1 $?
"$SOCOM" forge nosuchverb >/dev/null 2>&1; check "unknown forge verb RED" 1 $?
python3 - <<'EOF'
import yaml, pathlib
p = pathlib.Path("socom.yaml"); c = yaml.safe_load(p.read_text())
c["forge"] = {"ci-status": "echo result=succeeded status=completed"}
p.write_text(yaml.safe_dump(c, sort_keys=False))
EOF
"$SOCOM" forge ci-status 2>/dev/null | grep -q "succeeded" \
  && ok "bound forge verb dispatches" || bad "bound forge verb failed"
"$SOCOM" compile . --force >/dev/null
grep -q "Forge — git-provider operations" CLAUDE.md \
  && ok "forge table compiled into views" || bad "forge missing from views"

# 12. CI adapters — GitOps on any provider
for f in .github/workflows/socom-gates.yml .gitlab-ci.yml .socom/ci/azure-socom-gates.yml; do
  [ -f "$f" ] && grep -q "socom:generated" "$f" && ok "CI adapter $f generated+stamped" \
                                                || bad "CI adapter $f missing/unstamped"
done
grep -q "re-assert checks.full" .github/workflows/socom-gates.yml \
  && ok "CI adapters re-assert the bound full check (R1)" \
  || bad "CI adapter lost the R1 re-assertion"

# 13. redaction (HR6)
cat > .socom/memory/memories/leaky.md <<EOF
a memory containing password = supersecret123 which must not travel
EOF
"$SOCOM" hydrate . 2>&1 | grep -q "REFUSED leaky" && ok "hydrate refuses secrets (HR6)" \
                                                  || bad "hydrate leaked a secret (HR6)"
# hydrate must preserve pre-existing user memory (pilot finding, HR2)
# slug derived EXACTLY as the tool derives it (resolved path — macOS /var
# is a symlink to /private/var; pwd alone gives a different slug)
SLUG="$(python3 -c "from pathlib import Path; print(str(Path.cwd().resolve()).replace('/','-').replace('.','-'))")"
MEMMD="$HOME/.claude/projects/$SLUG/memory/MEMORY.md"
mkdir -p "$(dirname "$MEMMD")"
printf '# My index\n- [precious](precious.md) — user entry\n' > "$MEMMD"
"$SOCOM" hydrate . >/dev/null
grep -q "precious" "$MEMMD" && ok "hydrate preserves user MEMORY.md (HR2)" \
                            || bad "hydrate clobbered user MEMORY.md (HR2)"
"$SOCOM" hydrate . >/dev/null
[ "$(grep -c 'socom:hydrated section' "$MEMMD")" = "1" ] \
  && ok "hydrate block is idempotent" || bad "hydrate block duplicated"
cat > .socom/promises/leak.xml <<EOF
<promise socom="0.1" id="x"><goal embed="true">token = abcd1234efgh5678</goal></promise>
EOF
"$SOCOM" index . 2>&1 | grep -q "REDACTED" && ok "index redacts secrets (HR6)" \
                                           || bad "index embedded a secret (HR6)"

# 14. install/uninstall — symlink the checkout onto PATH, .resolve()-safe.
#     Isolated: targets an explicit dir, never the real ~/.local/bin.
BIN="$T/bin"
"$SOCOM" install "$BIN" >/dev/null;    check "install links onto a bin dir" 0 $?
[ -L "$BIN/socom" ] && [ "$(readlink "$BIN/socom")" = "$SOCOM" ] \
  && ok "install symlink points at this checkout" \
  || bad "install symlink wrong target"
"$BIN/socom" greet . >/dev/null 2>&1 && ok "linked socom runs (.resolve() TOOL_ROOT)" \
                                     || bad "linked socom failed to resolve resources"
"$SOCOM" install "$BIN" >/dev/null;    check "install is idempotent" 0 $?
mkdir -p "$T/foreign"; echo "not socom" > "$T/foreign/socom"
"$SOCOM" install "$T/foreign" >/dev/null 2>&1; check "install refuses foreign file" 1 $?
grep -q "not socom" "$T/foreign/socom" && ok "foreign file left untouched" \
                                       || bad "install clobbered a foreign file"
"$SOCOM" uninstall "$T/foreign" >/dev/null 2>&1; check "uninstall refuses foreign file" 1 $?
"$SOCOM" uninstall "$BIN" >/dev/null;  check "uninstall removes our symlink" 0 $?
[ -e "$BIN/socom" ] && bad "uninstall left the symlink" \
                    || ok "uninstall cleaned the symlink"

# 14b. spawn — record-first worker launch (orchestration slice 1). spawn makes a
# RUN a first-class artifact: it resolves the seat (reusing render_agent), forges
# a dispatch brief in verbatim-protocol order, content-addresses the run-id off
# the brief bytes (idempotent on identical intent), and writes an atomic run
# record. Default materializes + prints the launch command; --exec background-
# launches the bound runtime. The load-bearing boundary: spawn NEVER writes a
# verdict (no ledger row). $R is init'd+compiled, so .socom/canon/roles.xml and
# the builder seat exist.
cd "$R"; rm -rf .socom/runs .socom/ledger
mkdir -p .socom/promises
cat > .socom/promises/spawn-p.xml <<'EOF'
<promise id="P-SPN" state="open" domain="cli"><promiser seat="builder" participant="x"/>
  <intent><verbatim from="human:moses" date="2026-06-21">add teh freshness widget rite now</verbatim>
  <decoded>Record run freshness with a timestamp.</decoded></intent>
  <contract ref="C-SPN" state="ratified"><goal>a failed run is visible before the exception</goal>
  <check id="1" assessor="gate:task-completion"><run>true</run><expect>rows exist</expect></check>
  <check id="2" assessor="reviewer"><expect>idempotent on retry</expect></check></contract></promise>
EOF
"$SOCOM" spawn >/dev/null 2>&1;                         check "spawn usage without args" 1 $?
"$SOCOM" spawn --seat builder >/dev/null 2>&1;          check "spawn usage without --promise" 1 $?
"$SOCOM" spawn --seat nosuch --promise .socom/promises/spawn-p.xml >/dev/null 2>&1
check "spawn unknown seat RED (loud)" 1 $?
"$SOCOM" spawn --seat builder --promise no-such.xml >/dev/null 2>&1
check "spawn missing promise file RED (loud)" 1 $?
SPN="$("$SOCOM" spawn --seat builder --promise .socom/promises/spawn-p.xml 2>&1)"; SPNR=$?
check "spawn default materializes (rc=0)" 0 $SPNR
echo "$SPN" | grep -q "materialized" && echo "$SPN" | grep -q 'claude -p' \
  && ok "spawn default prints the launch command" || bad "spawn default output wrong:
$SPN"
RJSON="$(ls .socom/runs/R-*.json 2>/dev/null | head -1)"
[ -n "$RJSON" ] && grep -q '"status": "materialized"' "$RJSON" \
  && grep -q '"pid": null' "$RJSON" \
  && ok "spawn writes a materialized run record (status, null pid)" \
  || bad "spawn record missing/wrong: $(cat "$RJSON" 2>&1)"
RBRIEF="$(ls .socom/runs/R-*.brief.md 2>/dev/null | head -1)"
grep -q "add teh freshness widget rite now" "$RBRIEF" \
  && ok "brief carries the literal user verbatim (reviewer blind-spot defense)" \
  || bad "brief is missing the verbatim block"
grep -q "occupy the .*builder.* seat" "$RBRIEF" && grep -q "You promise" "$RBRIEF" \
  && ok "brief embeds the seat envelope (reused render_agent)" || bad "brief lacks the seat envelope"
RID1="$(basename "$RJSON" .json)"
"$SOCOM" spawn --seat builder --promise .socom/promises/spawn-p.xml >/dev/null 2>&1
[ "$(ls .socom/runs/R-*.json | wc -l | tr -d ' ')" = "1" ] \
  && [ -f ".socom/runs/$RID1.json" ] \
  && ok "spawn id is content-addressed + idempotent (re-spawn resolves the same run)" \
  || bad "spawn id not idempotent ($(ls .socom/runs/R-*.json))"
[ ! -f .socom/ledger/runs.jsonl ] \
  && ok "spawn writes NO verdict (verify-never-claim: no ledger row)" \
  || bad "spawn wrote a ledger row (verdict boundary violated)"
"$SOCOM" spawn --seat builder --promise .socom/promises/spawn-p.xml --out /tmp/socom-spawn-outside >/dev/null 2>&1
check "spawn refuses --out outside the repo tree (containment)" 1 $?
[ ! -e /tmp/socom-spawn-outside ] && ok "spawn made no partial write outside the tree" \
                                  || { bad "spawn wrote outside the tree"; rm -rf /tmp/socom-spawn-outside; }
# --exec happy path: a stub `claude` on PATH; the record flips to running with a pid.
SPB="$T/spawnbin"; mkdir -p "$SPB"
printf '#!/bin/sh\nsleep 0.3\n' > "$SPB/claude"; chmod +x "$SPB/claude"
rm -rf .socom/runs
PATH="$SPB:$PATH" "$SOCOM" spawn --seat builder --promise .socom/promises/spawn-p.xml --exec >/dev/null 2>&1
check "spawn --exec launches (rc=0)" 0 $?
EJSON="$(ls .socom/runs/R-*.json 2>/dev/null | head -1)"
python3 -c "import json,sys; r=json.load(open(sys.argv[1])); sys.exit(0 if r['status']=='running' and isinstance(r['pid'],int) else 1)" "$EJSON" \
  && ok "spawn --exec record reads running with a live pid" \
  || bad "spawn --exec record wrong: $(cat "$EJSON" 2>&1)"
# --exec missing binary: keep python's dir on PATH, drop claude -> loud, no record.
rm -rf .socom/runs
PYDIR="$(dirname "$(command -v python3)")"; mkdir -p "$T/spawn-nobin"
PATH="$T/spawn-nobin:$PYDIR" "$SOCOM" spawn --seat builder --promise .socom/promises/spawn-p.xml --exec >/dev/null 2>&1
check "spawn --exec with the runtime binary absent RED (loud)" 1 $?
[ ! -f "$(ls .socom/runs/R-*.json 2>/dev/null | head -1)" ] \
  && ok "spawn --exec writes no running record when the binary is absent" \
  || bad "spawn --exec left a running record without launching"

# 14c. heuristic envelope (slice 3): spawn renders an "Operating envelope" brief
# section — earned domain lessons (ranked, lifecycle-honest) + doctrine devices +
# residuality stressors (on a residuality trigger) — appended but NOT hashed, so the
# run-id is idempotent on intent even as the lesson corpus grows. Default-on;
# --no-envelope suppresses. $R has canon (doctrine/residuality) from init.
rm -rf .socom/runs .socom/lessons
cat > .socom/promises/env-p.xml <<'EOF'
<promise id="P-ENVS" state="open" domain="cli"><promiser seat="builder" participant="x"/>
<intent><verbatim>make the ledger flock serialize concurrent writers</verbatim></intent>
<contract ref="C-ENVS" state="ratified"><goal>concurrent ledger writers never tear a row or duplicate an attempt</goal></contract></promise>
EOF
EID1="$("$SOCOM" spawn --seat builder --promise .socom/promises/env-p.xml | grep -o 'R-[0-9-]*-builder-[0-9a-f]*' | head -1)"
EB=".socom/runs/$EID1.brief.md"
grep -q "Operating envelope" "$EB" && ok "spawn brief carries the Operating envelope section (default-on)" \
                                   || bad "spawn brief lacks the Operating envelope"
grep -q "none on record yet" "$EB" && ok "envelope degrades loudly with no lessons (not a silent empty section)" \
                                   || bad "envelope did not degrade loudly"
grep -q "capability-ladder" "$EB" && ok "envelope lists doctrine thinking-devices (cited by id)" \
                                  || bad "envelope missing doctrine devices"
# an active cli-domain lesson now surfaces, and the run-id is UNCHANGED (core-only hash)
mkdir -p .socom/lessons
cat > .socom/lessons/L-ENVS.xml <<'EOF'
<lesson id="L-ENVS" domain="cli" state="active" source="cycle"><statement embed="true">concurrent ledger writers must hold an exclusive flock around read-compute-append or attempts duplicate and rows tear</statement></lesson>
EOF
EID2="$("$SOCOM" spawn --seat builder --promise .socom/promises/env-p.xml | grep -o 'R-[0-9-]*-builder-[0-9a-f]*' | head -1)"
grep -q "L-ENVS" ".socom/runs/$EID2.brief.md" \
  && ok "an active domain lesson surfaces in the envelope (ranked, cited by id)" \
  || bad "active lesson not injected into envelope"
[ "$EID1" = "$EID2" ] \
  && ok "a new lesson does NOT change the run-id (id hashes the stable core, not the envelope)" \
  || bad "run-id changed when the lesson corpus grew ($EID1 -> $EID2)"
# a retired lesson must never surface (lifecycle-honest)
printf '<lesson id="L-RET" domain="cli" state="retired" source="cycle"><statement embed="true">zzz retired concurrent flock guard</statement></lesson>' > .socom/lessons/L-RET.xml
"$SOCOM" spawn --seat builder --promise .socom/promises/env-p.xml >/dev/null
grep -rq "L-RET" .socom/runs/*.brief.md && bad "retired lesson surfaced in envelope (lifecycle filter)" \
                                        || ok "retired lessons never surface in the envelope (lifecycle-honest)"
# --no-envelope omits the section AND keeps the same id (core hash unchanged)
EID3="$("$SOCOM" spawn --seat builder --promise .socom/promises/env-p.xml --no-envelope | grep -o 'R-[0-9-]*-builder-[0-9a-f]*' | head -1)"
grep -q "Operating envelope" ".socom/runs/$EID3.brief.md" \
  && bad "--no-envelope still rendered the envelope" \
  || ok "--no-envelope omits the section"
[ "$EID3" = "$EID1" ] && ok "--no-envelope keeps the same run-id (advisory section is unhashed)" \
                      || bad "--no-envelope changed the run-id ($EID1 -> $EID3)"
# residuality stressors appear only on a residuality trigger
cat > .socom/promises/env-r.xml <<'EOF'
<promise id="P-ENVR" state="open" domain="cli"><promiser seat="builder" participant="x"/>
<intent><verbatim>this fix may relocate the residual stress rather than remove it</verbatim></intent>
<contract ref="C-ENVR" state="ratified"><goal>the stress is removed at source, not hidden</goal></contract></promise>
EOF
"$SOCOM" spawn --seat builder --promise .socom/promises/env-r.xml >/dev/null
grep -rq "relocate-not-remove" .socom/runs/*.brief.md \
  && ok "residuality stressors injected when a residuality contract applies" \
  || bad "residuality stressors missing on a residuality trigger"
rm -rf .socom/runs .socom/lessons .socom/promises/env-p.xml .socom/promises/env-r.xml
rm -rf .socom/runs .socom/ledger .socom/promises/spawn-p.xml

# 15. white-box unit tests on the pure core — complements the black-box checks
#     above. Chained here so every check that runs smoke (fast/medium/full + CI)
#     also pins the scoring/hash/regex/template contracts. ROOT is absolute, so
#     this tests the real bin/socom regardless of the temp working dir.
U="$(python3 "$ROOT/tests/unit.py" 2>&1)"; UR=$?
[ "$UR" = 0 ] && ok "unit: pure core ($(printf '%s' "$U" | tail -1))" \
             || { bad "unit tests on pure core"; printf '%s\n' "$U"; }

# 15b. orchestration end-to-end (Python harness): drives the real bin/socom
#      through spawn --exec -> kill -> monarch tally/reap -> session-start wiring,
#      in its own throwaway repos. Chained here so the full launch/supervise/reap
#      lifecycle is part of fast/medium/full + CI, not just a standalone tool.
E2E="$(python3 "$ROOT/tests/orchestration_e2e.py" 2>&1)"; E2ER=$?
[ "$E2ER" = 0 ] && ok "e2e: orchestration ($(printf '%s' "$E2E" | tail -1))" \
               || { bad "orchestration e2e (spawn+monarch lifecycle)"; printf '%s\n' "$E2E"; }

# 16. version — the build-identity command. The DIGEST is the contract, not the
#     version string: SOCOM_VERSION is a static "0.1" while `curl` of raw main
#     mints a new artifact on every merge, so only a hash of the running file can
#     answer "which build did this person run". An exposure result that cannot
#     name its build is not reproducible evidence. Assert the digest is not
#     decorative — it must equal a hash of bin/socom computed independently here.
"$SOCOM" version >/dev/null 2>&1; check "version: exits 0" 0 $?
"$SOCOM" version 2>/dev/null | grep -q '^socom '; check "version: reports the version line" 0 $?
V_REPORTED="$("$SOCOM" version 2>/dev/null | awk '/^build/{print $2}')"
V_ACTUAL="$(python3 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest()[:12])" "$SOCOM")"
[ -n "$V_REPORTED" ] && [ "$V_REPORTED" = "$V_ACTUAL" ]
check "version: build digest IS sha256(bin/socom)[:12] — identifies the artifact" 0 $?
"$SOCOM" version 2>/dev/null | grep -q '^source .*socom'; check "version: names the file it hashed" 0 $?

# 17. `<cmd> --help` EXPLAINS, it never ACTS (DEF-SUBCOMMAND-HELP-MUTATES-STATE-01).
#     No subcommand handled the flag, so it fell through as a positional and the
#     universal "explain, don't act" reflex made socom act: `claim --help` took a
#     real lease NAMED "--help", `compile --help` planted the full compiled view.
#     It fires AT first contact — `<cmd> --help` is what a stranger types at an
#     unfamiliar subcommand — so the acceptance is the whole surface, not a
#     sample: EVERY command in the table, both flags, in a pristine repo, must
#     exit 0 and leave the working tree byte-for-byte untouched.
HR="$T/help-repo"; mkdir -p "$HR"; ( cd "$HR" && git init -q -b main . )
HELP_CMDS="$("$SOCOM" --help 2>&1 | sed -n '/^Commands:/,/^$/p' \
             | grep -E '^  [^ ]' | awk '{print $1}')"
HELP_N="$(printf '%s\n' "$HELP_CMDS" | wc -l | tr -d ' ')"
[ "$HELP_N" -ge 40 ]
check "help: the command table parses (${HELP_N} commands swept x2 flags)" 0 $?
HELP_BAD=""
for c in $HELP_CMDS; do
  for f in --help -h; do
    ( cd "$HR" && "$SOCOM" "$c" "$f" ) >/dev/null 2>&1 \
      || HELP_BAD="$HELP_BAD $c/$f"
  done
done
[ -z "$HELP_BAD" ]
check "help: every <cmd> --help and -h exits 0${HELP_BAD:+ (non-zero:$HELP_BAD)}" 0 $?
# The load-bearing half: asking what a command does must write NOTHING — no
# planted file, no lease, no git config, no ref. Pre-fix this printed 10
# untracked entries and a live lease.
HELP_DIRT="$( cd "$HR" && git status --porcelain )"
[ -z "$HELP_DIRT" ]
check "help: 80 help requests wrote NOTHING (git status clean)" 0 $?
[ -z "$HELP_DIRT" ] || printf '%s\n' "$HELP_DIRT" | sed 's/^/      /'
( cd "$HR" && "$SOCOM" claim --scan 2>&1 ) | grep -q '^socom claim: 0 live lease'
check "help: ...and took NO lease (claim --help is not a claim)" 0 $?
( cd "$HR" && git config --get-regexp 'socom|hooksPath' ) >/dev/null 2>&1
check "help: ...and wrote no git config" 1 $?
[ "$( cd "$HR" && git for-each-ref refs/socom | wc -l | tr -d ' ')" = 0 ]
check "help: ...and published no ref" 0 $?
# Usage is DERIVED from the one command table, so it cannot drift from it.
( cd "$HR" && "$SOCOM" claim --help ) | grep -q 'claim PATHS before you touch them'
check "help: prints THAT subcommand's entry, not the whole command list" 0 $?

rm -rf "$T"
if [ "$FAIL" -gt 0 ]; then echo "smoke: $FAIL FAILURE(S)"; exit 1; fi
echo "smoke: all checks passed"
