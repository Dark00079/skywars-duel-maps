"""The 12 duel maps. Each builder returns a dict with the canvas and spawn info.

Every map is point-symmetric (180 degree rotation about the centre), so both players
get identical islands, chests and distances.

S is the map scale. Island sizes, depths, gaps and the centrepiece structures scale
with it; trees, flowers and other details stay normal Minecraft size (there are just
more of them).
"""
import math

import numpy as np

from terrain import (Canvas, Noise2, Theme, big_oak, boulder, brown_mushroom_tree, bush, cactus, giant_tree,
                     jungle_tree, mega_jungle, mega_spruce, oak_tree, pick, red_mushroom_tree, spruce_tree)

S = 5

FLOWERS = [("poppy", 3), ("dandelion", 3), ("oxeye_daisy", 2), ("azure_bluet", 2),
           ("red_tulip", 1), ("orange_tulip", 1), ("allium", 1), ("blue_orchid", 1)]


def P(v):
    """A layout coordinate/size from the original 1x design, scaled."""
    return int(round(v * S))


def spawn_island(cv, th, x, z, top, r, depth, seed, chest_offs, decor=None, hill=None):
    hill = 0.7 * S if hill is None else hill
    isl = cv.island(x, z, top, r, depth, th, seed, "spawn", flat=[(x, z, 7.5)], hill=hill)
    cv.reserve(x, z, 4)  # no trees or plants right on the spawn
    for dx, dz in chest_offs:
        cv.chest(isl, x + dx, z + dz, "in")
    if decor:
        decor(isl)
    # a clear 3x3, 4-high space above the pad for the spawn cage
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for dy in range(1, 5):
                cv.set(x + dx, top + dy, z + dz, "air")
    return isl


def result(name, slug, blurb, cv, spawn_xyz, layout):
    return dict(name=name, slug=slug, blurb=blurb, cv=cv, spawn=spawn_xyz, layout=layout)


def square_ring(cv, cx, y, cz, half, name, thick=1):
    for dx in range(-half, half + 1):
        for dz in range(-half, half + 1):
            if max(abs(dx), abs(dz)) > half - thick:
                cv.set(cx + dx, y, cz + dz, name)


# =======================================================================================
def meadow():
    cv = Canvas(P(81), P(44), P(61), S)
    rng = np.random.default_rng(101)
    th = Theme("grass_block", "dirt", [("stone", 70), ("andesite", 14), ("cobblestone", 10), ("granite", 6)],
               top_fn=lambda tn, r, t: "coarse_dirt" if (tn > 0.84 and r.random() < 0.45) else "grass_block")
    patch = Noise2(1999, 9.0)

    def tree(x, y, z):
        roll = rng.random()
        if roll < 0.25:
            big_oak(cv, x, y, z, rng)
        elif roll < 0.75:
            oak_tree(cv, x, y, z, rng)
        else:
            oak_tree(cv, x, y, z, rng, wood="birch", height=int(rng.integers(5, 8)))

    def greenery(isl, spacing=9, margin=4, tmin=0.15):
        cv.forest(isl, rng, tree, spacing, tmin=tmin, tmax=0.82, margin=margin)
        cv.scatter(isl, rng, FLOWERS, 0.4, on={"grass_block"}, cluster=(patch, 0.6))
        cv.forest(isl, rng, lambda x, y, z: boulder(cv, x, y, z, rng, "mossy_cobblestone", 1.4), 30,
                  tmin=0.3, tmax=0.8, margin=margin, limit=3)

    spawn_island(cv, th, P(12), P(30), P(20), 5.5 * S, 9 * S, 1001, [(-4, -4), (-5, 3), (4, -4)],
                 lambda i: greenery(i))

    n = cv.island(cv.cx, P(9), P(19), 4.6 * S, 7 * S, th, 1003, "side")
    cv.chest(n, cv.cx - 5, P(9))
    cv.chest(n, cv.cx + 5, P(9))
    cv.forest(n, rng, lambda x, y, z: oak_tree(cv, x, y, z, rng, wood="birch", height=int(rng.integers(5, 8))),
              6, tmin=0.1, tmax=0.8)
    cv.scatter(n, rng, FLOWERS, 0.5, on={"grass_block"}, cluster=(patch, 0.55))

    cv.clip = True
    top = P(22)
    m = cv.island(cv.cx, cv.cz, top, 9.6 * S, 14 * S, th, 1002, "mid", sym=True, hill=1.2 * S,
                  flat=[(cv.cx, cv.cz, 16)])
    giant_tree(cv, cv.cx, top + 1, cv.cz, rng, height=26, trunk_r=2.6, canopy_r=17, wood="oak", branches=8)
    cv.chest_ring(m, 4, 13, 45)
    greenery(m, spacing=9, margin=8, tmin=0.42)
    cv.clip = False
    return result("Meadow", "meadow", "Grassy oak islands with a giant oak tree in the middle.",
                  cv, (P(12), P(20) + 1, P(30)), "2 spawns, middle, 2 centre-line side islands")


# =======================================================================================
def dunes():
    cv = Canvas(P(81), P(42), P(51), S)
    rng = np.random.default_rng(202)
    th = Theme("sand", "sandstone", [("sandstone", 62), ("cut_sandstone", 16), ("red_sandstone", 12),
                                     ("chiseled_sandstone", 3)], fill_depth=2,
               fill_fn=lambda dd, fd, r: "sand" if dd <= 2 else "sandstone")

    def ruin_pillar(x, y, z):
        h = int(rng.integers(2, 7))
        for dy in range(h):
            cv.set(x, y + dy, z, "cut_sandstone" if dy % 3 else "sandstone")
        cv.set(x, y + h, z, "chiseled_sandstone" if rng.random() < 0.6 else "sandstone_slab")

    def desert(isl, margin=2, tmin=0.15):
        cv.forest(isl, rng, lambda x, y, z: cactus(cv, x, y, z, rng), 6, tmin=tmin, tmax=0.85, margin=margin,
                  density=0.6, on={"sand"})
        cv.scatter(isl, rng, [("dead_bush", 1)], 0.025, on={"sand"}, margin=margin)
        cv.forest(isl, rng, ruin_pillar, 16, tmin=tmin, tmax=0.75, margin=margin, limit=4, on={"sand"})

    spawn_island(cv, th, P(12), P(25), P(20), 5.6 * S, 9 * S, 2001, [(-4, -4), (-4, 4), (5, 0)],
                 lambda i: desert(i))

    rk = cv.island(P(27), P(11), P(18), 3.0 * S, 5 * S, th, 2003, "rock")
    cv.chest(rk, P(27), P(11))
    desert(rk)

    cv.clip = True
    top = P(22)
    m = cv.island(cv.cx, cv.cz, top, 10.2 * S, 14 * S, th, 2002, "mid", sym=True, hill=1.4 * S,
                  flat=[(cv.cx, cv.cz, 30)])
    cx, cz = cv.cx, cv.cz
    for lvl in range(21):  # stepped pyramid, 41 wide and 21 high
        half = 20 - lvl
        y = top + 1 + lvl
        for dx in range(-half, half + 1):
            for dz in range(-half, half + 1):
                edge = max(abs(dx), abs(dz)) == half
                name = "sandstone"
                if edge:
                    name = "chiseled_sandstone" if lvl % 5 == 4 else "cut_sandstone"
                cv.set(cx + dx, y, cz + dz, name)
    cv.set(cx, top + 22, cz, "chiseled_sandstone")
    cv.chest_ring(m, 4, 25, 0)
    desert(m, margin=4, tmin=0.62)
    cv.clip = False
    return result("Dunes", "dunes", "Sandstone desert islands around a big stepped pyramid.",
                  cv, (P(12), P(20) + 1, P(25)), "2 spawns, pyramid middle, 2 rocks")


# =======================================================================================
def frostbite():
    cv = Canvas(P(81), P(46), P(55), S)
    rng = np.random.default_rng(303)
    th = Theme("snow_block", "snow_block", [("stone", 45), ("packed_ice", 25), ("andesite", 15), ("ice", 15)],
               fill_depth=1)

    def tree(x, y, z):
        if rng.random() < 0.12:
            mega_spruce(cv, x, y, z, rng, snowy=True)
        else:
            spruce_tree(cv, x, y, z, rng, snowy=True)

    spawn_island(cv, th, P(12), P(27), P(20), 5.6 * S, 9 * S, 3001, [(-4, -5), (-5, 3), (4, -4)],
                 lambda i: cv.forest(i, rng, tree, 8, tmin=0.2, tmax=0.85))

    for i, (x, z) in enumerate(((P(25), P(11)), (P(25), P(43)))):
        rk = cv.island(x, z, P(18), 2.8 * S, 5 * S, th, 3010 + i, "rock")
        cv.chest(rk, x, z)
        cv.spike(x + 4, rk.surface(x + 4, z - 3) + 1, z - 3, 2.2, 10, "packed_ice")

    cv.clip = True
    top = P(22)
    m = cv.island(cv.cx, cv.cz, top, 9.4 * S, 13 * S, th, 3002, "mid", sym=True, hill=1.0 * S,
                  flat=[(cv.cx, cv.cz, 14)])
    cv.spike(cv.cx, top + 1, cv.cz, 9.5, 72, "packed_ice", power=1.35)
    for (dx, dz, r0, h) in ((-17, -6, 3.5, 24), (-13, 13, 2.6, 16), (-24, 4, 2.0, 12)):
        cv.spike(cv.cx + dx, m.surface(cv.cx + dx, cv.cz + dz) + 1, cv.cz + dz, r0, h, "packed_ice", power=1.2)
    cv.chest_ring(m, 4, 15, 45)
    cv.forest(m, rng, tree, 8, tmin=0.45, tmax=0.86, margin=6)
    cv.clip = False
    return result("Frostbite", "frostbite", "Snowy spruce forests and a towering packed-ice spike.",
                  cv, (P(12), P(20) + 1, P(27)), "2 spawns, middle, 4 ice rocks")


# =======================================================================================
def inferno():
    cv = Canvas(P(81), P(44), P(55), S)
    rng = np.random.default_rng(404)
    th = Theme("netherrack", "netherrack", [("netherrack", 86), ("nether_quartz_ore", 6), ("soul_sand", 4),
                                             ("nether_bricks", 4)], fill_depth=2,
               top_fn=lambda tn, r, t: "soul_sand" if tn > 0.66 else "netherrack",
               bottom=lambda r, t: "glowstone" if r.random() < 0.12 else None)

    def lamp(x, y, z, h=3):
        for dy in range(h):
            cv.set(x, y + dy, z, "nether_brick_fence")
        cv.set(x, y + h, z, "glowstone")

    def rack_spike(x, y, z):
        cv.spike(x, y, z, rng.uniform(1.2, 2.6), int(rng.integers(5, 12)), "netherrack", power=1.1)

    def hellscape(isl, margin=3, tmin=0.2):
        cv.forest(isl, rng, rack_spike, 11, tmin=tmin, tmax=0.85, margin=margin, density=0.7)
        cv.forest(isl, rng, lambda x, y, z: lamp(x, y, z), 14, tmin=tmin, tmax=0.7, margin=margin, limit=4)

    spawn_island(cv, th, P(12), P(27), P(20), 5.6 * S, 9 * S, 4001, [(-4, -4), (-4, 4), (4, 5)],
                 lambda i: hellscape(i))

    sx, sz = P(26), P(12)
    s = cv.island(sx, sz, P(19), 4.3 * S, 7 * S, th, 4003, "side")
    cv.chest(s, sx - 5, sz)
    cv.chest(s, sx + 3, sz - 5)
    hellscape(s)

    cv.clip = True
    top = P(22)
    m = cv.island(cv.cx, cv.cz, top, 9.6 * S, 14 * S, th, 4002, "mid", sym=True, hill=1.0 * S,
                  flat=[(cv.cx, cv.cz, 20)])
    cx, cz, y0, H = cv.cx, cv.cz, top + 1, 32
    cv.box(cx - 7, top, cz - 7, cx + 7, top, cz + 7, "nether_bricks")  # floor
    for y in range(y0, y0 + H):
        square_ring(cv, cx, y, cz, 7, "nether_bricks")
    for (px, pz) in ((-7, -7), (-7, 7), (7, -7), (7, 7)):  # corner buttresses
        cv.box(cx + px - 1, y0, cz + pz - 1, cx + px + 1, y0 + H + 2, cz + pz + 1, "nether_bricks")
    for (dx, dz) in ((0, -7), (0, 7), (-7, 0), (7, 0)):
        ax, az = (1, 0) if dz else (0, 1)
        for w in (-1, 0, 1):  # 3-wide, 5-high doorways
            for dy in range(5):
                cv.set(cx + dx + ax * w, y0 + dy, cz + dz + az * w, "air")
        for wy in (y0 + 10, y0 + 18, y0 + 26):  # fence windows
            for w in (-1, 0, 1):
                for dy in range(2):
                    cv.set(cx + dx + ax * w, wy + dy, cz + dz + az * w, "nether_brick_fence")
    cv.box(cx - 7, y0 + H, cz - 7, cx + 7, y0 + H, cz + 7, "nether_bricks")  # roof
    for dx in range(-7, 8):
        for dz in range(-7, 8):
            if max(abs(dx), abs(dz)) == 7 and (dx + dz) % 2 == 0:
                cv.set(cx + dx, y0 + H + 1, cz + dz, "nether_bricks")
    cv.set(cx, y0 + H + 1, cz, "glowstone")
    for dy in range(1, 7):  # chandelier
        cv.set(cx, y0 + H - dy, cz, "nether_brick_fence")
    cv.box(cx - 1, y0 + H - 8, cz - 1, cx + 1, y0 + H - 7, cz + 1, "glowstone")
    cv.chest(m, cx - 5, cz - 5, "south")
    cv.chest_ring(m, 4, 17, 45)
    hellscape(m, margin=4, tmin=0.45)
    cv.clip = False
    return result("Inferno", "inferno", "Netherrack and soul sand around a tall nether-brick tower.",
                  cv, (P(12), P(20) + 1, P(27)), "2 spawns, tower middle, 2 personal side islands")


# =======================================================================================
def the_end():
    cv = Canvas(P(81), P(44), P(55), S)
    rng = np.random.default_rng(505)
    th = Theme("end_stone", "end_stone", [("end_stone", 92), ("obsidian", 8)], fill_depth=2)

    def pillar(x, y, z, h, r=1.5, cage=False):
        cv.cylinder(x, y, z, r, h, "obsidian")
        if cage:
            half = int(math.ceil(r)) + 2
            for dy in range(5):
                for dx in range(-half, half + 1):
                    for dz in range(-half, half + 1):
                        edge = max(abs(dx), abs(dz)) == half
                        bar = abs(dx) == half and abs(dz) == half or (dx + dz) % 2 == 0
                        if dy == 4 or (edge and (dy == 0 or bar)):
                            cv.set(x + dx, y + h + dy, z + dz, "purple_stained_glass")
            cv.set(x, y + h + 2, z, "magenta_stained_glass")
            cv.cylinder(x, y + h, z, r, 1, "obsidian")
        else:
            cv.disk(x, y + h, z, r, "purple_stained_glass")

    def rubble(isl, margin=3, tmin=0.25):
        cv.forest(isl, rng, lambda x, y, z: boulder(cv, x, y, z, rng, "end_stone", rng.uniform(1.2, 2.4)), 12,
                  tmin=tmin, tmax=0.85, margin=margin, density=0.6)

    def sdecor(i):
        pillar(i.cx - 8, i.top + 1, i.cz + 3, 12)
        rubble(i)

    spawn_island(cv, th, P(12), P(27), P(20), 5.6 * S, 9 * S, 5001, [(-4, -4), (-4, 4), (5, -2)], sdecor)

    n = cv.island(cv.cx, P(8), P(19), 4.3 * S, 7 * S, th, 5003, "side")
    cv.chest(n, cv.cx - 5, P(8))
    cv.chest(n, cv.cx + 5, P(8))
    pillar(cv.cx, n.surface(cv.cx, P(8) - 5) + 1, P(8) - 5, 10)
    rubble(n)

    cv.clip = True
    top = P(22)
    m = cv.island(cv.cx, cv.cz, top, 9.2 * S, 14 * S, th, 5002, "mid", sym=True, hill=0.9 * S,
                  flat=[(cv.cx, cv.cz, 12)])
    pillar(cv.cx, top + 1, cv.cz, 44, r=4.2, cage=True)
    for i in range(6):
        ang = math.radians(60 * i)
        px, pz = cv.cx + int(round(24 * math.cos(ang))), cv.cz + int(round(24 * math.sin(ang)))
        h = (18, 26, 22)[i % 3]
        pillar(px, m.surface(px, pz) + 1, pz, h, r=2.2, cage=True)
    cv.chest_ring(m, 6, 13, 30)
    rubble(m, margin=5, tmin=0.6)
    cv.clip = False
    return result("The End", "the-end", "End stone islands with obsidian pillars capped by purple glass cages.",
                  cv, (P(12), P(20) + 1, P(27)), "2 spawns, pillar middle, 2 centre-line side islands")


# =======================================================================================
def atlantis():
    cv = Canvas(P(81), P(42), P(61), S)
    rng = np.random.default_rng(606)
    th = Theme("prismarine_bricks", "prismarine",
               [("prismarine", 50), ("dark_prismarine", 30), ("prismarine_bricks", 20)], fill_depth=2,
               top_fn=lambda tn, r, t: "prismarine_bricks" if tn > 0.42 else "prismarine",
               bottom=lambda r, t: "sea_lantern" if r.random() < 0.07 else None)

    def post(x, y, z, h=3):
        for dy in range(h):
            cv.set(x, y + dy, z, "dark_prismarine")
        cv.set(x, y + h, z, "sea_lantern")

    def arch(x, y, z):
        w = 3 if rng.random() < 0.5 else 0
        for dy in range(5):
            cv.set(x, y + dy, z, "prismarine_bricks")
            cv.set(x + w, y + dy, z + (3 - w), "prismarine_bricks")
        cv.line((x, y + 5, z), (x + w, y + 5, z + (3 - w)), "dark_prismarine")

    def reef(isl, margin=3, tmin=0.2):
        cv.forest(isl, rng, lambda x, y, z: post(x, y, z, int(rng.integers(2, 5))), 12, tmin=tmin, tmax=0.85,
                  margin=margin, density=0.7)
        cv.forest(isl, rng, arch, 22, tmin=tmin, tmax=0.7, margin=margin + 4, limit=2)

    spawn_island(cv, th, P(12), P(30), P(20), 5.6 * S, 9 * S, 6001, [(-4, -5), (-4, 5), (5, -2)],
                 lambda i: reef(i))

    n = cv.island(cv.cx, P(9), P(19), 4.5 * S, 7 * S, th, 6003, "side")
    cv.chest(n, cv.cx - 5, P(9) + 1)
    cv.chest(n, cv.cx + 5, P(9) + 1)
    reef(n)

    cv.clip = True
    top = P(22)
    m = cv.island(cv.cx, cv.cz, top, 10.0 * S, 14 * S, th, 6002, "mid", sym=True, hill=0.8 * S,
                  flat=[(cv.cx, cv.cz, 30)])
    cx, cz, y = cv.cx, cv.cz, top
    cv.box(cx - 20, y, cz - 20, cx + 20, y, cz + 20, "dark_prismarine")
    square_ring(cv, cx, y, cz, 20, "prismarine_bricks", thick=2)
    cv.set(cx, y, cz, "sea_lantern")
    for px in (-17, 0, 17):
        for pz in (-17, 0, 17):
            if px == 0 and pz == 0:
                continue
            cv.box(cx + px - 1, y + 1, cz + pz - 1, cx + px + 1, y + 14, cz + pz + 1, "dark_prismarine")
            cv.set(cx + px, y + 7, cz + pz, "sea_lantern")
    cv.box(cx - 20, y + 15, cz - 20, cx + 20, y + 15, cz + 20, "prismarine_bricks")
    for gx in range(-18, 19, 6):
        for gz in range(-18, 19, 6):
            cv.set(cx + gx, y + 15, cz + gz, "sea_lantern")
    cv.box(cx - 13, y + 16, cz - 13, cx + 13, y + 17, cz + 13, "dark_prismarine")
    cv.box(cx - 7, y + 18, cz - 7, cx + 7, y + 19, cz + 7, "prismarine_bricks")
    cv.box(cx - 1, y + 20, cz - 1, cx + 1, y + 21, cz + 1, "sea_lantern")
    cv.chest_ring(m, 4, 7, 0)
    cv.chest_ring(m, 2, 30, 90)
    reef(m, margin=5, tmin=0.66)
    cv.clip = False
    return result("Atlantis", "atlantis", "Prismarine islands with sea lanterns and a huge pillared temple.",
                  cv, (P(12), P(20) + 1, P(30)), "2 spawns, temple middle, 2 centre-line side islands")


# =======================================================================================
def fungal():
    cv = Canvas(P(81), P(44), P(51), S)
    rng = np.random.default_rng(707)
    th = Theme("mycelium", "dirt", [("stone", 60), ("andesite", 15), ("granite", 10), ("cobblestone", 15)],
               fill_depth=2)
    shrooms = [("red_mushroom", 1), ("brown_mushroom", 1)]

    def huge(x, y, z):
        if rng.random() < 0.55:
            red_mushroom_tree(cv, x, y, z, rng)
        else:
            brown_mushroom_tree(cv, x, y, z, rng)

    def grove(isl, spacing=9, margin=3, tmin=0.2):
        cv.forest(isl, rng, huge, spacing, tmin=tmin, tmax=0.84, margin=margin)
        cv.scatter(isl, rng, shrooms, 0.06, on={"mycelium"}, margin=margin)

    spawn_island(cv, th, P(12), P(25), P(20), 5.6 * S, 9 * S, 7001, [(-4, -4), (2, 5), (5, -2)],
                 lambda i: grove(i))

    rk = cv.island(P(27), P(10), P(18), 3.2 * S, 6 * S, th, 7003, "rock")
    cv.chest(rk, P(27), P(10))
    grove(rk, spacing=8)

    cv.clip = True
    top = P(22)
    m = cv.island(cv.cx, cv.cz, top, 10.0 * S, 14 * S, th, 7002, "mid", sym=True, hill=1.1 * S,
                  flat=[(cv.cx, cv.cz, 12)])
    cx, cz = cv.cx, cv.cz
    cv.cylinder(cx, top + 1, cz, 3.2, 34, "mushroom_stem")
    cv.disk(cx, top + 34, cz, 20, "brown_mushroom_block", hollow=17.5)
    cv.disk(cx, top + 35, cz, 18, "brown_mushroom_block")
    cv.disk(cx, top + 36, cz, 13, "brown_mushroom_block")

    def giant_red(x, z, h, r):
        y = m.surface(x, z) + 1
        cv.cylinder(x, y, z, 1.6, h, "mushroom_stem")
        for dy in range(6):
            rad = r * math.sqrt(max(0.0, 1 - (dy / 6.0) ** 2))
            cv.disk(x, y + h - 1 + dy, z, rad, "red_mushroom_block", hollow=rad - 1.5 if dy == 0 else None)

    giant_red(cx - 26, cz - 9, 20, 8.5)
    giant_red(cx - 17, cz + 19, 15, 7)
    cv.chest_ring(m, 4, 11, 45)
    grove(m, spacing=10, margin=6, tmin=0.5)
    cv.clip = False
    return result("Fungal", "fungal", "Mycelium islands under giant red and brown mushrooms.",
                  cv, (P(12), P(20) + 1, P(25)), "2 spawns, giant mushroom middle, 2 rocks")


# =======================================================================================
def jungle():
    cv = Canvas(P(81), P(46), P(61), S)
    rng = np.random.default_rng(808)
    th = Theme("grass_block", "dirt", [("stone", 50), ("mossy_cobblestone", 25), ("cobblestone", 15),
                                       ("andesite", 10)],
               top_fn=lambda tn, r, t: "podzol" if tn > 0.68 else "grass_block")
    mossy = [("mossy_cobblestone", 3), ("mossy_stone_bricks", 3), ("cobblestone", 2), ("cracked_stone_bricks", 1),
             ("stone_bricks", 2)]

    def tree(x, y, z):
        roll = rng.random()
        if roll < 0.2:
            mega_jungle(cv, x, y, z, rng)
        elif roll < 0.6:
            jungle_tree(cv, x, y, z, rng)
        else:
            bush(cv, x, y, z, rng, "jungle" if rng.random() < 0.7 else "oak")

    def jungle_floor(isl, spacing=7, margin=3, tmin=0.15):
        cv.forest(isl, rng, tree, spacing, tmin=tmin, tmax=0.86, margin=margin)
        cv.scatter(isl, rng, [("fern", 4), ("blue_orchid", 1), ("poppy", 1)], 0.22, on={"grass_block", "podzol"},
                   margin=margin)

    spawn_island(cv, th, P(12), P(30), P(20), 5.6 * S, 9 * S, 8001, [(-3, -5), (-5, 4), (5, 3)],
                 lambda i: jungle_floor(i))

    sx, sz = P(26), P(14)
    s = cv.island(sx, sz, P(19), 4.6 * S, 7 * S, th, 8003, "side")
    cv.chest(s, sx - 5, sz)
    cv.chest(s, sx + 3, sz + 4)
    jungle_floor(s)

    cv.clip = True
    top = P(22)
    m = cv.island(cv.cx, cv.cz, top, 10.2 * S, 14 * S, th, 8002, "mid", sym=True, hill=1.0 * S,
                  flat=[(cv.cx, cv.cz, 24)])
    cx, cz, y0 = cv.cx, cv.cz, top + 1
    cv.box(cx - 15, top, cz - 15, cx + 15, top, cz + 15, "stone_bricks")
    for y in range(y0, y0 + 7):  # hollow first tier
        for dx in range(-15, 16):
            for dz in range(-15, 16):
                if max(abs(dx), abs(dz)) == 15:
                    cv.set(cx + dx, y, cz + dz, pick(rng, mossy))
    for dz in (-15, 15):  # doorways north/south
        for w in (-1, 0, 1):
            for dy in range(4):
                cv.set(cx + w, y0 + dy, cz + dz, "air")
    for dx in (-15, 15):  # windows east/west
        for wz in (-8, 0, 8):
            for dy in (2, 3):
                cv.set(cx + dx, y0 + dy, cz + wz, "air")
    for (px, pz) in ((-7, -7), (-7, 7), (7, -7), (7, 7)):  # inner pillars with lamps
        cv.box(cx + px, y0, cz + pz, cx + px, y0 + 6, cz + pz, "chiseled_stone_bricks")
        cv.set(cx + px, y0 + 5, cz + pz, "glowstone")
    cv.box(cx - 15, y0 + 7, cz - 15, cx + 15, y0 + 7, cz + 15, "mossy_stone_bricks")
    for base, half, h in ((y0 + 8, 11, 4), (y0 + 12, 7, 3)):
        for y in range(base, base + h):
            for dx in range(-half, half + 1):
                for dz in range(-half, half + 1):
                    cv.set(cx + dx, y, cz + dz, pick(rng, mossy))
    for y in range(y0 + 15, y0 + 18):  # shrine
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if max(abs(dx), abs(dz)) == 3 and ((abs(dx) == 3 and abs(dz) == 3) or y == y0 + 17):
                    cv.set(cx + dx, y, cz + dz, "chiseled_stone_bricks")
    cv.set(cx, y0 + 15, cz, "glowstone")
    cv.chest(m, cx - 10, cz, "east")
    cv.chest_ring(m, 4, 24, 45)
    jungle_floor(m, spacing=8, margin=6, tmin=0.5)
    cv.clip = False
    return result("Jungle", "jungle", "Dense jungle with giant trees around a mossy stone temple.",
                  cv, (P(12), P(20) + 1, P(30)), "2 spawns, temple middle, 2 personal side islands")


# =======================================================================================
def crystal():
    cv = Canvas(P(81), P(44), P(55), S)
    rng = np.random.default_rng(909)
    glass = [("light_blue_stained_glass", 4), ("purple_stained_glass", 2), ("magenta_stained_glass", 1),
             ("white_stained_glass", 1)]
    th = Theme("quartz_block", "quartz_block", [("diorite", 45), ("stone", 25), ("polished_andesite", 10),
                                                ("quartz_block", 20)], fill_depth=1,
               top_fn=lambda tn, r, t: "chiseled_quartz_block" if tn > 0.78 else "quartz_block",
               bottom=lambda r, t: pick(r, glass) if r.random() < 0.1 else None)

    def cluster(x, y, z, big=1.0):
        cv.disk(x, y - 1, z, 2.2 * big, "quartz_pillar")
        cv.spike(x, y, z, 1.6 * big, int(rng.integers(9, 15) * big), "light_blue_stained_glass", power=0.9)
        for i in range(int(rng.integers(3, 6))):
            ang = rng.uniform(0, 2 * math.pi)
            ox, oz = int(round(math.cos(ang) * 2.5 * big)), int(round(math.sin(ang) * 2.5 * big))
            cv.spike(x + ox, y, z + oz, rng.uniform(0.8, 1.4) * big, int(rng.integers(4, 10) * big),
                     pick(rng, glass), power=0.9, lean=(math.cos(ang) * 0.12, math.sin(ang) * 0.12))

    def crystals(isl, spacing=13, margin=4, tmin=0.25, limit=10 ** 6):
        cv.forest(isl, rng, lambda x, y, z: cluster(x, y, z, rng.uniform(0.8, 1.2)), spacing, tmin=tmin,
                  tmax=0.8, margin=margin, limit=limit)

    spawn_island(cv, th, P(11), P(27), P(20), 5.6 * S, 9 * S, 9001, [(-4, -4), (-4, 4), (5, 3)],
                 lambda i: crystals(i))

    tx, tz = P(30), P(16)
    a = cv.island(tx, tz, P(21), 6.0 * S, 10 * S, th, 9003, "twin")
    cv.chest(a, tx - 6, tz + 5)
    cv.chest(a, tx + 6, tz - 5)
    crystals(a)

    cv.clip = True
    top = P(22)
    c = cv.island(cv.cx, cv.cz, top, 3.9 * S, 8 * S, th, 9002, "mid", sym=True, hill=0.0, flat=[(cv.cx, cv.cz, 6)])
    cx, cz = cv.cx, cv.cz
    cv.disk(cx, top, cz, 5, "chiseled_quartz_block")
    cv.spike(cx, top + 1, cz, 4.2, 38, "light_blue_stained_glass", power=0.85)
    for i in range(6):
        ang = math.radians(60 * i + 15)
        ox, oz = int(round(math.cos(ang) * 4)), int(round(math.sin(ang) * 4))
        name = ("purple_stained_glass", "magenta_stained_glass", "white_stained_glass")[i % 3]
        cv.spike(cx + ox, top + 1, cz + oz, 2.0, (16, 24, 20)[i % 3], name, power=0.9,
                 lean=(math.cos(ang) * 0.18, math.sin(ang) * 0.18))
    cv.chest_ring(c, 2, 10, 270)
    cv.clip = False
    return result("Crystal", "crystal", "White quartz islands with glass crystal spires and crystal drips.",
                  cv, (P(11), P(20) + 1, P(27)), "2 spawns, 2 twin islands, crystal spire centre island")


# =======================================================================================
def volcano():
    cv = Canvas(P(85), P(46), P(55), S)
    rng = np.random.default_rng(1010)

    def vtop(tn, r, t):
        if tn < 0.36:
            return "stone"
        if tn < 0.66:
            return "coarse_dirt"
        return "gravel"

    th = Theme("stone", "stone", [("stone", 55), ("cobblestone", 25), ("andesite", 12), ("obsidian", 8)],
               fill_depth=2, top_fn=vtop)

    def rocks(isl, margin=3, tmin=0.2):
        cv.forest(isl, rng, lambda x, y, z: boulder(cv, x, y, z, rng,
                                                    pick(rng, [("cobblestone", 3), ("andesite", 2), ("obsidian", 1)]),
                                                    rng.uniform(1.2, 2.6)),
                  10, tmin=tmin, tmax=0.85, margin=margin, density=0.7)
        cv.scatter(isl, rng, [("dead_bush", 1)], 0.05, on={"coarse_dirt"}, margin=margin)

    spawn_island(cv, th, P(12), P(27), P(20), 5.6 * S, 9 * S, 10001, [(-4, -5), (-4, 5), (5, -3)],
                 lambda i: rocks(i))

    sx, sz = P(26), P(11)
    s = cv.island(sx, sz, P(19), 4.4 * S, 7 * S, th, 10003, "side")
    cv.chest(s, sx - 5, sz + 4)
    cv.chest(s, sx + 5, sz - 2)
    rocks(s)

    cv.clip = True
    top = P(22)
    m = cv.island(cv.cx, cv.cz, top, 11.0 * S, 15 * S, th, 10002, "mid", sym=True, hill=0.6 * S,
                  flat=[(cv.cx, cv.cz, 36)])
    cx, cz = cv.cx, cv.cz
    cone = [("stone", 40), ("cobblestone", 30), ("andesite", 18)]
    streak = Noise2(1777, 1.0)
    for dx in range(-34, 35):
        for dz in range(-34, 35):
            d = math.hypot(dx, dz)
            if d > 33:
                continue
            if d <= 8.6:
                h = 28  # crater floor; the lava lake sits on it
            elif d <= 12:
                h = 37  # rim
            else:
                h = int(round(37 * ((33 - d) / 21.0) ** 1.15))
            ang = math.atan2(dz, dx)
            dark = (0.5 * (streak(ang * 6, 0) + streak(ang * 6 + 40, 3))) > 0.62 and d < 26
            for yy in range(top + 1, top + h + 1):
                if dark or (d <= 12 and yy > top + h - 6):
                    name = "obsidian"
                else:
                    name = pick(rng, cone)
                cv.set(cx + dx, yy, cz + dz, name)
            if d <= 8.6:
                cv.set(cx + dx, top + h + 1, cz + dz, "lava")
    cv.chest_ring(m, 4, 42, 45)
    rocks(m, margin=5, tmin=0.66)
    cv.clip = False
    return result("Volcano", "volcano", "Rocky islands around a huge volcano with a sealed lava lake.",
                  cv, (P(12), P(20) + 1, P(27)), "2 spawns, volcano middle, 2 personal side islands")


# =======================================================================================
def candy():
    cv = Canvas(P(81), P(44), P(61), S)
    rng = np.random.default_rng(1111)
    sprinkle = [("lime_wool", 1), ("light_blue_wool", 1), ("yellow_wool", 1), ("orange_wool", 1),
                ("magenta_wool", 1), ("red_wool", 1)]
    gum = ["lime_wool", "orange_wool", "magenta_wool", "yellow_wool", "light_blue_wool", "red_wool"]

    def ctop(tn, r, t):
        if r.random() < 0.04:
            return pick(r, sprinkle)
        return "white_terracotta" if tn > 0.52 else "pink_terracotta"

    th = Theme("pink_terracotta", "brown_terracotta", "brown_terracotta", fill_depth=2, top_fn=ctop,
               base_fn=lambda dd, total, r, t, x, y, z: "white_terracotta" if dd % 6 in (4, 5) else "brown_terracotta")

    def lollipop(x, y, z, color=None):
        color = color or gum[int(rng.integers(len(gum)))]
        for dy in range(7):
            cv.set(x, y + dy, z, "birch_fence")
        along_x = rng.random() < 0.5
        cyc = y + 10
        for a in range(-4, 5):
            for b in range(-4, 5):
                d = math.hypot(a, b)
                if d <= 3.6:
                    name = color if int(d + 0.5) % 2 == 0 else "white_wool"
                    if along_x:
                        cv.set(x + a, cyc + b, z, name)
                    else:
                        cv.set(x, cyc + b, z + a, name)

    def candy_cane(x, y, z):
        for dy in range(10):
            cv.set(x, y + dy, z, "red_wool" if (dy // 2) % 2 == 0 else "white_wool")
        for i, (ox, oy) in enumerate(((0, 10), (1, 11), (2, 11), (3, 10), (3, 9))):
            cv.set(x + ox, y + oy, z, "white_wool" if i % 2 else "red_wool")

    def gumdrop(x, y, z):
        c = gum[int(rng.integers(len(gum)))]
        for dy in range(3):
            cv.disk(x, y + dy, z, 2.4 - dy * 0.8, c)

    def treats(isl, margin=3, tmin=0.2, n_pops=3):
        cv.forest(isl, rng, lollipop, 18, tmin=tmin, tmax=0.75, margin=margin + 4, limit=n_pops)
        cv.forest(isl, rng, candy_cane, 16, tmin=tmin, tmax=0.75, margin=margin + 3, limit=2)
        cv.forest(isl, rng, gumdrop, 7, tmin=tmin, tmax=0.85, margin=margin + 2, density=0.6)
        cv.forest(isl, rng, lambda x, y, z: cv.set(x, y, z, "cake"), 9, tmin=tmin, tmax=0.85, margin=margin,
                  density=0.5)

    spawn_island(cv, th, P(12), P(30), P(20), 5.6 * S, 9 * S, 11001, [(-4, -5), (-5, 3), (5, -3)],
                 lambda i: treats(i))

    n = cv.island(cv.cx, P(9), P(19), 4.5 * S, 7 * S, th, 11003, "side")
    cv.chest(n, cv.cx - 5, P(9) + 1)
    cv.chest(n, cv.cx + 5, P(9) + 1)
    treats(n, n_pops=1)

    cv.clip = True
    top = P(22)
    m = cv.island(cv.cx, cv.cz, top, 10.0 * S, 14 * S, th, 11002, "mid", sym=True, hill=0.9 * S,
                  flat=[(cv.cx, cv.cz, 24)])
    cx, cz = cv.cx, cv.cz
    for dy in range(15):  # striped liner, flaring outwards
        rad = 14 + dy * 0.18
        for dx in range(-18, 19):
            for dz in range(-18, 19):
                d = math.hypot(dx, dz)
                if d <= rad:
                    stripe = int((math.atan2(dz, dx) + math.pi) / (2 * math.pi) * 24) % 2
                    cv.set(cx + dx, top + 1 + dy, cz + dz, "pink_wool" if stripe else "white_wool")
    base = top + 16
    for dy in range(15):  # swirled frosting dome
        rad = 19.0 * math.sqrt(max(0.0, 1 - (dy / 15.0) ** 2))
        for dx in range(-20, 21):
            for dz in range(-20, 21):
                d = math.hypot(dx, dz)
                if d <= rad:
                    sw = (math.atan2(dz, dx) * 2 + dy * 0.45) % (2 * math.pi) < math.pi
                    name = "white_wool" if sw else "pink_wool"
                    if rng.random() < 0.035:
                        name = pick(rng, sprinkle)
                    cv.set(cx + dx, base + dy, cz + dz, name)
    cv.blob(cx, base + 17, cz, 3.2, 3.2, 3.2, "red_wool", replace=True)
    for dy in range(3):
        cv.set(cx, base + 21 + dy, cz, "oak_fence")
    cv.chest_ring(m, 4, 24, 45)
    treats(m, margin=5, tmin=0.6, n_pops=2)
    cv.clip = False
    return result("Candy", "candy", "Frosted islands with lollipops, candy canes and a giant cupcake.",
                  cv, (P(12), P(20) + 1, P(30)), "2 spawns, cupcake middle, 2 centre-line side islands")


# =======================================================================================
def castle():
    cv = Canvas(P(81), P(44), P(55), S)
    rng = np.random.default_rng(1212)
    bricks = [("stone_bricks", 5), ("mossy_stone_bricks", 2), ("cracked_stone_bricks", 2)]
    th = Theme("grass_block", "dirt", [("stone_bricks", 35), ("cobblestone", 25), ("mossy_cobblestone", 15),
                                       ("stone", 15), ("cracked_stone_bricks", 10)], fill_depth=2)

    def ruins(isl, margin=3, tmin=0.2):
        cv.forest(isl, rng, lambda x, y, z: oak_tree(cv, x, y, z, rng), 11, tmin=tmin, tmax=0.85, margin=margin,
                  density=0.6)
        cv.scatter(isl, rng, FLOWERS, 0.05, on={"grass_block"}, margin=margin)

    def broken_tower(x, z, isl, half=3, hmin=6, hmax=11):
        base = isl.surface(x, z)
        for dx in range(-half, half + 1):
            for dz in range(-half, half + 1):
                if max(abs(dx), abs(dz)) != half:
                    continue
                hh = 0 if (dz == 0 and dx == half) else int(rng.integers(hmin, hmax + 1))  # doorway gap
                for dy in range(hh):
                    cv.set(x + dx, base + 1 + dy, z + dz, pick(rng, bricks))

    def sdecor(i):
        broken_tower(i.cx - 12, i.cz + 4, i)
        wx = i.cx - 9
        for dz in range(-10, -2):
            b = i.surface(wx, i.cz + dz)
            if b is None:
                continue
            for dy in range(int(rng.integers(1, 5))):
                cv.set(wx, b + 1 + dy, i.cz + dz, pick(rng, bricks))
        ruins(i)

    spawn_island(cv, th, P(12), P(27), P(20), 5.6 * S, 9 * S, 12001, [(-4, -4), (-4, 4), (5, 0)], sdecor)

    sx, sz = P(26), P(12)
    s = cv.island(sx, sz, P(19), 4.6 * S, 7 * S, th, 12003, "side")
    ty = s.surface(sx + 2, sz - 2)
    for dy in range(16):  # ruined round tower
        for dx in range(-5, 6):
            for dz in range(-5, 6):
                d = math.hypot(dx, dz)
                if 3.6 <= d <= 4.6:
                    if dy > 9 and rng.random() < (dy - 9) / 8.0:
                        continue
                    if dy < 3 and dx == 4 and abs(dz) <= 1:
                        continue
                    cv.set(sx + 2 + dx, ty + 1 + dy, sz - 2 + dz, pick(rng, bricks))
    cv.chest(s, sx - 6, sz + 3)
    cv.chest(s, sx + 4, sz + 7)
    ruins(s)

    cv.clip = True
    top = P(22)
    m = cv.island(cv.cx, cv.cz, top, 10.0 * S, 14 * S, th, 12002, "mid", sym=True, hill=0.9 * S,
                  flat=[(cv.cx, cv.cz, 31)])
    cx, cz, y0 = cv.cx, cv.cz, top + 1
    for y in range(y0, y0 + 12):  # curtain wall, 2 thick
        for dx in range(-21, 22):
            for dz in range(-21, 22):
                if max(abs(dx), abs(dz)) >= 20:
                    cv.set(cx + dx, y, cz + dz, pick(rng, bricks))
    for dx in range(-21, 22):
        for dz in range(-21, 22):
            if max(abs(dx), abs(dz)) == 21 and (dx + dz) % 2 == 0:
                cv.set(cx + dx, y0 + 12, cz + dz, "stone_bricks")
    for (px, pz) in ((-21, -21), (-21, 21), (21, -21), (21, 21)):  # corner towers
        cv.cylinder(cx + px, y0, cz + pz, 5.2, 18, "stone_bricks")
        for dx in range(-6, 7):
            for dz in range(-6, 7):
                d = math.hypot(dx, dz)
                if 4.4 <= d <= 5.4 and (dx + dz) % 2 == 0:
                    cv.set(cx + px + dx, y0 + 18, cz + pz + dz, "stone_bricks")
    for dz in (-21, -20, 20, 21):  # gates north and south
        for w in range(-2, 3):
            for dy in range(7):
                cv.set(cx + w, y0 + dy, cz + dz, "air")
    for dz in range(-19, 20):  # cobblestone road
        for w in (-1, 0, 1):
            if abs(dz) > 8:
                cv.set(cx + w, top, cz + dz, "cobblestone")
    for y in range(y0, y0 + 24):  # keep
        square_ring(cv, cx, y, cz, 8, "stone_bricks")
    for dx in range(-8, 9):
        for dz in range(-8, 9):
            if max(abs(dx), abs(dz)) == 8 and (dx + dz) % 2 == 0:
                cv.set(cx + dx, y0 + 24, cz + dz, "stone_bricks")
    for wy in (y0 + 6, y0 + 12, y0 + 18):
        for k in (-4, 0, 4):
            for (dx, dz) in ((k, -8), (k, 8), (-8, k), (8, k)):
                cv.set(cx + dx, wy, cz + dz, "air")
                cv.set(cx + dx, wy + 1, cz + dz, "air")
    for dz in (-8, 8):
        for w in (-1, 0, 1):
            for dy in range(4):
                cv.set(cx + w, y0 + dy, cz + dz, "air")
    cv.box(cx - 7, top, cz - 7, cx + 7, top, cz + 7, "stone_bricks")
    cv.chest(m, cx - 6, cz - 4, "east")
    cv.chest_ring(m, 4, 15, 45)
    cv.scatter(m, rng, FLOWERS, 0.05, on={"grass_block"}, margin=4)
    cv.forest(m, rng, lambda x, y, z: oak_tree(cv, x, y, z, rng), 12, tmin=0.62, tmax=0.86, margin=6, density=0.7)
    cv.clip = False
    return result("Castle", "castle", "Floating stone-brick ruins around a walled castle with a central keep.",
                  cv, (P(12), P(20) + 1, P(27)), "2 spawns, castle middle, 2 personal side islands")


ALL = [meadow, dunes, frostbite, inferno, the_end, atlantis, fungal, jungle, crystal, volcano, candy, castle]
