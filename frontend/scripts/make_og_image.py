"""Generate the branded Open Graph card (1200x630) for social unfurls.

Run from frontend-vue/:  python scripts/make_og_image.py
Writes public/og.png. Pure Pillow — matches the site's ink-on-paper theme
(#fafaf5 base, lime #d7f522 accent, Segoe UI type).
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1200, 630
BG = (250, 250, 245)
LIME = (20, 184, 166)      # teal-500 (kept the var name; it's the accent fill)
DEEPLIME = (15, 118, 110)  # teal-700, for the headline gradient
FG = (28, 28, 23)
MUTED = (87, 87, 78)

out_path = os.path.join(os.path.dirname(__file__), "..", "public", "og.png")

img = Image.new("RGB", (W, H), BG)

# soft radial glows (lime family only — matches the site's ambient orbs)
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
for cx, cy, r, color, alpha in [
    (980, 110, 420, LIME, 70),
    (140, 560, 380, LIME, 50),
    (620, 320, 520, LIME, 22),
]:
    for i in range(r, 0, -6):
        a = int(alpha * (1 - i / r) ** 2)
        gd.ellipse([cx - i, cy - i, cx + i, cy + i], fill=color + (a,))
glow = glow.filter(ImageFilter.GaussianBlur(60))
img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"), (0, 0))

d = ImageDraw.Draw(img)

# faint dot grid, like the hero background
for gx in range(40, W, 56):
    for gy in range(40, H, 56):
        d.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(208, 208, 198))

FONTS = r"C:\Windows\Fonts"

# autofit the headline: largest size whose longest line fits the safe width
head1, head2 = "Answers that", "take your shape"
size = 120
while size > 40:
    bold = ImageFont.truetype(os.path.join(FONTS, "segoeuib.ttf"), size)
    if max(d.textlength(head1, font=bold), d.textlength(head2, font=bold)) <= W - 144:
        break
    size -= 4
semibold = ImageFont.truetype(os.path.join(FONTS, "seguisb.ttf"), 40)
small = ImageFont.truetype(os.path.join(FONTS, "segoeui.ttf"), 24)

# logo mark — ink tile with three format lines, the middle one lit (matches favicon)
d.rounded_rectangle([72, 76, 136, 140], radius=18, fill=(21, 20, 13))
d.rounded_rectangle([84, 90, 124, 98], radius=4, fill=(244, 244, 236))
d.rounded_rectangle([84, 104, 124, 112], radius=4, fill=LIME)
d.rounded_rectangle([84, 118, 108, 126], radius=4, fill=(107, 107, 94))
d.text((152, 86), "APE", font=ImageFont.truetype(os.path.join(FONTS, "segoeuib.ttf"), 46), fill=FG)

# headline with an ink→deep-lime gradient, applied via mask
y1 = 196
y2 = y1 + int(size * 1.12)
mask = Image.new("L", (W, H), 0)
md = ImageDraw.Draw(mask)
md.text((72, y1), head1, font=bold, fill=255)
md.text((72, y2), head2, font=bold, fill=255)
grad = Image.new("RGB", (W, H), BG)
gdr = ImageDraw.Draw(grad)
for x in range(W):
    t = x / W
    c = tuple(int(FG[i] * (1 - t) + DEEPLIME[i] * t) for i in range(3))
    gdr.line([(x, 0), (x, H)], fill=c)
img.paste(grad, (0, 0), mask)

base = y2 + int(size * 1.25)
d.rectangle([72, base, 560, base + 3], fill=LIME)
d.text((72, base + 22), "APE · The response-format layer", font=semibold, fill=FG)
d.text((72, base + 80), "Learns the format each user prefers, on top of your memory, RAG, or agent stack.",
       font=small, fill=MUTED)

img.save(os.path.abspath(out_path), "PNG")
print("wrote", os.path.abspath(out_path), img.size)
