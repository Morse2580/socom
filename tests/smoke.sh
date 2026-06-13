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

rm -rf "$T"
if [ "$FAIL" -gt 0 ]; then echo "smoke: $FAIL FAILURE(S)"; exit 1; fi
echo "smoke: all checks passed"
