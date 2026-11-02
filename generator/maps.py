"""The 12 duel maps. Each builder returns a dict with the canvas and spawn info.

Every map is point-symmetric (180 degree rotation about the centre), so both players
get identical islands, chests and distances.
"""
import math

import numpy as np

from terrain import (Canvas, Theme, boulder, brown_mushroom_tree, cactus, jungle_tree, oak_tree,
                     pick, red_mushroom_tree, spruce_tree)

FLOWERS = [("poppy", 3), ("dandelion", 3), ("oxeye_daisy", 2), ("azure_bluet", 2),
           ("red_tulip", 1), ("orange_tulip", 1), ("allium", 1), ("blue_orchid", 1)]


def spawn_island(cv, th, x, z, top, r, depth, seed, chest_offs, decor=None, hill=0.7, ax=1.0, az=1.0):
    isl = cv.island(x, z, top, r, depth, th, seed, "spawn", flat=[(x, z, 3.7)], hill=hill, ax=ax, az=az)
    cv.reserve(x, z, 1)  # keep a 3x3 pad clear for the spawn cage
    for dx, dz in chest_offs:
        cv.chest(isl, x + dx, z + dz, "in")
    if decor:
        decor(isl)
    # keep a 3x3, 4-high space above the pad free for the spawn cage (trims overhanging leaves)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for dy in range(1, 5):
                cv.set(x + dx, top + dy, z + dz, "air")
    return isl


def result(name, slug, blurb, cv, spawn_xyz, layout):
    return dict(name=name, slug=slug, blurb=blurb, cv=cv, spawn=spawn_xyz, layout=layout)


# =======================================================================================
def meadow():
    cv = Canvas(81, 44, 61)
    rng = np.random.default_rng(101)
    th = Theme("grass_block", "dirt", [("stone", 70), ("andesite", 14), ("cobblestone", 10), ("granite", 6)])

    def sdecor(isl):
        oak_tree(cv, isl.cx - 3, isl.top + 1, isl.cz + 1, rng)
        cv.scatter(isl, rng, FLOWERS, 0.14, on={"grass_block"})

    spawn_island(cv, th, 12, 30, 20, 5.5, 9, 1001, [(-2, -2), (-1, 3), (2, -2)], sdecor)

    # side islands on the centre line (one north, rotation makes the south one)
    n = cv.island(40, 9, 19, 4.6, 7, th, 1003, "side")
    cv.chest(n, 38, 9)
    cv.chest(n, 42, 9)
    oak_tree(cv, 40, n.surface(40, 8) + 1, 8, rng, wood="birch", height=5)
    cv.scatter(n, rng, FLOWERS, 0.2, on={"grass_block"})

    cv.clip = True
    m = cv.island(40, 30, 22, 9.6, 14, th, 1002, "mid", sym=True, hill=1.2, flat=[(40, 30, 3.2)])
    cv.chest_ring(m, 4, 5, 45)
    # big oak in the middle
    for dy in range(8):
        cv.set(40, 23 + dy, 30, "oak_log")
    cv.blob(40, 31, 30, 4.2, 2.6, 4.2, "oak_leaves", rng, ragged=0.35)
    cv.blob(40, 33, 30, 2.6, 1.6, 2.6, "oak_leaves", rng, ragged=0.25)
    cv.place_n(m, rng, 2, lambda x, y, z: oak_tree(cv, x, y, z, rng, wood="birch"), tmin=0.55, tmax=0.85, margin=6)
    cv.scatter(m, rng, FLOWERS, 0.12, on={"grass_block"})
    cv.clip = False
    return result("Meadow", "meadow", "Grassy oak islands with a giant oak in the middle.",
                  cv, (12, 21, 30), "2 spawns, middle, 2 centre-line side islands")


# =======================================================================================
def dunes():
    cv = Canvas(81, 42, 51)
    rng = np.random.default_rng(202)
    th = Theme("sand", "sandstone", [("sandstone", 62), ("cut_sandstone", 16), ("red_sandstone", 12),
                                     ("chiseled_sandstone", 3), ("red_sand", 0)], fill_depth=2)

    def cacti(isl, n, margin=0):
        cv.place_n(isl, rng, n, lambda x, y, z: cactus(cv, x, y, z, rng), tmin=0.2, tmax=0.8, min_dist=3, margin=margin)
        cv.scatter(isl, rng, [("dead_bush", 1)], 0.06, on={"sand"})

    spawn_island(cv, th, 12, 25, 20, 5.6, 9, 2001, [(-2, -2), (-2, 2), (3, 0)], lambda i: cacti(i, 2))

    rock = cv.island(27, 11, 18, 3.0, 5, th, 2003, "rock")
    cv.chest(rock, 27, 11)
    cv.scatter(rock, rng, [("dead_bush", 1)], 0.25, on={"sand"})

    cv.clip = True
    m = cv.island(40, 25, 22, 10.2, 14, th, 2002, "mid", sym=True, hill=1.0, flat=[(40, 25, 5.2)])
    # stepped pyramid
    for lvl, half in enumerate((4, 3, 2, 1, 0)):
        y = 23 + lvl
        for dx in range(-half, half + 1):
            for dz in range(-half, half + 1):
                edge = abs(dx) == half or abs(dz) == half
                cv.set(40 + dx, y, 25 + dz, "cut_sandstone" if edge else "sandstone")
    cv.set(40, 28, 25, "chiseled_sandstone")
    for dx, dz in ((-4, -4), (-4, 4), (4, -4), (4, 4)):
        cv.set(40 + dx, 24, 25 + dz, "chiseled_sandstone")
    cv.chest_ring(m, 4, 6.5, 0)
    cacti(m, 3, margin=6)
    cv.clip = False
    return result("Dunes", "dunes", "Sandstone desert islands around a stepped pyramid.",
                  cv, (12, 21, 25), "2 spawns, middle, 2 rocks")


# =======================================================================================
def frostbite():
    cv = Canvas(81, 46, 55)
    rng = np.random.default_rng(303)
    th = Theme("snow_block", "snow_block", [("stone", 45), ("packed_ice", 25), ("andesite", 15), ("ice", 15)],
               fill_depth=1)

    def sdecor(isl):
        spruce_tree(cv, isl.cx - 3, isl.top + 1, isl.cz - 1, rng, snowy=True)
        spruce_tree(cv, isl.cx - 1, isl.top + 1, isl.cz + 3, rng, height=5, snowy=True)

    spawn_island(cv, th, 12, 27, 20, 5.6, 9, 3001, [(-2, -3), (-3, 2), (2, -2)], sdecor)

    for i, (x, z) in enumerate(((25, 11), (25, 43))):
        rk = cv.island(x, z, 18, 2.8, 5, th, 3010 + i, "rock")
        cv.chest(rk, x, z)

    cv.clip = True
    m = cv.island(40, 27, 22, 9.4, 13, th, 3002, "mid", sym=True, hill=1.0, flat=[(40, 27, 3.0)])
    # ice spike
    for i in range(16):
        rad = 2.3 * (1 - i / 16.0) + 0.2
        cv.disk(40, 23 + i, 27, rad, "packed_ice")
    cv.chest_ring(m, 4, 5.5, 45)
    cv.place_n(m, rng, 2, lambda x, y, z: spruce_tree(cv, x, y, z, rng, snowy=True), tmin=0.5, tmax=0.85, margin=5)
    cv.clip = False
    return result("Frostbite", "frostbite", "Snowy spruce islands, ice veins and a packed-ice spike.",
                  cv, (12, 21, 27), "2 spawns, middle, 4 ice rocks")


# =======================================================================================
def inferno():
    cv = Canvas(81, 44, 55)
    rng = np.random.default_rng(404)
    th = Theme("netherrack", "netherrack", [("netherrack", 86), ("nether_quartz_ore", 6), ("soul_sand", 4),
                                             ("nether_bricks", 4)], fill_depth=2,
               top_fn=lambda tn, r, t: "soul_sand" if tn > 0.66 else "netherrack",
               bottom=lambda r, t: "glowstone" if r.random() < 0.2 else None)

    def lamp(x, y, z, h=2):
        for dy in range(h):
            cv.set(x, y + dy, z, "nether_brick_fence")
        cv.set(x, y + h, z, "glowstone")

    spawn_island(cv, th, 12, 27, 20, 5.6, 9, 4001, [(-2, -2), (-2, 2), (2, 3)],
                 lambda i: lamp(i.cx - 3, i.top + 1, i.cz, 2))

    s = cv.island(26, 12, 19, 4.3, 7, th, 4003, "side")
    cv.chest(s, 25, 12)
    cv.chest(s, 27, 10)
    lamp(27, s.surface(27, 13) + 1, 13, 1)

    cv.clip = True
    m = cv.island(40, 27, 22, 9.6, 14, th, 4002, "mid", sym=True, hill=1.0, flat=[(40, 27, 4.0)])
    # nether brick tower 5x5, 7 high, 4 doorways, fence windows, crenellated roof
    cx, cz, y0 = 40, 27, 23
    for y in range(y0, y0 + 7):
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if abs(dx) == 2 or abs(dz) == 2:
                    cv.set(cx + dx, y, cz + dz, "nether_bricks")
    for (dx, dz) in ((0, -2), (0, 2), (-2, 0), (2, 0)):
        cv.set(cx + dx, y0, cz + dz, "air")
        cv.set(cx + dx, y0 + 1, cz + dz, "air")
        cv.set(cx + dx, y0 + 4, cz + dz, "nether_brick_fence")
    cv.box(cx - 2, y0 + 7, cz - 2, cx + 2, y0 + 7, cz + 2, "nether_bricks")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if (abs(dx) == 2 or abs(dz) == 2) and (dx + dz) % 2 == 0:
                cv.set(cx + dx, y0 + 8, cz + dz, "nether_bricks")
    cv.set(cx, y0 + 8, cz, "glowstone")
    cv.chest(m, cx - 1, cz - 1, "south")
    cv.chest_ring(m, 4, 6.2, 45)
    cv.place_n(m, rng, 1, lambda x, y, z: lamp(x, y, z, 2), tmin=0.5, tmax=0.85, margin=5)
    cv.clip = False
    return result("Inferno", "inferno", "Netherrack and soul sand with a nether-brick tower and glowstone drips.",
                  cv, (12, 21, 27), "2 spawns, middle tower, 2 personal side islands")


# =======================================================================================
def the_end():
    cv = Canvas(81, 44, 55)
    rng = np.random.default_rng(505)
    th = Theme("end_stone", "end_stone", [("end_stone", 92), ("obsidian", 8)], fill_depth=2)

    def pillar(x, y, z, h, w=0):
        for dy in range(h):
            cv.box(x - w, y + dy, z - w, x + w, y + dy, z + w, "obsidian")
        cv.box(x - w, y + h, z - w, x + w, y + h, z + w, "purple_stained_glass")

    spawn_island(cv, th, 12, 27, 20, 5.6, 9, 5001, [(-2, -2), (-2, 2), (3, -1)],
                 lambda i: pillar(i.cx - 3, i.top + 1, i.cz + 1, 3))

    n = cv.island(40, 8, 19, 4.3, 7, th, 5003, "side")
    cv.chest(n, 38, 8)
    cv.chest(n, 42, 8)
    pillar(40, n.surface(40, 7) + 1, 7, 2)

    cv.clip = True
    m = cv.island(40, 27, 22, 9.2, 14, th, 5002, "mid", sym=True, hill=0.9, flat=[(40, 27, 3.0)])
    pillar(40, 23, 27, 9, w=1)
    cv.set(40, 33, 27, "magenta_stained_glass")
    for (dx, dz) in ((-4, 0), (0, -4), (4, 0), (0, 4)):
        pillar(40 + dx, m.surface(40 + dx, 27 + dz) + 1, 27 + dz, 3)
    cv.chest_ring(m, 6, 6.5, 30)
    cv.clip = False
    return result("The End", "the-end", "End stone islands with obsidian pillars and purple crystal caps.",
                  cv, (12, 21, 27), "2 spawns, middle, 2 centre-line side islands")


# =======================================================================================
def atlantis():
    cv = Canvas(81, 42, 61)
    rng = np.random.default_rng(606)
    th = Theme("prismarine_bricks", "prismarine",
               [("prismarine", 50), ("dark_prismarine", 30), ("prismarine_bricks", 20)], fill_depth=2,
               top_fn=lambda tn, r, t: "prismarine_bricks" if tn > 0.42 else "prismarine",
               bottom=lambda r, t: "sea_lantern" if r.random() < 0.09 else None)

    def post(x, y, z, h=2):
        for dy in range(h):
            cv.set(x, y + dy, z, "dark_prismarine")
        cv.set(x, y + h, z, "sea_lantern")

    spawn_island(cv, th, 12, 30, 20, 5.6, 9, 6001, [(-2, -3), (-2, 3), (3, -1)],
                 lambda i: post(i.cx - 3, i.top + 1, i.cz, 2))

    n = cv.island(40, 9, 19, 4.5, 7, th, 6003, "side")
    cv.chest(n, 38, 10)
    cv.chest(n, 42, 10)
    post(40, n.surface(40, 8) + 1, 8, 1)

    cv.clip = True
    m = cv.island(40, 30, 22, 10.0, 14, th, 6002, "mid", sym=True, hill=0.8, flat=[(40, 30, 6.4)])
    cx, cz, y = 40, 30, 22
    cv.box(cx - 4, y, cz - 4, cx + 4, y, cz + 4, "dark_prismarine")
    cv.set(cx, y, cz, "sea_lantern")
    for dx, dz in ((-4, -4), (-4, 4), (4, -4), (4, 4)):
        for dy in range(1, 5):
            cv.set(cx + dx, y + dy, cz + dz, "dark_prismarine")
    cv.box(cx - 4, y + 5, cz - 4, cx + 4, y + 5, cz + 4, "prismarine_bricks")
    cv.box(cx - 1, y + 5, cz - 1, cx + 1, y + 5, cz + 1, "sea_lantern")
    cv.box(cx - 2, y + 6, cz - 2, cx + 2, y + 6, cz + 2, "dark_prismarine")
    cv.set(cx, y + 7, cz, "sea_lantern")
    cv.chest_ring(m, 4, 2, 0)
    cv.chest_ring(m, 2, 7, 90)
    cv.clip = False
    return result("Atlantis", "atlantis", "Prismarine islands with sea lanterns and an open-sided temple.",
                  cv, (12, 21, 30), "2 spawns, middle temple, 2 centre-line side islands")


# =======================================================================================
def fungal():
    cv = Canvas(81, 44, 51)
    rng = np.random.default_rng(707)
    th = Theme("mycelium", "dirt", [("stone", 60), ("andesite", 15), ("granite", 10), ("cobblestone", 15)],
               fill_depth=2)
    shrooms = [("red_mushroom", 1), ("brown_mushroom", 1)]

    def sdecor(isl):
        red_mushroom_tree(cv, isl.cx - 3, isl.top + 1, isl.cz + 2, rng, height=4)
        cv.scatter(isl, rng, shrooms, 0.1, on={"mycelium"})

    spawn_island(cv, th, 12, 25, 20, 5.6, 9, 7001, [(-2, -2), (1, 3), (3, -1)], sdecor)

    rk = cv.island(27, 10, 18, 3.2, 6, th, 7003, "rock")
    cv.chest(rk, 27, 10)
    cv.scatter(rk, rng, shrooms, 0.3, on={"mycelium"})

    cv.clip = True
    m = cv.island(40, 25, 22, 10.0, 14, th, 7002, "mid", sym=True, hill=1.1, flat=[(40, 25, 3.0)])
    for dy in range(8):
        cv.set(40, 23 + dy, 25, "mushroom_stem")
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            d = math.hypot(dx, dz)
            if d <= 4.4:
                cv.set(40 + dx, 31, 25 + dz, "brown_mushroom_block")
            if d <= 2.9:
                cv.set(40 + dx, 32, 25 + dz, "brown_mushroom_block")
    cv.chest_ring(m, 4, 5.5, 45)
    cv.place_n(m, rng, 2, lambda x, y, z: red_mushroom_tree(cv, x, y, z, rng), tmin=0.55, tmax=0.85,
               margin=6, min_dist=5)
    cv.scatter(m, rng, shrooms, 0.08, on={"mycelium"})
    cv.clip = False
    return result("Fungal", "fungal", "Mycelium islands with giant red and brown mushrooms.",
                  cv, (12, 21, 25), "2 spawns, middle, 2 rocks")


# =======================================================================================
def jungle():
    cv = Canvas(81, 46, 61)
    rng = np.random.default_rng(808)
    th = Theme("grass_block", "dirt", [("stone", 50), ("mossy_cobblestone", 25), ("cobblestone", 15),
                                       ("andesite", 10)],
               top_fn=lambda tn, r, t: "podzol" if tn > 0.7 else "grass_block")

    def sdecor(isl):
        jungle_tree(cv, isl.cx - 3, isl.top + 1, isl.cz - 1, rng, height=7)
        cv.scatter(isl, rng, [("fern", 3), ("poppy", 1)], 0.16, on={"grass_block", "podzol"})

    spawn_island(cv, th, 12, 30, 20, 5.6, 9, 8001, [(-1, -3), (-2, 3), (3, 2)], sdecor)

    s = cv.island(26, 14, 19, 4.6, 7, th, 8003, "side")
    cv.chest(s, 24, 14)
    cv.chest(s, 27, 16)
    sx, sz = 27, 12
    sy = s.surface(sx, sz) + 1
    cv.set(sx, sy, sz, "jungle_log")
    cv.blob(sx, sy + 1, sz, 1.7, 1.2, 1.7, "jungle_leaves", rng, ragged=0.25)

    cv.clip = True
    m = cv.island(40, 30, 22, 10.2, 14, th, 8002, "mid", sym=True, hill=1.0, flat=[(40, 30, 5.0)])
    cx, cz, y0 = 40, 30, 23
    mossy = [("mossy_cobblestone", 3), ("mossy_stone_bricks", 3), ("cobblestone", 2), ("cracked_stone_bricks", 1)]
    for y in range(y0, y0 + 3):
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if abs(dx) == 3 or abs(dz) == 3:
                    cv.set(cx + dx, y, cz + dz, pick(rng, mossy))
    for dz in (-3, 3):  # doorways north/south
        cv.set(cx, y0, cz + dz, "air")
        cv.set(cx, y0 + 1, cz + dz, "air")
    for dx in (-3, 3):  # window slits east/west
        cv.set(cx + dx, y0 + 1, cz, "air")
    for lvl, half in enumerate((3, 2, 1)):
        y = y0 + 3 + lvl
        for dx in range(-half, half + 1):
            for dz in range(-half, half + 1):
                cv.set(cx + dx, y, cz + dz, "chiseled_stone_bricks" if half == 1 else pick(rng, mossy))
    cv.set(cx, y0 + 6, cz, "glowstone")
    cv.chest(m, cx - 2, cz, "east")
    cv.chest_ring(m, 4, 7, 45)
    cv.place_n(m, rng, 2, lambda x, y, z: jungle_tree(cv, x, y, z, rng), tmin=0.6, tmax=0.88, margin=7,
               min_dist=6)
    cv.scatter(m, rng, [("fern", 3), ("blue_orchid", 1)], 0.12, on={"grass_block", "podzol"})
    cv.clip = False
    return result("Jungle", "jungle", "Jungle trees, ferns and a mossy stone temple in the middle.",
                  cv, (12, 21, 30), "2 spawns, middle temple, 2 personal side islands")


# =======================================================================================
def crystal():
    cv = Canvas(81, 44, 55)
    rng = np.random.default_rng(909)
    glass = [("light_blue_stained_glass", 4), ("purple_stained_glass", 2), ("magenta_stained_glass", 1),
             ("white_stained_glass", 1)]
    th = Theme("quartz_block", "quartz_block", [("diorite", 45), ("stone", 25), ("polished_andesite", 10),
                                                ("quartz_block", 20)], fill_depth=1,
               top_fn=lambda tn, r, t: "chiseled_quartz_block" if tn > 0.78 else "quartz_block",
               bottom=lambda r, t: pick(r, glass) if r.random() < 0.16 else None)

    def cluster(x, y, z, tall=4):
        cv.set(x, y, z, "quartz_pillar")
        for dy in range(1, tall):
            cv.set(x, y + dy, z, "light_blue_stained_glass")
        for (dx, dz) in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            if rng.random() < 0.7:
                h = int(rng.integers(1, max(2, tall - 1)))
                for dy in range(h):
                    cv.set(x + dx, y + dy, z + dz, pick(rng, glass), replace=False)

    spawn_island(cv, th, 11, 27, 20, 5.6, 9, 9001, [(-2, -2), (-2, 2), (3, 2)],
                 lambda i: cluster(i.cx - 3, i.top + 1, i.cz, 4))

    a = cv.island(30, 16, 21, 6.0, 10, th, 9003, "twin")
    cv.chest(a, 28, 18)
    cv.chest(a, 32, 14)
    cluster(29, a.surface(29, 14) + 1, 14, 6)

    cv.clip = True
    c = cv.island(40, 27, 22, 3.9, 8, th, 9002, "mid", sym=True, hill=0.0)
    for dy in range(1, 8):
        cv.set(40, 22 + dy, 27, "light_blue_stained_glass" if dy < 7 else "white_stained_glass")
    for (dx, dz) in ((-1, 0), (0, -1), (1, 0), (0, 1)):
        for dy in range(1, 4):
            cv.set(40 + dx, 22 + dy, 27 + dz, "purple_stained_glass")
    cv.chest_ring(c, 2, 2.6, 270)
    cv.clip = False
    return result("Crystal", "crystal", "White quartz islands with glass crystal clusters hanging underneath.",
                  cv, (11, 21, 27), "2 spawns, 2 twin islands, small centre crystal island")


# =======================================================================================
def volcano():
    cv = Canvas(85, 46, 55)
    rng = np.random.default_rng(1010)

    def vtop(tn, r, t):
        if tn < 0.36:
            return "stone"
        if tn < 0.66:
            return "coarse_dirt"
        return "gravel"

    th = Theme("stone", "stone", [("stone", 55), ("cobblestone", 25), ("andesite", 12), ("obsidian", 8)],
               fill_depth=2, top_fn=vtop)

    def sdecor(isl):
        boulder(cv, isl.cx - 3, isl.top + 1, isl.cz + 1, rng, "cobblestone", 1.3)
        cv.scatter(isl, rng, [("dead_bush", 1)], 0.1, on={"coarse_dirt"})

    spawn_island(cv, th, 12, 27, 20, 5.6, 9, 10001, [(-2, -3), (-2, 3), (3, -2)], sdecor)

    s = cv.island(26, 11, 19, 4.4, 7, th, 10003, "side")
    cv.chest(s, 25, 13)
    cv.chest(s, 28, 10)
    boulder(cv, 24, s.surface(24, 10) + 1, 10, rng, "obsidian", 1.0)

    cv.clip = True
    m = cv.island(42, 27, 22, 11.0, 15, th, 10002, "mid", sym=True, hill=0.6, flat=[(42, 27, 7.5)])
    cx, cz, y = 42, 27, 22
    cone = [("stone", 40), ("cobblestone", 30), ("andesite", 15), ("obsidian", 15)]
    for dx in range(-7, 8):
        for dz in range(-7, 8):
            d = math.hypot(dx, dz)
            if d > 6.6:
                continue
            h = int(round(7.5 * (1 - d / 7.0)))  # cone height above surface
            if d <= 1.6:
                h = 5  # crater floor level (lava sits on top of it)
            elif d <= 2.7:
                h = 7  # rim
            for yy in range(y + 1, y + h + 1):
                cv.set(cx + dx, yy, cz + dz, "obsidian" if d <= 2.7 and yy > y + 3 else pick(rng, cone))
            if d <= 1.6:
                cv.set(cx + dx, y + h + 1, cz + dz, "lava")
    cv.chest_ring(m, 4, 8.6, 45)
    cv.place_n(m, rng, 1, lambda x, yy, z: boulder(cv, x, yy, z, rng, "andesite", 1.0), tmin=0.75, tmax=0.88,
               margin=8)
    cv.scatter(m, rng, [("dead_bush", 1)], 0.05, on={"coarse_dirt"})
    cv.clip = False
    return result("Volcano", "volcano", "Rocky islands around a smoking volcano with a lava crater.",
                  cv, (12, 21, 27), "2 spawns, volcano middle, 2 personal side islands")


# =======================================================================================
def candy():
    cv = Canvas(81, 44, 61)
    rng = np.random.default_rng(1111)
    sprinkle = [("lime_wool", 1), ("light_blue_wool", 1), ("yellow_wool", 1), ("orange_wool", 1),
                ("magenta_wool", 1), ("red_wool", 1)]

    def ctop(tn, r, t):
        if r.random() < 0.05:
            return pick(r, sprinkle)
        return "white_terracotta" if tn > 0.52 else "pink_terracotta"

    th = Theme("pink_terracotta", "brown_terracotta", "brown_terracotta", fill_depth=2, top_fn=ctop,
               base_fn=lambda dd, total, r, t: "white_terracotta" if dd % 4 == 3 else "brown_terracotta")

    def lollipop(x, y, z, color):
        for dy in range(3):
            cv.set(x, y + dy, z, "birch_fence")
        cv.blob(x, y + 4, z, 1.5, 1.5, 0.6, color, rng)

    def candy_cane(x, y, z):
        for dy in range(6):
            cv.set(x, y + dy, z, "red_wool" if dy % 2 == 0 else "white_wool")
        cv.set(x + 1, y + 5, z, "red_wool")
        cv.set(x + 2, y + 5, z, "white_wool")
        cv.set(x + 2, y + 4, z, "red_wool")

    def sdecor(isl):
        lollipop(isl.cx - 3, isl.top + 1, isl.cz - 1, "magenta_wool")
        candy_cane(isl.cx - 1, isl.top + 1, isl.cz + 3)
        cv.set(isl.cx + 2, isl.top + 1, isl.cz + 2, "cake")

    spawn_island(cv, th, 12, 30, 20, 5.6, 9, 11001, [(-2, -3), (-3, 2), (3, -2)], sdecor)

    n = cv.island(40, 9, 19, 4.5, 7, th, 11003, "side")
    cv.chest(n, 38, 10)
    cv.chest(n, 42, 10)
    lollipop(40, n.surface(40, 8) + 1, 8, "light_blue_wool")

    cv.clip = True
    m = cv.island(40, 30, 22, 10.0, 14, th, 11002, "mid", sym=True, hill=0.9, flat=[(40, 30, 4.6)])
    cx, cz, y = 40, 30, 22
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            d = math.hypot(dx, dz)
            if d <= 3.3:  # striped wrapper
                stripe = int((math.atan2(dz, dx) + math.pi) / (2 * math.pi) * 12) % 2
                for yy in range(y + 1, y + 4):
                    cv.set(cx + dx, yy, cz + dz, "pink_wool" if stripe else "white_wool")
            for yy, rad in ((y + 4, 4.0), (y + 5, 3.4), (y + 6, 2.5), (y + 7, 1.2)):
                if d <= rad:
                    cv.set(cx + dx, yy, cz + dz, pick(rng, sprinkle) if rng.random() < 0.08 else "white_wool")
    cv.set(cx, y + 8, cz, "red_wool")
    cv.chest_ring(m, 4, 6.6, 45)
    cv.place_n(m, rng, 1, lambda x, yy, z: lollipop(x, yy, z, "lime_wool"), tmin=0.6, tmax=0.85, margin=6)
    cv.place_n(m, rng, 1, lambda x, yy, z: candy_cane(x, yy, z), tmin=0.55, tmax=0.85, margin=6)
    cv.clip = False
    return result("Candy", "candy", "Frosted terracotta islands with lollipops, candy canes and a giant cupcake.",
                  cv, (12, 21, 30), "2 spawns, cupcake middle, 2 centre-line side islands")


# =======================================================================================
def castle():
    cv = Canvas(81, 44, 55)
    rng = np.random.default_rng(1212)
    bricks = [("stone_bricks", 5), ("mossy_stone_bricks", 2), ("cracked_stone_bricks", 2)]
    th = Theme("grass_block", "dirt", [("stone_bricks", 35), ("cobblestone", 25), ("mossy_cobblestone", 15),
                                       ("stone", 15), ("cracked_stone_bricks", 10)], fill_depth=2)

    def ruin_wall(isl):
        x = isl.cx - 4
        for dz in range(-3, 4):
            h = int(rng.integers(1, 4)) if abs(dz) < 3 else 1
            base = isl.surface(x, isl.cz + dz)
            if base is None:
                continue
            for dy in range(h):
                cv.set(x, base + 1 + dy, isl.cz + dz, pick(rng, bricks))
        cv.scatter(isl, rng, FLOWERS, 0.08, on={"grass_block"})

    spawn_island(cv, th, 12, 27, 20, 5.6, 9, 12001, [(-2, -2), (-2, 2), (3, 0)], ruin_wall)

    s = cv.island(26, 12, 19, 4.6, 7, th, 12003, "side")
    tx, tz = 27, 11
    ty = s.surface(tx, tz) + 1
    for dy in range(4):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx or dz) and not (dy < 2 and dx == 1 and dz == 0):
                    if dy < 3 or (dx + dz) % 2 == 0:
                        cv.set(tx + dx, ty + dy, tz + dz, pick(rng, bricks))
    cv.chest(s, 24, 13)
    cv.chest(s, 27, 14)

    cv.clip = True
    m = cv.island(40, 27, 22, 10.0, 14, th, 12002, "mid", sym=True, hill=0.9, flat=[(40, 27, 5.2)])
    cx, cz, y0 = 40, 27, 23
    for y in range(y0, y0 + 6):
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if abs(dx) == 3 or abs(dz) == 3:
                    cv.set(cx + dx, y, cz + dz, pick(rng, bricks))
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            if (abs(dx) == 3 or abs(dz) == 3) and (dx + dz) % 2 == 0:
                cv.set(cx + dx, y0 + 6, cz + dz, "stone_bricks")
    for dz in (-3, 3):
        cv.set(cx, y0, cz + dz, "air")
        cv.set(cx, y0 + 1, cz + dz, "air")
    for dx in (-3, 3):
        cv.set(cx + dx, y0 + 2, cz, "air")
        cv.set(cx + dx, y0 + 3, cz, "air")
    for dx, dz in ((-3, -3), (-3, 3), (3, -3), (3, 3)):
        cv.set(cx + dx, y0 + 6, cz + dz, "chiseled_stone_bricks")
        cv.set(cx + dx, y0 + 7, cz + dz, "stone_brick_slab")
    cv.chest(m, cx - 2, cz - 1, "east")
    cv.chest_ring(m, 4, 7, 45)
    cv.scatter(m, rng, FLOWERS, 0.06, on={"grass_block"})
    cv.clip = False
    return result("Castle", "castle", "Floating stone-brick ruins with a crenellated keep in the middle.",
                  cv, (12, 21, 27), "2 spawns, keep middle, 2 personal side islands")


ALL = [meadow, dunes, frostbite, inferno, the_end, atlantis, fungal, jungle, crystal, volcano, candy, castle]
