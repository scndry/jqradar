#!/bin/sh
# 한 명령으로 도는 전부. **"돌린다"가 여러 명령이면 하나는 빠진다.**
#
#   sh ci/check-all.sh                       # 전부
#   sh ci/check-all.sh contracts             # contract/*/compute.py --check 여섯
#   sh ci/check-all.sh landing               # 결정 착지 (자기 반례 먼저)
#   sh ci/check-all.sh review-entry          # 검토 입구의 자기 반례
#   sh ci/check-all.sh fixture-change [base] [head]
#
# 왜 있는가: PR #11과 PR #17에서 **같은 자리**가 두 번 비었다 — §7 예시가 얻은 필드를
# `schemas/`가 몰라 적합성 스위트가 빨갛게 됐는데, 둘 다 착지·반례·입구 셋만 돌리고
# 전 스위트를 빼먹었다. 두 세션이 같은 실패를 했으면 그것은 주의력이 아니라 구조의
# 문제다. 목록은 여기 한 곳에만 둔다 — CI 잡도, 세션 종료 체크(CLAUDE.md §6)도,
# 소유자 프롬프트도 이 한 명령을 가리킨다.
#
# 빌드(Gradle·ArchUnit)는 여기 없다 — JDK가 필요하고 목적이 다르다. `contract.yml`의
# 별도 잡이 진다.

set -eu
cd "$(dirname "$0")/.."

PY=${PYTHON:-python3}
fail=0
section=${1:-all}

run() {  # run <이름> <명령...>
  name=$1; shift
  printf '\n── %s\n' "$name"
  if "$@"; then
    return 0
  else
    printf '   ^^ 실패: %s\n' "$name"
    fail=1
  fi
}

if [ "$section" = all ] || [ "$section" = contracts ]; then
  # §2.9 적합성 스위트. 하나라도 빠지면 계약이 아니라 일부 계약이다.
  for c in percentile cpd graph history reproducibility schema; do
    run "계약 $c" "$PY" "contract/$c/compute.py" --check
  done
fi

if [ "$section" = all ] || [ "$section" = landing ]; then
  # 반례를 먼저 돌린다 — 반례가 깨진 검사는 통과만 시킨다(D131).
  run "결정 착지 — 자기 반례" sh ci/check-decision-landing.sh --selftest
  run "결정 착지 — prd.md"    sh ci/check-decision-landing.sh prd.md
fi

if [ "$section" = all ] || [ "$section" = review-entry ]; then
  run "검토 입구 — 자기 반례" "$PY" docs/review/g0-review.py --selftest
fi

if [ "$section" = all ] || [ "$section" = fixture-change ]; then
  # 커밋 범위가 있을 때만. 로컬 기본은 main..HEAD.
  base=${2:-main}; head=${3:-HEAD}
  if git rev-parse --verify -q "$base" >/dev/null 2>&1; then
    run "fixture_change 가드 ($base..$head)" sh ci/check-fixture-change.sh "$base" "$head"
  else
    printf '\n── fixture_change 가드\n   건너뜀: %s 를 찾을 수 없다\n' "$base"
  fi
fi

printf '\n'
if [ "$fail" -eq 0 ]; then
  echo "전부 통과 — ci/check-all.sh ($section)"
else
  echo "실패가 있다 — ci/check-all.sh ($section)"
fi
exit "$fail"
