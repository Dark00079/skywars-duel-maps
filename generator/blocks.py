"""Block registry.

Every block used by the generator is listed once with:
  * its 1.13 block state (Sponge .schem, DataVersion 1631; newer servers upgrade it)
  * its legacy numeric id:data (MCEdit .schematic for 1.8 - 1.12)
  * preview colours (top face, side face) and a render "kind"

Only blocks that exist in 1.8 are used, so both formats contain the same map.
Nothing here is a valuable resource (no ores/iron/diamond blocks), so players
cannot mine free loot out of the maps - all loot comes from the (empty) chests
your plugin fills.
"""

DATA_VERSION = 1631  # Minecraft 1.13.2

DYES = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray",
        "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black"]

WOOL_RGB = {
    "white": (233, 236, 236), "orange": (240, 118, 19), "magenta": (189, 68, 179),
    "light_blue": (58, 175, 217), "yellow": (248, 197, 39), "lime": (112, 185, 25),
    "pink": (237, 141, 172), "gray": (62, 68, 71), "light_gray": (142, 142, 134),
    "cyan": (21, 137, 145), "purple": (121, 42, 172), "blue": (53, 57, 157),
    "brown": (114, 71, 40), "green": (84, 109, 27), "red": (161, 39, 34), "black": (20, 21, 25),
}
TERRACOTTA_RGB = {
    "white": (209, 178, 161), "orange": (161, 83, 37), "magenta": (149, 88, 108),
    "light_blue": (113, 108, 137), "yellow": (186, 133, 35), "lime": (103, 117, 52),
    "pink": (161, 78, 78), "gray": (57, 42, 35), "light_gray": (135, 106, 97),
    "cyan": (86, 91, 91), "purple": (118, 70, 86), "blue": (74, 59, 91),
    "brown": (77, 51, 35), "green": (76, 83, 42), "red": (143, 61, 46), "black": (37, 22, 16),
}
GLASS_RGB = {k: tuple(min(255, int(c * 0.75 + 70)) for c in v) for k, v in WOOL_RGB.items()}

# kind -> render box inside the unit cell (x0, y0, z0, x1, y1, z1); "full" kinds occlude
SHAPES = {
    "solid": (0, 0, 0, 1, 1, 1),
    "leaves": (0, 0, 0, 1, 1, 1),
    "glass": (0, 0, 0, 1, 1, 1),
    "liquid": (0, 0, 0, 1, 0.875, 1),
    "chest": (0.0625, 0, 0.0625, 0.9375, 0.875, 0.9375),
    "plant": (0.3, 0, 0.3, 0.7, 0.6, 0.7),
    "fence": (0.375, 0, 0.375, 0.625, 1, 0.625),
    "slab": (0, 0, 0, 1, 0.5, 1),
    "snow": (0, 0, 0, 1, 0.125, 1),
    "cactus": (0.0625, 0, 0.0625, 0.9375, 1, 0.9375),
    "cake": (0.0625, 0, 0.0625, 0.9375, 0.5, 0.9375),
}
FULL_KINDS = {"solid", "leaves", "glass", "liquid"}


class Block:
    __slots__ = ("idx", "name", "modern", "lid", "ldata", "top", "side", "kind", "family")

    def __init__(self, idx, name, modern, lid, ldata, top, side, kind, family):
        self.idx, self.name, self.modern = idx, name, modern
        self.lid, self.ldata = lid, ldata
        self.top, self.side = top, side
        self.kind, self.family = kind, family

    @property
    def full(self):
        return self.kind in FULL_KINDS


REG = []
BY_NAME = {}


def reg(name, modern, lid, ldata, top, side=None, kind="solid", family=None):
    b = Block(len(REG), name, modern, lid, ldata, top, side or top, kind, family)
    REG.append(b)
    BY_NAME[name] = b
    return b


def mc(s):
    return "minecraft:" + s


reg("air", mc("air"), 0, 0, (0, 0, 0), kind="air")

# --- stone family -----------------------------------------------------------------
reg("stone", mc("stone"), 1, 0, (125, 125, 125))
reg("granite", mc("granite"), 1, 1, (153, 108, 88))
reg("diorite", mc("diorite"), 1, 3, (190, 190, 192))
reg("andesite", mc("andesite"), 1, 5, (136, 136, 137))
reg("polished_andesite", mc("polished_andesite"), 1, 6, (132, 135, 134))
reg("cobblestone", mc("cobblestone"), 4, 0, (118, 118, 118))
reg("mossy_cobblestone", mc("mossy_cobblestone"), 48, 0, (104, 123, 96))
reg("stone_bricks", mc("stone_bricks"), 98, 0, (122, 121, 122))
reg("mossy_stone_bricks", mc("mossy_stone_bricks"), 98, 1, (110, 120, 98))
reg("cracked_stone_bricks", mc("cracked_stone_bricks"), 98, 2, (112, 111, 112))
reg("chiseled_stone_bricks", mc("chiseled_stone_bricks"), 98, 3, (128, 127, 128))
reg("stone_brick_slab", mc("stone_brick_slab[type=bottom,waterlogged=false]"), 44, 5, (122, 121, 122), kind="slab")
reg("cobblestone_slab", mc("cobblestone_slab[type=bottom,waterlogged=false]"), 44, 3, (118, 118, 118), kind="slab")
reg("gravel", mc("gravel"), 13, 0, (136, 128, 126))
reg("obsidian", mc("obsidian"), 49, 0, (24, 19, 36))
reg("clay", mc("clay"), 82, 0, (160, 166, 179))

# --- soil & plants ----------------------------------------------------------------
reg("grass_block", mc("grass_block[snowy=false]"), 2, 0, (104, 168, 62), (134, 100, 68), family="grass")
reg("dirt", mc("dirt"), 3, 0, (134, 96, 67))
reg("coarse_dirt", mc("coarse_dirt"), 3, 1, (119, 85, 59))
reg("podzol", mc("podzol[snowy=false]"), 3, 2, (106, 76, 33), (134, 96, 67))
reg("mycelium", mc("mycelium[snowy=false]"), 110, 0, (113, 98, 112), (134, 96, 67))
reg("sand", mc("sand"), 12, 0, (219, 207, 163))
reg("red_sand", mc("red_sand"), 12, 1, (190, 103, 33))
reg("dandelion", mc("dandelion"), 37, 0, (245, 222, 50), kind="plant")
reg("poppy", mc("poppy"), 38, 0, (210, 36, 36), kind="plant")
reg("blue_orchid", mc("blue_orchid"), 38, 1, (48, 165, 230), kind="plant")
reg("allium", mc("allium"), 38, 2, (190, 110, 230), kind="plant")
reg("azure_bluet", mc("azure_bluet"), 38, 3, (225, 230, 240), kind="plant")
reg("red_tulip", mc("red_tulip"), 38, 4, (220, 50, 40), kind="plant")
reg("orange_tulip", mc("orange_tulip"), 38, 5, (240, 140, 40), kind="plant")
reg("white_tulip", mc("white_tulip"), 38, 6, (235, 235, 235), kind="plant")
reg("pink_tulip", mc("pink_tulip"), 38, 7, (240, 170, 200), kind="plant")
reg("oxeye_daisy", mc("oxeye_daisy"), 38, 8, (235, 235, 215), kind="plant")
reg("fern", mc("fern"), 31, 2, (88, 140, 58), kind="plant")
reg("dead_bush", mc("dead_bush"), 32, 0, (120, 88, 46), kind="plant")
reg("red_mushroom", mc("red_mushroom"), 40, 0, (220, 50, 50), kind="plant")
reg("brown_mushroom", mc("brown_mushroom"), 39, 0, (160, 120, 90), kind="plant")
reg("cactus", mc("cactus[age=0]"), 81, 0, (88, 132, 44), (72, 112, 34), kind="cactus")
reg("hay_block", mc("hay_block[axis=y]"), 170, 0, (178, 150, 36), (166, 136, 38))
reg("red_mushroom_block",
    mc("red_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]"),
    100, 14, (200, 46, 45))
reg("brown_mushroom_block",
    mc("brown_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]"),
    99, 14, (149, 111, 81))
reg("mushroom_stem",
    mc("mushroom_stem[down=false,east=true,north=true,south=true,up=false,west=true]"),
    99, 10, (208, 202, 190), (203, 196, 185))

# --- wood -------------------------------------------------------------------------
WOODS = {
    # name: (log legacy id, data, plank data, leaves id, leaves data, log top, log side, leaves, planks)
    "oak": (17, 0, 0, 18, 0, (160, 129, 77), (109, 85, 50), (62, 128, 34), (162, 130, 78)),
    "spruce": (17, 1, 1, 18, 1, (115, 89, 52), (58, 37, 16), (54, 90, 58), (114, 84, 48)),
    "birch": (17, 2, 2, 18, 2, (193, 179, 135), (216, 215, 210), (110, 150, 70), (192, 175, 121)),
    "jungle": (17, 3, 3, 18, 3, (160, 115, 80), (85, 67, 25), (48, 140, 22), (160, 115, 80)),
    "acacia": (162, 0, 4, 161, 0, (168, 90, 50), (103, 96, 86), (86, 130, 30), (168, 90, 50)),
    "dark_oak": (162, 1, 5, 161, 1, (63, 42, 21), (60, 46, 26), (44, 96, 24), (66, 43, 20)),
}
for w, (lid, ld, pd, fid, fd, ltop, lside, leaf, plank) in WOODS.items():
    reg(w + "_log", mc(w + "_log[axis=y]"), lid, ld, ltop, lside, family="log")
    # persistent=true / legacy no-decay bit (4): pasted leaves never decay
    reg(w + "_leaves", mc(w + "_leaves[distance=7,persistent=true]"), fid, fd | 4, leaf, kind="leaves")
    reg(w + "_planks", mc(w + "_planks"), 5, pd, plank)
reg("oak_slab", mc("oak_slab[type=bottom,waterlogged=false]"), 126, 0, (162, 130, 78), kind="slab")
reg("spruce_slab", mc("spruce_slab[type=bottom,waterlogged=false]"), 126, 1, (114, 84, 48), kind="slab")
reg("oak_fence", mc("oak_fence"), 85, 0, (162, 130, 78), kind="fence", family="woodfence")
reg("spruce_fence", mc("spruce_fence"), 188, 0, (114, 84, 48), kind="fence", family="woodfence")
reg("birch_fence", mc("birch_fence"), 189, 0, (215, 203, 143), kind="fence", family="woodfence")
reg("jungle_fence", mc("jungle_fence"), 190, 0, (160, 115, 80), kind="fence", family="woodfence")
reg("bookshelf", mc("bookshelf"), 47, 0, (162, 130, 78), (117, 94, 59))

# --- desert -----------------------------------------------------------------------
reg("sandstone", mc("sandstone"), 24, 0, (216, 203, 155))
reg("chiseled_sandstone", mc("chiseled_sandstone"), 24, 1, (214, 200, 150))
reg("cut_sandstone", mc("cut_sandstone"), 24, 2, (218, 206, 160))
reg("red_sandstone", mc("red_sandstone"), 179, 0, (186, 99, 29))
reg("chiseled_red_sandstone", mc("chiseled_red_sandstone"), 179, 1, (183, 96, 27))
reg("cut_red_sandstone", mc("cut_red_sandstone"), 179, 2, (189, 101, 31))
reg("sandstone_slab", mc("sandstone_slab[type=bottom,waterlogged=false]"), 44, 1, (218, 206, 160), kind="slab")

# --- snow & ice -------------------------------------------------------------------
reg("snow_block", mc("snow_block"), 80, 0, (243, 252, 252), (232, 242, 242))
reg("snow", mc("snow[layers=1]"), 78, 0, (248, 254, 254), kind="snow")
reg("ice", mc("ice"), 79, 0, (150, 186, 252), kind="glass")
reg("packed_ice", mc("packed_ice"), 174, 0, (141, 180, 250))

# --- nether -----------------------------------------------------------------------
reg("netherrack", mc("netherrack"), 87, 0, (111, 54, 52))
reg("soul_sand", mc("soul_sand"), 88, 0, (84, 64, 51))
reg("nether_bricks", mc("nether_bricks"), 112, 0, (45, 23, 27))
reg("nether_brick_fence", mc("nether_brick_fence"), 113, 0, (45, 23, 27), kind="fence", family="netherfence")
reg("nether_brick_slab", mc("nether_brick_slab[type=bottom,waterlogged=false]"), 44, 6, (45, 23, 27), kind="slab")
reg("glowstone", mc("glowstone"), 89, 0, (226, 186, 112))
reg("nether_quartz_ore", mc("nether_quartz_ore"), 153, 0, (125, 84, 79))
reg("lava", mc("lava[level=0]"), 11, 0, (214, 100, 18), kind="liquid")

# --- end --------------------------------------------------------------------------
reg("end_stone", mc("end_stone"), 121, 0, (220, 223, 160))

# --- ocean ------------------------------------------------------------------------
reg("prismarine", mc("prismarine"), 168, 0, (99, 158, 150))
reg("prismarine_bricks", mc("prismarine_bricks"), 168, 1, (99, 172, 158))
reg("dark_prismarine", mc("dark_prismarine"), 168, 2, (52, 92, 76))
reg("sea_lantern", mc("sea_lantern"), 169, 0, (190, 215, 205))

# --- quartz & glass ---------------------------------------------------------------
reg("quartz_block", mc("quartz_block"), 155, 0, (236, 231, 224))
reg("chiseled_quartz_block", mc("chiseled_quartz_block"), 155, 1, (231, 226, 218))
reg("quartz_pillar", mc("quartz_pillar[axis=y]"), 155, 2, (234, 229, 221), (228, 222, 213))
reg("quartz_slab", mc("quartz_slab[type=bottom,waterlogged=false]"), 44, 7, (236, 231, 224), kind="slab")
reg("glass", mc("glass"), 20, 0, (205, 228, 235), kind="glass")
for i, d in enumerate(DYES):
    reg(d + "_stained_glass", mc(d + "_stained_glass"), 95, i, GLASS_RGB[d], kind="glass")
    reg(d + "_wool", mc(d + "_wool"), 35, i, WOOL_RGB[d])
    reg(d + "_terracotta", mc(d + "_terracotta"), 159, i, TERRACOTTA_RGB[d])
reg("terracotta", mc("terracotta"), 172, 0, (152, 94, 68))
reg("bricks", mc("bricks"), 45, 0, (150, 97, 83))
reg("cake", mc("cake[bites=0]"), 92, 0, (238, 230, 222), (200, 160, 120), kind="cake")

# --- chests (one entry per facing so 180deg rotation can swap them) -----------------
for f, ld in (("north", 2), ("south", 3), ("west", 4), ("east", 5)):
    reg("chest_" + f, mc("chest[facing=%s,type=single,waterlogged=false]" % f), 54, ld,
        (176, 126, 52), (150, 104, 38), kind="chest", family="chest")

# 180 degree rotation about the vertical axis (used to make maps point-symmetric)
ROT180 = {"chest_north": "chest_south", "chest_south": "chest_north",
          "chest_east": "chest_west", "chest_west": "chest_east"}

AIR = 0


def B(name):
    return BY_NAME[name].idx
