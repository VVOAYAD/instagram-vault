"""Crop the fallenpoe.t IG screenshot into style refs.
The screenshot has: cover slide at top, then a 3x3 grid of recent posts.
We crop 9 grid tiles + the cover = 10 painted refs.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
SRC = ROOT / "ig-fallenpoet-DXsI4P5kV1N.png"
OUT = ROOT / "style_refs_painted"
OUT.mkdir(exist_ok=True)

img = Image.open(SRC)
W, H = img.size
print(f"Source: {W}x{H}")

# Layout (ratios, derived from visual inspection of the IG profile screenshot):
# cover slide: roughly top-left, x=0..0.34*W, y=0.04*H..0.32*H
# grid header "More posts from..." at ~y=0.36*H
# 3x3 grid: x=0.01..0.99 of W, y=0.38..0.95 of H, with small gutters
#
# We'll be conservative — crop 3x3 cells with small inset to skip gutters and
# avoid the small "carousel" overlay icon in the top-right of each tile.

# 3x3 grid bounds (re-tuned to eliminate neighbor bleed)
GRID_TOP = 0.385
GRID_BOTTOM = 0.928
GRID_LEFT = 0.013
GRID_RIGHT = 0.989

cell_h = (GRID_BOTTOM - GRID_TOP) / 3
cell_w = (GRID_RIGHT - GRID_LEFT) / 3
inset = 0.014  # inner crop to skip cell border / icons / sibling-tile bleed

idx = 1
for row in range(3):
    for col in range(3):
        l = (GRID_LEFT + col * cell_w + inset) * W
        r = (GRID_LEFT + (col + 1) * cell_w - inset) * W
        t = (GRID_TOP + row * cell_h + inset) * H
        b = (GRID_TOP + (row + 1) * cell_h - inset) * H
        crop = img.crop((int(l), int(t), int(r), int(b)))
        out_path = OUT / f"ref_{idx:02d}.png"
        crop.save(out_path)
        print(f"  saved: {out_path} ({crop.size[0]}x{crop.size[1]})")
        idx += 1

# Cover slide (top of screenshot, partially behind popup but bottom half visible)
# crop only the lower portion that's visible: y=0.18..0.32, x=0..0.33
cover_l = int(0.005 * W)
cover_r = int(0.335 * W)
cover_t = int(0.045 * H)
cover_b = int(0.325 * H)
cover_crop = img.crop((cover_l, cover_t, cover_r, cover_b))
cover_path = OUT / f"ref_{idx:02d}_cover.png"
cover_crop.save(cover_path)
print(f"  saved: {cover_path} ({cover_crop.size[0]}x{cover_crop.size[1]})")

print(f"\nTotal: {idx} refs in {OUT}")
