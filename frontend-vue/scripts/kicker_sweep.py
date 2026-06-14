# -*- coding: utf-8 -*-
"""Convert the six Home section kickers from pill chips to Ramp-style eyebrows."""
from pathlib import Path

f = Path(__file__).resolve().parents[1] / "src" / "pages" / "Home.vue"
t = f.read_text(encoding="utf-8")

KICKERS = [
    "ChatGPT vs Claude vs an APE app",
    "why teams plug it in",
    "wired into the live engine",
    "the portrait, not a number",
    "engineered with",
    "straight answers",
]

n = 0
for k in KICKERS:
    old = '<span class="ape-chip">%s</span>' % k
    new = '<span class="eyebrow">%s</span>' % k
    n += t.count(old)
    t = t.replace(old, new)

f.write_text(t, encoding="utf-8")
print("converted", n)
