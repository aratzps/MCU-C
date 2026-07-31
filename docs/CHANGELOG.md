# Design changelog

Append-only, newest first.

## 2026-07-30 — Pack architecture decided: 88S1P dual-chemistry (D011)

- SPEC §2 operating window now 220–370 V (LFP "Life" 281.6 V nom / NMC "Range" 325.6 V nom, Desten 10135170 pouches, both 6C). Original 48–450 V envelope retained as hardware capability.
- OVP 490 → 400 V; UVLO 45 → 200 V; aux input range 48–450 V (9.4:1) → 220–370 V (1.7:1) — the §14 hard flyback problem dissolves.
- Constraints regenerated. Decision record and evidence live in the OrekaVault (`ARCHITECTURE-2026-07-30-dual-sku.md` + bus-voltage A/B study).
- Verification: ERC unchanged (no schematic edits in this change); copperhead constraints check green.

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
