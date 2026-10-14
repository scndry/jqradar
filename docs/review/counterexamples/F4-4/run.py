import copy
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# F4-4 — §2.7 `authors_window_days`의 설명("90일 지표가 실제로 본 일수", "10일 된 리포는 90일을 못 봤지만 잃은 것이 없다")과
# 같은 문장의 공식(`min(90, HEAD_TIME − 창의 가장 오래된 커밋 시각)`)이 다른 값을 낸다.
from datetime import datetime
from fractions import Fraction
history = load("history", "contract/history/compute.py")
inp = json.loads((ROOT / "contract" / "history" / "window-outside-last-commit-recovered" / "input.json").read_text(encoding="utf-8"))
tmp = tempfile.mkdtemp()
try:
    got = history.build_expected(inp, Path(tmp) / "repo")
    workdir = Path(tmp) / "repo2"
    history.build_repo(inp["repo"], workdir)
    commits = history.read_history(workdir)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
t = lambda c: int(datetime.fromisoformat(c["committer_time"]).timestamp())
head = t(commits[0])
first = min(t(c) for c in commits)
lower = head - int(inp["window"]["months"]) * history.MONTH_SECONDS
seen = Fraction(head - max(lower, first), 86400)                    # 창이 덮은 기간(리포의 첫 커밋부터)
by_sentence = min(Fraction(90), max(Fraction(0), seen))
formula = got["window_applied"]["authors_window_days"]
print(json.dumps({"key": "F4-4", "values": {"설명 문장 — 90일 중 창이 덮은 일수": str(by_sentence),
                                            "공식·계산기 — 창 안 가장 오래된 커밋부터": str(formula)}}, ensure_ascii=False))
