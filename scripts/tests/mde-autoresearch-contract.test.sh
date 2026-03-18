#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEAM_FILE="$ROOT_DIR/configs/agent-teams/mde-autoresearch-team.yaml"
RUNNER_FILE="$ROOT_DIR/scripts/teams/run-mde-autoresearch-team.sh"
VALIDATOR_FILE="$ROOT_DIR/scripts/teams/validate-mde-autoresearch-output.sh"
AGENT_RUNNER_FILE="$ROOT_DIR/scripts/agent-runner.sh"
PROMPT_DIR="$ROOT_DIR/prompts/agent-team/mde-autoresearch"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

subagent_count="$(rg -c '^  - id:' "$TEAM_FILE")"
if [[ "$subagent_count" == '12' ]]; then
  pass 'autoresearch team defines the required 12 subagents'
else
  fail "expected 12 autoresearch subagents (got $subagent_count)"
fi

runtime_contract_mentions="$(rg -c 'skills/mde-agent-runtime-contract' "$TEAM_FILE")"
if [[ "$runtime_contract_mentions" -ge 12 ]]; then
  pass 'every autoresearch subagent requires the runtime contract skill'
else
  fail "expected runtime contract on each autoresearch subagent (count=$runtime_contract_mentions)"
fi

if rg -q 'mde-agent-preflight.sh' "$RUNNER_FILE" && rg -q 'mde_prepare_guard_dir' "$RUNNER_FILE"; then
  pass 'autoresearch runner enforces preflight and command guard setup'
else
  fail 'expected autoresearch runner to set up preflight and guardrails'
fi

if rg -q 'configs/mde-domain-catalog\.json' "$RUNNER_FILE" && \
   rg -q 'configs/mde-reference-sources\.json' "$RUNNER_FILE" && \
   rg -q 'configs/mde-preset-catalog\.json' "$RUNNER_FILE" && \
   rg -q 'configs/mde-learning-registry\.json' "$RUNNER_FILE"; then
  pass 'autoresearch runner references domain, reference, preset, and learning catalogs'
else
  fail 'expected autoresearch runner to reference all domain-team catalog inputs'
fi

if rg -q 'domain classification' "$RUNNER_FILE" && rg -q 'delegate' "$RUNNER_FILE"; then
  pass 'autoresearch runner requires domain classification and delegation markers'
else
  fail 'expected autoresearch runner to mention domain classification and delegation'
fi

if rg -q 'discovery-records\.jsonl' "$RUNNER_FILE" && \
   rg -q 'pattern-records\.jsonl' "$RUNNER_FILE" && \
   rg -q 'social-pattern-records\.jsonl' "$RUNNER_FILE" && \
   rg -q 'acceptance-records\.jsonl' "$RUNNER_FILE" && \
   rg -q 'decision-records\.jsonl' "$RUNNER_FILE" && \
   rg -q 'summary\.md' "$RUNNER_FILE"; then
  pass 'autoresearch runner requires the multi-file evidence outputs from team config'
else
  fail 'expected autoresearch runner to require jsonl and summary outputs'
fi

if rg -q 'domain classification' "$VALIDATOR_FILE" && \
   rg -q 'delegat' "$VALIDATOR_FILE" && \
   rg -q 'preset' "$VALIDATOR_FILE" && \
   rg -q 'learning registry' "$VALIDATOR_FILE"; then
  pass 'autoresearch validator enforces domain delegation and preset/learning markers'
else
  fail 'expected autoresearch validator to enforce domain delegation and preset/learning markers'
fi

if rg -q 'configs/mde-domain-catalog\.json' "$AGENT_RUNNER_FILE" && \
   rg -q 'configs/mde-reference-sources\.json' "$AGENT_RUNNER_FILE" && \
   rg -q 'configs/mde-preset-catalog\.json' "$AGENT_RUNNER_FILE" && \
   rg -q 'configs/mde-learning-registry\.json' "$AGENT_RUNNER_FILE"; then
  pass 'shared agent runner injects the new domain-team catalog contract'
else
  fail 'expected shared agent runner to inject new domain-team catalog contract'
fi

prompt_fail=0
while IFS= read -r prompt_file; do
  if rg -q 'skills/mde-agent-runtime-contract' "$prompt_file"; then
    :
  else
    printf 'missing runtime contract reference: %s\n' "$prompt_file" >&2
    prompt_fail=1
  fi
done < <(find "$PROMPT_DIR" -maxdepth 1 -type f -name '*.md' | sort)

if (( prompt_fail == 0 )); then
  pass 'all autoresearch prompts reference the runtime contract skill'
else
  fail 'one or more autoresearch prompts are missing the runtime contract skill reference'
fi

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
