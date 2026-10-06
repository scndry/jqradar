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
    # 3차 라운드(D151 — 입력을 바꾼 라운드). 쌍 1–8은 이력에 닫은 D를 적고 "볼 것"을
    # **결정이 다른 절과 또 어긋났는가**로 바꿨다 — 1·2차가 잡은 것은 전부 결정이 §10에 있고
    # 본문이 따라오지 않은 자리였다. 쌍 9–11은 §2 내부(기록 다섯이 "거의 보지 않았다"고 적은 축),
    # 쌍 12–14는 D174–D178이 방금 만든 접점이다.
    {
        "id": 1,
        "title": "모집단 정의 ↔ 그 모집단을 쓰는 렌즈",
        "sections": ["2.5", "3.1", "3.2", "3.3"],
        "history": "충돌 1의 자리(§0-4). 그 뒤 D168(기록은 <field>.<population> 두 단계, 뜻은 소속), D169(순위 지름길은 렌즈별 — F는 지시변수 먼저), D172(렌즈 = H·Dx·F, composite는 렌즈가 아니다).",
        "ask": "두 단계 기록을 §3.x의 식·§3.7의 evidence·§7 예시가 같은 모양으로 쓰는가. F의 0 동점군(D169)이 §3.7의 priority desc·§5.5의 anchor_class와 또 어긋나는가. 결정을 다시 묻지 말고 결정이 이웃 절에 내려갔는지를 보라.",
    },
    {
        "id": 2,
        "title": "시간 앵커·창 ↔ 시간을 쓰는 측정 ↔ F의 P90",
        "sections": ["2.7", "2.1", "3.3"],
        "history": "충돌 2의 자리(§0-4). D137(90일 지표는 창 안)·D146–D150(파일별 마지막 커밋 맵이 id 입력, 창 밖 한정 걷기, shallow는 age_unknown, D137의 근거 교체)·D174(W는 측정의 집합 — §5.5의 first-parent와 다른 질문).",
        "ask": "D174의 '측정의 집합'이 §2.1 표의 모든 'W 안'과 §4.5의 한정 걷기와 또 어긋나는가. shallow(D148)에서 age_unknown과 last_commit_map_sha256이 같은 사실을 말하는가. 창 밖의 어떤 사실이 값에 들어오는 문장이 아직 남아 있는가.",
    },
    {
        "id": 3,
        "title": "analysis_input_id ↔ 캐시 키 ↔ '두 머신 바이트 동일'",
        "sections": ["2.8", "4.5", "2.9"],
        "history": "D87·D111·D138. 그 뒤 D154(비교 대상 = scanned_at·classes_reproduction_inputs를 뺀 전부)·D155(스케일 표)·D156(분수 파라미터는 문자열)·D157(시각은 Z)·D158(reproduce의 필드는 세 종류)·D159(캐시 키 = §2.8 입력의 사영)·D160(people은 id 입력).",
        "ask": "reproduce의 세 종류 표시([id]·[fn]·[x])가 §7의 모든 필드에 붙어 있는가 — 붙지 않은 필드가 넷째 종류다. 사영(D159)이 §4.5의 캐시 셋(측정·전이·이력)에 전부 걸리는가. reproduce 예시만으로 id를 다시 계산할 수 있는가.",
    },
    {
        "id": 4,
        "title": "산술 계약 ↔ composite ↔ 임계 비교",
        "sections": ["2.5", "3.6", "3.7"],
        "history": "D121(composite는 전정밀 가중합). 그 뒤 D169·D171(interpretation은 lens_pct의 함수 — null이면 null + reason)·D172(composite에는 백분위·interpretation이 없다)·D173(population_note는 confidence와 같은 시험).",
        "ask": "interpretation null + reason이 §5.5의 anchor_class·§7.1의 렌더러에서 같은 뜻으로 읽히는가. composite가 렌즈가 아니라는 것이 §7.1 A2·§5.4 앵커와 또 어긋나는가. 직렬화된 값을 다시 읽어 비교하는 경로가 어디에 열려 있는가.",
    },
    {
        "id": 5,
        "title": "CPD 클러스터 ↔ 파일×클러스터 수준 새 중복 ↔ twins",
        "sections": ["2.6", "5.2", "2.1"],
        "history": "D40. 그 뒤 D165(새 중복은 파일×클러스터 수준·새 발생 수 = max(0, HEAD − BASE)·서로 다른 파일 ≥ 2·게이트 손잡이 min_tokens)·D166(self_dup_tokens는 한 파일에만 있는 클러스터의 것)·D178(§6.3도 그 손잡이를 가리킨다).",
        "ask": "§5.2의 '새 발생 수'가 §5.5의 후속 판정 토큰 비율(≥ 80% / ≥ 20% / ≥ 50%)과 §6.3의 BLOCK이 세는 것과 같은 단위인가 — 1차 리뷰어 5가 지목하고 보지 않은 자리. rename 매핑이 §5.2·§5.5 양쪽에 같은 방향으로 적용되는가.",
    },
    {
        "id": 6,
        "title": "컴포넌트 전략 ↔ Lakos ↔ Architecture Context",
        "sections": ["2.2", "2.3", "3.4"],
        "history": "D130(60%는 클래스 수). 그 뒤 D170(적격 main 소스 정의, 클래스 없는 소스는 fan_in null·reason no_bytecode·컴포넌트 null)·D175(컴포넌트 식별자 집합이 바뀌면 context_changed)·D177(auto 분할은 1회).",
        "ask": "no_bytecode·arch_context: null이 §2.3의 N·§3.4·§5.3의 SCC 행과 또 어긋나는가. I = Ce/(Ca+Ce)의 분모가 0인 컴포넌트(external만 이웃)에서 §3.4가 무엇을 붙이는가 — 1차 리뷰어 5가 유보한 자리.",
    },
    {
        "id": 7,
        "title": "파일 쌍 ↔ Hidden Coupling ↔ 커밋 거칠기",
        "sections": ["2.4", "3.5", "2.7"],
        "history": "D134. 그 뒤 D164(shared는 W 안, tc ≤ 1 불변식)·D167(정렬 키)·D176(그래프 밖 쌍은 판정하지 않음 — static_dependency null + reason, 정렬 false·true·null).",
        "ask": "static_dependency: null이 §7.1 A5 결합 오버레이·§5.5의 순환 근사(source_imports)와 또 어긋나는가. tc ≤ 1 불변식이 coarse에서도 서는가. 보고 임계의 등호 방향이 §2.4와 §3.5에서 여전히 같은가.",
    },
    {
        "id": 8,
        "title": "저자 사실 ↔ 저자 필드 읽기 ↔ people 정책",
        "sections": ["2.1", "2.7", "4.3"],
        "history": "D48·D135. 그 뒤 D160(people.attribution·매핑 해시는 id 입력, reproduce.people)·D161(저자 사실은 people.json, k 하한은 팀 집계에)·D162(off는 셋으로 닫힘)·D163(author_id는 매핑 파일의 키).",
        "ask": "people.json의 팀·저자 사실이 §7.1·§6.2 MCP(저자 데이터는 individual만)와 같은 범위인가. authors_unmapped·teams_folded가 §2.1 표와 D155-1 표에 다 있는가. off에서 나가는 것의 목록이 §2.1·§2.7·§7에서 여전히 같은 셋인가.",
    },
    {
        "id": 9,
        "title": "토크나이저 ↔ 토큰을 세는 모든 필드",
        "sections": ["2.6", "2.1", "5.2"],
        "history": "§2 내부 쌍 — 예시 기록·1차 리뷰어 5가 '거의 보지 않았다'고 적은 축. §2.6은 identifier·literal을 무시한 정규화 열을 세고 §2.1의 file_tokens는 'CPD 토크나이저 전체 토큰 수'다. D166이 분할(union ⊇ 교차 ∪ 자기)을 적었다.",
        "ask": "dup_extent = union_dup_tokens / file_tokens의 분자와 분모가 같은 토크나이저·같은 정규화인가. §5.2의 min_tokens 비교가 정규화 전인가 후인가. §7 fixture_change 예시의 Kotlin 문자열 템플릿이 두 수에 다르게 닿는가.",
    },
    {
        "id": 10,
        "title": "쌍별 투영의 방향 ↔ 대칭이어야 하는 것",
        "sections": ["2.6", "2.1", "3.5"],
        "history": "§2 내부 쌍 — 1차 리뷰어 1 유보 (a): pair_dup_tokens(A,B)는 'A = 경로 사전순 앞'의 A쪽 합집합인데 twins(A)는 A가 뒤여도 성립해야 한다. D167이 hidden_couplings를 (a, b) 사전순으로 정렬한다.",
        "ask": "twins·active_twins·active_twin_ratio가 투영 방향과 무관한가(§2.1 ↔ §2.6). duplication_pairs와 hidden_couplings의 (a, b)가 같은 사전순인가. B쪽 구간이 A쪽과 길이가 다를 때 어느 수가 §7에 인쇄되는가.",
    },
    {
        "id": 11,
        "title": "단위의 끝 — 일·클래스·자기 간선",
        "sections": ["2.1", "2.2", "2.7"],
        "history": "§2 내부 쌍 — 1차 리뷰어 4 유보 (1): age_last_days의 '일'이 내림인지 반올림인지; 리뷰어 1 유보 (b): fan_in이 같은 파일 안 클래스 간 의존을 세는지(§2.2의 자기 간선 제거는 컴포넌트로 접을 때만 언급). D170이 fan_in null을 정했다.",
        "ask": "age_last_days·chg_days·authors_window_days가 같은 '일'(UTC 날짜 / 86400초 / 내림)인가 — §2.7·D157과 contract/history가 같은 답인가. fan_in의 '직접 의존'에서 같은 파일·같은 컴포넌트·external이 각각 세어지는가.",
    },
    {
        "id": 12,
        "title": "측정의 집합 ↔ 전이의 후보 ↔ 검증 트리",
        "sections": ["2.7", "5.5", "6.3"],
        "history": "D174 — W(비머지, 브랜치 포함)와 first-parent(머지 커밋)는 다른 질문. 충돌 해결 편집이 보이는 자리는 merge_drift(D91·D103). history/window-vs-first-parent가 두 집합의 다름을 값으로. 이 쌍의 발견은 §5.5·§6.3에 걸리면 범위 밖(D152 — G3 목록으로)이고 그것이 맞는 결과다.",
        "ask": "§5.5의 후보 커밋이 §6.3의 validated_tree_id 결속(D89)과 또 어긋나는가 — 검증 트리는 브랜치 끝인데 귀속은 머지 커밋이면 머지 커밋을 유지하는 리포에서 merge_drift가 항상 참인가, 그때 무엇이 남는가. §5.6 한정 blame이 어느 집합을 걷는가.",
    },
    {
        "id": 13,
        "title": "컴포넌트 식별자 ↔ 게이트 ↔ 원장 정체성",
        "sections": ["2.2", "5.3", "5.5"],
        "history": "D175 — 식별자 집합이 바뀌면 SCC·NCCD 둘 다 context_changed, exit 0. D177 — auto 분할 1회(N의 안정성). 1차 리뷰어 5가 보지 않은 자리: 순환(SCC)의 단위가 §2.2·§5.5(finding 정체성 = SCC 멤버의 정렬 해시)·§6.3(해당 SCC 소멸 ∧ 새 SCC 없음)에서 같은가. 발견이 §5.3·§5.5에만 걸리면 범위 밖(D152).",
        "ask": "auto의 식별자가 이동만으로 바뀔 때 §5.5 component_cycle finding의 정체성(id_drift?)과 §6.3의 합격 판정이 D175와 같은 답을 하는가 — 게이트는 context_changed인데 원장은 새 finding을 만드는가. module·depth:<n>을 쓰라는 절이 §5.4 앵커(SHA 봉인)와 맞는가.",
    },
    {
        "id": 14,
        "title": "판정 없음의 전파",
        "sections": ["2.4", "3.5", "3.7", "7.1"],
        "history": "D176(그래프 밖 쌍은 static_dependency null + reason)·D171(lens_pct null → interpretation null + reason)·D170(fan_in null → F null). 세 결정이 같은 모양('값이 아니라 판정 없음')을 세 자리에 두었다. §7.1에만 걸리는 발견은 범위 밖(D152).",
        "ask": "세 null이 §3.7 confidence·§7.1(A5 결합 오버레이의 굵기 = tc, 불투명도 = confidence)·§5.3 게이트에서 같은 뜻으로 읽히는가 — null을 0으로 그리거나 세는 문장이 어디에 남아 있는가. reason 열거가 세 자리에서 하나의 사전인가(outside_bytecode_scope·no_bytecode·not_in_active …).",
    },
]

# 쌍 15 = 자유(D151 그대로 — 각 모델이 목록 밖 절 둘을 **스스로** 고른다).
# 쌍 16 = 배정(이번 라운드만의 덮기 — 1·2차가 안 간 절). 리뷰어 순서대로 하나씩.
ASSIGNED_STARTS = [
    ("2.9", "픽스처 표가 요구하는 케이스와 §7 예시 JSON의 필드가 서로 다 덮는가 — 1차 리뷰어 3이 손대지 않은 자리"),
    ("7.1", "렌더러가 lens_percentiles·hidden_couplings에 없는 값을 요구하는 자리가 있는가 — 1차 리뷰어 4"),
    ("4.4", "Kotlin smells = null과 §5.3의 '새 P1 smell → WARN'이 만나 Kotlin 전용 변경에서 게이트가 비는가 — 1차 리뷰어 1 유보 (c)"),
    ("6.3", "§2.8의 정체성 셋(validated_tree_id 등)이 검증 경로에서 실제로 만들어지는가 — 1차 리뷰어 3"),
]

QUESTIONS = [
    "두 절이 같은 이름을 **다른 뜻**으로 쓰는가?  (n이 모집단인지 랭킹 집합인지 — 실제로 갈렸다, D116)",
    "한 절이 요구하는 것을 다른 절이 **불가능하게** 하는가?  (F의 모집단 — 실제로 그랬다, D24)",
    "두 절을 순서대로 실행하면 **정의되지 않은 상태**가 생기는가?  (validated 뒤 머지 전에 다른 PR이 먼저 머지되면 — D91·D99)",
]


def input_hash() -> str:
    """`--pairs`가 리뷰어에게 주는 입력(쌍 목록·세 질문·배정)의 sha256 앞 12자.

    D151의 정지 조건은 **입력을 바꾼** 두 라운드 연속 새 발견 0이다. "입력이 바뀌었다"가
    사람의 말이면 확인할 수 없으니 해시로 적는다 — 기록 머리의 `입력: pairs@<해시>`가 같으면
    그 라운드는 '연속'의 둘째가 아니다. prd.md 버전은 넣지 않는다: 쌍 목록이 그대로인데
    본문만 바뀐 라운드는 D151(b)의 '입력 변경'이 아니다.
    """
    import hashlib
    blob = json.dumps({"pairs": PAIRS, "questions": QUESTIONS, "assigned": ASSIGNED_STARTS},
                      ensure_ascii=False, sort_keys=True)
    return "pairs@" + hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


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
    print(f"\n입력: {input_hash()}  — 기록 머리에 그대로 적는다(D151: 입력을 바꾼 라운드만 '연속'으로 센다)")
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
    print(f"쌍 {len(PAIRS)}이 끝나면 둘 더.")
    print("쌍 15 — 목록에 들지 않은 절 둘을 **당신이 골라** 같은 세 질문을 던진다(D151). 배정하지 않는다 —")
    print("        1·2차에서 목록 밖이 생산적이었던 이유가 목록 작성자가 예견하지 못한 자리를 리뷰어가 스스로 골랐기 때문이다.")
    print("쌍 16 — 배정(이번 라운드만의 덮기). 리뷰어 순서대로 하나씩, 그 절에서 출발해 쌍을 만든다:")
    for i, (sec, why) in enumerate(ASSIGNED_STARTS, 1):
        print(f"        리뷰어 {i}: §{sec} — {why}")
    print("쌍 12–14와 쌍 16의 발견은 §5·§6·§7.1에 걸리면 **범위 밖**이다(D152 — 세지 않고 버리지도 않는다, G3 목록으로).")
    print("그것이 맞는 결과다 — 종합자가 범위 안으로 끌어오지 않는다. 범위 안 새 발견 0이 나오면 그 0은 정직한 0이다.")
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
- 입력: {input_hash()}  — `--pairs`가 찍은 값 그대로. 다음 라운드의 기록이 같은 해시면 그 라운드는 "입력을 바꾼 연속"의 둘째가 아니다(D151).
- 기계 확인(`g0-review.py --verify`)을 **먼저** 돌렸는가: [ ] — 그 출력의 첫 행(prd.md 버전 — 작업트리 = 커밋)과 마지막 줄을 여기에 붙인다:
  - `
  - `
- key 접두어: (리뷰어 번호 또는 머리글자 — `--count`가 읽는다, D152)

## 쌍별 판정

판정은 셋 중 하나: **모순 없음** / **모순** / **모호**(두 절이 같은 말인지 판단할 수 없음 — 이것도 발견이다).

| 쌍 | 제목 | 절 | 판정 | 어느 문장이 | 왜 |
|---|---|---|---|---|---|
{rows}
| 15 | (당신이 고른 쌍 — 목록 밖 절 둘, D151) |  |  |  |  |
| 16 | (배정 — `--pairs`의 쌍 16에서 당신 번호의 출발 절) |  |  |  |  |

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

기계 확인이 초록이어도, 위 쌍 열넷도, 전부 이 문서를 만든 도구가 정한 범위다. 여기 적어 두면 다음 라운드의 쌍 목록이 거기서 시작한다(D151 — 입력을 바꾸는 재료):
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
#   · **결정에 의한 분리**(D153): `분리 — D<n>`이 붙은 행은 접지 않는다. D가 key의
#     일부만 닫았으면 주장이 실은 둘이었다는 뜻이므로 **닫는 결정이** 쪼갠다.
#     **D 번호가 그 둘을 가르는 유일한 표지다** — 없으면 종합자의 쪼갬으로 보아 접는다.
#   · 출처 없는 종합 항목(병합한 개별이 0) → 세지 않고 보고한다.
#
# 범위(D152): **밖 = 절 집합에 §2.1–2.9가 하나도 없는 것.** 표의 선언과 절 집합에서
# 계산한 값이 어긋나면 어긋남을 보고한다 — 표를 믿지 않는다.
#
# 닫힘: **기록에 `닫힘 — D<n>`이 적힌 것만.** `prd.md`를 읽어 추측하지 않는다.
# 표시가 없으면 열린 것이다.
#
# 밖 key에도 닫힘 표시가 붙을 수 있다(D191 — S3-24·O3-9). D152는 "세지 않고 버리지도 않는다"이고
# D153의 닫힘은 기록의 표시라 **수에 닿지 않는다** — 그래서 범위 밖은 열림/닫힘을 **갈라** 세되
# 어느 쪽도 범위 안의 수에 더하지 않는다. G3 목록의 상태가 보이는 자리이지 G0 #1의 수가 아니다.

KEY_TABLE_HEAD = "| # | 종합 발견 | 병합한 개별 |"
UNATTACHED_HEAD = "| 개별 | 주장 | 절 집합 | 범위 |"
CLOSED_RE = re.compile(r"닫힘\s*—\s*((?:D\d+[·,]?\s*)+)")
SPLIT_RE = re.compile(r"분리\s*—\s*(D\d+)")
SOURCE_RE = re.compile(r"(?:R\d+|[A-Z][A-Z0-9_]*)-\d+")
SECTION_RE = re.compile(r"§\d+(?:\.\d+)?")
IN_SCOPE_RE = re.compile(r"§2\.[1-9]$")


# 개별 기록의 파일명 → key 접두어. 1차는 `리뷰어-<n>.md` → `R<n>`,
# 2차는 모델 이름 `…-<model>.md` → 대문자 머리글자(`haiku` → `H`).
REVIEWER_FILE_RE = re.compile(r"리뷰어-(\d+)\.md$")
MODEL_FILE_RE = re.compile(r"\d{4}-\d\d-\d\d-([a-z]+)\.md$")
# 기록이 스스로 적는 접두어 — 파일명 추론보다 우선한다.
PREFIX_DECL_RE = re.compile(r"^- key 접두어:\s*([A-Z][A-Z0-9_]*)\s*$", re.M)
FINDING_HEAD_RE = re.compile(r"^### 발견 (\d+)\b")


def read_individuals(records_dir: Path) -> dict:
    """개별 기록에서 `R<k>-<n>` → 절 집합을 읽는다. **개별이 정본이다**(D141·D152).

    `--count`가 종합의 표만 읽으면 표가 정본을 배신해도 조용히 센다 — 표의 절 집합을
    `§2.8 §7`에서 `§7`로 바꾸고 범위 선언도 `밖`으로 바꾸면 범위 안 key 하나가 소리
    없이 사라진다(2026-09-17 변조로 확인). 표는 **사본**이므로 정본과 대조한다.
    """
    out = {}
    for path in records_dir.glob("*.md"):
        if "종합" in path.name:
            continue
        text = path.read_text(encoding="utf-8")
        # 기록이 스스로 접두어를 선언하면 그것을 쓴다 — **개별 기록이면 저자가 누구든 읽는다.**
        # 파일명에서 추론하면 패널 밖(소유자·외부 사람)의 기록이 조용히 빠진다.
        decl = PREFIX_DECL_RE.search(text)
        if decl:
            r = decl.group(1)
        elif (m := REVIEWER_FILE_RE.search(path.name)):
            r = m.group(1)
        elif (m := MODEL_FILE_RE.search(path.name)):
            r = m.group(1)[0].upper()
        else:
            continue
        cur = None
        for line in text.split("\n"):
            head = FINDING_HEAD_RE.match(line)
            if head:
                cur = f"{'R' if r.isdigit() else ''}{r}-{head.group(1)}"
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
            split = SPLIT_RE.search(" ".join(cells))
            groups.append([ident, srcs, secs, decl,
                           "·".join(re.findall(r"D\d+", closed.group(1))) if closed else None,
                           split.group(1) if split else None])
        # 쪼갬: 같은 개별이 둘 이상의 종합 항목에 붙으면 접는다
        folded, seen = [], {}
        for g in groups:
            if g[5]:   # `분리 — D<n>` — 닫는 결정이 쪼갠 것이라 접지 않는다(D153)
                folded.append(g)
                continue
            hit = next((folded[seen[s]] for s in g[1] if s in seen), None)
            if hit is not None:
                problems.append(("쪼갬", path.name,
                                 f"{g[0]} — {hit[0]}과 같은 개별({', '.join(sorted(set(g[1]) & set(hit[1])))})"
                                 f". 한 key로 접는다"))
                hit[0] += f"+{g[0]}"
                hit[1] = sorted(set(hit[1]) | set(g[1]))
                hit[2] = sorted(set(hit[2]) | set(g[2]))
                hit[4] = hit[4] or g[4]
                hit[5] = hit[5] or g[5]
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
                           "·".join(re.findall(r"D\d+", closed.group(1))) if closed else None, None])
        for ident, srcs, secs, decl, closed, _split in folded:
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
    print(f"    닫힘  {len(closed)}" + (f" — {', '.join(sorted({d for k in closed for d in k['closed'].split('·')}, key=lambda x: int(x[1:])))}" if closed else ""))
    print(f"    열림  {len(openk)}")
    outside = [k for k in keys if k["scope"] == "밖"]
    out_closed = [k for k in outside if k["closed"]]
    print(f"  범위 밖 (G3 목록으로) 총 {len(outside)} — 닫힘 {len(out_closed)}"
          + (f"({', '.join(sorted({d for k in out_closed for d in k['closed'].split('·')}, key=lambda x: int(x[1:])))})" if out_closed else "")
          + f" · 열림 {len(outside) - len(out_closed)} — 안의 수에 더하지 않는다(D152·D153)")
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
    하지 않는가(D152), 출처 없는 것을 세지 않는가, 쪼개진 것을 둘로 세지 않는가,
    밖 key의 닫힘을 안으로 세지 않는가(D191 — 밖은 열림/닫힘을 갈라 세되 안에 더하지 않는다).
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
        outside = [k for k in got["keys"] if k["scope"] == "밖"]
        out_closed = [k for k in outside if k["closed"]]
        kinds = sorted({p[0] for p in got["problems"]})
        # 밖은 기대에 없으면 0이어야 한다 — 밖 key가 있는 반례는 열림/닫힘을 둘 다 적는다(D191).
        ok = (len(inside) == exp["inside"] and len(closed) == exp["closed"]
              and len(inside) - len(closed) == exp["open"]
              and len(outside) == exp.get("outside", 0)
              and len(out_closed) == exp.get("outside_closed", 0)
              and kinds == sorted(exp["problems"]))
        why = re.sub(r"^# 합성 종합 — ", "", md.read_text(encoding="utf-8").split("\n")[1])
        detail = (f"안{len(inside)} 닫{len(closed)} 열{len(inside)-len(closed)} "
                  f"밖{len(outside)} 밖닫{len(out_closed)} {kinds or ''}")
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
    for sec, _ in ASSIGNED_STARTS:
        section_text(sec)
    checks.append(("쌍 16의 배정 절이 prd.md에 있다", True))
    # 3차 라운드의 규칙: 쌍의 이력은 닫은 D를 들고, '볼 것'은 결정을 다시 묻지 않는다.
    # `\b`는 한글 앞에서 맞지 않는다("D166이" — 둘 다 \w). D139 검사기와 같은 패턴을 쓴다.
    no_d = [p["id"] for p in PAIRS if not re.search(r"(^|[^A-Za-z0-9])D\d+([^0-9]|$)", p["history"])]
    checks.append((f"모든 쌍의 이력이 D 번호를 인용한다" + (f" — 없는 쌍 {no_d}" if no_d else ""), not no_d))
    # 입력 해시가 입력에 반응하는가 — 반응하지 않는 해시는 D151(b)를 지키지 못한다.
    h0 = input_hash()
    PAIRS[0]["ask"] += " "
    h1 = input_hash()
    PAIRS[0]["ask"] = PAIRS[0]["ask"][:-1]
    checks.append(("입력 해시가 쌍 목록의 한 글자 변화에 반응한다", h0 != h1 and h0 == input_hash()))

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
    ap.add_argument("--input-hash", action="store_true", help="리뷰어 입력(쌍 목록·질문·배정)의 해시만 — D151(b)")
    args = ap.parse_args()

    if args.input_hash:
        print(input_hash())
        return 0

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
