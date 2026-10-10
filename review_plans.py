"""Перевірка пачки планів ClinicCards: що скаже конвертер про кожен план і чи збігаються ціни з прайсом.

    python3 review_plans.py out/review плани/*.pdf --prices Price.xlsx

Пише out/review/report.md (підсумок + кожен план: читається / суми / послуги без опису / назви блоків /
незнайомі позначки ділянок / ціни, що відрізняються від прайсу) і out/review/maps.html (зубні формули всіх етапів).
Нічого не змінює: план можна переглянути до того, як офіс його завантажить. Звіт містить імена пацієнтів —
тримайте його в out/ (не потрапляє в репозиторій).
"""
import json
import re
import sys
import traceback
from collections import OrderedDict, defaultdict
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
import parse_clinicards as P  # noqa: E402
import render as R  # noqa: E402

args = sys.argv[1:]
price_path = None
if "--prices" in args:
    i = args.index("--prices")
    price_path = Path(args[i + 1])
    del args[i:i + 2]
if len(args) < 2:
    raise SystemExit(__doc__)
out_dir, pdfs = Path(args[0]), [Path(p) for p in args[1:]]
out_dir.mkdir(parents=True, exist_ok=True)
dic = json.loads((REPO / "data" / "services.json").read_text())
services = {R.norm(k): v for k, v in dic["services"].items()}
rules = dic["pic_rules"]

# ---- price list: name -> [(currency, price)] (duplicates kept) -------------------------------
prices = defaultdict(list)
section = ""
wb = None
if price_path:
    import openpyxl                     # only needed for the price check (pip install openpyxl)
    wb = openpyxl.load_workbook(price_path, read_only=True, data_only=True)
for ws in (wb.worksheets if wb else []):
    for row in ws.iter_rows(values_only=True):
        name, val = row[0], row[1] if len(row) > 1 else None
        if not name:
            continue
        if val is None:
            section = str(name).strip()
            continue
        if isinstance(val, (int, float)):
            cur, amount = "UAH", Decimal(str(val))
        else:
            s = str(val).replace(" ", "").replace(" ", "")
            m = re.match(r"€?([\d.,]+)", s)
            if not m:
                continue
            amount = Decimal(m.group(1).replace(",", ""))
            cur = "EUR" if "€" in s else "UAH"
        prices[R.norm(str(name))].append((cur, amount.quantize(Decimal("0.01"))))

AREA_OK = re.compile(r"^(\d{2}|в/щ|н/щ|сегмент\s*\d|квадрант\s*\d|)$", re.I)

report, summary_missing, summary_prices, summary_unpriced, summary_areas, summary_titles = [], defaultdict(set), [], defaultdict(set), defaultdict(set), []
maps_html = []
for n, pdf in enumerate(pdfs, 1):
    tag = f"План {n}"
    lines = [f"## {tag} · {pdf.name}"]
    try:
        plan = P.parse(str(pdf))
    except Exception as e:  # noqa: BLE001
        lines.append(f"- НЕ ЧИТАЄТЬСЯ: {type(e).__name__}: {e}")
        report.append("\n".join(lines))
        continue
    items = [(ph, b, it) for ph in plan["phases"] for b in ph["blocks"] for it in b["items"]]
    h = plan["header"]
    done = sum(1 for _, _, it in items if it.get("done"))
    lines.append(f"- етапів {len(plan['phases'])}, блоків {sum(len(ph['blocks']) for ph in plan['phases'])}, позицій {len(items)}, "
                 f"виконано {done} з {len(items)}, дата {h.get('date', '')}")
    chk = P.check(plan)
    if chk["problems"]:
        lines.append("- СУМИ В ОРИГІНАЛІ: " + "; ".join(chk["problems"]))
    try:
        view, missing, flagged = R.build(plan, dic)
        lines.append(f"- конвертується: так, разом {view['grand']}" + (f" (виконано {view['done_total']})" if view.get("done_total") else ""))
    except SystemExit as e:
        view, missing, flagged = None, [], []
        lines.append(f"- НЕ КОНВЕРТУЄТЬСЯ: {e}")
    except Exception as e:  # noqa: BLE001
        view, missing, flagged = None, [], []
        lines.append(f"- ПОМИЛКА: {type(e).__name__}: {e}\n```\n{traceback.format_exc()[-1500:]}\n```")
    for m in OrderedDict.fromkeys(missing):
        summary_missing[m].add(tag)
    if missing:
        lines.append(f"- без опису ({len(set(missing))}): " + "; ".join(OrderedDict.fromkeys(missing)))
    if flagged:
        lines.append("- слова, яких уникаємо: " + "; ".join(flagged))
    # phases and block titles as the patient will see them
    for ph in plan["phases"]:
        t, tm = R.phase_names(ph["title"], ph.get("timing", ""))
        lines.append(f"- етап «{t or '—'}» {('· ' + tm) if tm else ''} {('· ' + ph.get('duration', '')) if ph.get('duration') else ''}")
        for b in ph["blocks"]:
            title = R.block_title(b["title"], b["items"])
            cat = next((c for c in dic["categories"] if any(m in title.lower() for m in c["match"])), None)
            if not cat or title != R.clean_title(b["title"]):
                summary_titles.append((tag, b["title"], title, cat["plain"] if cat else "— без категорії"))
            lines.append(f"    - блок «{title}»" + ("" if cat else "  ← без категорії (сірий фон, без підзаголовка)")
                         + (f"  (в оригіналі: «{b['title']}»)" if title != b["title"].strip() else ""))
    # tooth / area labels the converter does not know
    for _, _, it in items:
        t = (it["tooth"] or "").strip()
        if not AREA_OK.match(t):
            summary_areas[t].add(tag)
    # prices against the price list
    seen = set()
    for _, _, it in items:
        key = R.norm(it["name"])
        unit = Decimal(it.get("price") or it["final"])
        k = (key, it["currency"], unit)
        if k in seen:
            continue
        seen.add(k)
        listed = prices.get(key)
        if not prices:
            continue
        if not listed:
            summary_unpriced[R.display_name(it["name"])].add(tag)
            continue
        if not any(c == it["currency"] and p == unit for c, p in listed):
            now = ", ".join(R.money(p, c) for c, p in listed)
            summary_prices.append((tag, R.display_name(it["name"]), R.money(unit, it["currency"]), now))
    if view:
        for ph in view["phases"]:
            if ph["map"]:
                maps_html.append(f"<h4>{tag} · {ph['num']} {ph['title']}</h4>{ph['map']}"
                                 + "".join(f"<div class='lg-line'>{e['label']}: {e['teeth']}</div>" for e in ph["legend"]))
    report.append("\n".join(lines))

summ = ["# Підсумок", ""]
if summary_missing:
    summ.append(f"## Послуги без опису ({len(summary_missing)})")
    summ += [f"- {m} — {', '.join(sorted(t))}" for m, t in sorted(summary_missing.items())]
if summary_areas:
    summ.append("## Незнайомі позначки зубів / ділянок")
    summ += [f"- «{a}» — {', '.join(sorted(t))}" for a, t in sorted(summary_areas.items())]
if summary_titles:
    summ.append("## Назви блоків, які змінено або без категорії")
    summ += [f"- {t}: «{raw}» → «{new}» · {plain}" for t, raw, new, plain in summary_titles]
if summary_prices:
    summ.append(f"## Ціна в плані ≠ прайс ({len(summary_prices)})")
    summ += [f"- {t}: {name} — у плані {old}, у прайсі {now}" for t, name, old, now in summary_prices]
if summary_unpriced:
    summ.append(f"## Немає в прайсі під такою назвою ({len(summary_unpriced)})")
    summ += [f"- {m} — {', '.join(sorted(t))}" for m, t in sorted(summary_unpriced.items())]
(out_dir / "report.md").write_text("\n".join(summ) + "\n\n" + "\n\n".join(report) + "\n")
css = (REPO / "templates/plan.html.j2").read_text()
css = css[css.index("<style>") + 7:css.index("</style>")].replace("{{ font_url }}", (REPO / "assets/fonts/Onest-wght.woff2").as_uri())
css = re.sub(r"@page[^{]*\{(?:[^{}]|\{[^{}]*\})*\}", "", css)
(out_dir / "maps.html").write_text(f"<html><head><meta charset='utf-8'><style>{css} body{{padding:10px}} h4{{margin:18px 0 4px;font-weight:600}}"
                                   f" .lg-line{{font-size:10px;color:#474a50}}</style></head><body>{''.join(maps_html)}</body></html>")
print((out_dir / "report.md").read_text()[:200000])
