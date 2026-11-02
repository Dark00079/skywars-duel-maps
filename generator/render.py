"""Isometric PNG preview renderer (painter's algorithm over visible voxels)."""
import numpy as np
from PIL import Image, ImageDraw

from blocks import AIR, REG, SHAPES

SHADE_TOP, SHADE_X, SHADE_Z = 1.0, 0.80, 0.64
STRIPPED_TOP = {"grass_block", "mycelium", "podzol"}


def _jit(x, y, z):
    h = (x * 73856093) ^ (y * 19349663) ^ (z * 83492791)
    return 0.94 + ((h & 0xFF) / 255.0) * 0.12


def _col(rgb, f):
    return tuple(max(0, min(255, int(c * f))) for c in rgb)


def render(a, path, spawns=(), a_px=2.0, vscale=1.2, pad=16):
    """Render the map (without its two corner stones) and crop to the drawn pixels."""
    W, H, L = a.shape
    a = a.copy()
    a[0, 0, 0] = AIR
    a[W - 1, H - 1, L - 1] = AIR
    full = np.array([REG[i].full if i else False for i in range(len(REG))])
    fa = full[a]
    occ = np.zeros((W + 1, H + 1, L + 1), bool)
    occ[:W, :H, :L] = fa
    nz = a != AIR
    top_vis = nz & ~occ[:W, 1:, :L]
    x_vis = nz & ~occ[1:, :H, :L]
    z_vis = nz & ~occ[:W, :H, 1:]
    nonfull = nz & ~fa
    draw = top_vis | x_vis | z_vis | nonfull
    pts = np.argwhere(draw)
    order = np.argsort(pts.sum(axis=1), kind="stable")

    def proj(X, Y, Z):
        return ((X - Z) * a_px, (X + Z) * a_px / 2.0 - Y * a_px * vscale)

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

    strips = a_px >= 4
    for k in order:
        x, y, z = (int(v) for v in pts[k])
        b = REG[int(a[x, y, z])]
        if b.full:
            tv, xv, zv = top_vis[x, y, z], x_vis[x, y, z], z_vis[x, y, z]
        else:
            tv = xv = zv = True
        x0, y0, z0, x1, y1, z1 = SHAPES[b.kind]
        X0, Y0, Z0, X1, Y1, Z1 = x + x0, y + y0, z + z0, x + x1, y + y1, z + z1
        j = _jit(x, y, z)
        stripe = strips and b.name in STRIPPED_TOP
        if xv:
            d.polygon([P(X1, Y0, Z0), P(X1, Y1, Z0), P(X1, Y1, Z1), P(X1, Y0, Z1)], fill=_col(b.side, SHADE_X * j))
            if stripe:
                s = Y1 - 0.2
                d.polygon([P(X1, s, Z0), P(X1, Y1, Z0), P(X1, Y1, Z1), P(X1, s, Z1)], fill=_col(b.top, SHADE_X * j))
        if zv:
            d.polygon([P(X0, Y0, Z1), P(X1, Y0, Z1), P(X1, Y1, Z1), P(X0, Y1, Z1)], fill=_col(b.side, SHADE_Z * j))
            if stripe:
                s = Y1 - 0.2
                d.polygon([P(X0, s, Z1), P(X1, s, Z1), P(X1, Y1, Z1), P(X0, Y1, Z1)], fill=_col(b.top, SHADE_Z * j))
        if tv:
            d.polygon([P(X0, Y1, Z0), P(X1, Y1, Z0), P(X1, Y1, Z1), P(X0, Y1, Z1)], fill=_col(b.top, SHADE_TOP * j))

    # spawn markers
    r = max(5.0, a_px * 2.2)
    for i, (sx, sy, sz) in enumerate(spawns):
        col = (230, 70, 60, 255) if i == 0 else (60, 120, 235, 255)
        base = P(sx + 0.5, sy, sz + 0.5)
        tip = P(sx + 0.5, sy + max(4, 24 / a_px), sz + 0.5)
        d.line([base, tip], fill=col, width=2)
        d.polygon([(tip[0], tip[1] - r * 1.4), (tip[0] + r, tip[1]), (tip[0], tip[1] + r * 1.4), (tip[0] - r, tip[1])],
                  fill=col, outline=(255, 255, 255, 255))
    bb = img.getbbox()
    if bb:
        img = img.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(img.size[0], bb[2] + pad),
                        min(img.size[1], bb[3] + pad)))
    img.save(path, optimize=True)
    return img.size
