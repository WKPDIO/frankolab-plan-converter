"""Thin-line icons and the dental chart, drawn as inline SVG in the FrankoLab style.

Icons: 24x24 grid, one ink (currentColor), round caps, non-scaling 1.3px strokes.
Chart: FDI numbering, dentist's view (patient's right on the viewer's left),
upper row 18..11 | 21..28, lower row 48..41 | 31..38.
"""

# one tooth outline, crown up, roots down, inside the 24x24 grid
TOOTH = ("M12 5.6C10.4 4.3 8.2 3.5 6.4 4.3C4.4 5.2 4.1 7.7 4.6 10C5.1 12.2 6 13.8 6.4 16.5"
         "C6.8 19.3 7.1 22.6 8.7 22.8C10.3 23 10.6 20.2 10.9 18.4C11.1 17.1 11.3 16.3 12 16.3"
         "C12.7 16.3 12.9 17.1 13.1 18.4C13.4 20.2 13.7 23 15.3 22.8C16.9 22.6 17.2 19.3 17.6 16.5"
         "C18 13.8 18.9 12.2 19.4 10C19.9 7.7 19.6 5.2 17.6 4.3C15.8 3.5 13.6 4.3 12 5.6Z")
# crown part of the tooth (closed along the gum line at y = 11.6)
CROWN = ("M12 5.6C10.4 4.3 8.2 3.5 6.4 4.3C4.4 5.2 4.1 7.7 4.6 10C4.7 10.6 4.9 11.1 5.1 11.6"
         "H18.9C19.1 11.1 19.3 10.6 19.4 10C19.9 7.7 19.6 5.2 17.6 4.3C15.8 3.5 13.6 4.3 12 5.6Z")

S = 'fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"'


def _svg(body, size=28):
    return (f'<svg class="ico" width="{size}" height="{size}" viewBox="0 0 24 24" aria-hidden="true" '
            f'xmlns="http://www.w3.org/2000/svg">{body}</svg>')


def _tooth(transform=""):
    t = f' transform="{transform}"' if transform else ""
    return f'<path d="{TOOTH}" {S}{t}/>'


ICONS = {
    # огляд і план: зуб у рамці видошукача
    "scan": _tooth("translate(4.8 4.4) scale(0.6)")
            + f'<path d="M3 7.5V4.2Q3 3 4.2 3H7.5M16.5 3H19.8Q21 3 21 4.2V7.5M21 16.5V19.8Q21 21 19.8 21H16.5M7.5 21H4.2Q3 21 3 19.8V16.5" {S}/>',
    # гігієна: зуб і дві іскри
    "hygiene": _tooth("translate(0.6 3.2) scale(0.82)")
               + f'<path d="M19.2 1.8L19.9 3.6L21.7 4.3L19.9 5L19.2 6.8L18.5 5L16.7 4.3L18.5 3.6Z" {S}/>'
               + f'<path d="M21.2 8.6L21.6 9.6L22.6 10L21.6 10.4L21.2 11.4L20.8 10.4L19.8 10L20.8 9.6Z" {S}/>',
    # пломба: зуб із латкою на коронці
    "filling": _tooth() + '<ellipse cx="12" cy="9" rx="3" ry="1.9" fill="currentColor" fill-opacity=".35" stroke="none"/>',
    # канали: зуб із каналами в коренях
    "endo": _tooth() + f'<path d="M9.4 9.8Q12 8.4 14.6 9.8M9.4 9.8C9.3 13.4 9 16.8 8.8 20.6M14.6 9.8C14.7 13.4 15 16.8 15.2 20.6" {S}/>',
    # видалення: зуб і стрілка вгору
    "extraction": _tooth("translate(2.4 4.4) scale(0.8)")
                  + f'<path d="M12 6.2V1.6M9.9 3.6L12 1.5L14.1 3.6" {S}/>',
    # імплантація: коронка, абатмент і гвинт
    "implant": f'<path d="{CROWN}" {S}/>'
               + f'<path d="M10.3 11.6V13.6H13.7V11.6M9.8 13.6H14.2L13.7 20.6L12 22.4L10.3 20.6Z" {S}/>'
               + f'<path d="M9.9 15.8H14.1M10.1 18H13.9" {S}/>',
    # тимчасова коронка: пунктирна межа коронки
    "crown_temp": _tooth() + f'<path d="M4.9 11.6H19.1" {S} stroke-dasharray="1.4 1.6"/>'
                  + f'<path d="{CROWN}" fill="currentColor" fill-opacity=".12" stroke="none"/>',
    # постійна коронка: заповнена коронка
    "crown": _tooth() + f'<path d="M4.9 11.6H19.1" {S}/>'
             + f'<path d="{CROWN}" fill="currentColor" fill-opacity=".35" stroke="none"/>',
    "tooth": _tooth(),
}


def icon(name, size=28):
    return _svg(ICONS.get(name, ICONS["tooth"]), size)


# ---- dental chart -----------------------------------------------------------
UPPER = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28]
LOWER = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]

# buccal view proportions, mm: crown width, cervical width, crown height, root length, root form
# root forms: 1 — one root, 2 — two roots (mesial + distal / buccal + palatal), 3 — three roots, f — fused
ANATOMY = {
    "upper": {1: (8.5, 6.6, 10.0, 13.0, "1", "incisor"), 2: (6.6, 4.9, 8.7, 13.0, "1", "incisor"),
              3: (7.6, 5.6, 10.0, 17.0, "1", "canine"), 4: (7.0, 5.0, 8.5, 14.0, "2b", "premolar"),
              5: (6.6, 5.0, 8.5, 14.0, "1", "premolar"), 6: (10.0, 8.0, 7.5, 12.5, "3", "molar"),
              7: (9.0, 7.0, 7.0, 12.0, "3", "molar"), 8: (8.5, 6.6, 6.5, 10.5, "f", "molar")},
    "lower": {1: (5.2, 3.6, 9.0, 12.5, "1", "incisor"), 2: (5.6, 4.0, 9.5, 14.0, "1", "incisor"),
              3: (7.0, 5.4, 11.0, 16.0, "1", "canine"), 4: (7.0, 5.0, 8.5, 14.0, "1", "premolar"),
              5: (7.0, 5.0, 8.0, 14.5, "1", "premolar"), 6: (11.0, 9.0, 7.5, 14.0, "2", "molar"),
              7: (10.5, 8.2, 7.0, 13.0, "2", "molar"), 8: (10.0, 7.6, 7.0, 11.0, "f", "molar")},
}
ROOT_K = 0.9       # roots drawn a little shorter so the chart stays compact


def _crown_outline(kind, w, cw, hc):
    """crown silhouette from the distal cervical point (-cw/2, hc) to the mesial one (cw/2, hc); mesial is +x.
    The shape follows a real buccal view: a narrow neck that flares quickly to a wide, slightly angular equator
    in the middle third, then nearly straight flanks running to sharp incisal / cusp corners."""
    def flare_up(sh):       # distal: a straight-ish flank from the neck up to the shoulder at height sh (fraction of hc)
        return [("M", (-cw / 2, hc)), ("C", (-cw / 2 - (w - cw) * .12, hc * .92), (-w / 2 + (w - cw) * .06, hc * (sh + .08)), (-w / 2, hc * sh))]

    def flare_down(sh):     # mesial: from the shoulder straight down into the neck
        return [("C", (w / 2 - (w - cw) * .06, hc * (sh + .08)), (cw / 2 + (w - cw) * .12, hc * .92), (cw / 2, hc))]

    if kind == "incisor":
        shD, shM = .4, .3
        mid = [("L", (-w * .475, hc * .1)), ("C", (-w * .465, hc * .04), (-w * .44, hc * .012), (-w * .37, hc * .008)),
               ("L", (w * .44, 0)), ("C", (w * .48, 0), (w * .49, hc * .02), (w * .49, hc * .07)), ("L", (w / 2, hc * shM))]
    elif kind == "canine":
        shD, shM = .46, .4
        mid = [("L", (-w * .36, hc * .22)), ("C", (-w * .24, hc * .1), (-w * .08, hc * .02), (0, hc * .012)),
               ("Q", (w * .06, -hc * .006), (w * .12, hc * .015)),
               ("C", (w * .26, hc * .06), (w * .44, hc * .2), (w * .49, hc * .36)), ("L", (w / 2, hc * shM))]
    elif kind == "premolar":
        shD, shM = .42, .4
        mid = [("L", (-w * .45, hc * .2)), ("C", (-w * .36, hc * .05), (-w * .16, 0), (-w * .05, 0)), ("L", (w * .05, 0)),
               ("C", (w * .16, 0), (w * .36, hc * .05), (w * .44, hc * .2)), ("L", (w / 2, hc * shM))]
    else:   # molar: mesio-buccal cusp larger, disto-buccal smaller, buccal groove between them
        shD, shM = .36, .34
        mid = [("L", (-w * .48, hc * .14)), ("C", (-w * .44, hc * .04), (-w * .36, 0), (-w * .27, 0)),
               ("C", (-w * .15, 0), (-w * .09, hc * .14), (-w * .02, hc * .15)),
               ("C", (w * .06, hc * .15), (w * .1, 0), (w * .25, 0)),
               ("C", (w * .35, 0), (w * .44, hc * .04), (w * .47, hc * .14)), ("L", (w / 2, hc * shM))]
    return flare_up(shD) + mid + flare_down(shM)


def _relief(kind, w, hc, form):
    """surface anatomy as a few thin strokes: line angles and lobes of incisors, the labial ridge of a canine,
    the buccal ridge of a premolar, the buccal groove and cusp ridges of a molar. Local coords, mesial +x."""
    r = []
    if kind == "incisor":
        # line angles: where the flat labial face turns into the proximal surfaces
        r += [("M", (-w * .34, hc * .06)), ("C", (-w * .35, hc * .3), (-w * .33, hc * .5), (-w * .27, hc * .74))]
        r += [("M", (w * .37, hc * .05)), ("C", (w * .38, hc * .3), (w * .36, hc * .5), (w * .3, hc * .74))]
        # two developmental grooves between the three lobes, short, from the incisal edge
        for x in (-w * .11, w * .12):
            r += [("M", (x, hc * .05)), ("Q", (x * 1.1, hc * .18), (x * .95, hc * .32))]
    elif kind == "canine":
        r += [("M", (w * .06, hc * .07)), ("C", (w * .07, hc * .3), (w * .04, hc * .55), (w * .01, hc * .82))]
        r += [("M", (-w * .3, hc * .2)), ("C", (-w * .33, hc * .4), (-w * .3, hc * .58), (-w * .22, hc * .76))]
        r += [("M", (w * .33, hc * .2)), ("C", (w * .35, hc * .4), (w * .32, hc * .58), (w * .25, hc * .76))]
    elif kind == "premolar":
        r += [("M", (0, hc * .08)), ("C", (-w * .01, hc * .3), (-w * .02, hc * .5), (-w * .03, hc * .74))]
        r += [("M", (-w * .32, hc * .22)), ("Q", (-w * .34, hc * .45), (-w * .26, hc * .68))]
        r += [("M", (w * .32, hc * .22)), ("Q", (w * .34, hc * .45), (w * .26, hc * .68))]
    else:
        r += [("M", (-w * .02, hc * .17)), ("C", (-w * .03, hc * .3), (-w * .045, hc * .42), (-w * .05, hc * .54))]
        r += [("M", (-w * .09, hc * .57)), ("Q", (-w * .05, hc * .62), (-w * .01, hc * .57))]            # pit at the groove end
        r += [("M", (w * .3, hc * .1)), ("C", (w * .3, hc * .3), (w * .26, hc * .45), (w * .17, hc * .58))]
        r += [("M", (-w * .32, hc * .1)), ("C", (-w * .32, hc * .28), (-w * .28, hc * .42), (-w * .19, hc * .54))]
    return r


def _facets(kind, w, hc):
    """planes that turn away from the light, as faint tone over the crown (clipped to it): the proximal faces
    beyond the line angles, the distal slope of a canine, the distal cusp of a molar. [(cmds, opacity)]"""
    out = []
    if kind == "incisor":
        out.append(([("M", (-w, -1)), ("L", (-w * .34, -1)), ("C", (-w * .35, hc * .3), (-w * .33, hc * .5), (-w * .27, hc * .74)),
                     ("L", (-w * .3, hc * 1.2)), ("L", (-w, hc * 1.2)), ("Z",)], .09))
        out.append(([("M", (w, -1)), ("L", (w * .37, -1)), ("C", (w * .38, hc * .3), (w * .36, hc * .5), (w * .3, hc * .74)),
                     ("L", (w * .32, hc * 1.2)), ("L", (w, hc * 1.2)), ("Z",)], .045))
    elif kind == "canine":
        out.append(([("M", (-w, -1)), ("L", (w * .06, -1)), ("C", (w * .07, hc * .3), (w * .04, hc * .55), (w * .01, hc * .82)),
                     ("L", (0, hc * 1.2)), ("L", (-w, hc * 1.2)), ("Z",)], .07))
        out.append(([("M", (-w, -1)), ("L", (-w * .3, -1)), ("C", (-w * .33, hc * .4), (-w * .3, hc * .58), (-w * .22, hc * .76)),
                     ("L", (-w * .24, hc * 1.2)), ("L", (-w, hc * 1.2)), ("Z",)], .06))
    elif kind == "premolar":
        out.append(([("M", (-w, -1)), ("L", (0, -1)), ("C", (-w * .01, hc * .3), (-w * .02, hc * .5), (-w * .03, hc * .74)),
                     ("L", (-w * .03, hc * 1.2)), ("L", (-w, hc * 1.2)), ("Z",)], .06))
        out.append(([("M", (w, -1)), ("L", (w * .32, -1)), ("Q", (w * .34, hc * .45), (w * .26, hc * .68)),
                     ("L", (w * .28, hc * 1.2)), ("L", (w, hc * 1.2)), ("Z",)], .045))
    else:
        out.append(([("M", (-w, -1)), ("L", (-w * .02, -1)), ("C", (-w * .03, hc * .3), (-w * .045, hc * .42), (-w * .05, hc * .54)),
                     ("L", (-w * .06, hc * 1.2)), ("L", (-w, hc * 1.2)), ("Z",)], .06))
        out.append(([("M", (w, -1)), ("L", (w * .3, -1)), ("C", (w * .3, hc * .3), (w * .26, hc * .45), (w * .17, hc * .58)),
                     ("L", (w * .2, hc * 1.2)), ("L", (w, hc * 1.2)), ("Z",)], .04))
    return out


def _lobed(cw, hc, hr, lobes, notches):
    """root silhouette from the mesial cervical point (cw/2, hc) to the distal one (-cw/2, hc).
    lobes: [(apex x, apex y, tip half-width)] from mesial to distal; notches: [(x, y)] between them."""
    x, y, h = lobes[0]
    cmds = [("C", (cw * .47, hc + hr * .33), (x + h * 1.5, y - hr * .2), (x + h * .8, y - h * .5)),
            ("C", (x + h * .55, y + h * .2), (x - h * .55, y + h * .2), (x - h * .8, y - h * .5))]
    for (nx, ny), (x2, y2, h2) in zip(notches, lobes[1:]):
        cmds += [("C", (x - h * 1.0, y - (y - ny) * .5), (nx + (x - nx) * .45, ny), (nx, ny)),
                 ("C", (nx - (nx - x2) * .45, ny), (x2 + h2 * 1.0, y2 - (y2 - ny) * .5), (x2 + h2 * .8, y2 - h2 * .5)),
                 ("C", (x2 + h2 * .55, y2 + h2 * .2), (x2 - h2 * .55, y2 + h2 * .2), (x2 - h2 * .8, y2 - h2 * .5))]
        x, y, h = x2, y2, h2
    cmds.append(("C", (x - h * 1.6, y - hr * .2), (-cw * .47, hc + hr * .33), (-cw / 2, hc)))
    return cmds


def _root_lobes(form, cw, hc, hr):
    """apices [(x, y, tip half-width)] from mesial to distal and the notches between them"""
    t = -cw * .12            # roots lean a little distally
    a = hc + hr               # apex level
    if form == "1":
        return [(t, a, cw * .16)], []
    if form == "f":           # fused roots of a wisdom tooth
        return [(t, a, cw * .24)], []
    if form == "2b":          # upper first premolar: buccal + palatal root split near the apex
        return [(cw * .19 + t, a, cw * .12), (-cw * .19 + t, a - hr * .03, cw * .12)], [(t, a - hr * .36)]
    if form == "2":           # lower molar: mesial + distal root
        return [(cw * .3 + t, a, cw * .12), (-cw * .3 + t, a - hr * .06, cw * .12)], [(t * .3, hc + hr * .3)]
    # upper molar: mesio-buccal, palatal (seen between them, longest), disto-buccal
    return ([(cw * .46 + t, a - hr * .1, cw * .1), (t * .4, a + hr * .06, cw * .1), (-cw * .46 + t, a - hr * .18, cw * .1)],
            [(cw * .22 + t * .5, a - hr * .52), (-cw * .22 + t * .5, a - hr * .55)])


def _roots(form, cw, hc, hr):
    return _lobed(cw, hc, hr, *_root_lobes(form, cw, hc, hr))


def _fmt(cmds, tf):
    out = []
    for c in cmds:
        if c[0] == "Z":
            out.append("Z")
            continue
        pts = " ".join("%.2f %.2f" % tf(*p) for p in c[1:])
        out.append(c[0] + pts)
    return "".join(out)


def tooth_geom(n, cx, y0, s, upper, k=1.0, grow_down=None):
    """geometry of tooth n (FDI) in a local frame — x toward the midline (mesial), y from the incisal edge (0)
    through the neck (hc) to the apex — plus `tf` that maps local mm to absolute px.
    cx — centre, y0 — level of the incisal edge, s — px per mm, k — vertical stretch.
    Upper teeth grow up (roots up) unless grow_down says otherwise."""
    q, pos = n // 10, n % 10
    w, cw, hc, hr, form, kind = ANATOMY["upper" if upper else "lower"][pos]
    hr *= ROOT_K
    sx = 1 if q in (1, 4) else -1          # mesial points to the midline
    down = (not upper) if grow_down is None else grow_down
    sy = 1 if down else -1

    def tf(x, y):
        return cx + sx * x * s, y0 + sy * y * s * k
    crown = _crown_outline(kind, w, cw, hc)
    lobes, notches = _root_lobes(form, cw, hc, hr)
    return {
        "n": n, "w": w, "cw": cw, "hc": hc, "hr": hr, "form": form, "kind": kind, "upper": upper,
        "lobes": lobes, "tf": tf, "s": s, "cx": cx,
        "relief": _fmt(_relief(kind, w, hc, form), tf),
        "facets": [(_fmt(cmds, tf), op) for cmds, op in _facets(kind, w, hc)],
        "sil": _fmt(crown + _lobed(cw, hc, hr, lobes, notches) + [("Z",)], tf),
        "crown": _fmt(crown + [("Q", (0, hc + hc * .09), (-cw / 2, hc)), ("Z",)], tf),
        "cej": _fmt([("M", (cw / 2, hc)), ("Q", (0, hc + hc * .09), (-cw / 2, hc))], tf),
    }


def tooth_paths(n, cx, y0, s, upper, k=1.0):
    """silhouette, crown and cemento-enamel line of tooth n (FDI) in absolute px (see tooth_geom)"""
    g = tooth_geom(n, cx, y0, s, upper, k)
    return g["sil"], g["crown"], g["cej"], g["w"] * s


def chart_layout(width):
    """positions shared by every chart: scale, rows and tooth centres"""
    gap = width * .0045
    mid_gap = width * .02
    total = max(sum(ANATOMY[j][p][0] for p in range(1, 9)) * 2 for j in ("upper", "lower"))
    s = (width - mid_gap - gap * 14) / total
    num_h = 9
    up_len = max(a[2] + a[3] * ROOT_K for a in ANATOMY["upper"].values()) * s
    lo_len = max(a[2] + a[3] * ROOT_K for a in ANATOMY["lower"].values()) * s
    occl_up = num_h + 2 + up_len
    occl = occl_up + 2.2
    occl_lo = occl + 2.2
    bot = occl_lo + lo_len
    centres = {}
    for jaw, seq in (("upper", UPPER), ("lower", LOWER)):
        for side, ns in ((-1, seq[:8][::-1]), (1, seq[8:])):
            x = width / 2 + side * mid_gap / 2
            for n in ns:
                w = ANATOMY[jaw][n % 10][0] * s
                centres[n] = x + side * w / 2
                x += side * (w + gap)
    return {"s": s, "num_h": num_h, "occl_up": occl_up, "occl": occl, "occl_lo": occl_lo, "bot": bot,
            "height": bot + num_h + 3, "centres": centres, "mid": width / 2}


_chart_seq = [0]


def tooth_gradients(uid):
    """soft left-to-right lighting for crowns and roots: 'on' (storm blue) and 'off' (white) variants"""
    def g(gid, c0, c1):
        return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{c0}"/>'
                f'<stop offset="1" stop-color="{c1}"/></linearGradient>')
    return ("<defs>" + g(f"{uid}c_on", "#a7b6c8", "#8c9eb4") + g(f"{uid}r_on", "#d2dbe5", "#bfcad7")
            + g(f"{uid}c_off", "#ffffff", "#eef2f6") + g(f"{uid}r_off", "#f7f9fb", "#eaeef3") + "</defs>")


def chart(teeth, width=320, show_sides=True, label=True):
    """Full FDI chart in buccal view, anatomical tooth forms; `teeth` = tooth numbers (ints) to highlight."""
    teeth = set(teeth)
    _chart_seq[0] += 1
    uid = f"c{_chart_seq[0]}"
    gap = width * .0045
    mid_gap = width * .02
    total = max(sum(ANATOMY[j][p][0] for p in range(1, 9)) * 2 for j in ("upper", "lower"))
    s = (width - mid_gap - gap * 14) / total
    num_h = 9
    up_len = max(a[2] + a[3] * ROOT_K for a in ANATOMY["upper"].values()) * s
    lo_len = max(a[2] + a[3] * ROOT_K for a in ANATOMY["lower"].values()) * s
    occl_up = num_h + 2 + up_len          # incisal level of the upper teeth
    occl = occl_up + 2.2                    # occlusal line
    occl_lo = occl + 2.2
    bot = occl_lo + lo_len
    height = bot + num_h + 3
    cx0 = width / 2
    roots, crowns, lines, nums, clips = [], [], [], [], []
    for jaw, seq, y0 in (("upper", UPPER, occl_up), ("lower", LOWER, occl_lo)):
        for side, ns in ((-1, seq[:8][::-1]), (1, seq[8:])):      # from the midline outward
            x = cx0 + side * mid_gap / 2
            for n in ns:
                w = ANATOMY[jaw][n % 10][0] * s
                cx = x + side * w / 2
                g = tooth_geom(n, cx, y0, s, jaw == "upper")
                sil, crown, cej = g["sil"], g["crown"], g["cej"]
                on = "on" if n in teeth else "off"
                roots.append(f'<path d="{sil}" fill="url(#{uid}r_{on})" class="ch-root-{on}"/>')
                crowns.append(f'<path d="{crown}" fill="url(#{uid}c_{on})" class="ch-crown-{on}"/>')
                clips.append(f'<clipPath id="{uid}k{n}"><path d="{crown}"/></clipPath>')
                facets = "".join(f'<path d="{d}" fill="#1e2a3a" fill-opacity="{op * (1.4 if on == "on" else 1):.3f}"/>' for d, op in g["facets"])
                crowns.append(f'<g clip-path="url(#{uid}k{n})">{facets}</g>')
                lines.append(f'<path d="{g["relief"]}" class="ch-rel-{on}"/><path d="{sil}" class="ch-edge-{on}"/><path d="{cej}" class="ch-cej-{on}"/>')
                ny = num_h - 1.5 if jaw == "upper" else height - 1.5
                nums.append(f'<text x="{cx:.1f}" y="{ny:.1f}" class="{"ch-num-on" if n in teeth else "ch-num"}" text-anchor="middle">{n}</text>')
                x += side * (w + gap)
    guide = (f'<line x1="0" y1="{occl:.1f}" x2="{width}" y2="{occl:.1f}" class="ch-line"/>'
             f'<line x1="{cx0:.1f}" y1="{num_h + 1:.1f}" x2="{cx0:.1f}" y2="{bot:.1f}" class="ch-line"/>')
    sides = '<div class="ch-sides"><span>права сторона</span><span>ліва сторона</span></div>' if show_sides else ""
    aria = ("Зубна формула: " + ", ".join(str(t) for t in UPPER + LOWER if t in teeth)) if label else ""
    svg = (f'<svg class="chart" width="{width}" height="{height:.0f}" viewBox="0 0 {width} {height:.1f}" '
           f'role="img" aria-label="{aria}" xmlns="http://www.w3.org/2000/svg">{tooth_gradients(uid).replace("</defs>", "".join(clips) + "</defs>")}{guide}{"".join(roots)}{"".join(crowns)}{"".join(lines)}{"".join(nums)}</svg>')
    return f'<div class="chart-wrap" style="width:{width}px">{svg}{sides}</div>'


def chart_order(t):
    """sort key: upper row left to right, then lower row left to right"""
    try:
        n = int(t)
    except ValueError:
        return (9, 0, str(t))
    seq = UPPER + LOWER
    return (0, seq.index(n), "") if n in seq else (8, n, "")
