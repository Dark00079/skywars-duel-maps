"""Build all maps: schematics (both formats), JSON metadata and PNG previews.

    python3 generator/build.py                 # from the repo root
    python3 generator/build.py --viewer DIR    # also write 3D-viewer data files to DIR

Maps are built in parallel (one process per map, up to the CPU count).
"""
import argparse
import gzip
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blocks import AIR, REG, B  # noqa: E402
import export  # noqa: E402
import maps  # noqa: E402
import render  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARGIN = 2  # empty blocks between the islands and the corner stones
CHESTS = ("chest_north", "chest_south", "chest_east", "chest_west")
GRAVITY = ("sand", "red_sand", "gravel")


def face_masks(a):
    """Bit mask of faces open to a non-full block: +x 1, -x 2, +y 4, -y 8, +z 16, -z 32."""
    full = np.array([REG[i].full if i else False for i in range(len(REG))])
    fa = np.pad(full[a], 1, constant_values=False)
    c = (slice(1, -1),) * 3
    mask = np.zeros(a.shape, np.uint8)
    for bit, sl in ((1, (slice(2, None), slice(1, -1), slice(1, -1))), (2, (slice(0, -2), slice(1, -1), slice(1, -1))),
                    (4, (slice(1, -1), slice(2, None), slice(1, -1))), (8, (slice(1, -1), slice(0, -2), slice(1, -1))),
                    (16, (slice(1, -1), slice(1, -1), slice(2, None))), (32, (slice(1, -1), slice(1, -1), slice(0, -2)))):
        mask |= np.where(fa[sl], 0, bit).astype(np.uint8)
    nonfull = (a != AIR) & ~fa[c]
    mask[nonfull] = 63
    mask[a == AIR] = 0
    return mask


def build_one(job):
    num, viewer_dir = job
    t0 = time.time()
    info = maps.ALL[num - 1]()
    cv = info["cv"]
    conflicts = cv.finish()
    a = cv.a
    W0, H0, L0 = a.shape

    # crop to the islands plus a margin; point symmetry keeps the centre in the middle
    nz = np.argwhere(a != AIR)
    lo, hi = nz.min(axis=0), nz.max(axis=0)
    assert lo[0] + hi[0] == W0 - 1 and lo[2] + hi[2] == L0 - 1, "content not centred"
    m = MARGIN
    a2 = np.zeros((hi[0] - lo[0] + 1 + 2 * m, hi[1] - lo[1] + 1 + 2 * m, hi[2] - lo[2] + 1 + 2 * m), np.uint16)
    a2[m:-m, m:-m, m:-m] = a[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, lo[2]:hi[2] + 1]
    off = lo - m
    a = a2
    W, H, L = a.shape
    stone = B("stone")
    a[0, 0, 0] = stone                 # pos1 corner stone
    a[W - 1, H - 1, L - 1] = stone     # pos2 corner stone

    sx, sy, sz = info["spawn"]
    s1 = (int(sx - off[0]), int(sy - off[1]), int(sz - off[2]))
    spawns = [s1, (W - 1 - s1[0], s1[1], L - 1 - s1[2])]
    chest_ids = [B(c) for c in CHESTS]
    chests = [tuple(int(v) for v in c) for c in np.argwhere(np.isin(a, chest_ids))]
    islands = [(x - off[0], z - off[2], r, role, sym) for (x, z, r, role, sym) in cv.islands]

    # --- validation --------------------------------------------------------------------------
    problems = []
    if conflicts:
        problems.append("%d symmetry conflicts" % conflicts)
    if len(chests) != len(cv.chests):
        problems.append("chest count mismatch %d vs %d" % (len(chests), len(cv.chests)))
    cs = set(chests)
    for (x, y, z) in chests:
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y, z + dz) in cs:
                problems.append("adjacent chests at %s" % ((x, y, z),))
        if not REG[int(a[x, y - 1, z])].full:
            problems.append("chest %s not supported" % ((x, y, z),))
        if REG[int(a[x, y + 1, z])].kind == "solid":
            problems.append("chest %s blocked above by %s" % ((x, y, z), REG[int(a[x, y + 1, z])].name))
    for (x, y, z) in spawns:
        if not REG[int(a[x, y - 1, z])].full:
            problems.append("spawn %s has no floor" % ((x, y, z),))
        if (a[x - 1:x + 2, y:y + 4, z - 1:z + 2] != AIR).any():
            problems.append("spawn %s: 3x3x4 cage space not clear" % ((x, y, z),))
    grav = np.isin(a, [B(g) for g in GRAVITY])
    hanging = grav[:, 1:, :] & (a[:, :-1, :] == AIR)
    if hanging.any() or grav[:, 0, :].any():
        problems.append("%d unsupported sand/gravel blocks" % int(hanging.sum()))
    chk = a.copy()
    chk[0, 0, 0] = chk[W - 1, H - 1, L - 1] = AIR
    lut = np.arange(len(REG))
    for k, v in (("chest_north", "chest_south"), ("chest_south", "chest_north"),
                 ("chest_east", "chest_west"), ("chest_west", "chest_east")):
        lut[B(k)] = B(v)
    if not np.array_equal(lut[chk[::-1, :, ::-1]], chk):
        problems.append("map is not point-symmetric")

    # --- outputs -----------------------------------------------------------------------------
    slug = "%02d-%s" % (num, info["slug"])
    offset = (-(W // 2), 0, -(L // 2))
    palette = export.write_sponge(os.path.join(ROOT, "schem", slug + ".schem"), a, info["name"], chests, offset)
    export.write_mcedit(os.path.join(ROOT, "schematic", slug + ".schematic"), a, chests, offset)
    size = render.render(a, os.path.join(ROOT, "previews", slug + ".png"), spawns=spawns)

    names = []
    seen = {}
    for (ix, iz, ir, role, sym) in islands:
        seen[role] = seen.get(role, 0) + 1
        label = {"spawn": "spawn_p%d", "mid": "middle", "side": "side_%d", "rock": "rock_%d",
                 "twin": "twin_%d"}[role]
        names.append(label % seen[role] if "%d" in label else label)

    def group(c):
        x, _, z = c
        best = min(range(len(islands)), key=lambda i: (x - islands[i][0]) ** 2 + (z - islands[i][1]) ** 2)
        return names[best]

    groups = {}
    for c in chests:
        groups.setdefault(group(c), []).append(list(c))
    groups = dict(sorted(groups.items(), key=lambda kv: (not kv[0].startswith("spawn"), kv[0] != "middle", kv[0])))
    core = a.copy()
    core[0, 0, 0] = core[W - 1, H - 1, L - 1] = AIR
    ys = np.argwhere(core.any(axis=(0, 2)))
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
        "chest_counts": {k: len(v) for k, v in groups.items()},
        "total_chests": len(chests),
        "blocks": int((a != AIR).sum()),
        "lowest_island_y": int(ys.min()),
        "paste_offset": list(offset),
    }

    if viewer_dir:
        fm = face_masks(a)
        vis = np.argwhere(fm > 0)
        t = a[vis[:, 0], vis[:, 1], vis[:, 2]].astype(np.uint16)
        mk = fm[vis[:, 0], vis[:, 1], vis[:, 2]].astype(np.uint16)
        rec = np.empty((len(vis), 4), "<u2")
        rec[:, 0], rec[:, 1], rec[:, 2] = vis[:, 0], vis[:, 1], vis[:, 2]
        rec[:, 3] = t | (mk << 8)
        with open(os.path.join(viewer_dir, slug + ".dat"), "wb") as f:
            f.write(gzip.compress(rec.tobytes(), compresslevel=9, mtime=0))
        meta["_viewer_voxels"] = int(len(vis))
        meta["_types"] = sorted(int(v) for v in np.unique(t))

    report = "%-10s %3dx%3dx%3d blocks=%7d chests=%2d palette=%2d debris=%d img=%s %.0fs" % (
        info["name"], W, H, L, meta["blocks"], len(chests), len(palette), cv.debris, size, time.time() - t0)
    return meta, problems, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--viewer", help="directory for 3D viewer data (optional)")
    ap.add_argument("--only", type=int, nargs="*", help="map numbers to build (default: all)")
    ap.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1))
    args = ap.parse_args()
    for p in ("schem", "schematic", "previews"):
        os.makedirs(os.path.join(ROOT, p), exist_ok=True)
    if args.viewer:
        os.makedirs(args.viewer, exist_ok=True)
    nums = args.only or list(range(1, len(maps.ALL) + 1))
    with Pool(args.jobs) as pool:
        results = pool.map(build_one, [(n, args.viewer) for n in nums], chunksize=1)
    bad = False
    for meta, problems, report in results:
        print(report)
        if problems:
            bad = True
            print("   !!", problems[:6])
    path = os.path.join(ROOT, "maps.json")
    existing = {}
    if args.only and os.path.exists(path):
        existing = {m["id"]: m for m in json.load(open(path))}
    viewer_meta = []
    for meta, _, _ in results:
        viewer_meta.append(dict(meta))
        existing[meta["id"]] = {k: v for k, v in meta.items() if not k.startswith("_")}
    with open(path, "w") as f:
        json.dump([existing[k] for k in sorted(existing)], f, indent=2)
    if args.viewer:
        types = sorted({t for m in viewer_meta for t in m["_types"]})
        blocks = {str(i): {"n": REG[i].name, "t": "#%02x%02x%02x" % REG[i].top, "s": "#%02x%02x%02x" % REG[i].side,
                           "k": REG[i].kind} for i in types}
        with open(os.path.join(args.viewer, "maps.js"), "w") as f:
            f.write("window.SKYWARS=" + json.dumps({
                "blocks": blocks,
                "maps": [{k: v for k, v in m.items() if not k.startswith("_")} for m in
                         sorted(viewer_meta, key=lambda m: m["id"])],
            }, separators=(",", ":")) + ";\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
