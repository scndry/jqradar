#!/bin/sh
# D139 — 결정이 §10에만 적히고 **본문이 따라오지 않은 것**을 기계가 잡는다.
#
#   sh ci/check-decision-landing.sh [prd.md]
#   sh ci/check-decision-landing.sh --selftest
#
# 이 리포가 반복해 온 실패 모드다(문서 규칙 2): 결정을 §10에 적고 본문을 안 고친다.
# v3.7.7이 일곱 건, v3.8.0이 넷, v3.8.2가 `∩ W`를 그렇게 놓쳤다. 사람이 잡았고,
# 사람이 잡으면 다음에도 놓친다.
#
# 규칙(D139): `- D<n> [§a.b, §c.d] 결정 문장.` 대괄호가 이 결정이 **바꾼 본문의 절**이다.
# 그 절 본문에 `D<n>`이 인용되어 있어야 한다. D1–D138은 소급하지 않는다 —
# 138개를 손으로 재작성하는 것 자체가 오류원이다(§0-22).
#
# **절 단위로 본다.** 파일 전체 `grep`은 다른 절의 우연한 일치를 통과로 센다 —
# v3.8.2의 `∩ W` 확인이 `'90일 ∩ 창'` 부분 문자열로 §5.5에서 맞아 거짓 통과한 것이
# 그 사례다(docs/status.md 사고 기록).
#
# **결정 자신의 줄은 착지로 세지 않는다.** 그러면 §10에 적은 것이 §10에 착지했다는
# 동어반복이 되고, 검사가 아무것도 막지 않는다.
#
# **취소선 항목(`- ~~D<n> …~~`)은 보지 않는다.** 취소된 결정은 착지할 본문이 없다
# (CLAUDE.md §5: 기존 결정은 지우지 않고 취소선 + 대체 참조). 실제 prd.md의 D73이
# 그 자리다 — 우연이 아니라 의도라는 것을 반례 08이 못 박는다.
#
# 검사도 틀릴 수 있으므로 자기 반례를 함께 둔다(`--selftest`, D131·§0-22):
# 있는 착지를 없다고 하지 않는가, 없는 착지를 있다고 하지 않는가.

set -eu

FIRST_STRUCTURED=139   # 이 번호부터 대괄호가 필수다(D139, 소급 없음)

check_file() {
  awk -v first="$FIRST_STRUCTURED" '
    { line[NR] = $0 }

    # 헤딩 수집: "## 10. ..." -> id 10, level 2 / "### 2.8 ..." -> id 2.8, level 3
    /^#+ [0-9]/ {
      lvl = index($0, " ") - 1
      id = $2
      sub(/\.$/, "", id)            # "10." -> "10"
      hline[++hn] = NR; hlevel[hn] = lvl; hid[hn] = id
    }
    END {
      bad = 0; checked = 0; skipped = 0
      for (n = 1; n <= NR; n++) {
        if (line[n] !~ /^- D[0-9]+ /) continue
        num = line[n]; sub(/^- D/, "", num); sub(/ .*/, "", num)

        # 대괄호 절 목록
        if (match(line[n], /^- D[0-9]+ \[§[^]]*\]/)) {
          secs = substr(line[n], RSTART, RLENGTH)
          sub(/^- D[0-9]+ \[/, "", secs); sub(/\]$/, "", secs)
        } else {
          if (num + 0 >= first) {
            printf "  FAIL  D%s: 형식이 없다 — `- D%s [§a.b] …`로 바꾼 절을 적어라 (D139)\n", num, num
            bad++
          } else skipped++
          continue
        }

        cnt = split(secs, arr, /, */)
        for (i = 1; i <= cnt; i++) {
          sec = arr[i]; sub(/^§/, "", sec)
          # 절 본문 범위: 헤딩 다음 줄부터, 같거나 상위 레벨 헤딩 직전까지.
          # awk 범위 패턴(/시작/,/종료/)을 쓰지 않는다 — 시작 줄이 종료 패턴에도
          # 맞으면 한 줄에서 끝나 언제나 0건을 낸다(docs/status.md 사고 기록).
          start = 0
          for (h = 1; h <= hn; h++) if (hid[h] == sec) { start = h; break }
          if (start == 0) {
            printf "  FAIL  D%s: §%s 절이 없다\n", num, sec
            bad++; continue
          }
          from = hline[start] + 1; to = NR
          for (h = start + 1; h <= hn; h++)
            if (hlevel[h] <= hlevel[start]) { to = hline[h] - 1; break }

          found = 0
          for (j = from; j <= to; j++) {
            if (j == n) continue                       # 결정 자신의 줄은 세지 않는다
            if (line[j] ~ ("(^|[^A-Za-z0-9])D" num "([^0-9]|$)")) { found = 1; break }
          }
          checked++
          if (!found) {
            printf "  FAIL  D%s: §%s 본문(%d–%d행)이 D%s를 인용하지 않는다 — 결정이 §10에만 있다\n", \
                   num, sec, from, to, num
            bad++
          }
        }
      }
      printf "  검사한 (결정,절) 쌍 %d · 소급하지 않은 항목 %d\n", checked, skipped
      exit (bad > 0)
    }
  ' "$1"
}

selftest() {
  dir=$(dirname "$0")/decision-landing-cases
  rc=0
  for case_file in "$dir"/*.md; do
    # BRE의 \| 는 이식성이 없다(BSD sed가 안 받는다) — awk로 읽는다.
    want=$(head -1 "$case_file" | awk '{print $3}')
    why=$(head -1 "$case_file" | sed -e 's/^<!-- expect: [a-z]* //' -e 's/ -->$//')
    if check_file "$case_file" >/dev/null 2>&1; then got=pass; else got=fail; fi
    if [ "$got" = "$want" ]; then
      printf "  ok    %-34s %s=%s  (%s)\n" "$(basename "$case_file")" "기대" "$want" "$why"
    else
      printf "  FAIL  %-34s 기대=%s 실제=%s  (%s)\n" "$(basename "$case_file")" "$want" "$got" "$why"
      rc=1
    fi
  done
  return $rc
}

if [ "${1:-}" = "--selftest" ]; then
  echo "자기 반례 — 검사가 무는지, 물지 말아야 할 것을 물지 않는지:"
  selftest
else
  prd=${1:-prd.md}
  echo "결정 착지 검사 (D139) — $prd"
  check_file "$prd"
fi
