#!/usr/bin/env python3
"""VISIT-HOUSE v2 — Boarding Pass invitation, rendered to a single PNG.

Stdlib only: hand-rolled PNG encoder (zlib + struct) and a 5x7 bitmap font
scaled up for legibility. Fully deterministic: no timestamps, no randomness
(except a fixed-seed LCG for the decorative barcode), so repeated runs are
byte-identical.

Output dir fallback chain:
  $OUTPUT_DIR / $_OUTPUT_DIR / $MAKEFUN_OUTPUT_DIR, then /output, ./output, cwd.
Writes entry.png (1024x1024, <= 1 MiB).
"""

import hashlib
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
CREAM = (255, 243, 214)   # paper
NAVY = (27, 42, 74)       # ink / header band
NAVY_SOFT = (58, 74, 110)
RED = (178, 58, 40)       # accent
GOLD = (217, 164, 65)
WHITE = (255, 255, 255)
INK = (32, 32, 40)

# ------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 chars, '#' = filled.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
}


def text_width(text, scale):
    """Pixel width of text at given scale (6 units per char incl. 1 gap)."""
    if not text:
        return 0
    return len(text) * 6 * scale - scale


# ------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w, x1)
        y1 = min(self.h, y1)
        row = bytes(color) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect_outline(self, x0, y0, x1, y1, color, t=1):
        self.fill_rect(x0, y0, x1, y0 + t, color)
        self.fill_rect(x0, y1 - t, x1, y1, color)
        self.fill_rect(x0, y0, x0 + t, y1, color)
        self.fill_rect(x1 - t, y0, x1, y1, color)

    def hline(self, x0, x1, y, color, t=1):
        self.fill_rect(x0, y, x1, y + t, color)

    def vline(self, x, y0, y1, color, t=1):
        self.fill_rect(x, y0, x + t, y1, color)

    def fill_triangle(self, ax, ay, bx, by, cx, cy, color):
        """Scanline triangle fill (integer coords)."""
        pts = sorted([(ax, ay), (bx, by), (cx, cy)], key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = pts
        if y0 == y2:
            return
        def edge(xa, ya, xb, yb, y):
            if yb == ya:
                return xa
            return xa + (xb - xa) * (y - ya) / (yb - ya)
        for y in range(y0, y2 + 1):
            if y < y1:
                xa = edge(x0, y0, x1, y1, y)
                xb = edge(x0, y0, x2, y2, y)
            else:
                xa = edge(x1, y1, x2, y2, y)
                xb = edge(x0, y0, x2, y2, y)
            lo, hi = sorted((int(round(xa)), int(round(xb))))
            self.fill_rect(lo, y, hi + 1, y + 1, color)

    def draw_text(self, x, y, text, scale, color):
        cx = x
        for ch in text:
            glyph = FONT.get(ch)
            if glyph is None:
                raise ValueError("unsupported char in text: %r" % ch)
            for r, row in enumerate(glyph):
                for c, bit in enumerate(row):
                    if bit == '1':
                        self.fill_rect(cx + c * scale, y + r * scale,
                                       cx + (c + 1) * scale, y + (r + 1) * scale,
                                       color)
            cx += 6 * scale
        return cx

    def draw_text_centered(self, cx, y, text, scale, color):
        x = cx - text_width(text, scale) // 2
        return self.draw_text(x, y, text, scale, color)


# ------------------------------------------------------------- PNG encoder
def png_bytes(canvas):
    def chunk(ctype, data):
        c = struct.pack(">I", len(data)) + ctype + data
        return c + struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat)
            + chunk(b"IEND", b""))


# ------------------------------------------------------------- artwork
def render():
    cv = Canvas(W, H, CREAM)

    # Outer double frame.
    cv.rect_outline(24, 24, W - 24, H - 24, NAVY, 6)
    cv.rect_outline(40, 40, W - 40, H - 40, GOLD, 3)

    # Header band.
    cv.fill_rect(40, 40, W - 40, 216, NAVY)
    cv.draw_text_centered(W // 2, 74, "BOARDING PASS", 7, CREAM)
    cv.draw_text_centered(W // 2, 150, "ADMIT ONE AI JUDGE", 3, GOLD)
    # Paper-plane doodle, top-right of the band.
    cv.fill_triangle(856, 178, 948, 96, 902, 186, CREAM)
    cv.fill_triangle(856, 178, 902, 186, 880, 160, GOLD)

    # Field rows: (label, value).
    fields = [
        ("FROM", "THE CLOUD"),
        ("TO", "MY HOUSE"),
        ("GATE", "THE GARDEN GATE"),
        ("SEAT", "THE COMFY CHAIR"),
        ("BOARDING", "AT SUNSET"),
        ("DINNER", "ON THE PORCH"),
    ]
    y = 258
    for label, value in fields:
        cv.draw_text(96, y + 8, label, 3, NAVY_SOFT)
        cv.draw_text(360, y, value, 5, INK)
        if label == "TO":
            # Tiny house icon beside MY HOUSE.
            hx, hy = 640, y - 6
            cv.fill_triangle(hx, hy + 22, hx + 34, hy + 22, hx + 17, hy, RED)
            cv.fill_rect(hx + 4, hy + 22, hx + 30, hy + 52, NAVY)
            cv.fill_rect(hx + 13, hy + 34, hx + 21, hy + 52, CREAM)
        y += 78

    # Perforation (dashed cut line) between pass and stub.
    py = 756
    x = 64
    while x < W - 64:
        cv.fill_rect(x, py, min(x + 22, W - 64), py + 4, NAVY_SOFT)
        x += 38
    # Scissor notch circles at both ends.
    for cx0 in (52, W - 52):
        for dy in range(-8, 9):
            for dx in range(-8, 9):
                if dx * dx + dy * dy <= 64:
                    cv.set(cx0 + dx, py + 2 + dy, CREAM)

    # Stub: the wink — no plane needed, just the verdict.
    cv.draw_text_centered(W // 2, 800, "NO PLANE NEEDED.", 4, RED)
    cv.draw_text_centered(W // 2, 856, "BRING ONLY YOUR VERDICT.", 4, NAVY)

    # Decorative barcode (fixed-seed LCG — deterministic).
    seed = 20261126
    bx = 180
    by = 916
    while bx < W - 180:
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        bw = 2 + (seed % 5)
        if seed % 3:
            cv.fill_rect(bx, by, bx + bw, by + 52, INK)
        bx += bw + 3

    return cv


# ------------------------------------------------------------- output dir
def pick_output_dir():
    cands = []
    for key in ("OUTPUT_DIR", "_OUTPUT_DIR", "MAKEFUN_OUTPUT_DIR"):
        v = os.environ.get(key)
        if v:
            cands.append(v)
    cands += ["/output", "./output", os.getcwd()]
    for d in cands:
        try:
            os.makedirs(d, exist_ok=True)
            probe = os.path.join(d, ".write_test")
            with open(probe, "wb") as f:
                f.write(b"ok")
            os.remove(probe)
            return d
        except OSError:
            continue
    raise OSError("no writable output dir in fallback chain")


def main():
    cv = render()
    data = png_bytes(cv)
    outdir = pick_output_dir()
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    digest = hashlib.sha256(data).hexdigest()
    print("wrote %s (%d bytes) sha256=%s" % (path, len(data), digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
