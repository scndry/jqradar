# `.githooks/` — 이 리포의 훅 경로

비어 있는 것이 목적이다.

전역 `core.hooksPath`(`~/.config/git/hooks`)에 `Co-Authored-By: Claude/Anthropic`
트레일러를 막는 `commit-msg` 훅이 있다. 이 리포에서는 그 트레일러가 **자료**다 —
§5.1의 `declared_ai_assistance`가 커밋 트레일러에서 선언된 것만 읽고(D48),
P17이 "선언된 도구 관여 변경이 finding을 더 여는가"를 그 표본으로 검증한다.

그래서 전역 훅을 지우는 대신(다른 리포까지 영향) 이 리포의 `core.hooksPath`만
여기로 돌려 해제한다(CLAUDE.md §5):

```sh
git config core.hooksPath .githooks
```

이 리포에 훅이 필요해지면 여기 둔다. 전역 훅은 그대로 살아 있다.
