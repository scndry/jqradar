#!/bin/sh
# docs/battery.md의 숫자를 다시 만드는 스크립트 (B.4 — 다시 계산할 수 없는 숫자는 의견이다).
#
#   sh docs/battery-measure.sh > /tmp/battery.tsv
#
# GitHub API만 쓴다(clone 없음). 그래서 `loc`은 여기서 나오지 않는다 —
# §2.1의 `loc`은 NCSS이고 PMD만 계산할 수 있다. 여기 나오는 것은 Java 바이트이며
# 배터리 실행 시점에 도구가 실제 `loc`을 낸다.
#
# 머지 비율은 최근 100커밋 표본이다. 리포 전체가 아니다 — 정책이 바뀐 리포는
# 옛 구간이 다를 수 있고, 그것이 P2가 보려는 것이기도 하다.

set -e
printf 'repo\tcreated\tbuild\tcommits\tmerges_in_100\tjava_KB\tkotlin_KB\n'
for r in "$@"; do
  b=$(gh api "repos/$r" -q .default_branch)
  created=$(gh api "repos/$r" -q .created_at | cut -c1-10)
  files=$(gh api "repos/$r/contents?ref=$b" -q '[.[].name]|join(" ")')
  case "$files" in
    *build.gradle.kts*) build="Gradle(kts)" ;;
    *build.gradle*)     build="Gradle" ;;
    *pom.xml*)          build="Maven" ;;
    *)                  build="?" ;;
  esac
  commits=$(gh api -i "repos/$r/commits?sha=$b&per_page=1" \
    | grep -i '^link:' | sed -n 's/.*[?&]page=\([0-9]*\)>; rel="last".*/\1/p')
  merges=$(gh api "repos/$r/commits?sha=$b&per_page=100" \
    | python3 -c 'import sys,json;c=json.load(sys.stdin);print(sum(1 for x in c if len(x["parents"])>1))')
  jb=$(gh api "repos/$r/languages" -q '.Java // 0')
  kb=$(gh api "repos/$r/languages" -q '.Kotlin // 0')
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$r" "$created" "$build" "$commits" "$merges" "$((jb/1024))" "$((kb/1024))"
done
