"""Trace the curves in the HD XRD/FTIR plots into data-space polylines."""
import json
from collections import deque
import numpy as np
from PIL import Image


def largest_component(mask):
    H, W = mask.shape
    seen = np.zeros_like(mask, bool)
    best = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        comp = []
        q = deque([(y0, x0)])
        seen[y0, x0] = True
        while q:
            y, x = q.popleft()
            comp.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
        if len(comp) > len(best):
            best = comp
    out = np.zeros_like(mask, bool)
    for y, x in best:
        out[y, x] = True
    return out


def dilate(m):
    o = m.copy()
    o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
    return o


def trace(mask, full_cols=None):
    """Per-column polyline; full vertical extent only where allowed."""
    pts, prev = [], None
    for x in range(mask.shape[1]):
        ys = np.nonzero(mask[:, x])[0]
        if len(ys) == 0:
            continue
        top, bot = int(ys.min()), int(ys.max())
        if full_cols is not None and not full_cols(x):
            bot = top
        if bot - top <= 6:
            pts.append((x, (top + bot) / 2))
            prev = (top + bot) / 2
        else:
            top, bot = top + 1.5, bot - 1.5   # centre of the ~4 px stroke
            order = (bot, top) if prev is not None and abs(prev - bot) < abs(prev - top) else (top, bot)
            pts += [(x, order[0]), (x, order[1])]
            prev = order[1]
    return pts


out = {}
# FTIR: x 4000 @143.5 -> 500 @805.5 ; y 100 @68.5 -> 0 @579.5
a = np.array(Image.open('assets/ftir_hd.jpg').convert('RGB')).astype(int)
dark = a.sum(axis=2) < 330
sub = dark[46:577, 147:822]
comp = largest_component(sub)
pts = trace(comp, full_cols=lambda x: False)
lastx = max(np.nonzero(comp.any(axis=0))[0])
pts.append((lastx, int(np.nonzero(comp[:, lastx])[0].max())))
out['ftir'] = [(4000 - (x + 147 - 143.5) / 94.571 * 500, 100 - (y + 46 - 68.5) / 5.11) for x, y in pts]

# XRD: x 10 @137.5 -> 90 @903.5
b = np.array(Image.open('assets/xrd_hd.jpg').convert('RGB')).astype(int)
red = (b[:, :, 0] > 150) & (b[:, :, 1] < 120) & (b[:, :, 2] < 120)
blk = (b.sum(axis=2) < 330) & ~red
X0, X1 = 140, 902
t = blk[69:334, X0:X1]
top = largest_component(dilate(t)) & t
# drop the thin label leader lines above the small peaks at ~69.1 and ~89.6 deg
for lo, hi, cap in ((68.6, 69.25, 0.19), (69.25, 70.8, 0.13), (87.0, 90.0, 0.085)):
    c0 = int((lo - 10) / 80 * 766 + 137.5 - X0); c1 = int((hi - 10) / 80 * 766 + 137.5 - X0)
    top[: int((1 - cap) * 265), c0:c1] = False
r = red[372:602, X0:X1]
bot = dilate(dilate(r)) & r
fx = lambda x: 10 + (x + X0 - 137.5) / 766 * 80
out['xrd_sample'] = [(fx(x), 1 - (y) / 265) for x, y in trace(top)]
out['xrd_std'] = [(fx(x), 1 - (y + 34) / 264) for x, y in trace(bot)]
json.dump(out, open('assets/traces.json', 'w'))
for k, v in out.items():
    print(k, len(v), 'x', round(min(p[0] for p in v), 1), round(max(p[0] for p in v), 1),
          'y', round(min(p[1] for p in v), 3), round(max(p[1] for p in v), 3))
