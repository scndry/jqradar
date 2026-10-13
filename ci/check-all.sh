#!/bin/sh
# 한 명령으로 도는 전부. **"돌린다"가 여러 명령이면 하나는 빠진다.**
#
#   sh ci/check-all.sh                       # 전부
#   sh ci/check-all.sh contracts             # contract/*/compute.py --check 여섯
#   sh ci/check-all.sh landing               # 결정 착지·reproduce 표시·§2.9 케이스 이름 (자기 반례 먼저)
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
  # D158·D186 — §7 reproduce 블록의 모든 줄에 종류 표시. 반례 먼저.
  run "reproduce 종류 표시 — 자기 반례" sh ci/check-reproduce-kinds.sh --selftest
  run "§2.8 (i) ↔ id 스펙 — 자기 반례" "$PY" contract/reproducibility/compute.py --selftest
  run "reproduce 종류 표시 — prd.md"    sh ci/check-reproduce-kinds.sh prd.md
  # D236 — §2.9 G0 행이 이름으로 가리키는 케이스가 디렉터리로 있는가. 가리키는 쪽을 택한 이상
  # 가리킴이 끊기는 것을 잡는 장치가 함께 있어야 한다. 반례 먼저.
  run "§2.9 케이스 이름 — 자기 반례" "$PY" ci/check-case-names.py --selftest
  run "§2.9 케이스 이름 — prd.md"    "$PY" ci/check-case-names.py prd.md
fi

if [ "$section" = all ] || [ "$section" = review-entry ]; then
  run "검토 입구 — 자기 반례" "$PY" docs/review/g0-review.py --selftest
  # D266·D267(옛 D152) — 게이트별 목록은 기록에서 생성한다. 사람이 옮기는 목록을 하나 없앤다.
  run "게이트별 목록 — 생성기와 diff 0" "$PY" docs/review/g0-review.py --gate-lists --check
  # D265 — 반례는 리포에 실행 가능한 것이다. 열린 반례가 아직 재현되는가(값이 갈리는가).
  run "반례 — 재현" "$PY" docs/review/g0-review.py --counterexamples
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
