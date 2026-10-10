"""Schematic dental illustrations in the FrankoLab palette (SVG, 160x160).

Language of every picture:
- neutral anatomy: tooth white with a graphite outline and a soft shade for volume,
  gum muted rose, bone pale storm with dots;
- what the procedure does is filled with Storm Blue (accent);
- future / temporary parts are dashed.
Proportions are deliberately compact (crown : root ≈ 1 : 1.3) so teeth read as friendly icons,
not anatomy charts. A crown on an implant emerges from the implant platform with no neck:
one continuous outline, the joint marked by a single line.
"""
import math

INK = "#474a50"
TOOTH = "#ffffff"
SHADE = "#edf1f6"
GUM = "#ead3cb"
GUM_EDGE = "#c9a99d"
BONE = "#e3e8ef"
BONE_DOT = "#b9c3cf"
ACCENT = "#99aabe"
ACCENT_SHADE = "#8a9cb2"
ACCENT_DEEP = "#6f839c"
METAL = "#cfd5dc"
METAL_SHADE = "#b4bcc6"
SAND = "#d8c3a5"
SAND_EDGE = "#a88f6c"
SKY_LIGHT = "#d6e7fc"

SW = f'stroke="{INK}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"'

# ---- shared geometry ---------------------------------------------------------------
# crown top of a molar (cusps, groove, height of contour), from the left cervical point
# (57,90) round to the right cervical point (103,90)
CROWN_TOP = ("C55 85 50 79 50 71C50 63 54 58 61 57C67 56 72 58.5 76 59.5Q80 60.5 84 59.5"
             "C88 58.5 93 56 99 57C106 58 110 63 110 71C110 79 105 85 102 90")
# natural molar: crown + two roots
MOLAR = ("M58 90" + CROWN_TOP +
         "C100.5 102 98.5 116 96.5 127C95.5 134 92 137 89.5 135C87.5 133 87 127 86 120"
         "C85 113 83.5 108 80 107C76.5 108 75 113 74 120C73 127 72.5 133 70.5 135"
         "C68 137 64.5 134 63.5 127C61.5 116 59.5 102 58 90Z")
# anatomical crown only (closed along the cemento-enamel junction)
CROWN = "M58 90" + CROWN_TOP + "Q80 93 58 90Z"
# crown on an implant: same crown, emerging from the implant platform (70..90 at y=104)
IMPLANT_CROWN = "M70 104C66 99 60.5 95 58 90" + CROWN_TOP + "C99.5 95 94 99 90 104Z"
# soft shade on the right flank of the crown and of the right root
CROWN_SHADE = "M97 58C105 59 108.5 64 108.5 71C108.5 78.5 104.5 84.5 101 89.5L95.5 89.5C99 81 100 68 97 58Z"
ROOT_SHADE = "M100 92C98.5 104 97 117 95 127C94.5 131 93 133.5 91.3 134C92.6 126 94 110 95.5 92Z"
# implant body: platform at the bone crest (y = 104), tapered, round apex
IMPLANT = "M70 104H90C90.5 116 89.5 128 87 136.5Q80 146 73 136.5C70.5 128 69.5 116 70 104Z"


def _defs(uid):
    return (f'<defs><pattern id="bone{uid}" width="9" height="9" patternUnits="userSpaceOnUse">'
            f'<rect width="9" height="9" fill="{BONE}"/><circle cx="2.5" cy="3" r="1.1" fill="{BONE_DOT}"/>'
            f'<circle cx="7" cy="7.2" r=".8" fill="{BONE_DOT}"/></pattern>'
            f'<clipPath id="crown{uid}"><path d="{CROWN}"/></clipPath></defs>')


def _jaw(uid):
    """bone only: it sits behind the tooth"""
    return (f'<path d="M8 106Q80 99 152 106V142Q152 150 144 150H16Q8 150 8 142Z" '
            f'fill="url(#bone{uid})" stroke="{BONE_DOT}" stroke-width="1"/>')


def _gum():
    """gum in front of the tooth, translucent: the part under the gum stays visible but recedes"""
    return (f'<path d="M8 97C36 93 58 89 80 89.5C102 89 124 93 152 97V109Q80 101 8 109Z" '
            f'fill="{GUM}" fill-opacity=".72"/>'
            f'<path d="M8 97C36 93 58 89 80 89.5C102 89 124 93 152 97" fill="none" stroke="{GUM_EDGE}" stroke-width="1"/>')


def _tooth():
    return (f'<path d="{MOLAR}" fill="{TOOTH}"/>'
            f'<path d="{CROWN_SHADE}" fill="{SHADE}"/><path d="{ROOT_SHADE}" fill="{SHADE}"/>'
            f'<path d="{MOLAR}" fill="none" {SW}/>')


def _threads(color=INK):
    out = ""
    for i, y in enumerate((111, 118, 125, 132)):
        half = 11.5 - i * 0.9
        out += f'<path d="M{80 - half:.1f} {y + 2.2}L{80 + half:.1f} {y - 2.2}" stroke="{color}" stroke-width="1.3" stroke-linecap="round"/>'
    return out


def _sparkle(cx, cy, r, fill=ACCENT):
    k = r * 0.28
    return (f'<path d="M{cx} {cy - r}L{cx + k} {cy - k}L{cx + r} {cy}L{cx + k} {cy + k}L{cx} {cy + r}'
            f'L{cx - k} {cy + k}L{cx - r} {cy}L{cx - k} {cy - k}Z" fill="{fill}" stroke="{INK}" stroke-width="1.1" stroke-linejoin="round"/>')


def svg(body, uid, label):
    return (f'<svg viewBox="0 0 160 160" width="160" height="160" role="img" aria-label="{label}" '
            f'xmlns="http://www.w3.org/2000/svg">{_defs(uid)}{body}</svg>')


# ---- pictures ------------------------------------------------------------------------
def implant():
    """Встановлення імплантату: імплантат у кістці, майбутня коронка пунктиром."""
    u = "im"
    body = _jaw(u)
    body += (f'<path d="{IMPLANT_CROWN}" fill="#ffffff" fill-opacity=".55" stroke="{INK}" stroke-width="1.5" '
             f'stroke-dasharray="4 3.2" stroke-linejoin="round"/>')
    body += f'<path d="{IMPLANT}" fill="{ACCENT}" {SW}/>' + _threads()
    body += _gum()
    return svg(body, u, "Імплантат у кістці; коронку поставимо пізніше")


def implant_crown():
    """Коронка на імпланті: коронка виходить з платформи імплантату без «шийки»."""
    u = "ic"
    body = _jaw(u)
    body += f'<path d="{IMPLANT}" fill="{METAL}" {SW}/>' + _threads("#8a939e")
    body += f'<path d="{IMPLANT_CROWN}" fill="{ACCENT}" {SW}/>'
    body += f'<path d="{CROWN_SHADE}" fill="{ACCENT_SHADE}" fill-opacity=".55"/>'
    body += f'<path d="{IMPLANT_CROWN}" fill="none" {SW}/>'
    body += f'<path d="M70.5 104H89.5" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>'
    body += _gum()
    return svg(body, u, "Коронка на імпланті")


def crown():
    """Коронка на власному зубі; обточений зуб під нею — пунктиром."""
    u = "cr"
    body = _jaw(u) + _tooth()
    body += f'<path d="{CROWN}" fill="{ACCENT}"/>'
    body += f'<path d="{CROWN_SHADE}" fill="{ACCENT_SHADE}" fill-opacity=".55"/>'
    body += (f'<path d="M61 90C60 82 61 75 64.5 70.5C68.5 67 91.5 67 95.5 70.5C99 75 100 82 99 90" '
             f'fill="none" stroke="{INK}" stroke-width="1.2" stroke-dasharray="3 2.6"/>')
    body += f'<path d="{MOLAR}" fill="none" {SW}/><path d="M58 90Q80 93 102 90" fill="none" {SW}/>'
    body += _gum()
    return svg(body, u, "Коронка на зубі")


def onlay():
    """Накладка: покриває жувальну поверхню й частину горбків, а не весь зуб."""
    u = "on"
    body = _jaw(u) + _tooth()
    body += (f'<g clip-path="url(#crown{u})"><path d="M40 30H125V77C112 73 98 68.5 84 67.5C74 67 66 65 56 61.5L40 59Z" '
             f'fill="{ACCENT}"/><path d="M97 50C106 55 112 63 112 75L101 72C101 63 100 57 97 50Z" fill="{ACCENT_SHADE}" fill-opacity=".55"/>'
             f'<path d="M115 75.5C102 71 96 68.5 84 67.5C74 67 66 65 54 61" fill="none" {SW}/></g>')
    body += f'<path d="{MOLAR}" fill="none" {SW}/>' + _gum()
    return svg(body, u, "Накладка на зуб")


def endo():
    """Лікування каналів: камера й канали заповнені, інструмент входить у зуб."""
    u = "en"
    body = _jaw(u) + _tooth()
    body += f'<path d="M70.5 73Q80 67 89.5 73L88 80.5Q80 77 72 80.5Z" fill="{ACCENT}" stroke="{ACCENT_DEEP}" stroke-width="1"/>'
    body += f'<path d="M73.2 80C71.5 96 69.5 116 67.8 131" stroke="{ACCENT_DEEP}" stroke-width="3.4" stroke-linecap="round" fill="none"/>'
    body += f'<path d="M86.8 80C88.5 96 90.5 116 92.2 131" stroke="{ACCENT_DEEP}" stroke-width="3.4" stroke-linecap="round" fill="none"/>'
    body += _gum()
    body += f'<path d="M103 26L88 70" stroke="{INK}" stroke-width="1.5" stroke-linecap="round"/>'
    body += f'<path d="M105.5 16L101.5 29" stroke="{INK}" stroke-width="5.5" stroke-linecap="round"/>'
    return svg(body, u, "Лікування каналів кореня")


def hygiene():
    """Гігієна: камінь біля ясен знімаємо інструментом, з іншого боку — чисто."""
    u = "hy"
    body = _jaw(u) + _tooth() + _gum()
    body += (f'<path d="M58.5 90.5C55.5 87 54 83 55.5 79.5C58.5 80.5 60.5 85 60.8 90.8Z" fill="{SAND}" stroke="{SAND_EDGE}" stroke-width="1"/>'
             f'<circle cx="56" cy="74.5" r="2.1" fill="{SAND}" stroke="{SAND_EDGE}" stroke-width=".8"/>')
    body += f'<path d="M27 31L48.5 70Q51.5 76 55.5 78" fill="none" stroke="{INK}" stroke-width="1.8" stroke-linecap="round"/>'
    body += f'<path d="M19 17L29.5 35" stroke="{INK}" stroke-width="5.5" stroke-linecap="round"/>'
    body += _sparkle(122, 52, 7) + _sparkle(133, 70, 4.2)
    return svg(body, u, "Професійна гігієна")


def ct_scan():
    """КТ: щелепа зверху всередині кільця сканера, пунктир — площини зрізу."""
    u = "ct"
    cx, cy, a, b = 80, 114, 41, 60   # arch: ellipse arc, front teeth at the top
    # tooth sizes from the midline: (along the arch, across), radius
    sizes = [(8.4, 7, 3), (7.2, 6.6, 3), (8, 8.4, 4), (7.6, 8.6, 3.6), (7.6, 8.8, 3.6), (11, 10.4, 4), (10.4, 10, 4)]
    # arc-length walk along the ellipse
    def pt(t):
        return cx + a * math.sin(t), cy - b * math.cos(t)
    ts = [i * 0.001 for i in range(0, 1800)]
    acc = [0.0]
    for i in range(1, len(ts)):
        x0, y0 = pt(ts[i - 1]); x1, y1 = pt(ts[i])
        acc.append(acc[-1] + math.hypot(x1 - x0, y1 - y0))

    def t_at(s):
        for i, v in enumerate(acc):
            if v >= s:
                return ts[i]
        return ts[-1]
    body = ""
    # jaw bone band under the teeth
    jaw = " ".join(f"{'M' if i == 0 else 'L'}{pt(t)[0]:.1f} {pt(t)[1]:.1f}" for i, t in enumerate([k * 0.05 - 1.75 for k in range(71)]))
    body += f'<path d="{jaw}" fill="none" stroke="{BONE}" stroke-width="21" stroke-linecap="round" stroke-linejoin="round"/>'
    body += f'<path d="{jaw}" fill="none" stroke="url(#bone{u})" stroke-width="19" stroke-linecap="round" stroke-linejoin="round"/>'
    teeth = ""
    for side in (-1, 1):
        s = 0.6
        for w, d, r in sizes:
            mid = t_at(s + w / 2) * side
            x, y = pt(mid)
            ang = math.degrees(math.atan2(b * math.sin(mid), a * math.cos(mid)))
            teeth += (f'<rect x="{x - w / 2:.1f}" y="{y - d / 2:.1f}" width="{w}" height="{d}" rx="{r}" '
                      f'transform="rotate({ang:.1f} {x:.1f} {y:.1f})" fill="{TOOTH}" {SW}/>')
            s += w + 0.9
    body += teeth
    # scanner ring, rotation arrow and slice planes
    body += f'<circle cx="80" cy="86" r="66" fill="none" stroke="{ACCENT}" stroke-width="5" stroke-opacity=".6"/>'
    body += (f'<path d="M127 40A66 66 0 0 1 143 64" fill="none" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>'
             f'<path d="M137.5 60.5L143.2 65L146.5 58.2" fill="none" stroke="{INK}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')
    body += f'<path d="M24 98H136M80 30V146" stroke="{ACCENT_DEEP}" stroke-width="1.3" stroke-dasharray="5 4"/>'
    return svg(body, u, "Комп'ютерна томографія")


ALL = [("Імплантат", implant), ("Коронка на імпланті", implant_crown), ("Коронка", crown),
       ("Накладка", onlay), ("Лікування каналів", endo), ("Професійна гігієна", hygiene),
       ("Комп'ютерна томографія", ct_scan)]


# =====================================================================================
# extended set — same visual language
# =====================================================================================
LIGHT_ACCENT = "#dbe2ea"
OLD = "#e4e6ea"
NS = 'vector-effect="non-scaling-stroke"'
INCISOR = ("M64 90C61 78 59 63 60 53C60.5 48 63 46 68 46H92C97 46 99.5 48 100 53"
           "C101 63 99 78 96 90C94 106 89 124 82.5 137C81 140 79 140 77.5 137C71 124 66 106 64 90Z")
INCISOR_SHADE = "M92 48C96 48 98.5 50 99 54C100 63 98.5 77 95.5 89.5L91 89.5C94 76 95 60 92 48Z"
STUMP = "M61 90C60 82 61 75 64.5 70.5C68.5 67 91.5 67 95.5 70.5C99 75 100 82 99 90Z"


def _tooth_at(cx, s, gum_y=92, crown_fill=None, outline=INK):
    """a scaled molar, centred on cx, its cervical line sitting on gum_y"""
    tx, ty = cx - 80 * s, gum_y - 90 * s
    g = f'<g transform="translate({tx:.2f} {ty:.2f}) scale({s})">'
    g += f'<path d="{MOLAR}" fill="{TOOTH}"/><path d="{CROWN_SHADE}" fill="{SHADE}"/>'
    if crown_fill:
        g += f'<path d="{CROWN}" fill="{crown_fill}"/>'
    g += f'<path d="{MOLAR}" fill="none" stroke="{outline}" stroke-width="{1.6 / s:.2f}" stroke-linejoin="round"/></g>'
    return g


def _arrow_up(x, y1, y2, color=INK):
    return (f'<path d="M{x} {y1}V{y2}M{x - 4.5} {y2 + 4.5}L{x} {y2}L{x + 4.5} {y2 + 4.5}" fill="none" stroke="{color}" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>')


def _arrow_down(x, y1, y2, color=INK):
    return (f'<path d="M{x} {y1}V{y2}M{x - 4} {y2 - 4}L{x} {y2}L{x + 4} {y2 - 4}" fill="none" stroke="{color}" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')


def exam():
    """Огляд, консультація: зуб і стоматологічне дзеркальце."""
    u = "ex"
    body = _jaw(u) + _tooth() + _gum()
    body += f'<path d="M138 18L109 54" stroke="{INK}" stroke-width="3.2" stroke-linecap="round"/>'
    body += f'<circle cx="103" cy="61.5" r="10" fill="#f6f8fb" {SW}/><circle cx="103" cy="61.5" r="6.2" fill="{LIGHT_ACCENT}"/>'
    body += _sparkle(30, 46, 5)
    return svg(body, u, "Огляд і консультація")


def scan():
    """Інтраоральне сканування: сканер і світловий промінь над зубом."""
    u = "sc"
    body = _jaw(u) + _tooth() + _gum()
    body += f'<path d="M108 46L64 58L98 57Z" fill="{ACCENT}" fill-opacity=".35"/>'
    body += f'<path d="M108 46L64 58M108 46L98 57" stroke="{ACCENT_DEEP}" stroke-width="1" stroke-dasharray="2.5 2.5"/>'
    body += f'<path d="M150 14L112 41" stroke="{INK}" stroke-width="15" stroke-linecap="round"/>'
    body += f'<path d="M150 14L112 41" stroke="#ffffff" stroke-width="11.8" stroke-linecap="round"/>'
    body += f'<path d="M118.5 36.5L111.5 41.5" stroke="{ACCENT}" stroke-width="11.8" stroke-linecap="round"/>'
    return svg(body, u, "Цифрове сканування зубів")


def modeling():
    """Цифрове моделювання: майбутній зуб на екрані."""
    u = "md"
    s = .55
    tx, ty = 80 - 80 * s, 24
    body = f'<defs><clipPath id="mdc"><path d="{MOLAR}" transform="translate({tx} {ty}) scale({s})"/></clipPath></defs>'
    body += f'<rect x="20" y="24" width="120" height="86" rx="8" fill="#f6f8fb" {SW}/>'
    body += f'<path d="M68 110L64 128H96L92 110M56 130H104" fill="none" {SW}/>'
    body += f'<g transform="translate({tx} {ty}) scale({s})"><path d="{MOLAR}" fill="{TOOTH}"/></g>'
    lines = "".join(f'<path d="M30 {y}H130" stroke="{ACCENT}" stroke-width="1"/>' for y in range(56, 104, 5))
    lines += "".join(f'<path d="M{x} 50V104" stroke="{ACCENT}" stroke-width=".8" stroke-opacity=".7"/>' for x in range(58, 104, 7))
    body += f'<g clip-path="url(#mdc)">{lines}</g>'
    body += f'<g transform="translate({tx} {ty}) scale({s})"><path d="{MOLAR}" fill="none" stroke="{INK}" stroke-width="{1.6 / s:.2f}"/></g>'
    body += f'<path d="M118 34L128 44M118 44L128 34" stroke="{ACCENT_DEEP}" stroke-width="1.2" stroke-linecap="round"/>'
    return svg(body, u, "Цифрове моделювання зуба")


HEAD = ("M34 140C34 122 30 108 26 96C18 72 20 42 40 27C56 15 84 13 100 22C110 28 114 38 113 50C113 54 112 57 114 60"
        "L124 76C125 78 124 80 121 80.5L116 81C116 84 118 85 117 88L114 90C117 92 117 95 114 97C111 98 111 100 112 103"
        "C114 108 113 114 108 117C100 121 88 120 80 117C74 120 72 128 72 140")
JAW_BAND = "M60 80C58 92 60 102 67 108C78 115 96 117 107 115.5C111 112 111.5 107 110 103L98 100.5C88 99.5 78 96 73 88L67 79Z"




def srp():
    """Глибоке чищення під яснами: камінь на корені, інструмент заходить під ясна."""
    u = "sr"
    body = _jaw(u) + _tooth()
    body += (f'<path d="M58.8 92C57 96 57.5 101 59.6 104.5C61 101 61 96 60.2 92Z" fill="{SAND}" stroke="{SAND_EDGE}" stroke-width="1"/>'
             f'<path d="M100.6 95C102.5 99 102 103 100 106C99 102.5 99.2 98.5 99.9 95Z" fill="{SAND}" stroke="{SAND_EDGE}" stroke-width="1"/>')
    body += _gum()
    body += f'<path d="M26 34L50 90Q53 98 57.5 101" fill="none" stroke="{INK}" stroke-width="1.8" stroke-linecap="round"/>'
    body += f'<path d="M18 19L29 40" stroke="{INK}" stroke-width="5.5" stroke-linecap="round"/>'
    return svg(body, u, "Глибоке чищення під яснами")


def perio_chart():
    """Пародонтологічна карта: тонкий зонд з міліметровими мітками заходить у ясенну кишеню, поруч — карта глибин."""
    u = "pc"
    # probe shaft past the crown's bulge into the pocket along the root; the bands are millimetre marks, the translucent
    # gum in front shows how deep the probe goes
    body = _jaw(u) + _tooth()
    x_at = lambda y: 124 - (y - 30) * 22.8 / 71
    body += f'<path d="M124 30L101.2 101" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>'
    for y0, y1 in ((76, 81.5), (86, 91.5), (96, 100.5)):
        body += f'<path d="M{x_at(y0):.1f} {y0}L{x_at(y1):.1f} {y1}" stroke="{ACCENT_DEEP}" stroke-width="4.2"/>'
    body += _gum()
    body += f'<path d="M132 9L124.6 28" stroke="{INK}" stroke-width="5.5" stroke-linecap="round"/>'
    # the chart: pocket depths around the teeth
    body += f'<rect x="16" y="20" width="44" height="34" rx="5" fill="#f6f8fb" {SW}/>'
    body += "".join(f'<path d="M{x} 26V49" stroke="{LIGHT_ACCENT}" stroke-width="1"/>' for x in (27, 38, 49))
    body += (f'<path d="M21 42L27 38L32 44L38 35L43 40L49 33L55 39" fill="none" stroke="{ACCENT_DEEP}" stroke-width="1.6" '
             f'stroke-linecap="round" stroke-linejoin="round"/>')
    return svg(body, u, "Пародонтологічна карта — вимірювання ясенних кишень")


def interdental_brush():
    """Міжзубний йоржик: щіточка між двома зубами біля ясен, ручка — вгору вбік."""
    u = "ib"
    teeth = _tooth_at(54, .62) + _tooth_at(106, .62)
    body = _jaw(u) + teeth + _gum()
    body += f'<path d="M80 80L124 36" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>'
    body += f'<path d="M124 36L144 16" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>'
    body += f'<path d="M124 36L144 16" stroke="{ACCENT}" stroke-width="6.2" stroke-linecap="round"/>'
    # bristle head in the gap: a small soft cylinder, its bristles across the wire
    body += f'<ellipse cx="80" cy="82" rx="6.4" ry="9" fill="{LIGHT_ACCENT}" stroke="{ACCENT_DEEP}" stroke-width="1.1"/>'
    body += "".join(f'<path d="M{80 - w:.1f} {y}H{80 + w:.1f}" stroke="{ACCENT_DEEP}" stroke-width=".9" stroke-linecap="round"/>'
                    for y, w in ((76, 3.6), (79, 5.2), (82, 5.8), (85, 5.2), (88, 3.6)))
    body += f'<path d="M80 73V91" stroke="{INK}" stroke-width="1.3" stroke-linecap="round"/>'
    return svg(body, u, "Міжзубний йоржик")


def _incisor_at(cx, s, gum_y=92):
    """a scaled front tooth, centred on cx, its cervical line on gum_y"""
    tx, ty = cx - 80 * s, gum_y - 90 * s
    return (f'<g transform="translate({tx:.2f} {ty:.2f}) scale({s})"><path d="{INCISOR}" fill="{TOOTH}"/>'
            f'<path d="{INCISOR_SHADE}" fill="{SHADE}"/><path d="{INCISOR}" fill="none" stroke="{INK}" '
            f'stroke-width="{1.6 / s:.2f}" stroke-linejoin="round"/></g>')


def braces():
    """Брекет-система: на передніх зубах — замочки, через них проходить дуга."""
    u = "br"
    xs = (46, 80, 114)
    body = _jaw(u) + "".join(_incisor_at(x, .62) for x in xs) + _gum()
    body += f'<path d="M26 77Q80 73 134 77" fill="none" stroke="{INK}" stroke-width="1.8" stroke-linecap="round"/>'
    for x in xs:
        body += (f'<rect x="{x - 5.5}" y="{70.5}" width="11" height="10" rx="2" fill="{METAL}" stroke="{INK}" stroke-width="1.2"/>'
                 f'<path d="M{x - 5.5} 75.5H{x + 5.5}" stroke="{INK}" stroke-width="1"/>'
                 f'<circle cx="{x}" cy="75.5" r="2.2" fill="none" stroke="{ACCENT_DEEP}" stroke-width="1.2"/>')
    return svg(body, u, "Брекет-система")


def mini_implant():
    """Ортодонтичний мікроімплант: маленький гвинт у кістці між коренями — опора, від якої тягнуть зуби."""
    u = "mi"
    body = _jaw(u) + _tooth_at(46, .62) + _tooth_at(114, .62)
    # the screw between the roots, its head just above the gum
    body += (f'<path d="M76 97H84L82.6 121Q80 127 77.4 121Z" fill="{METAL}" stroke="{INK}" stroke-width="1.3" stroke-linejoin="round"/>'
             + "".join(f'<path d="M76.4 {y + 1.6}L83.6 {y - 1.6}" stroke="#8a939e" stroke-width="1.1"/>' for y in (102, 107, 112, 117))
             + f'<rect x="73" y="84" width="14" height="13" rx="2.5" fill="{METAL}" stroke="{INK}" stroke-width="1.3"/>'
             + f'<path d="M73 90.5H87" stroke="{INK}" stroke-width="1"/>')
    body += _gum()
    # bracket on the tooth and the elastic pulling toward the screw
    body += f'<rect x="40" y="66" width="12" height="9" rx="2" fill="{METAL}" stroke="{INK}" stroke-width="1.2"/>'
    body += f'<path d="M52 71L75 87" stroke="{ACCENT_DEEP}" stroke-width="2.4" stroke-linecap="round"/>'
    return svg(body, u, "Ортодонтичний мікроімплант")


def whitening():
    """Відбілювання: лампа над передніми зубами, світло на зубах, зуби світлішають."""
    u = "wh"
    body = _jaw(u)
    body += f'<path d="M58 34L46 70H114L102 34Z" fill="{SKY_LIGHT}" fill-opacity=".7"/>'
    body += _incisor_at(64, .72) + _incisor_at(96, .72) + _gum()
    body += f'<rect x="50" y="16" width="60" height="18" rx="7" fill="#f6f8fb" {SW}/>'
    body += f'<path d="M58 34H102" stroke="{ACCENT_DEEP}" stroke-width="2.6" stroke-linecap="round"/>'
    body += f'<path d="M110 25H132" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    body += _sparkle(124, 56, 6) + _sparkle(36, 52, 4)
    return svg(body, u, "Професійне відбілювання зубів")


def implant_removal():
    """Видалення імплантату: імплантат виходить з кістки, на його місці — лунка."""
    u = "ir"
    body = _jaw(u)
    body += f'<path d="{IMPLANT}" fill="none" stroke="{BONE_DOT}" stroke-width="1.5" stroke-dasharray="3.5 3"/>'
    body += f'<g transform="translate(0 -40)"><path d="{IMPLANT}" fill="#e3e7ec" {SW}/>{_threads("#8a939e")}</g>'
    body += _gum() + _arrow_up(124, 76, 40)
    return svg(body, u, "Видалення імплантату")


def filling():
    """Пломба: відновлена ділянка жувальної поверхні."""
    u = "fi"
    body = _jaw(u) + _tooth()
    body += (f'<g clip-path="url(#crown{u})"><path d="M64 57C69 61 72 70 80 71.5C88 70 91 61 96 57C90 58.5 85 60.5 80 60.8C75 60.5 70 58.5 64 57Z" '
             f'fill="{ACCENT}"/><path d="M66 58C71 63 74 70.5 80 71.5C86 70.5 89 63 94 58" fill="none" {SW}/></g>')
    body += f'<path d="{MOLAR}" fill="none" {SW}/>' + _gum()
    return svg(body, u, "Пломба")


def aesthetic():
    """Естетична реставрація переднього зуба."""
    u = "ae"
    body = _jaw(u)
    body += f'<defs><clipPath id="aec"><path d="{INCISOR}"/></clipPath></defs>'
    body += f'<path d="{INCISOR}" fill="{TOOTH}"/><path d="{INCISOR_SHADE}" fill="{SHADE}"/>'
    body += (f'<g clip-path="url(#aec)"><path d="M50 30H110V66C102 62 94 67 86 64C78 61 70 66 62 63L50 64Z" fill="{ACCENT}"/>'
             f'<path d="M52 63.5C58 66 64 61.5 72 63.5C80 65.5 86 61.5 94 63.5C100 65 104 62 108 63" fill="none" stroke="{INK}" stroke-width="1.3"/></g>')
    body += f'<path d="{INCISOR}" fill="none" {SW}/>' + _gum()
    body += _sparkle(118, 44, 6) + _sparkle(128, 60, 3.6)
    return svg(body, u, "Естетична реставрація переднього зуба")


def core_buildup():
    """Відновлення культі: відбудована опора під майбутню коронку."""
    u = "co"
    body = _jaw(u)
    body += f'<defs><clipPath id="cob"><rect x="0" y="89" width="160" height="71"/></clipPath></defs>'
    body += f'<g clip-path="url(#cob)"><path d="{MOLAR}" fill="{TOOTH}"/><path d="{ROOT_SHADE}" fill="{SHADE}"/><path d="{MOLAR}" fill="none" {SW}/></g>'
    body += f'<path d="{STUMP}" fill="{ACCENT}" {SW}/>'
    body += f'<path d="{CROWN}" fill="none" stroke="{INK}" stroke-width="1.3" stroke-dasharray="4 3.2" stroke-linejoin="round"/>'
    body += _gum()
    return svg(body, u, "Відновлення культі зуба")


def fiber():
    """Зміцнення зуба скловолокном після лікування каналів."""
    u = "fb"
    body = _jaw(u) + _tooth()
    body += f'<path d="M73.2 80C71.5 96 69.5 116 67.8 131M86.8 80C88.5 96 90.5 116 92.2 131" stroke="{ACCENT_DEEP}" stroke-width="3.2" stroke-linecap="round" fill="none"/>'
    mesh = "".join(f'<path d="M{x} 64L{x + 22} 92" stroke="{ACCENT_DEEP}" stroke-width="1"/>' for x in range(40, 112, 6))
    mesh += "".join(f'<path d="M{x} 64L{x - 22} 92" stroke="{ACCENT_DEEP}" stroke-width="1"/>' for x in range(52, 124, 6))
    body += (f'<defs><clipPath id="fbc"><path d="M64 88C62 80 63 72 67 68.5Q80 63 93 68.5C97 72 98 80 96 88Z"/></clipPath></defs>'
             f'<path d="M64 88C62 80 63 72 67 68.5Q80 63 93 68.5C97 72 98 80 96 88Z" fill="{LIGHT_ACCENT}"/>'
             f'<g clip-path="url(#fbc)">{mesh}</g>')
    body += f'<path d="{MOLAR}" fill="none" {SW}/>' + _gum()
    return svg(body, u, "Зміцнення зуба скловолокном")


def crown_removal():
    """Зняття старої коронки: коронку знято, під нею — зуб."""
    u = "cx"
    body = _jaw(u)
    body += f'<defs><clipPath id="cxb"><rect x="0" y="89" width="160" height="71"/></clipPath></defs>'
    body += f'<g clip-path="url(#cxb)"><path d="{MOLAR}" fill="{TOOTH}"/><path d="{ROOT_SHADE}" fill="{SHADE}"/><path d="{MOLAR}" fill="none" {SW}/></g>'
    body += f'<path d="{STUMP}" fill="{TOOTH}" {SW}/>'
    body += f'<g transform="translate(0 -30)"><path d="{CROWN}" fill="{OLD}" {SW}/></g>'
    body += _gum() + _arrow_up(130, 62, 30)
    return svg(body, u, "Зняття старої коронки")


def post_removal():
    """Видалення штифта: штифт виходить з кореневого каналу, місце, де він був, — пунктиром."""
    u = "px"
    body = _jaw(u)
    body += f'<defs><clipPath id="pxb"><rect x="0" y="89" width="160" height="71"/></clipPath></defs>'
    body += f'<g clip-path="url(#pxb)"><path d="{MOLAR}" fill="{TOOTH}"/><path d="{ROOT_SHADE}" fill="{SHADE}"/><path d="{MOLAR}" fill="none" {SW}/></g>'
    body += f'<path d="{STUMP}" fill="{TOOTH}" {SW}/>'
    body += f'<path d="M74 70L72.4 106" stroke="{ACCENT_DEEP}" stroke-width="2.6" stroke-linecap="round" stroke-dasharray="1 4"/>'
    body += f'<path d="M71.3 30H76.7L75.7 60Q74 64 72.3 60Z" fill="{METAL}" {SW}/><rect x="68.5" y="22" width="11" height="8" rx="2" fill="{METAL_SHADE}" {SW}/>'
    body += _gum() + _arrow_up(98, 58, 28)
    return svg(body, u, "Видалення штифта")


DECAY = "#b9a48c"          # darkened, softened tooth tissue
DECAY_DEEP = "#8c7257"
INFLAMED = "#e49a95"       # inflamed area at the root tip


# the silhouette of a molar whose right cusp has broken away: same outline as MOLAR, but between the right cusp
# and the groove the edge drops into a ragged crater instead of running over the cusp
BROKEN_MOLAR = ("M58 90C55 85 50 79 50 71C50 63 54 58 61 57C67 56 72 58.5 76 59.5Q80 60.5 82 60"
                "L84 66L88 63L91 70L95 66L99 72C103 73 106 69 108 71C110 71 110 79 102 90"
                "C100.5 102 98.5 116 96.5 127C95.5 134 92 137 89.5 135C87.5 133 87 127 86 120"
                "C85 113 83.5 108 80 107C76.5 108 75 113 74 120C73 127 72.5 133 70.5 135"
                "C68 137 64.5 134 63.5 127C61.5 116 59.5 102 58 90Z")


def _damaged_tooth():
    """a tooth that cannot be saved: the right cusp has broken away over a deep cavity that reached the pulp,
    the roots are darkened, one is cracked, with an inflammation at its tip. Same calm language, only the damage
    carries colour."""
    out = f'<path d="{BROKEN_MOLAR}" fill="{TOOTH}"/><path d="{ROOT_SHADE}" fill="{SHADE}"/>'
    # darkened, weakened roots
    out += (f'<path d="M58 90C59.5 102 61.5 116 63.5 127C64.5 134 68 137 70.5 135C72.5 133 73 127 74 120C75 113 76.5 108 80 107'
            f'C83.5 108 85 113 86 120C87 127 87.5 133 89.5 135C92 137 95.5 134 96.5 127C98.5 116 100.5 102 102 90Z" '
            f'fill="{DECAY}" fill-opacity=".5"/>')
    # the cavity under the broken edge: soft, discoloured tissue around a dark hollow
    out += (f'<path d="M82 60L84 66L88 63L91 70L95 66L99 72C96 78 92 84 86 86C80 87 74 82 72 74C71 68 74 63 78 61Z" '
            f'fill="{DECAY}" fill-opacity=".8"/>')
    out += f'<path d="M80 66C77 70 77 77 81 81C85 84 91 82 93 77C94 73 93 69 91 67C88 67 85 69 83 68C82 67 81 66 80 66Z" fill="{DECAY_DEEP}"/>'
    # crack running from the cavity down the left root
    out += f'<path d="M75 80L70 92L72.5 104L68.5 118" fill="none" stroke="{DECAY_DEEP}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>'
    # inflammation at the apex of the left root
    out += f'<ellipse cx="67" cy="134" rx="10.5" ry="8" fill="{INFLAMED}" fill-opacity=".5"/><ellipse cx="67" cy="134" rx="5.5" ry="4.2" fill="{INFLAMED}"/>'
    out += f'<path d="{BROKEN_MOLAR}" fill="none" {SW}/>'
    return out


def extraction():
    """Видалення зуба, який неможливо зберегти: глибока порожнина до нерва, тріснутий потемнілий корінь,
    запалення біля верхівки. Зуб виходить із лунки, лунка — пунктиром."""
    u = "xt"
    body = _jaw(u)
    body += (f'<path d="M58 90C59.5 102 61.5 116 63.5 127C64.5 134 68 137 70.5 135C72.5 133 73 127 74 120C75 113 76.5 108 80 107'
             f'C83.5 108 85 113 86 120C87 127 87.5 133 89.5 135C92 137 95.5 134 96.5 127C98.5 116 100.5 102 102 90" '
             f'fill="#d3dae3" stroke="{INK}" stroke-width="1.2" stroke-dasharray="3.5 3"/>')
    body += _gum()
    body += f'<g transform="translate(0 -30)">' + _damaged_tooth() + '</g>'
    body += _arrow_up(130, 60, 26)
    return svg(body, u, "Видалення зуба, який неможливо зберегти")


def hopeless_tooth():
    """Зуб, який неможливо зберегти, на місці: для пояснення причини видалення."""
    u = "hp"
    body = _jaw(u) + _damaged_tooth() + _gum()
    return svg(body, u, "Зуб, який неможливо зберегти")


def crown_lengthening():
    """Видовження клінічної коронки: край ясен опускаємо, відкриваючи більше зуба."""
    u = "cl"
    body = _jaw(u) + _tooth()
    body += (f'<path d="M8 97C30 94 46 93 54 98C60 101 63 102 66 100.5H94C97 102 100 101 106 98C114 93 130 94 152 97V109Q80 101 8 109Z" '
             f'fill="{GUM}" fill-opacity=".72"/>'
             f'<path d="M8 97C30 94 46 93 54 98C60 101 63 102 66 100.5M94 100.5C97 102 100 101 106 98C114 93 130 94 152 97" fill="none" stroke="{GUM_EDGE}" stroke-width="1"/>')
    body += f'<path d="M40 90.5C52 89 64 89 80 89.5C96 89 108 89 120 90.5" fill="none" stroke="{ACCENT_DEEP}" stroke-width="1.3" stroke-dasharray="3.5 3"/>'
    body += _arrow_down(46, 82, 95, ACCENT_DEEP) + _arrow_down(114, 82, 95, ACCENT_DEEP)
    return svg(body, u, "Видовження клінічної коронки")


def bone_graft():
    """Кісткова пластика: заштрихований кістковий матеріал біля імплантату під мембраною (як у синус-ліфтингу)."""
    u = "bg"
    body = _hatch(u) + _jaw(u)
    graft = "M28 103C31 96 46 93 60 94.5L70 97V114C58 117 42 116 31 110Z"
    body += f'<path d="{graft}" fill="url(#hatch{u})" stroke="{ACCENT_DEEP}" stroke-width="1.1" stroke-linejoin="round"/>'
    body += f'<path d="{IMPLANT}" fill="{METAL}" {SW}/>' + _threads("#8a939e")
    body += f'<path d="M24 100C34 92 52 91 70 95.5" fill="none" stroke="{ACCENT_DEEP}" stroke-width="2.4" stroke-linecap="round"/>'
    body += (f'<path d="{IMPLANT_CROWN}" fill="#ffffff" fill-opacity=".55" stroke="{INK}" stroke-width="1.4" '
             f'stroke-dasharray="4 3.2" stroke-linejoin="round"/>')
    body += _gum()
    return svg(body, u, "Нарощування кістки")


def soft_tissue():
    """Пластика м'яких тканин: під яснами додаємо тканину — ясна стають товщими навколо коронки."""
    u = "st"
    body = _jaw(u)
    body += f'<path d="{IMPLANT}" fill="{METAL}" {SW}/>' + _threads("#8a939e")
    body += f'<path d="{IMPLANT_CROWN}" fill="{TOOTH}"/><path d="{CROWN_SHADE}" fill="{SHADE}"/><path d="{IMPLANT_CROWN}" fill="none" {SW}/>'
    body += f'<path d="M70.5 104H89.5" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>'
    graft = ("M28 99C38 95 48 93 56 93C58.5 96.5 62 100 67 103C54 105.5 40 105 28 103Z"
             "M132 99C122 95 112 93 104 93C101.5 96.5 98 100 93 103C106 105.5 120 105 132 103Z")
    body += f'<path d="{graft}" fill="{ACCENT}" fill-opacity=".8"/>'
    body += (f'<path d="M8 95C30 90.5 48 87 60 87.5C68 88 74 89 80 89C86 89 92 88 100 87.5C112 87 130 90.5 152 95V109Q80 101 8 109Z" '
             f'fill="{GUM}" fill-opacity=".6"/>'
             f'<path d="M8 95C30 90.5 48 87 60 87.5C68 88 74 89 80 89C86 89 92 88 100 87.5C112 87 130 90.5 152 95" fill="none" stroke="{GUM_EDGE}" stroke-width="1"/>')
    body += f'<path d="{graft}" fill="none" stroke="{ACCENT_DEEP}" stroke-width="1" stroke-dasharray="3 2.4"/>'
    return svg(body, u, "Пластика ясен")


def healing_cap():
    """Формувач ясен на імплантаті."""
    u = "hc"
    body = _jaw(u)
    body += f'<path d="{IMPLANT}" fill="{METAL}" {SW}/>' + _threads("#8a939e")
    body += f'<path d="M71 104C69 98 67 92 67.5 86.5C68 83.5 70 82 73 82H87C90 82 92 83.5 92.5 86.5C93 92 91 98 89 104Z" fill="{ACCENT}" {SW}/>'
    body += f'<path d="M76 84.5H84" stroke="{ACCENT_DEEP}" stroke-width="2" stroke-linecap="round"/>'
    body += _gum()
    return svg(body, u, "Формувач ясен")




def custom_abutment():
    """Індивідуальний абатмент: перехідна деталь під форму ясен, коронка — пунктиром."""
    u = "ca"
    body = _jaw(u)
    body += f'<path d="{IMPLANT}" fill="{METAL}" {SW}/>' + _threads("#8a939e")
    body += (f'<path d="{IMPLANT_CROWN}" fill="#ffffff" fill-opacity=".55" stroke="{INK}" stroke-width="1.4" '
             f'stroke-dasharray="4 3.2" stroke-linejoin="round"/>')
    body += f'<path d="M70.5 104C67 98 64 93 64 88C64 80 66 74 69 70H91C94 74 96 80 96 88C96 93 93 98 89.5 104Z" fill="{ACCENT}" {SW}/>'
    body += _gum()
    return svg(body, u, "Індивідуальний абатмент")


def temp_crown():
    """Тимчасова коронка: світла, з пунктирним контуром."""
    u = "tc"
    body = _jaw(u) + _tooth()
    body += f'<path d="{CROWN}" fill="{LIGHT_ACCENT}"/>'
    body += f'<path d="{STUMP}" fill="none" stroke="{INK}" stroke-width="1.1" stroke-dasharray="3 2.6"/>'
    body += f'<path d="{CROWN}" fill="none" stroke="{ACCENT_DEEP}" stroke-width="1.7" stroke-dasharray="4 3" stroke-linejoin="round"/>'
    body += _gum()
    return svg(body, u, "Тимчасова коронка")


def temp_implant_crown():
    """Тимчасова коронка на імплантаті."""
    u = "ti"
    body = _jaw(u)
    body += f'<path d="{IMPLANT}" fill="{METAL}" {SW}/>' + _threads("#8a939e")
    body += f'<path d="{IMPLANT_CROWN}" fill="{LIGHT_ACCENT}" stroke="{ACCENT_DEEP}" stroke-width="1.7" stroke-dasharray="4 3" stroke-linejoin="round"/>'
    body += f'<path d="M70.5 104H89.5" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>'
    body += _gum()
    return svg(body, u, "Тимчасова коронка на імплантаті")


def crown_layered():
    """Коронка з нанесенням кераміки: каркас і шари кераміки."""
    u = "cy"
    body = _jaw(u) + _tooth()
    body += f'<path d="{CROWN}" fill="{ACCENT}"/>'
    body += f'<path d="M62 89C60 80 60 72 63 66C66 61.5 72 61 76 63Q80 64.5 84 63C88 61 94 61.5 97 66C100 72 100 80 98 89Z" fill="{ACCENT_SHADE}" fill-opacity=".75" stroke="{ACCENT_DEEP}" stroke-width="1"/>'
    body += f'<path d="{STUMP}" fill="none" stroke="{INK}" stroke-width="1.1" stroke-dasharray="3 2.6"/>'
    body += f'<path d="{MOLAR}" fill="none" {SW}/><path d="M58 90Q80 93 102 90" fill="none" {SW}/>' + _gum()
    body += _sparkle(124, 50, 5.5)
    return svg(body, u, "Коронка з нанесенням кераміки")


def _row_of_teeth(n=3, s=.5, crown_fill=None, gap=36):
    xs = [80 + (i - (n - 1) / 2) * gap for i in range(n)]
    return "".join(_tooth_at(x, s, 92, crown_fill) for x in xs), xs


def _four_implants(fill):
    out = ""
    for x, ang in [(28, -14), (62, 0), (98, 0), (132, 14)]:
        out += (f'<g transform="rotate({ang} {x} 104) translate({x - 80 * .6} {104 - 104 * .6}) scale(.6)">'
                f'<path d="{IMPLANT}" fill="{fill}" stroke="{INK}" stroke-width="2.67"/>{_threads("#8a939e" if fill == METAL else INK)}</g>')
    return out


ARCH_BOTTOM = "C124 91.5 102 89 80 89.5C58 89 36 91.5 16 94.5"








def _tray(xs, s, thick=3.2, attach=False):
    out = ""
    for x in xs:
        tx, ty = x - 80 * s, 92 - 90 * s
        out += (f'<g transform="translate({tx:.2f} {ty:.2f}) scale({s})"><path d="M54 92C47 82 44 72 45 64C46 54 52 50 61 50C68 49.5 73 52.5 77 54.5Q80 55.5 83 54.5'
                f'C87 52.5 92 49.5 99 50C108 50 114 54 115 64C116 72 113 82 106 92Z" fill="{ACCENT}" fill-opacity=".28" stroke="{ACCENT_DEEP}" stroke-width="{thick / 2 / s:.2f}" stroke-linejoin="round"/></g>')
        if attach:
            out += f'<rect x="{x - 3.2:.1f}" y="{92 - 16:.1f}" width="6.4" height="5" rx="1.5" fill="{ACCENT}" stroke="{INK}" stroke-width=".9"/>'
    return out










def separation():
    """Сепарація: між зубами звільняємо частки міліметра простору."""
    u = "se"
    teeth = _tooth_at(56, .62) + _tooth_at(104, .62)
    body = _jaw(u) + teeth + _gum()
    body += f'<path d="M80 30V86" stroke="{ACCENT_DEEP}" stroke-width="3" stroke-linecap="round"/>'
    body += (f'<path d="M66 40H74M74 40L70.5 36.5M74 40L70.5 43.5M94 40H86M86 40L89.5 36.5M86 40L89.5 43.5" '
             f'stroke="{INK}" stroke-width="1.5" stroke-linecap="round" fill="none"/>')
    return svg(body, u, "Сепарація зубів")


def sedation():
    """Лікування уві сні: місяць і зірки."""
    u = "sd"
    body = f'<circle cx="80" cy="84" r="58" fill="#f6f8fb" stroke="{BONE_DOT}" stroke-width="1"/>'
    body += f'<path d="M96 40A44 44 0 1 0 118 112A36 36 0 1 1 96 40Z" fill="{ACCENT}" {SW}/>'
    body += _sparkle(116, 52, 7) + _sparkle(130, 76, 4) + _sparkle(104, 32, 3.5)
    body += f'<path d="M44 132C58 138 102 138 116 132" fill="none" stroke="{ACCENT_DEEP}" stroke-width="1.4" stroke-linecap="round" stroke-dasharray="3 3"/>'
    return svg(body, u, "Лікування уві сні під наглядом анестезіолога")



# =====================================================================================
# upper jaw (panoramic view), arches seen from above, reworked pictures
# =====================================================================================
import graphics as _G

PINK_BASE = "#e6bdb2"        # acrylic base of a prosthesis / denture
PINK_EDGE = "#b98c80"
AIR = "#f8fafc"              # sinus / nasal cavity


def _hatch(uid, color=ACCENT_DEEP, bg=ACCENT):
    return (f'<defs><pattern id="hatch{uid}" width="4.2" height="4.2" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<rect width="4.2" height="4.2" fill="{bg}" fill-opacity=".45"/><path d="M0 0V4.2" stroke="{color}" stroke-width="1.1"/></pattern></defs>')


def _implant_g(hx, hy, angle=0, sx=.85, sy=.85, fill=METAL, up=True, threads="#8a939e"):
    """implant with its platform at (hx, hy); up=True — apex points up (upper jaw)"""
    fy = -sy if up else sy
    return (f'<g transform="translate({hx} {hy}) rotate({angle}) scale({sx} {fy}) translate(-80 -104)">'
            f'<path d="{IMPLANT}" fill="{fill}" stroke="{INK}" stroke-width="{1.6 / sx:.2f}" stroke-linejoin="round"/>'
            f'{_threads(threads)}</g>')


# --- maxilla in a panoramic-like frontal view: bone, nasal cavity, two maxillary sinuses -------
# proportions follow a panoramic X-ray: crowns ~1.6 px per mm, implants ~4.5 mm thick
NOSE = "M66 16C64 28 61 38 61.5 50C62 61 69 68 80 68C91 68 98 61 98.5 50C99 38 96 28 94 16"
SINUS_L = ("M14 42C13 29 22 20 34 19C45 18 53 23 55 31C54 41 47 53 41 62C37 68 31 73 23 73"
           "C16 73 13 68 13 60Z")
CREST_Y = 100


def _maxilla(u):
    body = f'<path d="M8 26Q8 16 20 16H140Q152 16 152 26V95Q80 105 8 95Z" fill="url(#bone{u})" stroke="{BONE_DOT}" stroke-width="1"/>'
    body += f'<path d="{NOSE}Z" fill="{AIR}"/><path d="{NOSE}" fill="none" {SW}/>'
    body += f'<path d="M80 16.5C79 32 81 50 80 65" fill="none" stroke="{INK}" stroke-width="1.2" stroke-linecap="round"/>'
    body += (f'<path d="M65 38C68 35 73 36 75.5 39M84.5 39C87 36 92 35 95 38M63.5 50C67 47 72 48 75.5 51M84.5 51C88 48 93 47 96.5 50" '
             f'fill="none" stroke="{BONE_DOT}" stroke-width="1.1" stroke-linecap="round"/>')
    for t in ("", ' transform="matrix(-1 0 0 1 160 0)"'):
        body += f'<path d="{SINUS_L}" fill="{AIR}" {SW}{t}/>'
    return body


def _upper_gum(opacity=.72):
    return (f'<path d="M8 92Q80 103 152 92V102Q80 114 8 102Z" fill="{GUM}" fill-opacity="{opacity}"/>'
            f'<path d="M8 102Q80 114 152 102" fill="none" stroke="{GUM_EDGE}" stroke-width="1"/>')


def _upper_teeth(s=1.62, k=1.3, y_occl=129, curve=7, gap=.6):
    """frontal (panoramic) row of upper crowns 16..26, the occlusal line curving up toward the molars:
    [(n, cx, crown_path, cervical_y, width)]"""
    out = []
    for side, ns in ((-1, [11, 12, 13, 14, 15, 16]), (1, [21, 22, 23, 24, 25, 26])):
        x = 80 + side * gap / 2
        for n in ns:
            w, cw, hc = _G.ANATOMY["upper"][n % 10][:3]
            cx = x + side * w * s / 2
            y0 = y_occl - ((cx - 80) / 72) ** 2 * curve
            crown = _G.tooth_paths(n, cx, y0, s, True, k)[1]
            out.append((n, cx, crown, y0 - hc * s * k, w * s))
            x += side * (w * s + gap)
    return out


def _flange(teeth, top=93, depth=3.4):
    """pink base of a prosthesis: from the ridge down to a scalloped gingival line around the crowns"""
    ts = sorted(teeth, key=lambda t: t[1])
    left, right = ts[0][1] - ts[0][4] / 2, ts[-1][1] + ts[-1][4] / 2
    d = f"M{left:.1f} {top + 1:.1f}Q80 {top + 9:.1f} {right:.1f} {top + 1:.1f}"
    for i, (n, cx, _, cerv, w) in enumerate(reversed(ts)):
        x1, x0 = cx + w / 2, cx - w / 2
        if i == 0:
            d += f"L{x1:.1f} {cerv + depth:.1f}"
        d += f"Q{cx:.1f} {cerv - 3.2:.1f} {x0:.1f} {cerv + depth:.1f}"
    return d + "Z"


def _crowns(teeth, fill=TOOTH, dashed=False):
    out = ""
    for n, cx, crown, cerv, w in teeth:
        if dashed:
            out += (f'<path d="{crown}" fill="#ffffff" fill-opacity=".6" stroke="{INK}" stroke-width="1.15" '
                    f'stroke-dasharray="2.6 2.2" stroke-linejoin="round"/>')
        else:
            out += f'<path d="{crown}" fill="{fill}" stroke="{INK}" stroke-width="1.25" stroke-linejoin="round"/>'
    return out


# All-on-4 in the upper jaw: two straight implants in front (below the nose), two tilted at the back
# along the front wall of the sinuses. (x, y of the platform, angle, scale x, scale y)
A4_IMPLANTS = [(65, 99.6, 0, .42, .64), (95, 99.6, 0, .42, .64), (28, 96.6, 30, .42, .76), (132, 96.6, -30, .42, .76)]


# All-on-6: two in front, two at the premolars, two at the first molars slightly tilted
A6_IMPLANTS = [(66, 99.8, 0, .4, .62), (94, 99.8, 0, .4, .62), (45, 99.0, 0, .4, .6), (115, 99.0, 0, .4, .6),
               (25, 96.4, 16, .4, .58), (135, 96.4, -16, .4, .58)]


def _a4_implants(fill, threads, places=None):
    return "".join(_implant_g(x, y, a, sx, sy, fill, threads=threads) for x, y, a, sx, sy in (places or A4_IMPLANTS))


def all_on_4():
    """All-on-4 на верхній щелепі: два прямі імплантати спереду, два нахилені позаду вздовж пазух,
    майбутні зуби — пунктиром."""
    u = "a4"
    body = _maxilla(u) + _a4_implants(ACCENT, INK) + _upper_gum()
    body += _crowns(_upper_teeth(), dashed=True)
    return svg(body, u, "Імплантація All-on-4 на верхній щелепі")


def all_on_6():
    """All-on-6 на верхній щелепі: шість імплантатів — два спереду, два під премолярами, два під першими молярами;
    майбутні зуби — пунктиром."""
    u = "a6"
    body = _maxilla(u) + _a4_implants(ACCENT, INK, A6_IMPLANTS) + _upper_gum()
    body += _crowns(_upper_teeth(), dashed=True)
    return svg(body, u, "Імплантація All-on-6 на верхній щелепі")


def superstructure_6():
    """Незнімний протез на шести імплантатах."""
    return superstructure(A6_IMPLANTS, "s6", (25, 45, 66, 94, 115, 135))


def superstructure(places=None, u="ss", screws=(36, 65, 95, 124)):
    """Незнімний протез на імплантатах: титанова балка в рожевому акриловому базисі, анатомічні зуби."""
    teeth = _upper_teeth()
    body = _maxilla(u) + _a4_implants(METAL, "#8a939e", places)
    body += _crowns(teeth)
    body += f'<path d="{_flange(teeth)}" fill="{PINK_BASE}" fill-opacity=".93" stroke="{PINK_EDGE}" stroke-width="1.1" stroke-linejoin="round"/>'
    body += f'<path d="M24 99Q80 108 136 99" fill="none" stroke="{INK}" stroke-width="5.6" stroke-linecap="round"/>'
    body += f'<path d="M24 99Q80 108 136 99" fill="none" stroke="{METAL}" stroke-width="3.6" stroke-linecap="round"/>'
    for x in screws:
        body += f'<circle cx="{x}" cy="{99 + 9 * 4 * ((x - 24) / 112) * (1 - (x - 24) / 112) / 2:.1f}" r="1.2" fill="{INK}"/>'
    return svg(body, u, "Незнімний протез на імплантатах")


# --- arches seen from above (occlusal view), front teeth at the top -------------------------
ARCH_TEETH = {   # mesio-distal width, bucco-lingual depth (mm), form
    "upper": [(8.5, 7.0, "inc"), (6.5, 6.0, "inc"), (7.5, 8.0, "can"), (7.0, 9.0, "pm"), (6.5, 9.0, "pm"), (10.0, 11.0, "mol"), (9.0, 11.0, "mol")],
    "lower": [(5.2, 6.0, "inc"), (5.6, 6.2, "inc"), (7.0, 7.5, "can"), (7.0, 7.8, "pm"), (7.0, 8.0, "pm"), (11.0, 10.5, "mol"), (10.5, 10.0, "mol")],
}
ARCH = {"upper": dict(a=52, depth=92, top=24), "lower": dict(a=49, depth=90, top=26)}
ARCH_P = .42      # x = a * u^p: a little broader in front than a parabola, like a real dental arch


def _parabola(a, depth, top, n=700):
    """right half of the arch: x = a*sqrt(u), y = top + depth*u, with cumulative length"""
    pts = [(a * (i / n) ** ARCH_P, top + depth * i / n) for i in range(n + 1)]
    acc = [0.0]
    for i in range(1, len(pts)):
        acc.append(acc[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    return pts, acc


def _at(pts, acc, L):
    i = next((i for i, v in enumerate(acc) if v >= L), len(acc) - 1)
    j = max(i - 1, 0)
    (x0, y0), (x1, y1) = pts[j], pts[max(i, 1)]
    return pts[i][0], pts[i][1], math.degrees(math.atan2(y1 - y0, x1 - x0))


def arch_layout(jaw="upper", gap=.6, count=7):
    """teeth along a parabolic arch: [(x, y, theta, w, d, form, side, L)];
    rotate(theta) turns the tooth so that its local +v axis points to the cheek / lip."""
    g = ARCH[jaw]
    sizes = ARCH_TEETH[jaw][:count]
    pts, acc = _parabola(g["a"], g["depth"], g["top"])
    k = acc[-1] / (sum(w for w, _, _ in sizes) + gap * count + 1.5)
    out = []
    for side in (1, -1):
        L = gap * k / 2
        for w, d, form in sizes:
            Lc = L + w * k / 2
            x, y, ang = _at(pts, acc, Lc)
            theta = ang + 180 if side > 0 else 180 - ang
            out.append((80 + side * x, y, theta, w * k, d * k, form, side, Lc))
            L += (w + gap) * k
    return out, (pts, acc)


def _occl_shape(w, d, form):
    """tooth outline in local coords: u along the arch, +v toward the cheek / lip"""
    wl, wi = {"inc": (w, w * .55), "can": (w * .8, w * .55), "pm": (w * .85, w * .8), "mol": (w * .95, w * .92)}[form]
    h = d / 2
    return (f"M0 {h:.2f}C{wl * .5:.2f} {h:.2f} {w / 2:.2f} {h * .45:.2f} {w / 2:.2f} 0"
            f"C{w / 2:.2f} {-h * .5:.2f} {wi * .55:.2f} {-h:.2f} 0 {-h:.2f}"
            f"C{-wi * .55:.2f} {-h:.2f} {-w / 2:.2f} {-h * .5:.2f} {-w / 2:.2f} 0"
            f"C{-w / 2:.2f} {h * .45:.2f} {-wl * .5:.2f} {h:.2f} 0 {h:.2f}Z")


def _occl_grooves(w, d, form):
    if form == "pm":
        return f"M{-w * .28:.2f} 0Q0 {-d * .06:.2f} {w * .28:.2f} 0"
    if form == "mol":
        return (f"M{-w * .3:.2f} {d * .04:.2f}L{w * .3:.2f} {-d * .04:.2f}M{w * .04:.2f} {-d * .01:.2f}L{w * .12:.2f} {d * .4:.2f}"
                f"M{-w * .06:.2f} {d * .02:.2f}L{-w * .12:.2f} {-d * .4:.2f}")
    if form == "can":
        return f"M0 {d * .3:.2f}L0 {-d * .1:.2f}"
    return ""


def _local(x, y, theta, u, v):
    t = math.radians(theta)
    return x + u * math.cos(t) - v * math.sin(t), y + u * math.sin(t) + v * math.cos(t)


def _occl_teeth(layout, fill=TOOTH):
    out = ""
    for x, y, th, w, d, form, side, L in layout:
        g = _occl_grooves(w, d, form)
        out += (f'<g transform="translate({x:.2f} {y:.2f}) rotate({th:.1f})">'
                f'<path d="{_occl_shape(w, d, form)}" fill="{fill}" stroke="{INK}" stroke-width="1.2" stroke-linejoin="round"/>'
                + (f'<path d="{g}" fill="none" stroke="{BONE_DOT}" stroke-width=".9" stroke-linecap="round"/>' if g else "")
                + '</g>')
    return out


def _half_depth(layout, L):
    ts = sorted([(t[7], t[4] / 2) for t in layout if t[6] > 0])
    if L <= ts[0][0]:
        return ts[0][1]
    for (l0, h0), (l1, h1) in zip(ts, ts[1:]):
        if L <= l1:
            return h0 + (h1 - h0) * (L - l0) / (l1 - l0)
    return ts[-1][1]


def _arch_lines(layout, geom, out_extra, in_extra, back_extra=1.5):
    """outer (cheek) and inner (tongue) lines of a band hugging the teeth, right half from front to back"""
    pts, acc = geom
    last = max((t for t in layout if t[6] > 0), key=lambda t: t[7])
    L_end = last[7] + last[3] / 2 + back_extra
    outer, inner = [], []
    for i, (x, y) in enumerate(pts):
        if acc[i] > L_end:
            break
        j, h = min(i + 1, len(pts) - 1), max(i - 1, 0)
        dx, dy = pts[j][0] - pts[h][0], pts[j][1] - pts[h][1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = dy / ln, -dx / ln               # outward normal of the right half
        hd = _half_depth(layout, acc[i])
        outer.append((x + nx * (hd + out_extra), y + ny * (hd + out_extra)))
        inner.append((x - nx * (hd + in_extra), y - ny * (hd + in_extra)))
    return outer, inner


def _poly(points):
    return " L".join(f"{x:.1f} {y:.1f}" for x, y in points)


def _band(layout, geom, out_extra, in_extra):
    outer, inner = _arch_lines(layout, geom, out_extra, in_extra)
    R = [(80 + x, y) for x, y in outer]
    Ri = [(80 + x, y) for x, y in inner]
    Lo = [(80 - x, y) for x, y in outer]
    Li = [(80 - x, y) for x, y in inner]
    d = "M" + _poly(list(reversed(Lo)) + R[1:])
    (ex, ey), (ix, iy) = R[-1], Ri[-1]
    d += f" C{ex:.1f} {ey + 6:.1f} {ix:.1f} {iy + 6:.1f} {ix:.1f} {iy:.1f}"
    d += " L" + _poly(list(reversed(Ri))[1:] + Li[1:])
    (sx, sy), (lx, ly) = Lo[-1], Li[-1]
    d += f" C{lx:.1f} {ly + 6:.1f} {sx:.1f} {sy + 6:.1f} {sx:.1f} {sy:.1f}Z"
    return d


def splint():
    """Сплінт, вигляд зверху: товста тверда капа, що вкриває жувальні поверхні всієї дуги."""
    u = "sp"
    lay, geom = arch_layout()
    body = _occl_teeth(lay)
    body += f'<path d="{_band(lay, geom, 5, 6.5)}" fill="{ACCENT}" fill-opacity=".45" stroke="{ACCENT_DEEP}" stroke-width="2.4" stroke-linejoin="round"/>'
    for x, y, th, w, d, form, side, L in lay:
        if form in ("can", "mol"):
            body += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.4" fill="{INK}" fill-opacity=".55"/>'
    return svg(body, u, "Сплінт — вигляд зверху")


def _thin_tray(lay, geom):
    return (f'<path d="{_band(lay, geom, 1.4, 1.6)}" fill="{ACCENT}" fill-opacity=".2" stroke="{ACCENT_DEEP}" '
            f'stroke-width="1.1" stroke-linejoin="round"/>')


def aligner():
    """Елайнери, вигляд зверху: тонка прозора капа по контуру зубів, атачменти на зубах."""
    u = "al"
    lay, geom = arch_layout()
    body = _occl_teeth(lay)
    for x, y, th, w, d, form, side, L in lay:
        if form in ("can", "pm", "mol") and not (form == "mol" and L > lay[5][7] + 1):
            body += (f'<g transform="translate({x:.2f} {y:.2f}) rotate({th:.1f})"><rect x="-3" y="{d / 2 - 1.4:.2f}" width="6" height="3.6" rx="1.2" '
                     f'fill="{ACCENT_DEEP}" stroke="{INK}" stroke-width=".8"/></g>')
    body += _thin_tray(lay, geom)
    return svg(body, u, "Елайнери — вигляд зверху")


def retention_tray():
    """Ретенційна капа, вигляд зверху: тонка прозора капа без атачментів."""
    u = "rk"
    lay, geom = arch_layout()
    body = _occl_teeth(lay) + _thin_tray(lay, geom)
    return svg(body, u, "Ретенційна капа — вигляд зверху")


def retainer():
    """Ретейнер, вигляд зверху: тонкий дріт з язикового боку передніх зубів нижньої щелепи."""
    u = "rt"
    lay, geom = arch_layout("lower")
    body = _occl_teeth(lay)
    front = sorted([t for t in lay if t[5] in ("inc", "can")], key=lambda t: t[0])
    wire = [_local(x, y, th, 0, -(d / 2 - 1.9)) for x, y, th, w, d, form, side, L in front]
    body += f'<path d="M{_poly(wire)}" fill="none" stroke="{ACCENT_DEEP}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
    for x, y in wire:
        body += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.3" fill="{ACCENT}" stroke="{ACCENT_DEEP}" stroke-width=".8"/>'
    return svg(body, u, "Ретейнер — вигляд зверху")


def functiography():
    """Функціографія, вигляд зверху на нижню дугу: на пластинці — записана траєкторія рухів щелепи (вперед і вбоки)
    з точкою, де щелепи змикаються природно; стрілка під дугою — рух щелепи з боку в бік."""
    u = "fg"
    lay, geom = arch_layout("lower")
    body = _occl_teeth(lay)
    trace = f'stroke="{ACCENT_DEEP}" stroke-width="1.7" stroke-dasharray="3 2.4" stroke-linecap="round" stroke-linejoin="round" fill="none"'
    body += f'<rect x="61" y="54" width="38" height="52" rx="10" fill="{LIGHT_ACCENT}" stroke="{ACCENT}" stroke-width="1.1"/>'
    body += f'<path d="M66 68L80 95L94 68" {trace}/><path d="M80 95V61" {trace}/>'
    body += f'<circle cx="80" cy="95" r="4" fill="{ACCENT}" stroke="{INK}" stroke-width="1.3"/>'
    arrow = f'stroke="{INK}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="none"'
    body += (f'<path d="M50 140Q80 148 110 140" {arrow}/>'
             f'<path d="M55.5 136.2L50 140L55.8 143.4" {arrow}/><path d="M104.5 136.2L110 140L104.2 143.4" {arrow}/>')
    return svg(body, u, "Функціографія — запис рухів щелепи")


IMPRESSION = "#d9e7f6"       # impression mass (light Sky Blue)
IMPRESSION_EDGE = "#8fb1dc"


def impression():
    """Відбиток, вигляд зверху: ложка з ручкою спереду, заповнена відбитковою масою з відтисками зубів."""
    u = "im"
    lay, geom = arch_layout()
    top = ARCH["upper"]["top"]
    dy = 16                                         # room above the arch for the handle
    handle = (f'<path d="M75.5 {top + dy - 5}L74.5 16C74 11 69 10 69 6.5Q69 3 73 3H87Q91 3 91 6.5C91 10 86 11 85.5 16L84.5 {top + dy - 5}Z" '
              f'fill="{METAL}" stroke="{INK}" stroke-width="1.4" stroke-linejoin="round"/>'
              f'<path d="M75 7.5H85" stroke="{METAL_SHADE}" stroke-width="1.4" stroke-linecap="round"/>')
    body = f'<path d="{_band(lay, geom, 7.5, 9)}" fill="{METAL}" stroke="{INK}" stroke-width="1.5" stroke-linejoin="round"/>'
    body += f'<path d="{_band(lay, geom, 5, 6.5)}" fill="{IMPRESSION}" stroke="{IMPRESSION_EDGE}" stroke-width="1" stroke-linejoin="round"/>'
    for x, y, th, w, d, form, side, L in lay:      # imprints of the teeth: hollows in the mass, not teeth
        g = _occl_grooves(w * .9, d * .9, form)
        body += (f'<g transform="translate({x:.2f} {y:.2f}) rotate({th:.1f})">'
                 f'<path d="{_occl_shape(w * .9, d * .9, form)}" fill="{IMPRESSION_EDGE}" fill-opacity=".28" '
                 f'stroke="{IMPRESSION_EDGE}" stroke-width="1" stroke-linejoin="round"/>'
                 + (f'<path d="{g}" fill="none" stroke="{IMPRESSION_EDGE}" stroke-width=".8" stroke-linecap="round"/>' if g else "")
                 + '</g>')
    return svg(handle + f'<g transform="translate(0 {dy})">{body}</g>', u, "Відбиток щелепи — вигляд зверху")


def denture():
    """Повний знімний протез верхньої щелепи, вигляд з боку зубів: рожевий акриловий базис з краєм навколо
    зубів закриває піднебіння, штучні зуби стоять по дузі."""
    u = "dn"
    lay, geom = arch_layout()
    outer, _ = _arch_lines(lay, geom, 5, 0, back_extra=4)
    R = [(80 + x, y) for x, y in outer]
    Lo = [(80 - x, y) for x, y in outer]
    (rx, ry), (lx, ly) = R[-1], Lo[-1]
    d = "M" + _poly(list(reversed(Lo)) + R[1:])
    d += f" C{rx:.1f} {ry + 7:.1f} {rx - 7:.1f} {ry + 10:.1f} {rx - 14:.1f} {ry + 8:.1f}"     # round the tuberosity
    d += f" Q80 {ry - 2:.1f} {lx + 14:.1f} {ly + 8:.1f}"                                       # posterior border across the palate
    d += f" C{lx + 7:.1f} {ly + 10:.1f} {lx:.1f} {ly + 7:.1f} {lx:.1f} {ly:.1f}Z"
    body = f'<path d="{d}" fill="{PINK_BASE}" stroke="{PINK_EDGE}" stroke-width="1.3" stroke-linejoin="round"/>'
    # palatal rugae and the midline raphe
    top = ARCH["upper"]["top"]
    for i, y in enumerate((top + 30, top + 37, top + 44)):
        body += (f'<path d="M{67 - i * 1.5:.1f} {y}C71 {y - 3} 75 {y + 3} 80 {y}C85 {y - 3} 89 {y + 3} {93 + i * 1.5:.1f} {y}" '
                 f'fill="none" stroke="{PINK_EDGE}" stroke-width="1" stroke-linecap="round" stroke-opacity=".75"/>')
    body += f'<path d="M80 {top + 26}V{ly - 14:.1f}" stroke="{PINK_EDGE}" stroke-width=".9" stroke-dasharray="2 3" stroke-opacity=".7"/>'
    body += _occl_teeth(lay)
    return svg(body, u, "Повний знімний протез на акриловому базисі")


def sinus_lift():
    """Синус-ліфтинг (верхня щелепа, зуби донизу): мембрану пазухи піднято куполом, під нею — заштрихований
    кістковий матеріал, у нього входить імплантат; поруч власні зуби з коренями."""
    u = "sl"
    s = 2.6
    body = _hatch(u)
    body += f'<path d="M8 18Q8 8 18 8H142Q152 8 152 18V96Q80 102 8 96Z" fill="url(#bone{u})" stroke="{BONE_DOT}" stroke-width="1"/>'
    cavity = ("M56 60C50 44 54 27 69 19C84 11 108 12 124 16C140 20 148 32 147 48C146 58 142 66 134 70"
              "C126 73 118 69 110 72C104 74 99 72 96 70C93 54 87 45 80 45C73 45 67 54 64 70C61 72 58 67 56 60Z")
    body += f'<path d="{cavity}" fill="{AIR}"/>'
    body += f'<path d="{cavity}" fill="none" stroke="{GUM}" stroke-width="3.2" stroke-linejoin="round"/>'
    body += f'<path d="{cavity}" fill="none" {SW}/>'
    graft = "M64 70C67 54 73 45 80 45C87 45 93 54 96 70C90 82 70 82 64 70Z"
    body += f'<path d="{graft}" fill="url(#hatch{u})" stroke="{ACCENT_DEEP}" stroke-width="1.2" stroke-linejoin="round"/>'
    body += f'<path d="M64 70C70 82 90 82 96 70" fill="none" stroke="{INK}" stroke-width="1.1" stroke-dasharray="3 2.6"/>'
    body += _arrow_up(80, 38, 26, ACCENT_DEEP)
    # neighbouring teeth 23, 24 | gap 25 | 26, 27 — dentist's view of the patient's left side
    x, cerv = 31.8, 104
    for n in (23, 24, 25, 26, 27):
        w, cw, hc = _G.ANATOMY["upper"][n % 10][:3]
        cx = x + w * s / 2
        if n != 25:
            sil, crown, cej, _ = _G.tooth_paths(n, cx, cerv + hc * s, s, True)
            body += (f'<path d="{sil}" fill="{TOOTH}" stroke="{INK}" stroke-width="1.4" stroke-linejoin="round"/>'
                     f'<path d="{cej}" fill="none" stroke="{INK}" stroke-width="1"/>')
        x += w * s + .8
    body += _implant_g(80, 100.5, 0, .6, 1.18, METAL)
    body += f'<path d="M74 100.5H86" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>'
    body += (f'<path d="M8 94Q80 101 152 94V106Q80 114 8 106Z" fill="{GUM}" fill-opacity=".72"/>'
             f'<path d="M8 106Q80 114 152 106" fill="none" stroke="{GUM_EDGE}" stroke-width="1"/>')
    return svg(body, u, "Синус-ліфтинг")


def multi_unit():
    """Абатмент Multi-Unit (за фото): широкий комір на всю ширину імплантату, короткий конус
    і нижча голівка під гвинт протеза, що виходить над яснами."""
    u = "mu"
    body = _jaw(u)
    body += f'<path d="{IMPLANT}" fill="{METAL}" {SW}/>' + _threads("#8a939e")
    body += _gum()
    mu = ("M70 104L67.6 101.6Q67 100 68.8 100H70.4L73 96.6V86.6L75.4 84H84.6L87 86.6V96.6L89.6 100H91.2Q93 100 92.4 101.6L90 104Z")
    body += f'<path d="{mu}" fill="{ACCENT}" {SW}/>'
    body += f'<path d="M70.4 100H89.6" stroke="{INK}" stroke-width="1.1"/>'
    body += f'<path d="M77.6 84.6V96M82.4 84.6V96" stroke="{ACCENT_DEEP}" stroke-width="1" stroke-linecap="round"/>'
    body += f'<path d="M74.6 89V95" stroke="#ffffff" stroke-width="1.3" stroke-linecap="round" stroke-opacity=".7"/>'
    body += f'<path d="M70 104H90" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>'
    body += f'<path d="M36 72H124" stroke="{INK}" stroke-width="1.3" stroke-dasharray="4 3"/>'
    return svg(body, u, "Абатмент Multi-Unit")


def axiography():
    """Аксіографія: на голові — легка дуга з датчиками, плата датчика біля суглоба, нижня дуга з'єднана із зубами;
    стрілка — рух нижньої щелепи."""
    u = "ax"
    body = f'<path d="{HEAD}" fill="#f6f8fb" {SW}/>'
    body += f'<path d="{JAW_BAND}" fill="{ACCENT}" fill-opacity=".45" stroke="{ACCENT_DEEP}" stroke-width="1.1" stroke-linejoin="round"/>'
    body += f'<path d="M49 62C56 59 61 65 59.5 72C58.5 76 55.5 78 53 80" fill="none" stroke="{INK}" stroke-width="1.4" stroke-linecap="round"/>'
    # head band with a strap down to the sensor plate in front of the ear
    band = "M112 43C92 36 54 36 24 50"
    body += (f'<path d="{band}" fill="none" stroke="{INK}" stroke-width="6.4" stroke-linecap="round"/>'
             f'<path d="{band}" fill="none" stroke="{ACCENT}" stroke-width="4" stroke-linecap="round"/>')
    body += f'<path d="M68 38C69 48 70 56 71 63" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>'
    body += f'<rect x="62" y="63" width="22" height="18" rx="3" fill="#ffffff" stroke="{ACCENT_DEEP}" stroke-width="1.5"/>'
    body += f'<path d="M66 69H80M66 75H80" stroke="{LIGHT_ACCENT}" stroke-width="1"/>'
    # lower bow: from the teeth out of the mouth and back along the cheek to a stylus on the plate
    body += f'<path d="M112 95H124V101H80V81" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
    body += f'<circle cx="80" cy="77" r="2.8" fill="{ACCENT_DEEP}" stroke="{INK}" stroke-width=".8"/>'
    body += f'<circle cx="104" cy="40.6" r="2" fill="{INK}"/><circle cx="36" cy="45" r="2" fill="{INK}"/>'
    body += (f'<path d="M134 104A60 60 0 0 1 124 132" fill="none" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>'
             f'<path d="M120.2 127L124 132.4L129.3 128.8" fill="none" stroke="{INK}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')
    return svg(body, u, "Аксіографія — запис рухів щелепи датчиками")


ALL = ALL + [("Огляд", exam), ("Сканування", scan), ("Моделювання", modeling), ("Аксіографія", axiography),
             ("Глибоке чищення", srp), ("Пародонтологічна карта", perio_chart), ("Міжзубний йоржик", interdental_brush),
             ("Відбілювання", whitening), ("Брекет-система", braces), ("Мікроімплант", mini_implant), ("Видалення імплантату", implant_removal), ("Пломба", filling), ("Естетична реставрація", aesthetic),
             ("Відновлення культі", core_buildup), ("Скловолокно", fiber), ("Зняття коронки", crown_removal),
             ("Видалення штифта", post_removal), ("Видалення зуба", extraction), ("Зуб, який не зберегти", hopeless_tooth), ("Видовження коронки", crown_lengthening),
             ("Кісткова пластика", bone_graft), ("Синус-ліфтинг", sinus_lift), ("Пластика ясен", soft_tissue),
             ("Формувач ясен", healing_cap), ("Multi-Unit", multi_unit), ("Індив. абатмент", custom_abutment),
             ("Тимчасова коронка", temp_crown), ("Тимч. на імпланті", temp_implant_crown), ("Коронка з керамікою", crown_layered),
             ("All-on-4", all_on_4), ("Протез на імплантатах", superstructure),
             ("All-on-6", all_on_6), ("Протез на 6 імплантатах", superstructure_6), ("Знімний протез", denture),
             ("Сплінт", splint), ("Елайнери, капи", aligner), ("Ретенційна капа", retention_tray), ("Ретейнер", retainer), ("Відбиток", impression), ("Функціографія", functiography), ("Сепарація", separation),
             ("Седація", sedation)]

BY_KEY = {fn.__name__: fn for _, fn in ALL}


# ---- thumbnails for the PDF ------------------------------------------------------------
import re as _re
_seq = [0]


# thumbnails are cropped closer to the subject; wide or tall scenes keep more of the frame
THUMB_VIEW = {"default": "24 34 112 112", "ct_scan": "6 12 148 148", "sedation": "12 16 136 136",
              "modeling": "12 14 136 136", "axiography": "8 8 144 144", "sinus_lift": "8 8 144 144",
              "all_on_4": "10 14 140 140", "superstructure": "10 14 140 140",
              "all_on_6": "10 14 140 140", "superstructure_6": "10 14 140 140", "denture": "8 8 144 144",
              "splint": "8 8 144 144", "aligner": "8 8 144 144", "retention_tray": "8 8 144 144",
              "retainer": "8 8 144 144", "impression": "6 0 148 148", "perio_chart": "10 12 136 136", "whitening": "16 8 128 128", "braces": "20 30 120 120", "mini_implant": "18 32 124 124",
              "implant_removal": "20 18 128 128", "interdental_brush": "18 12 128 128", "functiography": "8 10 144 144", "separation": "18 22 124 124", "scan": "22 20 124 124",
              "exam": "22 22 124 124", "endo": "22 22 124 124", "hygiene": "16 22 124 124", "srp": "14 22 124 124",
              "extraction": "20 16 128 128", "hopeless_tooth": "22 30 116 116", "crown_removal": "20 18 128 128", "post_removal": "20 18 128 128",
              "aesthetic": "22 30 116 116"}


def thumb(name, k=1.55, size=52):
    """the same picture for a small tile: cropped closer, strokes thicker by k, ids unique per use"""
    src = BY_KEY[name]()
    src = src.replace('viewBox="0 0 160 160"', f'viewBox="{THUMB_VIEW.get(name, THUMB_VIEW["default"])}"', 1)
    _seq[0] += 1
    n = _seq[0]
    src = _re.sub(r'stroke-width="([\d.]+)"', lambda m: f'stroke-width="{float(m.group(1)) * (k if float(m.group(1)) <= 4.3 else 1):.2f}"', src)
    src = _re.sub(r'id="([\w-]+)"', lambda m: f'id="{m.group(1)}_{n}"', src)
    src = _re.sub(r'url\(#([\w-]+)\)', lambda m: f'url(#{m.group(1)}_{n})', src)
    return src.replace('width="160" height="160"', f'width="{size}" height="{size}"', 1)
