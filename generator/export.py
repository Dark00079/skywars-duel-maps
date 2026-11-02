"""Writers: Sponge schematic v2 (.schem), MCEdit/legacy (.schematic)."""
import numpy as np

import nbt
from blocks import AIR, DATA_VERSION, REG

DIRS = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}


def modern_state(a, x, y, z):
    """1.13 block state for the block at x,y,z. Fences get their connections computed
    from neighbours (WorldEdit pastes states as-is, without block updates)."""
    b = REG[int(a[x, y, z])]
    if b.kind != "fence":
        return b.modern
    W, H, L = a.shape
    props = {"waterlogged": "false"}
    for d, (dx, dz) in DIRS.items():
        nx, nz = x + dx, z + dz
        con = False
        if 0 <= nx < W and 0 <= nz < L:
            n = REG[int(a[nx, y, nz])]
            con = (n.kind == "fence" and n.family == b.family) or n.kind == "solid"
        props[d] = "true" if con else "false"
    return b.modern + "[" + ",".join("%s=%s" % kv for kv in sorted(props.items())) + "]"


def _order(a):
    # WorldEdit index = x + z*Width + y*Width*Length  ->  iterate y, then z, then x
    return np.ascontiguousarray(a.transpose(1, 2, 0)).ravel()


def write_sponge(path, a, name, chests, offset):
    W, H, L = a.shape
    states = np.empty(a.shape, dtype=object)
    palette = {"minecraft:air": 0}
    idx = np.zeros(a.shape, dtype=np.int32)
    nz = np.argwhere(a != AIR)
    for (x, y, z) in nz:
        s = modern_state(a, x, y, z)
        if s not in palette:
            palette[s] = len(palette)
        idx[x, y, z] = palette[s]
    flat = _order(idx)
    data = bytearray()
    for v in flat.tolist():
        while v & ~0x7F:
            data.append((v & 0x7F) | 0x80)
            v >>= 7
        data.append(v)
    block_entities = []
    for (x, y, z) in chests:
        block_entities.append({
            "Pos": nbt.IntArray([x, y, z]),
            "Id": nbt.String("minecraft:chest"),
            "Items": nbt.List(nbt.COMPOUND, []),
        })
    root = {
        "Version": nbt.Int(2),
        "DataVersion": nbt.Int(DATA_VERSION),
        "Width": nbt.Short(W),
        "Height": nbt.Short(H),
        "Length": nbt.Short(L),
        "Offset": nbt.IntArray([0, 0, 0]),
        "Metadata": nbt.Compound({
            "Name": nbt.String(name),
            "Author": nbt.String("skywars-duel-maps generator"),
            "WEOffsetX": nbt.Int(offset[0]),
            "WEOffsetY": nbt.Int(offset[1]),
            "WEOffsetZ": nbt.Int(offset[2]),
        }),
        "PaletteMax": nbt.Int(len(palette)),
        "Palette": nbt.Compound({k: nbt.Int(v) for k, v in palette.items()}),
        "BlockData": nbt.ByteArray(data),
        "BlockEntities": nbt.List(nbt.COMPOUND, block_entities),
    }
    nbt.write_gz(path, "Schematic", root)
    return palette


def write_mcedit(path, a, chests, offset):
    W, H, L = a.shape
    lid = np.array([b.lid for b in REG], dtype=np.uint8)
    ldat = np.array([b.ldata for b in REG], dtype=np.uint8)
    flat = _order(a)
    tiles = []
    for (x, y, z) in chests:
        tiles.append({
            "id": nbt.String("Chest"),
            "x": nbt.Int(x), "y": nbt.Int(y), "z": nbt.Int(z),
            "Items": nbt.List(nbt.COMPOUND, []),
        })
    root = {
        "Width": nbt.Short(W),
        "Height": nbt.Short(H),
        "Length": nbt.Short(L),
        "Materials": nbt.String("Alpha"),
        "Blocks": nbt.ByteArray(lid[flat].tobytes()),
        "Data": nbt.ByteArray(ldat[flat].tobytes()),
        "Entities": nbt.List(nbt.COMPOUND, []),
        "TileEntities": nbt.List(nbt.COMPOUND, tiles),
        "WEOriginX": nbt.Int(0), "WEOriginY": nbt.Int(0), "WEOriginZ": nbt.Int(0),
        "WEOffsetX": nbt.Int(offset[0]), "WEOffsetY": nbt.Int(offset[1]), "WEOffsetZ": nbt.Int(offset[2]),
    }
    nbt.write_gz(path, "Schematic", root)
