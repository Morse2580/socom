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

# 6. claims (R2) + reaper (R12)
cd "$R"
export SOCOM_SESSION="smoke-a"
"$SOCOM" claim core >/dev/null;            check "claim acquire" 0 $?
"$SOCOM" claim core >/dev/null;            check "re-claim by same holder ok" 0 $?
SOCOM_SESSION="smoke-b" "$SOCOM" claim core >/dev/null 2>&1; check "claim held by other RED" 1 $?
"$SOCOM" claim nosuch >/dev/null 2>&1;     check "claim unknown domain RED" 1 $?
"$SOCOM" claim --scan | grep -q "1 live" && ok "claim --scan sees live claim" \
                                         || bad "claim --scan missed live claim"
# expire it: backdate the timestamp, reaper must remove it
python3 - <<EOF
from pathlib import Path
p = Path(".socom/claims/core.claim"); ts, rest = p.read_text().split("\t", 1)
p.write_text("2020-01-01T00:00:00+00:00\t" + rest)
EOF
"$SOCOM" gate session-start 2>/dev/null | grep -q "reaped expired claim: core" \
  && ok "reaper removes expired claim (R12)" || bad "reaper did not reap (R12)"
"$SOCOM" claim core >/dev/null && "$SOCOM" release core >/dev/null
check "release" 0 $?

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

# 15. white-box unit tests on the pure core — complements the black-box checks
#     above. Chained here so every check that runs smoke (fast/medium/full + CI)
#     also pins the scoring/hash/regex/template contracts. ROOT is absolute, so
#     this tests the real bin/socom regardless of the temp working dir.
U="$(python3 "$ROOT/tests/unit.py" 2>&1)"; UR=$?
[ "$UR" = 0 ] && ok "unit: pure core ($(printf '%s' "$U" | tail -1))" \
             || { bad "unit tests on pure core"; printf '%s\n' "$U"; }

rm -rf "$T"
if [ "$FAIL" -gt 0 ]; then echo "smoke: $FAIL FAILURE(S)"; exit 1; fi
echo "smoke: all checks passed"
