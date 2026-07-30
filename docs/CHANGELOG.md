# Design changelog

Append-only, newest first.

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
