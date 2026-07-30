# Design changelog

Append-only, newest first.

## 2026-07-30 -- Comparator front end placed

- Placed the overcurrent comparator front end in `mcuc_inverter/supervisor.kicad_sch`: 13 components (threshold divider, three LM2903 packages giving six channels, wired-OR trip node with pull-up and filter), via `tools/gen_supervisor_frontend.py`.
- A single three-resistor string (1k / 11k / 1k off +3V3) generates both thresholds -- 3.046 V and 0.254 V -- keeping them ratiometric with the rail the current sense is referenced to.
- Verified by netlist export, not assumption: `OC_TRIP_N` has 8 nodes (six comparator outputs plus pull-up and filter), `V_TH_POS` and `V_TH_NEG` 6 each, each `ISENSE_x` reaches `Ux.2` and `Ux.5`, `GND` 10. ERC reports **0 errors**.
- `tools/gen_skeleton.py` now emits interface signals selectively (`EMIT_SIGNALS`), currently the three ISENSE lines, so warnings stay proportional to what is actually built.
- Six warnings remain (3 `label_dangling`, 3 `pin_not_driven`), all saying that `current_sense` is not yet built so nothing drives ISENSE. Left in place deliberately.
- `pin_not_driven` added to the WIP warning severities. `hier_label_mismatch` remains an error.
- Note: `copperhead check` fails on warnings as well as errors, so it reads red while any block is unbuilt. `kicad-cli sch erc --severity-error` is the meaningful gate during build-out and currently reports 0.

## 2026-07-30 — Supervisor logic design

- Added `docs/supervisor.md`: full logic design for the hardware interlock block — overcurrent detect and latch, fault aggregation, PWM overlap elimination and dead time. 24-signal interface, gate budget, failure-mode review.
- Two design decisions worth flagging: comparators run from **+5 V** because the LM2903's input common-mode ceiling on 3.3 V is 1.8 V, below the 3.05 V positive trip point — the positive-overcurrent channel would never have asserted. And **74HC** replaces the original's 74ACT, because the dead-time RC depends on a CMOS threshold at 0.5×VCC; TTL thresholds make the delay supply-dependent.
- Added `tools/gen_skeleton.py`, which generates the KiCad skeleton and records the block interfaces.
- Added ERC severities to `mcuc_inverter.kicad_pro`: `hier_label_mismatch` stays an error; `label_dangling` and `pin_not_connected` are warnings during build-out.
- The interface is **not** emitted into the schematic yet (`EMIT_INTERFACE = False`). Emitting it into empty sheets produces 96 legitimate dangling-label violations, and copperhead fails on warnings, which would leave the gate permanently red. Rationale in `docs/supervisor.md` §9.
- Verification: ERC 0 violations, `copperhead check` green. With the interface temporarily emitted, ERC confirmed **no `hier_label_mismatch`** — all 24 names and directions agree across sheet boundaries.
- Also set `core.ignorecase=false`, after the `Power.sch`/`power.sch` collision silently deleted the working copy of `power.sch` during the PR #1 merge.

## 2026-07-30 — KiCad 9 project skeleton

- Created `mcuc_inverter/` — a KiCad 9 project with a root schematic and 11 hierarchical sheets, one per functional block in `SPEC.md`: power stage/DC link, gate drive, precharge, current sense, bus sense, temperature, position feedback, supervisor, auxiliary power, MCU, communications.
- Sheets are empty placeholders. No symbols, no nets, no components yet.
- `HV_BUS` net class pre-defined with 2.0 mm clearance and 3.0 mm track width, per `SPEC.md` §10.
- Pointed `.copperhead/config.json` `schematic` at the new root sheet.
- Verification: **ERC runs and passes** (0 violations), hierarchy traverses under `kicad-cli sch export pdf`, `copperhead check` reports `ERC ✓ / drift ✓ / constraints ✓`. DRC still skipped — no `.kicad_pcb` yet.

This is the first artifact in the project that verification can actually act on. Everything before it was documents only.

## 2026-07-30 — Architecture baseline from scratch

- Scope set to **fully integrated inverter** (control + gate drive + DC link + precharge + power stage on one assembly).
- MCU set to **STM32F405VGT6, LQFP100**. All four rotor position interfaces required.
- Rewrote `SPEC.md` as the architecture baseline: ratings, DC vs phase current derivation, power stage, gate drive, DC link, precharge/discharge, sensing, protection, isolation, auxiliary power, thermal, MCU/VESC compatibility.
- Created `docs/DECISIONS.md` (D001–D010) and reset `.copperhead/constraints.json` from the new spec.
- Verification: none. No schematic exists yet; ERC and DRC cannot run.

## 2026-07-30 — Removed autonomous-run documents

Deleted `SPEC.md`, `BOM.md`, `PINOUT.md`, `openspec/changes/*` and the previous `docs/DECISIONS.md` / `docs/CHANGELOG.md` produced by autonomous copperhead runs.

Reason: fabricated part numbers (including a non-existent MOSFET as the central BOM item), a pinout with 96 invented power pins and universal GPIO collisions, and component selections that would destroy hardware on power-up (a 35 V-max regulator on a 48–450 V bus, a 45 V TVS across the bus, a 60 V gate driver at 450 V). No verification ran on any of it because no schematic existed, so the ERC/DRC gate was inert and the proposals self-approved.

No BOM has been recreated. Component selection follows architecture, not the other way round.
