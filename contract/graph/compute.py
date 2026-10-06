#!/usr/bin/env python3
"""contract/graph — §2.2–2.3 컴포넌트·시스템 그래프 계약의 기대값 계산기 (G0).

    python3 contract/graph/compute.py            # expected.json 재생성
    python3 contract/graph/compute.py --check    # CI

**순수 구조 계약**이라 `input.json` 하나로 전제가 완결된다(§2.9). 바이트코드가 아니라
**클래스 그래프**가 입력이다 — §2.2가 고정하는 것은 지표 공식이 아니라(그건 ArchUnit
`ArchitectureMetrics`가 낸다, D3) 그 앞의 **전처리**이기 때문이다: 무엇이 노드이고,
무엇을 접고, 무엇을 빼는가.

입력 모양 둘:
  `classes`     — 클래스와 그 사이 간선. 컴포넌트 전략(`auto` 등)이 여기서 돈다.
  `components`  — 컴포넌트 수준 간선을 바로 준다. Lakos 검산처럼 전략이 논점이 아닐 때.

산술(§2.5·D115): 도달 집합·개수는 정수, `I`·`A`·`D`는 정확 유리수, `NCCD`는 `log₂`가
무리수라 34자리 HALF_EVEN으로 낸 뒤 마지막에 한 번만 반올림한다(D121).
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CASE_DIR.parent / "tools"))
import exact  # noqa: E402

GENERATED_BY = "contract/graph/compute.py"
EXTERNAL = "external"


# --------------------------------------------------------------------------
# §2.2 컴포넌트 전략
# --------------------------------------------------------------------------

def longest_common_prefix(packages: list[str]) -> list[str]:
    if not packages:
        return []
    split = [p.split(".") for p in packages]
    prefix: list[str] = []
    for parts in zip(*split):
        if len(set(parts)) == 1:
            prefix.append(parts[0])
        else:
            break
    return prefix


def resolve_auto(packages: list[str], weights: dict[str, int],
                 split_share: Fraction) -> tuple[dict[str, str], dict]:
    """§2.2 `auto` — 최장 공통 접두어 아래 첫 레벨. 자식 1개면 하향,
    루트의 전체 **클래스 수**의 `split_share`(60%)를 넘는 자식은 추가 분할(D130),
    다중 루트는 루트별. 분할은 **한 번**이다 — 루트 아래 한 단계에서 한 번 쪼개고
    손자는 다시 보지 않는다(D177). 재귀는 N을 깊은 분포에 의존하게 해 이동마다
    `context_changed`(D175)가 늘고, 1회는 결과가 예측 가능하다. 더 고운 경계는
    `depth:<n>`·`module`의 자리다.
    """
    roots: dict[str, list[str]] = {}
    for p in packages:
        roots.setdefault(p.split(".")[0], []).append(p)

    notes: list[str] = []
    if len(roots) > 1:
        notes.append(f"다중 루트 {sorted(roots)} — 루트별로 따로 접는다")

    mapping: dict[str, str] = {}
    for root in sorted(roots):
        group = roots[root]
        prefix = longest_common_prefix(group)
        while True:
            depth = len(prefix)
            children: dict[str, list[str]] = {}
            for p in group:
                parts = p.split(".")
                children.setdefault(".".join(parts[:depth + 1]), []).append(p)
            if len(children) == 1 and depth < max(len(p.split(".")) for p in group) - 1:
                # 자식이 하나면 컴포넌트가 하나가 되어 아무것도 나누지 못한다 — 한 칸 내린다.
                prefix = next(iter(children)).split(".")
                notes.append(f"자식 1개 — `{'.'.join(prefix)}` 로 하향")
                continue
            break

        total = sum(weights[p] for p in group)
        for child, members in sorted(children.items()):
            weight = sum(weights[p] for p in members)
            share = Fraction(weight, total)
            if share > split_share and len(members) > 1:
                # 한 자식이 전체의 60%를 넘으면 컴포넌트가 사실상 하나다 — 그 아래를 한 번 더 쪼갠다.
                notes.append(f"`{child}` 가 클래스 {weight}/{total} (> {split_share}) — 추가 분할")
                depth = len(child.split(".")) + 1
                for p in members:
                    mapping[p] = ".".join(p.split(".")[:depth])
            else:
                for p in members:
                    mapping[p] = child
    return mapping, {"notes": notes}


def resolve_components(inp: dict, packages: list[str],
                       weights: dict[str, int]) -> tuple[dict[str, str], dict]:
    strategy = inp["component"]["strategy"]
    if strategy == "auto":
        share = Fraction(str(inp["component"].get("split_share", "0.6")))
        mapping, info = resolve_auto(packages, weights, share)
        info["strategy"] = "auto"
        info["split_share"] = share
        return mapping, info
    if strategy.startswith("depth:"):
        depth = int(strategy.split(":")[1])
        return ({p: ".".join(p.split(".")[:depth]) for p in packages},
                {"strategy": strategy})
    if strategy == "module":
        return (dict(inp["component"]["module_of"]), {"strategy": "module"})
    raise ValueError(f"알 수 없는 전략: {strategy}")


# --------------------------------------------------------------------------
# §2.2 Martin · §2.3 Lakos
# --------------------------------------------------------------------------

def tarjan_scc(nodes: list[str], edges: set[tuple[str, str]]) -> list[list[str]]:
    """§2.2 순환 = Tarjan SCC. 결정적이도록 노드·이웃을 정렬해 돈다."""
    graph = {n: sorted(t for s, t in edges if s == n and t != n) for n in nodes}
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    result: list[list[str]] = []
    counter = [0]

    def strong(v: str) -> None:
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on_stack.add(v)
        for w in graph.get(v, []):
            if w not in index:
                strong(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            group = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                group.append(w)
                if w == v:
                    break
            result.append(sorted(group))

    for n in sorted(nodes):
        if n not in index:
            strong(n)
    return sorted((g for g in result if len(g) > 1), key=lambda g: g[0])


def reachable(node: str, edges: set[tuple[str, str]], nodes: list[str]) -> set[str]:
    """전이적 도달 + 자기 자신(§2.3 CCD의 정의)."""
    seen = {node}
    stack = [node]
    adjacency = {n: {t for s, t in edges if s == n} for n in nodes}
    while stack:
        current = stack.pop()
        for nxt in adjacency.get(current, ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def generate_components(spec: dict) -> dict:
    """41개를 손으로 나열하지 않기 위한 압축 표기. 모양이 결정적이라 감사할 수 있다.

    `chain: n`        c01 -> c02 -> ... -> cn  (도달 = n-i+1)
    `isolated: m`     i01..im                  (도달 = 1)
    `attached: [...]` 지정한 노드 하나에 붙는 노드 (도달 = 1 + 그 노드의 도달)
    """
    nodes, edges = [], []
    chain = int(spec.get("chain", 0))
    for i in range(1, chain + 1):
        nodes.append(f"c{i:02d}")
        if i > 1:
            edges.append([f"c{i - 1:02d}", f"c{i:02d}"])
    for i in range(1, int(spec.get("isolated", 0)) + 1):
        nodes.append(f"i{i:02d}")
    for att in spec.get("attached", []):
        nodes.append(att["name"])
        edges.append([att["name"], att["to"]])
    return {"nodes": nodes, "edges": edges}


def system_of(spec: dict) -> dict:
    """노드·간선 명세 하나의 시스템 수(N·CCD·NCCD) — D183 비교 케이스가 두 그래프에 쓴다."""
    if "generate" in spec:
        spec = generate_components(spec["generate"])
    nodes = sorted(spec["nodes"])
    edges = {(e[0], e[1]) for e in spec["edges"]}
    n = len(nodes)
    ccd = sum(len(reachable(x, edges, nodes)) for x in nodes)
    balanced = exact.irrational(lambda: (Decimal(n + 1) * exact.log2(Decimal(n + 1)) - Decimal(n)))
    return {"identifiers": nodes, "components": n, "CCD": ccd,
            "NCCD": exact.round_half_even(exact.irrational(lambda: Decimal(ccd) / balanced), 2)}


def run_nccd_compare(inp: dict) -> dict:
    """§5.3·D183 — N이 같을 때 'NCCD 증가 > 5%'는 정수 비교 `20·CCD_head > 21·CCD_base`로 환원된다.

    분모 `(N+1)·log₂(N+1) − N`이 약분되므로 무리수 사이의 비교가 아니다. 경계(정확히 5%)를 양쪽에서
    밟는다 — `head_at_threshold`는 21/20 그 자체라 '>'가 거짓, `head_over_threshold`는 참. 2자리로
    직렬화된 NCCD를 다시 읽어 비교하면 어느 쪽인지 갈릴 수 있다 — 그것을 `display_ratio_would_say`로 함께
    인쇄한다(계약은 그것을 읽지 않는다). 식별자 집합이 다르면 비교가 없다(D175)."""
    base = system_of(inp["compare"]["base"])
    out_variants, assertions = {}, {}
    for name in ("head_at_threshold", "head_over_threshold"):
        head = system_of(inp["compare"][name])
        same = head["identifiers"] == base["identifiers"]
        over = (20 * head["CCD"] > 21 * base["CCD"]) if same else None
        out_variants[name] = {
            "components": head["components"], "CCD": head["CCD"], "NCCD": head["NCCD"],
            "same_identifier_set": same,
            "ratio_exact": Fraction(head["CCD"], base["CCD"]),
            "nccd_increase_over_5pct": over,
            "display_ratio_would_say": (head["NCCD"] / base["NCCD"] > Decimal("1.05")),
        }
    assertions["identifier_sets_equal"] = all(v["same_identifier_set"] for v in out_variants.values())
    assertions["at_threshold_is_not_over"] = out_variants["head_at_threshold"]["nccd_increase_over_5pct"] is False
    assertions["over_threshold_is_over"] = out_variants["head_over_threshold"]["nccd_increase_over_5pct"] is True
    assertions["threshold_is_twenty_one_over_twenty"] = out_variants["head_at_threshold"]["ratio_exact"] == Fraction(21, 20)
    return {"case": inp["case"], "contract_refs": inp["contract_refs"], "what_this_pins": inp["what_this_pins"],
            "base": base, "variants": out_variants, "assertions": assertions}


def build_expected(inp: dict) -> dict:
    if "compare" in inp:
        return run_nccd_compare(inp)
    out: dict = {
        "case": inp["case"],
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
    }

    if "classes" in inp:
        classes = inp["classes"]
        packages = sorted({c["package"] for c in classes})
        weights = {p: sum(1 for c in classes if c["package"] == p) for p in packages}
        mapping, info = resolve_components(inp, packages, weights)
        info["split_share_basis"] = "class_count"
        out["component_strategy"] = info
        out["package_to_component"] = {p: mapping[p] for p in packages}

        by_name = {c["name"]: c for c in classes}
        component_of = {c["name"]: mapping[c["package"]] for c in classes}

        # §2.2 — 외부 타입 간선은 `external` 의사 노드로 **접어 기록하되**
        # Ca/Ce/I/A/D·CCD에서는 **제외**한다. 기록하지 않으면 "무엇을 뺐는지"를
        # 재현할 수 없고, 빼지 않으면 우리 것이 아닌 결합이 지표에 섞인다.
        class_edges, external_edges = set(), []
        for c in classes:
            for target in c.get("depends_on", []):
                if target in by_name:
                    class_edges.add((c["name"], target))
                else:
                    external_edges.append({"from": c["name"], "to": target})

        component_edges = {(component_of[s], component_of[t])
                           for s, t in class_edges if component_of[s] != component_of[t]}
        nodes = sorted(set(mapping.values()))
        abstract = {n: 0 for n in nodes}
        total = {n: 0 for n in nodes}
        for c in classes:
            comp = component_of[c["name"]]
            total[comp] += 1
            if c.get("abstract"):
                abstract[comp] += 1
        out["class_edge_count"] = len(class_edges)
        out["external_edges"] = sorted(external_edges, key=lambda e: (e["from"], e["to"]))
        out["external_included_in_metrics"] = False
    else:
        spec = inp["components"]
        if "generate" in spec:
            spec = generate_components(spec["generate"])
            out["generated_from"] = inp["components"]["generate"]
        nodes = sorted(spec["nodes"])
        component_edges = {(e[0], e[1]) for e in spec["edges"]}
        abstract = {n: int(inp["components"].get("abstract", {}).get(n, 0)) for n in nodes}
        total = {n: int(inp["components"].get("total", {}).get(n, 1)) for n in nodes}
        out["component_strategy"] = {"strategy": "given"}

    # Martin (§2.2)
    components = []
    for n in nodes:
        ca = sum(1 for s, t in component_edges if t == n)
        ce = sum(1 for s, t in component_edges if s == n)
        # D179 — 비율은 정수(Ca·Ce·클래스 수)에서 정확 유리수로. 라이브러리의 double은 쓰지 않는다.
        # D180 — external을 접은 뒤 이웃이 없으면(Ca+Ce = 0) I·D는 null + reason, A는 값이다.
        i = Fraction(ce, ca + ce) if (ca + ce) else None
        a = Fraction(abstract[n], total[n]) if total[n] else None   # D181 — 분모는 모든 클래스
        d = abs(a + i - 1) if (a is not None and i is not None) else None
        entry = {"id": n, "Ca": ca, "Ce": ce, "I": i, "A": a, "D": d, "class_count": total[n]}
        if (ca + ce) == 0:
            entry["reason"] = "isolated_component"
        components.append(entry)
    out["components"] = components

    cycles = tarjan_scc(nodes, component_edges)
    out["cycles"] = [{"id": f"cyc-{k + 1}", "size": len(g), "members": g}
                     for k, g in enumerate(cycles)]

    # Lakos (§2.3)
    n_count = len(nodes)
    ccd = sum(len(reachable(n, component_edges, nodes)) for n in nodes)
    balanced = exact.irrational(
        lambda: (Decimal(n_count + 1) * exact.log2(Decimal(n_count + 1)) - Decimal(n_count)))
    acd = Fraction(ccd, n_count) if n_count else None
    racd = Fraction(ccd, n_count * n_count) if n_count else None
    nccd = exact.round_half_even(exact.irrational(lambda: Decimal(ccd) / balanced), 2)
    out["system"] = {
        "components": n_count,
        "CCD": ccd,
        # 정확값. 임계 비교는 반올림 전 값으로 한다(§2.5 산술 계약).
        "ACD": acd,
        "RACD": racd,
        # log₂는 유리수로 닫히지 않는다 — 34자리에서 파생하고 마지막에 한 번 반올림(D121).
        "CCD_balanced": exact.round_half_even(balanced, 2),
        "NCCD": nccd,
        # 표시 스케일은 D155-1(§2.5): 비율(RACD) 4자리, Lakos 절대량(ACD·CCD_balanced·NCCD) 2자리.
        # 표시용이며 비교에 쓰지 않는다 — 비교는 위의 정확값으로 한다.
        "display": {
            "ACD": exact.round_half_even(Decimal(acd.numerator) / Decimal(acd.denominator), 2)
                   if acd is not None else None,
            "RACD": exact.round_half_even(
                Decimal(racd.numerator) / Decimal(racd.denominator), 4)
                    if racd is not None else None,
            "CCD_balanced": exact.round_half_even(balanced, 2),
            "NCCD": nccd,
        },
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="§2.2–2.3 그래프 계약")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("cases", nargs="*")
    args = ap.parse_args()

    dirs = sorted(p.parent for p in CASE_DIR.glob("*/input.json"))
    if args.cases:
        dirs = [p for p in dirs if p.name in set(args.cases)]

    failures = 0
    for case_dir in dirs:
        inp = json.loads((case_dir / "input.json").read_text(encoding="utf-8"))
        text = exact.finish(build_expected(inp), GENERATED_BY)
        target = case_dir / "expected.json"
        if args.check:
            current = target.read_text(encoding="utf-8") if target.exists() else None
            if current == text:
                print(f"ok    {case_dir.name}")
            else:
                failures += 1
                print(f"FAIL  {case_dir.name}: expected.json "
                      f"{'없음' if current is None else '다름'} — §2.2–2.3 그래프 계약")
        else:
            target.write_text(text, encoding="utf-8")
            print(f"wrote {case_dir.name}/expected.json")

    if failures:
        print(f"\n{failures}개 실패. 의도한 변경이면 fixture_change를 같은 커밋에(§2.9·D129).")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
