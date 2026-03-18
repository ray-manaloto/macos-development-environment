#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNNER_FILE="$ROOT_DIR/scripts/agent-runner.sh"
DOMAIN_RUNNER_FILE="$ROOT_DIR/scripts/teams/run-mde-domain-team.sh"
POLICY_FILE="$ROOT_DIR/scripts/lib/mde-agent-policy.sh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

if rg -q 'REQUESTED_OUTPUTS=\(\)' "$RUNNER_FILE" && \
   rg -q "sed -n 's/\^Output file: //p'" "$RUNNER_FILE"; then
  pass 'agent runner collects all declared output files'
else
  fail 'agent runner does not collect all declared output files'
fi

if ! rg -q "sed -n 's/\^Output file: //p'.*head -n1|head -n1.*sed -n 's/\^Output file: //p'" "$RUNNER_FILE"; then
  pass 'agent runner no longer truncates output-file parsing to a single line'
else
  fail 'agent runner still truncates output-file parsing to a single line'
fi

if rg -q 'output_matches_dir' "$RUNNER_FILE" && \
   rg -q 'required_outputs_for_subagent' "$RUNNER_FILE"; then
  pass 'agent runner scopes default output expansion by output directory'
else
  fail 'agent runner is missing scoped default output expansion logic'
fi

if rg -q 'configs/mde-domain-catalog\.json' "$RUNNER_FILE" && \
   rg -q 'configs/mde-reference-sources\.json' "$RUNNER_FILE" && \
   rg -q 'configs/mde-preset-catalog\.json' "$RUNNER_FILE" && \
   rg -q 'configs/mde-learning-registry\.json' "$RUNNER_FILE" && \
   rg -q 'domain classification' "$RUNNER_FILE" && \
   rg -q 'delegat' "$RUNNER_FILE"; then
  pass 'agent runner injects the domain-team contract and delegation markers'
else
  fail 'agent runner is missing domain-team contract or delegation markers'
fi

if rg -q 'MDE_AGENT_RUNNER_MODE' "$RUNNER_FILE" && \
   rg -q 'local-synth' "$RUNNER_FILE"; then
  pass 'agent runner keeps local-synth behind an explicit opt-in'
else
  fail 'agent runner is missing the explicit local-synth opt-in gate'
fi

if ! grep -Fq 'MDE_AGENT_RUNNER_MODE="${MDE_AGENT_RUNNER_MODE:-local-synth}"' "$DOMAIN_RUNNER_FILE"; then
  pass 'domain team runner does not force local-synth mode by default'
else
  fail 'domain team runner still forces local-synth mode by default'
fi

if rg -q 'if \[\[ -n "\$dir" && -d "\$dir" \]\]' "$POLICY_FILE" && \
   rg -q 'ln -sfn "\$wrapper" "\$dir/\$cmd"' "$POLICY_FILE"; then
  pass 'guard-dir policy reuses existing directories and refreshes guard symlinks safely'
else
  fail 'guard-dir policy is missing reuse or safe symlink refresh behavior'
fi

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
