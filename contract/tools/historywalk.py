"""§4.5 창 밖 한정 걷기 — 프런티어에서 W의 규칙을 창 밖으로 연장한다 (D147·D203·D204·D205).

history/·reproducibility/ 두 계산기가 **같은 걷기**를 쓴다 — 걷기가 둘이면 "두 구현이 같은 shallow clone에서
같은 id"(D205)를 픽스처가 증명할 수 없다. git을 읽지 않는 순수 함수다: 입력은 커밋 dict(관측된 부모·접촉 경로·
머지 여부·커미터 시각·graft 경계 여부)이고 출력은 파일별 결과다.

규칙(D203): 시작점은 창의 프런티어(창 안 커밋과 창 안에서 제외된 머지의 창 밖 부모 전부). 모든 조상을 역방향으로
걷되 머지는 통과만 하고 접촉의 후보가 아니다. 한 경로에서 접촉(그 파일을 만진 비머지 커밋)을 만나면 그 경로는 더
가지 않는다(유계 — "뒤로 한 번"). "마지막" = **지배되지 않는 접촉**(다른 접촉의 조상이 아닌 것) 중 커미터 시각 최대,
동률은 SHA 사전순. graft 경계(D204): 어느 한 경로에서든 접촉을 찾기 전에 경계에 닿으면 지배되지 않는 집합이 불완전할
수 있으므로 `age_unknown` — 보수적이다.
"""

from __future__ import annotations


def frontier(commits: dict[str, dict], in_window: set[str]) -> list[str]:
    """창 안 커밋(머지 포함)의 창 밖 부모 전부 — SHA 사전순(결정적)."""
    out = set()
    for sha in in_window:
        for p in commits[sha]["parents"]:
            if p not in in_window:
                out.add(p)
    return sorted(out)


def _ancestors(commits: dict[str, dict], start: str) -> set[str]:
    seen, stack = set(), list(commits[start]["parents"])
    while stack:
        s = stack.pop()
        if s in seen or s not in commits:
            continue
        seen.add(s)
        stack.extend(commits[s]["parents"])
    return seen


def last_touch(commits: dict[str, dict], start: list[str], path: str) -> dict:
    """한 파일의 창 밖 마지막 접촉. 결과: {"sha": str|None, "contacts": [...], "undominated": [...],
    "touched_boundary": bool, "visited": int}. `sha`가 None이면 경계에 닿았거나(`touched_boundary`) 접촉이 없다."""
    visited: set[str] = set()
    contacts: list[str] = []
    touched_boundary = False
    stack = list(reversed(start))
    while stack:
        sha = stack.pop()
        if sha in visited:
            continue
        visited.add(sha)
        c = commits.get(sha)
        if c is None:
            # 관측 밖(얕은 클론에서 보이지 않는 부모) — 경계와 같은 뜻이다.
            touched_boundary = True
            continue
        if c.get("is_boundary"):
            # graft 경계는 부모 없이 보여 트리 전체를 "추가"한 것처럼 보인다(D148) — 접촉이 아니라 경계다.
            touched_boundary = True
            continue
        if not c["is_merge"] and path in c["paths"]:
            contacts.append(sha)       # 이 경로는 여기서 멈춘다 — 뒤로 한 번
            continue
        stack.extend(reversed(c["parents"]))
    # 지배되지 않는 접촉 — 다른 접촉의 조상이 아닌 것
    anc = {s: _ancestors(commits, s) for s in contacts}
    undominated = sorted(s for s in contacts if not any(s in anc[o] for o in contacts if o != s))
    sha = None
    if undominated and not touched_boundary:
        # 시각 최대, 동률은 SHA 사전순 — 토폴로지가 못 가르는 것만 §2.1의 시각 축으로
        sha = min(undominated, key=lambda s: (-commits[s]["committer_time"], s))
    return {"sha": sha, "contacts": sorted(contacts), "undominated": undominated,
            "touched_boundary": touched_boundary, "visited": len(visited)}
