"""Regression check: render every example plan and confirm the money still matches the source.

usage: python3 check_examples.py [out_dir]

Each example in examples/ is a parsed ClinicCards plan with the patient's name removed.
render_plan() stops with an error if any block, stage or plan total differs from the source,
so a clean run means the layout changes did not touch the numbers. Open the PDFs in out/examples
to look at the result.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from render import render_plan  # noqa: E402


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "out" / "examples"
    failed = 0
    for src in sorted((ROOT / "examples").glob("plan_*.json")):
        try:
            pdf, r = render_plan(src, out)
        except SystemExit as e:
            failed += 1
            print(f"FAIL {src.name}: {e}")
            continue
        ok = r["sum"] == r["printed"] or {k: v for k, v in r["sum"].items() if float(v)} == {k: v for k, v in r["printed"].items() if float(v)}
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {src.name}: {r['items']} items, sum {r['sum']}"
              + (f", missing descriptions: {len(r['missing'])}" if r["missing"] else "")
              + (f", avoid-words: {r['avoid_words']}" if r["avoid_words"] else ""))
    if failed:
        raise SystemExit(f"{failed} example(s) failed")
    print(f"all examples fine → {out}")


if __name__ == "__main__":
    main()
