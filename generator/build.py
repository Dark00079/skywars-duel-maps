"""Build all maps: schematics (both formats), JSON metadata, PNG previews, viewer data.

    python3 generator/build.py            # from the repo root
"""
import base64
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blocks import AIR, BY_NAME, REG, B  # noqa: E402
import export  # noqa: E402
import maps  # noqa: E402
import render  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def visible_voxels(a):
    """Blocks with at least one face open to a non-full block (what a viewer can see)."""
    full = np.array([REG[i].full if i else False for i in range(len(REG))])
    fa = np.pad(full[a], 1, constant_values=False)
    inner = fa[1:-1, 1:-1, 1:-1]
    hidden = inner.copy()
    for sl in ((slice(2, None), slice(1, -1), slice(1, -1)), (slice(0, -2), slice(1, -1), slice(1, -1)),
               (slice(1, -1), slice(2, None), slice(1, -1)), (slice(1, -1), slice(0, -2), slice(1, -1)),
               (slice(1, -1), slice(1, -1), slice(2, None)), (slice(1, -1), slice(1, -1), slice(0, -2))):
        hidden &= fa[sl]
    vis = (a != AIR) & ~hidden
    return np.argwhere(vis)


def main():
    out_schem = os.path.join(ROOT, "schem")
    out_legacy = os.path.join(ROOT, "schematic")
    out_prev = os.path.join(ROOT, "previews")
    for p in (out_schem, out_legacy, out_prev):
        os.makedirs(p, exist_ok=True)
    viewer = {"blocks": [], "maps": []}
    used_types = set()
    meta_all = []
    stone = B("stone")
    for num, fn in enumerate(maps.ALL, start=1):
        info = fn()
        cv = info["cv"]
        conflicts = cv.finish()
        a = cv.a
        W, H, L = a.shape
        # the two corner stones for //pos1 + //pos2
        assert a[0, 0, 0] == AIR and a[W - 1, H - 1, L - 1] == AIR, "corner not empty"
        a[0, 0, 0] = stone
        a[W - 1, H - 1, L - 1] = stone

        sx, sy, sz = info["spawn"]
        spawns = [(sx, sy, sz), (W - 1 - sx, sy, L - 1 - sz)]
        chests = [tuple(int(v) for v in c) for c in np.argwhere(np.isin(a, [B("chest_north"), B("chest_south"),
                                                                             B("chest_east"), B("chest_west")]))]
        # --- validation --------------------------------------------------------------------
        problems = []
        if conflicts:
            problems.append("%d symmetry conflicts" % conflicts)
        if sorted(chests) != sorted(cv.chests):
            problems.append("chest list mismatch %d vs %d" % (len(chests), len(cv.chests)))
        cs = set(chests)
        for (x, y, z) in chests:
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y, z + dz) in cs:
                    problems.append("adjacent chests at %s" % ((x, y, z),))
            below = REG[int(a[x, y - 1, z])]
            above = REG[int(a[x, y + 1, z])]
            if not below.full:
                problems.append("chest %s not supported (%s)" % ((x, y, z), below.name))
            if above.kind == "solid":
                problems.append("chest %s blocked above by %s" % ((x, y, z), above.name))
        for (x, y, z) in spawns:
            if not REG[int(a[x, y - 1, z])].full:
                problems.append("spawn %s has no floor" % ((x, y, z),))
            if (a[x - 1:x + 2, y:y + 4, z - 1:z + 2] != AIR).any():
                problems.append("spawn %s: 3x3x4 cage space not clear" % ((x, y, z),))
        # gravity blocks need support
        for name in ("sand", "red_sand", "gravel"):
            for (x, y, z) in np.argwhere(a == B(name)):
                if y == 0 or a[x, y - 1, z] == AIR:
                    problems.append("unsupported %s at %s" % (name, (x, y, z)))
        # point symmetry check (ignores the two corner stones)
        chk = a.copy()
        chk[0, 0, 0] = chk[W - 1, H - 1, L - 1] = AIR
        lut = np.arange(len(REG))
        for k, v in (("chest_north", "chest_south"), ("chest_south", "chest_north"),
                     ("chest_east", "chest_west"), ("chest_west", "chest_east")):
            lut[B(k)] = B(v)
        if not np.array_equal(lut[chk[::-1, :, ::-1]], chk):
            problems.append("map is not point-symmetric")
        if problems:
            print("!!", info["name"], problems[:8])

        slug = "%02d-%s" % (num, info["slug"])
        offset = (-(W // 2), 0, -(L // 2))
        palette = export.write_sponge(os.path.join(out_schem, slug + ".schem"), a, info["name"], chests, offset)
        export.write_mcedit(os.path.join(out_legacy, slug + ".schematic"), a, chests, offset)
        size = render.render(a, os.path.join(out_prev, slug + ".png"), spawns=spawns)

        # chest groups by the island each chest stands on
        roles = {}
        names = []
        for (ix, iz, ir, role, sym) in cv.islands:
            roles[role] = roles.get(role, 0) + 1
        seen = {}
        for (ix, iz, ir, role, sym) in cv.islands:
            seen[role] = seen.get(role, 0) + 1
            label = {"spawn": "spawn_p%d", "mid": "middle", "side": "side_%d", "rock": "rock_%d",
                     "twin": "twin_%d"}[role]
            names.append(label % seen[role] if "%d" in label else label)

        def group(c):
            x, _, z = c
            best = min(range(len(cv.islands)),
                       key=lambda i: (x - cv.islands[i][0]) ** 2 + (z - cv.islands[i][1]) ** 2)
            return names[best]

        groups = {}
        for c in chests:
            groups.setdefault(group(c), []).append(list(c))
        groups = dict(sorted(groups.items(), key=lambda kv: (not kv[0].startswith("spawn"), kv[0] != "middle", kv[0])))
        counts = {k: len(v) for k, v in groups.items()}
        n_blocks = int((a != AIR).sum())
        meta = {
            "id": num,
            "name": info["name"],
            "file": slug,
            "description": info["blurb"],
            "layout": info["layout"],
            "size": {"x": W, "y": H, "z": L},
            "pos1_stone": [0, 0, 0],
            "pos2_stone": [W - 1, H - 1, L - 1],
            "spawns": [list(s) for s in spawns],
            "chests": groups,
            "chest_counts": counts,
            "total_chests": len(chests),
            "blocks": n_blocks,
            "paste_offset": list(offset),
        }
        meta_all.append(meta)
        print("%-10s %3dx%2dx%3d  blocks=%5d chests=%2d %s palette=%d debris=%d img=%s" % (
            info["name"], W, H, L, n_blocks, len(chests), counts, len(palette), cv.debris, size))

        vis = visible_voxels(a)
        t = a[vis[:, 0], vis[:, 1], vis[:, 2]]
        used_types.update(int(v) for v in np.unique(t))
        packed = np.concatenate([vis.astype(np.uint8), t[:, None].astype(np.uint8)], axis=1).ravel()
        viewer["maps"].append({"meta": meta, "data": base64.b64encode(packed.tobytes()).decode("ascii")})

    with open(os.path.join(ROOT, "maps.json"), "w") as f:
        json.dump(meta_all, f, indent=2)
    viewer["blocks"] = {str(i): {"n": REG[i].name, "t": "#%02x%02x%02x" % REG[i].top,
                                 "s": "#%02x%02x%02x" % REG[i].side, "k": REG[i].kind}
                        for i in sorted(used_types)}
    return viewer


if __name__ == "__main__":
    v = main()
    dest = sys.argv[1] if len(sys.argv) > 1 else None
    if dest:
        with open(dest, "w") as f:
            f.write("window.SKYWARS=" + json.dumps(v, separators=(",", ":")) + ";\n")
        print("viewer data ->", dest, os.path.getsize(dest), "bytes")
