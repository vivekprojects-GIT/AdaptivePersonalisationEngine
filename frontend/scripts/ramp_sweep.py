# -*- coding: utf-8 -*-
"""One-shot sweep: violet/indigo brand classes -> Ramp lime/ink across .vue files.

Order matters:
1. Gradient-text spans (text-transparent bg-clip-text ...) become solid ink
   (Ramp headlines are black, never gradient).
2. Exact text-color classes get readable lime pairs (light + dark variants).
3. Generic stem replacements catch the rest (borders, bgs, shadows, bars)
   while preserving any /alpha suffixes.
"""
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"

GRADIENT_TEXT = re.compile(
    r"text-transparent bg-clip-text bg-gradient-to-\w+ "
    r"from-[\w\[\]./%-]+(?: via-[\w\[\]./%-]+)? to-[\w\[\]./%-]+"
)

EXACT = [
    ("text-violet-300", "text-lime-600 dark:text-lime-300"),
    ("text-violet-400", "text-lime-600 dark:text-lime-300"),
    ("text-violet-500", "text-lime-600 dark:text-lime-400"),
    ("text-indigo-300", "text-lime-600 dark:text-lime-300"),
    ("text-indigo-400", "text-lime-600 dark:text-lime-300"),
]

STEMS = [
    ("violet-300", "lime-300"),
    ("violet-400", "lime-400"),
    ("violet-500", "lime-500"),
    ("violet-600", "lime-600"),
    ("indigo-300", "lime-300"),
    ("indigo-400", "lime-400"),
    ("indigo-500", "lime-500"),
    ("indigo-600", "lime-600"),
]

total = 0
for f in sorted(SRC.rglob("*.vue")):
    text = f.read_text(encoding="utf-8")
    orig = text
    n = 0

    text, k = GRADIENT_TEXT.subn("text-foreground", text)
    n += k

    for old, new in EXACT:
        k = text.count(old)
        text = text.replace(old, new)
        n += k

    for old, new in STEMS:
        k = text.count(old)
        text = text.replace(old, new)
        n += k

    if text != orig:
        f.write_text(text, encoding="utf-8")
        print(f"{f.relative_to(SRC)}: {n} replacements")
        total += n

print(f"TOTAL: {total}")
