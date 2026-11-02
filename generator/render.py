"""Isometric PNG preview renderer (painter's algorithm over visible voxels)."""
import numpy as np
from PIL import Image, ImageDraw

from blocks import AIR, REG, SHAPES

SHADE_TOP, SHADE_X, SHADE_Z = 1.0, 0.80, 0.64


def _jit(x, y, z):
    h = (x * 73856093) ^ (y * 19349663) ^ (z * 83492791)
    return 0.94 + ((h & 0xFF) / 255.0) * 0.12


def _col(rgb, f):
    return tuple(max(0, min(255, int(c * f))) for c in rgb)


def render(a, path, spawns=(), a_px=8, vscale=1.2, pad=20, bbox=False, crop=True):
    W, H, L = a.shape
    full = np.array([REG[i].full if i else False for i in range(len(REG))])
    fa = full[a]

    def proj(X, Y, Z):
        return ((X - Z) * a_px, (X + Z) * a_px / 2.0 - Y * a_px * vscale)

    # canvas bounds
    xs, ys = [], []
    for X in (0, W):
        for Y in (0, H):
            for Z in (0, L):
                sx, sy = proj(X, Y, Z)
                xs.append(sx)
                ys.append(sy)
    ox, oy = -min(xs) + pad, -min(ys) + pad
    img = Image.new("RGBA", (int(max(xs) - min(xs) + 2 * pad), int(max(ys) - min(ys) + 2 * pad)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def P(X, Y, Z):
        sx, sy = proj(X, Y, Z)
        return (sx + ox, sy + oy)

    def box_line(p0, p1, color, width=1, dash=6):
        x0, y0 = P(*p0)
        x1, y1 = P(*p1)
        n = max(1, int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / dash))
        for i in range(0, n, 2):
            t0, t1 = i / n, min(1.0, (i + 1) / n)
            d.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0), (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)],
                   fill=color, width=width)

    corners = [(0, 0, 0), (W, 0, 0), (W, 0, L), (0, 0, L), (0, H, 0), (W, H, 0), (W, H, L), (0, H, L)]
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
    back = {(0, 1), (3, 0), (0, 4)}  # edges touching the far corner (0,0,0)
    if bbox:
        for e in edges:
            if e in back:
                box_line(corners[e[0]], corners[e[1]], (120, 140, 160, 90))

    occ = np.zeros((W + 1, H + 1, L + 1), bool)
    occ[:W, :H, :L] = fa
    a = a.copy()
    if not bbox:
        a[0, 0, 0] = AIR
        a[W - 1, H - 1, L - 1] = AIR
    nzs = np.argwhere(a != AIR)
    order = np.argsort(nzs.sum(axis=1), kind="stable")
    for k in order:
        x, y, z = (int(v) for v in nzs[k])
        b = REG[int(a[x, y, z])]
        if b.full:
            top_vis = not occ[x, y + 1, z]
            xv = not occ[x + 1, y, z]
            zv = not occ[x, y, z + 1]
            if not (top_vis or xv or zv):
                continue
        else:
            top_vis = xv = zv = True
        x0, y0, z0, x1, y1, z1 = SHAPES[b.kind]
        X0, Y0, Z0, X1, Y1, Z1 = x + x0, y + y0, z + z0, x + x1, y + y1, z + z1
        j = _jit(x, y, z)
        if xv:
            pts = [P(X1, Y0, Z0), P(X1, Y1, Z0), P(X1, Y1, Z1), P(X1, Y0, Z1)]
            d.polygon(pts, fill=_col(b.side, SHADE_X * j))
            if b.family == "grass" or b.name in ("mycelium", "podzol"):
                s = Y1 - 0.2
                d.polygon([P(X1, s, Z0), P(X1, Y1, Z0), P(X1, Y1, Z1), P(X1, s, Z1)], fill=_col(b.top, SHADE_X * j))
        if zv:
            pts = [P(X0, Y0, Z1), P(X1, Y0, Z1), P(X1, Y1, Z1), P(X0, Y1, Z1)]
            d.polygon(pts, fill=_col(b.side, SHADE_Z * j))
            if b.family == "grass" or b.name in ("mycelium", "podzol"):
                s = Y1 - 0.2
                d.polygon([P(X0, s, Z1), P(X1, s, Z1), P(X1, Y1, Z1), P(X0, Y1, Z1)], fill=_col(b.top, SHADE_Z * j))
        if top_vis:
            pts = [P(X0, Y1, Z0), P(X1, Y1, Z0), P(X1, Y1, Z1), P(X0, Y1, Z1)]
            d.polygon(pts, fill=_col(b.top, SHADE_TOP * j))
        if b.kind == "chest":
            # latch
            cx, cz = (X0 + X1) / 2, Z1
            d.line([P(cx, Y0 + 0.45, cz), P(cx, Y0 + 0.7, cz)], fill=(60, 50, 40, 255), width=2)

    if bbox:
        for e in edges:
            if e not in back:
                box_line(corners[e[0]], corners[e[1]], (120, 140, 160, 140))

    # spawn markers
    for i, (sx, sy, sz) in enumerate(spawns):
        col = (230, 70, 60, 255) if i == 0 else (60, 120, 235, 255)
        base = P(sx + 0.5, sy, sz + 0.5)
        tip = P(sx + 0.5, sy + 4, sz + 0.5)
        d.line([base, tip], fill=col, width=2)
        r = a_px * 0.9
        d.polygon([(tip[0], tip[1] - r * 1.4), (tip[0] + r, tip[1]), (tip[0], tip[1] + r * 1.4), (tip[0] - r, tip[1])],
                  fill=col, outline=(255, 255, 255, 255))
    if crop:
        bb = img.getbbox()
        if bb:
            img = img.crop((max(0, bb[0] - pad), max(0, bb[1] - pad),
                            min(img.size[0], bb[2] + pad), min(img.size[1], bb[3] + pad)))
    img.save(path, optimize=True)
    return img.size
