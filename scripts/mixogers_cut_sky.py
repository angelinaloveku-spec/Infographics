"""Remove the sky from the refinery photo. Writes an RGBA PNG (sky transparent)."""
import sys
import cv2
import numpy as np

src, out = sys.argv[1], sys.argv[2]
im = cv2.imread(src)[2:]                      # first two rows are a black bar from the screenshot
rows = im.mean(axis=(1, 2))
bot = len(rows)
while bot > 0 and rows[bot - 1] < 45:          # black bar at the bottom of the screenshot
    bot -= 1
im = im[:bot]
H, W = im.shape[:2]
lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
L, A, B = lab[..., 0] * 100 / 255, lab[..., 1] - 128, lab[..., 2] - 128

# smooth sky model: fit L, a, b as quadratic surfaces over confident sky pixels in the upper image
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
xn, yn = xx / W, yy / H
gx = cv2.Sobel(L, cv2.CV_32F, 1, 0, ksize=3)
gy = cv2.Sobel(L, cv2.CV_32F, 0, 1, ksize=3)
grad = cv2.GaussianBlur(np.hypot(gx, gy), (0, 0), 2)
seed = (L > 76) & (B < -4.5) & (grad < 6) & (yn < 0.55)
X = np.stack([np.ones_like(xn), xn, yn, xn * xn, yn * yn, xn * yn], -1)
coef = {}
for name, ch in (("L", L), ("A", A), ("B", B)):
    coef[name], *_ = np.linalg.lstsq(X[seed], ch[seed], rcond=None)
Ls, As, Bs = (X @ coef["L"], X @ coef["A"], X @ coef["B"])
d2 = ((L - Ls) / 4.5) ** 2 + ((A - As) / 2.5) ** 2 + ((B - Bs) / 2.6) ** 2 + (grad / 9) ** 2
sky = np.exp(-d2 / 2)

# GrabCut refinement
m = np.full((H, W), cv2.GC_PR_FGD, np.uint8)
m[sky > 0.35] = cv2.GC_PR_BGD
m[(sky > 0.75) & (yn < 0.5)] = cv2.GC_BGD
m[yn > 0.80] = cv2.GC_FGD
m[(sky < 0.02) & (L < 72)] = cv2.GC_FGD
bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
cv2.grabCut(im, m, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
fg = ((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)).astype(np.uint8)

# drop small floating specks in the sky; keep anything connected to big structures
n, lbl, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
keep = np.zeros(n, bool)
for i in range(1, n):
    x, y, w, h, area = stats[i]
    keep[i] = area > 400 or (y + h) > 0.8 * H
fg = keep[lbl].astype(np.uint8)
# fill tiny sky pinholes inside structures (< 30 px), keep real gaps in lattices
inv = 1 - fg
n2, lbl2, st2, _ = cv2.connectedComponentsWithStats(inv, 4)
for i in range(1, n2):
    if st2[i][4] < 30:
        fg[lbl2 == i] = 1

# clear pure-sky pixels that GrabCut kept inside lattices (colour-only test, upper part of the image)
d2c = ((L - Ls) / 4.5) ** 2 + ((A - As) / 2.5) ** 2 + ((B - Bs) / 2.6) ** 2
fg[(np.exp(-d2c / 2) > 0.35) & (L > 74) & (yn < 0.6)] = 0
# tighten edges by 1 px so the sky does not leave a light halo
fg = cv2.erode(fg, np.ones((3, 3), np.uint8), iterations=1)
alpha = cv2.GaussianBlur(fg.astype(np.float32), (0, 0), 0.8)
# keep the steam as translucent smoke (it also bridges the stack behind it)
box = np.zeros((H, W), np.float32)
box[int(0.22 * H):int(0.45 * H), int(0.43 * W):int(0.58 * W)] = 1
box = cv2.GaussianBlur(box, (0, 0), 12)
steam = np.clip((Ls - L - 2) / 7, 0, 0.85) * box
alpha = np.maximum(alpha, steam)
rgba = np.dstack([im, (alpha * 255).astype(np.uint8)])
cv2.imwrite(out, rgba)
print("sky fraction", 1 - alpha.mean())
