# MCU-C DC-link carrier — fabrication package

Generated with `kicad-cli` 9.0.6 from `mcuc_dclink/mcuc_dclink.kicad_pcb`.
**DRC status at generation: 0 violations, 0 unconnected items.**

## Order parameters (PCBWay or equivalent)

| Parameter | Value | Why |
|---|---|---|
| Layers | 2 | Solid DC+ front / DC− back planes |
| Board size | 320 × 100 mm | |
| Thickness | 1.6 mm | |
| **Outer copper weight** | **4 oz (140 µm) — BOTH sides. NOT the default.** | The planes are in series in the main DC path (battery feed lug → planes → module P1–P3 lugs). At 2 oz the path is ~1.9 mΩ, so the 140 A peak dissipates **37 W in the board** with ~65 K rise over the 120 s peak. 4 oz halves it. This is a functional requirement, not a preference — see `docs/REVIEW_FINDINGS.md` #16 |
| Material | FR-4, TG150 or better | 4 oz processing + elevated operating temperature |
| Surface finish | HASL lead-free or ENIG | No press-fit holes on this board, so immersion tin is **not** required (unlike the control board) |
| Soldermask / silkscreen | Both sides | |
| Min track / clearance | 0.5 mm / 2.0 mm | HV_BUS netclass; DC+ to DC− separation is by front/back plane split |
| Drill | See `mcuc_dclink.drl` | Ø6.4 mm M6 lug holes dominate |

**Quote note for the fabricator:** 4 oz outer copper on a 2-layer board changes minimum track/space capability. Nothing on this board is finer than 0.5 mm, so standard 4 oz rules apply comfortably — but confirm the fabricator does not silently substitute 2 oz.

## Contents

| File | Layer |
|---|---|
| `mcuc_dclink-F_Cu.gbr` / `-B_Cu.gbr` | Copper, front / back (solid DC_BUS_P / DC_BUS_N zones) |
| `mcuc_dclink-F_Mask.gbr` / `-B_Mask.gbr` | Soldermask |
| `mcuc_dclink-F_Paste.gbr` / `-B_Paste.gbr` | Paste (minimal — this board is all THT) |
| `mcuc_dclink-F_Silkscreen.gbr` / `-B_Silkscreen.gbr` | Silkscreen, carries the build note |
| `mcuc_dclink-Edge_Cuts.gbr` | Board outline |
| `mcuc_dclink.drl` | Excellon drill, absolute origin, mm |
| `mcuc_dclink-drl_map.gbr` | Drill map |
| `mcuc_dclink-job.gbrjob` | Gerber job file (layer stack definition) |
| `mcuc_dclink-pos.csv` | Component positions (5 capacitors + 10 terminals) |

## Assembly notes

- **All parts are through-hole.** Assembly is hand or wave; no paste stencil is needed despite the paste layers being present.
- **Capacitor polarity: none** (film), but the **bank orientation matters**: every capacitor's pad-1 column must land on the front (DC_BUS_P) plane. The footprint enforces this by pad numbering.
- **M6 lug positions are marked `[TBV] per busbar drawing`** on the silkscreen. They are placed at the module's 47 mm phase pitch, but final positions follow the laminated-busbar mechanical drawing, which is not yet released. **Do not fabricate the busbar from this board's coordinates without cross-checking.**
- Zone connections are **solid — no thermal reliefs** (deliberate: this board carries 114 A rms of ripple). Expect a preheat requirement when hand-soldering the M6 lugs into 4 oz planes.

## BOM

`docs/BOM_mcuc_dclink.csv` (refdes level) and `docs/BOM.md` §1 (suppliers, pricing, stock).
Principal item: 5 × Vishay **MKP1848C71010JY5**, 100 µF / 1000 V, $28.85 ea at qty 1.
