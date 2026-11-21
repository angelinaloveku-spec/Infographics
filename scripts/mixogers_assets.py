"""Build the image assets for the MIXOGERS A1 poster (Canva design DAHbeQo7rxg).

Usage: python3 mixogers_assets.py <uploads_dir> <pdf_pages_dir> <pdf_images_dir>
Writes into ../assets/mixogers/.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

UP, PAGES, PDFIMG = sys.argv[1:4]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "mixogers")
os.makedirs(OUT, exist_ok=True)

S = 1.5                      # background pixels per poster pixel
PW, PH = 2245, 3179          # poster size
BW, BH = 3368, 4768          # background size

# Row bands on the poster (poster px)
HERO_END = 800
CREAM_TOP, CREAM_END = 1988, 2418
GREEN_END = 2755
LIGHT_END = 3062


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def vgrad(stops, y0, y1, w):
    """Vertical gradient between poster rows y0..y1 (bg px rows)."""
    a, b = int(y0 * S), int(y1 * S)
    n = b - a
    t = np.linspace(0, 1, n)[:, None]
    pos = [p for p, _ in stops]
    cols = [hexrgb(c) for _, c in stops]
    out = np.zeros((n, 3), np.float32)
    for ch in range(3):
        out[:, ch] = np.interp(t[:, 0], pos, [c[ch] for c in cols])
    return np.repeat(out[:, None, :], w, axis=1)


def radial(img, cx, cy, r, color, strength):
    """Add a soft radial glow (poster coords)."""
    h, w, _ = img.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - cx * S) ** 2 + (yy - cy * S) ** 2) / (r * S)
    a = np.clip(1 - d, 0, 1) ** 2 * strength
    img[:] = img * (1 - a[..., None]) + hexrgb(color) * a[..., None]


# ---------------------------------------------------------------- background
bg = np.zeros((BH, BW, 3), np.float32)

# navy body (hero area is replaced by the photo later)
bg[: int(CREAM_TOP * S)] = vgrad(
    [(0, "#0a1a3d"), (0.35, "#0c1638"), (0.7, "#121334"), (1, "#141233")], 0, CREAM_TOP, BW)

# soft glows in the navy body
body = bg[int(760 * S): int(CREAM_TOP * S)]
radial(body, 120, 560, 900, "#3b1442", 0.45)       # magenta glow left (y relative to 760)
radial(body, 2150, 250, 800, "#16306e", 0.45)      # blue glow right
radial(body, 1122, 1260, 900, "#4a2f3e", 0.55)     # warm glow toward the horizon

# cream band with an arched horizon on top
cream = vgrad([(0, "#fcd6ab"), (0.12, "#fde0bd"), (0.6, "#ffe9d2"), (1, "#fff3e2")],
              CREAM_TOP - 30, CREAM_END, BW)
c0 = int((CREAM_TOP - 30) * S)
bg[c0: int(CREAM_END * S)] = cream
xs = np.arange(BW) / S
edge = CREAM_TOP + 16 * ((xs - PW / 2) / (PW / 2)) ** 2          # arched edge, lower at the sides
yy = np.arange(c0, int(CREAM_END * S))[:, None] / S
above = yy < edge[None, :]
navy_part = vgrad([(0, "#141233"), (1, "#141233")], CREAM_TOP - 30, CREAM_END, BW)
blk = bg[c0: int(CREAM_END * S)]
blk[above] = navy_part[above]
# warm glow just above the horizon
gl = np.zeros_like(blk)
dist = (edge[None, :] - yy)                                         # >0 above edge
glow_a = np.clip(1 - dist / 30, 0, 1) * above * (0.85 - 0.5 * np.abs((xs - PW / 2) / (PW / 2)))[None, :]
blk[:] = blk * (1 - glow_a[..., None]) + hexrgb("#e39a5c") * glow_a[..., None]
# wider, fainter glow further up into the navy
g2 = bg[int((CREAM_TOP - 160) * S): c0]
n2 = g2.shape[0]
a2 = (np.linspace(0, 1, n2) ** 2.2)[:, None] * (0.55 - 0.4 * np.abs((xs - PW / 2) / (PW / 2)))[None, :]
g2[:] = g2 * (1 - a2[..., None]) + hexrgb("#7a4a45") * a2[..., None]

# thin light separator + green band
bg[int(CREAM_END * S): int((CREAM_END + 3) * S)] = hexrgb("#fff8e6")
bg[int((CREAM_END + 3) * S): int(GREEN_END * S)] = vgrad(
    [(0, "#0b3a22"), (0.06, "#0c4228"), (0.5, "#0f432d"), (1, "#10472f")], CREAM_END + 3, GREEN_END, BW)
bg[int(GREEN_END * S): int((GREEN_END + 3) * S)] = hexrgb("#4c7a58")
bg[int((GREEN_END + 3) * S): int(LIGHT_END * S)] = vgrad(
    [(0, "#d3f3d7"), (0.3, "#e0efd3"), (0.7, "#d8eec7"), (1, "#d6ebc8")], GREEN_END + 3, LIGHT_END, BW)
bg[int(LIGHT_END * S):] = vgrad([(0, "#03182b"), (0.2, "#0f2244"), (1, "#0c1e46")], LIGHT_END, PH, BW)

# ---------------------------------------------------------------- hero photo
photo = Image.open(os.path.join(UP, "7915f7e7-image.jpg")).convert("RGB")     # 1200x697
scale = BW * 1.15 / photo.width
ph = photo.resize((int(photo.width * scale), int(photo.height * scale)), Image.LANCZOS)
top = int(14 * scale)
hero_h = int(HERO_END * S)
ph = ph.crop((0, top, BW, top + hero_h))
ph = ImageEnhance.Contrast(ph).enhance(1.12)
ph = ImageEnhance.Color(ph).enhance(0.75)
p = np.asarray(ph).astype(np.float32)
# cool blue duotone blended with the real colours
lum = (0.299 * p[..., 0] + 0.587 * p[..., 1] + 0.114 * p[..., 2])[..., None] / 255
duo = hexrgb("#061433") * (1 - lum) + hexrgb("#9fc0f0") * lum
p = p * 0.5 + duo * 0.5
# darken: strong on the left (title area), lighter on the right
xx = np.linspace(0, 1, BW)[None, :]
t = np.clip((0.66 - xx) / 0.46, 0, 1)
left = t * t * (3 - 2 * t)                              # smoothstep, no visible kink
a = 0.42 + 0.46 * left                                  # 0.88 on left .. 0.42 on right
yv = np.linspace(0, HERO_END, hero_h)[:, None]
navy = hexrgb("#0a1a3d")
p = p * (1 - a[..., None]) + navy * a[..., None]
# top vignette under the white logo plates
tv = np.clip(1 - yv / 160, 0, 1) * 0.25
p = p * (1 - tv[..., None]) + navy * tv[..., None]
# fade into the navy body underneath (blend toward the real body pixels, so no seam)
f = np.clip((yv - 500) / 300, 0, 1)
f = f * f * (3 - 2 * f)
bg[:hero_h] = p * (1 - f[..., None]) + bg[:hero_h] * f[..., None]

bg_img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))
bg_img = bg_img.filter(ImageFilter.GaussianBlur(0.4))
bg_img.save(os.path.join(OUT, "bg_mixogers.jpg"), quality=90)

# ---------------------------------------------------------------- modes graphic (attached image 2)
m = Image.open(os.path.join(UP, "9ec377b7-image.jpg")).convert("RGB")
m = m.resize((m.width * 2, m.height * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 60, 2))
md = ImageDraw.Draw(m)
md.rectangle((1560, 376, 1686, 405), fill="white")                           # drop "Lampiran 3.4"
m = m.crop((0, 14, m.width, m.height))                                       # clipped text strip on top
m.save(os.path.join(OUT, "modes.png"))

# ---------------------------------------------------------------- technical drawing (PDF page 9)
pg = Image.open(os.path.join(PAGES, "p9-009.png")).convert("RGB")
k = pg.width / 1334
d = pg.crop((int(24 * k), int(150 * k), int(598 * k), int(150 * k) + 612))
dd = ImageDraw.Draw(d)
dd.rectangle((985, 310, 1160, 350), fill="white")      # drop the "Lampiran 3.5" link
dd.rectangle((28, 576, 442, 612), fill="white")        # tops of the Indonesian label boxes
dd.rectangle((812, 564, 1228, 612), fill="white")
d.save(os.path.join(OUT, "drawing.png"))

# ---------------------------------------------------------------- documentation photos (PDF page 13)


def crop_to(im, ratio, yfrac=0.5):
    w, h = im.size
    if w / h > ratio:
        nw = int(h * ratio)
        x0 = (w - nw) // 2
        return im.crop((x0, 0, x0 + nw, h))
    nh = int(w / ratio)
    y0 = int((h - nh) * yfrac)
    return im.crop((0, y0, w, y0 + nh))


R = 190 / 116
docs = [("x-013-035", 0.45, "doc_cv.jpg"), ("x-013-036", 0.55, "doc_guns.jpg"),
        ("x-013-040", 0.45, "doc_run.jpg"), ("x-013-067", 0.5, "doc_flame.jpg")]
for src, yf, name in docs:
    im = Image.open(os.path.join(PDFIMG, src + ".png")).convert("RGB")
    im = crop_to(im, R, yf)
    im = im.resize((380, 232), Image.LANCZOS)
    im.save(os.path.join(OUT, name), quality=92)

# certificate + award
Image.open(os.path.join(PDFIMG, "x-016-017.png")).convert("RGB").save(os.path.join(OUT, "copyright_cert.jpg"), quality=92)
Image.open(os.path.join(PDFIMG, "x-017-020.png")).convert("RGB").save(os.path.join(OUT, "award.jpg"), quality=92)

# ---------------------------------------------------------------- plan vs actual S-curve
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

months = ["Dec\n'24", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov\n'25"]
plan = [0, 10, 21, 36, 46, 54, 62, 69, 77, 92, 100, 100]
real = [0, 3, 28, 41, 46, 56, 67, 77, 87, 92, 100, 100]
fam = "Inter" if any("Inter" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": fam})
fig, ax = plt.subplots(figsize=(6.0, 1.9), dpi=200)
fig.patch.set_alpha(0)
ax.set_facecolor("none")
x = range(len(months))
ax.fill_between(x, real, color="#d9560b", alpha=0.10, lw=0)
ax.plot(x, plan, color="#2d6fd6", lw=2.2, marker="o", ms=3.6, label="Plan")
ax.plot(x, real, color="#d9560b", lw=2.6, marker="o", ms=3.8, label="Actual")
for i in (2, 8):
    ax.annotate(f"{real[i]}%", (i, real[i]), textcoords="offset points", xytext=(-4, 6),
                fontsize=7.5, color="#d9560b", fontweight="bold", ha="right")
ax.set_xticks(list(x))
ax.set_xticklabels(months, fontsize=7, color="#7c6a57")
ax.set_yticks([0, 50, 100])
ax.set_yticklabels(["0%", "50%", "100%"], fontsize=7, color="#7c6a57")
ax.set_ylim(-4, 108)
ax.set_xlim(-0.3, 11.3)
ax.grid(axis="y", color="#ebcfa9", lw=0.8)
for s in ax.spines.values():
    s.set_visible(False)
ax.tick_params(length=0, pad=2)
leg = ax.legend(loc="lower right", fontsize=7.5, frameon=False, ncol=2, handlelength=1.6)
for t in leg.get_texts():
    t.set_color("#16213a")
fig.tight_layout(pad=0.2)
fig.savefig(os.path.join(OUT, "scurve.png"), transparent=True)
print("assets written to", os.path.abspath(OUT))
