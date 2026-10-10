"""Stage chart: the full anatomical tooth chart where every tooth shows what happens to it in this stage.

Each procedure is drawn on the tooth itself, in the language of the big illustrations:
Storm Blue — what we do, dashed — future / temporary, hatching — bone material, metal grey — implant already in place.
Effects are picked from the service picture (services.json → pic); the legend repeats each effect on one tooth.
"""
import math
from itertools import count

import graphics as G

INK = "#474a50"
FADE = "#c9d2dc"
ROOT = "#f1f4f8"
# one colour per family of procedures, so the chart reads at a glance
CROWN, CROWN_DEEP = "#99aabe", "#6f839c"           # permanent constructions: crowns, bridges, prostheses (Storm Blue)
TEMP, TEMP_DEEP = "#cfe0f7", "#7fa6dc"             # temporary constructions (Sky Blue, dashed)
RESTO, RESTO_DEEP = "#9fc9b0", "#5f9478"           # fillings, composite and ceramic restorations (sage)
ENDO, ENDO_DEEP = "#e3a28f", "#c26b55"             # root canals, posts (coral)
CORE, CORE_DEEP = "#c0b3d8", "#8a78b1"             # core build-up (lavender)
GUM, GUM_DEEP = "#efb5ad", "#cc7f73"               # gum: soft-tissue graft, crown lengthening (rose)
BONE, BONE_DEEP = "#e2cfb0", "#b3966c"             # bone material (sand, hatched)
METAL, METAL_DEEP = "#c9d0d8", "#7c8691"           # implants, abutments, healing caps
OLD = "#e4e6ea"
SAND, SAND_EDGE = "#d8c3a5", "#a88f6c"             # tartar
PINK, PINK_EDGE = "#e6bdb2", "#b98c80"             # acrylic base of a prosthesis
MODEL = "#9ac2f4"
DECAY, DECAY_DEEP, INFLAMED = "#b9a48c", "#8c7257", "#e49a95"   # the tooth that cannot be saved

# service picture -> what is drawn on the tooth
EFFECT_OF_PIC = {
    "filling": "filling", "aesthetic": "aesthetic", "endo": "endo", "fiber": "fiber", "post_removal": "post_removal",
    "core_buildup": "core", "crown_removal": "crown_removal", "temp_crown": "temp_crown", "crown": "crown",
    "crown_layered": "crown", "onlay": "onlay", "extraction": "extraction", "implant": "implant",
    "healing_cap": "healing_cap", "custom_abutment": "abutment", "multi_unit": "abutment", "implant_crown": "implant_crown",
    "temp_implant_crown": "temp_implant_crown", "bone_graft": "bone_graft", "soft_tissue": "soft_tissue",
    "sinus_lift": "sinus_lift", "srp": "srp", "crown_lengthening": "crown_lengthening", "modeling": "modeling",
    "all_on_4": "all_on_4", "superstructure": "superstructure", "all_on_6": "all_on_6", "superstructure_6": "superstructure_6",
    "denture": "denture", "aligner": "aligner",
    "retention_tray": "retention_tray", "splint": "splint", "retainer": "retainer", "separation": "separation",
}
# a fixed prosthesis on the implants of a whole jaw; "superstructure_temp" is the temporary one (set in services.json → effect)
PROSTHESES = {"superstructure", "superstructure_6", "superstructure_temp"}
FULL_ARCH = {"all_on_4", "all_on_6"} | PROSTHESES
JAW_EFFECTS = FULL_ARCH | {"denture", "aligner", "retention_tray", "splint", "retainer"}
# work on the site, not on a tooth: when given per segment it attaches to the implant / extraction sites in that segment
SITE_EFFECTS = {"bone_graft", "sinus_lift", "soft_tissue"}
SITE_ANCHORS = {"implant", "extraction", "healing_cap", "abutment", "implant_crown", "temp_implant_crown", "a4_new"}
IMPLANT_ANCHORS = SITE_ANCHORS - {"extraction"}
IMPLANT_EFFECTS = {"implant", "implant_crown", "temp_implant_crown", "healing_cap", "abutment"}

LABEL = {
    "filling": "Лікування карієсу, пломба", "aesthetic": "Естетична реставрація", "endo": "Лікування каналів",
    "fiber": "Зміцнення скловолокном", "post_removal": "Видалення штифта", "core": "Відновлення культі",
    "crown_removal": "Зняття старої коронки", "temp_crown": "Тимчасова коронка", "crown": "Постійна коронка",
    "onlay": "Накладка, вкладка, вінір", "extraction": "Видалення зуба", "implant": "Імплантат",
    "healing_cap": "Формувач ясен", "abutment": "Абатмент", "implant_crown": "Коронка на імплантаті",
    "temp_implant_crown": "Тимчасова коронка на імплантаті", "bone_graft": "Нарощування кістки",
    "soft_tissue": "Пластика ясен", "sinus_lift": "Синус-ліфтинг", "srp": "Глибоке чищення під яснами",
    "crown_lengthening": "Видовження коронки", "modeling": "Цифрове моделювання",
    "all_on_4": "All-on-4: чотири імплантати", "superstructure_temp": "Тимчасовий незнімний протез на імплантатах",
    "superstructure": "Незнімний протез на імплантатах",
    "all_on_6": "All-on-6: шість імплантатів", "superstructure_6": "Незнімний протез на шести імплантатах",
    "denture": "Знімний протез", "aligner": "Елайнери", "retention_tray": "Ретенційна капа", "splint": "Сплінт",
    "retainer": "Ретейнер", "separation": "Сепарація",
}
ORDER = list(LABEL)

# All-on-4 implant positions: two straight in front, two tilted at the back (apex toward the midline)
A4_POS = {12: 0, 22: 0, 15: 28, 25: 28, 32: 0, 42: 0, 35: 28, 45: 28}
# All-on-6: two in front, two at the premolars, two at the first molars (slightly tilted)
A6_POS = {12: 0, 22: 0, 14: 0, 24: 0, 16: 18, 26: 18, 32: 0, 42: 0, 34: 0, 44: 0, 36: 18, 46: 18}


def in_jaw(pos_map, jaw):
    up = jaw == "upper"
    return {n: t for n, t in pos_map.items() if (n // 10 in (1, 2)) == up}


def implant_sites(jaw, effects, known=None):
    """where the implants of a full-arch treatment stand on this jaw, {tooth: tilt}. One set per jaw:
    the implantation decides (All-on-6 → six); a prosthesis sits on the implants the plan placed, whatever concept its
    name gives — a temporary bridge "in the All-on-4 concept" on six implants still stands on six. known — the jaw's
    implants from the whole plan (render.plan_implant_sites); only without them does the prosthesis concept decide."""
    if "all_on_6" in effects:
        return in_jaw(A6_POS, jaw)
    if "all_on_4" in effects:
        return in_jaw(A4_POS, jaw)
    if not effects & PROSTHESES:
        return {}
    if known:
        return dict(known)
    return in_jaw(A6_POS if "superstructure_6" in effects else A4_POS, jaw)

_ids = count(1)


def _defs(uid):
    return (f'<defs><pattern id="{uid}h" width="3.4" height="3.4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<rect width="3.4" height="3.4" fill="{BONE}"/><path d="M0 0V3.4" stroke="{BONE_DEEP}" stroke-width=".9"/></pattern>'
            f'<pattern id="{uid}o" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">'
            f'<rect width="3" height="3" fill="{OLD}"/><path d="M0 0V3" stroke="#a9b0b9" stroke-width=".8"/></pattern></defs>')


def _p(g, cmds):
    return G._fmt(cmds, g["tf"])


def _rect(g, x0, y0, x1, y1, r=.8):
    return _p(g, [("M", (x0 + r, y0)), ("L", (x1 - r, y0)), ("Q", (x1, y0), (x1, y0 + r)), ("L", (x1, y1 - r)),
                  ("Q", (x1, y1), (x1 - r, y1)), ("L", (x0 + r, y1)), ("Q", (x0, y1), (x0, y1 - r)),
                  ("L", (x0, y0 + r)), ("Q", (x0, y0), (x0 + r, y0)), ("Z",)])


def _ellipse_pts(g, cx, cy, rx, ry):
    k = .552
    return _p(g, [("M", (cx + rx, cy)), ("C", (cx + rx, cy + ry * k), (cx + rx * k, cy + ry), (cx, cy + ry)),
                  ("C", (cx - rx * k, cy + ry), (cx - rx, cy + ry * k), (cx - rx, cy)),
                  ("C", (cx - rx, cy - ry * k), (cx - rx * k, cy - ry), (cx, cy - ry)),
                  ("C", (cx + rx * k, cy - ry), (cx + rx, cy - ry * k), (cx + rx, cy)), ("Z",)])


def _canal(g, lobe):
    hc, cw = g["hc"], g["cw"]
    x, y, h = lobe
    return _p(g, [("M", (x * .25, hc * .66)), ("Q", (x * .85, hc + (y - hc) * .4), (x, y - h * 1.6))])


def _implant(g, fill, tilt=0, length=None):
    """implant in place of the root: platform at the neck, apex toward the root tip; tilt in degrees toward mesial"""
    hc, hr, cw = g["hc"], g["hr"], g["cw"]
    iw = min(4.2, cw * .8)
    L = length or hr * .9
    a = math.radians(tilt)

    def rot(x, y):                      # rotate around the platform centre (0, hc)
        dy = y - hc
        return (x * math.cos(a) + dy * math.sin(a), hc + dy * math.cos(a) - x * math.sin(a))
    body = [("M", rot(-iw / 2, hc)), ("L", rot(iw / 2, hc)),
            ("C", rot(iw / 2 + .1, hc + L * .6), rot(iw * .42, hc + L * .92), rot(iw * .26, hc + L)),
            ("Q", rot(0, hc + L + .7), rot(-iw * .26, hc + L)),
            ("C", rot(-iw * .42, hc + L * .92), rot(-iw / 2 - .1, hc + L * .6), rot(-iw / 2, hc)), ("Z",)]
    out = f'<path d="{_p(g, body)}" fill="{fill}" stroke="{INK}" stroke-width=".8" stroke-linejoin="round"/>'
    thr = []
    y = hc + 1.4
    while y < hc + L - 1:
        half = iw / 2 * (1 - (y - hc) / L * .35)
        thr += [("M", rot(-half, y + .5)), ("L", rot(half, y - .5))]
        y += 1.5
    out += f'<path d="{_p(g, thr)}" fill="none" stroke="{METAL_DEEP}" stroke-width=".55"/>'
    return out


def _facets(g, clip, k=1.0):
    """the crown's proximal planes as faint tone, clipped to the crown"""
    return (f'<g clip-path="url(#{clip})">' + "".join(f'<path d="{d}" fill="#1e2a3a" fill-opacity="{op * k:.3f}"/>' for d, op in g["facets"]) + "</g>")


def _implant_crown_path(g, cw_top=None):
    """crown on an implant: the anatomical crown continued below the neck by a smooth emergence profile
    that narrows to the implant platform (no mushroom step)"""
    hc, cw, w = g["hc"], g["cw"], g["w"]
    iw = min(4.2, cw * .8)
    plat = hc + 2.6                       # platform a little below the gum line
    outline = G._crown_outline(g["kind"], w, cw, hc)      # from (-cw/2, hc) ... to (cw/2, hc)
    tail = [("C", (cw / 2 - .1, hc + 1.2), (iw / 2 + .4, plat - .9), (iw / 2, plat)), ("L", (-iw / 2, plat)),
            ("C", (-iw / 2 - .4, plat - .9), (-cw / 2 + .1, hc + 1.2), (-cw / 2, hc)), ("Z",)]
    return _p(g, outline + tail), plat


def _pontic_path(g):
    """bridge pontic: the anatomical crown closed by a gentle oval base resting on the gum — no root"""
    hc, cw, w = g["hc"], g["cw"], g["w"]
    outline = G._crown_outline(g["kind"], w, cw, hc)      # from (-cw/2, hc) ... to (cw/2, hc)
    return _p(g, outline + [("Q", (0, hc + 2.6), (-cw / 2, hc)), ("Z",)])


def _stump(g):
    hc, cw = g["hc"], g["cw"]
    return _p(g, [("M", (-cw * .46, hc)), ("C", (-cw * .48, hc * .55), (-cw * .42, hc * .32), (-cw * .3, hc * .3)),
                  ("L", (cw * .3, hc * .3)), ("C", (cw * .42, hc * .32), (cw * .48, hc * .55), (cw * .46, hc)), ("Z",)])


def draw_tooth(g, fx, uid, active=True):
    """svg for one tooth with its set of effects (local frame of tooth_geom)"""
    hc, hr, w, cw = g["hc"], g["hr"], g["w"], g["cw"]
    n = g["n"]
    under, base, over = "", "", ""
    if "absent" in fx:
        return "", "", "", ""
    clip = f"{uid}c{n}"
    clipdef = f'<clipPath id="{clip}"><path d="{g["crown"]}"/></clipPath>'
    stroke = INK if active else FADE
    sw = .8 if active else .6

    # behind the tooth: bone material and the lifted sinus floor
    if "bone_graft" in fx:
        under += f'<path d="{_rect(g, -w * .62, hc + hr * .1, w * .62, hc + hr * .8, 1.5)}" fill="url(#{uid}h)" stroke="{BONE_DEEP}" stroke-width=".5"/>'
    if "sinus_lift" in fx:
        dome = [("M", (-w * .62, hc + hr * .98)), ("Q", (-w * .62, hc + hr * .52), (0, hc + hr * .48)),
                ("Q", (w * .62, hc + hr * .52), (w * .62, hc + hr * .98)), ("Z",)]
        under += f'<path d="{_p(g, dome)}" fill="url(#{uid}h)" stroke="{BONE_DEEP}" stroke-width=".6"/>'

    implantish = fx & (IMPLANT_EFFECTS | {"a4_new", "a4_metal"})
    edentulous = bool(implantish or fx & {"a4_future", "prosthesis", "prosthesis_temp", "denture"})

    if "pontic" in fx and not implantish:
        # a crown where the tooth is removed: a bridge pontic, resting on the gum
        pon = _pontic_path(g)
        if "crown" in fx:
            base += f'<path d="{pon}" fill="{CROWN}" stroke="{INK}" stroke-width=".8" stroke-linejoin="round"/>'
            base += _facets(g, clip, 1.4)
            base += f'<path d="{g["relief"]}" fill="none" stroke="#ffffff" stroke-opacity=".5" stroke-width=".5" stroke-linecap="round"/>'
        else:
            base += (f'<path d="{pon}" fill="{TEMP}" fill-opacity=".85" stroke="{TEMP_DEEP}" stroke-width=".9" '
                     f'stroke-dasharray="2 1.6" stroke-linejoin="round"/>')
    elif edentulous:
        if implantish:
            new = bool(fx & {"implant", "a4_new"})
            base += _implant(g, METAL if new else "#e3e7ec", tilt=fx_tilt(fx))
            if fx & {"implant_crown", "temp_implant_crown", "prosthesis", "prosthesis_temp"} and not fx_tilt(fx):
                # hide the top of the implant under the emergence profile (the crown path is drawn over it)
                icp, _ = _implant_crown_path(g)
                base += f'<path d="{icp}" fill="{ROOT if active else "#f7f9fb"}"/>'
        if "healing_cap" in fx:
            cap = _rect(g, -cw * .3, hc * .68, cw * .3, hc + .4, .9)
            base += f'<path d="{cap}" fill="{METAL}" stroke="{INK}" stroke-width=".8"/>'
        if "abutment" in fx:
            ab = _p(g, [("M", (-cw * .34, hc)), ("L", (-cw * .3, hc * .42)), ("Q", (0, hc * .36), (cw * .3, hc * .42)),
                        ("L", (cw * .34, hc)), ("Z",)])
            base += f'<path d="{ab}" fill="{METAL}" stroke="{INK}" stroke-width=".8"/>'
        if fx & {"implant_crown"} or "prosthesis" in fx:
            icp, plat = _implant_crown_path(g)
            base += f'<path d="{icp}" fill="{CROWN}" stroke="{INK}" stroke-width=".8" stroke-linejoin="round"/>'
            base += _facets(g, clip, 1.4)
            base += f'<path d="{g["relief"]}" fill="none" stroke="#ffffff" stroke-opacity=".5" stroke-width=".5" stroke-linecap="round"/>'
            base += f'<path d="{_p(g, [("M", (-min(4.2, cw * .8) / 2, plat)), ("L", (min(4.2, cw * .8) / 2, plat))])}" stroke="{INK}" stroke-width=".9" stroke-linecap="round"/>'
        elif fx & {"temp_implant_crown", "prosthesis_temp"}:      # a fixed temporary wins over a removable denture
            icp, plat = _implant_crown_path(g)
            base += (f'<path d="{icp}" fill="{TEMP}" fill-opacity=".85" stroke="{TEMP_DEEP}" stroke-width=".9" '
                     f'stroke-dasharray="2 1.6" stroke-linejoin="round"/>')
        elif "denture" in fx:
            base += f'<path d="{g["crown"]}" fill="#ffffff" stroke="{INK}" stroke-width=".8" stroke-linejoin="round"/>'
        elif fx & {"implant", "a4_future", "a4_new"} and "healing_cap" not in fx:
            base += (f'<path d="{g["crown"]}" fill="#ffffff" fill-opacity=".5" stroke="{INK}" stroke-width=".75" '
                     f'stroke-dasharray="2 1.6" stroke-linejoin="round"/>')
        elif "abutment" in fx:
            base += (f'<path d="{g["crown"]}" fill="none" stroke="{INK}" stroke-width=".75" stroke-dasharray="2 1.6" stroke-linejoin="round"/>')
        if fx & {"prosthesis", "prosthesis_temp", "denture"} and "flange_local" in fx:
            fl = _rect(g, -w / 2 - .5, hc - .9, w / 2 + .5, hc + 2.8, .6)
            base += f'<path d="{fl}" fill="{PINK}" stroke="{PINK_EDGE}" stroke-width=".5"/>'
    elif "extraction" in fx:
        # the tooth that cannot be saved: dashed outline, darkened root, a dark cavity in the crown and an inflamed tip
        base += (f'<path d="{g["sil"]}" fill="{DECAY}" fill-opacity=".35" stroke="{INK}" stroke-width=".75" stroke-dasharray="2 1.6" stroke-linejoin="round"/>')
        cav = _ellipse_pts(g, w * .08, hc * .32, w * .2, hc * .2)
        base += f'<g clip-path="url(#{clip})"><path d="{cav}" fill="{DECAY_DEEP}"/></g>'
        x, y, h = g["lobes"][0]
        base += f'<path d="{_ellipse_pts(g, x, y - h * 1.2, 1.7, 1.4)}" fill="{INFLAMED}" fill-opacity=".85"/>'
    else:
        base += f'<path d="{g["sil"]}" fill="{ROOT if active else "#f7f9fb"}"/>'
        base += f'<path d="{g["crown"]}" fill="#ffffff"/>'
        base += _facets(g, clip, 1 if active else .6)
        base += f'<path d="{g["relief"]}" fill="none" stroke="{"#c9d2dc" if active else "#dfe5ec"}" stroke-width=".5" stroke-linecap="round"/>'
        # root canal layers
        if "endo" in fx:
            ch = _rect(g, -cw * .22, hc * .55, cw * .22, hc * .9, 1)
            base += f'<path d="{ch}" fill="{ENDO}"/>'
            base += "".join(f'<path d="{_canal(g, lb)}" fill="none" stroke="{ENDO_DEEP}" stroke-width="1.3" stroke-linecap="round"/>' for lb in g["lobes"])
        if "fiber" in fx:
            x, y, h = g["lobes"][0]
            post = _p(g, [("M", (0, hc * .7)), ("Q", (x * .5, hc + (y - hc) * .2), (x * .8, hc + (y - hc) * .5))])
            base += f'<path d="{post}" fill="none" stroke="{ENDO_DEEP}" stroke-width="2.1" stroke-linecap="round"/>'
            base += f'<path d="{post}" fill="none" stroke="#ffffff" stroke-width=".8" stroke-linecap="round"/>'
        if "post_removal" in fx:
            x, y, h = g["lobes"][0]
            post = _p(g, [("M", (0, hc * .7)), ("Q", (x * .5, hc + (y - hc) * .2), (x * .8, hc + (y - hc) * .5))])
            base += f'<path d="{post}" fill="none" stroke="{ENDO_DEEP}" stroke-width="1.1" stroke-dasharray="1.6 1.4" stroke-linecap="round"/>'
        # crown layers, from the inside out
        if "core" in fx:
            base += f'<path d="{_stump(g)}" fill="{CORE}" stroke="{CORE_DEEP}" stroke-width=".7"/>'
        if "filling" in fx:
            front = g["kind"] in ("incisor", "canine")
            spot = _ellipse_pts(g, w * .04, hc * (.45 if front else .2), w * (.2 if front else .24), hc * (.16 if front else .16))
            base += f'<g clip-path="url(#{clip})"><path d="{spot}" fill="{RESTO}" stroke="{RESTO_DEEP}" stroke-width=".6"/></g>'
        if "aesthetic" in fx:
            band = _rect(g, -w, -1, w, hc * .4, 0)
            base += f'<g clip-path="url(#{clip})"><path d="{band}" fill="{RESTO}"/></g>'
        if "onlay" in fx:
            cap = _p(g, [("M", (-w, -1)), ("L", (w, -1)), ("L", (w, hc * .42)), ("Q", (w * .2, hc * .55), (0, hc * .44)),
                         ("Q", (-w * .25, hc * .34), (-w, hc * .48)), ("Z",)])
            base += f'<g clip-path="url(#{clip})"><path d="{cap}" fill="{RESTO}" stroke="{RESTO_DEEP}" stroke-width=".6"/></g>'
        if "modeling" in fx:
            grid = []
            step = w / 5
            xg = -w / 2
            while xg <= w / 2:
                grid += [("M", (xg, 0)), ("L", (xg, hc))]
                xg += step
            yg = 0
            while yg <= hc:
                grid += [("M", (-w / 2, yg)), ("L", (w / 2, yg))]
                yg += hc / 5
            base += f'<g clip-path="url(#{clip})"><path d="{_p(g, grid)}" stroke="{MODEL}" stroke-width=".5"/></g>'
        if "crown_removal" in fx and not fx & {"crown", "temp_crown"}:
            base += f'<path d="{g["crown"]}" fill="url(#{uid}o)" stroke="{INK}" stroke-width=".7" stroke-dasharray="2 1.4"/>'
        if "crown" in fx:
            base += f'<path d="{g["crown"]}" fill="{CROWN}" stroke="{INK}" stroke-width=".8" stroke-linejoin="round"/>'
            base += _facets(g, clip, 1.4)
            base += f'<path d="{g["relief"]}" fill="none" stroke="#ffffff" stroke-opacity=".5" stroke-width=".5" stroke-linecap="round"/>'
        elif "temp_crown" in fx:
            base += (f'<path d="{g["crown"]}" fill="{TEMP}" fill-opacity=".8" stroke="{TEMP_DEEP}" stroke-width=".9" '
                     f'stroke-dasharray="2 1.6" stroke-linejoin="round"/>')
        base += f'<path d="{g["sil"]}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>'
        base += f'<path d="{g["cej"]}" fill="none" stroke="{stroke}" stroke-width="{sw * .6:.2f}"/>'

    # on top: gum, tartar, trays
    if "soft_tissue" in fx:
        band = _rect(g, -w * .56, hc - .6, w * .56, hc + hr * .18, 1)
        over += f'<path d="{band}" fill="{GUM}" fill-opacity=".8" stroke="{GUM_DEEP}" stroke-width=".5"/>'
    if "srp" in fx:
        for side in (-1, 1):
            over += f'<path d="{_ellipse_pts(g, side * cw * .5, hc + hr * .14, .55, 1.5)}" fill="{SAND}" stroke="{SAND_EDGE}" stroke-width=".5"/>'
    if "crown_lengthening" in fx:
        line = _p(g, [("M", (-w * .6, hc + hr * .14)), ("L", (w * .6, hc + hr * .14))])
        over += f'<path d="{line}" stroke="{GUM_DEEP}" stroke-width="1.2" stroke-dasharray="2 1.4"/>'
    if fx & {"aligner", "retention_tray", "splint"}:
        thick = 3.4 if "splint" in fx else 1.8
        over += (f'<path d="{g["crown"]}" fill="{MODEL}" fill-opacity="{.3 if "splint" in fx else .14}" stroke="{TEMP_DEEP}" '
                 f'stroke-width="{thick}" stroke-opacity=".8" stroke-linejoin="round"/>')
        if "aligner" in fx and g["kind"] in ("canine", "premolar"):
            over += f'<path d="{_rect(g, -w * .2, hc * .38, w * .2, hc * .62, .4)}" fill="{TEMP_DEEP}"/>'
    if "separation" in fx:
        line = _p(g, [("M", (w / 2 + .3, hc * .05)), ("L", (w / 2 + .3, hc * .7))])
        over += f'<path d="{line}" stroke="{RESTO_DEEP}" stroke-width="1.2" stroke-linecap="round"/>'
    return clipdef, under, base, over


def fx_tilt(fx):
    for f in fx:
        if isinstance(f, str) and f.startswith("tilt:"):
            return float(f[5:])
    return 0


def expand_jaw(fx_by_tooth, jaw_fx, known=None):
    """turn jaw-wide effects into per-tooth ones; known — {jaw: {tooth: tilt}} implants the whole plan places"""
    fx = {n: set(v) for n, v in fx_by_tooth.items()}
    for jaw, effects in jaw_fx.items():
        if not effects:
            continue
        teeth = G.UPPER if jaw == "upper" else G.LOWER
        arch = effects & FULL_ARCH
        sites = implant_sites(jaw, effects, (known or {}).get(jaw))
        implantation = effects & {"all_on_4", "all_on_6"}
        # one prosthesis drawn per jaw: the permanent one wins over the temporary one in the same stage
        prosthesis = ("prosthesis" if effects & {"superstructure", "superstructure_6"} else
                      "prosthesis_temp" if "superstructure_temp" in effects else None)
        last = max([6] + [n % 10 for n in sites]) if arch else (7 if "denture" in effects else 6)
        for n in teeth:
            pos = n % 10
            e = fx.setdefault(n, set())
            if effects & (FULL_ARCH | {"denture"}) and pos > last:
                e.add("absent")
                continue
            own_implant = bool(e & IMPLANT_EFFECTS)      # a single implant of this stage is drawn by its own effect
            if implantation:
                e.add("a4_future")
                if n in sites:
                    e.add("a4_new")
            if prosthesis:
                e.add(prosthesis)
                if n in sites and not own_implant:
                    e.add("a4_metal")
            if n in sites and (implantation or prosthesis) and not own_implant:
                e.add(f"tilt:{sites[n]}")
            if "denture" in effects:
                e.add("denture")
            for t in ("aligner", "retention_tray", "splint"):
                if t in effects:
                    e.add(t)
            if "retainer" in effects and pos <= 3:
                e.add("retainer")
    return fx


def stage_chart(fx_by_tooth, jaw_fx=None, width=600, known=None):
    uid = f"s{next(_ids)}"
    fx = expand_jaw(fx_by_tooth, jaw_fx or {}, known)
    L = G.chart_layout(width)
    s = L["s"]
    clips, unders, bases, overs, nums = [], [], [], [], []
    retainer_pts = {"upper": [], "lower": []}
    flange = {"upper": [], "lower": []}
    for jaw, seq, y0 in (("upper", G.UPPER, L["occl_up"]), ("lower", G.LOWER, L["occl_lo"])):
        for n in seq:
            e = fx.get(n, set())
            g = G.tooth_geom(n, L["centres"][n], y0, s, jaw == "upper")
            # "ctx" — context from earlier stages (an implant already in place): drawn, but the tooth is not worked on now
            on = bool({x for x in e if not x.startswith("tilt:") and x not in ("absent", "ctx")})
            c, u, b, o = draw_tooth(g, e, uid, active=on)
            clips.append(c), unders.append(u), bases.append(b), overs.append(o)
            if "retainer" in e:
                retainer_pts[jaw].append(g["tf"](0, g["hc"] * .5))
            if e & {"prosthesis", "prosthesis_temp", "denture"}:
                hc, w = g["hc"], g["w"]
                a, b = sorted([g["tf"](-w / 2 - .35, hc - 1.1), g["tf"](w / 2 + .35, hc - 1.1)])
                ta, tb = sorted([g["tf"](-w / 2 - .35, hc + 3.4), g["tf"](w / 2 + .35, hc + 3.4)])
                flange[jaw].append((a, g["tf"](0, hc + .5), b, ta, tb))
            ny = L["num_h"] - 1.5 if jaw == "upper" else L["height"] - 1.5
            nums.append(f'<text x="{L["centres"][n]:.1f}" y="{ny:.1f}" class="{"ch-num-on" if on else "ch-num"}" text-anchor="middle">{n}</text>')
    for teeth in flange.values():
        if not teeth:
            continue
        teeth.sort(key=lambda t: t[0][0])
        ys = [p[1] for t in teeth for p in (t[3], t[4])]
        upper_jaw = teeth[0][3][1] < teeth[0][0][1]
        yt = min(ys) if upper_jaw else max(ys)
        x0, x1 = teeth[0][3][0], teeth[-1][4][0]
        d = f"M{x0:.1f} {yt:.1f} L{x1:.1f} {yt:.1f}"
        for a, m, b, _, _ in reversed(teeth):
            d += f" L{b[0]:.1f} {b[1]:.1f} Q{m[0]:.1f} {m[1] + (m[1] - b[1]) * .9:.1f} {a[0]:.1f} {a[1]:.1f}"
        d += "Z"
        overs.append(f'<path d="{d}" fill="{PINK}" stroke="{PINK_EDGE}" stroke-width=".7" stroke-linejoin="round"/>')
    for pts in retainer_pts.values():
        if pts:
            pts.sort()
            d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
            overs.append(f'<path d="{d}" fill="none" stroke="{METAL_DEEP}" stroke-width="1.8" stroke-linecap="round"/>')
            overs += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.9" fill="{METAL}" stroke="{METAL_DEEP}" stroke-width=".6"/>' for x, y in pts]
    guide = (f'<line x1="0" y1="{L["occl"]:.1f}" x2="{width}" y2="{L["occl"]:.1f}" class="ch-line"/>'
             f'<line x1="{L["mid"]:.1f}" y1="{L["num_h"] + 1:.1f}" x2="{L["mid"]:.1f}" y2="{L["bot"]:.1f}" class="ch-line"/>')
    defs = _defs(uid).replace("</defs>", "".join(clips) + "</defs>")
    h = L["height"]
    return (f'<svg class="chart stage-chart" width="{width}" height="{h:.0f}" viewBox="0 0 {width} {h:.1f}" role="img" '
            f'aria-label="Зубна формула етапу" xmlns="http://www.w3.org/2000/svg">{defs}{guide}{"".join(unders)}'
            f'{"".join(bases)}{"".join(overs)}{"".join(nums)}</svg>')


# ---- legend: one tooth per effect ------------------------------------------------------
GLYPH_TOOTH = {"aesthetic": 21, "sinus_lift": 26, "retainer": 31, "separation": 35, "aligner": 34, "retention_tray": 36,
               "splint": 36, "denture": 36, "superstructure": 36, "superstructure_temp": 36, "all_on_4": 35, "filling": 36,
               "crown_lengthening": 36}


def glyph(effect, size=34):
    """one tooth showing the effect, for the legend"""
    uid = f"g{next(_ids)}"
    n = GLYPH_TOOTH.get(effect, 36)
    upper = n < 30
    s = 2.0
    if effect == "sinus_lift":          # upper tooth, roots up — the lifted floor sits above them
        g = G.tooth_geom(n, 15, 38, s, True)
    else:
        g = G.tooth_geom(n, 15, 3.5, s, upper, grow_down=True)
    fx = {effect}
    if effect in ("all_on_4", "all_on_6"):
        fx = {"a4_new", "a4_future"}
    elif effect in ("superstructure", "superstructure_6"):
        fx = {"prosthesis", "a4_metal", "flange_local"}
    elif effect == "superstructure_temp":
        fx = {"prosthesis_temp", "a4_metal", "flange_local"}
    elif effect == "denture":
        fx = {"denture", "flange_local"}
    c, u, b, o = draw_tooth(g, fx, uid)
    if effect == "retainer":
        x, y = g["tf"](0, g["hc"] * .5)
        o += (f'<path d="M{x - 13:.1f} {y:.1f}H{x + 13:.1f}" stroke="{METAL_DEEP}" stroke-width="1.8" stroke-linecap="round"/>'
              f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="{METAL}" stroke="{METAL_DEEP}" stroke-width=".6"/>')
    return (f'<svg width="{size * 30 / 46:.0f}" height="{size}" viewBox="0 0 30 46" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
            f'{_defs(uid).replace("</defs>", c + "</defs>")}{u}{b}{o}</svg>')
