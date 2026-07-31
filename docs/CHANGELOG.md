# Design changelog

Append-only, newest first.

## 2026-07-31 — Target motor fixed: EMRAX 188 HV; currents re-derived

- Recorded the EMRAX 188 (HV winding) as the target motor (`SPEC.md` §2.2, D011), with figures verified against the manufacturer's datasheet v1.6 — not from memory.
- Re-derived design currents from motor ratings, superseding the 1.5× placeholder: 100 A rms continuous, 190 A rms peak, 270 A instantaneous, ±325 A sense full scale, 300 A hardware trip. Module selection criteria raised to ≥ 150 A continuous / ≥ 270 A peak; DC-link ripple requirement now 60/114 A rms (cap rating ≥ 65 A rms @ 70 °C).
- Added a motor winding temperature input (KTY 81/210, EMRAX standard) to `SPEC.md` §8.3 — previously missing entirely.
- Updated `.copperhead/constraints.json` to match.
- Open item 1 (target motor) resolved; remaining: confirm winding variant at motor order time.
- Verification: document-level only. Schematic sheets are still empty; ERC has nothing new to check.

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
