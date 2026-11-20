"""Helpers to digitize curves from scanned charts (AFSAM Section 9 figures).

The approach is deliberately simple and auditable:
1. the axes are calibrated from the pixel positions of the chart's own grid lines;
2. for every pixel column, the centres of the dark runs (curve pixels) are found, with the grid-line
   rows / columns masked out;
3. the runs are assigned to curves figure by figure (see digitize_afsam.py);
4. the result is drawn back over the original scan in colour (overlay images) for visual checking.
"""
import numpy as np
from PIL import Image, ImageDraw


class Axis:
    """Pixel <-> value mapping, piecewise linear through the chart's grid lines.

    Axis(p0, v0, p1, v1) for two points, or Axis.grid([(pixel, value), ...]) for every grid line, which
    absorbs small scan distortions.
    """

    def __init__(self, p0, v0, p1, v1):
        self.P = np.array([p0, p1], float)
        self.V = np.array([v0, v1], float)
        self._sort()

    @classmethod
    def grid(cls, pairs):
        a = cls(0, 0, 1, 1)
        a.P = np.array([p for p, v in pairs], float)
        a.V = np.array([v for p, v in pairs], float)
        a._sort()
        return a

    def _sort(self):
        o = np.argsort(self.P)
        self.P, self.V = self.P[o], self.V[o]

    def val(self, p):
        p = np.asarray(p, float)
        return np.interp(p, self.P, self.V, left=None, right=None) if self.P.size > 2 else \
            self.V[0] + (p - self.P[0]) * (self.V[1] - self.V[0]) / (self.P[1] - self.P[0])

    def pix(self, v):
        v = np.asarray(v, float)
        o = np.argsort(self.V)
        if self.P.size > 2:
            return np.interp(v, self.V[o], self.P[o])
        return self.P[0] + (v - self.V[0]) * (self.P[1] - self.P[0]) / (self.V[1] - self.V[0])


def load(path):
    return np.array(Image.open(path).convert("L")).astype(int)


def column_runs(img, x, y_top, y_bot, thr=120, mask_rows=(), min_len=1):
    """Centres of dark runs in column x between y_top and y_bot, skipping masked rows."""
    col = img[y_top:y_bot + 1, x] < thr
    for r in mask_rows:
        if y_top <= r <= y_bot:
            col[r - y_top] = False
    runs, start = [], None
    for i, v in enumerate(col):
        if v and start is None:
            start = i
        if not v and start is not None:
            if i - start >= min_len:
                runs.append((y_top + (start + i - 1) / 2, i - start))
            start = None
    if start is not None:
        runs.append((y_top + (start + len(col) - 1) / 2, len(col) - start))
    return runs


def expand(rows, pad=1):
    out = set()
    for r in rows:
        for k in range(-pad, pad + 1):
            out.add(r + k)
    return sorted(out)


def overlay(path, out, curves, xax, yax, colors=None, dot=1.6, crop=None):
    """Draw digitized curves (list of (label, xs, ys)) over the scan."""
    im = Image.open(path).convert("RGB")
    dr = ImageDraw.Draw(im)
    pal = colors or ["#E00000", "#0070C0", "#00A000", "#C000C0", "#FF8000", "#008080", "#7030A0", "#A05000",
                     "#FF0080", "#0000FF", "#00C0C0", "#808000", "#C00060", "#406000"]
    for i, (lab, xs, ys) in enumerate(curves):
        c = pal[i % len(pal)]
        for x, y in zip(xs, ys):
            if y is None or np.isnan(y):
                continue
            px, py = xax.pix(x), yax.pix(y)
            dr.ellipse((px - dot, py - dot, px + dot, py + dot), fill=c)
    if crop:
        im = im.crop(crop)
    im.save(out)


def despike(xs, ys, win=7, tol=0.03):
    """Drop points that deviate more than tol from the running median (removes text/grid hits)."""
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    keep = np.ones(len(ys), bool)
    for i in range(len(ys)):
        lo, hi = max(0, i - win), min(len(ys), i + win + 1)
        if abs(ys[i] - np.median(ys[lo:hi])) > tol:
            keep[i] = False
    return xs[keep], ys[keep]
