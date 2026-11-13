"""Extract muscle paths and outlines from react-native-body-highlighter sources into one JSON file.

usage: python -I extract_body.py <source dir> <output json>
"""
import json
import re
import sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])


def parts(name):
    text = (src / name).read_text(encoding="utf-8-sig")
    res = []
    for block in re.split(r"\bslug:\s*", text)[1:]:
        slug = re.match(r'"([^"]+)"', block).group(1)
        for side in ("common", "left", "right"):
            m = re.search(side + r":\s*\[(.*?)\]", block, re.S)
            if not m:
                continue
            for d in re.findall(r'"([^"]+)"', m.group(1)):
                res.append({"slug": slug, "side": side, "d": d})
    return res


def wrapper(name):
    text = (src / name).read_text(encoding="utf-8-sig")
    vb = re.search(r'viewBox\s*=\s*side === "front" \? "([^"]+)" : "([^"]+)"', text)
    outlines = {}
    for side in ("front", "back"):
        m = re.search(r'side === "%s" && \((.*?)\)\}' % side, text, re.S)
        outlines[side] = re.findall(r'\bd="([^"]+)"', m.group(1))
    return {"front": vb.group(1), "back": vb.group(2)}, outlines


data = {
    "source": "https://github.com/HichamELBSI/react-native-body-highlighter",
    "license": "MIT, Copyright (c) 2022 ELABBASSI Hicham",
}
for gender, wrap, front, back in (("male", "components_SvgMaleWrapper.tsx", "assets_bodyFront.ts", "assets_bodyBack.ts"),):
    vb, outlines = wrapper(wrap)
    data[gender] = {
        "front": {"viewBox": vb["front"], "outline": outlines["front"], "parts": parts(front)},
        "back": {"viewBox": vb["back"], "outline": outlines["back"], "parts": parts(back)},
    }
    for side in ("front", "back"):
        v = data[gender][side]
        slugs = sorted({p["slug"] for p in v["parts"]})
        print(gender, side, v["viewBox"], "outline paths:", len(v["outline"]), "parts:", len(v["parts"]), slugs)

out.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
print("wrote", out, out.stat().st_size, "bytes")
