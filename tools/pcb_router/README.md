# PCB completion-routing tooling

Scripted completion router for `mcuc_inverter/mcuc_inverter.kicad_pcb`, written against
KiCad 9.0's bundled Python (`C:\Program Files\KiCad\9.0\bin\python.exe` — the scripts
import `pcbnew` and will not run under a plain system Python).

Committed to the repository deliberately: the 2026-08-04 routing session used a
`scratch/fast_router.py` that never entered version control, and the 2026-08-14
reconciliation had to re-measure everything from scratch. This directory is that
lesson applied.

## What it achieved / where it stopped

Starting board (PR #7 merge): **421 unconnected items**, 0 error-severity DRC violations.
After this tooling ran to convergence: **203 unconnected items**, still 0 error-severity
violations (measured with `kicad-cli 9.0.6 pcb drc --severity-error`, zones refilled).

The remaining 203 opens are the congested residue: fine-pitch logic blocks threaded by
minimum-clearance track bundles, and HV-relax pockets where every legal exit lane is
exactly at minimum clearance. A grid router cannot use a lane whose legal band is
narrower than its grid pitch; those need KiCad's interactive push-and-shove router or
FreeRouting. **Do not expect re-running this tooling to converge further** — it stops at
the same plateau reproducibly.

## Scripts

| Script | Purpose |
|---|---|
| `drive.ps1` | Convergence driver: refill → DRC → route, iterating until 0 unconnected or 2 stalls. Rolling backup + auto-restore. Run this. |
| `router.py` | The router. Reads a DRC JSON `unconnected_items` list, routes each edge: same-net zone taps, L/Z paths from pad-exit stubs, one-via plans, multi-start grid A* (F/B, escalating to In2 and 45 mm margins), then rip-up-and-reroute with victim repair. Exact `SHAPE::Collide` checks against a spatial index for every candidate. |
| `refill.py` | Zone refill + atomic save. |
| `analyze_drc.py` | Per-net breakdown of a DRC report's unconnected items. |
| `cluster_fails.py` | Spatial clustering of unconnected endpoints (hotspot map). |
| `render_debug.py` | Renders a board crop to PNG (tracks/pads/rule areas/unconnected marks) for visual debugging. |
| `probe_seg.py` | Explains *why* a candidate segment collides: prints every obstacle and the clearance applied. |

## Design rules the router enforces

- Netclass clearances from `mcuc_inverter.kicad_pro` (Default/GATE 0.2 mm, HV_BUS 2.0 mm),
  including the netclass pattern assignments.
- `HV_to_LV` 6.4 mm rule with `HV_DOMAIN` exemption and `HV_RELAX` (0.6) /
  `HV_RELAX_PIN` (0.25) relaxations, using intersects semantics for `insideArea`.
- `BARRIER_*` rule areas (no track / no via), **including footprint-embedded rule areas**
  (U608 carries one) — `board.Zones()` alone misses those.
- Board-edge clearance, hole-to-hole ≥ 0.5 mm.
- Inner-layer pours are obstacles for same-layer tracks (never fragment a plane/island)
  but not for through-vias.
- HV nets fall back to narrower widths (3.0 → 2.0 → 1.2 → 0.6 mm, vias 0.8/0.4 below
  1.0 mm) where the relax areas permit — matching how the sense strings were already routed.

## Environment

- `MCUC_ROOT` — repo root (default: two levels above this directory).
- `MCUC_ROUTER_WORK` — scratch dir for DRC reports, logs, backups (default `%TEMP%\mcuc_router`).

## Known limitations

- A recurring native crash (0xC0000005) inside KiCad's Python bindings kills roughly one
  run in three. All saves are atomic and checkpointed every 25 edges, and `drive.ps1`
  restores from backup if the board file is damaged, so a crash costs at most 25 edges of
  progress. Root cause not isolated.
- Grid A* (0.5 / 0.25 / 0.1 mm steps) cannot thread lanes whose legal center band is
  narrower than the step — the plateau above.
- Rip-up removes whole track items (not split segments) and repairs victims on their own
  layer only.
