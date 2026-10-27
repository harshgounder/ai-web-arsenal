#!/usr/bin/env bash
# gate.sh: every check this repo has, in one command.
#
# A phase is done when this exits 0. Not when the prose says so.
#   ./scripts/gate.sh          offline gates, about a minute
#   ./scripts/gate.sh --full   adds the network stage and the determinism rebuild, a few minutes
#
# Exit codes: 0 all gates passed, 1 a gate failed, 2 a gate could not run.

set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

FULL=0
[ "${1:-}" = "--full" ] && FULL=1

PASS=0
FAIL=0
SKIP=0
declare -a RESULTS

run_gate() {
  local name="$1"; shift
  local out rc
  out=$("$@" 2>&1)
  rc=$?
  if [ $rc -eq 3 ]; then
    # exit 3 means "could not run here", which is not the same as failed. It is still reported.
    SKIP=$((SKIP + 1))
    RESULTS+=("SKIP  $name")
    printf '\n----- %s skipped -----\n%s\n' "$name" "$(printf '%s' "$out" | tail -6)"
  elif [ $rc -eq 0 ]; then
    PASS=$((PASS + 1))
    RESULTS+=("PASS  $name")
  else
    FAIL=$((FAIL + 1))
    RESULTS+=("FAIL  $name")
    printf '\n----- %s -----\n%s\n' "$name" "$(printf '%s' "$out" | tail -25)"
  fi
}

echo "ai-web-arsenal gate"
echo "==================="

if [ $FULL -eq 1 ]; then
  run_gate "install matrix is live" python3 scripts/verify-tools.py
fi

run_gate "doc numbers match disk"   python3 scripts/recheck.py
run_gate "prose claims hold"        python3 scripts/check-claims.py
run_gate "regression tests"         python3 scripts/test-regressions.py
run_gate "rea operations"           python3 rea-ops/test-ops.py
run_gate "mcp server answers"       python3 mcps/test-mcp.py
run_gate "playbooks reference real entries" python3 scripts/render-playbooks.py --check
run_gate "counters cover every class"   python3 scripts/render-counters.py --check
run_gate "mutation candidates are sound" python3 scripts/generate-mutations.py --check
run_gate "capability candidates are sound" python3 scripts/mine-capability.py --check
run_gate "domain invariants"        python3 scripts/validate-domains.py

if [ -d ../web-attack-atlas ]; then
  ( cd ../web-attack-atlas && python3 scripts/render-patterns.py --check >/dev/null 2>&1 )
  if [ $? -eq 0 ]; then
    PASS=$((PASS + 1)); RESULTS+=("PASS  atlas pattern gate")
  else
    FAIL=$((FAIL + 1)); RESULTS+=("FAIL  atlas pattern gate")
  fi
fi

if [ $FULL -eq 1 ]; then
  run_gate "generators are deterministic" python3 scripts/check-determinism.py
  run_gate "denominator is complete"      python3 scripts/validate-denominator.py
  run_gate "coverage ledger is sound"     python3 scripts/coverage.py --validate
  run_gate "gap is fully classified"      python3 scripts/classify-gap.py --validate
  run_gate "observations replay"          python3 scripts/observe.py --verify
fi

echo
for r in "${RESULTS[@]}"; do echo "  $r"; done
echo
echo "gates: $((PASS + FAIL + SKIP))  pass $PASS  fail $FAIL  skip $SKIP"

if [ $FAIL -ne 0 ]; then
  echo
  echo "A failed gate is a false statement in the repository. Do not proceed to the next phase."
  exit 1
fi
if [ $SKIP -ne 0 ]; then
  echo
  echo "Skipped gates could not run here. That is not the same as passing: it means part of this repo"
  echo "was not checked. The usual cause is a missing companion repo."
  if [ "$STRICT" = "1" ]; then
    echo
    echo "STRICT is set, so a skipped gate is a failure here."
    exit 2
  fi
  echo
  echo "Exiting 0 because STRICT is not set. A caller that needs completeness must set STRICT=1 or read"
  echo "the skip count above; the exit status alone does not distinguish a full run from a partial one."
  exit 0
fi
exit 0
