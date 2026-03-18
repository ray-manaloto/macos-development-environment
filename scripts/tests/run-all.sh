#!/usr/bin/env bash
set -euo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MDE_TEST_PROFILE="${MDE_TEST_PROFILE:-ci}" # ci|host|all
MDE_TEST_TIMEOUT_SECS="${MDE_TEST_TIMEOUT_SECS:-120}"

PASS=0
FAIL=0
SKIP=0

should_skip() {
  local name="$1"
  case "$MDE_TEST_PROFILE" in
    ci)
      case "$name" in
        alias-resolution.test.sh|template-sync.test.sh|tool-precedence.test.sh|drift-remediation-transition.test.sh|profile-zsh-startup.test.sh)
          return 0
          ;;
      esac
      ;;
    host|all)
      ;;
    *)
      echo "Unknown MDE_TEST_PROFILE: $MDE_TEST_PROFILE" >&2
      exit 1
      ;;
  esac
  return 1
}

run_with_timeout() {
  local secs="$1"
  shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "$secs" "$@"
    return
  fi
  if command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$secs" "$@"
    return
  fi
  "$@"
}

while IFS= read -r test_file; do
  local_name="$(basename "$test_file")"
  [[ "$local_name" == "run-all.sh" ]] && continue

  if should_skip "$local_name"; then
    echo "Skipping $local_name (profile=$MDE_TEST_PROFILE)"
    SKIP=$((SKIP + 1))
    echo
    continue
  fi

  echo "Running $local_name"
  if run_with_timeout "$MDE_TEST_TIMEOUT_SECS" bash "$test_file"; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
  fi
  echo
done < <(LC_ALL=C find "$TEST_DIR" -maxdepth 1 -type f -name '*.test.sh' | LC_ALL=C sort)

echo "Test suites: $PASS passed, $FAIL failed, $SKIP skipped (profile=$MDE_TEST_PROFILE)"
(( FAIL == 0 ))
