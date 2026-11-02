"""Voxel canvas, noise and the building blocks (islands, trees, shapes) for the maps."""
import math

import numpy as np

from blocks import AIR, BY_NAME, REG, ROT180


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
        i0, i1, j0, j1 = i % 97, (i + 1) % 97, j % 97, (j + 1) % 97
        a, b, c, d = g[i0, j0], g[i1, j0], g[i0, j1], g[i1, j1]
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


# ---------------------------------------------------------------------------------------
# Themes: how island columns are layered
# ---------------------------------------------------------------------------------------
class Theme:
    """top: surface block; fill: the layer(s) under it; base: the island body.

    base may be a weighted list; the most common block is the background and the others
    form slanted noise patches (veins) so big islands don't look like salt and pepper.
    """

    def __init__(self, top, fill, base, fill_depth=3, bottom=None, top_fn=None, fill_fn=None, base_fn=None,
                 mix=0.12):
        self.top, self.fill, self.base = top, fill, base
        self.fill_depth = fill_depth
        self.bottom = bottom
        self.top_fn, self.fill_fn, self.base_fn = top_fn, fill_fn, base_fn
        self.mix = mix
        self.sec = []
        self.dominant = base if isinstance(base, str) else None

    def setup(self, seed):
        if isinstance(self.base, str):
            return
        total = float(sum(w for _, w in self.base))
        ordered = sorted(self.base, key=lambda nw: -nw[1])
        self.dominant = ordered[0][0]
        self.sec = []
        for i, (n, w) in enumerate(ordered[1:]):
            f = w / total
            slant = ((0.55, -0.45), (-0.4, 0.6), (0.3, 0.5), (-0.6, -0.3))[i % 4]
            self.sec.append((n, Noise2(seed + 200 + i, 3.5 + 1.5 * i), 1.0 - 1.15 * f, slant))

    def base_block(self, rng, x, y, z):
        if isinstance(self.base, str):
            return self.base
        if rng.random() < self.mix:
            return pick(rng, self.base)
        for n, nz, thr, (a, b) in self.sec:
            if nz(x + a * y, z + b * y) > thr:
                return n
        return self.dominant

    GRAVITY = {"sand", "red_sand", "gravel"}

    def block(self, dd, total, fd, tn, rng, x, y, z, t):
        name = self._block(dd, total, fd, tn, rng, x, y, z, t)
        if dd == total and name in self.GRAVITY:  # never leave sand/gravel hanging over air
            return self.dominant or "stone"
        return name

    def _block(self, dd, total, fd, tn, rng, x, y, z, t):
        if dd == 0:
            return self.top_fn(tn, rng, t) if self.top_fn else self.top
        if dd <= fd:
            if self.fill_fn:
                return self.fill_fn(dd, fd, rng)
            return self.fill if isinstance(self.fill, str) else pick(rng, self.fill)
        if self.bottom and dd == total:
            b = self.bottom(rng, t)
            if b:
                return b
        if self.base_fn:
            return self.base_fn(dd, total, rng, t, x, y, z)
        return self.base_block(rng, x, y, z)


class Canvas:
    """W x H x L voxel grid indexed [x, y, z]. Maps are built point-symmetric:

    * paired islands (spawns, side islands, rocks) are built once, in full;
    * self-symmetric islands (the middle) are built only in the half space H
      (clip mode), and
    * finish() copies everything rotated 180 degrees about the map centre.
    """

    def __init__(self, W, H, L, S=1):
        assert W % 2 == 1 and L % 2 == 1, "odd sizes keep the rotation centre on a block"
        self.W, self.H, self.L, self.S = W, H, L, S
        self.cx, self.cz = W // 2, L // 2
        self.a = np.zeros((W, H, L), np.uint16)
        self.clip = False
        self.reserved = set()
        self.chests = []
        self.islands = []  # (cx, cz, r, role, sym)
        self.debris = 0

    # -- basic access ----------------------------------------------------------------
    def in_half(self, x, z):
        return x < self.cx or (x == self.cx and z <= self.cz)

    def set(self, x, y, z, name, replace=True):
        if not (0 <= x < self.W and 0 <= y < self.H and 0 <= z < self.L):
            return
        if self.clip and not (x < self.cx or (x == self.cx and z <= self.cz)):
            return
        if not replace and self.a[x, y, z] != AIR:
            return
        self.a[x, y, z] = BY_NAME[name].idx

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

    def disk(self, cx, y, cz, r, name, replace=True, rng=None, ragged=0.0, hollow=None):
        ri = int(math.ceil(r)) + 1
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                d = math.hypot(dx, dz)
                if d <= r + 0.25:
                    if hollow is not None and d < hollow:
                        continue
                    if ragged and rng is not None and d > r - 1 and rng.random() < ragged:
                        continue
                    self.set(cx + dx, y, cz + dz, name, replace)

    def cylinder(self, cx, y0, cz, r, h, name, replace=True, hollow=None):
        for y in range(y0, y0 + h):
            self.disk(cx, y, cz, r, name, replace, hollow=hollow)

    def spike(self, cx, y0, cz, r0, h, name, power=1.3, replace=True, lean=(0.0, 0.0)):
        """Tapered cone: radius r0 at the bottom, a point at the top (ice spikes, crystals)."""
        for i in range(h):
            r = r0 * (1 - i / float(h)) ** power
            ox, oz = int(round(lean[0] * i)), int(round(lean[1] * i))
            self.disk(cx + ox, y0 + i, cz + oz, max(r, 0.0), name, replace)

    def blob(self, cx, cy, cz, rx, ry, rz, name, rng=None, ragged=0.0, replace=False):
        for dx in range(-int(rx) - 1, int(rx) + 2):
            for dy in range(-int(ry) - 1, int(ry) + 2):
                for dz in range(-int(rz) - 1, int(rz) + 2):
                    e = (dx / max(rx, 0.1)) ** 2 + (dy / max(ry, 0.1)) ** 2 + (dz / max(rz, 0.1)) ** 2
                    if e <= 1.0:
                        if ragged and rng is not None and e > 0.55 and rng.random() < ragged:
                            continue
                        self.set(cx + dx, cy + dy, cz + dz, name, replace)

    def line(self, p0, p1, name, replace=True, thick=0):
        (x0, y0, z0), (x1, y1, z1) = p0, p1
        n = int(max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)) * 1.5) + 1
        for i in range(n + 1):
            t = i / float(n)
            x = int(round(x0 + (x1 - x0) * t))
            y = int(round(y0 + (y1 - y0) * t))
            z = int(round(z0 + (z1 - z0) * t))
            if thick:
                self.box(x - thick, y - thick, z - thick, x + thick, y + thick, z + thick, name, replace)
            else:
                self.set(x, y, z, name, replace)

    # -- islands -------------------------------------------------------------------------
    def island(self, cx, cz, top, r, depth, theme, seed, role, sym=False, ax=1.0, az=1.0,
               hill=1.0, flat=(), lumps=1.0, spiky=1.0):
        """Floating island: noisy outline, rolling hills on top, jagged stalactite underside.

        r, depth and hill are in blocks. sym=True makes the shape point-symmetric about
        (cx, cz) (needed for islands that sit on the map centre and are built in clip mode).
        """
        S = self.S
        rng = np.random.default_rng(seed)
        theme.setup(seed)
        ks = (2, 4, 6, 8) if sym else (2, 3, 4, 5, 7)
        harm = [(k, rng.uniform(0.05, 0.13) * (2.2 / k) * lumps, rng.uniform(0, 2 * math.pi)) for k in ks]
        n_hill = Noise2(seed + 11, 4.5 * S)
        n_hill2 = Noise2(seed + 12, 1.6 * S)
        n_dep = Noise2(seed + 23, 2.6 * S)
        n_dep2 = Noise2(seed + 37, 1.3 * S)
        n_spike = Noise2(seed + 38, 2.3)
        n_top = Noise2(seed + 41, 3.0 * S)
        n_fill = Noise2(seed + 43, 2.0 * S)
        n_edge = Noise2(seed + 47, 1.7)
        isl = Island(cx, cz, top, r, role, sym)
        self.islands.append((cx, cz, r * max(ax, az), role, sym))
        fill_mul = max(1.0, S * 0.6)

        def Sym(f, dx, dz):
            return 0.5 * (f(dx, dz) + f(-dx, -dz)) if sym else f(dx, dz)

        R = int(math.ceil(r * max(ax, az) * 1.45)) + 2
        for x in range(cx - R, cx + R + 1):
            for z in range(cz - R, cz + R + 1):
                dx, dz = x - cx, z - cz
                ex, ez = dx / ax, dz / az
                d = math.hypot(ex, ez)
                ang = math.atan2(ez, ex)
                re = r * (1 + sum(a * math.sin(k * ang + p) for k, a, p in harm))
                if S > 1:
                    re += (Sym(n_edge, dx, dz) - 0.5) * 1.6
                if d > re:
                    continue
                t = d / re
                h = top + int(round(hill * (1 - t * t) * (Sym(n_hill, dx, dz) * 2.4 - 0.9)
                                    + hill * 0.45 * (Sym(n_hill2, dx, dz) - 0.5) * (1 - t)))
                for fx, fz, fr in flat:
                    if math.hypot(x - fx, z - fz) <= fr:
                        h = top
                dep = 1.5 + depth * ((1 - t) ** 1.15) * (0.55 + 0.6 * Sym(n_dep, dx, dz) + 0.35 * Sym(n_dep2, dx, dz))
                if S > 1:
                    dep += spiky * depth * 0.25 * max(0.0, Sym(n_spike, dx, dz) - 0.45) * (1 - t) ** 0.5
                bot = h - int(round(dep))
                fd = max(1, int(round(theme.fill_depth * fill_mul * (0.7 + 0.6 * Sym(n_fill, dx, dz)))))
                isl.cols[(x, z)] = h
                isl.t[(x, z)] = t
                tn = Sym(n_top, dx, dz)
                for y in range(bot, h + 1):
                    self.set(x, y, z, theme.block(h - y, h - bot, fd, tn, rng, x, y, z, t))
        return isl

    # -- placement helpers ---------------------------------------------------------------
    def spots(self, isl, rng, tmin=0.0, tmax=0.8, margin=0):
        """Candidate surface columns of an island, shuffled. Symmetric islands only offer
        columns in the left half (x <= cx - margin); rotation copies them to the right."""
        out = []
        for (x, z), h in isl.cols.items():
            t = isl.t[(x, z)]
            if t < tmin or t > tmax:
                continue
            if (x, z) in self.reserved:
                continue
            if isl.sym and not (x <= self.cx - margin):
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
        self.set(x, y, z, "chest_" + facing)
        self.chests.append((x, y, z))
        self.reserve(x, z, 2)
        return (x, y, z)

    def chest_ring(self, isl, n, radius, start_deg=45.0, face="out"):
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
            placed.append(self.chest(isl, x, z, "in" if face == "in" else None))
        return placed

    def scatter(self, isl, rng, plants, density, tmax=0.92, on=None, cluster=None, margin=1):
        """Sprinkle 1-block plants on free surface cells. cluster=(noise, threshold) makes
        them grow in patches."""
        for (x, z) in self.spots(isl, rng, 0.0, tmax, margin=margin):
            if rng.random() > density:
                continue
            if cluster and cluster[0](x, z) < cluster[1]:
                continue
            h = isl.cols[(x, z)]
            if on and self.name_at(x, h, z) not in on:
                continue
            if not self.free(x, h + 1, z):
                continue
            self.set(x, h + 1, z, pick(rng, plants))

    def forest(self, isl, rng, fn, spacing, tmin=0.1, tmax=0.8, margin=4, limit=10 ** 6, density=1.0,
               clear=1, on=None):
        """Place decorations fn(x, y, z) on the island, at least `spacing` apart."""
        cell = max(1.0, spacing)
        grid = {}
        done = []
        for (x, z) in self.spots(isl, rng, tmin, tmax, margin=margin):
            if len(done) >= limit:
                break
            if density < 1.0 and rng.random() > density:
                continue
            gx, gz = int(x // cell), int(z // cell)
            near = False
            for ix in (gx - 1, gx, gx + 1):
                for iz in (gz - 1, gz, gz + 1):
                    for (px, pz) in grid.get((ix, iz), ()):
                        if (x - px) ** 2 + (z - pz) ** 2 < spacing * spacing:
                            near = True
                            break
            if near:
                continue
            if any((x + dx, z + dz) in self.reserved
                   for dx in range(-clear, clear + 1) for dz in range(-clear, clear + 1)):
                continue
            h = isl.cols[(x, z)]
            if on and self.name_at(x, h, z) not in on:
                continue
            if not self.free(x, h + 1, z):
                continue
            fn(x, h + 1, z)
            grid.setdefault((gx, gz), []).append((x, z))
            done.append((x, z))
        return done

    # -- finishing -----------------------------------------------------------------------
    def remove_debris(self, min_size=12):
        """Drop small 6-connected clusters that float free of any island (ragged blob
        leftovers). Chests are never in such clusters because they sit on islands."""
        pts = np.argwhere(self.a != AIR)
        filled = set(map(tuple, pts.tolist()))
        seen = set()
        removed = 0
        for start in filled:
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
        self.islands = self.islands + [(W - 1 - x, L - 1 - z, r_, role, sym)
                                       for (x, z, r_, role, sym) in self.islands if not sym]
        self.chests = sorted(set(self.chests) | {(W - 1 - x, y, L - 1 - z) for (x, y, z) in self.chests})
        return conflicts


# ---------------------------------------------------------------------------------------
# Trees & plants (normal Minecraft size)
# ---------------------------------------------------------------------------------------
def oak_tree(cv, x, y, z, rng, wood="oak", height=None, leaves=None):
    h = height or int(rng.integers(4, 7))
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


def big_oak(cv, x, y, z, rng, wood="oak", height=None):
    """Fancy oak: taller trunk, a few branches and several leaf clumps."""
    h = height or int(rng.integers(8, 13))
    log, lv, bark = wood + "_log", wood + "_leaves", wood + "_wood"
    top = y + h
    cv.blob(x, top, z, 3.2, 2.2, 3.2, lv, rng, ragged=0.3)
    for i in range(int(rng.integers(2, 4))):
        ang = rng.uniform(0, 2 * math.pi)
        by = y + int(h * rng.uniform(0.5, 0.8))
        ex, ez = x + int(round(math.cos(ang) * 3)), z + int(round(math.sin(ang) * 3))
        cv.line((x, by, z), (ex, by + 2, ez), bark)
        cv.blob(ex, by + 3, ez, 2.3, 1.6, 2.3, lv, rng, ragged=0.3)
    for dy in range(h):
        cv.set(x, y + dy, z, log)


def spruce_tree(cv, x, y, z, rng, height=None, snowy=False, maxr=None):
    h = height or int(rng.integers(6, 11))
    maxr = maxr or (2 if h < 9 else 3)
    top = y + h
    for dy in range(h):
        cv.set(x, y + dy, z, "spruce_log")
    cv.set(x, top, z, "spruce_leaves", replace=False)
    if snowy:
        cv.set(x, top + 1, z, "snow", replace=False)
    layers = h - 2
    for i in range(layers):
        yy = top - 1 - i
        rad = int(round(maxr * (i + 1) / layers + 0.3)) - (1 if i % 2 == 0 and i > 1 else 0)
        rad = max(0, rad)
        for dx in range(-rad, rad + 1):
            for dz in range(-rad, rad + 1):
                if abs(dx) + abs(dz) > rad + (1 if rad >= 2 else 0):
                    continue
                if (dx or dz) and cv.free(x + dx, yy, z + dz):
                    cv.set(x + dx, yy, z + dz, "spruce_leaves")
                    if snowy and cv.free(x + dx, yy + 1, z + dz):
                        cv.set(x + dx, yy + 1, z + dz, "snow")


def mega_spruce(cv, x, y, z, rng, height=None, snowy=False):
    """2x2 trunk giant spruce."""
    h = height or int(rng.integers(16, 26))
    top = y + h
    for dy in range(h):
        for ox in (0, 1):
            for oz in (0, 1):
                cv.set(x + ox, y + dy, z + oz, "spruce_log")
    crown = int(h * 0.65)
    for i in range(crown):
        yy = top - i
        rad = 0.8 + 4.2 * (i / float(crown)) - (0.9 if i % 3 == 2 else 0)
        for dx in range(-6, 8):
            for dz in range(-6, 8):
                if math.hypot(dx - 0.5, dz - 0.5) <= rad and cv.free(x + dx, yy, z + dz):
                    cv.set(x + dx, yy, z + dz, "spruce_leaves")
                    if snowy and cv.free(x + dx, yy + 1, z + dz):
                        cv.set(x + dx, yy + 1, z + dz, "snow")


def jungle_tree(cv, x, y, z, rng, height=None):
    h = height or int(rng.integers(7, 11))
    top = y + h
    for dy in range(h):
        cv.set(x, y + dy, z, "jungle_log")
    cv.blob(x, top, z, 3.2, 1.6, 3.2, "jungle_leaves", rng, ragged=0.35)
    cv.blob(x, top + 1, z, 2.0, 1.2, 2.0, "jungle_leaves", rng, ragged=0.25)
    sx, sz = (1, 0) if rng.random() < 0.5 else (0, 1)
    by = y + h // 2
    cv.set(x + sx, by, z + sz, "jungle_log")
    cv.blob(x + 2 * sx, by + 1, z + 2 * sz, 1.6, 1.0, 1.6, "jungle_leaves", rng, ragged=0.3)


def mega_jungle(cv, x, y, z, rng, height=None):
    """2x2 trunk jungle giant with a wide crown and side branches."""
    h = height or int(rng.integers(16, 25))
    top = y + h
    for dy in range(h):
        for ox in (0, 1):
            for oz in (0, 1):
                cv.set(x + ox, y + dy, z + oz, "jungle_log")
    cv.blob(x, top, z, 5.5, 2.6, 5.5, "jungle_leaves", rng, ragged=0.35)
    cv.blob(x, top + 2, z, 3.5, 1.5, 3.5, "jungle_leaves", rng, ragged=0.3)
    for i in range(int(rng.integers(2, 4))):
        ang = rng.uniform(0, 2 * math.pi)
        by = y + int(h * rng.uniform(0.45, 0.75))
        ex, ez = x + int(round(math.cos(ang) * 5)), z + int(round(math.sin(ang) * 5))
        cv.line((x, by, z), (ex, by + 3, ez), "jungle_wood")
        cv.blob(ex, by + 4, ez, 3.0, 1.6, 3.0, "jungle_leaves", rng, ragged=0.3)


def bush(cv, x, y, z, rng, wood="jungle"):
    cv.set(x, y, z, wood + "_log")
    cv.blob(x, y + 1, z, 1.8, 1.2, 1.8, wood + "_leaves", rng, ragged=0.3)


def red_mushroom_tree(cv, x, y, z, rng, height=None):
    h = height or int(rng.integers(4, 7))
    for dy in range(h):
        cv.set(x, y + dy, z, "mushroom_stem")
    top = y + h
    for dy, rad in ((-1, 2), (0, 2), (1, 1)):
        for dx in range(-rad, rad + 1):
            for dz in range(-rad, rad + 1):
                if dy == -1 and abs(dx) < rad and abs(dz) < rad:
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


def giant_tree(cv, x, y, z, rng, height, trunk_r, canopy_r, wood="oak", branches=7):
    """Landmark tree: tapered bark trunk with roots, long branches and a huge crown."""
    bark, lv = wood + "_wood", wood + "_leaves"
    for i in range(8):  # roots
        ang = 2 * math.pi * i / 8 + rng.uniform(-0.2, 0.2)
        ln = trunk_r + rng.uniform(2.5, 5.0)
        ex, ez = int(round(x + math.cos(ang) * ln)), int(round(z + math.sin(ang) * ln))
        cv.line((x, y + 2, z), (ex, y, ez), bark)
        cv.line((x, y + 1, z), (ex, y, ez), bark)
    for dy in range(height):
        rr = trunk_r * (1 - 0.45 * dy / height)
        cv.disk(x, y + dy, z, rr, bark)
    for i in range(branches):
        ang = 2 * math.pi * i / branches + rng.uniform(-0.3, 0.3)
        sy = y + int(height * rng.uniform(0.5, 0.85))
        ln = canopy_r * rng.uniform(0.6, 0.85)
        ex, ez = int(round(x + math.cos(ang) * ln)), int(round(z + math.sin(ang) * ln))
        ey = sy + int(ln * 0.45)
        cv.line((x, sy, z), (ex, ey, ez), bark, thick=1 if trunk_r >= 2 else 0)
        cv.blob(ex, ey + 1, ez, canopy_r * 0.45, canopy_r * 0.3, canopy_r * 0.45, lv, rng, ragged=0.3)
    cv.blob(x, y + height, z, canopy_r * 0.7, canopy_r * 0.38, canopy_r * 0.7, lv, rng, ragged=0.3)
