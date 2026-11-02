"""Voxel canvas, noise and the building blocks (islands, trees, shapes) for the maps."""
import math

import numpy as np

from blocks import AIR, BY_NAME, REG, ROT180, B


class Noise2:
    """Smooth 2D value noise in [0, 1]."""

    def __init__(self, seed, scale):
        self.g = np.random.default_rng(seed).random((97, 97))
        self.scale = scale

    def __call__(self, x, z):
        u = x / self.scale + 48.3
        v = z / self.scale + 48.7
        i, j = int(math.floor(u)), int(math.floor(v))
        fu, fv = u - i, v - j
        fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
        g = self.g
        a = g[i % 97, j % 97]
        b = g[(i + 1) % 97, j % 97]
        c = g[i % 97, (j + 1) % 97]
        d = g[(i + 1) % 97, (j + 1) % 97]
        return (a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv


def pick(rng, weighted):
    """weighted: list of (name, weight) -> block name"""
    total = sum(w for _, w in weighted)
    r = rng.random() * total
    for n, w in weighted:
        r -= w
        if r <= 0:
            return n
    return weighted[-1][0]


class Island:
    def __init__(self, cx, cz, top, r, role, sym):
        self.cx, self.cz, self.top, self.r = cx, cz, top, r
        self.role, self.sym = role, sym
        self.cols = {}     # (x, z) -> surface y
        self.t = {}        # (x, z) -> normalised distance from centre (0 centre, 1 edge)

    def surface(self, x, z):
        return self.cols.get((x, z))


class Canvas:
    """W x H x L voxel grid indexed [x, y, z]. Maps are built point-symmetric:

    * paired islands (spawns, side islands, rocks) are built once, in full;
    * self-symmetric islands (the middle) are built only in the half space H
      (clip mode), and
    * finish() copies everything rotated 180 degrees about the map centre.
    """

    def __init__(self, W, H, L):
        assert W % 2 == 1 and L % 2 == 1, "odd sizes keep the rotation centre on a block"
        self.W, self.H, self.L = W, H, L
        self.cx, self.cz = W // 2, L // 2
        self.a = np.zeros((W, H, L), np.uint16)
        self.clip = False
        self.reserved = set()
        self.chests = []
        self.islands = []  # (cx, cz, r, role, sym)

    # -- basic access ----------------------------------------------------------------
    def in_half(self, x, z):
        return x < self.cx or (x == self.cx and z <= self.cz)

    def ok(self, x, y, z):
        if not (0 <= x < self.W and 0 <= y < self.H and 0 <= z < self.L):
            return False
        if self.clip and not self.in_half(x, z):
            return False
        return True

    def set(self, x, y, z, name, replace=True):
        if not self.ok(x, y, z):
            return
        if not replace and self.a[x, y, z] != AIR:
            return
        self.a[x, y, z] = B(name)

    def get(self, x, y, z):
        if not (0 <= x < self.W and 0 <= y < self.H and 0 <= z < self.L):
            return AIR
        return int(self.a[x, y, z])

    def name_at(self, x, y, z):
        return REG[self.get(x, y, z)].name

    def free(self, x, y, z):
        return self.get(x, y, z) == AIR

    def reserve(self, x, z, rad=1):
        for dx in range(-rad, rad + 1):
            for dz in range(-rad, rad + 1):
                self.reserved.add((x + dx, z + dz))

    # -- shapes --------------------------------------------------------------------------
    def box(self, x0, y0, z0, x1, y1, z1, name, replace=True):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set(x, y, z, name, replace)

    def hollow_box(self, x0, y0, z0, x1, y1, z1, name):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    if x in (x0, x1) or z in (z0, z1):
                        self.set(x, y, z, name)

    def disk(self, cx, y, cz, r, name, replace=True, rng=None, ragged=0.0):
        ri = int(math.ceil(r))
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                d = math.hypot(dx, dz)
                if d <= r + 0.25:
                    if ragged and rng is not None and d > r - 1 and rng.random() < ragged:
                        continue
                    self.set(cx + dx, y, cz + dz, name, replace)

    def blob(self, cx, cy, cz, rx, ry, rz, name, rng=None, ragged=0.0, replace=False):
        for dx in range(-int(rx) - 1, int(rx) + 2):
            for dy in range(-int(ry) - 1, int(ry) + 2):
                for dz in range(-int(rz) - 1, int(rz) + 2):
                    e = (dx / max(rx, 0.1)) ** 2 + (dy / max(ry, 0.1)) ** 2 + (dz / max(rz, 0.1)) ** 2
                    if e <= 1.0:
                        if ragged and rng is not None and e > 0.55 and rng.random() < ragged:
                            continue
                        self.set(cx + dx, cy + dy, cz + dz, name, replace)

    # -- islands -------------------------------------------------------------------------
    def island(self, cx, cz, top, r, depth, theme, seed, role, sym=False, ax=1.0, az=1.0,
               hill=1.0, flat=(), lumps=1.0):
        """Floating island: noisy outline, gentle hills on top, stalactite underside.

        sym=True makes the shape point-symmetric about (cx, cz) (needed for islands that
        sit on the map centre and are only built in clip mode).
        """
        rng = np.random.default_rng(seed)
        ks = (2, 4, 6) if sym else (2, 3, 4, 5)
        harm = [(k, rng.uniform(0.05, 0.13) * (2.2 / k) * lumps, rng.uniform(0, 2 * math.pi)) for k in ks]
        n_hill = Noise2(seed + 11, 4.5)
        n_dep = Noise2(seed + 23, 2.6)
        n_dep2 = Noise2(seed + 37, 1.3)
        n_top = Noise2(seed + 41, 3.0)
        isl = Island(cx, cz, top, r, role, sym)
        self.islands.append((cx, cz, r * max(ax, az), role, sym))

        def S(f, dx, dz):
            return 0.5 * (f(dx, dz) + f(-dx, -dz)) if sym else f(dx, dz)

        R = int(math.ceil(r * max(ax, az) * 1.45)) + 1
        for x in range(cx - R, cx + R + 1):
            for z in range(cz - R, cz + R + 1):
                dx, dz = x - cx, z - cz
                ex, ez = dx / ax, dz / az
                d = math.hypot(ex, ez)
                ang = math.atan2(ez, ex)
                re = r * (1 + sum(a * math.sin(k * ang + p) for k, a, p in harm))
                if d > re:
                    continue
                t = d / re
                h = top + int(round(hill * (1 - t * t) * (S(n_hill, dx, dz) * 2.4 - 0.9)))
                for fx, fz, fr in flat:
                    if math.hypot(x - fx, z - fz) <= fr:
                        h = top
                dep = 1.5 + depth * ((1 - t) ** 1.15) * (0.55 + 0.6 * S(n_dep, dx, dz) + 0.35 * S(n_dep2, dx, dz))
                bot = h - int(round(dep))
                isl.cols[(x, z)] = h
                isl.t[(x, z)] = t
                tn = S(n_top, dx, dz)
                for y in range(bot, h + 1):
                    dd = h - y  # depth below surface
                    name = theme.block(dd, h - bot, tn, rng, x, y, z, t)
                    self.set(x, y, z, name)
        return isl

    # -- placement helpers ---------------------------------------------------------------
    def spots(self, isl, rng, tmin=0.0, tmax=0.8, side=None, margin=0):
        """Candidate surface columns of an island, shuffled. side='left' restricts to x<cx-margin."""
        out = []
        for (x, z), h in isl.cols.items():
            t = isl.t[(x, z)]
            if t < tmin or t > tmax:
                continue
            if (x, z) in self.reserved:
                continue
            if isl.sym and not (x <= self.cx - margin):
                continue
            if side == "left" and not (x <= self.cx - margin):
                continue
            out.append((x, z))
        out.sort()
        rng.shuffle(out)
        return out

    def chest(self, isl, x, z, facing=None):
        h = isl.surface(x, z)
        if h is None:
            raise ValueError("chest off island at %d,%d" % (x, z))
        y = h + 1
        for (ox, oy, oz) in self.chests:
            if abs(ox - x) + abs(oz - z) <= 1 and abs(oy - y) <= 1:
                raise ValueError("adjacent chests at %d,%d" % (x, z))
        if facing == "in":
            dx, dz = isl.cx - x, isl.cz - z
            if dx == 0 and dz == 0:
                facing = "north"
            elif abs(dx) >= abs(dz):
                facing = "east" if dx > 0 else "west"
            else:
                facing = "south" if dz > 0 else "north"
        if facing is None:
            dx, dz = x - isl.cx, z - isl.cz
            if abs(dx) >= abs(dz):
                facing = "east" if dx > 0 else "west"
            else:
                facing = "south" if dz > 0 else "north"
        # clear the cell (decor) and make sure there is something under it
        self.set(x, y, z, "chest_" + facing)
        self.chests.append((x, y, z))
        self.reserve(x, z, 1)
        return (x, y, z)

    def chest_ring(self, isl, n, radius, start_deg=45.0, y_override=None, face="out"):
        """Place n chests evenly around the island centre. For symmetric islands only the
        ones in the build half are placed (rotation creates the rest), so n must be even."""
        placed = []
        for i in range(n):
            ang = math.radians(start_deg + 360.0 * i / n)
            rr = radius
            while True:
                x = isl.cx + int(round(math.cos(ang) * rr))
                z = isl.cz + int(round(math.sin(ang) * rr))
                if (x, z) in isl.cols and isl.t[(x, z)] < 0.92:
                    break
                rr -= 0.5
                if rr < 1:
                    raise ValueError("no room for ring chest")
            if isl.sym and not self.in_half(x, z):
                continue
            facing = None
            if face == "in":
                dx, dz = isl.cx - x, isl.cz - z
                if abs(dx) >= abs(dz):
                    facing = "east" if dx > 0 else "west"
                else:
                    facing = "south" if dz > 0 else "north"
            placed.append(self.chest(isl, x, z, facing))
        return placed

    def scatter(self, isl, rng, plants, density, tmax=0.9, on=None, side=None):
        """Sprinkle 1-block plants on free surface cells."""
        for (x, z) in self.spots(isl, rng, 0.0, tmax, side=side, margin=1):
            if rng.random() > density:
                continue
            h = isl.cols[(x, z)]
            if on and self.name_at(x, h, z) not in on:
                continue
            if not self.free(x, h + 1, z):
                continue
            self.set(x, h + 1, z, pick(rng, plants))

    def place_n(self, isl, rng, n, fn, tmin=0.15, tmax=0.7, min_dist=4.0, margin=4, avoid=()):
        """Place up to n decorations with fn(x, y, z) at spaced surface spots."""
        done = []
        for (x, z) in self.spots(isl, rng, tmin, tmax, margin=margin):
            if len(done) >= n:
                break
            if any(math.hypot(x - px, z - pz) < min_dist for px, pz in done + list(avoid)):
                continue
            if any((x + dx, z + dz) in self.reserved for dx in (-1, 0, 1) for dz in (-1, 0, 1)):
                continue
            h = isl.cols[(x, z)]
            if not self.free(x, h + 1, z):
                continue
            fn(x, h + 1, z)
            done.append((x, z))
        return done

    # -- finishing -----------------------------------------------------------------------
    def remove_debris(self, min_size=12):
        """Drop small 6-connected clusters that float free of any island (ragged blob
        leftovers). Chests are never in such clusters because they sit on islands."""
        filled = set(map(tuple, np.argwhere(self.a != AIR).tolist()))
        seen = set()
        removed = 0
        for start in list(filled):
            if start in seen:
                continue
            comp = [start]
            seen.add(start)
            i = 0
            while i < len(comp):
                x, y, z = comp[i]
                i += 1
                for n in ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1), (x, y, z - 1)):
                    if n in filled and n not in seen:
                        seen.add(n)
                        comp.append(n)
            if len(comp) < min_size:
                for (x, y, z) in comp:
                    self.a[x, y, z] = AIR
                removed += len(comp)
        return removed

    def finish(self):
        self.debris = self.remove_debris()
        rot_lut = np.arange(len(REG), dtype=np.uint16)
        for a, b in ROT180.items():
            rot_lut[BY_NAME[a].idx] = BY_NAME[b].idx
        r = rot_lut[self.a[::-1, :, ::-1]]
        both = (self.a != AIR) & (r != AIR) & (self.a != r)
        conflicts = int(both.sum())
        self.a = np.where(self.a != AIR, self.a, r).astype(np.uint16)
        W, L = self.W, self.L
        self.islands = self.islands + [(W - 1 - x, L - 1 - z, r, role, sym)
                                       for (x, z, r, role, sym) in self.islands if not sym]
        self.chests = sorted(set(self.chests) | {(W - 1 - x, y, L - 1 - z) for (x, y, z) in self.chests})
        return conflicts


# ---------------------------------------------------------------------------------------
# Themes: how island columns are layered
# ---------------------------------------------------------------------------------------
class Theme:
    def __init__(self, top, fill, base, fill_depth=3, bottom=None, top_fn=None, base_fn=None):
        self.top, self.fill, self.base = top, fill, base
        self.fill_depth = fill_depth
        self.bottom = bottom
        self.top_fn, self.base_fn = top_fn, base_fn

    def block(self, dd, total, tn, rng, x, y, z, t):
        if dd == 0:
            if self.top_fn:
                return self.top_fn(tn, rng, t)
            return self.top
        if dd <= self.fill_depth:
            return self.fill if isinstance(self.fill, str) else pick(rng, self.fill)
        if self.bottom and dd == total:
            b = self.bottom(rng, t)
            if b:
                return b
        if self.base_fn:
            return self.base_fn(dd, total, rng, t)
        return self.base if isinstance(self.base, str) else pick(rng, self.base)


# ---------------------------------------------------------------------------------------
# Trees & plants
# ---------------------------------------------------------------------------------------
def oak_tree(cv, x, y, z, rng, wood="oak", height=None, leaves=None):
    h = height or int(rng.integers(4, 6))
    log, lv = wood + "_log", leaves or (wood + "_leaves")
    top = y + h - 1
    for dy in range(-2, 2):
        rad = 2 if dy < 0 else 1
        for dx in range(-rad, rad + 1):
            for dz in range(-rad, rad + 1):
                if abs(dx) == rad and abs(dz) == rad and (dy >= 0 or rng.random() < 0.5):
                    continue
                cv.set(x + dx, top + dy, z + dz, lv, replace=False)
    cv.set(x, top + 2, z, lv, replace=False)
    for dy in range(h):
        cv.set(x, y + dy, z, log)


def spruce_tree(cv, x, y, z, rng, height=None, snowy=False):
    h = height or int(rng.integers(6, 9))
    top = y + h
    for dy in range(h):
        cv.set(x, y + dy, z, "spruce_log")
    # cone of rings, alternating radius
    yy = top
    cv.set(x, yy, z, "spruce_leaves", replace=False)
    if snowy:
        cv.set(x, yy + 1, z, "snow", replace=False)
    rad_seq = [1, 0, 1, 2, 1, 2, 3, 2][: max(3, h - 2)]
    for i, rad in enumerate(rad_seq):
        yy = top - 1 - i
        for dx in range(-rad, rad + 1):
            for dz in range(-rad, rad + 1):
                if abs(dx) + abs(dz) > rad + (1 if rad >= 2 else 0):
                    continue
                if (dx or dz) and cv.free(x + dx, yy, z + dz):
                    cv.set(x + dx, yy, z + dz, "spruce_leaves")
                    if snowy and cv.free(x + dx, yy + 1, z + dz):
                        cv.set(x + dx, yy + 1, z + dz, "snow")


def jungle_tree(cv, x, y, z, rng, height=None):
    h = height or int(rng.integers(7, 10))
    top = y + h
    for dy in range(h):
        cv.set(x, y + dy, z, "jungle_log")
    cv.blob(x, top, z, 3.2, 1.6, 3.2, "jungle_leaves", rng, ragged=0.35)
    cv.blob(x, top + 1, z, 2.0, 1.2, 2.0, "jungle_leaves", rng, ragged=0.25)
    # a lower side branch canopy
    sx, sz = (1, 0) if rng.random() < 0.5 else (0, 1)
    by = y + h // 2
    cv.set(x + sx, by, z + sz, "jungle_log")
    cv.blob(x + 2 * sx, by + 1, z + 2 * sz, 1.6, 1.0, 1.6, "jungle_leaves", rng, ragged=0.3)


def red_mushroom_tree(cv, x, y, z, rng, height=None):
    h = height or int(rng.integers(4, 7))
    for dy in range(h):
        cv.set(x, y + dy, z, "mushroom_stem")
    top = y + h
    for dy, rad in ((-1, 2), (0, 2), (1, 1)):
        for dx in range(-rad, rad + 1):
            for dz in range(-rad, rad + 1):
                if dy < 1 and abs(dx) < rad and abs(dz) < rad and dy == -1:
                    continue  # hollow underside like vanilla
                if abs(dx) == rad and abs(dz) == rad:
                    continue
                cv.set(x + dx, top + dy, z + dz, "red_mushroom_block", replace=False)


def brown_mushroom_tree(cv, x, y, z, rng, height=None):
    h = height or int(rng.integers(4, 6))
    for dy in range(h):
        cv.set(x, y + dy, z, "mushroom_stem")
    top = y + h
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            if abs(dx) == 3 and abs(dz) == 3:
                continue
            cv.set(x + dx, top, z + dz, "brown_mushroom_block", replace=False)


def cactus(cv, x, y, z, rng):
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if not cv.free(x + dx, y, z + dz):
            return
    h = int(rng.integers(1, 4))
    for dy in range(h):
        cv.set(x, y + dy, z, "cactus")


def boulder(cv, x, y, z, rng, name, size=1.3):
    cv.blob(x, y, z, size, size * 0.8, size, name, rng, ragged=0.3, replace=False)
