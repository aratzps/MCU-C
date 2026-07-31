# Design changelog

Append-only, newest first.

## 2026-07-31 — Supervisor sheet ported from PALTA; dead-time claim corrected (D018)

- `mcuc_inverter/supervisor.kicad_sch` captured from the legacy `pcb_design/supervisor.sch`: overlap-elimination gating, overcurrent latch (AUP1G74), driver-fault conditioning to FAULT_BKIN, driver-reset chain. Root sheet wires the six PWM nets and FAULT_BKIN between MCU and supervisor sheets; netlist-verified that FAULT_BKIN lands on PB12/TIM1_BKIN.
- Verification: ERC 0 errors on the root hierarchy; 24/24 gate-by-gate netlist checks against the legacy netlist; PDF export clean.
- **Finding:** the original supervisor performs overlap elimination only — it never inserted dead time. SPEC §9.2 corrected: dead time = TIM1 silicon generator + planned RC turn-on delay network in the gate_drive sheet (D018).

## 2026-07-31 — Gate driver selected at candidate level (D017)

- 1ED3491MC12M primary (reinforced, 200 V/ns, adjustable DESAT/soft-off, stocked), UCC21755-Q1/UCC21750 alternates; Infineon's zero-stock automotive 1EDI3035AS kept as reference design. Gate levels fixed at +18/−5 V from the module datasheet (+15 V costs +26 % conduction loss). Isolated supplies: discrete push-pull baseline (Murata MGJ2 19-wk lead).
- Module datasheet corrections into SPEC: temp sensing is a per-phase **diode** (TS1–TS3, current-source bias), not an NTC; no integrated current sense; PressFIT PCB must follow AN-G2-ASSEMBLY pattern.

## 2026-07-31 — SiC selected (D016); GaN ruled out (D015); volume analysis

- **Power stage technology decided: SiC** (owner decision on the `docs/SI_VS_SIC.md` analysis). Baseline module Infineon FS02MR12A8MA2B (HybridPACK Drive G2). Consequences propagated: f_sw 25 kHz baseline, DC link stays 400 µF, gate drive to SiC levels (+15/0…−5 V TBV, CMTI ≥ 100 V/ns), overtemp 150 °C, thermal design point 300 W cont / 700 W @ 120 s, pin-fin coolant-jacket mechanical concept.
- `docs/SI_VS_SIC.md` extended with 10 k/yr volume estimates (net SiC premium ~$70–200/unit at scale) and a GaN evaluation; D015 records GaN as unviable for the power stage on 2026 product data (no ≥900 V GaN above 34 A ever shipped, now obsolete; no avalanche rating; no benefit at 25 kHz).
- Verification: document-level; distributor and datasheet figures cited in the doc.

## 2026-07-31 — Peak matched to motor; DC-link derived; verified sourcing research

- **Peak duration 10 s → 120 s [REQ]**, matched to the motor's S2 2 min rating (D012). Consequence: the 120 s peak is quasi-steady-state for the cooling loop — cold plate must be sized for ~700 W (SiC) / ~1225 W (Si) at 35 kW, and the module continuous criterion rises to ≥ 200 A.
- **DC-link capacitance derived (D013, SPEC §6.1):** 400 µF confirmed for f_sw ≥ ~23 kHz (SiC path); ≥ 750 µF if Si at ~12 kHz. Binding constraint is ripple current: bank ≥ 80 A rms @ 70 °C, 114 A / 120 s duty to verify against manufacturer thermal model.
- **Si vs SiC priced with real stocked parts (`docs/SI_VS_SIC.md`):** Si FS200R12KT4R $132 vs SiC FS02MR12A8MA2B $767 — a ~$635 premium, against ~1.6 % battery compensation plus DC-link/cooling offsets; net SiC premium ≈ $280 for a 20 kWh pack. Decision remains with owner.
- **Aux supply candidate resolved (D014):** InnoSwitch3-AQ INN3990CQ — the only verified family with 30 V DC start covering 48–450 V; all other candidates fail on datasheet numbers.
- Verification: document-level; prices and datasheet figures from live distributor/manufacturer pages, cited in the docs.

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
