# S4-16 — team 모드에서 매핑에 없는 저자는 `team_count`에 드는가 (반례 (B) 갈림 · 게이트 G0 — `history/`)

- **인용**: §2.1 `team_count` "이 파일을 만진 팀 수 — 매핑에서 **3인 미만 팀을 `other`로 접은 뒤**의 수(`other`는 하나로 셈)"; §2.1 `authors_unmapped` "`individual`에서 매핑에 없어 `unmapped`로 접힌 저자 수 … `people.json`에만(D163)"; §2.7 "매핑에 없는 저자는 `unmapped`로 접고 파일마다 `authors_unmapped: n`을 병기한다 — 팀의 `other`·`teams_folded`와 같은 처리다"(그 문장은 `individual`의 `author_id`에 대한 것).
- **입력**: `contract/history/team-folding-k-threshold/input.json`(team 모드, 매핑 payments 4·platform 3·billing 1)에 매핑에 없는 저자 z — `src/OnlyUnmapped.java`(z만), `src/PaymentsAndUnmapped.java`(a·z).
- **두 값**(`run.py`가 계산한다): "만진 팀 수"를 글자대로(매핑 밖 저자는 어느 팀도 아니다) → `OnlyUnmapped` **0**·`PaymentsAndUnmapped` **1**; D163의 접기를 team 모드에(매핑 밖 → `unmapped` 하나) → **1**·**2**. history 계산기는 이 입력을 정의하지 않는다 — 매핑 밖 저자에서 `KeyError`("매핑 밖 저자는 이 픽스처가 만들지 않는다").
- **무엇이 갈리나**: 매핑이 저자를 다 덮지 않는 리포(퇴사자·외부 기여자·봇)에서 `team_count`가 0이 되는가(만진 팀이 없는 파일 — "아무도 안 만졌다"와 같은 수)와, team 모드에서 그 저자들의 수가 어디에도 남지 않는가(`authors_unmapped`는 individual 전용).
- **게이트**: 값(`team_count`)이 `report.json` `measures`(team·individual)의 것이고 `history/` 스위트(G0 — `team-folding-k-threshold`)가 그 수를 고정한다 → G0(D266).
