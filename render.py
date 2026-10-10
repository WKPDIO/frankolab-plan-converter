"""ClinicCards plan (PDF or parsed JSON) -> patient-friendly FrankoLab PDF.

usage: python3 render.py <plan.pdf|plan.json> [out_dir] [panorama.png]
"""
import json
import re
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

import segno
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

sys.path.insert(0, str(Path(__file__).parent))
import parse_clinicards as P  # noqa: E402
from graphics import chart, chart_order, icon  # noqa: E402
import illustrations as ILL  # noqa: E402
import stagechart as SC  # noqa: E402

ROOT = Path(__file__).parent
NBSP = " "
AVOID = ["продаємо", "терміново", "дешево", "акці", "гарантован", "найкращ", "унікальн", "100%", "тільки сьогодні"]


def norm(name):
    s = name.lower().replace("послуга", " ")
    s = re.sub(r"[\"«»“”„]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace(" )", ")").replace("( ", "(")
    s = re.sub(r"(\d)-\s+(?=[^\W\d_])", r"\1-", s)   # "3- го" -> "3-го"
    s = re.sub(r"(?<=[a-z])-\s+(?=[a-z])", "-", s)      # "all- on-6" -> "all-on-6"
    return s


TITLE_FIXES = {"Тимачасове": "Тимчасове", "співвідношені": "співвідношенні"}


def clean_title(t):
    """block title as the patient sees it: no stray quotes, obvious ERP typos fixed, no trailing dot"""
    t = re.sub(r"[\"«»“”„]+", "", t).strip().rstrip(".").strip()
    t = re.sub(r"^послуга\s+", "", t, flags=re.I)          # a block named by pasting a service: «Послуга "…"»
    if t.count("(") > t.count(")"):                        # cut off inside brackets: drop the unfinished bracket
        t = t[:t.rfind("(")].strip()
    for a, b in TITLE_FIXES.items():
        t = re.sub(rf"\b{a}\b", b, t)
    return t


def block_title(raw, items):
    """the block's title; ClinicCards cuts a long one mid-word, so a block named after one of its services
    ("Супраструктура … (титанова балка+діоксид цир") is named after that service, without the details in brackets"""
    title = clean_title(raw)
    tn = norm(title)
    pasted = bool(re.match(r"\W*послуга\b", raw.strip(), re.I))
    if len(tn) >= 12:
        for it in items:
            full = norm(it["name"])
            cut_mid_word = full.startswith(tn) and len(full) > len(tn) and full[len(tn)].isalnum() and tn[-1].isalnum()
            if full != tn and full.startswith(tn) and (pasted or cut_mid_word):
                return re.sub(r"\s*\(.*$", "", display_name(it["name"])).strip() or title
    return title


# block subtitle when a prosthetics block holds prostheses, not (only) crowns: categories → plain_with_prosthesis
PROSTHESIS_PICS = {"superstructure", "superstructure_6", "denture"}
CROWN_PICS = {"crown", "crown_layered", "temp_crown", "implant_crown", "temp_implant_crown", "onlay"}


def block_plain(cat, rows):
    variants = cat.get("plain_with_prosthesis")
    pics = {r["pic_name"] for r in rows}
    if not variants or not pics & PROSTHESIS_PICS:
        return cat["plain"]
    if pics & CROWN_PICS:
        return variants["with_crowns"]
    return variants["many"] if sum(r["qty"] for r in rows if r["pic_name"] in PROSTHESIS_PICS) > 1 else variants["one"]


def pic_for(key, entry, rules):
    name = (entry or {}).get("pic")
    if not name:
        name = next((r["pic"] for r in rules
                     if any(m in key for m in r["match"]) and all(m in key for m in r.get("all", []))), None)
    return name if name in ILL.BY_KEY else None


def effect_of(key, entry, rules):
    """(picture, what the stage chart draws) for a service: the entry's own effect, else the one of its picture"""
    pic = pic_for(key, entry, rules)
    return pic, (entry or {}).get("effect") or SC.EFFECT_OF_PIC.get(pic)


def jaw_of_tooth(label):
    t = (label or "").strip()
    if t.isdigit() and len(t) == 2:
        return "upper" if int(t) // 10 in (1, 2) else "lower"
    return jaw_of(t)


def plan_implant_sites(plan, services, rules):
    """the implants of each jaw over the whole plan, {jaw: {tooth: tilt}}: a full-arch implantation (All-on-6 / All-on-4),
    or else four or more single implants. A prosthesis in any stage is drawn on these, so a jaw never shows two sets."""
    arch = {"upper": set(), "lower": set()}
    single = {"upper": set(), "lower": set()}
    for ph in plan["phases"]:
        for b in ph["blocks"]:
            for it in b["items"]:
                key = norm(it["name"])
                _, effect = effect_of(key, services.get(key), rules)
                jaw = jaw_of_tooth(it["tooth"])
                if not jaw:
                    continue
                if effect in ("all_on_4", "all_on_6"):
                    arch[jaw].add(effect)
                elif effect in SC.IMPLANT_EFFECTS and it["tooth"].strip().isdigit():
                    single[jaw].add(int(it["tooth"]))
    out = {}
    for jaw in ("upper", "lower"):
        if arch[jaw]:
            out[jaw] = SC.in_jaw(SC.A6_POS if "all_on_6" in arch[jaw] else SC.A4_POS, jaw)
        elif len(single[jaw]) >= 4:
            out[jaw] = {n: 0 for n in single[jaw]}
    return out


def display_name(name):
    s = re.sub(r"^\W*послуга\W*", "", name, flags=re.I)
    s = re.sub(r"[\"«»“”„]+", "", s)
    s = re.sub(r"\s+", " ", s).strip().replace(" )", ")")
    s = re.sub(r",(?=\S)", ", ", s)
    s = re.sub(r"(\d)-\s+(?=[^\W\d_])", r"\1-", s)
    s = re.sub(r"(?<=[A-Za-z])-\s+(?=[A-Za-z])", "-", s)
    s = re.sub(r"\)\.(?=[^\W\d_])", "). ", s)            # "фіксація).Встановлення" -> "фіксація). Встановлення"
    s = re.sub(r"\s*\+\s*", " + ", s)                         # "PMMA+ титанова балка" -> "PMMA + титанова балка"
    return s[:1].upper() + s[1:]


def group_thousands(n):
    s = f"{n:,}".replace(",", NBSP)
    return s


def money(v, cur):
    v = Decimal(v)
    whole = v == v.to_integral()
    num = group_thousands(int(v)) if whole else group_thousands(int(v)) + "," + f"{v:.2f}".split(".")[1]
    return f"€{num}" if cur == "EUR" else f"{num}{NBSP}грн"


def money_pair(d):
    parts = []
    if Decimal(d.get("UAH", 0)):
        parts.append(money(d["UAH"], "UAH"))
    if Decimal(d.get("EUR", 0)):
        parts.append(money(d["EUR"], "EUR"))
    return f" + ".join(parts) if parts else "—"


def add(acc, cur, v):
    acc[cur] = acc.get(cur, Decimal(0)) + Decimal(v)


def duration_text(s):
    m = re.search(r"орієнтовно\s+(?:днів\s+)?(\d+)\s*[-–]\s*(\d+)(?:\s*днів)?", s, re.I)
    if m:
        return f"орієнтовно {m.group(1)}–{m.group(2)} днів"
    return s.strip().rstrip(".")


def teeth_label(t, segments):
    t = t.strip()
    m = re.fullmatch(r"(сегмент|квадрант)\s*(\d)", t, re.I)
    if m:
        return f"{m.group(1).lower()}{NBSP}{m.group(2)}"     # the number never wraps away from its word
    return {"в/щ": "верхня щелепа", "н/щ": "нижня щелепа"}.get(t, t)


# sextants (сегменти) and whole jaws, to light up the chart when a service is given for an area, not a tooth
SEXTANTS = {"1": [18, 17, 16, 15, 14], "2": [13, 12, 11, 21, 22, 23], "3": [24, 25, 26, 27, 28],
            "4": [34, 35, 36, 37, 38], "5": [33, 32, 31, 41, 42, 43], "6": [44, 45, 46, 47, 48]}


# quadrants (квадранти): a quarter of the mouth, numbered like the first digit of a tooth
QUADRANTS = {"1": "зуби 18–11", "2": "зуби 21–28", "3": "зуби 31–38", "4": "зуби 41–48"}


def area_teeth(label):
    t = label.strip().lower()
    m = re.fullmatch(r"сегмент\s*(\d)", t)
    if m:
        return set(SEXTANTS.get(m.group(1), []))
    m = re.fullmatch(r"квадрант\s*(\d)", t)
    if m and m.group(1) in QUADRANTS:
        return {int(m.group(1)) * 10 + i for i in range(1, 9)}
    if t in ("в/щ", "верхня щелепа"):
        return {q * 10 + i for q in (1, 2) for i in range(1, 9)}
    if t in ("н/щ", "нижня щелепа"):
        return {q * 10 + i for q in (3, 4) for i in range(1, 9)}
    return set()


OTHER_NAME = {"ct_scan": "консультація і 3D-знімок", "exam": "консультація", "scan": "цифрове сканування", "impression": "відбиток щелепи",
              "hygiene": "професійна гігієна", "sedation": "лікування уві сні (седація)", "axiography": "аксіографія"}


def jaw_of(label):
    t = label.strip().lower()
    if t in ("в/щ", "верхня щелепа"):
        return "upper"
    if t in ("н/щ", "нижня щелепа"):
        return "lower"
    return None


def teeth_runs(labels):
    """17, 16, 15, 14 -> 17–14: runs of 3+ neighbouring teeth in one quadrant (labels already in chart order)"""
    out, run = [], []

    def flush():
        if len(run) >= 3:
            out.append(f"{run[0]}–{run[-1]}")
        else:
            out.extend(run)
        run.clear()
    for t in labels:
        if run and t.isdigit() and run[-1].isdigit() and t[0] == run[-1][0] and abs(int(t[1]) - int(run[-1][1])) == 1:
            run.append(t)
            continue
        flush()
        if t.isdigit() and len(t) == 2:
            run.append(t)
        else:
            out.append(t)
    flush()
    return out


ORDINALS = [(r"перш", "Перший"), (r"друг", "Другий"), (r"тр?ет|терт", "Третій"), (r"четв", "Четвертий"),
            (r"п.ят", "П'ятий"), (r"шост", "Шостий")]


def months(m):
    n = int(m.group(2))
    word = "місяць" if n % 10 == 1 and n % 100 != 11 else "місяці" if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else "місяців"
    return f"{m.group(1)}{word}"


def phase_names(title, timing):
    """'Етап' + 'тертій через 4-6 місяці' -> 'Третій етап' + 'через 4–6 місяців'"""
    title, timing = (title or "").strip(), (timing or "").strip()
    if title.lower() == "етап" and timing:
        word, _, rest = timing.partition(" ")
        for pat, name in ORDINALS:
            if re.match(pat, word.lower()):
                title, timing = f"{name} етап", rest.strip()
                break
    timing = re.sub(r"(\d)\s*-\s*(\d)", r"\1–\2", timing)
    timing = re.sub(r"((?:\d+–)?(\d+)\s)місяц\w*", months, timing)
    return title, timing


def phone_fmt(p):
    d = re.sub(r"\D", "", p)
    if len(d) == 12 and d.startswith("380"):
        return f"+380{NBSP}{d[3:5]}{NBSP}{d[5:8]}{NBSP}{d[8:10]}{NBSP}{d[10:12]}"
    return p


def attach_memos(blocks, memos):
    """put each matching memo above the first / below the last block of the stage that needs it"""
    stage_keys = [k for b in blocks for k in b["keys"]]
    for m in memos:
        hits = [i for i, b in enumerate(blocks) if any(t in k for k in b["keys"] for t in m["trigger"])]
        if not hits:
            continue
        items = []
        for it in m["items"]:
            if isinstance(it, dict):
                hit = lambda ts: any(t in k for k in stage_keys for t in ts)
                if ("if" in it and hit(it["if"])) or ("unless" in it and not hit(it["unless"])):
                    items.append(it["text"])
            else:
                items.append(it)
        view = {"title": m["title"], "items": items, "rx": m.get("rx"), "kind": m["place"]}
        if m["place"] == "before":
            blocks[hits[0]]["memos_before"].append(view)
        else:
            blocks[hits[-1]]["memos_after"].append(view)


def build(plan, dic):
    services = {norm(k): v for k, v in dic["services"].items()}
    memos = json.loads((ROOT / "data" / "memos.json").read_text())["memos"]
    cats = dic["categories"]
    rules = dic.get("pic_rules", [])
    seg_names = {k: v for k, v in dic["segments"].items() if not k.startswith("_")}
    missing, flagged = [], []
    has_discount = any("discount" in it for ph in plan["phases"] for b in ph["blocks"] for it in b["items"])
    view_phases = []
    grand = {}
    done_tot = {}
    all_teeth = set()
    seen = {}   # service key -> number of the stage where its description was first shown
    seen_desc = {}  # description text -> the same, for different positions explained by one text
    known_sites = plan_implant_sites(plan, services, rules)
    for i, ph in enumerate(plan["phases"], 1):
        ph_tot = {}
        blocks = []
        fx_teeth, jaw_fx = {}, {"upper": set(), "lower": set()}
        area_fx = []       # (teeth of the area, effect) for services given per segment / jaw, resolved after the stage
        legend, other = OrderedDict(), []
        for b in ph["blocks"]:
            title = block_title(b["title"], b["items"])
            cat = next((c for c in cats if any(m in title.lower() for m in c["match"])), {"plain": "", "icon": "tooth", "tint": "#eef1f4"})
            groups = OrderedDict()
            b_tot = {}
            b_done = 0
            teeth = set()
            segs, quads = [], []
            for it in b["items"]:
                key = (norm(it["name"]), it["currency"], it.get("price"), json.dumps(it.get("discount"), sort_keys=True), it["final"])
                g = groups.setdefault(key, {"name": display_name(it["name"]), "key": norm(it["name"]), "currency": it["currency"],
                                            "price": it.get("price"), "discount": it.get("discount"), "final": it["final"],
                                            "teeth": [], "qty": 0, "sum": Decimal(0), "done": 0})
                g["qty"] += 1
                g["sum"] += Decimal(it["final"])
                if it.get("done"):
                    g["done"] += 1
                    add(done_tot, it["currency"], it["final"])
                    b_done += 1
                if it["tooth"]:
                    g["teeth"].append(it["tooth"])
                    if it["tooth"].isdigit():
                        teeth.add(int(it["tooth"]))
                    m = re.fullmatch(r"сегмент\s*(\d)", it["tooth"], re.I)
                    if m and m.group(1) not in segs:
                        segs.append(m.group(1))
                    m = re.fullmatch(r"квадрант\s*(\d)", it["tooth"], re.I)
                    if m and m.group(1) in QUADRANTS and m.group(1) not in quads:
                        quads.append(m.group(1))
                    teeth |= area_teeth(it["tooth"])
                add(b_tot, it["currency"], it["final"])
            rows = []
            prev_pic = None
            for g in groups.values():
                s = services.get(g["key"])
                if not s:
                    missing.append(g["name"])
                desc = (s or {}).get("desc", "")
                for w in AVOID:
                    if w in desc.lower():
                        flagged.append(f"{g['name']}: «{w}»")
                tl = sorted(g["teeth"], key=chart_order)
                unit = Decimal(g["price"]) if g["price"] else Decimal(g["final"])
                disc = ""
                if g["discount"]:
                    d = g["discount"]
                    disc = f"−{d['value'].rstrip('0').rstrip('.') if '.' in d['value'] else d['value']}%" if d["type"] == "percent" else "−" + money(d["value"], g["currency"])
                pic, effect = effect_of(g["key"], s, rules)
                if cat.get("temporary") and effect in ("superstructure", "superstructure_6"):
                    effect = "superstructure_temp"      # a prosthesis listed under temporary prosthetics is the temporary one
                if not effect:
                    nm = OTHER_NAME.get(pic, g["name"][:1].lower() + g["name"][1:])
                    if nm not in other:
                        other.append(nm)
                else:
                    labels = legend.setdefault(effect, [])
                    for t in g["teeth"]:
                        if t not in labels:
                            labels.append(t)
                        jaw = jaw_of(t)
                        if effect in SC.JAW_EFFECTS:
                            if jaw:
                                jaw_fx[jaw].add(effect)
                            elif t.isdigit():
                                jaw_fx["upper" if int(t) // 10 in (1, 2) else "lower"].add(effect)
                        elif t.isdigit():
                            fx_teeth.setdefault(int(t), set()).add(effect)
                        else:
                            area_fx.append((area_teeth(t), effect))
                ref = ""
                if desc and g["key"] in seen:
                    ref = "Про цю послугу — вище." if seen[g["key"]] == i else f"Про цю послугу — в етапі {seen[g['key']]:02d}."
                    desc = ""
                elif desc and desc in seen_desc:      # another price-list position with the very same explanation
                    seen[g["key"]] = seen_desc[desc]
                    ref = "Пояснення таке саме, як вище." if seen_desc[desc] == i else f"Пояснення таке саме, як в етапі {seen_desc[desc]:02d}."
                    desc = ""
                elif desc:
                    seen[g["key"]] = i
                    seen_desc[desc] = i
                rows.append({
                    # raw fields for other views (patient cabinet): full description, picture name, money as numbers
                    "key": g["key"], "pic_name": pic, "effect": effect, "desc_full": (s or {}).get("desc", ""),
                    "teeth_raw": list(g["teeth"]), "currency": g["currency"], "final": g["final"], "sum_raw": g["sum"],
                    "name": g["name"], "desc": desc, "ref": ref, "lab": bool((s or {}).get("lab")),
                    "incl": (s or {}).get("incl", ""),
                    "pic": Markup(ILL.thumb(pic, 1.4, 50)) if pic and pic != prev_pic else None,
                    "pic_slot": bool(pic),
                    "teeth": [teeth_label(t, seg_names) for t in teeth_runs(tl)],
                    "unit": money(unit, g["currency"]), "disc": disc, "qty": g["qty"],
                    "done_n": g["done"], "done_state": "all" if g["done"] == g["qty"] else ("some" if g["done"] else ""),
                    "uah": money(g["sum"], "UAH") if g["currency"] == "UAH" else "",
                    "eur": money(g["sum"], "EUR") if g["currency"] == "EUR" else "",
                })
                prev_pic = pic
            printed = {k: Decimal(v) for k, v in b.get("total", {}).items()}
            if printed and {k: v for k, v in b_tot.items() if v} != {k: v for k, v in printed.items() if v}:
                raise SystemExit(f"STOP: block '{title}' sum {b_tot} differs from printed {printed}")
            for k, v in b_tot.items():
                add(ph_tot, k, v)
            all_teeth |= teeth
            blocks.append({
                "title": title, "plain": block_plain(cat, rows), "icon": Markup(icon(cat["icon"], 30)), "tint": cat.get("tint", "#eef1f4"),
                "chart": None,
                "rows": rows, "total": money_pair({k: str(v) for k, v in b_tot.items()}),
                "total_uah": money(b_tot["UAH"], "UAH") if "UAH" in b_tot and (b_tot["UAH"] or not any(b_tot.values())) else "",
                "total_eur": money(b_tot["EUR"], "EUR") if "EUR" in b_tot and (b_tot["EUR"] or not any(b_tot.values())) else "",
                "segments": [(s, seg_names.get(s, "")) for s in segs],
                "quadrants": [(q, QUADRANTS[q]) for q in sorted(quads)],
                "keys": [g["key"] for g in groups.values()],
                "memos_before": [], "memos_after": [],
                "done_state": "all" if b_done and b_done == len(b["items"]) else ("some" if b_done else ""),
                "done_n": b_done, "n": len(b["items"]),
            })
        # a service on a segment means "somewhere in this area", not "on every tooth of it": bone, gum and sinus work
        # goes only to the teeth of the area that get an implant (or, if none, are extracted) in this stage; anything else
        # on an area is shown on all its teeth
        jaw_sites = set()
        for jaw, effects in jaw_fx.items():
            jaw_sites |= set(SC.implant_sites(jaw, effects, known_sites.get(jaw)))
        for teeth_of_area, effect in area_fx:
            if effect in SC.SITE_EFFECTS:
                # implant sites first: bone, sinus and gum work there is for the implant; extraction sites only
                # when the area gets no implant in this stage (e.g. preserving the socket after an extraction)
                sites = [n for n in teeth_of_area if fx_teeth.get(n, set()) & SC.IMPLANT_ANCHORS or n in jaw_sites] or \
                        [n for n in teeth_of_area if fx_teeth.get(n, set()) & SC.SITE_ANCHORS]
                for n in sites:
                    fx_teeth.setdefault(n, set()).add(effect)
            else:
                for n in teeth_of_area:
                    fx_teeth.setdefault(n, set()).add(effect)
        attach_memos(blocks, memos)
        for k, v in ph_tot.items():
            add(grand, k, v)
        ph_title, ph_timing = phase_names(ph["title"], ph.get("timing", ""))
        has_map = bool(fx_teeth) or any(jaw_fx.values())
        legend_view = []
        for e in sorted(legend, key=SC.ORDER.index):
            labs = legend[e]
            digits = sorted([t for t in labs if t.isdigit()], key=chart_order)
            words = [teeth_label(t, seg_names) for t in labs if not t.isdigit()]
            legend_view.append({"glyph": Markup(SC.glyph(e, 36)), "label": SC.LABEL[e],
                                "teeth": ", ".join(teeth_runs(digits) + words)})
        view_phases.append({
            "map": Markup(SC.stage_chart(fx_teeth, jaw_fx, 640, known_sites)) if has_map else None,
            "legend": legend_view, "other": other,
            "num": f"{i:02d}", "title": ph_title or f"Етап {i}", "timing": ph_timing,
            "duration": duration_text(ph.get("duration", "")),
            "what": [(b["plain"] or b["title"], b["tint"]) for b in blocks],
            "blocks": blocks, "total": money_pair({k: str(v) for k, v in ph_tot.items()}),
            "total_uah": money(ph_tot["UAH"], "UAH") if ph_tot.get("UAH") else "",
            "total_eur": money(ph_tot["EUR"], "EUR") if ph_tot.get("EUR") else "",
            "done_state": ("all" if all(b["done_state"] == "all" for b in blocks) else
                           "some" if any(b["done_state"] for b in blocks) else ""),
        })
    printed = {}
    for t in plan["totals"]:
        for k, v in t["amounts"].items():
            add(printed, k, v)
    if printed and {k: v for k, v in grand.items() if v} != {k: v for k, v in printed.items() if v}:
        raise SystemExit(f"STOP: plan sum {grand} differs from printed {printed}")
    has_progress = any(it.get("done") for ph in plan["phases"] for b in ph["blocks"] for it in b["items"])
    printed_done = {}
    for t in plan["totals"]:
        if t.get("done"):
            for k, v in t["amounts"].items():
                add(printed_done, k, v)
    if (printed_done or has_progress) and {k: v for k, v in done_tot.items() if v} != {k: v for k, v in printed_done.items() if v}:
        raise SystemExit(f"STOP: done sum {done_tot} differs from printed {printed_done}")
    h = dict(plan["header"])
    h["website"] = h.get("website", "").replace("\x00", "tt").replace("h ps", "https")
    h["phone_fmt"] = phone_fmt(h.get("phone", ""))
    qr = None
    if h.get("website"):
        qr = Markup(segno.make(h["website"], error="m").svg_inline(scale=2, border=0, dark="#212121"))
    site_short = re.sub(r"^https?://(www\.)?|/$", "", h.get("website", ""))
    terms = [t for t in plan["terms"] if not t.startswith("З рекомендованим") and not t.startswith("Дата:")]
    consent = next((t for t in plan["terms"] if t.startswith("З рекомендованим")), "")
    view = {
        "h": h, "site_short": site_short, "qr": qr, "phases": view_phases, "has_discount": has_discount,
        "grand": money_pair({k: str(v) for k, v in grand.items()}),
        "grand_uah": money(grand["UAH"], "UAH") if grand.get("UAH") else "",
        "grand_eur": money(grand["EUR"], "EUR") if grand.get("EUR") else "",
        "has_eur": bool(grand.get("EUR")),
        "has_progress": has_progress,
        "done_total": money_pair({k: str(v) for k, v in done_tot.items()}) if has_progress else "",
        "left_total": money_pair({k: str(grand.get(k, Decimal(0)) - done_tot.get(k, Decimal(0))) for k in grand}),
        "done_uah": money(done_tot["UAH"], "UAH") if done_tot.get("UAH") else "",
        "done_eur": money(done_tot["EUR"], "EUR") if done_tot.get("EUR") else "",
        "left_uah": money(grand.get("UAH", 0) - done_tot.get("UAH", 0), "UAH") if grand.get("UAH", 0) - done_tot.get("UAH", 0) else "",
        "left_eur": money(grand.get("EUR", 0) - done_tot.get("EUR", 0), "EUR") if grand.get("EUR", 0) - done_tot.get("EUR", 0) else "",
        "included_note": dic.get("included_everywhere", ""),
        "overview_chart": Markup(chart(all_teeth, 520)) if all_teeth else None,
        "terms": terms, "consent": consent,
        "plan_name": h.get("plan_name", ""),
    }
    return view, missing, flagged


def render_plan(src, out_dir, pano=None, preview=None):
    """ClinicCards PDF (or its parsed JSON) -> patient PDF. Stops if any sum does not match the source.
    preview — optional path for a PNG of the first page (used by the web app).
    Returns (pdf_path, report) — report has the item count, sums and missing descriptions."""
    src, out_dir = Path(src), Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    plan = json.loads(src.read_text()) if src.suffix == ".json" else P.parse(str(src))
    chk = P.check(plan)
    if chk["problems"]:
        raise SystemExit("STOP: source totals do not add up:\n" + "\n".join(chk["problems"]))
    dic = json.loads((ROOT / "data" / "services.json").read_text())
    view, missing, flagged = build(plan, dic)
    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")), autoescape=True)
    pano_uri = Path(pano).resolve().as_uri() if pano else None
    html = env.get_template("plan.html.j2").render(**view, pano=pano_uri, font_url=(ROOT / "assets/fonts/Onest-wght.woff2").as_uri())
    stem = re.sub(r"\s+", "_", plan["header"].get("patient", src.stem))
    html_path = out_dir / f"План_лікування_{stem}.html"
    html_path.write_text(html)
    pdf_path = out_dir / f"План_лікування_{stem}.pdf"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        # --disable-dev-shm-usage: small /dev/shm in containers would otherwise crash Chromium
        b = pw.chromium.launch(args=["--disable-dev-shm-usage"])
        pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=1)
        pg.goto(html_path.as_uri())
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(200)
        pg.pdf(path=str(pdf_path), format="A4", print_background=True, prefer_css_page_size=True)
        b.close()
    if preview:     # first page exactly as printed (pypdfium2 comes with pdfplumber)
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(pdf_path))
        doc[0].render(scale=1.4).to_pil().save(str(preview))
        doc.close()
    report = {"items": chk["items"], "sum": chk["sum"], "printed": chk["printed"], "missing": missing, "avoid_words": flagged,
              "patient": plan["header"].get("patient", ""), "doctor": plan["header"].get("doctor", ""),
              "date": plan["header"].get("date", ""), "phases": len(view["phases"]), "total": view["grand"],
              "done_total": view["done_total"], "left_total": view["left_total"] if view["has_progress"] else ""}
    return pdf_path, report


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else ROOT / "out"
    pdf, r = render_plan(sys.argv[1], out_dir, sys.argv[3] if len(sys.argv) > 3 else None)
    print(f"items {r['items']} · sum {r['sum']} · printed {r['printed']}")
    print("missing descriptions:", r["missing"] or "none")
    print("avoid-words:", r["avoid_words"] or "none")
    print(pdf)


if __name__ == "__main__":
    main()
