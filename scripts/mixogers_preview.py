"""Render a simulated Canva page (sim.json from mixogers_layout.py) to HTML for a local preview.

Usage: python3 mixogers_preview.py <sim.json> <media_map.json> <out.html>
media_map.json maps Canva media ids to local image paths (missing ids render as grey boxes).
"""
import html
import json
import sys

sim = json.load(open(sys.argv[1]))
media = json.load(open(sys.argv[2]))
FONTS = {"YAFdJvSyp_k": "Inter", "YAFdtQi73Xs": "Inter Display"}
WEIGHT = {"normal": 400, "semibold": 600, "bold": 700, "heavy": 900}


def media_tag(mid, w, h, extra=""):
    p = media.get(mid)
    if p:
        return f'<img src="file://{p}" style="width:{w}px;height:{h}px;object-fit:contain;{extra}">'
    return f'<div style="width:{w}px;height:{h}px;background:#8888;{extra}"></div>'


out = ['<html><head><meta charset="utf-8"><style>body{margin:0}div.e{position:absolute}'
       'ul{margin:0;padding-left:1.25em}p{margin:0}</style></head>'
       '<body><div style="position:relative;width:2245px;height:3179px;overflow:hidden;background:#fff">']
for e in sim:
    t = e["type"]
    base = f'left:{e["left"]}px;top:{e["top"]}px;width:{e["width"]}px;opacity:{e.get("opacity", 1)};'
    if t == "text":
        f = e["textRegions"][0]["formatting"]
        fam = FONTS.get(f["fontRef"].split(",")[0], "Inter")
        txt = "".join(r["characters"] for r in e["textRegions"])
        style = (f'{base}font-family:&quot;{fam}&quot;;font-size:{f["fontSize"]}px;font-weight:{WEIGHT.get(f["fontWeight"], 400)};'
                 f'color:{f["color"]};text-align:{ {"start": "left", "end": "right"}.get(f["textAlign"], f["textAlign"]) };'
                 f'line-height:{f.get("lineHeight", 1.2)};white-space:pre-wrap;')
        if f.get("listLevel", 0) >= 1:
            body = "<ul>" + "".join(f"<li>{html.escape(p)}</li>" for p in txt.split("\n")) + "</ul>"
        else:
            body = html.escape(txt)
        out.append(f'<div class="e" data-id="{e["id"]}" style="{style}">{body}</div>')
    elif t == "rect":
        out.append(f'<div class="e" style="{base}height:{e["height"]}px">'
                   f'{media_tag(e["fill"]["media"]["mediaId"], e["width"], e["height"])}</div>')
    elif t == "shape":
        p0 = e["paths"][0]["fill"]
        if "media" in p0:
            out.append(f'<div class="e" style="{base}height:{e["height"]}px">'
                       f'{media_tag(p0["media"]["mediaId"], e["width"], e["height"])}</div>')
            continue
        vb = e["viewBox"]
        paths = []
        for p in e["paths"]:
            c = p["fill"].get("color", {})
            if c.get("type") == "linear_gradient":
                col, op = c["stops"][-1]["color"], 0.55
            else:
                col, op = c.get("color", "none"), 1
            paths.append(f'<path d="{p["d"]}" fill="{col}" fill-opacity="{op}"/>')
        out.append(f'<svg class="e" style="position:absolute;{base}height:{e["height"]}px" '
                   f'viewBox="{vb["left"]} {vb["top"]} {vb["width"]} {vb["height"]}" preserveAspectRatio="none">'
                   + "".join(paths) + "</svg>")
out.append("</div></body></html>")
open(sys.argv[3], "w").write("\n".join(out))
