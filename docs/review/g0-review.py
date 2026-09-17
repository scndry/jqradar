#!/usr/bin/env python3
"""G0 교차 검토 — 리뷰어가 실행하는 입구 (§9 G0 #1).

    python3 docs/review/g0-review.py                 # 기계 확인 + 읽을 쌍 안내 + 기록 파일 생성
    python3 docs/review/g0-review.py --verify        # 기계 확인만 (5분)
    python3 docs/review/g0-review.py --pairs         # 읽을 쌍만 화면에 (본문 발췌 포함)
    python3 docs/review/g0-review.py --record 홍길동  # 기록 파일만 만든다
    python3 docs/review/g0-review.py --selftest      # 이 스크립트 자신의 반례 (CI)

이 스크립트는 두 부분으로 나뉜다. **앞부분은 기계가 확인할 수 있는 것**이고 결과가 한 표로
나온다 — 픽스처가 도는가, 스키마가 하드룰을 무는가, 결정이 본문에 착지했는가, 본문의 숫자가
계산에서 나오는가. **뒷부분은 사람만 할 수 있는 것**이다 — 계약 둘을 나란히 읽고 서로
모순되는지 보는 일. 앞부분이 전부 초록이어도 뒷부분은 조금도 줄어들지 않는다. 지금까지 실제로
난 계약 충돌 넷은 전부 앞부분이 초록인 상태에서 사람이 두 절을 함께 읽다가 찾은 것이다.

이 스크립트를 쓴 도구는 계약도 픽스처도 썼다(D84, Trusting Trust). 그래서 이 스크립트는
"통과"를 말하지 않는다 — "기계가 확인한 것"과 "당신이 확인할 것"을 가른다.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRD = ROOT / "prd.md"
RECORDS = ROOT / "docs" / "review" / "records"

# --------------------------------------------------------------------------
# 1. 기계가 확인하는 것
# --------------------------------------------------------------------------

CALCULATORS = [
    ("§2.5 백분위·분위·산술", "contract/percentile/compute.py"),
    ("§2.6 CPD 집계", "contract/cpd/compute.py"),
    ("§2.7 이력·§2.4 쌍·§2.1 저자 사실", "contract/history/compute.py"),
    ("§2.2–2.3 그래프·Lakos", "contract/graph/compute.py"),
    ("§2.8 정체성·정규 인코딩", "contract/reproducibility/compute.py"),
    ("§7 스키마 — 긍정 + 하드룰 변조", "contract/schema/compute.py"),
]

GUARDS = [
    ("결정 착지 검사의 자기 반례 (D139)", ["sh", "ci/check-decision-landing.sh", "--selftest"]),
    ("결정 착지 검사 — prd.md (D139)", ["sh", "ci/check-decision-landing.sh", "prd.md"]),
]

# 본문에 적힌 숫자 ↔ 계산된 값. (본문에서 찾을 문자열, expected.json 경로, JSON 경로, 기대값)
BODY_NUMBERS = [
    ("§2.5 P90 [1..9,100] = 18.1", "contract/percentile/p90-type7/expected.json",
     ["quantiles", 0, "value"], 18.1),
    ("§2.6 겹침 합집합 = 150", "contract/cpd/overlap-merge/expected.json",
     ["duplication_pairs", 0, "pair_dup_tokens"], 150),
    ("§2.3 NCCD(N=41, CCD=512) = 2.76", "contract/graph/nccd-cross-check/expected.json",
     ["system", "display", "NCCD"], 2.76),
    ("§2.3 CCD_balanced(41) = 185.48", "contract/graph/nccd-cross-check/expected.json",
     ["system", "display", "CCD_balanced"], 185.48),
]


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr)


def count_ok(output: str) -> int:
    return sum(1 for line in output.splitlines() if line.startswith("ok"))


def dig(obj, path):
    for key in path:
        obj = obj[key]
    return obj


def ci_jobs() -> list[str]:
    """CI 잡 이름을 워크플로에서 읽는다. 손으로 적으면 잡이 늘 때마다 낡는다."""
    wf = ROOT / ".github" / "workflows" / "contract.yml"
    if not wf.exists():
        return []
    names = re.findall(r"^    name: (.+)$", wf.read_text(encoding="utf-8"), re.M)
    return [n.strip() for n in names]


def prd_version() -> str:
    first = PRD.read_text(encoding="utf-8").splitlines()[0]
    m = re.search(r"v\d+\.\d+(\.\d+)?", first)
    return m.group(0) if m else "?"


def committed_prd_version() -> str:
    """작업트리가 아니라 **커밋된** prd.md의 버전. 미커밋 수정이 브랜치를 따라다닌 사고(§0-22)의 진입점을 본다."""
    code, out = run(["git", "show", "HEAD:prd.md"])
    if code != 0:
        return "?"
    m = re.search(r"v\d+\.\d+(\.\d+)?", out.splitlines()[0])
    return m.group(0) if m else "?"


def verify() -> bool:
    rows = []
    all_ok = True

    wt, committed = prd_version(), committed_prd_version()
    same = wt == committed
    rows.append(("prd.md 버전 — 작업트리 = 커밋", f"{wt} = {committed}" if same else f"{wt} ≠ {committed}  ← 미커밋 수정", same))
    all_ok &= same

    for label, script in CALCULATORS:
        if not (ROOT / script).exists():
            rows.append((label, "스크립트 없음", False)); all_ok = False; continue
        code, out = run([sys.executable, script, "--check"])
        n = count_ok(out)
        rows.append((label, f"{n} 케이스" if code == 0 else "실패 — 아래 출력", code == 0))
        if code != 0:
            all_ok = False
            print(out[-2000:])

    for label, cmd in GUARDS:
        code, out = run(cmd)
        rows.append((label, "무는 것 확인" if code == 0 else "실패 — 아래 출력", code == 0))
        if code != 0:
            all_ok = False
            print(out[-2000:])

    body = PRD.read_text(encoding="utf-8")
    for label, path, jpath, expected in BODY_NUMBERS:
        try:
            got = dig(json.loads((ROOT / path).read_text(encoding="utf-8")), jpath)
            in_body = str(expected) in body
            ok = (got == expected) and in_body
            note = f"계산 {got}, 본문에 {'있음' if in_body else '없음'}"
        except Exception as exc:  # noqa: BLE001
            ok, note = False, f"읽기 실패: {exc}"
        rows.append((label, note, ok))
        all_ok &= ok

    width = max(len(r[0]) for r in rows)
    print("\n기계가 확인한 것")
    print("─" * (width + 40))
    for label, note, ok in rows:
        print(f"  {'✅' if ok else '❌'}  {label.ljust(width)}  {note}")
    print("─" * (width + 40))
    print("  Gradle 빌드·자체 ArchUnit 규칙은 여기서 돌리지 않는다 — Maven Central이 필요하다.")
    jobs = ci_jobs()
    where = f"CI {len(jobs)}잡 중 '{jobs[-1]}'" if jobs else "CI"
    print(f"  직접 보려면: ./gradlew build   (BUILD SUCCESSFUL, 11 tests — {where})")
    return all_ok


# --------------------------------------------------------------------------
# 2. 사람만 할 수 있는 것 — 쌍으로 읽기
# --------------------------------------------------------------------------

PAIRS = [
    {
        "id": 1,
        "title": "모집단 정의 ↔ 그 모집단을 쓰는 렌즈",
        "sections": ["2.5", "3.1", "3.2", "3.3"],
        "history": "충돌 1의 자리. F는 '오래 안 바뀐 파일'을 찾는데 모집단이 active(창 안 변경 ≥ 1)였다 — 찾으려는 파일이 모집단에서 빠졌다. 두 절 각각은 맞았다(§0-4).",
        "ask": "세 렌즈가 각각 어느 모집단에서 백분위를 구하는지 §2.5 표와 §3.1–3.3 식이 일치하는가. 렌즈 백분위(interpretation의 근거)의 모집단과 성분 백분위의 모집단이 같은가.",
    },
    {
        "id": 2,
        "title": "시간 앵커·창 ↔ 시간을 쓰는 측정 ↔ F의 P90",
        "sections": ["2.7", "2.1", "3.3"],
        "history": "충돌 2의 자리. '최근'·'경과 일'의 기준 시점이 없어 같은 HEAD를 나중에 재면 값이 달라졌다(§0-4). v3.8.2에서 90일 지표가 창 안으로 잘렸다(D137).",
        "ask": "age_last_days·chg_days·distinct_authors_90d·change_exposure_90d가 전부 HEAD_TIME과 창 W만 보는가. 창 밖의 어떤 사실이 값에 들어올 수 있는 문장이 남아 있는가.",
    },
    {
        "id": 3,
        "title": "analysis_input_id ↔ 캐시 키 ↔ '두 머신 바이트 동일'",
        "sections": ["2.8", "4.5", "2.9"],
        "history": "D87(포함되지 않은 입력은 결과에 영향을 주면 안 된다)·D111(포함된 입력은 reproduce에 나타난다)·D138(정규 인코딩 = RFC 8785). 재현성 계약 자신이 git 시각 포맷(`%cI`가 UTC를 `Z`로도 `+00:00`으로도 쓴다)에 의존해 CI가 잡은 적이 있다 — `contract/reproducibility/compute.py`와 `contract/history/compute.py`의 주석. prd.md에는 없다.",
        "ask": "§2.8의 입력 목록에 없는데 값에 영향을 주는 것이 §2.1–2.7 어디에 있는가(환경변수·로케일·git 버전·시계). reproduce 예시(§7)만으로 id를 다시 계산할 수 있는가.",
    },
    {
        "id": 4,
        "title": "산술 계약 ↔ composite ↔ 임계 비교",
        "sections": ["2.5", "3.6", "3.7"],
        "history": "여기서 이미 하나 나왔다(D121): composite는 √를 산술 입력으로 쓰므로 '√는 표시값에만'이 닿지 않았다 — 전정밀 71.5 vs 표시값 71.4.",
        "ask": "'반올림 전 정확값으로 비교한다'가 §3.7의 모든 임계(0.90·0.75·IQR·N)에 실제로 적용되는가. 직렬화(1자리·4자리)된 값을 다시 읽어 비교하는 경로가 문장 어디에 열려 있는가.",
    },
    {
        "id": 5,
        "title": "CPD 클러스터 ↔ 발생 수준 새 중복 ↔ twins",
        "sections": ["2.6", "5.2", "2.1"],
        "history": "클러스터 해시만으로는 A↔B → A↔C의 새 사본 C를 놓쳤다(D40). 클러스터 ID는 해시+토큰 수, 새 중복은 발생(파일·구간) 수준.",
        "ask": "§2.6의 '발생'과 §5.2의 '발생'이 같은 단위인가(파일·시작·끝 토큰). twins(§2.1)가 자기 중복을 세지 않는다는 문장이 §2.6과 일치하는가. rename 매핑이 어느 쪽에 적용되는가.",
    },
    {
        "id": 6,
        "title": "컴포넌트 전략 ↔ Lakos ↔ Architecture Context",
        "sections": ["2.2", "2.3", "3.4"],
        "history": "D130: auto의 '60% 초과 자식'이 무엇의 60%인지 없었다 — 클래스 수로 정했다. 외부 의존은 의사 노드로 그래프에 두되 지표에서는 뺀다.",
        "ask": "external 의사 노드가 Ca·Ce·CCD 계산에 들어가는지 세 절이 같은 말을 하는가. 테스트 클래스 제외(§2.2)가 §2.1 fan_in 정의와 일치하는가.",
    },
    {
        "id": 7,
        "title": "파일 쌍 ↔ Hidden Coupling ↔ 커밋 거칠기",
        "sections": ["2.4", "3.5", "2.7"],
        "history": "D134: tc의 분모가 min(chg_a, chg_b)라 스쿼시 리포에서 분모가 작아져 tc가 커진다. 판정은 없고 commit_granularity: coarse 표기만.",
        "ask": "보고 임계(shared ≥ 5 ∧ tc ≥ 0.5)가 §2.4와 §3.5에서 같은 등호 방향인가. coarse가 tc 값 자체를 바꾸는가, 표기만 붙이는가 — 두 절이 같은 답을 하는가.",
    },
    {
        "id": 8,
        "title": "저자 사실 ↔ 저자 필드 읽기 ↔ people 정책",
        "sections": ["2.1", "2.7", "4.3"],
        "history": "D48·D135: 정체는 프로세스 밖으로 나가지 않고, 익명 집계만 기본 켜짐. 정체 부재 검사는 모양이 아니라 출처로 가른다.",
        "ask": "attribution=off에서 산출물에 나가는 것의 목록이 §2.1과 §2.7에서 같은가. '해시도 저장하지 않는다'가 §2.1의 어떤 필드와도 충돌하지 않는가(team_count는?). scan이 people 절을 읽는 것을 §4.3 외의 절이 부정하는가.",
    },
]

QUESTIONS = [
    "두 절이 같은 이름을 **다른 뜻**으로 쓰는가?  (n이 모집단인지 랭킹 집합인지 — 실제로 갈렸다, D116)",
    "한 절이 요구하는 것을 다른 절이 **불가능하게** 하는가?  (F의 모집단 — 실제로 그랬다, D24)",
    "두 절을 순서대로 실행하면 **정의되지 않은 상태**가 생기는가?  (validated 뒤 머지 전에 다른 PR이 먼저 머지되면 — D91·D99)",
]


def section_text(number: str) -> str:
    """`### 2.5 …` 또는 `## 4. …`부터 다음 같은 급 이상의 제목 전까지. 없으면 크게 실패한다 — prd.md가 절을 옮겼다는 뜻이다."""
    lines = PRD.read_text(encoding="utf-8").splitlines()
    pat_sub = re.compile(rf"^### {re.escape(number)}\b")
    pat_top = re.compile(rf"^## {re.escape(number.split('.')[0])}\.\s")
    start = next((i for i, l in enumerate(lines) if pat_sub.match(l)), None)
    level = 3
    if start is None and "." not in number:          # `10` 같은 최상위 절만 `## n.`으로 찾는다
        start = next((i for i, l in enumerate(lines) if pat_top.match(l)), None)
        level = 2
    if start is None:
        sys.exit(f"prd.md에 §{number} 제목이 없다 — 절이 옮겨졌으면 이 스크립트의 PAIRS를 먼저 고쳐야 한다.")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## ") or (level == 3 and lines[j].startswith("### ")):
            end = j
            break
    return "\n".join(lines[start:end]).rstrip()


def show_pairs(full: bool) -> None:
    print("\n당신만 할 수 있는 것 — 계약을 **쌍으로** 읽기")
    print("지금까지 실제로 난 충돌 넷은 전부 한 절 안에서는 보이지 않았고, 두 절을 함께 실행하려 할 때 드러났다.")
    print("쌍마다 아래 세 질문을 던진다:\n")
    for q in QUESTIONS:
        print(f"  · {q}")
    for pair in PAIRS:
        secs = " ↔ ".join(f"§{s}" for s in pair["sections"])
        print("\n" + "═" * 78)
        print(f"쌍 {pair['id']}  {pair['title']}    [{secs}]")
        print("─" * 78)
        print(f"이력: {pair['history']}")
        print(f"볼 것: {pair['ask']}")
        if full:
            for s in pair["sections"]:
                print("\n" + "·" * 78)
                print(section_text(s))
    print("\n" + "═" * 78)
    print("쌍 여덟이 끝나면 하나 더 — 여덟에 들지 않은 절 둘을 **당신이 골라** 같은 세 질문을 던진다.")
    print("위 목록도 이 스크립트를 쓴 도구가 정한 것이라, 도구가 못 본 쌍은 목록에도 없다.")


# --------------------------------------------------------------------------
# 3. 기록 파일
# --------------------------------------------------------------------------

def make_record(reviewer: str) -> Path:
    RECORDS.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    slug = re.sub(r"[^\w-]+", "-", reviewer).strip("-") or "reviewer"
    path = RECORDS / f"{today}-{slug}.md"
    if path.exists():
        return path
    version = prd_version()
    head = run(["git", "rev-parse", "--short", "HEAD"])[1].strip()
    rows = "\n".join(
        f"| {p['id']} | {p['title']} | §{' ↔ §'.join(p['sections'])} |  |  |  |" for p in PAIRS
    )
    path.write_text(f"""# G0 교차 검토 기록 — {reviewer}

- 대상: `prd.md` {version} @ `{head}` · 범위: **§2.1–2.9** (G0 #1)
- 날짜: {today}
- 독립성: 이 리포에 커밋한 적이 [ ] 없다 / [ ] 있다 — 둘 중 최소 한 명은 없어야 한다(D84).
- 기계 확인(`g0-review.py --verify`)을 직접 돌렸는가: [ ]

## 쌍별 판정

판정은 셋 중 하나: **모순 없음** / **모순** / **모호**(두 절이 같은 말인지 판단할 수 없음 — 이것도 발견이다).

| 쌍 | 제목 | 절 | 판정 | 어느 문장이 | 왜 |
|---|---|---|---|---|---|
{rows}
| 9 | (당신이 고른 쌍) |  |  |  |  |

## 발견 — 모순·모호마다 한 항목

각 항목: 충돌하는 문장 둘을 **그대로 인용**하고(§번호 포함), 어느 쪽이 맞아야 하는지 의견을 적는다. 고치지 않는다 — 결정은 §0에 항목, §10에 D 번호로 소유자가 한다.

### 발견 1
- 절:
- 문장 A:
- 문장 B:
- 무엇이 갈리나:
- 의견:

## 판정

- [ ] G0 #1 통과 — 모순 없음 (모호는 있어도 됨, 목록으로 남긴다)
- [ ] 통과시키지 않음 — 발견 n건이 먼저 닫혀야 한다

통과시키지 않기로 한 판단도 같은 자리에 적는다 — 그것은 도구가 일하고 있다는 증거다(§9 자기 적용 규칙).

## 이 검토가 보지 못한 것

기계 확인이 초록이어도, 위 쌍 여덟도, 전부 이 문서를 만든 도구가 정한 범위다. 여기 적어 두면 다음 리뷰어가 거기서 시작한다:
-
""", encoding="utf-8")
    return path


# --------------------------------------------------------------------------


# ── `--count` — 기록에서 열린 발견을 센다 (D140·D151·D152) ────────────────────
#
# **사람 보고가 아니라 계산이다.** 그래서 무엇을 읽는지가 계약이어야 한다.
#
# 읽는 것: `docs/review/records/`의 **종합** 파일에 있는 표 둘.
#
#   병합 대응표   `| # | 종합 발견 | 병합한 개별 | 절 집합… | 범위 |`
#   미부착 표     `| 개별 | 주장 | 절 집합 | 범위 |`
#
# 개별 기록이 **정본**이므로(D141) 절 집합은 개별의 `절:` 줄에서 온 것이어야 하고,
# 종합은 자기가 병합한 개별을 가리켜야 한다(D152). 그래서 **대응표가 없는 종합은
# 세지 않고 "대응 없음"으로 보고한다** — 1차 종합이 범위 안 발견 일곱을 떨어뜨린 것을
# 종합만 읽었으면 놓쳤다(2026-09-16 대응표).
#
# 세는 단위는 `dedupe_key`(D151·D152) = (절 집합, 주장, 범위):
#   · 한 종합 항목에 병합된 개별들 → key 하나
#   · 어느 종합 항목에도 안 붙은 개별(미부착) → 각각 key 하나
#   · **쪼갬**: 한 개별이 두 종합 항목에 붙으면 그 둘은 **한 key다**(접는다).
#     접지 않으면 종합자가 개별 하나를 쪼개 "발견 수"를 늘릴 수 있다.
#   · 출처 없는 종합 항목(병합한 개별이 0) → 세지 않고 보고한다.
#
# 범위(D152): **밖 = 절 집합에 §2.1–2.9가 하나도 없는 것.** 표의 선언과 절 집합에서
# 계산한 값이 어긋나면 어긋남을 보고한다 — 표를 믿지 않는다.
#
# 닫힘: **기록에 `닫힘 — D<n>`이 적힌 것만.** `prd.md`를 읽어 추측하지 않는다.
# 표시가 없으면 열린 것이다.

KEY_TABLE_HEAD = "| # | 종합 발견 | 병합한 개별 |"
UNATTACHED_HEAD = "| 개별 | 주장 | 절 집합 | 범위 |"
CLOSED_RE = re.compile(r"닫힘\s*—\s*(D\d+)")
SOURCE_RE = re.compile(r"R\d+-\d+")
SECTION_RE = re.compile(r"§\d+(?:\.\d+)?")
IN_SCOPE_RE = re.compile(r"§2\.[1-9]$")


REVIEWER_FILE_RE = re.compile(r"리뷰어-(\d+)\.md$")
FINDING_HEAD_RE = re.compile(r"^### 발견 (\d+)\b")


def read_individuals(records_dir: Path) -> dict:
    """개별 기록에서 `R<k>-<n>` → 절 집합을 읽는다. **개별이 정본이다**(D141·D152).

    `--count`가 종합의 표만 읽으면 표가 정본을 배신해도 조용히 센다 — 표의 절 집합을
    `§2.8 §7`에서 `§7`로 바꾸고 범위 선언도 `밖`으로 바꾸면 범위 안 key 하나가 소리
    없이 사라진다(2026-09-17 변조로 확인). 표는 **사본**이므로 정본과 대조한다.
    """
    out = {}
    for path in records_dir.glob("*.md"):
        m = REVIEWER_FILE_RE.search(path.name)
        if not m:
            continue
        r = m.group(1)
        cur = None
        for line in path.read_text(encoding="utf-8").split("\n"):
            head = FINDING_HEAD_RE.match(line)
            if head:
                cur = f"R{r}-{head.group(1)}"
                out[cur] = {"sections": [], "file": path.name}
                continue
            if cur and line.startswith("- 절:") and not out[cur]["sections"]:
                out[cur]["sections"] = SECTION_RE.findall(line)
    return out


def _rows_after(lines: list[str], head: str) -> list[list[str]]:
    """표 헤더 다음의 행들을 셀 목록으로. 구분선(---)은 건너뛰고 표가 끝나면 멈춘다."""
    out = []
    for i, l in enumerate(lines):
        if not l.startswith(head):
            continue
        for l2 in lines[i + 1:]:
            if not l2.startswith("|"):
                break
            cells = [c.strip() for c in l2.strip().strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            out.append(cells)
        break
    return out


def _reconcile(ident, srcs, declared, individuals, problems, where) -> list:
    """표의 절 집합을 **개별의 합집합**과 대조한다. 정본은 개별이므로 개별을 돌려준다."""
    truth = sorted({s for k in srcs for s in individuals.get(k, {}).get("sections", [])},
                   key=lambda x: [float(y) for y in x[1:].split(".")] + [0])
    if sorted(set(declared)) != sorted(set(truth)):
        problems.append(("절 집합 어긋남", where,
                         f"{ident} — 표는 `{' '.join(declared) or '(없음)'}`, "
                         f"개별({', '.join(srcs)})의 합집합은 `{' '.join(truth)}`. 개별이 정본이다"))
    return truth


def _scope_of(sections: list[str]) -> str:
    return "안" if any(IN_SCOPE_RE.match(s) for s in sections) else "밖"


def collect_keys(records_dir: Path) -> dict:
    """종합 파일들에서 key를 모은다. 판정하지 않고 읽은 것과 어긋남을 함께 돌려준다."""
    keys, problems = [], []
    individuals = read_individuals(records_dir)
    synth = sorted(p for p in records_dir.glob("*.md") if "종합" in p.name)
    for path in synth:
        lines = path.read_text(encoding="utf-8").split("\n")
        merged = _rows_after(lines, KEY_TABLE_HEAD)
        unatt = _rows_after(lines, UNATTACHED_HEAD)
        if not merged:
            problems.append(("대응 없음", path.name,
                             "병합 대응표가 없다 — 이 종합은 세지 않는다(D152)"))
            continue
        groups = []   # (id, sources, sections, declared, closed)
        for cells in merged:
            ident = cells[0]
            srcs = SOURCE_RE.findall(cells[2]) if len(cells) > 2 else []
            secs = SECTION_RE.findall(cells[3]) if len(cells) > 3 else []
            decl = "밖" if len(cells) > 4 and "밖" in cells[4] else "안"
            closed = CLOSED_RE.search(" ".join(cells))
            missing = [s for s in srcs if s not in individuals]
            if not srcs or missing:
                problems.append(("출처 없음", path.name,
                                 f"{ident} — " + ("병합한 개별이 없다" if not srcs
                                  else f"가리킨 개별이 실재하지 않는다: {', '.join(missing)}")
                                 + ". 세지 않는다"))
                continue
            secs = _reconcile(ident, srcs, secs, individuals, problems, path.name)
            groups.append([ident, srcs, secs, decl, closed.group(1) if closed else None])
        # 쪼갬: 같은 개별이 둘 이상의 종합 항목에 붙으면 접는다
        folded, seen = [], {}
        for g in groups:
            hit = next((folded[seen[s]] for s in g[1] if s in seen), None)
            if hit is not None:
                problems.append(("쪼갬", path.name,
                                 f"{g[0]} — {hit[0]}과 같은 개별({', '.join(sorted(set(g[1]) & set(hit[1])))})"
                                 f". 한 key로 접는다"))
                hit[0] += f"+{g[0]}"
                hit[1] = sorted(set(hit[1]) | set(g[1]))
                hit[2] = sorted(set(hit[2]) | set(g[2]))
                hit[4] = hit[4] or g[4]
                continue
            folded.append(g)
            for s in g[1]:
                seen[s] = len(folded) - 1
        for cells in unatt:
            srcs = SOURCE_RE.findall(cells[0])
            secs = SECTION_RE.findall(cells[2]) if len(cells) > 2 else []
            decl = "밖" if len(cells) > 3 and "밖" in cells[3] else "안"
            closed = CLOSED_RE.search(" ".join(cells))
            missing = [s for s in srcs if s not in individuals]
            if not srcs or missing:
                if srcs:
                    problems.append(("출처 없음", path.name,
                                     f"{srcs[0]}(미부착) — 가리킨 개별이 실재하지 않는다. 세지 않는다"))
                continue
            secs = _reconcile(srcs[0] + "(미부착)", srcs, secs, individuals, problems, path.name)
            folded.append([srcs[0] + "(미부착)", srcs, secs, decl,
                           closed.group(1) if closed else None])
        for ident, srcs, secs, decl, closed in folded:
            computed = _scope_of(secs)
            if computed != decl:
                problems.append(("범위 어긋남", path.name,
                                 f"{ident} — 표는 '{decl}', 절 집합 {' '.join(secs)}로는 '{computed}'"))
            keys.append({"id": ident, "file": path.name, "sources": srcs,
                         "sections": secs, "scope": computed, "closed": closed})
    return {"keys": keys, "problems": problems, "synth": [p.name for p in synth]}


def count_keys(records_dir: Path = RECORDS) -> int:
    got = collect_keys(records_dir)
    keys, problems = got["keys"], got["problems"]
    inside = [k for k in keys if k["scope"] == "안"]
    closed = [k for k in inside if k["closed"]]
    openk = [k for k in inside if not k["closed"]]
    print("G0 #1 열린 발견 — 기록에서 센 수 (D140·D151·D152)")
    print(f"  읽은 종합: {', '.join(got['synth']) or '없음'}")
    print()
    print(f"  범위 안 `dedupe_key`  총 {len(inside)}")
    print(f"    닫힘  {len(closed)}" + (f" — {', '.join(sorted({k['closed'] for k in closed}))}" if closed else ""))
    print(f"    열림  {len(openk)}")
    print(f"  범위 밖 (G3 목록으로) {len([k for k in keys if k['scope'] == '밖'])}")
    print()
    print("  **닫힘 표시는 기록에서만 읽는다** — `닫힘 — D<n>`이 적힌 key만 닫힌 것으로 센다.")
    print("  `prd.md`를 읽어 추측하지 않는다. 표시가 없으면 열린 것이다.")
    if problems:
        print()
        print("  보고 — 세지 않았거나 어긋난 것:")
        for kind, where, what in problems:
            print(f"    [{kind}] {where}: {what}")
    if openk:
        print()
        print("  열린 key:")
        for k in openk:
            print(f"    {k['id']:<28} {' '.join(k['sections'])}")
    return 0


def count_selftest() -> list[tuple[str, bool, str]]:
    """`--count`의 자기 반례. 합성 종합 하나마다 기대를 첫 줄 주석에 적어 둔다.

    계산기가 통과만 시키면 "열린 발견 0"이 검사 없이 참이 된다 — 그래서 **세는 쪽과
    세지 않는 쪽을 둘 다** 시험한다: 닫힘/열림을 뒤집지 않는가, 걸친 것을 밖이라
    하지 않는가(D152), 출처 없는 것을 세지 않는가, 쪼개진 것을 둘로 세지 않는가.
    """
    import json as _json
    out = []
    cases = sorted((ROOT / "docs" / "review" / "count-cases").glob("*/"))
    for case in cases:
        md = case / "종합.md"
        if not md.exists():
            continue
        head = md.read_text(encoding="utf-8").split("\n", 1)[0]
        exp = _json.loads(re.search(r"<!-- expect: (.*) -->", head).group(1))
        got = collect_keys(case)
        inside = [k for k in got["keys"] if k["scope"] == "안"]
        closed = [k for k in inside if k["closed"]]
        kinds = sorted({p[0] for p in got["problems"]})
        ok = (len(inside) == exp["inside"] and len(closed) == exp["closed"]
              and len(inside) - len(closed) == exp["open"]
              and kinds == sorted(exp["problems"]))
        why = re.sub(r"^# 합성 종합 — ", "", md.read_text(encoding="utf-8").split("\n")[1])
        detail = f"안{len(inside)} 닫{len(closed)} 열{len(inside)-len(closed)} {kinds or ''}"
        out.append((f"{case.name:<30} {why}", ok, detail))
    return out


def selftest() -> int:
    """이 스크립트 자신의 반례 — 있는 절을 있다고, 없는 절을 없다고 하는가(D131·§0-22)."""
    checks = []
    checks.append(("있는 하위 절(2.5)을 찾는다", section_text("2.5").startswith("### 2.5")))
    checks.append(("있는 최상위 절(10)을 찾는다", section_text("10").startswith("## 10.")))
    try:
        section_text("2.99"); checks.append(("없는 하위 절(2.99)에서 멈춘다", False))
    except SystemExit:
        checks.append(("없는 하위 절(2.99)에서 멈춘다", True))
    try:
        section_text("99"); checks.append(("없는 최상위 절(99)에서 멈춘다", False))
    except SystemExit:
        checks.append(("없는 최상위 절(99)에서 멈춘다", True))
    t25 = section_text("2.5")
    checks.append(("절 발췌가 다음 절(2.6)로 넘어가지 않는다", "### 2.6" not in t25))
    for p in PAIRS:
        for sec in p["sections"]:
            section_text(sec)  # 없으면 SystemExit — PAIRS와 prd.md의 절 번호가 어긋난 것
    checks.append(("PAIRS의 모든 절이 prd.md에 있다", True))

    # 쌍의 '이력'·'질문'이 인용하는 D 번호와 §0 항목이 실제로 있는가.
    # 없는 것을 가리키면 리뷰어가 첫 발을 헛디딘다. 절 번호만 보던 검사에
    # 이것이 빠져 있었고, 실제로 하나가 어긋나 있었다(쌍 3이 git 시각 포맷 사고를
    # §0-22로 가리켰는데 §0-22는 정규 인코딩·결정 착지다).
    #
    # **이 검사는 존재만 본다.** 인용이 가리키는 내용이 맞는지는 기계가 모른다 —
    # 위 사례도 §0-22가 '있었기' 때문에 존재 검사로는 잡히지 않았을 것이다.
    # 내용은 사람이 본다.
    prd_text = PRD.read_text(encoding="utf-8")
    have_d = set(re.findall(r"^- ~?~?D(\d+) ", prd_text, re.M))
    have_zero = set(re.findall(r"^### (0-\d+)\.", prd_text, re.M))
    dangling = []
    for p in PAIRS:
        blob = p["history"] + " " + p["ask"]
        dangling += [f"쌍{p['id']}:D{d}" for d in re.findall(r"\bD(\d+)\b", blob)
                     if d not in have_d]
        dangling += [f"쌍{p['id']}:§{z}" for z in re.findall(r"§(0-\d+)", blob)
                     if z not in have_zero]
    # 머리말(QUESTIONS)의 인용도 같은 자리에서 본다 — 리뷰어가 가장 먼저 읽는 줄이다.
    qblob = " ".join(str(q) for q in QUESTIONS)
    dangling += [f"머리말:D{d}" for d in re.findall(r"\bD(\d+)\b", qblob)
                 if d not in have_d]
    checks.append((f"쌍이 인용하는 D 번호·§0 항목이 prd.md에 있다"
                   + (f" — 없는 것 {dangling}" if dangling else ""), not dangling))
    for name, ok, detail in count_selftest():
        checks.append((f"--count 반례: {name}" + ("" if ok else f"  [{detail}]"), ok))

    bad = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  {'ok ' if ok else 'BAD'}  {name}")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true", help="기계 확인만")
    ap.add_argument("--pairs", action="store_true", help="읽을 쌍만 (본문 발췌 포함)")
    ap.add_argument("--record", metavar="이름", help="기록 파일만 만든다")
    ap.add_argument("--count", action="store_true", help="기록에서 열린 발견을 센다")
    ap.add_argument("--selftest", action="store_true", help="이 스크립트 자신의 반례")
    args = ap.parse_args()

    if args.count:
        return count_keys()

    if args.selftest:
        print("자기 반례 — 절 발췌기가 있는 것을 있다고, 없는 것을 없다고 하는가:")
        return selftest()

    if args.record and not (args.verify or args.pairs):
        path = make_record(args.record)
        print(f"기록 파일: {path.relative_to(ROOT)}")
        return 0

    print(f"G0 교차 검토 — prd.md {prd_version()} · 범위 §2.1–2.9 · 리포 {ROOT.name}")
    ok = True
    if args.verify or not args.pairs:
        ok = verify()
    if args.pairs or not args.verify:
        show_pairs(full=args.pairs)
    if not (args.verify or args.pairs):
        print("\n다음:")
        print("  1. 쌍의 본문을 나란히 보려면:   python3 docs/review/g0-review.py --pairs | less")
        print("  2. 기록 파일을 만들려면:        python3 docs/review/g0-review.py --record <이름>")
        print("  3. 결과를 어디에 적는가:        docs/g0-review-packet.md §6")
        print("\n기계가 확인한 것이 전부 초록이라는 사실은 위 쌍 읽기를 조금도 대신하지 않는다.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
