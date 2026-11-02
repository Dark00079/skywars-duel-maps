"""Write README.md from maps.json (run after build.py)."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def label(k):
    names = {"spawn_p1": "spawn P1", "spawn_p2": "spawn P2", "middle": "middle"}
    if k in names:
        return names[k]
    a, b = k.split("_")
    return "%s %s" % (a, b)


def main():
    maps = json.load(open(os.path.join(ROOT, "maps.json")))
    xs = [m["size"]["x"] for m in maps]
    ys = [m["size"]["y"] for m in maps]
    zs = [m["size"]["z"] for m in maps]
    bl = [m["blocks"] for m in maps]
    tallest = max(ys)

    rows = []
    for i in range(0, len(maps), 2):
        cells = []
        for m in maps[i:i + 2]:
            groups = ", ".join("%s %d" % (label(k), v) for k, v in m["chest_counts"].items())
            cells.append(
                '<td width="50%%" valign="top"><img src="previews/%s.png" alt="%s"><br>'
                '<b>%02d · %s</b> &nbsp;<code>%s</code><br>%s<br>'
                '<sub>%d×%d×%d · %s blocks · %d chests (%s)</sub></td>'
                % (m["file"], m["name"], m["id"], m["name"], m["file"], m["description"],
                   m["size"]["x"], m["size"]["y"], m["size"]["z"], format(m["blocks"], ","), m["total_chests"],
                   groups))
        rows.append("<tr>\n" + "\n".join(cells) + "\n</tr>")
    gallery = "<table>\n" + "\n".join(rows) + "\n</table>"

    spawn_rows = "\n".join(
        "| %02d | %s | %s | `%s` | `%s` | `%s` | %d | %d |" % (
            m["id"], m["name"], "%d×%d×%d" % (m["size"]["x"], m["size"]["y"], m["size"]["z"]),
            " ".join(map(str, m["pos2_stone"])), " ".join(map(str, m["spawns"][0])),
            " ".join(map(str, m["spawns"][1])), m["total_chests"], 256 - m["size"]["y"]) for m in maps)

    readme = f"""# Skywars Duel Maps

12 big floating-island maps for 1v1 Skywars, ready to paste with FAWE or WorldEdit.

- **Big:** each map is about {min(xs)}–{max(xs)} blocks wide, {min(zs)}–{max(zs)} deep and {min(ys)}–{max(ys)} tall ({min(bl) // 1000}k–{max(bl) // 1000}k blocks), each with a big centrepiece and fully decorated islands.
- **Fair:** every map is point-symmetric (rotated 180° around its centre), so both players get the same islands, chests and distances.
- **Empty chests:** each chest is placed as a block entity with no items, so your Skywars plugin's loot tables fill them.
- **Corner stones:** each map has a stone block at its bottom corner (**pos1**) and one at the opposite top corner (**pos2**), so you can reselect and `//copy` the exact arena after pasting.
- **Two formats:** `.schem` for 1.13+ and `.schematic` for 1.8–1.12.

![All 12 maps](previews/overview.png)

## Maps

{gallery}

## Files

| Folder | Format | Use it on |
|---|---|---|
| `schem/` | Sponge schematic v2, DataVersion 1631 (1.13.2) | FAWE / WorldEdit 7 on 1.13 → 1.21+ (blocks upgrade automatically) |
| `schematic/` | MCEdit / legacy `.schematic` | FAWE or WorldEdit 6 on 1.8–1.12 (modern WorldEdit can load these too) |
| `previews/` | PNG renders | The pictures in this README |
| `maps.json` | JSON | Size, corner stones, spawns and every chest position for each map |
| `generator/` | Python | The script that builds all of the above |

Both folders hold the same 12 maps, block for block. Only blocks that exist in 1.8 are used.

## Paste a map

1. Copy the files into `plugins/FastAsyncWorldEdit/schematics/` (or `plugins/WorldEdit/schematics/`).
2. Stand where you want the **middle** of the map, in a void world.
3. Run:

```
//schem load 01-meadow
//paste -a
```

The paste is centred on you horizontally, and the bottom layer (with the pos1 stone) is at your feet. The islands start 2 blocks above it. `-a` skips air, so nothing around the map is erased.

Each map is a few hundred thousand blocks. FAWE handles that quickly; plain WorldEdit is much slower at this size.

**Build height:** the tallest map is {tallest} blocks. On 1.8–1.17 (top of the world at y=255), stand at or below the y in the "Paste at y ≤" column. On 1.18+ any height up to y=160 works.

## Copy it again with the corner stones

The two stones mark opposite corners of the map's bounding box:

- **pos1 stone:** bottom, north-west corner (lowest X, Y and Z)
- **pos2 stone:** top, south-east corner (highest X, Y and Z)

```
//hpos1      (while looking at the bottom stone, or left-click it with the wand)
//hpos2      (while looking at the top stone, or right-click it with the wand)
//copy
```

The stones are far apart on maps this size, so fly to each one before targeting it. Break the two stones by hand if you don't want them in your arena. Don't use `//replace stone air`, because the islands contain stone too.

## Spawns and chests

Coordinates are relative to the **pos1 stone** (add them to the pos1 stone's world position). Each spawn is the block a player stands in, on a flat pad with a clear 3×3, 4-high space above it, so a spawn cage fits. Every chest's position is listed in [`maps.json`](maps.json).

| # | Map | Size (X×Y×Z) | pos2 stone | P1 spawn | P2 spawn | Chests | Paste at y ≤ (1.8–1.17) |
|---|---|---|---|---|---|---|---|
{spawn_rows}

## Notes

- The gap between each spawn island and the next island is about 55–75 blocks, so expect long bridges.
- Leaves are set to persistent (no decay), and sand and gravel always rest on solid blocks.
- No valuable resources: there are no iron, gold, diamond or emerald ores or blocks. Inferno's netherrack has some nether quartz ore mixed in for looks.
- Volcano has a lava lake sealed inside its crater. No other map has liquids.

## Rebuild or change the maps

```
pip install -r generator/requirements.txt
python3 generator/build.py      # writes schem/, schematic/, previews/, maps.json
python3 generator/overview.py   # writes previews/overview.png
python3 generator/readme.py     # writes this README from maps.json
```

Each map is a function in `generator/maps.py` with its own seed and theme. `S` at the top of that file scales the island layout (sizes, depths and gaps); the centrepieces are sized for the default `S = 5`, and trees and plants stay normal size. The build checks every map for symmetry, chest placement (no double chests, nothing solid on top), safe spawns and unsupported sand or gravel.
"""
    with open(os.path.join(ROOT, "README.md"), "w") as f:
        f.write(readme)
    print("README.md", len(readme), "chars")


if __name__ == "__main__":
    main()
