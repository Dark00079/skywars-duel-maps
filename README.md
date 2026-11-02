# Skywars Duel Maps

12 floating-island maps for 1v1 Skywars, ready to paste with FAWE or WorldEdit.

- **Fair:** every map is point-symmetric (rotated 180° around its centre), so both players get the same islands, chests and distances.
- **Empty chests:** each chest is placed as a block entity with no items, so your Skywars plugin's loot tables fill them.
- **Corner stones:** each map has a stone block at its bottom corner (**pos1**) and one at the opposite top corner (**pos2**), so you can reselect and `//copy` the exact arena after pasting.
- **Two formats:** `.schem` for 1.13+ and `.schematic` for 1.8–1.12.

![All 12 maps](previews/overview.png)

## Maps

<table>
<tr>
<td width="50%" valign="top"><img src="previews/01-meadow.png" alt="Meadow"><br><b>01 · Meadow</b> &nbsp;<code>01-meadow</code><br>Grassy oak islands with a giant oak in the middle.<br><sub>81×44×61 · 14 chests (spawn P1 3, spawn P2 3, middle 4, side 1 2, side 2 2)</sub></td>
<td width="50%" valign="top"><img src="previews/02-dunes.png" alt="Dunes"><br><b>02 · Dunes</b> &nbsp;<code>02-dunes</code><br>Sandstone desert islands around a stepped pyramid.<br><sub>81×42×51 · 12 chests (spawn P1 3, spawn P2 3, middle 4, rock 1 1, rock 2 1)</sub></td>
</tr>
<tr>
<td width="50%" valign="top"><img src="previews/03-frostbite.png" alt="Frostbite"><br><b>03 · Frostbite</b> &nbsp;<code>03-frostbite</code><br>Snowy spruce islands, ice veins and a packed-ice spike.<br><sub>81×46×55 · 14 chests (spawn P1 3, spawn P2 3, middle 4, rock 1 1, rock 2 1, rock 3 1, rock 4 1)</sub></td>
<td width="50%" valign="top"><img src="previews/04-inferno.png" alt="Inferno"><br><b>04 · Inferno</b> &nbsp;<code>04-inferno</code><br>Netherrack and soul sand with a nether-brick tower and glowstone drips.<br><sub>81×44×55 · 16 chests (spawn P1 3, spawn P2 3, middle 6, side 1 2, side 2 2)</sub></td>
</tr>
<tr>
<td width="50%" valign="top"><img src="previews/05-the-end.png" alt="The End"><br><b>05 · The End</b> &nbsp;<code>05-the-end</code><br>End stone islands with obsidian pillars and purple crystal caps.<br><sub>81×44×55 · 16 chests (spawn P1 3, spawn P2 3, middle 6, side 1 2, side 2 2)</sub></td>
<td width="50%" valign="top"><img src="previews/06-atlantis.png" alt="Atlantis"><br><b>06 · Atlantis</b> &nbsp;<code>06-atlantis</code><br>Prismarine islands with sea lanterns and an open-sided temple.<br><sub>81×42×61 · 16 chests (spawn P1 3, spawn P2 3, middle 6, side 1 2, side 2 2)</sub></td>
</tr>
<tr>
<td width="50%" valign="top"><img src="previews/07-fungal.png" alt="Fungal"><br><b>07 · Fungal</b> &nbsp;<code>07-fungal</code><br>Mycelium islands with giant red and brown mushrooms.<br><sub>81×44×51 · 12 chests (spawn P1 3, spawn P2 3, middle 4, rock 1 1, rock 2 1)</sub></td>
<td width="50%" valign="top"><img src="previews/08-jungle.png" alt="Jungle"><br><b>08 · Jungle</b> &nbsp;<code>08-jungle</code><br>Jungle trees, ferns and a mossy stone temple in the middle.<br><sub>81×46×61 · 16 chests (spawn P1 3, spawn P2 3, middle 6, side 1 2, side 2 2)</sub></td>
</tr>
<tr>
<td width="50%" valign="top"><img src="previews/09-crystal.png" alt="Crystal"><br><b>09 · Crystal</b> &nbsp;<code>09-crystal</code><br>White quartz islands with glass crystal clusters hanging underneath.<br><sub>81×44×55 · 12 chests (spawn P1 3, spawn P2 3, middle 2, twin 1 2, twin 2 2)</sub></td>
<td width="50%" valign="top"><img src="previews/10-volcano.png" alt="Volcano"><br><b>10 · Volcano</b> &nbsp;<code>10-volcano</code><br>Rocky islands around a smoking volcano with a lava crater.<br><sub>85×46×55 · 14 chests (spawn P1 3, spawn P2 3, middle 4, side 1 2, side 2 2)</sub></td>
</tr>
<tr>
<td width="50%" valign="top"><img src="previews/11-candy.png" alt="Candy"><br><b>11 · Candy</b> &nbsp;<code>11-candy</code><br>Frosted terracotta islands with lollipops, candy canes and a giant cupcake.<br><sub>81×44×61 · 14 chests (spawn P1 3, spawn P2 3, middle 4, side 1 2, side 2 2)</sub></td>
<td width="50%" valign="top"><img src="previews/12-castle.png" alt="Castle"><br><b>12 · Castle</b> &nbsp;<code>12-castle</code><br>Floating stone-brick ruins with a crenellated keep in the middle.<br><sub>81×44×55 · 16 chests (spawn P1 3, spawn P2 3, middle 6, side 1 2, side 2 2)</sub></td>
</tr>
</table>

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
2. Stand where you want the **middle** of the map, in a void world or high in the sky.
3. Run:

```
//schem load 01-meadow
//paste -a
```

The paste is centred on you horizontally, and the bottom layer (with the pos1 stone) is at your feet. The lowest island blocks are 3–9 blocks above that. `-a` skips air, so nothing around the map is erased.

## Copy it again with the corner stones

The two stones mark opposite corners of the map's bounding box:

- **pos1 stone:** bottom, north-west corner (lowest X, Y and Z)
- **pos2 stone:** top, south-east corner (highest X, Y and Z)

```
//hpos1      (while looking at the bottom stone, or left-click it with the wand)
//hpos2      (while looking at the top stone, or right-click it with the wand)
//copy
```

Break the two stones by hand if you don't want them in your arena. Don't use `//replace stone air`, because the island bases contain stone too.

## Spawns and chests

Coordinates are relative to the **pos1 stone** (add them to the pos1 stone's world position). Each spawn is the block a player stands in, on a flat pad with a clear 3×3, 4-high space above it, so a spawn cage fits. Every chest's position is listed in [`maps.json`](maps.json).

| # | Map | Size (X×Y×Z) | pos2 stone | P1 spawn | P2 spawn | Chests |
|---|---|---|---|---|---|---|
| 01 | Meadow | 81×44×61 | `80 43 60` | `12 21 30` | `68 21 30` | 14 |
| 02 | Dunes | 81×42×51 | `80 41 50` | `12 21 25` | `68 21 25` | 12 |
| 03 | Frostbite | 81×46×55 | `80 45 54` | `12 21 27` | `68 21 27` | 14 |
| 04 | Inferno | 81×44×55 | `80 43 54` | `12 21 27` | `68 21 27` | 16 |
| 05 | The End | 81×44×55 | `80 43 54` | `12 21 27` | `68 21 27` | 16 |
| 06 | Atlantis | 81×42×61 | `80 41 60` | `12 21 30` | `68 21 30` | 16 |
| 07 | Fungal | 81×44×51 | `80 43 50` | `12 21 25` | `68 21 25` | 12 |
| 08 | Jungle | 81×46×61 | `80 45 60` | `12 21 30` | `68 21 30` | 16 |
| 09 | Crystal | 81×44×55 | `80 43 54` | `11 21 27` | `69 21 27` | 12 |
| 10 | Volcano | 85×46×55 | `84 45 54` | `12 21 27` | `72 21 27` | 14 |
| 11 | Candy | 81×44×61 | `80 43 60` | `12 21 30` | `68 21 30` | 14 |
| 12 | Castle | 81×44×55 | `80 43 54` | `12 21 27` | `68 21 27` | 16 |

## Notes

- Leaves are set to persistent (no decay), and sand and gravel always rest on solid blocks.
- No valuable resources: there are no iron, gold, diamond or emerald ores or blocks. Inferno's netherrack has some nether quartz ore mixed in for looks.
- Volcano has a small lava pool sealed inside its crater. No other map has liquids.

## Rebuild or change the maps

```
pip install -r generator/requirements.txt
python3 generator/build.py      # writes schem/, schematic/, previews/, maps.json
python3 generator/overview.py   # writes previews/overview.png
```

Each map is a short function in `generator/maps.py`, with its own seed and theme. The build checks every map for symmetry, chest placement (no double chests, nothing solid on top), safe spawns and unsupported sand or gravel.
