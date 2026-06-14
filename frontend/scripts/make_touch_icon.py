"""Generate apple-touch-icon.png (180x180) matching the OG-card brand mark:
ink tile on paper, lime outline, lime diamond. Run from frontend-vue/:
python scripts/make_touch_icon.py
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFilter

S = 180
BG = (28, 28, 23)
TILE = (21, 21, 15)
LIME = (20, 184, 166)

out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public", "apple-touch-icon.png"))

img = Image.new("RGB", (S, S), BG)
d = ImageDraw.Draw(img)

# soft lime glow behind the tile
glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([20, 20, S - 20, S - 20], fill=LIME + (55,))
glow = glow.filter(ImageFilter.GaussianBlur(26))
img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
d = ImageDraw.Draw(img)

# tile + three format lines, the middle one lit (matches the app favicon)
d.rounded_rectangle([30, 30, S - 30, S - 30], radius=34, fill=TILE, outline=LIME, width=5)
d.rounded_rectangle([58, 62, 122, 75], radius=6, fill=(244, 244, 236))
d.rounded_rectangle([58, 84, 122, 97], radius=6, fill=LIME)
d.rounded_rectangle([58, 106, 100, 119], radius=6, fill=(107, 107, 94))

img.save(out_path, "PNG")
print("wrote", out_path, img.size)
