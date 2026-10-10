"""Parse a ClinicCards treatment-plan PDF into structured data.

Layout facts this parser relies on (ClinicCards print form, 2026):
- every plan block (a ClinicCards "stage") is a large filled rounded shape;
- block title: size 8.25, dark grey (0.2), at the top of the block;
- tooth chart: tooth numbers size 11.22, grey (0.502), above / below a
  horizontal line, left / right of a vertical midline;
- item rows: table cells (filled rects) holding words in grey 0.3647;
  columns: name | tooth | [base price | discount] | ... | final amount;
- block total: size 9, dark grey, below the rows ("€3 370.00, 25 000.00");
- free text outside blocks (size 10.5) is a phase heading when a block
  follows it, otherwise the closing terms;
- "Невиконані: ..." / "Виконано: ..." carry the plan totals (not done / done);
- a row or a total line starts with a marker: "✓" (green) — already done, "●" (blue) — still to do.
  A block with both shows two total lines, one per marker; a fully discounted line shows only the base and "-100%".
Money: "2 400.00" (space = thousands), "€550.00"; currency of a row is the
currency of its final amount.
"""
import json
import re
import sys
from decimal import Decimal

import pdfplumber

ITEM_GREY = 0.3647
DARK = 0.2
CHART_SIZE = 11.22
MARKERS = {"✓": True, "●": False}       # row / total-line marker -> done?


def rgb(col):
    """a colour as a tuple of numbers, or None: a pattern fill comes as its name ('P23'), which is not a colour"""
    if isinstance(col, (list, tuple)) and col and all(isinstance(x, (int, float)) for x in col):
        return tuple(col)
    return None


def grey(w):
    c = rgb(w.get("non_stroking_color"))
    if not c:
        return None
    return round(c[0], 4) if len(c) in (1, 3) else None


def neutral(w):
    """text in a shade of grey (black, grey, white) — row text; the coloured ✓ / ● markers are not"""
    c = rgb(w.get("non_stroking_color"))
    if not c or len(c) not in (1, 3):
        return False
    return len(c) == 1 or max(c) - min(c) < 0.03


PUA = re.compile("[\ue000-\uf8ff]")      # icon-font glyphs ClinicCards puts before some rows


def is_close(a, b, tol=0.01):
    return a is not None and abs(a - b) < tol


MONEY_RE = re.compile(r"(€?)\s*(\d{1,3}(?:\s\d{3})*(?:\.\d{2}))")


TOKEN_RE = re.compile(r"(-?\d+(?:[.,]\d+)?%)|(€?)\s*(\d{1,3}(?:\s\d{3})*\.\d{2})")


GROUP_RE = re.compile(r"(-?\d+(?:[.,]\d+)?%)|(,)|(€?)\s*(\d{1,3}(?:\s\d{3})*\.\d{2})")


def parse_total_line(text):
    """'2 900.00 -30% 2 030.00' / '6 500.00 6 442.00' / '€3 370.00, 25 000.00' / '€7 600.00, 9 700.00 €7 450.00'
    -> {'final': {cur: Decimal}, 'base': {cur: Decimal}, 'percent': str|None}
    Amounts come in comma-separated groups, one amount per currency: the first group is the sum before discount, the
    last one what the patient pays. A currency left out of the last group is fully discounted (pays 0)."""
    groups, prev, pct = [[]], None, None
    for m in GROUP_RE.finditer(text.replace(",", " , ")):
        if m.group(1):
            pct, prev = m.group(1), "pct"
            continue
        if m.group(2):
            prev = "comma"
            continue
        if prev in ("amount", "pct") and groups[-1]:
            groups.append([])
        groups[-1].append(("EUR" if m.group(3) else "UAH", Decimal(m.group(4).replace(" ", ""))))
        prev = "amount"
    groups = [dict(g) for g in groups if g]
    if not groups:
        raise ValueError(f"cannot parse total: {text!r}")
    if len(groups) == 1:
        if pct and Decimal(pct.rstrip("%").replace(",", ".")) == Decimal(-100):
            # ClinicCards prints a fully discounted total as "14 300.00 -100%": the base only, the zero is left out
            return {"final": {k: Decimal("0.00") for k in groups[0]}, "base": groups[0], "percent": pct}
        return {"final": groups[0], "base": {}, "percent": pct}
    base, final = groups[0], dict(groups[-1])
    for k in base:
        final.setdefault(k, Decimal("0.00"))
    return {"final": final, "base": base, "percent": pct}


def parse_money_list(text):
    return parse_total_line(text)["final"]


def parse_amount(text):
    """single amount -> (currency or None, Decimal)"""
    t = text.replace(" ", "").strip()
    cur = None
    if t.startswith("€"):
        cur, t = "EUR", t[1:]
    return cur, Decimal(t)


def join_words(ws):
    """words -> text in reading order (lines by top, then x)"""
    if not ws:
        return ""
    ws = sorted(ws, key=lambda w: (round(w["top"]), w["x0"]))
    lines, cur, last_top = [], [], None
    for w in ws:
        if last_top is not None and abs(w["top"] - last_top) > 3:
            lines.append(cur)
            cur = []
        cur.append(w)
        last_top = w["top"]
    lines.append(cur)
    out = []
    for ln in lines:
        ln.sort(key=lambda w: w["x0"])
        s = ""
        for i, w in enumerate(ln):
            if i and w["x0"] - ln[i - 1]["x1"] > 0.8:
                s += " "
            s += w["text"]
        out.append(s)
    return " ".join(out)


def clean_name(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace(" )", ")").replace("( ", "(")
    return s


def page_elements(page, pno):
    words = page.extract_words(x_tolerance=1.5, y_tolerance=2, extra_attrs=["non_stroking_color", "size"])
    for w in words:
        w["page"] = pno
    # block shapes: big filled curves that are not the white page background
    blocks = []
    for c in page.curves:
        if c.get("fill"):
            col = rgb(c.get("non_stroking_color")) or ()
            if len(col) == 3 and all(abs(x - 1.0) < 0.01 for x in col):
                continue                       # white: the page background, or a white block (found by its outline)
        elif c.get("stroke"):
            col = rgb(c.get("stroking_color")) or ()  # outline: the only trace of a white block
        else:
            continue
        if (c["x1"] - c["x0"]) > 400 and (c["bottom"] - c["top"]) > 12:
            blocks.append({"page": pno, "top": c["top"], "bottom": c["bottom"], "x0": c["x0"], "x1": c["x1"],
                           "color": [round(x, 3) for x in col]})
    # de-duplicate (fill + stroke shapes come in pairs)
    uniq = []
    for b in sorted(blocks, key=lambda b: b["top"]):
        if uniq and abs(uniq[-1]["top"] - b["top"]) < 1 and abs(uniq[-1]["bottom"] - b["bottom"]) < 1:
            continue
        uniq.append(b)
    rects = [r for r in page.rects if r.get("fill") and (r["x1"] - r["x0"]) > 2 and (r["bottom"] - r["top"]) > 8
             and (r["x1"] - r["x0"]) < 430]
    hlines = [l for l in page.lines if abs(l["top"] - l["bottom"]) < 0.5 and (l["x1"] - l["x0"]) > 300]
    vlines = [l for l in page.lines if abs(l["x0"] - l["x1"]) < 0.5]
    return words, uniq, rects, hlines, vlines


class CollapsedBlocks(ValueError):
    """the PDF was printed with blocks folded: their totals are there, their services are not"""

    def __init__(self, titles):
        self.titles = titles
        super().__init__("collapsed blocks without services: " + "; ".join(titles))


def _zero_free(amounts, rows, base=None):
    """ClinicCards prints, without "-100%", the list-price sum of rows that are all free: if every row of a currency costs
    0 and the printed amount is exactly their list-price sum, the patient pays 0 in that currency"""
    out = dict(amounts)
    for cur, v in amounts.items():
        v = Decimal(v)
        rs = [it for it in rows if it["currency"] == cur]
        if v and rs and all(Decimal(it["final"]) == 0 for it in rs) and v == sum(Decimal(it.get("price") or it["final"]) for it in rs):
            out[cur] = "0.00"
            if base is not None:
                base[cur] = str(v)
    return out


def fix_free_totals(plan):
    items = [it for ph in plan["phases"] for b in ph["blocks"] for it in b["items"]]
    marked = any("done" in it for it in items)
    for ph in plan["phases"]:
        for b in ph["blocks"]:
            parts = b.get("total_parts", [])
            if parts and all(part["done"] is not None for part in parts):
                # one line per marker (✓ / ●): fix each against its own rows, the block total is their sum
                total = {}
                for part in parts:
                    part["amounts"] = _zero_free(part["amounts"], [it for it in b["items"] if it.get("done") is part["done"]])
                    for k, v in part["amounts"].items():
                        total[k] = total.get(k, Decimal(0)) + Decimal(v)
                b["total"] = {k: str(v) for k, v in total.items()}
            elif b.get("total"):
                before = b.setdefault("total_before_discount", {})
                b["total"] = _zero_free(b["total"], b["items"], before)
                if not before:
                    del b["total_before_discount"]
    for tot in plan["totals"]:
        rows = [it for it in items if it.get("done") is tot["done"]] if marked else items
        tot["amounts"] = _zero_free(tot["amounts"], rows, tot["before_discount"])


def parse(path):
    plan = {"source": path.split("/")[-1], "header": {}, "phases": [], "terms": [], "totals": []}
    flow = []  # document-ordered elements: ('text', page, top, words) / ('block', block dict)
    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            words, blocks, rects, hlines, vlines = page_elements(page, pno)
            used = set()
            # header on page 1
            if pno == 1:
                hdr = [w for w in words if w["top"] < 140]
                for w in hdr:
                    used.add(id(w))
                plan["header"] = parse_header(hdr, words)
                for w in words:
                    if 140 <= w["top"] < 170 and abs(w["size"] - 10.5) < 0.1 and grey(w) is not None and is_close(grey(w), DARK):
                        used.add(id(w))
                plan["header"]["plan_name"] = join_words([w for w in words if 140 <= w["top"] < 170 and abs(w["size"] - 10.5) < 0.1])
            for b in blocks:
                beside = [w for w in words if b["top"] - 1 <= w["top"] <= b["bottom"] + 1 and id(w) not in used]
                inside = [w for w in beside if b["x0"] - 2 <= w["x0"] and w["x1"] <= b["x1"] + 2]
                # beside the block: ClinicCards' visit notes next to booked rows ("1 30.03.2026", "2 Візит не заплановано") —
                # not part of the plan, and not a heading either
                for w in beside:
                    used.add(id(w))
                b_rects = [r for r in rects if b["top"] <= r["top"] and r["bottom"] <= b["bottom"] + 1]
                b_h = [l for l in hlines if b["top"] <= l["top"] <= b["bottom"]]
                b_v = [l for l in vlines if b["top"] <= l["top"] <= b["bottom"]]
                flow.append(("block", pno, b["top"], parse_block(b, inside, b_rects, b_h, b_v)))
            rest = [w for w in words if id(w) not in used and w["text"] not in MARKERS]
            # totals line(s): "Невиконані:" — still to do, "Виконано:" / "Виконані:" — already done
            for label in ("Невиконані:", "Виконано:", "Виконані:"):
                for w in [w for w in rest if w["text"] == label]:
                    line = [x for x in rest if abs(x["top"] - w["top"]) < 2 and x["x0"] > w["x0"]]
                    t = parse_total_line(join_words(line))
                    plan["totals"].append({"label": label.rstrip(":"), "done": label != "Невиконані:",
                                           "amounts": {k: str(v) for k, v in t["final"].items()},
                                           "before_discount": {k: str(v) for k, v in t["base"].items()}})
                    rest = [x for x in rest if not (abs(x["top"] - w["top"]) < 2 and x["x0"] >= w["x0"])]
            # free text lines grouped into paragraphs
            rest.sort(key=lambda w: (round(w["top"]), w["x0"]))
            lines = []
            for w in rest:
                if lines and abs(lines[-1][0] - w["top"]) < 3:
                    lines[-1][1].append(w)
                else:
                    lines.append([w["top"], [w]])
            for top, ws in lines:
                flow.append(("text", pno, top, join_words(ws)))
    flow.sort(key=lambda e: (e[1], e[2]))
    # walk the flow: text before a block = phase heading; text after the last block = terms
    last_block_idx = max(i for i, e in enumerate(flow) if e[0] == "block")
    pending = []
    current = None
    for i, e in enumerate(flow):
        if e[0] == "text":
            if i > last_block_idx:
                plan["terms"].append(e[3])
            else:
                pending.append(e[3])
            continue
        blk = e[3]
        if blk.get("continued") and current and current["blocks"]:
            merge_block(current["blocks"][-1], blk)
            continue
        if not blk["items"] and not blk.get("total") and not blk.get("continued"):
            continue          # an empty block (no services, no sum): nothing for the patient; a heading above it stays pending
        if pending or current is None:
            current = {"heading": pending, "blocks": []}
            plan["phases"].append(current)
            pending = []
        current["blocks"].append(blk)
    plan["terms"] = group_terms(plan["terms"])
    for ph in plan["phases"]:
        ph.update(split_heading(ph.pop("heading")))
    collapsed = [b["title"] or "без назви" for ph in plan["phases"] for b in ph["blocks"] if not b["items"]]
    if collapsed:
        raise CollapsedBlocks(collapsed)
    fix_free_totals(plan)
    return plan


def parse_header(hdr, words):
    h = {}
    txt = {round(w["top"]): [] for w in hdr}
    for w in hdr:
        txt[round(w["top"])].append(w)
    lines = [join_words(ws) for _, ws in sorted(txt.items())]
    all_text = " | ".join(lines)
    m = re.search(r"Пацієнт:\s*(.+?)\s+Спеціаліст:\s*(.+?)(?:\s*\||$)", " ".join(join_words([w]) for w in sorted(hdr, key=lambda w: (round(w['top']), w['x0']))))
    pat = [w for w in hdr if w["text"] == "Пацієнт:"]
    spc = [w for w in hdr if w["text"] == "Спеціаліст:"]
    if pat:
        p = pat[0]
        h["patient"] = join_words([w for w in hdr if abs(w["top"] - p["top"]) < 4 and p["x1"] < w["x0"] < (spc[0]["x0"] if spc else 1e9)])
    if spc:
        s = spc[0]
        h["doctor"] = join_words([w for w in hdr if abs(w["top"] - s["top"]) < 4 and w["x0"] > s["x1"]])
    for w in hdr:
        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", w["text"]):
            h["date"] = w["text"]
    clinic = [w for w in hdr if w["top"] < 100]
    left = [w for w in clinic if w["x0"] < 300]
    right = [w for w in clinic if w["x0"] >= 300]
    h["clinic_name"] = join_words(left)
    rl = {}
    for w in right:
        rl.setdefault(round(w["top"]), []).append(w)
    clines = [join_words(ws) for _, ws in sorted(rl.items())]
    for ln in clines:
        l = ln.replace("h ps://", "https://").replace("h p://", "http://")
        if "@" in l:
            h["email"] = l
        elif l.startswith("http") or "www." in l:
            h["website"] = l
        elif re.fullmatch(r"\+?[\d\s()-]{9,}", l):
            h["phone"] = l.replace(" ", "")
        else:
            h.setdefault("address", l)
    h["address"] = re.sub(r"\s*—\s*", " — ", h.get("address", "")).replace(" ,", ",")
    return h


def parse_block(b, words, rects, hl, vl):
    blk = {"page": b["page"], "title": "", "chart": {"upper": [], "lower": []}, "items": [], "total": {}, "continued": False}
    titles = [w for w in words if abs(w["size"] - 8.25) < 0.05 and is_close(grey(w), DARK) and w["text"] not in MARKERS]
    # title = dark 8.25 words above the first table row
    row_bands = sorted({(round(r["top"], 1), round(r["bottom"], 1)) for r in rects})
    first_row_top = row_bands[0][0] if row_bands else b["bottom"]
    blk["title"] = clean_name(join_words([w for w in titles if w["top"] < first_row_top]))
    if not blk["title"]:
        blk["continued"] = True
    # tooth chart
    chart_words = [w for w in words if abs(w["size"] - CHART_SIZE) < 0.1]
    if chart_words:
        y = hl[0]["top"] if hl else None
        mid = vl[0]["x0"] if vl else 246
        up = sorted([w for w in chart_words if y is None or w["top"] + w["bottom"] < 2 * y], key=lambda w: w["x0"])
        lo = sorted([w for w in chart_words if y is not None and w["top"] + w["bottom"] >= 2 * y], key=lambda w: w["x0"])
        blk["chart"] = {"upper": [w["text"] for w in up], "lower": [w["text"] for w in lo]}
    # rows
    # row text is a shade of grey: grey rows, the darker price before a discount ("3 600.00 | 15% | 3 060.00"), a lighter
    # row with an icon, white on blue for a highlighted row (a visit booked for it); icon glyphs are dropped
    item_words = []
    for w in words:
        if neutral(w) and w["text"] not in MARKERS:
            text = PUA.sub("", w["text"])
            if text.strip():
                item_words.append({**w, "text": text})
    markers = [w for w in words if w["text"] in MARKERS]
    for top, bottom in row_bands:
        cells = sorted([r for r in rects if abs(r["top"] - top) < 0.6 and abs(r["bottom"] - bottom) < 0.6], key=lambda r: r["x0"])
        cells = [c for c in cells if (c["x1"] - c["x0"]) > 3]
        rw = [w for w in item_words if top - 1 <= (w["top"] + w["bottom"]) / 2 <= bottom + 1]
        if not rw:
            continue

        def in_cell(c):
            return [w for w in rw if c["x0"] - 0.5 <= (w["x0"] + w["x1"]) / 2 <= c["x1"] + 0.5]
        name = clean_name(join_words(in_cell(cells[0])))
        tooth = clean_name(join_words(in_cell(cells[1]))) if len(cells) > 1 else ""
        mids = cells[2:-1]
        final_txt = join_words(in_cell(cells[-1]))
        cur, final = parse_amount(final_txt)
        cur = cur or "UAH"
        base = None
        discount = None
        for c in mids:
            t = join_words(in_cell(c)).strip()
            if not t:
                continue
            if t.endswith("%"):
                discount = {"type": "percent", "value": str(Decimal(t[:-1].replace(",", ".")))}
            elif re.fullmatch(r"€?\s*\d[\d\s]*\.\d{2}", t):
                bc, base = parse_amount(t)
            else:
                discount = {"type": "amount", "value": str(Decimal(t.replace(" ", "").replace(",", ".")))}
        mk = [m for m in markers if top - 1 <= (m["top"] + m["bottom"]) / 2 <= bottom + 1 and m["x0"] < cells[0]["x0"] + 12]
        item = {"name": name, "tooth": tooth, "currency": cur, "final": str(final)}
        if mk:
            item["done"] = MARKERS[mk[0]["text"]]
        if base is not None:
            item["price"] = str(base)
        if discount:
            item["discount"] = discount
        blk["items"].append(item)
    # block total: dark size-9 words below the last row
    last_bottom = row_bands[-1][1] if row_bands else b["top"]
    tw = [w for w in words if is_close(grey(w), DARK) and abs(w["size"] - 9.0) < 0.1 and w["top"] >= last_bottom - 1]
    if tw:
        # a block with done and not-done rows has two total lines (✓ and ●); each is parsed on its own and summed
        lines = []
        for w in sorted(tw, key=lambda w: w["top"]):
            if lines and abs(lines[-1][0] - w["top"]) < 3:
                lines[-1][1].append(w)
            else:
                lines.append([w["top"], [w]])
        final, base, parts = {}, {}, []
        for top, ws in lines:
            t = parse_total_line(join_words(ws))
            mk = [m for m in markers if abs((m["top"] + m["bottom"]) / 2 - (top + ws[0]["bottom"]) / 2) < 4]
            done = MARKERS[mk[0]["text"]] if mk else None
            for k, v in t["final"].items():
                final[k] = final.get(k, Decimal(0)) + v
                base[k] = base.get(k, Decimal(0)) + t["base"].get(k, v)
            parts.append({"done": done, "amounts": {k: str(v) for k, v in t["final"].items()}, "percent": t["percent"]})
        blk["total"] = {k: str(v) for k, v in final.items()}
        if base != final:
            blk["total_before_discount"] = {k: str(v) for k, v in base.items()}
        pcts = {p["percent"] for p in parts if p["percent"]}
        if len(pcts) == 1:
            blk["total_discount"] = pcts.pop()
        if len(parts) > 1:
            blk["total_parts"] = parts
    return blk


def merge_block(a, b):
    a["items"].extend(b["items"])
    for k in ("upper", "lower"):
        a["chart"][k].extend(x for x in b["chart"][k] if x not in a["chart"][k])
    if b.get("total"):
        for k in ("total", "total_parts", "total_before_discount", "total_discount"):
            if k in b:
                a[k] = b[k]


def split_heading(lines):
    """['Перший етап.', 'Орієнтовно днів 8-12.'] -> title / timing / duration"""
    title, notes = "", []
    if lines:
        title = lines[0].rstrip(".")
        notes = [l.rstrip(".") for l in lines[1:]]
        # a long doctor's note as the heading wraps: lines that are not the duration ("Орієнтовно …") continue the title
        while notes and not re.search(r"орієнтовн|\d\s*(дн|тиж|міс)", notes[0], re.I) and not re.search(r"етап", title, re.I):
            title = f"{title} {notes.pop(0)}".strip()
        title = re.sub(r"([.!?])(?=[А-ЯІЇЄҐA-Z])", r"\1 ", title)      # "лікування.До" -> "лікування. До"
    out = {"title_raw": title, "notes_raw": notes}
    m = re.match(r"^(.*?етап)\s*(.*)$", title, re.I)
    out["title"] = (m.group(1) if m else title).strip()
    out["timing"] = (m.group(2) if m else "").strip()
    dur = " ".join(notes)
    out["duration"] = dur
    return out


def group_terms(lines):
    paras, cur = [], []
    for ln in lines:
        cur.append(ln)
        if ln.rstrip().endswith((".", ":")) or "Підпис" in ln:
            paras.append(" ".join(cur))
            cur = []
    if cur:
        paras.append(" ".join(cur))
    return paras


def check(plan):
    """sum items per block and per plan; compare with the printed totals"""
    problems = []
    grand = {}
    n = 0
    for ph in plan["phases"]:
        for b in ph["blocks"]:
            s = {}
            for it in b["items"]:
                n += 1
                s[it["currency"]] = s.get(it["currency"], Decimal(0)) + Decimal(it["final"])
                if "price" in it:
                    p, f = Decimal(it["price"]), Decimal(it["final"])
                    d = it.get("discount")
                    if d and d["type"] == "percent":
                        exp = (p * (100 - Decimal(d["value"])) / 100).quantize(Decimal("0.01"))
                    elif d:
                        exp = p - Decimal(d["value"])
                    else:
                        exp = p
                    if abs(exp - f) > Decimal("0.01"):
                        problems.append(f"{b['title']}: {it['name']} {it['tooth']}: {p} - {d} = {exp}, printed {f}")
            tot = {k: Decimal(v) for k, v in b.get("total", {}).items()}
            if {k: v for k, v in s.items() if v} != {k: v for k, v in tot.items() if v}:
                problems.append(f"block '{b['title']}': items {s} vs printed {tot}")
            # done / not done: each part of a split total must match the rows with the same marker
            for part in b.get("total_parts", []):
                if part["done"] is None:
                    continue
                ps = {}
                for it in b["items"]:
                    if it.get("done") is part["done"]:
                        ps[it["currency"]] = ps.get(it["currency"], Decimal(0)) + Decimal(it["final"])
                pt = {k: Decimal(v) for k, v in part["amounts"].items()}
                if {k: v for k, v in ps.items() if v} != {k: v for k, v in pt.items() if v}:
                    problems.append(f"block '{b['title']}' ({'done' if part['done'] else 'to do'}): items {ps} vs printed {pt}")
            for k, v in s.items():
                grand[k] = grand.get(k, Decimal(0)) + v
    printed = {}
    for t in plan["totals"]:
        for k, v in t["amounts"].items():
            printed[k] = printed.get(k, Decimal(0)) + Decimal(v)
        # "Виконано" must equal the rows marked ✓, "Невиконані" the rows marked ●
        if "done" in t and any("done" in it for ph in plan["phases"] for b in ph["blocks"] for it in b["items"]):
            part = {}
            for ph in plan["phases"]:
                for b in ph["blocks"]:
                    for it in b["items"]:
                        if bool(it.get("done")) is t["done"]:
                            part[it["currency"]] = part.get(it["currency"], Decimal(0)) + Decimal(it["final"])
            pt = {k: Decimal(v) for k, v in t["amounts"].items()}
            if {k: v for k, v in part.items() if v} != {k: v for k, v in pt.items() if v}:
                problems.append(f"plan '{t['label']}': items {part} vs printed {pt}")
    if printed and {k: v for k, v in grand.items() if v} != {k: v for k, v in printed.items() if v}:
        problems.append(f"plan total: items {grand} vs printed {printed}")
    return {"items": n, "sum": {k: str(v) for k, v in grand.items()}, "printed": {k: str(v) for k, v in printed.items()}, "problems": problems}


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None
    plan = parse(src)
    plan["check"] = check(plan)
    js = json.dumps(plan, ensure_ascii=False, indent=1)
    if dst:
        open(dst, "w").write(js)
    c = plan["check"]
    print(f"{plan['source']}: phases {len(plan['phases'])}, blocks {sum(len(p['blocks']) for p in plan['phases'])}, items {c['items']}, sum {c['sum']}, printed {c['printed']}, problems {len(c['problems'])}")
    for p in c["problems"]:
        print("  !", p)
