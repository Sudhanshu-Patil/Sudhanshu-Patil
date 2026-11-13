#!/usr/bin/env python3
"""Turn a photo into data/portrait.txt (ASCII rows) for the hero card. Run locally, once.

    python scripts/make_portrait.py photo.png [preview.png]

The photo is not kept in the repo; only the generated text is. CROP and the hint polygons are tuned
for one specific photo: edit them for another. Needs Pillow, numpy and opencv-python-headless.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parents[1] / "data" / "portrait.txt"
CROP = (420, 170, 950, 810)        # speaker, head to above the knees (left, top, right, bottom)
COLS = 120
RAMP = " .`:-=+*cs#%@"             # light -> dark
GAMMA = 1.1
FLOOR = 0.85                       # brighter than this stays blank

rgb = np.asarray(Image.open(sys.argv[1]).convert("RGB").crop(CROP))
h, w = rgb.shape[:2]

# cut the speaker out of the lecture hall: hand-placed hints (crop coordinates), GrabCut does the edges
mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
def poly(pts, val):
    cv2.fillPoly(mask, [np.array(pts, np.int32)], val)
poly([(150, 20), (310, 20), (400, 270), (430, 640), (20, 640), (20, 300)], cv2.GC_PR_FGD)
poly([(320, 0), (530, 0), (530, 440), (418, 440), (418, 270), (325, 240)], cv2.GC_BGD)   # screen and board
poly([(425, 540), (530, 540), (530, 640), (425, 640)], cv2.GC_BGD)
poly([(0, 150), (25, 150), (25, 640), (0, 640)], cv2.GC_BGD)
poly([(180, 50), (270, 50), (285, 160), (230, 190), (175, 130)], cv2.GC_FGD)              # face
poly([(150, 20), (280, 20), (290, 90), (160, 90)], cv2.GC_FGD)                            # hair
poly([(60, 330), (390, 330), (400, 600), (90, 620)], cv2.GC_FGD)                          # torso
poly([(430, 450), (510, 450), (510, 520), (430, 520)], cv2.GC_FGD)                        # hand
bgd, fgd = np.zeros((1, 65)), np.zeros((1, 65))
cv2.grabCut(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), mask, None, bgd, fgd, 8, cv2.GC_INIT_WITH_MASK)
alpha = cv2.GaussianBlur(np.where((mask == 1) | (mask == 3), 1.0, 0.0).astype(np.float32), (0, 0), 1.2)

gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
smooth = cv2.createCLAHE(1.6, (4, 4)).apply(cv2.bilateralFilter(gray, 7, 35, 7))  # local contrast so the face reads
lo, hi = np.percentile(smooth[alpha > 0.5], [2, 88])
tone = np.clip((smooth.astype(np.float32) - lo) / (hi - lo), 0, 1)
tone = 0.3 + 0.7 * tone ** 0.8                                   # keep the navy suit readable, not solid black
fine = cv2.GaussianBlur(smooth, (0, 0), 1.2).astype(np.float32)
coarse = cv2.GaussianBlur(smooth, (0, 0), 5).astype(np.float32)
tone = np.clip(tone - 0.8 * np.clip((coarse - fine) / 30, 0, 1), 0, 1)  # darken thin lines (glasses, smile)
out = (tone * alpha + (1 - alpha))[0:330, 70:370]   # head, shoulders and mic: a full-body face is too small to read
h, w = out.shape

rows = round(COLS * h / w / 1.875)
g = np.asarray(Image.fromarray((out * 255).astype(np.uint8)).resize((COLS, rows), Image.Resampling.LANCZOS), dtype=np.float32) / 255
lines = ["".join(" " if v >= FLOOR else RAMP[max(0, min(len(RAMP) - 1, int((1 - v) * (len(RAMP) - 1) + 0.5)))]
                 for v in r ** GAMMA) for r in g]
OUT.write_text("\n".join(lines), encoding="utf-8")
if len(sys.argv) > 2:
    Image.fromarray((out * 255).astype(np.uint8)).save(sys.argv[2])
print("wrote", OUT, f"{COLS}x{rows}")
