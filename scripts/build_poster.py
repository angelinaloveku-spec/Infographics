import json, math, os

PID = "PBb37h5XYVJp81DH"
OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 3179, 4494

DG, G, LG = "#14532D", "#1F7A3A", "#4CAF50"
MINT, TINT, BORDER = "#F1F8F1", "#E6F4E7", "#B7DDB9"
TXT, MUTED, AXIS, GRID = "#1F2D24", "#4A5E50", "#37474F", "#E3ECE4"
RED, BLUE, WHITE = "#C62828", "#1565C0", "#FFFFFF"

shapes = []      # ops for background/structure (batch 1)
charts = []      # chart shape ops (batch 2)
texts = []       # add_text specs (batch 3)
reuse = []       # reused heading text ops (final batch)
cur = shapes


def r1(v):
    return round(v, 1)


def shape(x, y, w, h, path, vw, vh, color=None, stroke=None, sw=None, opacity=None):
    op = {"type": "insert_shape", "page_id": PID, "top": r1(y), "left": r1(x),
          "width": r1(max(w, 1)), "height": r1(max(h, 1)), "path": path,
          "view_box_width": r1(max(vw, 1)), "view_box_height": r1(max(vh, 1))}
    if color: op["color"] = color
    if stroke: op["stroke_color"] = stroke; op["stroke_weight"] = sw or 2
    if opacity is not None: op["opacity"] = opacity
    cur.append(op)


def rrect(x, y, w, h, r, color=None, stroke=None, sw=None, opacity=None):
    r = min(r, w / 2, h / 2)
    if r <= 0:
        p = f"M0 0H{r1(w)}V{r1(h)}H0Z"
    else:
        p = (f"M{r1(r)} 0H{r1(w-r)}A{r1(r)} {r1(r)} 0 0 1 {r1(w)} {r1(r)}V{r1(h-r)}"
             f"A{r1(r)} {r1(r)} 0 0 1 {r1(w-r)} {r1(h)}H{r1(r)}A{r1(r)} {r1(r)} 0 0 1 0 {r1(h-r)}"
             f"V{r1(r)}A{r1(r)} {r1(r)} 0 0 1 {r1(r)} 0Z")
    shape(x, y, w, h, p, w, h, color, stroke, sw, opacity)


def circle(x, y, d, color=None, stroke=None, sw=None):
    r = d / 2
    p = f"M0 {r1(r)}A{r1(r)} {r1(r)} 0 1 1 {r1(d)} {r1(r)}A{r1(r)} {r1(r)} 0 1 1 0 {r1(r)}Z"
    shape(x, y, d, d, p, d, d, color, stroke, sw)


def segs(segments, stroke, sw, color=None):
    """segments: list of point lists (absolute coords). One shape, multiple subpaths."""
    xs = [p[0] for s in segments for p in s]
    ys = [p[1] for s in segments for p in s]
    mx, my = min(xs), min(ys)
    w, h = max(xs) - mx, max(ys) - my
    if w < 1: mx -= 0.5; w = 1
    if h < 1: my -= 0.5; h = 1
    parts = []
    for s in segments:
        parts.append("M" + " L".join(f"{r1(px-mx)} {r1(py-my)}" for px, py in s))
    shape(mx, my, w, h, " ".join(parts), w, h, color, stroke, sw)


def img(asset, x, y, w, h, alt):
    cur.append({"type": "insert_fill", "page_id": PID, "asset_type": "image", "asset_id": asset,
                "alt_text": alt, "top": r1(y), "left": r1(x), "width": r1(w), "height": r1(h)})


def text(x, y, w, s, size, color=TXT, bold=False, align="start", lh=1.35, italic=False, rot=None):
    t = {"x": r1(x), "y": r1(y), "w": r1(w), "text": s, "size": size, "color": color,
         "bold": bold, "align": align, "lh": lh, "italic": italic, "rot": rot}
    texts.append(t)


def rtext(x, y, w, s, size, color, **kw):
    """Rotated -90 text centred on (x,y) with box length w."""
    hgt = size * kw.get("lh", 1.3)
    text(x - w / 2, y - hgt / 2, w, s, size, color, align="center", rot=-90, **kw)


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


reuse_locs = []

# ---------------------------------------------------------------- HEADER
img("MAHYDaqgrd0", -40, 4180, 640, 320, "Dekorasi daun hijau")          # footer foliage L (behind)
img("MAHYDaqgrd0", 2580, 4180, 640, 320, "Dekorasi daun hijau")         # footer foliage R
shape(0, 0, W, 820, f"M0 0H{W}V770C2500 840 900 720 0 800Z", W, 820, WHITE)
segs([[(0, 800), (900, 722), (1700, 760), (2500, 836), (W, 770)]], LG, 6)  # placeholder line, replaced below
cur.pop()
img("MAHYDTs6Q2g", -70, -70, 860, 860, "Daun sirih merah (Piper porphyrophyllum)")
img("MAHYDaqgXlc", 2370, -40, 860, 860, "Daun hijau dan klaster nanopartikel ZnO")
circle(2860, 560, 210, G, WHITE, 8)
rrect(1395, 448, 390, 8, 4, LG)
rrect(1785, 484, 4, 210, 2, BORDER)
rrect(985, 724, 1210, 64, 32, TINT)

re("LBVfdr3ZrZYxnLsd", "SINTESIS HIJAU DAN KARAKTERISASI\nNANOPARTIKEL SENG OKSIDA (ZnO)", 560, 46, 2060, 92, DG, None, "center", 1.08)
re("LB2PmCqmfDGPzkWt", "MENGGUNAKAN EKSTRAK AIR DAUN SIRIH MERAH", 560, 268, 2060, 58, G, True, "center", 1.2)
re("LBtSxlSVnTm1Pt2q", "(Piper porphyrophyllum)", 560, 348, 2060, 56, G, True, "center", 1.2, italic=True)
re("LB3sYky8LPtsq6Wy", "Tim Peneliti:", 745, 478, 1000, 38, DG, True, "start", 1.2)
re("LB0DLLqGFBmxnCK3", "Prof. Dr. rer. nat. apt. Deni Rahmat, S.Si.\nProf. Dr. apt. Yesi Desmiati, M.Si.\nProf. Dr. apt. Ni Made Dwi Sandhiutami, S.Si., M.Kes.\nTria Prayoga, S.Farm., M.Farm.", 745, 528, 1010, 32, TXT, False, "start", 1.3)
re("LB1yCS23g5tVTr98", "Pendanaan: Hibah BIMA 2026 – Penelitian Disertasi Doktor (PDD)", 985, 736, 1210, 31, DG, True, "center", 1.2)
text(1820, 500, 760, "¹ Fakultas Farmasi,\n   Universitas Pancasila, Jakarta\n² STIKes IKIFA, Jakarta", 32, TXT, lh=1.35)
text(2860, 620, 210, "ZnO", 70, WHITE, bold=True, align="center", lh=1.1)

# ---------------------------------------------------------------- OBJECTIVE BANNER
rrect(90, 832, 2999, 170, 85, WHITE, BORDER, 4)
circle(108, 847, 140, WHITE, G, 5)
img("MAHYDcpUghg", 123, 862, 110, 110, "Ikon bola lampu")
rrect(728, 862, 6, 110, 3, LG)
re("LBMNmvWby1rnNTpj", "Tujuan Utama:", 275, 882, 450, 54, DG, True, "start", 1.2)
text(768, 866, 2290, "Sintesis hijau menggunakan ekstrak air daun sirih merah untuk menghasilkan nanopartikel ZnO berstruktur kristal heksagonal wurtzite dengan kristalinitas tinggi dan ukuran kristalit pada skala nanometer.", 37, TXT, lh=1.35)

# ---------------------------------------------------------------- SECTION HELPERS
num_locs = ["LB39PwTp4smC3qwp", "LBbBK0mYp5ptdY4t", "LBckj9dcRq327yBp", "LBRzG8pz6fLrMxBv",
            "LBszgX5fFtR2qZtV", "LBSSwfXBFxvklc5Q", "LBmZhjdB7gtsXZgr", "LBWyCMbBmHy1PPPv",
            "LBDWMg19WtZcmNnF", "LBLPcrmgz6b22H7S"]
head_locs = ["LBQL8cBDpnc2sB6G", "LBPYCcRWPXVpJT0W", "LBmg6Dmc926Vhqnj", "LBVj9TTjmxhJtzVb",
             "LBq3vP31686L074Y", "LB785vXdyDWFdR1P", "LB6tS7Kg4BmKfXPS", "LBFFzSFTLj1F0wFK",
             "LBvj83nZnGH81ktW", "LBTgLdjlmrGKPb1D"]


def section(n, title, x, y, w, h, pill_w=None):
    if h:
        rrect(x, y, w, h, 32, WHITE, BORDER, 4)
    rrect(x, y, pill_w or w, 104, 32 if h else 52, G)
    circle(x + 12, y - 8, 120, DG, WHITE, 6)
    re(num_locs[n - 1], str(n), x + 12, y + 18, 120, 62, WHITE, None, "center", 1.0)
    re(head_locs[n - 1], title, x + 148, y + 25, (pill_w or w) - 165, 44, WHITE, True, "start", 1.2)


LX, LW = 90, 700
MX, MW = 840, 1499
RX, RW = 2389, 700

# ---------------------------------------------------------------- LEFT COLUMN
section(1, "LATAR BELAKANG", LX, 1040, LW, 640)
text(125, 1168, 632, "Nanopartikel seng oksida (ZnO) memiliki potensi luas dalam bidang farmasi. Sintesis hijau menggunakan ekstrak tumbuhan, seperti daun sirih merah (Piper porphyrophyllum), menawarkan metode ramah lingkungan melalui pemanfaatan senyawa metabolit sekunder sebagai agen pereduksi dan penstabil nanopartikel.", 35, TXT, lh=1.42)

section(2, "TUJUAN PENELITIAN", LX, 1720, LW, 560)
circle(115, 1905, 160, TINT)
img("MAHYDRin93g", 130, 1920, 130, 130, "Ikon target")
text(300, 1850, 462, "Mensintesis nanopartikel ZnO menggunakan ekstrak air daun sirih merah dan mengkarakterisasi sifat optik, struktur kristal, gugus fungsi, morfologi, komposisi unsur, serta ukuran hidrodinamiknya.", 33, TXT, lh=1.42)

section(3, "METODE PENELITIAN", LX, 2320, LW, 1740)
rrect(127, 2470, 6, 1090, 3, LG, opacity=0.55)
for yy in (2448, 3023, 3538):
    circle(110, yy, 40, G, WHITE, 5)
text(170, 2445, 610, "Preparasi Ekstrak Daun Sirih Merah", 32, G, bold=True, lh=1.25)
img("MAHYDQA_zDM", 215, 2500, 495, 330, "Daun sirih merah dan ekstrak air")
text(170, 2845, 590, "Daun sirih merah dicuci, diekstraksi dengan air (50°C, 45 menit), kemudian disaring.", 31, TXT, lh=1.4)
text(170, 3020, 610, "Sintesis Nanopartikel ZnO", 32, G, bold=True, lh=1.25)
img("MAHYDX6GcGA", 255, 3075, 420, 280, "Labu berisi ekstrak dan suspensi ZnO")
text(170, 3370, 590, "Larutan Zn(NO₃)₂ direaksikan dengan ekstrak daun sirih merah, dipanaskan (100°C, 2 jam), lalu dikalsinasi (450°C, 3 jam).", 31, TXT, lh=1.4)
text(170, 3535, 610, "Karakterisasi", 32, G, bold=True, lh=1.25)
img("MAHYDZcwUpk", 265, 3590, 400, 300, "Instrumen karakterisasi")
text(170, 3905, 590, "UV-Vis, XRD, FTIR, SEM-EDX, dan DLS.", 31, TXT, lh=1.4, align="center")

# ---------------------------------------------------------------- MIDDLE: PARAMETER UTAMA
section(4, "PARAMETER UTAMA HASIL", MX, 1040, MW, 600)
tx0, tw, ty, th = 875, 453, 1170, 440
tiles = [("UV-Vis\nλ maks", "378,47", "nm", None),
         ("Kristalinitas\n(XRD)", "89,87%", None, "MAHYDXdZX_M"),
         ("Ukuran Kristalit\n(XRD)", "30,41", "nm", "MAHYDUIG0QA")]
val_locs = ["LB93b4WPYrrlnxR0", "LBNs3StDdMW8ftJH", "LBCwcMR8JBy1slQL"]
lab_locs = ["LB5LXWRCwd8l5Wbc", "LBDXwr85lTsc7P2Y", "LBBb7J20FL0dds42"]
unit_locs = {0: "LBYCRSKhdXc3CvSs", 2: "LBH9XFNDHvXWxVK4"}
for i, (lab, val, unit, icon) in enumerate(tiles):
    x = tx0 + i * (tw + 35)
    rrect(x, ty, tw, th, 28, "#F5FBF5", BORDER, 3)
    circle(x + 26, ty + 28, 136, WHITE, BORDER, 3)
    if icon:
        img(icon, x + 38, ty + 40, 112, 112, "Ikon " + lab.split("\n")[0])
    else:
        pts = []
        for k in range(61):
            u = k / 60
            gx = x + 50 + u * 88
            gy = ty + 140 - 72 * math.exp(-((u - 0.45) / 0.16) ** 2) - 6 * (1 - u)
            pts.append((gx, gy))
        segs([pts], G, 7)
        segs([[(x + 50, ty + 146), (x + 140, ty + 146)]], LG, 4)
    re(lab_locs[i], lab, x + 178, ty + 44, tw - 190, 34, G, True, "start", 1.15)
    re(val_locs[i], val, x, ty + 196, tw, 112, DG, None, "center", 1.0)
    if unit:
        re(unit_locs[i], unit, x, ty + 322, tw, 54, G, True, "center", 1.1)

# ---------------------------------------------------------------- MIDDLE: HASIL KARAKTERISASI
section(5, "HASIL KARAKTERISASI", MX, 1680, MW, 2380)
PAN = {"A": (875, 1815, 697, 700), "B": (1607, 1815, 697, 700),
       "C": (875, 2550, 697, 700), "D": (1607, 2550, 697, 700), "E": (875, 3285, 1429, 740)}
ptitle_locs = {"A": "LB8BZKKfdKtRm6Bw", "B": "LBbs8DqlzkpTlgCz", "C": "LBjKqb02cDjcMFb2",
               "D": "LBR77fdY4sXT8Jmv", "E": "LB1t7BPTMf8YYrmn"}
ptitles = {"A": "UV-Vis", "B": "XRD", "C": "FTIR", "D": "SEM dan EDX", "E": "DLS"}
for k, (px, py, pw, ph) in PAN.items():
    rrect(px, py, pw, ph, 24, WHITE, "#CFE8D1", 3)
    circle(px + 22, py + 22, 70, G)
    text(px + 22, py + 33, 70, k, 38, WHITE, bold=True, align="center", lh=1.1)
    re(ptitle_locs[k], ptitles[k], px + 108, py + 32, pw - 140, 40, DG, True, "start", 1.2)

cur = charts


def axes(X0, T, PW, PH):
    segs([[(X0, T), (X0, T + PH), (X0 + PW, T + PH)]], AXIS, 3)


def ticks_x(X0, T, PW, PH, vals, fx, labels, size=24):
    segs([[(fx(v), T + PH), (fx(v), T + PH + 10)] for v in vals], AXIS, 3)
    for v, lab in zip(vals, labels):
        text(fx(v) - 50, T + PH + 14, 100, lab, size, AXIS, align="center", lh=1.2)


def ticks_y(X0, T, PW, PH, vals, fy, labels, size=24, grid=True):
    if grid:
        segs([[(X0 + 2, fy(v)), (X0 + PW, fy(v))] for v in vals if abs(fy(v) - (T + PH)) > 2], GRID, 2)
    segs([[(X0 - 10, fy(v)), (X0, fy(v))] for v in vals], AXIS, 3)
    for v, lab in zip(vals, labels):
        text(X0 - 112, fy(v) - size * 0.62, 98, lab, size, AXIS, align="end", lh=1.2)


# ---- A: UV-Vis
px, py, pw, ph = PAN["A"]
X0, T, PW, PH = px + 140, py + 140, 520, 350
fx = lambda v: X0 + (v - 300) / 300 * PW
fy = lambda a: T + PH - (a - 0.334) / (0.497 - 0.334) * PH
segs([[(fx(v), T), (fx(v), T + PH)] for v in (400, 500, 600)], GRID, 2)
ticks_y(X0, T, PW, PH, [0.334, 0.350, 0.400, 0.450, 0.497], fy, ["0,334", "0,350", "0,400", "0,450", "0,497"])
axes(X0, T, PW, PH)
ticks_x(X0, T, PW, PH, [300, 400, 500, 600], fx, ["300", "400", "500", "600"])


def uv(l):
    s = 80.0 if l < 378.47 else 92.0
    tail = 0.03 * math.exp(-max(l - 378.47, 0) / 160) if l >= 378.47 else 0.03
    return 0.336 + 0.118 * math.exp(-((l - 378.47) / s) ** 2) + tail


pts = [(fx(l), fy(uv(l))) for l in [300 + i * 3 for i in range(101)]]
segs([pts], "#2E3B33", 5)
pk = (fx(378.47), fy(uv(378.47)))
circle(pk[0] - 9, pk[1] - 9, 18, RED)
segs([[(pk[0], pk[1] - 16), (pk[0], pk[1] - 52)]], RED, 3)
text(pk[0] - 110, pk[1] - 98, 220, "378,47 nm", 28, RED, bold=True, align="center", lh=1.2)
text(X0, T + PH + 52, PW, "Panjang Gelombang (nm)", 26, AXIS, bold=True, align="center", lh=1.2)
rtext(px + 34, T + PH / 2, 200, "Absorbansi", 26, AXIS, bold=True)
text(px + 24, py + 600, pw - 48, "Gambar 1. Spektrum UV-Vis nanopartikel ZnO. Puncak serapan pada 378,47 nm.", 26, MUTED, lh=1.3, italic=True)

# ---- B: XRD
px, py, pw, ph = PAN["B"]
X0, T, PW, PH = px + 90, py + 140, 570, 350
fx = lambda v: X0 + (v - 10) / 80 * PW
base_s = T + 232      # sample baseline
segs([[(fx(v), T), (fx(v), T + PH)] for v in range(20, 91, 10)], GRID, 2)
axes(X0, T, PW, PH)
ticks_x(X0, T, PW, PH, list(range(10, 91, 10)), fx, [str(v) for v in range(10, 91, 10)])
peaks = [(31.77, 0.56), (34.42, 0.42), (36.25, 1.0), (47.54, 0.22), (56.60, 0.32), (62.86, 0.28),
         (66.38, 0.05), (67.96, 0.23), (69.10, 0.11), (72.56, 0.03), (76.95, 0.05), (81.37, 0.02), (89.60, 0.04)]


def xrd(t):
    y = 0.025 + 0.012 * math.exp(-(t - 10) / 25)
    for c, a in peaks:
        y += a / (1 + ((t - c) / 0.17) ** 2)
    y += 0.006 * math.sin(t * 37.1) + 0.004 * math.sin(t * 91.7)
    return y


grid_t = set()
t = 10.0
while t <= 90.0:
    grid_t.add(round(t, 3)); t += 0.4
for c, a in peaks:
    for k in range(-30, 31):
        tt = c + k * 0.05
        if 10 <= tt <= 90: grid_t.add(round(tt, 3))
ts = sorted(grid_t)
pts = [(fx(t), base_s - xrd(t) * 205) for t in ts]
segs([pts], "#1E1E1E", 3)
std = [(31.77, 57), (34.42, 44), (36.25, 100), (47.54, 23), (56.60, 32), (62.86, 29), (66.38, 4),
       (67.96, 23), (69.10, 11), (72.56, 2), (76.95, 4), (81.37, 2), (89.60, 7)]
segs([[(fx(c), T + PH - 1), (fx(c), T + PH - 1 - a * 0.95)] for c, a in std], RED, 4)
for c, lab, dx, al in [(31.77, "31,74° (100)", -158, "end"), (36.25, "36,23° (101)", 10, "start")]:
    yy = base_s - xrd(c) * 205
    text(fx(c) + dx, yy - 8, 150, lab, 22, "#1E1E1E", bold=True, align=al, lh=1.2)
for c, lab in [(47.54, "47,52° (102)"), (56.60, "56,58° (110)")]:
    yy = base_s - xrd(c) * 205
    rtext(fx(c), yy - 12 - 75, 150, lab, 21, "#1E1E1E", bold=True)
segs([[(X0 + PW - 150, T + 28), (X0 + PW - 105, T + 28)]], "#1E1E1E", 4)
text(X0 + PW - 98, T + 12, 100, "ZnO", 24, "#1E1E1E", bold=True, lh=1.2)
text(X0 + 250, T + PH - 112, 310, "ZnO Standard\n(JCPDS No. 79-2205)", 21, RED, bold=True, align="end", lh=1.2)
text(X0, T + PH + 52, PW, "2θ (°)", 26, AXIS, bold=True, align="center", lh=1.2)
rtext(px + 50, T + PH / 2, 260, "Intensitas (a.u.)", 26, AXIS, bold=True)
text(px + 24, py + 600, pw - 48, "Gambar 2. Pola difraksi XRD nanopartikel ZnO dibandingkan standar JCPDS No. 79-2205.", 26, MUTED, lh=1.3, italic=True)

# ---- C: FTIR
px, py, pw, ph = PAN["C"]
X0, T, PW, PH = px + 120, py + 140, 545, 350
fx = lambda v: X0 + (4000 - v) / 3600 * PW
fy = lambda v: T + PH - v / 100 * PH
ticks_y(X0, T, PW, PH, [0, 20, 40, 60, 80, 100], fy, ["0", "20", "40", "60", "80", "100"])
axes(X0, T, PW, PH)
xt = [4000, 3500, 3000, 2500, 2000, 1500, 1000, 500]
ticks_x(X0, T, PW, PH, xt, fx, [str(v) for v in xt], size=21)
dips = [(2340, 7, 28), (1558, 11, 40), (1436, 13, 42), (1118, 8, 30), (877, 6, 18), (618, 5, 16)]


def ftir(v):
    y = 96.5 - 1.2 * (4000 - v) / 3600 + 0.5 * math.sin(v / 37.0)
    for c, d, w in dips:
        y -= d * math.exp(-((v - c) / w) ** 2)
    y -= 84 / (1 + math.exp((v - 548) / 22))
    return y


vs = sorted(set([4000 - i * 25 for i in range(141)] + [c + k * 4 for c, d, w in dips for k in range(-25, 26)]),
            reverse=True)
vs = [v for v in vs if 400 <= v <= 4000]
segs([[(fx(v), fy(ftir(v))) for v in vs]], "#1E1E1E", 3)
for c, dx, row, al in [(2340, -40, 0, "center"), (1558, -82, 0, "end"), (1436, 2, 0, "start"),
                       (1118, -82, 0, "end"), (877, -40, 1, "center"), (618, -10, 0, "start")]:
    yy = fy(ftir(c)) + 10 + row * 38
    text(fx(c) + dx, yy, 80, str(c), 21, "#1E1E1E", bold=True, align=al, lh=1.2)
rrect(X0 + 24, T + PH - 72, 150, 52, 6, WHITE, AXIS, 2)
segs([[(X0 + 38, T + PH - 46), (X0 + 88, T + PH - 46)]], "#1E1E1E", 4)
text(X0 + 96, T + PH - 62, 80, "ZnO", 24, "#1E1E1E", bold=True, lh=1.2)
text(X0, T + PH + 50, PW, "Bilangan Gelombang (cm⁻¹)", 26, AXIS, bold=True, align="center", lh=1.2)
rtext(px + 30, T + PH / 2, 260, "Transmitansi (%)", 26, AXIS, bold=True)
text(px + 24, py + 600, pw - 48, "Gambar 3. Spektrum FTIR nanopartikel ZnO. Pita serapan Zn–O pada 400–600 cm⁻¹.", 26, MUTED, lh=1.3, italic=True)

# ---- D: SEM & EDX
px, py, pw, ph = PAN["D"]
for i, (lab, scale) in enumerate([("Citra SEM 1", "skala 10 µm"), ("Citra SEM 2", "skala 1 µm · 170 nm, 69 nm")]):
    sx = px + 24 + i * 334
    rrect(sx, py + 112, 315, 250, 8, "#3B4240")
    rrect(sx + 14, py + 318, 110, 30, 4, "#111111")
    rrect(sx + 24, py + 330, 60, 6, 2, WHITE)
    text(sx + 10, py + 170, 295, "Tempel " + lab + "\nasli di sini\n(" + scale + ")", 23, WHITE, align="center", lh=1.3)
edx = [(0.525, 0.36, "O Kα"), (1.012, 1.0, "Zn Lα"), (1.74, 0.07, None), (8.63, 0.17, "Zn Kα"), (9.57, 0.05, None)]
for i, (col, tag) in enumerate([(RED, "Spc_001"), (BLUE, "Spc_002")]):
    ex = px + 24 + i * 334
    X0, T, PW, PH = ex + 62, py + 398, 245, 122
    fx = lambda v: X0 + v / 10 * PW
    axes(X0, T, PW, PH)
    segs([[(fx(v), T + PH), (fx(v), T + PH + 8)] for v in (0, 5, 10)], AXIS, 2)
    for v in (0, 5, 10):
        text(fx(v) - 30, T + PH + 10, 60, str(v), 19, AXIS, align="center", lh=1.2)
    text(ex - 6, T - 6, 64, "50k", 18, AXIS, align="end", lh=1.2)
    segs([[(X0 - 6, T + 6), (X0, T + 6)]], AXIS, 2)
    scale = 1.0 if i == 0 else 0.92
    es = sorted(set([j * 0.05 for j in range(201)] + [c + k * 0.01 for c, a, _ in edx for k in range(-12, 13)]))
    es = [e for e in es if 0 <= e <= 10]

    def edxf(e):
        y = 0.02 * math.exp(-e / 3)
        for c, a, _ in edx:
            aa = a * (scale if c > 1.5 else 1)
            y += aa * math.exp(-((e - c) / 0.06) ** 2)
        return y
    segs([[(fx(e), T + PH - min(edxf(e), 1.0) * (PH - 8)) for e in es]], col, 2.5)
    for c, a, lab in edx:
        if lab:
            yy = T + PH - a * (PH - 8)
            text(fx(c) + 6, yy - 4 if a < 0.9 else yy + 2, 80, lab, 17, col, bold=True, lh=1.15)
    text(X0 + PW - 98, T, 96, tag, 17, MUTED, align="end", lh=1.15)
    text(X0, T + PH + 34, PW, "Energi (keV)", 19, AXIS, bold=True, align="center", lh=1.15)
text(px + 24, py + 600, pw - 48, "Gambar 4. Citra SEM dan spektrum EDX nanopartikel ZnO.", 26, MUTED, lh=1.3, italic=True)

# ---- E: DLS
px, py, pw, ph = PAN["E"]
X0, T, PW, PH = px + 140, py + 175, 640, 370
fx = lambda d: X0 + (math.log10(d) + 1) / 5 * PW
fy = lambda v: T + PH - v / 30 * PH
text(X0, py + 118, PW, "Size Distribution by Intensity", 28, DG, bold=True, align="center", lh=1.2)
segs([[(fx(d), T), (fx(d), T + PH)] for d in (1, 10, 100, 1000, 10000)], GRID, 2)
ticks_y(X0, T, PW, PH, [0, 5, 10, 15, 20, 25, 30], fy, ["0", "5", "10", "15", "20", "25", "30"])
axes(X0, T, PW, PH)
dv = [0.1, 1, 10, 100, 1000, 10000]
ticks_x(X0, T, PW, PH, dv, fx, ["0,1", "1", "10", "100", "1000", "10000"])
minor = [m * 10 ** e for e in range(-1, 4) for m in range(2, 10)]
segs([[(fx(d), T + PH), (fx(d), T + PH + 5)] for d in minor], AXIS, 1.5)
mu, sg = math.log10(780), 0.105
ds = [10 ** (-1 + i * 0.02) for i in range(251)]
segs([[(fx(d), fy(24.0 * math.exp(-((math.log10(d) - mu) / sg) ** 2 / 2))) for d in ds]], RED, 4)
text(X0, T + PH + 52, PW, "Size (d.nm)", 26, AXIS, bold=True, align="center", lh=1.2)
rtext(px + 36, T + PH / 2, 300, "Intensity (Percent)", 26, AXIS, bold=True)
segs([[(X0 + 90, T + PH + 112), (X0 + 140, T + PH + 112)]], RED, 4)
text(X0 + 150, T + PH + 96, 480, "Record 46: 0804_Tria Prayoga_ZnO NP 1", 22, AXIS, lh=1.2)
# cumulant table
TX, TY, TW = px + 840, py + 172, 560
text(TX, py + 118, TW, "Cumulant Results (n = 3)", 30, G, bold=True, lh=1.2)
rows = [("Z-average (nm)", "876,5 ± 83,3"), ("PDI", "0,334 ± 0,138"), ("Pd (nm)", "525,6"), ("%Pd", "64,2")]
rrect(TX, TY, TW, 4 * 62, 14, WHITE, BORDER, 3)
for i, (a, b) in enumerate(rows):
    if i % 2 == 0:
        rrect(TX + 3, TY + 3 + i * 62, TW - 6, 56 + (3 if i == 0 else 0), 10, "#EEF7EF")
    text(TX + 22, TY + 14 + i * 62, 300, a, 27, TXT, lh=1.2)
    text(TX + 250, TY + 14 + i * 62, 290, b, 27, DG, bold=True, align="end", lh=1.2)
segs([[(TX + 240, TY + 8), (TX + 240, TY + 4 * 62 - 8)]], BORDER, 2)
text(TX, TY + 4 * 62 + 28, TW, "Keterangan:", 26, DG, bold=True, lh=1.2)
text(TX, TY + 4 * 62 + 66, TW, "Grafik menunjukkan distribusi ukuran partikel berdasarkan intensitas (representatif). Nilai merupakan rata-rata tiga kali pengukuran (n = 3).", 24, MUTED, lh=1.35)
text(px + 24, py + 672, pw - 48, "Gambar 5. Distribusi ukuran partikel berdasarkan intensitas (DLS).", 26, MUTED, lh=1.3, italic=True)

cur = shapes
# ---------------------------------------------------------------- RIGHT COLUMN
section(6, "HASIL UTAMA", RX, 1040, RW, 1260)
y = 1170
LBL_X, LBL_W, D_X, D_W = 2424, 170, 2596, 460


def item(label, desc, lines):
    global y
    text(LBL_X, y, LBL_W, label, 30, G, bold=True, lh=1.35)
    text(D_X, y, D_W, desc, 30, TXT, lh=1.35)
    y += lines * 40.5


def divider():
    global y
    y += 20
    rrect(2424, y, 630, 3, 1, "#DCEEDD")
    y += 24


item("LC-MS:", "senyawa dominan dalam ekstrak daun sirih merah:", 2)
y += 10
for name, pct in [("5,7-dimethoxyflavone", "36,17%"), ("peperphilippinin II", "31,65%"), ("apigenin trimethyl ether", "16,90%")]:
    circle(2444, y + 14, 13, LG)
    text(2470, y, 430, name, 28, TXT, lh=1.3)
    text(2900, y, 154, pct, 28, DG, bold=True, align="end", lh=1.3)
    y += 42
divider()
item("XRD:", "struktur heksagonal wurtzite (P6₃mc) dengan kristalinitas 89,87% dan ukuran kristalit 30,41 nm.", 4)
divider()
item("UV-Vis:", "puncak serapan pada 378,47 nm.", 2)
divider()
item("FTIR:", "pita Zn–O pada daerah 400–600 cm⁻¹.", 2)
divider()
item("SEM:", "morfologi membulat hingga hampir sferis; ukuran sekitar 60–220 nm; pusat distribusi 123,85 ± 4,66 nm.", 4)
divider()
item("EDX:", "unsur dominan Zn dan O.", 1)
divider()
item("DLS:", "Z-average 876,5 ± 83,3 nm; PDI 0,334 ± 0,138 (n = 3).", 2)

section(7, "PEMBAHASAN SINGKAT", RX, 2340, RW, 770)
pts7 = [(2468, "Senyawa fenolik dan flavonoid dalam ekstrak daun sirih merah berperan sebagai agen pereduksi dan penstabil nanopartikel ZnO."),
        (2668, "Hasil karakterisasi mengonfirmasi terbentuknya ZnO dengan struktur wurtzite, kristalinitas tinggi, dan ukuran kristalit pada skala nanometer."),
        (2908, "Ukuran partikel cenderung lebih besar pada DLS yang mengindikasikan adanya aglomerasi dalam medium dispersi.")]
rrect(2438, 2490, 4, 430, 2, LG, opacity=0.5)
for yy, s in pts7:
    circle(2427, yy + 6, 26, G, WHITE, 4)
    text(2474, yy, 582, s, 30, TXT, lh=1.38)

section(8, "KEBARUAN", RX, 3150, RW, 340)
text(2424, 3280, 632, "Pemanfaatan ekstrak air daun sirih merah sebagai agen pereduksi dan penstabil untuk sintesis ZnO secara ramah lingkungan dengan karakteristik kristalinitas tinggi.", 30, TXT, lh=1.38)

section(9, "POTENSI PENGEMBANGAN", RX, 3530, RW, 530)
for yy, s in [(3662, "Aplikasi sebagai bahan aktif antimikroba, antiinflamasi, dan fotoprotektif dalam sediaan farmasi."),
              (3818, "Optimasi formulasi dan uji bioaktivitas lebih lanjut."),
              (3932, "Pengembangan ke skala lebih besar dengan pendekatan green chemistry.")]:
    circle(2430, yy + 13, 16, LG)
    text(2470, yy, 586, s, 30, TXT, lh=1.38)

# ---------------------------------------------------------------- CONCLUSION
rrect(90, 4150, 2999, 290, 40, WHITE, BORDER, 4)
section(10, "KESIMPULAN UTAMA", 90, 4098, 0, 0, pill_w=980)
cnum_locs = ["LBKh4rM2XzchwWpz", "LBhqNHWqFd5CWNCG", "LBhxCjBMl6hST7mW"]
ctext_locs = ["LBlxrnKWxqJrJxJC", "LBS3jW2bp7FnrwyP", "LBRpVzlFVTmSQkFh"]
concl = [("Sintesis hijau ZnO berhasil menggunakan ekstrak air daun sirih merah.", "MAHYDbIi_Bw"),
         ("Struktur kristal wurtzite dan kristalinitas tinggi terkonfirmasi.", "MAHYDXdZX_M"),
         ("SEM dan DLS menunjukkan kecenderungan aglomerasi partikel.", "MAHYDUIG0QA")]
for i, (s, icon) in enumerate(concl):
    x0 = 140 + i * 985
    if i:
        rrect(x0 - 40, 4250, 3, 150, 1, "#DCEEDD")
    circle(x0, 4278, 92, G, WHITE, 5)
    circle(x0 + 112, 4243, 160, TINT)
    img(icon, x0 + 132, 4263, 120, 120, "Ikon kesimpulan " + str(i + 1))
    re(cnum_locs[i], str(i + 1), x0, 4300, 92, 48, WHITE, True, "center", 1.0)
    re(ctext_locs[i], s, x0 + 295, 4252, 600, 38, DG, True, "start", 1.25)

# reused-text front layering
for L in reuse_locs:
    reuse.append({"type": "layer_element", "locator_id": L, "position": "front"})

# text add ops
tops = []
for t in texts:
    op = {"type": "add_text", "page_id": PID, "text": t["text"], "top": t["y"], "left": t["x"], "width": t["w"]}
    if t["rot"]:
        op["rotation"] = t["rot"]
    tops.append(op)

json.dump(shapes, open(f"{OUT}/b_shapes.json", "w"), ensure_ascii=False)
json.dump(charts, open(f"{OUT}/b_charts.json", "w"), ensure_ascii=False)
json.dump(tops, open(f"{OUT}/b_texts.json", "w"), ensure_ascii=False)
json.dump(texts, open(f"{OUT}/texts_spec.json", "w"), ensure_ascii=False)
json.dump(reuse, open(f"{OUT}/b_reuse.json", "w"), ensure_ascii=False)
print("shapes", len(shapes), "charts", len(charts), "texts", len(tops), "reuse", len(reuse), "reuse_locs", len(reuse_locs), len(set(reuse_locs)))
for n in ("b_shapes", "b_charts", "b_texts", "b_reuse"):
    print(n, os.path.getsize(f"{OUT}/{n}.json"))
