#!/bin/sh
# G0 체크리스트 #6 — `expected.json`을 바꾼 **커밋**은 `fixture_change` 레코드를
# 같은 커밋에 동반해야 한다 (§2.9, D129).
#
#   sh ci/check-fixture-change.sh <base-ref> <head-ref>
#
# **커밋 단위**로 본다. §2.9는 "기대값을 바꾸는 커밋은 ... 반드시 동반한다"이고
# D129가 자리를 파일로 못 박았다. PR 범위 전체로 보면 다른 커밋에 끼워 넣은 레코드가
# 통과하고, 그러면 "어느 변경이 왜 일어났는지"가 커밋에서 끊긴다.
#
# 막으려는 것: 회귀 테스트가 "새 정답을 손으로 승인하는 테스트"로 변질되는 것(P11).

set -eu
base=${1:?base ref}
head=${2:?head ref}

fail=0
for sha in $(git rev-list --reverse --no-merges "$base..$head"); do
  changed=$(git show --pretty=format: --name-only "$sha" | grep -v '^$' || true)
  touches_expected=$(printf '%s\n' "$changed" | grep -E '^contract/.*/expected\.json$' || true)
  [ -z "$touches_expected" ] && continue

  record=$(printf '%s\n' "$changed" | grep -E '^contract/fixture-changes/.*\.json$' || true)
  subject=$(git log -1 --format=%s "$sha")
  if [ -z "$record" ]; then
    fail=1
    echo "FAIL  $(git rev-parse --short "$sha")  $subject"
    echo "      expected.json을 바꿨는데 같은 커밋에 fixture_change 레코드가 없다:"
    printf '%s\n' "$touches_expected" | sed 's/^/        /'
    echo "      §2.9·D129 — contract/fixture-changes/<날짜>-<슬러그>.json 을 같은 커밋에."
    echo "      reason ∈ {library_behavior_change, contract_change, bug_fix}"
  else
    echo "ok    $(git rev-parse --short "$sha")  $subject"
    printf '%s\n' "$record" | sed 's/^/        + /'
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "expected.json을 바꾼 커밋이 전부 fixture_change를 동반한다."
fi
exit "$fail"
