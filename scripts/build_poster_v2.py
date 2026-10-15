"""A0 poster v2: every graphic is a live Canva shape (no raster art except SEM micrographs).

Generates edit-design operation batches for the Canva connector:
  v2_shapes.json  structure, vector illustrations, icons
  v2_charts.json  live vector charts (UV-Vis, XRD, FTIR, EDX, DLS)
  v2_texts.json   add_text operations (+ v2_texts_spec.json for formatting)
  v2_reuse.json   restyling of the 46 reused heading text boxes
"""
import json
import math
import os
import re as regex

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.environ.get("OUT_DIR", HERE)
PID = "PBb37h5XYVJp81DH"
W, H = 3179, 4494

# palette
FOREST, FOREST_D, HEADER_BG = "#1F7A3A", "#14532D", "#0F3D24"
BERRY, BERRY_D, BERRY_L, BERRY_T = "#A3195B", "#6D1140", "#F2C4D8", "#FCE8F1"
TEAL, TEAL_D, TEAL_L, TEAL_T = "#0E7490", "#155E75", "#A9DCE8", "#E3F4F8"
AMBER, AMBER_D, AMBER_L, AMBER_T = "#D97706", "#92400E", "#F6C77A", "#FFF7E6"
LIME, LIME_SOFT = "#A3E635", "#D9F99D"
MINT, GREEN_L, GREEN_T = "#F1F8F1", "#B7DDB9", "#E6F4E7"
TXT, MUTED, AXIS, GRID = "#1F2D24", "#4A5E50", "#37474F", "#E3ECE4"
RED, BLUE, WHITE, INK = "#C62828", "#1565C0", "#FFFFFF", "#1E1E1E"

shapes, charts, texts, reuse, reuse_locs = [], [], [], [], []
cur = shapes


def r1(v):
    return round(v, 1)


def shape(x, y, w, h, path, vw, vh, color=None, stroke=None, sw=None, opacity=None, rot=None):
    op = {"type": "insert_shape", "page_id": PID, "top": r1(y), "left": r1(x),
          "width": r1(max(w, 1)), "height": r1(max(h, 1)), "path": path,
          "view_box_width": r1(max(vw, 1)), "view_box_height": r1(max(vh, 1))}
    if color:
        op["color"] = color
    if stroke:
        op["stroke_color"] = stroke
        op["stroke_weight"] = sw or 2
    if opacity is not None:
        op["opacity"] = opacity
    if rot:
        op["rotation"] = rot
    cur.append(op)


def scale_path(d, s):
    """Scale an SVG path (M/L/H/V/C/S/A/Z, absolute) by s, leaving arc flags/rotation alone."""
    toks = regex.findall(r"[MLHVCSAZmlhvcsaz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    out, cmd, idx = [], None, 0
    for t in toks:
        if t.isalpha():
            cmd, idx = t, 0
            out.append(t)
            continue
        v = float(t)
        if cmd in "Aa":
            k = idx % 7
            if k in (2, 3, 4):
                out.append(t)
            else:
                out.append(str(round(v * s, 1)))
        else:
            out.append(str(round(v * s, 1)))
        idx += 1
    return " ".join(out)


def gshape(x, y, size, path, box=100, **kw):
    """Shape from a path authored in a box x box design space, drawn at size px."""
    s = size / box
    shape(x, y, size, size, scale_path(path, s), size, size, **kw)


def rrect(x, y, w, h, r, color=None, stroke=None, sw=None, opacity=None):
    r = min(r, w / 2, h / 2)
    p = (f"M{r1(r)} 0H{r1(w-r)}A{r1(r)} {r1(r)} 0 0 1 {r1(w)} {r1(r)}V{r1(h-r)}"
         f"A{r1(r)} {r1(r)} 0 0 1 {r1(w-r)} {r1(h)}H{r1(r)}A{r1(r)} {r1(r)} 0 0 1 0 {r1(h-r)}"
         f"V{r1(r)}A{r1(r)} {r1(r)} 0 0 1 {r1(r)} 0Z") if r > 0 else f"M0 0H{r1(w)}V{r1(h)}H0Z"
    shape(x, y, w, h, p, w, h, color, stroke, sw, opacity)


def circ_path(cx, cy, r):
    return f"M{r1(cx-r)} {r1(cy)}A{r1(r)} {r1(r)} 0 1 1 {r1(cx+r)} {r1(cy)}A{r1(r)} {r1(r)} 0 1 1 {r1(cx-r)} {r1(cy)}Z"


def circle(x, y, d, color=None, stroke=None, sw=None, opacity=None):
    shape(x, y, d, d, circ_path(d / 2, d / 2, d / 2), d, d, color, stroke, sw, opacity)


def segs(segments, stroke, sw, color=None):
    xs = [p[0] for s in segments for p in s]
    ys = [p[1] for s in segments for p in s]
    mx, my = min(xs), min(ys)
    w, h = max(xs) - mx, max(ys) - my
    if w < 1:
        mx -= 0.5
        w = 1
    if h < 1:
        my -= 0.5
        h = 1
    prec = 0 if sum(len(s) for s in segments) > 120 else 1
    fmt = (lambda v: str(int(round(v)))) if prec == 0 else (lambda v: str(r1(v)))
    parts = ["M" + " L".join(f"{fmt(px-mx)} {fmt(py-my)}" for px, py in s) for s in segments]
    shape(mx, my, w, h, " ".join(parts), w, h, color, stroke, sw)


def img(asset, x, y, w, h, alt):
    cur.append({"type": "insert_fill", "page_id": PID, "asset_type": "image", "asset_id": asset,
                "alt_text": alt, "top": r1(y), "left": r1(x), "width": r1(w), "height": r1(h)})


def text(x, y, w, s, size, color=TXT, bold=False, align="start", lh=1.35, italic=False, rot=None):
    texts.append({"x": r1(x), "y": r1(y), "w": r1(w), "text": s, "size": size, "color": color,
                  "bold": bold, "align": align, "lh": lh, "italic": italic, "rot": rot})


def rtext(cx, cy, w, s, size, color, **kw):
    hgt = size * kw.get("lh", 1.2)
    text(cx - w / 2, cy - hgt / 2, w, s, size, color, align="center", rot=-90, **kw)


def re(loc, s, x, y, w, size, color, bold=None, align="start", lh=1.2, italic=False):
    L = f"{PID}-{loc}"
    f = {"font_size": size, "color": color, "text_align": align, "line_height": lh,
         "font_style": "italic" if italic else "normal"}
    if bold is not None:
        f["font_weight"] = "bold" if bold else "normal"
    reuse.extend([
        {"type": "replace_text", "locator_id": L, "text": s},
        {"type": "format_text", "locator_id": L, "formatting": f},
        {"type": "resize_element", "locator_id": L, "width": r1(w)},
        {"type": "position_element", "locator_id": L, "top": r1(y), "left": r1(x)},
    ])
    reuse_locs.append(L)


# ------------------------------------------------------------------ icon glyphs (100x100)
def cp(cx, cy, r):
    return circ_path(cx, cy, r)


G = {
    "flask": ("M38 10H62 M43 10V40L18 84C15 90 19 94 25 94H75C81 94 85 90 82 84L57 40V10 M28 66H72", "s"),
    "hex": ("M50 8L86 29V71L50 92L14 71V29Z M50 8V50 M14 29L50 50L86 29 M50 50V92", "s"),
    "peak": ("M6 82H20C36 82 38 16 50 16C62 16 64 82 80 82H94 M6 92H94", "s"),
    "wave": ("M4 30H26L33 62L40 30H52L57 52L63 30H74L78 44L82 30H96 M4 88H96", "s"),
    "mag": (cp(42, 42, 27) + " M62 62L88 88", "s"),
    "atom": ("M8 50A42 16 0 1 1 92 50A42 16 0 1 1 8 50Z M50 8A16 42 0 1 1 50 92A16 42 0 1 1 50 8Z " + cp(50, 50, 6), "s"),
    "dist": ("M6 90H94 M10 86C32 86 36 16 50 16C64 16 68 86 90 86", "s"),
    "bulb": ("M50 8C30 8 18 24 18 40C18 56 32 62 34 74H66C68 62 82 56 82 40C82 24 70 8 50 8Z M36 84H64 M40 94H60", "s"),
    "target": (cp(46, 54, 38) + " " + cp(46, 54, 22) + " " + cp(46, 54, 6) + " M50 50L86 14 M72 12H88V28", "s"),
    "leaf": ("M16 86C16 42 44 14 88 12C88 58 60 86 16 86Z M16 86L64 38", "s"),
    "mol": ("M50 14L74 28V56L50 70L26 56V28Z M74 28L92 18 M26 56L8 66 M50 70V92 M40 34V50", "s"),
    "check": (cp(50, 50, 40) + " M30 52L44 66L72 36", "s"),
    "cluster": (cp(50, 52, 18) + " " + cp(24, 34, 13) + " " + cp(76, 32, 13) + " " + cp(24, 74, 13) + " " + cp(76, 74, 13) + " " + cp(50, 16, 10) + " " + cp(50, 88, 10), "f"),
    "pill": ("M22 64L64 22C72 14 86 14 92 22C100 30 100 42 92 50L50 92C42 100 28 100 20 92C12 84 12 72 22 64Z M43 43L71 71", "s"),
    "factory": ("M8 92V48L32 62V48L56 62V26H70V14H82V92Z M8 92H92 M20 76H28 M40 76H48 M64 76H72", "s"),
    "star": ("M50 6L62 38H96L69 58L79 92L50 72L21 92L31 58L4 38H38Z", "f"),
    "drop": ("M50 6C50 6 18 46 18 64C18 82 32 94 50 94C68 94 82 82 82 64C82 46 50 6 50 6Z", "f"),
    "flame": ("M50 4C60 28 82 40 82 64C82 82 68 96 50 96C32 96 18 82 18 64C18 48 30 42 34 26C40 42 46 46 50 52C54 38 48 20 50 4Z", "f"),
    "sun": (cp(50, 50, 18) + " M50 6V20 M50 80V94 M6 50H20 M80 50H94 M19 19L29 29 M71 71L81 81 M19 81L29 71 M71 29L81 19", "s"),
    "chip": ("M8 70H30L38 40L48 82L58 28L66 70H92", "s"),
}


def icon(x, y, d, name, bg, fg=WHITE, ring=None):
    """Coloured circle with a white (or fg) vector glyph, all live shapes."""
    circle(x, y, d, bg, ring, 4 if ring else None)
    path, mode = G[name]
    g = d * 0.58
    gx, gy = x + (d - g) / 2, y + (d - g) / 2
    if mode == "f":
        gshape(gx, gy, g, path, color=fg)
    else:
        gshape(gx, gy, g, path, stroke=fg, sw=max(2.5, d * 0.06))


# ------------------------------------------------------------------ vector botanicals
HEART = "M100 252C60 202 8 160 8 96C8 40 50 12 86 28C96 33 100 44 100 56C100 44 104 33 114 28C150 12 192 40 192 96C192 160 140 202 100 252Z"
HEART_V = ("M100 58V246 M100 96C80 84 54 88 32 104 M100 138C76 126 50 136 26 156 M100 178C80 172 62 182 46 202 "
           "M100 96C120 84 146 88 168 104 M100 138C124 126 150 136 174 156 M100 178C120 172 138 182 154 202")
OVAL = "M50 0C86 40 96 122 50 200C4 122 14 40 50 0Z"
OVAL_V = "M50 12V192 M50 70L74 50 M50 100L78 78 M50 130L74 112 M50 70L26 50 M50 100L22 78 M50 130L26 112"


def betel(x, y, w, h, rot, fill, vein, opacity=None):
    shape(x, y, w, h, HEART, 200, 260, color=fill, rot=rot, opacity=opacity)
    shape(x, y, w, h, HEART_V, 200, 260, stroke=vein, sw=max(2, w * 0.012), rot=rot, opacity=opacity)


def oval_leaf(x, y, w, h, rot, fill, vein, opacity=None):
    shape(x, y, w, h, OVAL, 100, 200, color=fill, rot=rot, opacity=opacity)
    shape(x, y, w, h, OVAL_V, 100, 200, stroke=vein, sw=max(2, w * 0.02), rot=rot, opacity=opacity)


def sphere(cx, cy, r):
    circle(cx - r, cy - r, 2 * r, "#D7DBE0", "#9AA3AD", 3)
    circle(cx - r * 0.55, cy - r * 0.62, r * 0.55, "#F4F6F8")
    for a, b in ((0.25, 0.35), (-0.35, 0.3), (0.1, -0.05), (0.45, -0.25)):
        circle(cx + a * r - 4, cy + b * r - 4, 8, "#AEB6BF")


# ================================================================== HEADER
for lx, ly, rot, fill in ((-80, 4250, 30, "#2F7D4F"), (60, 4300, -15, "#3E9A5F"), (-40, 4330, 70, "#276A42")):
    oval_leaf(lx, ly, 150, 300, rot, fill, "#BBF7D0")
for lx, ly, rot, fill in ((3030, 4250, -30, "#2F7D4F"), (2900, 4300, 15, "#3E9A5F"), (2990, 4330, -70, "#276A42")):
    oval_leaf(lx, ly, 150, 300, rot, fill, "#BBF7D0")

shape(0, 0, W, 820, f"M0 0H{W}V770C2500 840 900 720 0 800Z", W, 820, HEADER_BG)
# faint molecular network
for hx, hy, s in ((600, 640, 70), (690, 700, 50), (2480, 70, 60), (2420, 150, 40)):
    gshape(hx, hy, s, "M50 6L88 28V72L50 94L12 72V28Z", stroke=LIME, sw=3, opacity=0.25)
segs([[(670, 675), (712, 705)], [(2540, 130), (2580, 100)]], LIME, 3)

betel(-70, -60, 330, 430, 35, "#8E1650", "#F9A8D4")
betel(110, -100, 300, 390, -20, BERRY, "#FBCFE8")
betel(250, 180, 250, 330, -55, "#2F7D4F", "#BBF7D0")
betel(-50, 300, 280, 360, 18, BERRY_D, "#F9A8D4")
betel(360, 30, 190, 250, -72, "#3E9A5F", LIME_SOFT)

oval_leaf(2560, -70, 200, 400, 40, "#2F7D4F", "#BBF7D0")
oval_leaf(2930, 190, 180, 360, -35, "#3E9A5F", "#BBF7D0")
oval_leaf(2680, 330, 150, 300, 75, "#276A42", "#BBF7D0")
for cx, cy, r in ((2680, 270, 52), (3020, 270, 48), (2760, 250, 76), (2900, 235, 68), (2720, 365, 62),
                  (2960, 350, 70), (2840, 340, 82), (2800, 452, 66), (2930, 462, 60)):
    sphere(cx, cy, r)
for cx, cy, r in ((2620, 130, 28), (3110, 520, 24), (2600, 600, 18), (3080, 120, 16)):
    circle(cx - r, cy - r, 2 * r, None, "#E0F2E9", 3, opacity=0.7)
circle(2860, 560, 210, AMBER, WHITE, 8)
rrect(1395, 448, 390, 8, 4, LIME)
rrect(1785, 484, 4, 210, 2, "#3F7A55")
rrect(985, 724, 1210, 64, 32, LIME)

re("LBVfdr3ZrZYxnLsd", "SINTESIS HIJAU DAN KARAKTERISASI\nNANOPARTIKEL SENG OKSIDA (ZnO)", 560, 46, 2060, 92, WHITE, None, "center", 1.08)
re("LB2PmCqmfDGPzkWt", "MENGGUNAKAN EKSTRAK AIR DAUN SIRIH MERAH", 560, 268, 2060, 58, LIME, True, "center", 1.2)
re("LBtSxlSVnTm1Pt2q", "(Piper porphyrophyllum)", 560, 348, 2060, 56, LIME_SOFT, True, "center", 1.2, italic=True)
re("LB3sYky8LPtsq6Wy", "Tim Peneliti:", 745, 478, 1000, 38, LIME, True, "start", 1.2)
re("LB0DLLqGFBmxnCK3", "Prof. Dr. rer. nat. apt. Deni Rahmat, S.Si.\nProf. Dr. apt. Yesi Desmiati, M.Si.\nProf. Dr. apt. Ni Made Dwi Sandhiutami, S.Si., M.Kes.\nTria Prayoga, S.Farm., M.Farm.", 745, 528, 1010, 32, "#E8F5EC", False, "start", 1.3)
re("LB1yCS23g5tVTr98", "Pendanaan: Hibah BIMA 2026 – Penelitian Disertasi Doktor (PDD)", 985, 736, 1210, 31, HEADER_BG, True, "center", 1.2)
text(1820, 500, 760, "¹ Fakultas Farmasi,\n   Universitas Pancasila, Jakarta\n² STIKes IKIFA, Jakarta", 32, "#E8F5EC", lh=1.35)
text(2860, 620, 210, "ZnO", 70, WHITE, bold=True, align="center", lh=1.1)

# ================================================================== OBJECTIVE BANNER
rrect(90, 832, 2999, 170, 85, AMBER_T, AMBER_L, 5)
icon(108, 847, 140, "bulb", AMBER)
rrect(728, 862, 6, 110, 3, AMBER)
re("LBMNmvWby1rnNTpj", "Tujuan Utama:", 275, 882, 450, 54, AMBER_D, True, "start", 1.2)
text(768, 866, 2290, "Sintesis hijau menggunakan ekstrak air daun sirih merah untuk menghasilkan nanopartikel ZnO berstruktur kristal heksagonal wurtzite dengan kristalinitas tinggi dan ukuran kristalit pada skala nanometer.", 37, TXT, lh=1.35)

# ================================================================== SECTIONS
num_locs = ["LB39PwTp4smC3qwp", "LBbBK0mYp5ptdY4t", "LBckj9dcRq327yBp", "LBRzG8pz6fLrMxBv",
            "LBszgX5fFtR2qZtV", "LBSSwfXBFxvklc5Q", "LBmZhjdB7gtsXZgr", "LBWyCMbBmHy1PPPv",
            "LBDWMg19WtZcmNnF", "LBLPcrmgz6b22H7S"]
head_locs = ["LBQL8cBDpnc2sB6G", "LBPYCcRWPXVpJT0W", "LBmg6Dmc926Vhqnj", "LBVj9TTjmxhJtzVb",
             "LBq3vP31686L074Y", "LB785vXdyDWFdR1P", "LB6tS7Kg4BmKfXPS", "LBFFzSFTLj1F0wFK",
             "LBvj83nZnGH81ktW", "LBTgLdjlmrGKPb1D"]


def section(n, title, x, y, w, h, col, pill_w=None, card=WHITE):
    main, dark, light, tint = col
    if h:
        rrect(x, y, w, h, 32, card, light, 5)
    rrect(x, y, pill_w or w, 104, 32 if h else 52, main)
    circle(x + 12, y - 8, 120, dark, WHITE, 6)
    re(num_locs[n - 1], str(n), x + 12, y + 18, 120, 62, WHITE, None, "center", 1.0)
    re(head_locs[n - 1], title, x + 148, y + 25, (pill_w or w) - 165, 44, WHITE, True, "start", 1.2)


CB = (BERRY, BERRY_D, BERRY_L, BERRY_T)
CG = (FOREST, FOREST_D, GREEN_L, GREEN_T)
CT = (TEAL, TEAL_D, TEAL_L, TEAL_T)
CA = (AMBER, AMBER_D, AMBER_L, AMBER_T)
LX, LW, MX, MW, RX, RW = 90, 700, 840, 1499, 2389, 700

# ------------------------------------------------------------------ 1 LATAR BELAKANG
section(1, "LATAR BELAKANG", LX, 1040, LW, 660, CB)
for yy, ic, s in ((1170, "pill", "Nanopartikel seng oksida (ZnO) memiliki potensi luas dalam bidang farmasi."),
                  (1325, "leaf", "Sintesis hijau menggunakan ekstrak tumbuhan, seperti daun sirih merah (Piper porphyrophyllum), menawarkan metode ramah lingkungan."),
                  (1523, "mol", "Memanfaatkan senyawa metabolit sekunder sebagai agen pereduksi dan penstabil nanopartikel.")):
    icon(122, yy, 64, ic, BERRY)
    text(208, yy - 2, 556, s, 32, TXT, lh=1.35)

# ------------------------------------------------------------------ 2 TUJUAN PENELITIAN
section(2, "TUJUAN PENELITIAN", LX, 1740, LW, 550, CB)
icon(122, 1870, 64, "target", BERRY)
text(208, 1868, 556, "Mensintesis nanopartikel ZnO menggunakan ekstrak air daun sirih merah dan mengkarakterisasi:", 32, TXT, lh=1.35)
chips = [("sun", "Sifat optik"), ("hex", "Struktur kristal"), ("wave", "Gugus fungsi"),
         ("mag", "Morfologi"), ("atom", "Komposisi unsur"), ("dist", "Ukuran hidrodinamik")]
for i, (ic, lab) in enumerate(chips):
    cx, cy = 122 + (i % 2) * 324, 2034 + (i // 2) * 82
    rrect(cx, cy, 310, 70, 35, BERRY_T, BERRY_L, 2)
    icon(cx + 9, cy + 9, 52, ic, BERRY)
    two = len(lab) * 13.5 > 225
    text(cx + 72, cy + (7 if two else 19), 228, lab, 26, BERRY_D, bold=True, lh=1.1)

# ------------------------------------------------------------------ 3 METODE PENELITIAN
section(3, "METODE PENELITIAN", LX, 2330, LW, 1730, CB)
rrect(127, 2486, 6, 1110, 3, BERRY_L)


def flask_shape(x, y, w, h, liquid, glass_stroke="#94A3B8"):
    body = "M60 0H100V70L150 190C156 205 148 215 132 215H28C12 215 4 205 10 190L60 70Z"
    liq = "M37 125H123L150 190C156 205 148 215 132 215H28C12 215 4 205 10 190Z"
    shape(x, y, w, h, body, 160, 220, color="#F1F7FB")
    shape(x, y, w, h, liq, 160, 220, color=liquid)
    shape(x, y, w, h, body + " M52 0H108", 160, 220, stroke=glass_stroke, sw=5)


def beaker(x, y, w, h, liquid):
    body = "M20 0H150V180C150 196 140 205 125 205H45C30 205 20 196 20 180Z"
    liq = "M20 82H150V180C150 196 140 205 125 205H45C30 205 20 196 20 180Z"
    shape(x, y, w, h, body, 170, 210, color="#F1F7FB")
    shape(x, y, w, h, liq, 170, 210, color=liquid)
    shape(x, y, w, h, "M6 0H164 M20 0V180C20 196 30 205 45 205H125C140 205 150 196 150 180V0 M34 40H58 M34 70H52 M34 100H58",
          170, 210, stroke="#94A3B8", sw=5)


def arrow(x, y, w, color):
    shape(x, y, w, 40, f"M0 20H{w-4} M{w-22} 4L{w-4} 20L{w-22} 36", w, 40, stroke=color, sw=6)


steps = [
    (2456, "Preparasi Ekstrak Daun Sirih Merah", "Daun sirih merah dicuci, diekstraksi dengan air (50°C, 45 menit), kemudian disaring."),
    (2996, "Sintesis Nanopartikel ZnO", "Larutan Zn(NO₃)₂ direaksikan dengan ekstrak daun sirih merah, dipanaskan (100°C, 2 jam), lalu dikalsinasi (450°C, 3 jam)."),
    (3576, "Karakterisasi", "UV-Vis, XRD, FTIR, SEM-EDX, dan DLS."),
]
for i, (sy, head, body) in enumerate(steps):
    circle(102, sy - 4, 56, BERRY, WHITE, 5)
    text(102, sy + 6, 56, str(i + 1), 30, WHITE, bold=True, align="center", lh=1.1)
    text(175, sy + 2, 600, head, 31, BERRY, bold=True, lh=1.25)
    ox, oy = 175, sy + 54
    rrect(ox, oy, 585, 300, 26, "#FBF3F7" if i == 0 else ("#FFF8EE" if i == 1 else "#EEF7FA"))
    if i == 0:
        betel(ox + 150, oy + 70, 150, 190, 25, "#2F7D4F", "#BBF7D0")
        betel(ox + 30, oy + 25, 200, 255, -15, BERRY, "#FBCFE8")
        gshape(ox + 250, oy + 34, 46, G["drop"][0], color="#38BDF8")
        arrow(ox + 300, oy + 135, 80, BERRY)
        beaker(ox + 395, oy + 55, 160, 200, "#9A3412")
        text(ox + 395, oy + 262, 160, "50°C · 45 menit", 20, BERRY_D, bold=True, align="center", lh=1.1)
    elif i == 1:
        flask_shape(ox + 50, oy + 40, 150, 210, "#B45309")
        gshape(ox + 262, oy + 70, 54, G["flame"][0], color="#F97316")
        gshape(ox + 274, oy + 92, 30, G["flame"][0], color="#FDE047")
        arrow(ox + 232, oy + 150, 110, AMBER)
        flask_shape(ox + 370, oy + 40, 150, 210, "#F8FAFC", glass_stroke="#94A3B8")
        for bx, by in ((ox + 420, oy + 205), (ox + 455, oy + 222), (ox + 440, oy + 190), (ox + 475, oy + 200)):
            circle(bx, by, 14, "#CBD5E1")
        text(ox + 230, oy + 205, 130, "100°C → 450°C", 20, AMBER_D, bold=True, align="center", lh=1.1)
    else:
        rrect(ox + 30, oy + 36, 170, 230, 14, "#F8FAFC", "#94A3B8", 4)
        rrect(ox + 50, oy + 62, 130, 110, 10, "#334155")
        circle(ox + 92, oy + 94, 46, None, "#22D3EE", 4)
        rrect(ox + 30, oy + 236, 170, 30, 8, TEAL)
        rrect(ox + 250, oy + 50, 220, 150, 12, "#1F2937")
        segs([[(ox + 268, oy + 175), (ox + 300, oy + 172), (ox + 318, oy + 110), (ox + 330, oy + 172),
               (ox + 362, oy + 168), (ox + 378, oy + 130), (ox + 392, oy + 168), (ox + 452, oy + 170)]], LIME, 4)
        rrect(ox + 346, oy + 200, 28, 34, 4, "#94A3B8")
        rrect(ox + 305, oy + 232, 110, 12, 6, "#94A3B8")
        rrect(ox + 485, oy + 150, 80, 110, 12, "#E2E8F0", "#94A3B8", 3)
        rrect(ox + 497, oy + 165, 56, 26, 6, TEAL)
        rrect(ox + 20, oy + 268, 545, 8, 4, "#CBD5E1")
    text(175, oy + 314, 585, body, 30, TXT, lh=1.38, align="center" if i == 2 else "start")

# ------------------------------------------------------------------ 4 PARAMETER UTAMA
section(4, "PARAMETER UTAMA HASIL", MX, 1040, MW, 600, CG)
tiles = [("UV-Vis\nλ maks", "378,47", "nm", "peak", TEAL),
         ("Kristalinitas\n(XRD)", "89,87%", None, "hex", BERRY),
         ("Ukuran Kristalit\n(XRD)", "30,41", "nm", "cluster", AMBER)]
val_locs = ["LB93b4WPYrrlnxR0", "LBNs3StDdMW8ftJH", "LBCwcMR8JBy1slQL"]
lab_locs = ["LB5LXWRCwd8l5Wbc", "LBDXwr85lTsc7P2Y", "LBBb7J20FL0dds42"]
unit_locs = {0: "LBYCRSKhdXc3CvSs", 2: "LBH9XFNDHvXWxVK4"}
for i, (lab, val, unit, ic, colr) in enumerate(tiles):
    x = 875 + i * 488
    rrect(x, 1170, 453, 440, 28, colr)
    circle(x + 330, 1450, 190, WHITE, None, opacity=0.08)
    icon(x + 26, 1198, 136, ic, WHITE, fg=colr)
    re(lab_locs[i], lab, x + 178, 1214, 263, 34, WHITE, True, "start", 1.15)
    re(val_locs[i], val, x, 1366, 453, 112, WHITE, None, "center", 1.0)
    if unit:
        re(unit_locs[i], unit, x, 1492, 453, 54, WHITE, True, "center", 1.1)

# ------------------------------------------------------------------ 5 HASIL KARAKTERISASI (frames)
section(5, "HASIL KARAKTERISASI", MX, 1680, MW, 2380, CG)
PAN = {"A": (875, 1815, 697, 700, TEAL), "B": (1607, 1815, 697, 700, BERRY),
       "C": (875, 2550, 697, 700, AMBER), "D": (1607, 2550, 697, 700, FOREST), "E": (875, 3285, 1429, 740, TEAL)}
ptitle_locs = {"A": "LB8BZKKfdKtRm6Bw", "B": "LBbs8DqlzkpTlgCz", "C": "LBjKqb02cDjcMFb2",
               "D": "LBR77fdY4sXT8Jmv", "E": "LB1t7BPTMf8YYrmn"}
ptitles = {"A": "UV-Vis", "B": "XRD", "C": "FTIR", "D": "SEM dan EDX", "E": "Distribusi Ukuran Partikel (SEM dan DLS)"}
for k, (px, py, pw, ph, colr) in PAN.items():
    rrect(px, py, pw, ph, 24, WHITE, "#CBE6CE", 3)
    rrect(px + 3, py + 3, pw - 6, 108, 22, "#F6FAF6")
    rrect(px + 3, py + 108, pw - 6, 3, 1, "#E1EEE2")
    circle(px + 22, py + 22, 70, colr)
    text(px + 22, py + 33, 70, k, 38, WHITE, bold=True, align="center", lh=1.1)
    re(ptitle_locs[k], ptitles[k], px + 108, py + 32, pw - 140, 40, FOREST_D, True, "start", 1.2)

# ================================================================== CHARTS
cur = charts


def axes(X0, T, PW, PH, frame=False):
    if frame:
        segs([[(X0, T), (X0, T + PH), (X0 + PW, T + PH), (X0 + PW, T), (X0, T)]], AXIS, 3)
    else:
        segs([[(X0, T), (X0, T + PH), (X0 + PW, T + PH)]], AXIS, 3)


def ticks_x(T, PH, vals, fx, labels, size=24):
    segs([[(fx(v), T + PH), (fx(v), T + PH + 10)] for v in vals], AXIS, 3)
    for v, lab in zip(vals, labels):
        text(fx(v) - 50, T + PH + 14, 100, lab, size, AXIS, align="center", lh=1.2)


def ticks_y(X0, T, PW, PH, vals, fy, labels, size=24, grid=True):
    if grid:
        segs([[(X0 + 2, fy(v)), (X0 + PW, fy(v))] for v in vals if abs(fy(v) - (T + PH)) > 2], GRID, 2)
    segs([[(X0 - 10, fy(v)), (X0, fy(v))] for v in vals], AXIS, 3)
    for v, lab in zip(vals, labels):
        text(X0 - 112, fy(v) - size * 0.62, 98, lab, size, AXIS, align="end", lh=1.2)


def caption(px, py, s, dy=600, w=649):
    text(px + 24, py + dy, w, s, 26, MUTED, lh=1.3, italic=True)


traces = json.load(open(os.path.join(ROOT, "assets", "traces.json")))

# ---- A: UV-Vis
px, py, pw, ph, _ = PAN["A"]
X0, T, PW, PH = px + 140, py + 140, 520, 350
fx = lambda v: X0 + (v - 300) / 300 * PW
fy = lambda a: T + PH - (a - 0.334) / (0.497 - 0.334) * PH
segs([[(fx(v), T), (fx(v), T + PH)] for v in (400, 500, 600)], GRID, 2)
ticks_y(X0, T, PW, PH, [0.334, 0.350, 0.400, 0.450, 0.497], fy, ["0,334", "0,350", "0,400", "0,450", "0,497"])
axes(X0, T, PW, PH)
ticks_x(T, PH, [300, 400, 500, 600], fx, ["300", "400", "500", "600"])


def uv(l):
    s = 80.0 if l < 378.47 else 92.0
    tail = 0.03 * math.exp(-max(l - 378.47, 0) / 160) if l >= 378.47 else 0.03
    return 0.336 + 0.118 * math.exp(-((l - 378.47) / s) ** 2) + tail


segs([[(fx(l), fy(uv(l))) for l in [300 + i * 3 for i in range(101)]]], TEAL_D, 5)
pk = (fx(378.47), fy(uv(378.47)))
circle(pk[0] - 9, pk[1] - 9, 18, RED)
segs([[(pk[0], pk[1] - 16), (pk[0], pk[1] - 52)]], RED, 3)
text(pk[0] - 110, pk[1] - 98, 220, "378,47 nm", 28, RED, bold=True, align="center", lh=1.2)
text(X0, T + PH + 52, PW, "Panjang Gelombang (nm)", 26, AXIS, bold=True, align="center", lh=1.2)
rtext(px + 34, T + PH / 2, 200, "Absorbansi", 26, AXIS, bold=True)
caption(px, py, "Gambar 1. Spektrum UV-Vis nanopartikel ZnO. Puncak serapan pada 378,47 nm.")

# ---- B: XRD (traced from the authors' HD diffractogram)
px, py, pw, ph, _ = PAN["B"]
X0, T, PW, PH = px + 78, py + 118, 595, 410
fx = lambda v: X0 + (v - 10) / 80 * PW
base_s, base_r = T + 250, T + PH - 3
segs([[(fx(v), T), (fx(v), T + PH)] for v in range(20, 90, 10)], GRID, 2)
axes(X0, T, PW, PH, frame=True)
segs([[(X0, T + 262), (X0 + PW, T + 262)]], AXIS, 2)
ticks_x(T, PH, list(range(10, 91, 10)), fx, [str(v) for v in range(10, 91, 10)], size=22)
smax = max(p[1] for p in traces["xrd_sample"])
smin = min(p[1] for p in traces["xrd_sample"])
fys = lambda v: base_s - (v - smin) / (smax - smin) * 140
segs([[(fx(x), fys(y)) for x, y in traces["xrd_sample"]]], INK, 3)
rmax = max(p[1] for p in traces["xrd_std"])
rmin = min(p[1] for p in traces["xrd_std"])
segs([[(fx(x), base_r - (y - rmin) / (rmax - rmin) * 125) for x, y in traces["xrd_std"]]], RED, 3)


def ytop_sample(a):
    near = [p for p in traces["xrd_sample"] if abs(p[0] - a) < 0.35]
    return min(fys(p[1]) for p in near) if near else base_s


for ang, hkl in ((31.74, "100"), (34.41, "002"), (36.23, "101"), (47.52, "102"), (56.58, "110"), (62.86, "103"),
                 (66.37, "200"), (67.93, "112"), (69.06, "201"), (76.93, "202"), (81.42, "104"), (89.62, "203")):
    s = f"{ang:.2f}°".replace(".", ",") + f" ({hkl})"
    yt = ytop_sample(ang) - 6
    rtext(fx(ang) - (6 if ang > 89 else 0), yt - 54, 108, s, 15, INK, bold=True)
segs([[(X0 + PW - 125, T + 24), (X0 + PW - 82, T + 24)]], INK, 4)
text(X0 + PW - 76, T + 9, 80, "ZnO", 22, INK, bold=True, lh=1.2)
segs([[(X0 + 190, T + 286), (X0 + 233, T + 286)]], RED, 4)
text(X0 + 240, T + 272, 360, "ZnO Standard (JCPDS No. 79-2205)", 20, RED, bold=True, lh=1.2)
text(X0, T + PH + 46, PW, "2θ (°)", 26, AXIS, bold=True, align="center", lh=1.2)
rtext(px + 44, T + PH / 2, 260, "Intensitas (a.u.)", 24, AXIS, bold=True)
caption(px, py, "Gambar 2. Pola difraksi XRD nanopartikel ZnO dibandingkan standar JCPDS No. 79-2205.", dy=612)

# ---- C: FTIR (traced from the authors' HD spectrum)
px, py, pw, ph, _ = PAN["C"]
X0, T, PW, PH = px + 120, py + 135, 545, 370
fx = lambda v: X0 + (4000 - v) / 3600 * PW
fy = lambda v: T + PH - v / 105 * PH
ticks_y(X0, T, PW, PH, [0, 20, 40, 60, 80, 100], fy, ["0", "20", "40", "60", "80", "100"])
axes(X0, T, PW, PH, frame=True)
xt = [4000, 3500, 3000, 2500, 2000, 1500, 1000, 500]
ticks_x(T, PH, xt, fx, [str(v) for v in xt], size=21)
ft = traces["ftir"]
segs([[(fx(v), fy(t)) for v, t in ft]], INK, 3)


def ft_at(v):
    return min(ft, key=lambda p: abs(p[0] - v))[1]


for v, dx, dy, al, lead in ((2340, -40, 10, "center", 0), (1558, -86, 26, "end", 22), (1436, -40, 58, "center", 52),
                            (1118, -86, 14, "end", 8), (877, 4, 14, "start", 8), (618, -8, -38, "start", 0)):
    y0 = fy(ft_at(v))
    if lead:
        segs([[(fx(v), y0 + 4), (fx(v) - (12 if al == "end" else 0), y0 + lead)]], INK, 2)
    text(fx(v) + dx, y0 + dy, 80, str(v), 22, INK, bold=True, align=al, lh=1.2)
rrect(X0 + 22, T + PH - 72, 150, 52, 6, WHITE, AXIS, 2)
segs([[(X0 + 36, T + PH - 46), (X0 + 86, T + PH - 46)]], INK, 4)
text(X0 + 94, T + PH - 62, 80, "ZnO", 24, INK, bold=True, lh=1.2)
text(X0, T + PH + 48, PW, "Bilangan Gelombang (cm⁻¹)", 26, AXIS, bold=True, align="center", lh=1.2)
rtext(px + 30, T + PH / 2, 260, "Transmitansi (%)", 26, AXIS, bold=True)
caption(px, py, "Gambar 3. Spektrum FTIR nanopartikel ZnO. Pita serapan Zn–O pada 400–600 cm⁻¹.", dy=612)

# ---- D: SEM & EDX
px, py, pw, ph, _ = PAN["D"]
rrect(px + 24, py + 122, 315, 250, 10, "#3B4240")
rrect(px + 358, py + 122, 315, 250, 10, "#3B4240")
img("MAHYDXRDzWQ", px + 40, py + 122, 283, 250, "Citra SEM nanopartikel ZnO (skala 10 µm)")
img("MAHYDuac98M", px + 359, py + 122, 313, 250, "Citra SEM HD nanopartikel ZnO perbesaran 15.000x (skala 1 µm)")
edx = [(0.525, 0.36, "O Kα"), (1.012, 1.0, "Zn Lα"), (1.74, 0.07, None), (8.63, 0.17, "Zn Kα"), (9.57, 0.05, None)]
for i, (colr, tag) in enumerate([(RED, "Spc_001"), (BLUE, "Spc_002")]):
    ex = px + 24 + i * 334
    X0, T, PW, PH = ex + 62, py + 398, 245, 122
    fx = lambda v: X0 + v / 10 * PW
    axes(X0, T, PW, PH)
    segs([[(fx(v), T + PH), (fx(v), T + PH + 8)] for v in (0, 5, 10)], AXIS, 2)
    for v in (0, 5, 10):
        text(fx(v) - 30, T + PH + 10, 60, str(v), 19, AXIS, align="center", lh=1.2)
    text(ex - 6, T - 6, 64, "50k", 18, AXIS, align="end", lh=1.2)
    segs([[(X0 - 6, T + 6), (X0, T + 6)]], AXIS, 2)
    sc = 1.0 if i == 0 else 0.92
    es = sorted(set([j * 0.05 for j in range(201)] + [c + k * 0.01 for c, a, _ in edx for k in range(-12, 13)]))
    es = [e for e in es if 0 <= e <= 10]

    def edxf(e):
        y = 0.02 * math.exp(-e / 3)
        for c, a, _ in edx:
            y += a * (sc if c > 1.5 else 1) * math.exp(-((e - c) / 0.06) ** 2)
        return y
    segs([[(fx(e), T + PH - min(edxf(e), 1.0) * (PH - 8)) for e in es]], colr, 2.5)
    for c, a, lab in edx:
        if lab:
            yy = T + PH - a * (PH - 8)
            text(fx(c) + 6, yy - 4 if a < 0.9 else yy + 2, 80, lab, 17, colr, bold=True, lh=1.15)
    text(X0 + PW - 98, T, 96, tag, 17, MUTED, align="end", lh=1.15)
    text(X0, T + PH + 34, PW, "Energi (keV)", 19, AXIS, bold=True, align="center", lh=1.15)
caption(px, py, "Gambar 4. Citra SEM dan spektrum EDX nanopartikel ZnO.")

# ---- E: particle size (SEM histogram + DLS)
px, py, pw, ph, _ = PAN["E"]
T, PH = py + 178, 310
# (a) SEM particle-size histogram, lognormal fit (Origin: y0, xc, w, A)
X0, PW = px + 128, 400
fx = lambda d: X0 + (d - 60) / 160 * PW
fy = lambda v: T + PH - v / 25 * PH
text(px + 24, py + 126, 520, "(a) Histogram Ukuran Partikel (SEM)", 26, FOREST_D, bold=True, align="center", lh=1.2)
ticks_y(X0, T, PW, PH, [0, 5, 10, 15, 20, 25], fy, ["0", "5", "10", "15", "20", "25"])
for i, n in enumerate((6, 10, 17, 18, 16, 12, 8, 8, 4, 1)):
    d0 = 60 + 15 * i
    rrect(fx(d0 + 1.2), fy(n), fx(d0 + 13.8) - fx(d0 + 1.2), fy(0) - fy(n), 3, TEAL_L, TEAL_D, 2.5)
axes(X0, T, PW, PH)
ticks_x(T, PH, [60, 100, 140, 180, 220], fx, ["60", "100", "140", "180", "220"])
y0, xc, wl, A = -2.36273, 123.85601, 0.34345, 2003.05891
lgn = lambda d: y0 + A / (math.sqrt(2 * math.pi) * wl * d) * math.exp(-math.log(d / xc) ** 2 / (2 * wl * wl))
segs([[(fx(d), fy(max(lgn(d), 0))) for d in range(60, 221, 4)]], RED, 4)
rrect(X0 + PW - 214, T + 6, 208, 92, 8, WHITE, GRID, 2)
rrect(X0 + PW - 200, T + 20, 34, 22, 3, TEAL_L, TEAL_D, 2)
text(X0 + PW - 156, T + 15, 150, "ZnO (n = 100)", 19, AXIS, lh=1.2)
segs([[(X0 + PW - 200, T + 72), (X0 + PW - 166, T + 72)]], RED, 4)
text(X0 + PW - 156, T + 58, 150, "Fit lognormal", 19, AXIS, lh=1.2)
text(X0, T + PH + 52, PW, "Diameter Partikel (nm)", 24, AXIS, bold=True, align="center", lh=1.2)
rtext(px + 34, T + PH / 2, 200, "Jumlah", 24, AXIS, bold=True)
rrect(X0 + 10, T + PH + 100, PW - 20, 50, 25, TEAL_T)
text(X0 + 10, T + PH + 110, PW - 20, "xc = 123,86 ± 4,66 nm  ·  R² = 0,971", 22, TEAL_D, bold=True, align="center", lh=1.2)

# (b) DLS size distribution by intensity
X0, PW = px + 660, 380
fx = lambda d: X0 + math.log10(d) / 4 * PW
fy = lambda v: T + PH - v / 40 * PH
text(px + 560, py + 126, 520, "(b) Distribusi Intensitas (DLS)", 26, FOREST_D, bold=True, align="center", lh=1.2)
segs([[(fx(d), T), (fx(d), T + PH)] for d in (10, 100, 1000, 10000)], GRID, 2)
ticks_y(X0, T, PW, PH, [0, 10, 20, 30, 40], fy, ["0", "10", "20", "30", "40"])
axes(X0, T, PW, PH)
ticks_x(T, PH, [1, 10, 100, 1000, 10000], fx, ["1", "10", "100", "1000", "10000"], size=22)
minor = [m * 10 ** e for e in range(0, 4) for m in range(2, 10)]
segs([[(fx(d), T + PH), (fx(d), T + PH + 5)] for d in minor], AXIS, 1.5)
segs([[(fx(1), fy(0)), (fx(415), fy(0)), (fx(568), fy(34.8)), (fx(640), fy(32.4)), (fx(865), fy(0)), (fx(10000), fy(0))]], RED, 4)
text(fx(568) - 150, fy(34.8) - 34, 140, "~568 nm", 20, RED, bold=True, align="end", lh=1.2)
text(X0, T + PH + 52, PW, "Size (d.nm)", 24, AXIS, bold=True, align="center", lh=1.2)
rtext(px + 572, T + PH / 2, 300, "Intensity (Percent)", 24, AXIS, bold=True)
segs([[(X0 - 10, T + PH + 127), (X0 + 30, T + PH + 127)]], RED, 4)
text(X0 + 38, T + PH + 112, 400, "Record 46: 0804_Tria Prayoga_ZnO NP 1", 19, AXIS, lh=1.2)

# (c) cumulant results
TX, TW = px + 1080, 326
text(TX, py + 126, TW, "Cumulant Results (n = 3)", 26, TEAL, bold=True, lh=1.2)
TY = py + 180
rrect(TX, TY, TW, 4 * 76, 14, WHITE, TEAL_L, 3)
for i, (a_, b_) in enumerate([("Z-average (nm)", "876,5 ± 83,3"), ("PDI", "0,334 ± 0,138"), ("Pd (nm)", "525,6"), ("%Pd", "64,2")]):
    if i % 2 == 0:
        rrect(TX + 3, TY + 3 + i * 76, TW - 6, 70 + (3 if i == 0 else 0), 10, TEAL_T)
    text(TX + 20, TY + 10 + i * 76, 160, a_, 22, MUTED, lh=1.2)
    text(TX + 20, TY + 36 + i * 76, TW - 40, b_, 28, TEAL_D, bold=True, align="end", lh=1.15)
text(TX, TY + 4 * 76 + 24, TW, "Keterangan:", 23, TEAL_D, bold=True, lh=1.2)
text(TX, TY + 4 * 76 + 58, TW, "Ukuran DLS > SEM: indikasi aglomerasi partikel dalam medium dispersi.", 21, MUTED, lh=1.35)
caption(px, py, "Gambar 5. (a) Histogram ukuran partikel dari citra SEM dengan fit lognormal; (b) distribusi ukuran berdasarkan intensitas (DLS) dan hasil kumulan.", dy=654, w=1381)

cur = shapes
# ================================================================== RIGHT COLUMN
# ---- 6 HASIL UTAMA
section(6, "HASIL UTAMA", RX, 1040, RW, 1230, CT)
y = 1168
IC_X, LB_X, LB_W, DS_X, DS_W = 2414, 2476, 142, 2620, 444


def finding(ic, label, desc, lines):
    global y
    icon(IC_X, y - 4, 50, ic, TEAL)
    text(LB_X, y, LB_W, label, 29, TEAL, bold=True, lh=1.35)
    text(DS_X, y, DS_W, desc, 29, TXT, lh=1.35)
    y += lines * 39.2


def rule():
    global y
    y += 14
    rrect(2414, y, 650, 3, 1, "#CFEAF1")
    y += 22


finding("flask", "LC-MS", "Senyawa dominan dalam ekstrak daun sirih merah:", 2)
y += 10
for name, pct, v in (("5,7-dimethoxyflavone", "36,17%", 36.17), ("apigenin trimethyl ether", "16,90%", 16.90),
                     ("peperphilippinin II", "11,56%", 11.56)):
    text(2476, y, 420, name, 27, TXT, lh=1.25)
    text(2900, y, 164, pct, 27, TEAL_D, bold=True, align="end", lh=1.25)
    rrect(2476, y + 38, 588, 12, 6, TEAL_T)
    rrect(2476, y + 38, 588 * v / 40, 12, 6, TEAL)
    y += 66
rule()
finding("hex", "XRD", "Struktur heksagonal wurtzite (P6₃mc) dengan kristalinitas 89,87% dan ukuran kristalit 30,41 nm.", 4)
rule()
finding("peak", "UV-Vis", "Puncak serapan pada 378,47 nm.", 2)
rule()
finding("wave", "FTIR", "Pita Zn–O pada daerah 400–600 cm⁻¹.", 2)
rule()
finding("mag", "SEM", "Morfologi membulat hingga hampir sferis; ukuran sekitar 60–220 nm; pusat distribusi 123,85 ± 4,66 nm.", 4)
rule()
finding("atom", "EDX", "Unsur dominan Zn dan O.", 1)
rule()
finding("dist", "DLS", "Z-average 876,5 ± 83,3 nm; PDI 0,334 ± 0,138 (n = 3).", 2)

# ---- 7 PEMBAHASAN
section(7, "PEMBAHASAN SINGKAT", RX, 2310, RW, 670, CT)
for yy, ic, s in ((2440, "mol", "Senyawa fenolik dan flavonoid dalam ekstrak daun sirih merah berperan sebagai agen pereduksi dan penstabil nanopartikel ZnO."),
                  (2625, "check", "Hasil karakterisasi mengonfirmasi terbentuknya ZnO dengan struktur wurtzite, kristalinitas tinggi, dan ukuran kristalit pada skala nanometer."),
                  (2810, "cluster", "Ukuran partikel cenderung lebih besar pada DLS yang mengindikasikan adanya aglomerasi dalam medium dispersi.")):
    icon(2414, yy, 58, ic, TEAL)
    text(2488, yy - 2, 576, s, 29, TXT, lh=1.35)

# ---- 8 KEBARUAN
section(8, "KEBARUAN", RX, 3020, RW, 380, CA)
circle(2412, 3166, 116, AMBER_T, AMBER_L, 4)
icon(2422, 3176, 96, "star", AMBER)
text(2550, 3148, 512, "Pemanfaatan ekstrak air daun sirih merah sebagai agen pereduksi dan penstabil untuk sintesis ZnO secara ramah lingkungan dengan karakteristik kristalinitas tinggi.", 29, TXT, lh=1.35)

# ---- 9 POTENSI
section(9, "POTENSI PENGEMBANGAN", RX, 3440, RW, 620, CT)
for yy, ic, s in ((3572, "pill", "Aplikasi sebagai bahan aktif antimikroba, antiinflamasi, dan fotoprotektif dalam sediaan farmasi."),
                  (3746, "flask", "Optimasi formulasi dan uji bioaktivitas lebih lanjut."),
                  (3880, "factory", "Pengembangan ke skala lebih besar dengan pendekatan green chemistry.")):
    icon(2414, yy, 58, ic, TEAL)
    text(2488, yy - 2, 576, s, 29, TXT, lh=1.35)

# ================================================================== CONCLUSION
rrect(90, 4150, 2999, 290, 40, FOREST_D, FOREST_D, 4)
section(10, "KESIMPULAN UTAMA", 90, 4098, 0, 0, CA, pill_w=980)
cnum_locs = ["LBKh4rM2XzchwWpz", "LBhqNHWqFd5CWNCG", "LBhxCjBMl6hST7mW"]
ctext_locs = ["LBlxrnKWxqJrJxJC", "LBS3jW2bp7FnrwyP", "LBRpVzlFVTmSQkFh"]
for i, (s, ic) in enumerate((("Sintesis hijau ZnO berhasil menggunakan ekstrak air daun sirih merah.", "leaf"),
                             ("Struktur kristal wurtzite dan kristalinitas tinggi terkonfirmasi.", "hex"),
                             ("SEM dan DLS menunjukkan kecenderungan aglomerasi partikel.", "cluster"))):
    x0 = 140 + i * 985
    if i:
        rrect(x0 - 40, 4250, 3, 150, 1, "#2F6B45")
    circle(x0, 4278, 92, AMBER, WHITE, 5)
    icon(x0 + 112, 4243, 160, ic, WHITE, fg=FOREST)
    re(cnum_locs[i], str(i + 1), x0, 4300, 92, 48, WHITE, True, "center", 1.0)
    re(ctext_locs[i], s, x0 + 295, 4252, 600, 38, WHITE, True, "start", 1.25)

# ================================================================== HEADER LOGOS (white boxes)
cur = shapes
rrect(130, 36, 300, 300, 34, WHITE, LIME_SOFT, 4)
img("MAHYDp02aL8", 155, 60, 250, 252, "Logo Universitas Pancasila")
rrect(2749, 36, 300, 300, 34, WHITE, LIME_SOFT, 4)
img("MAHYDp3ry3k", 2781, 61, 236, 250, "Logo STIKes IKIFA")

for L in reuse_locs:
    reuse.append({"type": "layer_element", "locator_id": L, "position": "front"})

tops = []
for t in texts:
    op = {"type": "add_text", "page_id": PID, "text": t["text"], "top": t["y"], "left": t["x"], "width": t["w"]}
    if t["rot"]:
        op["rotation"] = t["rot"]
    tops.append(op)

for name, data in (("v2_shapes", shapes), ("v2_charts", charts), ("v2_texts", tops),
                   ("v2_texts_spec", texts), ("v2_reuse", reuse)):
    json.dump(data, open(os.path.join(OUT, name + ".json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("shapes", len(shapes), "charts", len(charts), "texts", len(tops), "reuse", len(reuse), "locs", len(set(reuse_locs)))
for n in ("v2_shapes", "v2_charts", "v2_texts", "v2_reuse"):
    print(n, os.path.getsize(os.path.join(OUT, n + ".json")))
