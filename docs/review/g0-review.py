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
    # 4차 라운드(D151 — 입력을 바꾼 라운드). 쌍 1–14의 이력에 결정 판 열둘(D179–D227)을 더하고 '볼 것'을
    # **그 결정이 이웃 절에 내려갔는가**로 바꿨다 — 3차가 찾은 모양의 다수가 그것이었다. 쌍 15–18은 열두 판이 만든
    # 접점, 쌍 19는 표 셋의 덮음(소유자 추가 — 표를 적은 판이 자기 §7 예시에서 표를 어긴 일이 두 번).
    # 3차의 기록은 이 아래 이력과 '볼 것'의 출처다; 3차 입력 해시는 PREVIOUS_INPUT_HASHES에.
    {
        "id": 1,
        "title": "모집단 정의 ↔ 그 모집단을 쓰는 렌즈",
        "sections": ["2.5", "3.1", "3.2", "3.3"],
        "history": "충돌 1의 자리(§0-4). 그 뒤 D168(기록은 <field>.<population> 두 단계, 뜻은 소속), D169(순위 지름길은 렌즈별 — F는 지시변수 먼저), D172(렌즈 = H·Dx·F, composite는 렌즈가 아니다). 그 뒤 D206(언어 하위 모집단 < 20이면 그 언어의 H는 null)·D213(finding 선정 = lens_pct ≥ 0.75; anchor_class는 high·medium 둘)·D216(§7의 null 기록은 (필드, 모집단)마다)·D218·D220(F > 0은 전부 investigate_first, 순위는 priority).",
        "ask": "선정 규칙(D213)과 anchor_class의 두 값이 §5.4 캠페인·§5.7 touched_legacy_findings·§7.1 렌더러에 내려갔는가. 언어 하위 모집단의 H null(D206)이 §5.3 eligible_n(D215)과 같은 분모를 말하는가. 결정을 다시 묻지 말고 결정이 이웃 절에 내려갔는지를 보라.",
    },
    {
        "id": 2,
        "title": "시간 앵커·창 ↔ 시간을 쓰는 측정 ↔ F의 P90",
        "sections": ["2.7", "2.1", "3.3"],
        "history": "충돌 2의 자리(§0-4). D137(90일 지표는 창 안)·D146–D150(파일별 마지막 커밋 맵이 id 입력, 창 밖 한정 걷기, shallow는 age_unknown, D137의 근거 교체)·D174(W는 측정의 집합 — §5.5의 first-parent와 다른 질문). 그 뒤 D184('일'은 초/86400의 유리수)·D203(한정 걷기 — 프런티어에서, 지배되지 않는 접촉 중 시각 최대)·D204(age_unknown은 경계에 닿은 파일만, history_complete는 걷기의 함수)·D205(맵의 값)·D217(truncated = 상한이 잘라낸 비머지 커밋).",
        "ask": "'지배되지 않는 접촉'(D203)이 §5.5 succession·§5.6 한정 blame의 걷기와 같은 말인가. history_complete(D204)가 §5.4 앵커 봉인·§6.3 검증 트리와 또 어긋나는가. 맵의 값(D205 — 정하지 못한 셋은 null, invalid_metadata는 SHA)이 §7 reproduce·§2.9 행과 같은가.",
    },
    {
        "id": 3,
        "title": "analysis_input_id ↔ 캐시 키 ↔ '두 머신 바이트 동일'",
        "sections": ["2.8", "4.5", "2.9"],
        "history": "D87·D111·D138. 그 뒤 D154(비교 대상 = scanned_at·classes_reproduction_inputs를 뺀 전부)·D155(스케일 표)·D156(분수 파라미터는 문자열)·D157(시각은 Z)·D158(reproduce의 필드는 세 종류)·D159(캐시 키 = §2.8 입력의 사영)·D160(people은 id 입력). 그 뒤 D182(output.irrational 한 키)·D186(reproduce의 자리 없던 값 넷)·D192–D195(세 캐시의 사영)·D210(source_scope)·D223(repository_state_id = HEAD 경로 × 작업트리 내용 − .jqradar/).",
        "ask": "§2.8 (i)의 이름이 §4.5 세 캐시 키·§7의 [id] 표시와 뜻까지 맞는가(자기 반례는 이름만 대조한다). repository_state_id(D223)·source_scope(D210)·내용 ID의 '추적/미추적 무관'이 §5.4 앵커·§6.3 검증 트리에서 같은 집합을 말하는가. reproduce 예시만으로 id를 다시 계산할 수 있는가.",
    },
    {
        "id": 4,
        "title": "산술 계약 ↔ composite ↔ 임계 비교",
        "sections": ["2.5", "3.6", "3.7"],
        "history": "D121(composite는 전정밀 가중합). 그 뒤 D169·D171(interpretation은 lens_pct의 함수 — null이면 null + reason)·D172(composite에는 백분위·interpretation이 없다)·D173(population_note는 confidence와 같은 시험). 그 뒤 D179–D183(산술 — ArchUnit에서는 정수만, log₂는 √와 같은 규칙, NCCD는 정수 비교)·D215(top-decile = lens_pct ≥ 0.90).",
        "ask": "top-decile(D215)·investigate_first·anchor_class high가 모든 자리에서 같은 값(≥ 0.90)·같은 비교(반올림 전 정확값)인가. 직렬화된 값을 다시 읽어 비교하는 경로가 어디에 남았는가. composite가 렌즈가 아니라는 것(D172)이 §5.4·§7.1과 또 어긋나는가.",
    },
    {
        "id": 5,
        "title": "CPD 클러스터 ↔ 파일×클러스터 수준 새 중복 ↔ twins",
        "sections": ["2.6", "5.2", "2.1"],
        "history": "D40. 그 뒤 D165(새 중복은 파일×클러스터 수준·새 발생 수 = max(0, HEAD − BASE)·서로 다른 파일 ≥ 2·게이트 손잡이 min_tokens)·D166(self_dup_tokens는 한 파일에만 있는 클러스터의 것)·D178(§6.3도 그 손잡이를 가리킨다). 그 뒤 D187(토큰은 정규화 후 스트림)·D199·D200(쌍 측정은 두 수, 한쪽 0 ⇔ 다른 쪽 0)·D221(새 발생은 라인 구간 겹침 — ~~D165~~의 세는 구절을 대체).",
        "ask": "라인 구간 겹침(D221)이 §5.5 succession의 토큰 비율(≥ 80% / ≥ 20% / ≥ 50%)·§6.3 BLOCK이 세는 것과 같은 단위인가 — 1차 리뷰어 5가 지목한 자리를 두 번째로 묻는다. 두 수(D199)가 §6.3 합격('target_pairs 전부 0')·§5.5 Dx 대응(D214)에 내려갔는가.",
    },
    {
        "id": 6,
        "title": "컴포넌트 전략 ↔ Lakos ↔ Architecture Context",
        "sections": ["2.2", "2.3", "3.4"],
        "history": "D130(60%는 클래스 수). 그 뒤 D170(적격 main 소스 정의, 클래스 없는 소스는 fan_in null·reason no_bytecode·컴포넌트 null)·D175(컴포넌트 식별자 집합이 바뀌면 context_changed)·D177(auto 분할은 1회). 그 뒤 D179–D181(I·A·D는 정수에서, Ca+Ce = 0은 isolated_component, A의 분모는 모든 클래스)·D211(클래스 쪽 배제 = 소스 배제의 전파, 최상위 타입으로 접기)·D222(fan_in = 밖의 파일 수, 같은 접기).",
        "ask": "D211·D222의 접기(클래스 → 최상위 타입)와 D197의 순환 정체성(SCC 멤버 **클래스** 집합)이 §2.3 Lakos·§5.5에서 같은 단위를 쓰는가. isolated_component(D180)가 §3.4·§5.3 SCC 행과 또 어긋나는가.",
    },
    {
        "id": 7,
        "title": "파일 쌍 ↔ Hidden Coupling ↔ 커밋 거칠기",
        "sections": ["2.4", "3.5", "2.7"],
        "history": "D134. 그 뒤 D164(shared는 W 안, tc ≤ 1 불변식)·D167(정렬 키)·D176(그래프 밖 쌍은 판정하지 않음 — static_dependency null + reason, 정렬 false·true·null). 그 뒤 D190(클래스 없는 파일이 든 쌍은 no_bytecode)·D201(쌍 집합 = main ∪ 테스트, 분모를 행에)·D202(a < b, 배열 정렬 키)·D213(Hidden Coupling 지도 finding = false인 보고 쌍마다)·D227(원장 finding이 아니다).",
        "ask": "Hidden Coupling이 지도 finding이고 원장 밖(D227)이라는 것이 §6.2 MCP·§7.1 A5·§5.4 캠페인 범위·§5.7과 맞는가. tc ≤ 1(D164)이 테스트 파일의 분모(D201)에서도 서는가.",
    },
    {
        "id": 8,
        "title": "저자 사실 ↔ 저자 필드 읽기 ↔ people 정책",
        "sections": ["2.1", "2.7", "4.3"],
        "history": "D48·D135. 그 뒤 D160(people.attribution·매핑 해시는 id 입력, reproduce.people)·D161(저자 사실은 people.json, k 하한은 팀 집계에)·D162(off는 셋으로 닫힘)·D163(author_id는 매핑 파일의 키). 그 뒤 D195(저자 유래 캐시 키는 commit_list_sha256, 부재 검사는 build/jqradar/까지)·D219(팀의 수는 report의 measures에 — 라벨은 people.json).",
        "ask": "team_count가 report의 measures에 있다(D219)는 것이 D126·§6.2 MCP(저자 데이터는 individual만)·§7.1의 저자 범위와 같은 선인가. 캐시 디렉터리의 부재 검사(D195)가 §6.6 샌드박스 산출물에도 닿는가.",
    },
    {
        "id": 9,
        "title": "토크나이저 ↔ 토큰을 세는 모든 필드",
        "sections": ["2.6", "2.1", "5.2"],
        "history": "§2 내부 쌍 — 3차에서 사실상 아무도 보지 못했다(기억에 기댄 판정). 그 뒤 D187(토큰을 세는 모든 수는 정규화 후 스트림, dup_extent ≤ 1 불변식; 토크나이저 실측은 G1의 확인 픽스처).",
        "ask": "D187이 내려갔는가 — 토큰을 세는 모든 수가 정규화 후 스트림이라는 것이 §2.6·§5.2(min_tokens)·§5.5 succession의 토큰 비율·§7 fixture_change 예시에 같은 말로 있는가. 답의 근거로 `contract/cpd/`의 expected.json 줄을 인용한다.",
    },
    {
        "id": 10,
        "title": "쌍별 투영의 방향 ↔ 대칭이어야 하는 것",
        "sections": ["2.6", "2.1", "3.5"],
        "history": "§2 내부 쌍 — 1차 리뷰어 1 유보 (a). 그 뒤 D199·D200(쌍 측정은 두 수 — a_dup_tokens·b_dup_tokens)·D202(a < b, 배열 정렬 키 표 D202-1).",
        "ask": "두 수·a < b·D202-1이 §6.3 합격·§7.1 렌더러·§5.5 Dx 대응에 내려갔는가. 투영과 무관해야 하는 것(twins·active_twin_ratio)을 어디서 한쪽 수만으로 읽는가.",
    },
    {
        "id": 11,
        "title": "단위의 끝 — 일·클래스·자기 간선",
        "sections": ["2.1", "2.2", "2.7"],
        "history": "§2 내부 쌍 — 1차 유보 둘. 그 뒤 D184('일' = 초/86400의 유리수, 표시 2자리; chg_days는 달력 일)·D222(fan_in은 접힌 최상위 타입 단위, 같은 파일 안·external은 세지 않는다).",
        "ask": "'일'과 '파일 단위'가 다른 절의 같은 낱말과 같은 뜻인가(§2.7 authors_window_days, §5.4 debt_age_days, §5.5 국소 재스캔의 '파일'). 같은 낱말이 다른 단위로 쓰인 자리가 남았는가.",
    },
    {
        "id": 12,
        "title": "측정의 집합 ↔ 전이의 후보 ↔ 검증 트리",
        "sections": ["2.7", "5.5", "6.3"],
        "history": "D174 — W와 first-parent는 다른 질문. 그 뒤 D196(검증의 순환 합격에도 D175의 가드)·D223(repository_state_id의 집합)·D224(merge_drift는 표기, 원인 넷, 판정 순서)·D225(validation_tree_unreachable). 발견이 §5.5·§6.3에만 걸리면 범위 밖(D152).",
        "ask": "원인표의 판정 순서(D224)와 merge_drift의 조건(PR이 바꾼 경로)이 §6.3 검증·§5.7·§7 원장 행에 내려갔는가. validation_tree_unreachable(D225)이 §5.5의 상태 어휘·C3 Lost findings와 같은 자리인가.",
    },
    {
        "id": 13,
        "title": "컴포넌트 식별자 ↔ 게이트 ↔ 원장 정체성",
        "sections": ["2.2", "5.3", "5.5"],
        "history": "D175 — 식별자 집합이 바뀌면 SCC·NCCD 둘 다 context_changed. 그 뒤 D196(검증도 not_validated: context_changed)·D197(순환 정체성 = 클래스 집합)·D198(§7 gate SCC 행)·D226(앵커 재빌드 불가면 생성 거부). 발견이 §5.3·§5.5에만 걸리면 범위 밖(D152).",
        "ask": "클래스 집합 정체성(D197)이 앵커 재빌드 불가(D226 — anchor_scan.bytecode: unavailable)에서 무엇이 되는가. 게이트(context_changed)·검증(not_validated)·원장(계보)의 세 답이 같은 이동에 대해 서로 맞는가.",
    },
    {
        "id": 14,
        "title": "판정 없음의 전파",
        "sections": ["2.4", "3.5", "3.7", "7.1"],
        "history": "D176·D171·D170 — '판정 없음'의 세 자리. 그 뒤 D188(reason 사전 한 곳 — 오는 자리 열)·D191(렌즈 없는 finding은 필드 부재)·D207(unsupported_language)·D208(files_examined)·D215(eligible_n).",
        "ask": "'판정 없음'의 모양 넷 — null + reason(D188), 필드 부재(D191), 본 수·못 본 수(D208·D215), context_changed(D175) — 을 자리마다 하나의 규칙으로 골랐는가, 같은 상황에 둘이 쓰인 자리가 있는가. 사전의 '오는 자리' 열이 스키마의 부분집합과 같은 표인가.",
    },
    {
        "id": 15,
        "title": "소스 범위 ↔ 클래스 범위 ↔ id",
        "sections": ["2.1", "2.2", "2.8"],
        "history": "4차 새 쌍 — 열두 판의 접점. D210(source_scope, [id])·D211(클래스 쪽 배제 = 소스 배제의 전파, unmapped_classes)·D212(origin)·D222(fan_in의 접기).",
        "ask": "두 범위가 같은 접기·같은 경계를 말하는가 — 소스에서 빠진 파일의 클래스가 그래프에도 없고 fan_in의 의존자로도 세지 않는가. convention의 셋째 세트(범위 밖)가 쌍의 집합(D201)·history의 테스트 집합과 맞는가.",
    },
    {
        "id": 16,
        "title": "원인표의 판정 순서 ↔ 원장·검증 케이스",
        "sections": ["2.9", "5.5", "6.3"],
        "history": "4차 새 쌍. D224(원인 넷·판정 순서·merge_drift는 표기)·D225(validation_tree_unreachable)·§2.9 ledger/·validation/ 행의 '각 1건'. §2.9를 걸쳐 열린 동안 범위 안(D152).",
        "ask": "§2.9가 요구하는 '각 1건' 케이스들이 판정 순서 아래서 서로 배타적으로 만들어질 수 있는가 — 한 합성 이력이 두 원인의 조건을 함께 만족하면 어느 것이 나오는가. merge_drift 표기가 lost_in_merge의 증거로만 쓰이는가.",
    },
    {
        "id": 17,
        "title": "'가릴 것이 없었다'의 세 표지",
        "sections": ["2.5", "5.3", "7"],
        "history": "4차 새 쌍. D215(eligible_n)·D208(files_examined·files_unmeasured)·D175(context_changed) — 게이트 행마다 '판정 없음'을 다르게 말한다. 정수 이름은 D155-1에.",
        "ask": "게이트의 다섯 행이 '가릴 것이 없었다'를 같은 모양으로 말하는가 — 어느 행은 수, 어느 행은 결과 어휘, 어느 행은 아무것도 없는가. §7 gate.json이 그 셋을 다 보여 주는가.",
    },
    {
        "id": 18,
        "title": "finding 선정 ↔ 캠페인 등록 ↔ anchor_class",
        "sections": ["2.5", "3.7", "5.4"],
        "history": "4차 새 쌍. D213(선정 = lens_pct ≥ 0.75, low는 죽은 어휘였다)·D214(Dx의 세 단위, 등록 단위는 원장 finding = 클러스터 × 파일)·D227(Hidden Coupling은 원장 밖).",
        "ask": "캠페인이 등록하는 집합이 선정 규칙과 같은가 — 지도에 없는 원장 finding, 원장에 못 드는 지도 finding이 생기는가. Dx의 1 : n이 §5.4 목표 수('high 20개')에 어떻게 들어가는가.",
    },
    {
        "id": 19,
        "title": "스키마가 베끼는 표 셋의 덮음",
        "sections": ["2.5", "7", "2.9"],
        "history": "4차 새 쌍(소유자 추가). 표를 적은 판이 자기 §7 예시에서 그 표를 어긴 일이 두 번 — D155-1(PR #50의 age_last_days·debt_age_days), D202-1(PR #54의 occurrences·teams). reason 사전(D188)이 셋째 표. 쌍 14는 사전의 자리를, 이 쌍은 세 표의 덮음을 본다.",
        "ask": "D155-1 스케일·D202-1 정렬·reason 사전이 §7의 모든 블록과 contract/schema/의 스키마에서 같은 집합인가 — 표에 있는데 아무 블록에도 안 나오는 이름, 블록에 있는데 표에 없는 이름. 답의 근거로 스키마 파일의 줄이나 린트 출력을 인용한다.",
    },
]

# 쌍 len(PAIRS)+1 = 자유(D151 그대로 — 각 모델이 목록 밖 절 둘을 **스스로** 고른다).
# 쌍 len(PAIRS)+2 = 배정(이번 라운드만의 덮기 — 아무도 출발하지 않은 절). 리뷰어 순서대로 하나씩.
FREE_PAIR = len(PAIRS) + 1
ASSIGNED_PAIR = len(PAIRS) + 2
ASSIGNED_STARTS = [
    ("5.1", "change.json 일곱 키 — smell_delta(D209)가 §5.3 새 P1 행의 입력이고 items의 여섯이 필수인 것이 §5.1 표와 맞는가"),
    ("5.6", "한정 blame — 한 번도 출발점이 아니었다; '매 스캔에서 blame 없음'과 캠페인 생성 시 1회가 D203의 걷기·D226의 생성 거부와 맞는가"),
    ("6.4", "재배치 — 리포 총 cx는 cx_method별(D207)이고 재배치 분모가 그것을 읽는가"),
    ("4.1", "모듈·입구 — source_scope는 입구가 만든다(D210·D212); core의 빌드 무지와 CLI·플러그인의 책임이 §4.1 표와 맞는가"),
    ("5.7", "변경 리포트와 원장의 연결 — touched_legacy_findings의 kind가 이제 셋뿐(D227)·anchor_class 두 값(D213)·D191·D214가 §5.7 문장과 맞는가 — 결정 넷이 닿았는데 출발점이었던 적이 없다"),
]
# 지난 라운드의 입력 해시 — 이번 입력이 그것들과 달라야 '입력을 바꾼' 라운드다(D151(b)). selftest가 본다.
PREVIOUS_INPUT_HASHES = {"3차": "pairs@816c35bfca1d"}

QUESTIONS = [
    "두 절이 같은 이름을 **다른 뜻**으로 쓰는가?  (n이 모집단인지 랭킹 집합인지 — 실제로 갈렸다, D116)",
    "한 절이 요구하는 것을 다른 절이 **불가능하게** 하는가?  (F의 모집단 — 실제로 그랬다, D24)",
    "두 절을 순서대로 실행하면 **정의되지 않은 상태**가 생기는가?  (validated 뒤 머지 전에 다른 PR이 먼저 머지되면 — D91·D99)",
    "한 절이 단언한 수·조건·예시 값이 그 절이 가리키는 픽스처나 §7 예시에서 **성립하는가**? — 답의 근거로 `expected.json`의 줄이나 계산기 출력을 **인용한다**.  (§2.9 cpd/ 행의 '20줄' — v3.10.11 보정; 3차 쌍 9는 기억에 기댔다)",
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
    # 절 번호 뒤는 공백이나 줄 끝 — `\\b`는 "2.5.1"(점 뒤)과 "2.5분포"(한글)를 잘못 가른다.
    pat_sub = re.compile(rf"^### {re.escape(number)}(?=\s|$)")
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


def _count_word(n: int) -> str:
    return {3: "세", 4: "네", 5: "다섯"}.get(n, str(n))


def show_pairs(full: bool) -> None:
    print(f"\n입력: {input_hash()}  — 기록 머리에 그대로 적는다(D151: 입력을 바꾼 라운드만 '연속'으로 센다)")
    print("\n당신만 할 수 있는 것 — 계약을 **쌍으로** 읽기")
    print("지금까지 실제로 난 충돌 넷은 전부 한 절 안에서는 보이지 않았고, 두 절을 함께 실행하려 할 때 드러났다.")
    print(f"쌍마다 아래 {_count_word(len(QUESTIONS))} 질문을 던진다:\n")
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
    print(f"쌍 {FREE_PAIR} — 목록에 들지 않은 절 둘을 **당신이 골라** 같은 질문을 던진다(D151). 배정하지 않는다 —")
    print("        1–3차에서 목록 밖이 생산적이었던 이유가 목록 작성자가 예견하지 못한 자리를 리뷰어가 스스로 골랐기 때문이다.")
    print(f"쌍 {ASSIGNED_PAIR} — 배정(이번 라운드만의 덮기). 리뷰어 순서대로 하나씩, 그 절에서 출발해 쌍을 만든다:")
    for i, (sec, why) in enumerate(ASSIGNED_STARTS, 1):
        print(f"        리뷰어 {i}: §{sec} — {why}")
    print(f"쌍 12·13과 쌍 {ASSIGNED_PAIR}의 발견은 §2.1–2.9를 인용하지 않으면 **범위 밖**이다(D152 — 세지 않고 버리지도 않는다, G3 목록으로 — 이제 생성된다).")
    print("쌍 16(§2.9를 걸친다)과 쌍 19(§2.5·§2.9)의 발견은 범위 안이다.")
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
| {FREE_PAIR} | (당신이 고른 쌍 — 목록 밖 절 둘, D151) |  |  |  |  |
| {ASSIGNED_PAIR} | (배정 — `--pairs`의 쌍 {ASSIGNED_PAIR}에서 당신 번호의 출발 절) |  |  |  |  |

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

기계 확인이 초록이어도, 위 쌍 {len(PAIRS)}개도, 전부 이 문서를 만든 도구가 정한 범위다. 여기 적어 두면 다음 라운드의 쌍 목록이 거기서 시작한다(D151 — 입력을 바꾸는 재료):
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
# 번호 뒤에 숫자만 아니면 된다 — `\\b`는 "### 발견 12번"처럼 한글이 붙으면 발견을 못 읽었다(같은 함정).
FINDING_HEAD_RE = re.compile(r"^### 발견 (\d+)(?!\d)")


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
        for lineno, line in enumerate(text.split("\n"), start=1):
            head = FINDING_HEAD_RE.match(line)
            if head:
                cur = f"{'R' if r.isdigit() else ''}{r}-{head.group(1)}"
                out[cur] = {"sections": [], "file": path.name, "line": lineno}
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
        groups = []   # (id, sources, sections, declared, closed, split, claim)
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
                           split.group(1) if split else None,
                           cells[1] if len(cells) > 1 else ""])
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
                           "·".join(re.findall(r"D\d+", closed.group(1))) if closed else None, None,
                           cells[1] if len(cells) > 1 else ""])
        for ident, srcs, secs, decl, closed, _split, claim in folded:
            computed = _scope_of(secs)
            if computed != decl:
                problems.append(("범위 어긋남", path.name,
                                 f"{ident} — 표는 '{decl}', 절 집합 {' '.join(secs)}로는 '{computed}'"))
            keys.append({"id": ident, "file": path.name, "sources": srcs,
                         "sections": secs, "scope": computed, "closed": closed,
                         "claim": claim, "round": synth.index(path) + 1,
                         "source_lines": [f"{individuals[k]['file']}:{individuals[k]['line']}" for k in srcs]})
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


# ── `--g3-list` — 범위 밖 key의 목록을 **생성**한다 (D152) ─────────────────────────────
#
# 범위 밖 key는 "세지 않고 버리지도 않는다"(D152) — G3 입장 조건(§6.3–6.6 교차 검토·값 층
# 픽스처)의 입력이 된다. 그 목록을 사람이 옮기면 status의 수처럼 옮기다 틀린다(140 → 142).
# 그래서 종합에서 계산해 쓰고, `check-all`이 생성기를 다시 돌려 파일과 diff 0을 확인한다.
G3_LIST = ROOT / "docs" / "review" / "g3-list.md"


def _natural(key: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", key)]


def g3_list_text(records_dir: Path = RECORDS) -> str:
    got = collect_keys(records_dir)
    out = [k for k in got["keys"] if k["scope"] == "밖"]
    open_ = sorted((k for k in out if not k["closed"]), key=lambda k: (k["round"], _natural(k["id"])))
    closed = sorted((k for k in out if k["closed"]), key=lambda k: (k["round"], _natural(k["id"])))
    rounds = {i + 1: name for i, name in enumerate(got["synth"])}

    def row(k, with_d=False):
        ident = k["id"].replace("(미부착)", "")
        claim = k["claim"].replace("\n", " ")
        cells = [f"`{ident}`", claim, " ".join(f"`{s}`" for s in k["sections"]),
                 " · ".join(k["source_lines"]), f"{k['round']}차"]
        if with_d:
            cells.append(k["closed"])
        return "| " + " | ".join(cells) + " |"

    lines = [
        "# G3 목록 — 범위 밖 발견 (D152)",
        "",
        "> **생성됨 — 손으로 고치지 않는다.** `python3 docs/review/g0-review.py --g3-list`가 종합 기록에서",
        "> 계산해 쓰고, `ci/check-all.sh`가 생성기를 다시 돌려 이 파일과 diff 0을 확인한다(`--g3-list --check`).",
        "> 바꾸려면 기록(종합의 표·개별 기록)을 고친다 — 이 파일은 사본이다.",
        "",
        "범위 밖 = 절 집합(개별 기록의 `절:`)에 §2.1–2.9가 하나도 없는 key(D152). **세지 않고 버리지도 않는다** — G0 #1의",
        "수에 닿지 않고, G3 입장 조건(§6.3–6.6 교차 검토·값 층 픽스처)의 입력이다. 닫힘 표시가 붙은 밖 key는 아래 따로 둔다",
        "(D153 — 표시는 기록의 것이고 수에 닿지 않는다).",
        "",
        "읽은 종합: " + ", ".join(f"{i}차 `{n}`" for i, n in rounds.items()),
        "",
        f"## 열린 것 — {len(open_)}",
        "",
        "정렬: 라운드 → key(자연 순서). 출처는 개별 기록의 `### 발견` 머리 줄.",
        "",
        "| key | 주장 | 절 집합 | 출처(기록:줄) | 라운드 |",
        "|---|---|---|---|---|",
        *[row(k) for k in open_],
        "",
        f"## 닫힌 것 — {len(closed)}",
        "",
        "| key | 주장 | 절 집합 | 출처(기록:줄) | 라운드 | 닫은 결정 |",
        "|---|---|---|---|---|---|",
        *[row(k, with_d=True) for k in closed],
        "",
    ]
    return "\n".join(lines)


def g3_list(check: bool) -> int:
    text = g3_list_text()
    if check:
        current = G3_LIST.read_text(encoding="utf-8") if G3_LIST.exists() else None
        if current == text:
            print(f"  ok   {G3_LIST.relative_to(ROOT)} — 생성기와 diff 0")
            return 0
        print(f"  BAD  {G3_LIST.relative_to(ROOT)} — " + ("없다" if current is None else "생성기 출력과 다르다(손으로 고쳤거나 기록이 바뀌었다 — `--g3-list`로 다시 쓴다)"))
        return 1
    G3_LIST.write_text(text, encoding="utf-8")
    print(f"wrote {G3_LIST.relative_to(ROOT)}")
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
    checks.append((f"쌍 {ASSIGNED_PAIR}의 배정 절이 prd.md에 있다", True))
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
    same_as = [r for r, h in PREVIOUS_INPUT_HASHES.items() if h == h0]
    checks.append((f"입력 해시({h0})가 지난 라운드의 입력과 다르다 — '입력을 바꾼' 라운드(D151(b))"
                   + (f" — 같은 라운드: {same_as}" if same_as else ""), not same_as))

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
        # `\b`는 한글 앞에서 맞지 않아("D206이") 인용을 조용히 건너뛰었다 — 착지 검사기와 같은 경계를 쓴다.
        dangling += [f"쌍{p['id']}:D{d}" for d in re.findall(r"(?<![A-Za-z0-9])D(\d+)(?![0-9])", blob)
                     if d not in have_d]
        dangling += [f"쌍{p['id']}:§{z}" for z in re.findall(r"§(0-\d+)", blob)
                     if z not in have_zero]
    # 머리말(QUESTIONS)의 인용도 같은 자리에서 본다 — 리뷰어가 가장 먼저 읽는 줄이다.
    qblob = " ".join(str(q) for q in QUESTIONS)
    dangling += [f"머리말:D{d}" for d in re.findall(r"(?<![A-Za-z0-9])D(\d+)(?![0-9])", qblob)
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
    ap.add_argument("--g3-list", action="store_true", help="범위 밖 key 목록 docs/review/g3-list.md를 생성한다(D152)")
    ap.add_argument("--check", action="store_true", help="--g3-list와 함께: 쓰지 않고 파일과 생성기 출력의 diff 0만 본다")
    args = ap.parse_args()

    if args.g3_list:
        return g3_list(check=args.check)

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
