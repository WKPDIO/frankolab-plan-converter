"""Patient cabinet: one patient's plan with progress and money, laid out for a phone.

The cabinet reuses the converter: the same plan model, dictionary, pictures, memos and stage maps.
What it adds is the patient's status, which will come from the ClinicCards API:

    status = {
        "done":     [{"key": "<service name>", "tooth": "11", "date": "2026-10-12"}, ...],   # performed works (acts)
        "payments": [{"date": "2026-10-12", "amount": "4800.00", "currency": "UAH"}, ...],
        "demo": True,            # optional: the page says the figures are an example
        "progress_from_plan": True,   # optional: take progress from the plan's own done marks (a ClinicCards PDF has them)
        "payments_known": False,      # optional: no payment data yet — show the value of the work, never a debt
    }

Until the API is connected, `demo_status(plan)` makes believable example data.

usage: python3 portal/cabinet.py examples/plan_2.json [out.html] [--demo]
"""
import json
import re
import sys
from base64 import b64encode
from collections import OrderedDict
from decimal import Decimal
from itertools import count
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import illustrations as ILL  # noqa: E402
import render as R  # noqa: E402
from jinja2 import Environment, FileSystemLoader  # noqa: E402
from markupsafe import Markup  # noqa: E402

_ids = count(1)


def big_picture(name):
    """full illustration for the opened procedure; ids made unique so the page can hold many"""
    src = ILL.BY_KEY[name]()
    n = next(_ids)
    src = re.sub(r'id="([\w-]+)"', lambda m: f'id="{m.group(1)}_p{n}"', src)
    src = re.sub(r'url\(#([\w-]+)\)', lambda m: f'url(#{m.group(1)}_p{n})', src)
    return src.replace('width="160" height="160"', 'width="100%" height="100%"', 1)


def _money(d, cur):
    return R.money(d, cur) if d else ""


def _pair(d):
    parts = [R.money(d[c], c) for c in ("UAH", "EUR") if d.get(c)]
    return " + ".join(parts) if parts else "0 грн"


def demo_status(plan, dic):
    """example progress: the first stage is half done, part of it is paid"""
    view, _, _ = R.build(plan, dic)
    done, value = [], {}
    first = view["phases"][0]
    blocks = first["blocks"]
    cut = max(1, len(blocks) - 2)                 # everything but the last two blocks of the first stage is done
    day = 3
    for b in blocks[:cut]:
        for r in b["rows"]:
            teeth = r["teeth_raw"] + [""] * (r["qty"] - len(r["teeth_raw"]))
            for t in teeth:
                done.append({"key": r["key"], "tooth": t, "date": f"2026-10-{day:02d}"})
            value[r["currency"]] = value.get(r["currency"], Decimal(0)) + r["sum_raw"]
        day += 4
    payments = []
    if value.get("UAH"):
        paid = (value["UAH"] * Decimal("0.8")).quantize(Decimal("100"))
        payments += [{"date": "2026-10-03", "amount": str(paid * Decimal("0.5")), "currency": "UAH"},
                     {"date": "2026-10-11", "amount": str(paid * Decimal("0.5")), "currency": "UAH"}]
    if value.get("EUR"):
        payments.append({"date": "2026-10-11", "amount": str(value["EUR"]), "currency": "EUR"})
    return {"done": done, "payments": payments, "demo": True}


def build_cabinet(plan, dic, status):
    view, missing, flagged = R.build(plan, dic)
    done_left = {}
    for d in status.get("done", []):
        k = (R.norm(d["key"]), (d.get("tooth") or "").strip())
        done_left[k] = done_left.get(k, 0) + 1

    def take(key, tooth):
        k = (key, (tooth or "").strip())
        if done_left.get(k):
            done_left[k] -= 1
            return True
        return False

    from_plan = status.get("progress_from_plan", False)
    total, done_value = {}, {}
    n_all = n_done = 0
    phases = []
    current = None
    next_step = None
    for ph in view["phases"]:
        p_all = p_done = 0
        blocks = []
        for b in ph["blocks"]:
            rows = []
            for r in b["rows"]:
                if from_plan:
                    k = r["done_n"]
                else:
                    teeth = r["teeth_raw"] + [""] * (r["qty"] - len(r["teeth_raw"]))
                    k = sum(take(r["key"], t) for t in teeth)
                state = "done" if k == r["qty"] else ("partial" if k else "planned")
                unit = Decimal(r["final"])
                R.add(total, r["currency"], r["sum_raw"])
                if k:
                    R.add(done_value, r["currency"], unit * k)
                p_all += r["qty"]
                p_done += k
                if state != "done" and next_step is None:
                    next_step = {"name": r["name"], "teeth": ", ".join(r["teeth"]), "stage": ph["num"]}
                pic = r["pic_name"]
                rows.append({**r, "state": state, "done_qty": k,
                             "thumb": Markup(ILL.thumb(pic, 1.4, 46)) if pic else None,
                             "big": Markup(big_picture(pic)) if pic else None,
                             "line_total": R.money(r["sum_raw"], r["currency"])})
            blocks.append({**b, "rows": rows,
                           "memos": b["memos_before"] + b["memos_after"],
                           "state": "done" if all(x["state"] == "done" for x in rows) else
                                    ("partial" if any(x["state"] != "planned" for x in rows) else "planned")})
        n_all += p_all
        n_done += p_done
        state = "done" if p_done == p_all else ("current" if p_done else "planned")
        if state != "done" and current is None:
            current = ph["num"]
            state = "current"
        phases.append({**ph, "blocks": blocks, "state": state, "n_all": p_all, "n_done": p_done})

    paid = {}
    pay_rows = []
    for p in sorted(status.get("payments", []), key=lambda x: x["date"], reverse=True):
        R.add(paid, p["currency"], p["amount"])
        pay_rows.append({"date": _date(p["date"]), "amount": R.money(p["amount"], p["currency"])})
    debt = {c: v - paid.get(c, Decimal(0)) for c, v in done_value.items() if v - paid.get(c, Decimal(0)) > 0}
    left = {c: v - paid.get(c, Decimal(0)) for c, v in total.items() if v - paid.get(c, Decimal(0)) > 0}
    to_do = {c: v - done_value.get(c, Decimal(0)) for c, v in total.items() if v - done_value.get(c, Decimal(0)) > 0}

    acts = OrderedDict()
    for d in sorted(status.get("done", []), key=lambda x: x.get("date", ""), reverse=True):
        acts.setdefault(_date(d.get("date", "")), []).append(d)
    names = {r["key"]: r["name"] for ph in view["phases"] for b in ph["blocks"] for r in b["rows"]}
    act_rows = []
    for date, items in acts.items():
        grouped = OrderedDict()
        for d in items:
            key = R.norm(d["key"])
            grouped.setdefault(key, []).append(d.get("tooth") or "")
        act_rows.append({"date": date, "items": [
            {"name": names.get(k, k), "teeth": ", ".join(R.teeth_runs(sorted([t for t in ts if t], key=R.chart_order)))}
            for k, ts in grouped.items()]})

    h = view["h"]
    first_name = h.get("patient", "").split()
    return {
        **view, "phases": phases, "current": current, "next_step": next_step,
        "n_all": n_all, "n_done": n_done, "pct": round(100 * n_done / n_all) if n_all else 0,
        "n_stages": len(phases),
        "paid": _pair(paid), "debt": _pair(debt) if debt else "", "left": _pair(left) if left else "",
        "total": _pair(total), "done_value": _pair(done_value), "to_do": _pair(to_do) if to_do else "",
        "payments_known": status.get("payments_known", True), "progress_from_plan": from_plan,
        "payments": pay_rows, "acts": act_rows, "demo": status.get("demo", False),
        "hello": first_name[1] if len(first_name) > 1 else h.get("patient", ""),
        "phone_href": "tel:+" + re.sub(r"\D", "", h.get("phone", "")),
        "missing": missing,
    }


MONTHS = ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"]


def _date(iso):
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    return f"{int(m.group(3))} {MONTHS[int(m.group(2)) - 1]}" if m else iso


def render_cabinet(plan, dic, status, out_path, **extra):
    """extra goes to the template as is: preview (clinic preview banner), back_url (link back), home_url"""
    data = build_cabinet(plan, dic, status)
    data.update(extra)
    env = Environment(loader=FileSystemLoader(str(ROOT / "portal" / "templates")), autoescape=True)
    font = b64encode((ROOT / "assets/fonts/Onest-wght.woff2").read_bytes()).decode()
    html = env.get_template("cabinet.html.j2").render(**data, font_b64=font)
    Path(out_path).write_text(html)
    return out_path, data


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    src = Path(args[0])
    plan = json.loads(src.read_text()) if src.suffix == ".json" else R.P.parse(str(src))
    dic = json.loads((ROOT / "data" / "services.json").read_text())
    status = demo_status(plan, dic) if "--demo" in sys.argv else {"done": [], "payments": []}
    out = Path(args[1]) if len(args) > 1 else ROOT / "out" / f"cabinet_{src.stem}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    path, d = render_cabinet(plan, dic, status, out)
    print(f"{d['n_done']}/{d['n_all']} procedures done · paid {d['paid']} · debt {d['debt'] or '—'} · left {d['left'] or '—'}")
    print(path)


if __name__ == "__main__":
    main()
