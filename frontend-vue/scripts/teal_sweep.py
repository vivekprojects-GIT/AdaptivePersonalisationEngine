# -*- coding: utf-8 -*-
"""Recolor the brand from Ramp-lime to deep teal. src/ only (node_modules is a
junction to the original — never recurse it)."""
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"

HEX = {
    "#d7f522": "#14b8a6",  # bright lime/cta -> bright teal
    "#a3e635": "#2dd4bf",  # lime-400 -> teal-400
    "#84cc16": "#0d9488",  # lime ring/secondary -> teal-600
    "#bef264": "#5eead4",  # light lime -> teal-300
    "#4d7c0f": "#0f766e",  # deep lime -> deep teal
    "#65a30d": "#0f766e",
    "#f7fee7": "#f0fdfa",  # lime-50 tint -> teal-50
}

total = 0
for f in sorted(list(SRC.rglob("*.vue")) + list(SRC.rglob("*.ts")) + list(SRC.rglob("*.css"))):
    t = f.read_text(encoding="utf-8")
    o = t
    n = 0
    n += t.count("lime-"); t = t.replace("lime-", "teal-")
    for old, new in HEX.items():
        n += t.lower().count(old.lower())
        t = re.sub(re.escape(old), new, t, flags=re.IGNORECASE)
    if t != o:
        f.write_text(t, encoding="utf-8")
        print(f"{f.relative_to(SRC)}: {n}")
        total += n

print("TOTAL", total)
