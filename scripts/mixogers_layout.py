"""Generate Canva edit operations for the MIXOGERS A1 poster (design DAHbeQo7rxg).

Input : all_els.json  (element dump of the current page, read via the Canva MCP)
Output: ops.json      (list of edit-design operations, in order)
        sim.json      (simulated element list after the ops, for a local preview)

Usage: python3 mixogers_layout.py <all_els.json> <out_dir>
"""
import copy
import json
import os
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
PID = "PBNSHGvkDnb4tGtH"
ELS = json.load(open(SRC))
BYID = {e["id"]: e for e in ELS}

MEDIA = {
    "bg": "MAHbhmiepTY", "modes": "MAHbhoxiW4w", "drawing": "MAHbhhuDeVk", "scurve": "MAHbhmEOa_g",
    "doc_cv": "MAHbhprc18M", "doc_guns": "MAHbhqP-3SQ", "doc_run": "MAHbhjiYN3Y", "doc_flame": "MAHbhm8ZUkI",
    "cert": "MAHbhm02zRg", "award": "MAHbhlTM7UI",
}

ops = []
handled = set()          # ids whose geometry is set explicitly


def loc(i):
    return f"{PID}-{i}"


def r1(v):
    return round(v, 1)


# ------------------------------------------------------------------ primitives
def pos(i, x, y):
    ops.append({"type": "position_element", "locator_id": loc(i), "top": r1(y), "left": r1(x)})
    handled.add(i)


def move(i, dy, dx=0):
    e = BYID[i]
    pos(i, e["left"] + dx, e["top"] + dy)


def width(i, w):
    ops.append({"type": "resize_element", "locator_id": loc(i), "width": r1(w)})


def scale_img(i, w):
    ops.append({"type": "resize_element", "locator_id": loc(i), "width": r1(w), "preserve_aspect_ratio": True})


def size(i, w, h):
    ops.append({"type": "resize_element", "locator_id": loc(i), "width": r1(w), "height": r1(h)})


def text(i, s):
    ops.append({"type": "replace_text", "locator_id": loc(i), "text": s})


def fmt(i, **f):
    ops.append({"type": "format_text", "locator_id": loc(i), "formatting": f})


def delete(i):
    ops.append({"type": "delete_element", "locator_id": loc(i)})
    handled.add(i)


def front(i):
    ops.append({"type": "layer_element", "locator_id": loc(i), "position": "front"})


def put(i, x, y, w=None, s=None, **f):
    """Repurpose a text element: new text, formatting, width and position."""
    if s is not None:
        text(i, s)
    if f:
        fmt(i, **f)
    if w is not None:
        width(i, w)
    pos(i, x, y)


def shape(x, y, w, h, path, vw, vh, color=None, opacity=None, stroke=None, sw=None):
    op = {"type": "insert_shape", "page_id": PID, "top": r1(y), "left": r1(x), "width": r1(w),
          "height": r1(h), "path": path, "view_box_width": r1(vw), "view_box_height": r1(vh)}
    if color:
        op["color"] = color
    if opacity is not None:
        op["opacity"] = opacity
    if stroke:
        op["stroke_color"] = stroke
        op["stroke_weight"] = sw or 1
    ops.append(op)


def rr_path(x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    return (f"M{r1(x + r)} {r1(y)}H{r1(x + w - r)}A{r1(r)} {r1(r)} 0 0 1 {r1(x + w)} {r1(y + r)}"
            f"V{r1(y + h - r)}A{r1(r)} {r1(r)} 0 0 1 {r1(x + w - r)} {r1(y + h)}H{r1(x + r)}"
            f"A{r1(r)} {r1(r)} 0 0 1 {r1(x)} {r1(y + h - r)}V{r1(y + r)}A{r1(r)} {r1(r)} 0 0 1 {r1(x + r)} {r1(y)}Z")


def rrect(x, y, w, h, r, color, opacity=None):
    shape(x, y, w, h, rr_path(0, 0, w, h, r), w, h, color, opacity)


def multi(rects, color, opacity=None, kind="rr"):
    """One shape made of several sub-paths. rects: (x, y, w, h, r) in page px."""
    x0 = min(r[0] for r in rects)
    y0 = min(r[1] for r in rects)
    x1 = max(r[0] + r[2] for r in rects)
    y1 = max(r[1] + r[3] for r in rects)
    parts = []
    for x, y, w, h, r in rects:
        if kind == "circle":
            rad = w / 2
            cx, cy = x - x0 + rad, y - y0 + rad
            parts.append(f"M{r1(cx - rad)} {r1(cy)}A{r1(rad)} {r1(rad)} 0 1 1 {r1(cx + rad)} {r1(cy)}"
                         f"A{r1(rad)} {r1(rad)} 0 1 1 {r1(cx - rad)} {r1(cy)}Z")
        elif r <= 0:
            parts.append(f"M{r1(x - x0)} {r1(y - y0)}H{r1(x - x0 + w)}V{r1(y - y0 + h)}H{r1(x - x0)}Z")
        else:
            parts.append(rr_path(x - x0, y - y0, w, h, r))
    shape(x0, y0, x1 - x0, y1 - y0, " ".join(parts), x1 - x0, y1 - y0, color, opacity)


def img(key, x, y, w, h, alt):
    ops.append({"type": "insert_fill", "page_id": PID, "asset_type": "image", "asset_id": MEDIA[key],
                "alt_text": alt, "top": r1(y), "left": r1(x), "width": r1(w), "height": r1(h)})


def region(y0, y1, xmin=-1e9, xmax=1e9):
    return [e["id"] for e in ELS if y0 <= e["top"] < y1 and xmin <= e["left"] < xmax and not e.get("isLocked")]


# ================================================================== 0. background
ops.append({"type": "update_fill", "locator_id": loc("LBWCb2pSW6d6Rj0D"), "asset_type": "image",
            "asset_id": MEDIA["bg"], "alt_text": "Poster background: Balongan refinery utilities photo fading into navy, cream, green and light bands"})

# ================================================================== 1. header (compress ~48 px)
put("LBjhyBbQJbwLjtdD", 86, 208, 560, "OUR INNOVATION")
scale_img("LBnr55rgmfVLshzc", 800)
pos("LBnr55rgmfVLshzc", 76, 266)
pos("LBHyq3XsgwR2R8gL", 86, 452)
pos("LB2ZVStsNQ0J7SvP", 568, 453)
pos("LBYRVQSy4tbjM2qG", 607, 459)
scale_img("LBl8cgjKSs0Xb4GQ", 430)
pos("LBl8cgjKSs0Xb4GQ", 1712, 180)

# KPI strip: up 47
for i in region(600, 815):
    if i not in handled:
        move(i, -47)

# ================================================================== 2. row 1 – problem / root cause / risk (up 49)
R1 = -49
put("LBCxfvC1ZvjXhFzP", 86, 882, 724,
    "Boiler F (52-B-101F) supplies high-pressure (HP) steam with a 115 T/h design load. "
    "Its upper and lower burners run on total fuel gas, or in dual firing: one burner on fuel oil, "
    "the other on fuel gas.", font_size=20)
gauge = ["LBghfGYQ3Gfz2BZ9", "LBZyPdVv9f5Lvkk4", "LBv5Yy7kF2vXZbDj", "LBl0GQl8qtFYGkFT", "LBkH4cMzsC2YzFvf",
         "LBNdGWSgYhFD8t4L", "LBtVfTf5gxXvDSGd", "LBWd3BFKMJ8cJ2SP", "LBXgQmyfkwfchHHy", "LBLzx0B7S9ZFjSkp",
         "LBVFZm4drmdb82Xq", "LBWx3vMqHpTTDQ8S", "LBZ8SsTvzJGYG7c4", "LBG6kYpvvrJ2vtLf", "LBc6cwZ4DRTv0ycz",
         "LB7NB3n3DZR3v7Xh", "LBPGW7Kj9cJS0QPS"]
for i in gauge:
    move(i, -50)
for i in ["LBmW6WtT4XQpmjcv", "LBD6Q9QnP9y0vjds", "LB4kH5XgBmtMYF8R", "LBpRhCT7sMdx52wz"]:
    delete(i)
BUL_Y, BUL_P = 1252, 35
put("LBFTlkxWXRQBc3lf", 128, BUL_Y, 700,
    "Meeting NR-023/KPI49210/2024-S2: load stays below 90 T/h\n"
    "Clogged fuel gas burner tips: the gas does not burn well\n"
    "Efficiency (T steam/TSRF) drops in both firing modes\n"
    "No stop to clean the tips: HP steam supply is too tight",
    font_size=19, line_height=round(BUL_P / 19, 3))
for i in region(815, 1440):
    if i not in handled:
        move(i, R1)

# ================================================================== 3. row 2 – solution / options (up 38)
R2 = -38
for i in ["LB3PvJ415hDPKC2m", "LBkMKKLCzwhrwYzQ", "LB8byPpR5JppVnMH", "LBzZB22138ylRqHd", "LBzRp2q54ZNRh6Z1",
          "LBKLF10MskXVFNhR", "LBl6WxDXt9RSpyhz", "LBqzF8LcCVVDGvgw", "LBktnyVKsmN9LDyN", "LBhscmDtcV5g2B3G",
          "LB3w1LRYbY4txjcg", "LBvXxy30YZJV0PNp", "LBnYn8SyysfFsckv", "LBgx52RCLClTSSg4", "LB1QhvlpfX6Yrlw2",
          "LBRBzS7Hm0VrKtK0"]:
    delete(i)
# column A: technical drawing
put("LBsKx0Kf6dSzMd2G", 86, 1527, 554, "MIXING BURNER SCHEME (FO + FG)")
DW_H = 534 * 612 / 1263
put("LBxS5fRkZcbwPCKr", 124, 1836, 516, "Fuel gas line to the upper & lower burners", font_size=17)
put("LBqqS69ptvbMFh0V", 124, 1866, 516, "Fuel oil line to the upper & lower burners", font_size=17)
put("LB6MYYgHmGlyfVLX", 86, 1902, 554,
    "No equipment change, so no MoC needed\n(TKO B04-010/KPI49320/2025-S9)", font_size=17)
# column B: firing modes + method + QA/QC
put("LB1pGS7Pl0cLh66r", 690, 1527, 640, "FIRING MODES & MAX LOAD (PERFORMANCE TEST)", text_align="start")
MD_W = 620
MD_H = MD_W * 438 / 1738
cap_y = 1556 + 6 + MD_H + 10
for i, s, c in [("LBn8kryHLZnzW07H", "93 T/h", 230), ("LBmW73WJsnzQ07zh", "90 T/h", 670), ("LBFxB0Zqdnmkl9sR", "115 T/h", 1410)]:
    cx = 700 + c * MD_W / 1738
    put(i, cx - 80, cap_y, 160, s, font_size=22, text_align="center")
put("LBMVnDPQBfzpPlD2", 690, 1786, 640, "HOW THE METHOD WAS BUILT", text_align="start")
put("LBQlQ0DCQTRrDYyb", 690, 1808, 640,
    "Whole PCP Booster 2.1 team designed the MIXOGERS method\n"
    "Deep-dive on FO + FG readiness: instruments, mechanical\n"
    "New valve scheme: both burners fire oil and gas together",
    font_size=17, line_height=1.4, list_level=1, list_marker="disc")
put("LB0R4CbLgWkCWrnw", 690, 1886, 640, "QA / QC BASIS", font_size=16, color="#93a5c6", text_align="start")
put("LB6RnVJJlkhmY7JL", 690, 1908, 640,
    "TKI C04-063 boiler operation · TKI C03-002 fuel switch · TKO C047-101 mixing burner · "
    "ROP-S-52-1283-102R-E manual · Memo NR-023/KPI49210/2024-S2",
    font_size=16, font_weight="normal", color="#e3eaf6", text_align="start", line_height=1.3)
for i in region(1440, 2040):
    if i not in handled:
        move(i, R2)

# ================================================================== 4. row 3 – plan + implementation (cream band)
R3 = -85
for i in ["LBXfbNGbZk39NPLt", "LBR6wznQry186JHQ", "LB4Y4BQyKsTLBrBl", "LBsGYsk7Xt3TCfWg", "LBKkGN9h4hLBh8xc",
          "LB0P6CD0KqyfZtsr", "LBDCrnLTwVQrKxLf", "LBN1pFHz2Pt8S25l", "LBY034tCzGLWpKDp", "LBtKPtbMP91Ztqhd",
          "LBSzVTd987B4khkr", "LBNsYSqVBd7PZYk9", "LBhYtmxT6R4p8Tq0", "LB95FdzDbKtd6Lj9"]:
    move(i, R3)
put("LB6rC8NTH0Zzs0lT", 86, 2190, 600, "PROGRESS: PLAN VS ACTUAL (DEC 2024 – NOV 2025)")
deletes_r3 = ["LBmL4YXWZ7CX1ndN", "LBxQ1d7Y9T71mHpM", "LBHYjl0fyKnMMrZK",
              "LBDwlCffXTmSyznl", "LBMwMw6DsHybpFtv", "LBvsgb1QRkKgyfyt", "LBT4GrQTgX4P9HB0", "LBZJ4dK3RryVvdrq",
              "LBn7Zh4BDnGNq5vK", "LBlQlZBY95SJdmk1", "LB4nX8LsFhD8pz9c", "LBHxyzjdfmzWg4fY", "LBBhJ97gZsjWTlfB",
              "LBLJ4JgkNZcfJk2d", "LBYwP1tX6vkZLcZS", "LBZBchSlsX0xnZFV", "LBd8NGz3Gm8Gt1tt", "LBW7zFqf4KVnCG6b",
              "LB5W1VBhG9mWVdyL", "LBDyzTTpG67Hr8tP",
              "LBcWYMV82TSWBkSN", "LBSPpbDC90QJKCFV", "LBK4Yjcd1HfCb41C", "LBtfxYdPZfmbL3B3",
              "LB5mmz4jnK9FtCWm", "LBlgbnnzFF0J2ZXn", "LBty7kMLZLfHth2Z",
              "LBG2lqBYZ2T5bvpy", "LBs252X3ptrnbTvj", "LBbLlZsCC5zvfSMh", "LBsvL7Yqvpl8JZsg", "LBnZGb2b1KwWCpl3",
              "LBS3skPPlJ8bH8pR", "LBlnSYWx6d1tbLnZ", "LBHGr8HvR6h04dcK", "LBvNBB6YBpkDgJJM", "LB9KPdwc5Qgx0Sky",
              "LBBPpZyCwtt0Yzhc", "LBFxFMKcyqTVxx6N", "LBH38gyWvwDYCD28",
              "LBQTx9dQt5pgZlNd", "LBxDWnFLVHBsDNRq", "LBYgMLkY8JS1SLkv", "LBNs86zRb517Qd8S", "LBWFgMzLnYn4dGRF",
              "LBMGZXH31VKggpg7", "LBMyw6BRVdwl5rMG", "LB6jbrBztk9FT2Q8", "LBhYgwFY4ZB1Csgb", "LBbZ8ljsrstlB6zX",
              "LBCdtjpGnWtfvwWt", "LBP3Wrv6NtrlrH3R", "LBFgRdnVXBz07wX4"]
for i in deletes_r3:
    delete(i)

# implementation table
T_X = [752, 1100, 1250, 1495]
T_W = [343, 145, 240, 235]
T_HEAD_Y, T_Y, T_P = 2100, 2124, 27
rows = [
    ("Map fuel oil system facilities", "Musonif", "FO control valve too slow", "Re-stroked FO valve"),
    ("Set valve open/close scheme", "DCS (Rizqor)", "Needs 2+ field operators", "Field crew coordinated"),
    ("Write fuel oil operating STK", "DCS (Choirul)", "TKO number still pending", "Followed up with QM"),
    ("Map FO guns & sootblow frequency", "Musonif", "Too few FO burner guns", "Borrowed from UTL OSBL"),
    ("Agree fuel oil use with ECLC", "ECLC (Kumara)", "FO/FG ratio need unclear", "Agreed with OM & ECLC"),
    ("Run FO + FG mixing mode", "Sandra, Yusuf", "Damaged peepholes", "Replaced in stages"),
    ("Monitor Boiler F in mixing mode", "Akbar, Choirul", "Damaged peepholes", "Replaced in stages"),
    ("Evaluate Boiler F load gain", "All", "FO guns swapped more often", "Contractor cleans guns"),
    ("Results meeting", "Fariz", "Not everyone attended", "Sent by email & WhatsApp"),
    ("Share the success story", "ECLC", "Couldn't reach every shift", "M-Team KOMET session"),
]
hdr = [("LBkHTTs7R39k1vqR", "ACTIVITY"), ("LBJF6GXDsZgLSTYK", "PIC"),
       ("LBf8m2FJXXqvftK0", "ISSUE FOUND"), ("LBDJC0t0slqG8L8k", "HOW IT WAS FIXED")]
for k, (i, s) in enumerate(hdr):
    put(i, T_X[k], T_HEAD_Y, T_W[k], s, font_size=14, font_weight="bold",
        color="#3f8a1e" if k == 3 else "#7c6a57", text_align="start")
cols = [("LBRx91K3lvnMVTJh", 16, {}), ("LBySfn0Y1cbkpk3l", 15, {"text_align": "start"}),
        ("LBKXkfvRsxz9kY3w", 15, {}), ("LBLLpkQYtslyD6Cv", 15, {})]
for k, (i, fs, extra) in enumerate(cols):
    put(i, T_X[k], T_Y, T_W[k], "\n".join(r[k] for r in rows), font_size=fs,
        line_height=round(T_P / fs, 4), **extra)
# documentation photos
put("LByQLRSdnz9kn8h4", 1772, T_HEAD_Y, 380, "FIELD DOCUMENTATION", font_size=14, color="#7c6a57", text_align="start")
PH_W, PH_H = 190, 116
ph_xy = [(1772, 2124), (1972, 2124), (1772, 2268), (1972, 2268)]
caps = [("LBwJs0wqcB33WG7H", "Re-stroking the FO valve"), ("LBmqPwCFFxxRGvRq", "Burner gun readiness"),
        ("LByvpVNV4rKdT87p", "Running MIXOGERS"), ("LBgxRqxxbjy1dgJt", "Flame check")]
for (x, y), (i, s) in zip(ph_xy, caps):
    put(i, x, y + PH_H + 3, PH_W, s, font_size=14)

# ================================================================== 5. row 4 – results (green band)
R4 = -23
for i in ["LBJbCprm0wMSZ9h5", "LBlfVZcMbSGsFSHV", "LBKwWdpL6sfJ8pmr"]:
    move(i, R4)
width("LBTZw2Nh37t0VhnW", 200)
move("LBTZw2Nh37t0VhnW", R4)
put("LBfHKSm7sQS0cNTt", 400, 2452, 600,
    "ECLC daily monitoring · Performance test with ECLC, Rotating & Stationary Eng., MA IV and "
    "Process Eng.: 115 T/h", font_size=16)
# parameter table: scale the old table into x 79..1000, y 2515..2745
tb = BYID["LBMPrMC4FNkcD1xh"]
NT_X, NT_Y, NT_W, NT_H = 79, 2513, 921, 232
sx, sy = NT_W / tb["width"], NT_H / tb["height"]
size("LBMPrMC4FNkcD1xh", NT_W, NT_H)
pos("LBMPrMC4FNkcD1xh", NT_X, NT_Y)
tbl_txt = [i for i in region(2545, 2830, xmax=1400) if BYID[i]["type"] == "text"]
for i in tbl_txt:
    e = BYID[i]
    f = e["textRegions"][0]["formatting"]
    nx = NT_X + (e["left"] - tb["left"]) * sx
    ny = NT_Y + (e["top"] - tb["top"]) * sy
    fs = f["fontSize"]
    nfs = {19: 16, 20: 17, 17: 14}.get(int(fs), int(fs) - 3)
    fmt(i, font_size=nfs)
    width(i, e["width"] * sx)
    pos(i, nx, ny + (fs - nfs) * 0.3)

# QCDSM before / target / result
Q_X = 1050
for i, (x, y) in {"LBc58ZJhBxDYL6zj": (Q_X, 2444), "LBSvGtxx9W8qDT9r": (Q_X + 15, 2459),
                  "LBxXf8Mj1mLMc6jC": (Q_X + 82, 2444), "LBQgYKjgxt94d2Jl": (Q_X + 75, 2506)}.items():
    pos(i, x, y)
put("LBdZgLYQttXkbcv3", Q_X + 82, 2467, 1000, "BEFORE VS AFTER (QCDSM)")
QC_X = [1092, 1462, 1772]
QC_W = [358, 298, 380]
QH_Y, Q_Y, Q_P = 2517, 2542, 41
put("LBlfPmThr8FNyycD", QC_X[0], QH_Y, QC_W[0], "BEFORE", font_size=15, font_weight="bold", color="#ffb3ba")
put("LBHnjh3TZ76yc3BR", QC_X[1], QH_Y, QC_W[1], "TARGET (SMART-C)", font_size=15)
put("LBqWj8QQkzqjyqQB", QC_X[2], QH_Y, QC_W[2], "RESULT", font_size=15)
qrows = [
    ("LBNZJncwPkT1qxwr",
     ("LBbnybtc3zZkfLxN", "Load < 90 T/h vs. 115 T/h design; 13.63 / 14.6 T/TSRF"),
     ("LBWjkqTlDC9M5J8m", "Load > 90 T/h; efficiency > 15.50 T/TSRF"),
     ("LBF8qDQQnxFSqptt", "115 T/h capable (runs 90–100 T/h); 15.70 T/TSRF")),
    ("LBc0nwB12Ylgd25G",
     ("LBPQmFWSgP0dxMwr", "Rp1,173,743,259 a year of revenue lost"),
     ("LBdPNpJHkyhYntlc", "Win back Rp1,173,743,259 a year"),
     ("LBQy5PlPLxQh7xw8", "+Rp1,173,743,259 potential (Feb–Dec 2025)")),
    ("LBqcb1Rg8LHBKFty",
     ("LBh3s48znJwTnJ5w", "HP steam header short 25 T/h; 30 min recovery after FO trip"),
     ("LBLKkMnFsWKmkggh", "+25 T/h HP steam; no recovery time"),
     ("LBDC0KvvV7WG3rGf", "+25 T/h HP steam ready; 0 min recovery")),
    ("LBvYmjjqs7rGbzl5",
     ("LBjyzcv6Y0dTLD5L", "53,270.4 t CO₂/yr in dual firing; sooty stack"),
     ("LBtyzmRgvKxT4qgn", "Cut 35,089 t CO₂/yr; soot-free stack"),
     ("LBzdcNYT0Qv2WBPZ", "35,089.6 t CO₂/yr cut; clean stack")),
    ("LBp1f4XLR4072Rq3",
     ("LB2fpTF1xBh7JDcy", "Low confidence: load never reached 115 T/h"),
     ("LBB58HRmg4rsv04V", "Confidence > 97.63%"),
     ("LB1Kb42QdrFV06GH", "Confidence > 97.63%")),
]
qcells = []
for k, (letter, b, t, r) in enumerate(qrows):
    ty = Q_Y + k * Q_P
    pos(letter, 1052, ty + 9)
    put(b[0], QC_X[0], ty + 1, QC_W[0], b[1], font_size=15, font_weight="normal", color="#d8ecdd", line_height=1.25)
    put(t[0], QC_X[1], ty + 1, QC_W[1], t[1], font_size=15, color="#d8ecdd", line_height=1.25)
    put(r[0], QC_X[2], ty + 1, QC_W[2], r[1], font_size=15, color="#ffffff", line_height=1.25)
    qcells += [letter, b[0], t[0], r[0]]
for i in ["LBMjP0xSQ5H1DSDB", "LBpkvbVFLHGBps4D", "LBdwGq0Gn3wyM2ZM", "LBbwp8NNDz7mMdT2", "LBxkZMc0xGNTz13K",
          "LB2VzCZHL5lgt1YR", "LBmfCY4SVhr73Skt", "LB9fQFhDD673FSZh", "LBXTdyY0HLBXS8Dk", "LB4vhj38J7hkr8rx",
          "LBpDlwyQQzNMm9bx", "LBvZlrQj08KLLtcp"]:
    delete(i)

# ================================================================== 6. row 5 – standard & patent / sustainability / market
R5Y = 2765
for i in ["LBsKKYH6rN02ypQn", "LB3tk0yNsm9jLrZw",
          "LBFNZGM5DZkVfSmg", "LBJ008f544bfbsb3", "LBXJp2Fxm9dWpzXh", "LB2MkkxCHFlSDJCB", "LBF20sX2GG6CP6Wn",
          "LBY3z3V98Q38YqxR", "LBsrsGCVHLLfSwBn", "LB6DH64vSF720hDR", "LBn10h1ckZfK6NSD", "LBlKsVL9kWMN3lZJ",
          "LBpKW0X4dcLfDZDt", "LBM6F4s00PN4KWYG", "LBdBrTt72HJkTJhZ", "LBZS4XGWSmDZSmk4", "LBQls1XybSLx29pY",
          "LBHtZFTH5HtQHLLX",
          "LBfBrFnlvQk9l3ln", "LBCBhDkGg6G1MTNP", "LB3qGCQZ8hpkLJZY", "LBqM45jTh2nMtG6V", "LBmVTx2PCBGVdn4W",
          "LB8rMJghzxFFqHpf", "LB2x7jFkLS8k1P2T", "LBXJM0SblctvF9bT", "LBSRpwK93sqWFx2h", "LBlGR15YZJZNDcYG",
          "LBwDKRlQCWcdxrJJ"]:
    delete(i)
COLS = [(86, 654), (780, 660), (1480, 680)]
CARD_Y, CARD_H = 2846, 206
# col 1
pos("LBM7Km9RSR8xM71l", 86, R5Y)
pos("LBN2sCP4GFYB1C8J", 178, R5Y + 12)
put("LBjXQjg39sPhY1Bx", 178, R5Y + 31, 540, "STANDARD & PATENT")
pos("LBlzNX8v84n1hdHv", 171, R5Y + 62)
put("LBGXdVw00wNQvQ45", 106, 2858, 480, "STANDARD (STK)", font_size=14)
put("LBX0KHzTfKqRHxjG", 106, 2879, 500,
    "TKI C04-063/KPI149121/2025-S9 · Boiler operation\n"
    "TKI C03-002/KPI49121/2021-S9 · Gas-to-oil fuel switch\n"
    "TKO C047-101/KPI149121/2025-S9 · Mixing FO & FG burner\n"
    "ROP-S-52-1283-102R-E · Boiler F operating manual",
    font_size=15, line_height=1.42)
put("LBcWsBsmqHtdcv6w", 106, 2972, 480, "PATENT & COPYRIGHT", font_size=14)
put("LBbySkyg87KdQ45G", 106, 2993, 500,
    "HAKI & WIPO Patentscope search: no matching name or method\n"
    "Copyright registered: EC002026237899 (Kemenkumham)",
    font_size=15, line_height=1.42)
# col 2
pos("LBT4ssNyqyF9Wnxz", 780, R5Y)
pos("LBgCMjgQ7t3px1th", 872, R5Y + 12)
pos("LB1QHW8pLjFcdq2T", 872, R5Y + 31)
pos("LBG3fhLXTJbQjyDP", 865, R5Y + 62)
put("LBV3BhT5HH70t1Zt", 800, 2858, 500,
    "BOC checks of flame pattern and radiant tubes\n"
    "Sootblowing twice a day\n"
    "New fuel oil burner guns bought (WAM UTL)\n"
    "APC on: efficiency up to 17.19 T/TSRF\n"
    "ECLC memo 124/KPI49230/2025-S2\n"
    "Shared via KOMET, CoP and UNS journal\n"
    "Forum IDEA 2026 delegate\n"
    "Supports Pertamina Net Zero 2060",
    font_size=15, line_height=1.38, list_level=1, list_marker="disc")
put("LBVd6mQNmtFgVJQN", 1302, 3002, 132, "Best Decarbonization Program 2025",
    font_size=12, font_weight="bold", color="#3f8a1e", text_align="center", line_height=1.15)
# col 3
put("LBTW3Q6jHSWgwswr", 1480, R5Y, 110, "09", font_size=58, color="#3f8a1e", text_align="start")
put("LBKWtNKFGYcbKPXb", 1572, R5Y + 12, 300, "POTENTIAL", font_size=15, color="#2d6fd6")
put("LByxxTt4kfWt4ypD", 1572, R5Y + 31, 590, "MARKET & BUSINESS FEASIBILITY",
    font_size=27, font_weight="bold", color="#0b1f45", text_align="start")
put("LBgjrXtnGHgKx39w", 1500, 2850, 290, "Rp1.25 b*", font_size=46, color="#d9560b")
put("LBzRFWYVtTD281XS", 1500, 2908, 285,
    "value of technology transfer in a detailed engineering design (DED) project",
    font_size=14, text_align="start", line_height=1.2)
put("LB8Fcxg8pjCXdbwM", 1500, 2968, 285, "MARKET", font_size=13)
put("LBrZSCXydq73kWC3", 1500, 2986, 285,
    "Retrofit refinery & petrochemical boilers to fire fuel oil and fuel gas together",
    font_size=14, text_align="start", line_height=1.2)
put("LBJ0JZX1V0nrnrx1", 1810, 2858, 335, "WHO CAN ADOPT IT", font_size=13)
put("LBlpm9HyHTjcn70w", 1810, 2877, 335,
    "EPC firms in boiler & burner modification or retrofit\n"
    "EPC firms in fired heater & boiler performance\n"
    "Engineering & service firms in combustion, burner tuning and emission cuts\n"
    "Replicable at KPI Units II–VII, power plants, petrochemicals",
    font_size=14, line_height=1.3, list_level=1, list_marker="disc")
put("LBF7SrcQ5ZchgNSh", 1810, 3032, 335, "*Commercial feasibility study by Sulzer", font_size=12)

# ================================================================== 7. new shapes
# problem bullets
dots = [(86, BUL_Y + BUL_P * k + BUL_P / 2 - 13, 26, 26, 0) for k in range(4)]
multi(dots, "#ff7a1a", kind="circle")
multi([(x + 8, y + 8, 10, 10, 0) for x, y, _, _, _ in dots], "#0b1f45", kind="circle")
# solution cards + legend swatches
rrect(86, 1556, 554, DW_H + 12, 14, "#ffffff")
rrect(690, 1556, 640, MD_H + 12, 14, "#ffffff")
rrect(86, 1836 + 8, 26, 5, 2.5, "#3d8bff")
rrect(86, 1866 + 8, 26, 5, 2.5, "#ff5964")
# implementation table rules
multi([(T_X[0], T_Y + T_P * k - 1, T_X[3] + T_W[3] - T_X[0], 1.5, 0) for k in range(11)], "#e4c39a")
# QCDSM stripes + letter circles
multi([(Q_X - 4, Q_Y + Q_P * k - 2, 2164 - Q_X, Q_P - 3, 8) for k in (0, 2, 4)], "#2a6a4c", opacity=0.75)
multi([(1052, Q_Y + Q_P * k + 5, 28, 28, 0) for k in range(5)], "#c2e05a", kind="circle")
# row 5 cards + underline for col 3
for x, w in COLS:
    rrect(x, CARD_Y, w, CARD_H, 16, "#ffffff", opacity=0.82)
ul = BYID["LBlzNX8v84n1hdHv"]
shape(1565, R5Y + 62, ul["width"], ul["height"],
      " ".join(p["d"] for p in ul["paths"][:1]), ul["viewBox"]["width"], ul["viewBox"]["height"], "#ff7a1a")
shape(1565, R5Y + 62, ul["width"], ul["height"],
      " ".join(p["d"] for p in ul["paths"][1:]), ul["viewBox"]["width"], ul["viewBox"]["height"], "#3d8bff")

# ================================================================== 8. bring text above the new shapes
for i in [c[0] for c in cols] + qcells + [
        "LBGXdVw00wNQvQ45", "LBX0KHzTfKqRHxjG", "LBcWsBsmqHtdcv6w", "LBbySkyg87KdQ45G", "LBV3BhT5HH70t1Zt",
        "LBVd6mQNmtFgVJQN", "LBgjrXtnGHgKx39w", "LBzRFWYVtTD281XS", "LB8Fcxg8pjCXdbwM", "LBrZSCXydq73kWC3",
        "LBJ0JZX1V0nrnrx1", "LBlpm9HyHTjcn70w", "LBF7SrcQ5ZchgNSh"]:
    front(i)

# ================================================================== 9. images (inserted last, on top)
img("drawing", 96, 1562, 534, DW_H, "Mixing burner scheme: fuel gas (blue) and fuel oil (red) lines to the upper and lower burners")
img("modes", 700, 1562, MD_W, MD_H, "Dual firing and total fuel gas modes compared with the MIXOGERS mixed FO/FG mode")
img("scurve", 86, 2213, 600, 190, "Plan vs actual cumulative progress, Dec 2024 to Nov 2025")
for (x, y), key, alt in zip(ph_xy, ["doc_cv", "doc_guns", "doc_run", "doc_flame"],
                            ["Re-stroking the fuel oil control valve", "Fuel oil burner guns ready",
                             "Operator running the MIXOGERS valve scheme", "Burner flame seen through the peephole"]):
    img(key, x, y, PH_W, PH_H, alt)
img("cert", 622, 2858, 104, 104 * 852 / 601, "Copyright registration certificate EC002026237899")
img("award", 1316, 2858, 104, 104 * 691 / 508, "Sustainability Awards 2025, Best Decarbonization Program trophy")

# ================================================================== 10. alignment nudges
# Canva top-aligns each line inside its line-height, so centre rows on their dots / rules / stripes.
pos("LBFTlkxWXRQBc3lf", 128, BUL_Y + 6)
pos("LBRx91K3lvnMVTJh", T_X[0], T_Y + 3.6)
for k in (1, 2, 3):
    pos(cols[k][0], T_X[k], T_Y + 4.2)
two_line = {"LBbnybtc3zZkfLxN", "LBh3s48znJwTnJ5w"}
for k, (_, b, t, r) in enumerate(qrows):
    ty = Q_Y + k * Q_P
    for (i, _), x in zip((b, t, r), QC_X):
        pos(i, x, ty + (0.4 if i in two_line else 9.4))

# ================================================================== check + write
unhandled_regions = [i for i in region(2040, 3068) if i not in handled]
missing = [i for i in unhandled_regions]
if missing:
    print("WARNING unhandled elements in rows 3-5:", missing)
os.makedirs(OUT, exist_ok=True)
json.dump(ops, open(os.path.join(OUT, "ops.json"), "w"), ensure_ascii=False, indent=0)
print(len(ops), "ops")


# ------------------------------------------------------------------ simulate for preview
def simulate():
    els = [copy.deepcopy(e) for e in ELS]
    by = {e["id"]: e for e in els}
    n = 0
    for op in ops:
        t = op["type"]
        i = op.get("locator_id", "").split("-")[-1]
        e = by.get(i)
        if t == "update_fill":
            e["paths"][0]["fill"]["media"]["mediaId"] = op["asset_id"]
        elif t == "position_element":
            e["top"], e["left"] = op["top"], op["left"]
        elif t == "resize_element":
            if e["type"] == "text":
                e["width"] = op["width"]
            elif op.get("preserve_aspect_ratio"):
                e["height"] = e["height"] * op["width"] / e["width"]
                e["width"] = op["width"]
            else:
                e["width"], e["height"] = op["width"], op["height"]
        elif t == "replace_text":
            e["textRegions"] = [{"characters": op["text"], "formatting": dict(e["textRegions"][0]["formatting"])}]
        elif t == "format_text":
            f = e["textRegions"][0]["formatting"]
            m = op["formatting"]
            for a, b in [("font_size", "fontSize"), ("font_weight", "fontWeight"), ("color", "color"),
                         ("line_height", "lineHeight"), ("text_align", "textAlign"), ("list_level", "listLevel"),
                         ("list_marker", "listMarker")]:
                if a in m:
                    f[b] = m[a]
        elif t == "delete_element":
            els.remove(e)
            del by[i]
        elif t == "layer_element":
            els.remove(e)
            els.append(e)
        elif t == "insert_shape":
            n += 1
            ne = {"id": f"NEW{n}", "type": "shape", "top": op["top"], "left": op["left"], "width": op["width"],
                  "height": op["height"], "opacity": op.get("opacity", 1),
                  "viewBox": {"top": 0, "left": 0, "width": op["view_box_width"], "height": op["view_box_height"]},
                  "paths": [{"d": op["path"], "fill": {"color": {"type": "solid", "color": op.get("color", "#000000")}}}]}
            els.append(ne)
        elif t == "insert_fill":
            n += 1
            els.append({"id": f"NEW{n}", "type": "rect", "top": op["top"], "left": op["left"], "width": op["width"],
                        "height": op["height"], "fill": {"media": {"mediaId": op["asset_id"]}}})
    return els


json.dump(simulate(), open(os.path.join(OUT, "sim.json"), "w"), ensure_ascii=False)
print("simulation written")
