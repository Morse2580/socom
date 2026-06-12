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

# 6. redaction (HR6)
cat > .socom/memory/memories/leaky.md <<EOF
a memory containing password = supersecret123 which must not travel
EOF
"$SOCOM" hydrate . 2>&1 | grep -q "REFUSED leaky" && ok "hydrate refuses secrets (HR6)" \
                                                  || bad "hydrate leaked a secret (HR6)"
cat > .socom/promises/leak.xml <<EOF
<promise socom="0.1" id="x"><goal embed="true">token = abcd1234efgh5678</goal></promise>
EOF
"$SOCOM" index . 2>&1 | grep -q "REDACTED" && ok "index redacts secrets (HR6)" \
                                           || bad "index embedded a secret (HR6)"

rm -rf "$T"
if [ "$FAIL" -gt 0 ]; then echo "smoke: $FAIL FAILURE(S)"; exit 1; fi
echo "smoke: all checks passed"
