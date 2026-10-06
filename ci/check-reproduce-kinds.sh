#!/bin/sh
# D158·D186 — §7 `reproduce` 블록의 **모든 줄**에 종류 표시([id]·[fn]·[x])가 있는가.
#
#   sh ci/check-reproduce-kinds.sh [prd.md]
#   sh ci/check-reproduce-kinds.sh --selftest
#
# §2.8: reproduce의 필드는 세 종류뿐이고 §7 예시의 주석이 그것을 표시한다. 표시 없는 필드가
# 넷째 종류다(id 입력도 함수도 아닌데 비교되는 값) — 3차 T8이 그런 값을 넷 찾았고(창 파라미터·
# git_version·k·인코딩) 전부 표시가 없는 줄에 있었다. 사람이 붙이면 객체의 첫 줄에만 붙이고
# 연속 줄을 빠뜨린다(v3.10.1 첫 검산에서 `parameters`·`percentile_method`의 연속 줄 셋이 비어
# 있었다) — 그래서 **객체 단위가 아니라 줄 단위**로 본다: `"키":`가 있는 줄마다 표시가 있어야 한다.
# 닫는 괄호만 있는 줄은 보지 않는다.
#
# 검사도 틀릴 수 있으므로 자기 반례를 둔다(--selftest, D131).

set -eu

check_file() {
  awk '
    /"reproduce": \{/ && !started { started = 1; depth = 0 }
    started {
      line = $0
      # 주석 뒤는 표시만 본다 — 키 검출은 주석 앞 부분으로
      code = line; sub(/\/\/.*$/, "", code)
      mark = (line ~ /\[id\]/ || line ~ /\[fn\]/ || line ~ /\[x\]/)
      # 키가 있는 줄인가 ("name": …)
      if (code ~ /"[A-Za-z_.]+"[ ]*:/ && !(line ~ /"reproduce": \{/)) {
        if (!mark) { printf("  FAIL  %d행: 종류 표시 없음 — %s\n", NR, substr(code, 1, 90)); bad++ }
      }
      # 깊이 추적
      n = gsub(/\{/, "{", code); m = gsub(/\}/, "}", code)
      depth += n - m
      if (depth <= 0 && NR > 1 && !(line ~ /"reproduce": \{/)) { exit (bad ? 1 : 0) }
    }
    END { if (!started) { print "  FAIL  reproduce 블록을 찾지 못했다"; exit 1 } exit (bad ? 1 : 0) }
  ' "$1"
}

if [ "${1:-}" = "--selftest" ]; then
  fail=0
  for f in "$(dirname "$0")"/reproduce-kinds-cases/*.md; do
    expect=$(head -1 "$f" | sed -n 's/.*expect: \([a-z]*\).*/\1/p')
    why=$(head -1 "$f" | sed -n 's/.*expect: [a-z]* \(.*\) -->/\1/p')
    if check_file "$f" >/dev/null 2>&1; then got=pass; else got=fail; fi
    if [ "$got" = "$expect" ]; then printf '  ok    %-36s 기대=%s  (%s)\n' "$(basename "$f")" "$expect" "$why"
    else printf '  BAD   %-36s 기대=%s 결과=%s  (%s)\n' "$(basename "$f")" "$expect" "$got" "$why"; fail=1; fi
  done
  exit $fail
fi

file=${1:-prd.md}
if check_file "$file"; then echo "reproduce 종류 표시 (D158·D186) — $file: 모든 줄에 표시"; else echo "reproduce 종류 표시 — 표시 없는 줄이 있다"; exit 1; fi
