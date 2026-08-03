# Design changelog

Append-only, newest first.

## 2026-08-03 — Adversarial review wave, and the refinement it forced

Three independent reviewers attacked the design against manufacturer datasheets. Full record: `docs/REVIEW_FINDINGS.md`; consequences: D025, D026.

- **Review verdict was "not fabrication-ready", and it was right.** The headline defect: the gate-driver fault latch could never be cleared (RDYC only rises when FLT_N is already high; FLT_N only clears on a rising RDYC edge; the MCU reset was ANDed in so it could only add another low) — the bridge very likely never enabled, even once. Second: the hardware overcurrent trip never reached TIM1_BKIN, so SPEC §9.2's central safety claim was false as built. Third: the comparators could not see the upper trip threshold, so the overcurrent protection would silently not function.
- **D025 — spec corrections.** Thermal design point recomputed from the module's loss tables (700 W → ~1145 W at the peak condition; the module keeps 3–4× junction margin, so the error lands on the coolant loop). Every 400 µF-era derivation redone for the real 500 µF bank — the passive bleeder was **failing its own <60 s requirement** at 75.4 s. Internal ambient specified (≤70 °C) for the first time; contactor coil current made a requirement; active discharge required to be hardware-inhibited. SPEC open item 5 closed with verified arithmetic.
- **D026 — gate drive derated to +15 V.** The module withstands a short circuit for <1.2 µs at +18 V but <2 µs at +15 V, and the driver chain reaches ~2.0 µs at best — so the 18 V rating was unreachable. Costs +26 % conduction loss, paid out of junction margin. Residual risk recorded honestly: ~2.0 µs sits *at* the rating, so a double-pulse short-circuit test is now a gate on production release.
- **DC-link carrier: 2 oz → 4 oz copper.** Its planes sit in series in the main DC path; at 2 oz the 140 A peak dissipated 37 W in the board, and D024's "heavy copper" claim had never reached the stackup — a fab would have built it at KiCad's 35 µm default.
- **Fabrication package generated for the carrier board** (`fabrication/mcuc_dclink/`) from a board at 0 DRC violations, with order parameters and their reasoning.
- **Engineering report §17–18**: what the reviews changed (including the eight defects that passed ERC, DRC and inspection, and why each survived), seven validation gates on production release, and five open risks with the conditions that make each binding.
- Verification: ERC 0 errors maintained throughout; carrier DRC 0 violations; control-board PCB reverted to its last clean placement state after an interrupted routing attempt left it with violations and no tracks.


## 2026-08-01 — precharge, current_sense and aux_power sheets captured; D019/D020

- **D019:** phase current sensing = 3× LEM HOYS 200-S/SP33 (shunts rejected: 27 W at 0.75 mΩ; ΔΣ route blocked — STM32F405 has no DFSDM; AMC1302 fallback unstocked). 300 A trip via per-phase LM2903-class window comparators (2.340/0.960 V thresholds), open-drain wire-OR onto the supervisor's OC_TRIP; the transducers' own OCD outputs join the same net as an independent ~584 A backup. Bandwidth/latency spec re-derived for 25 kHz switching (≥150 kHz, <5 µs).
- **D020:** aux power architecture fully part-verified: INN3990CQ flyback (DER-948Q pattern) → 15 V; LM5175 buck-boost from the 12–24 V aux input OR'd in via LM74610-Q1; LMR51430 bucks (5 V, 12 V); TLV1117-33; 4× SN6505B + Würth 750316856 (23 V, zener-split +18/−5) gate supplies off the 5 V rail; Murata NXE2S0505MC isolated CAN 5 V. Verified traps: SN6505B is 5 V-only; plain boost can't serve a 24 V aux input.
- **Sheets captured** (7 of 11 now live): precharge (relay path, contactor driver, 4-series bleeder, opto-driven C3M0350120J active discharge; HV/LV separation asserted in netlist), current_sense (69/69 netlist checks; phase busbar paths explicit), aux_power (all 7 blocks; all 12 VGD nets verified to span aux_power → gate_drive; the 3.3 V rail's PWR_FLAG moved from the MCU sheet to its true source, the TLV1117).
- Verification: ERC 0 errors after each sheet; netlist machine-checks per block; independent re-verification before each commit.

## 2026-07-31 — power_stage and gate_drive sheets captured

- **power_stage**: FS02MR12A8MA2B module as a custom 39-pin symbol in the new project library (`mcuc_inverter.kicad_sym`), pin map extracted from datasheet Fig. 1/3/4 (odd=HS/even=LS, 1/2=U 3/4=V 5/6=W); per-phase DC terminals tied on-sheet with a laminated-busbar note; DC-link bank C201–C205 (5 × 100 µF 900 V film [TBV]) with the §6.1 duty note.
- **gate_drive**: six 1ED3491MC12M channels (pinout verified from datasheet v1.20 — single IN pin, not IN±): D018 turn-on RC delay networks (~250 ns target, retune note on-sheet), split 12 Ω/3.3 Ω gate resistors, external BSS138 Miller clamp to **VEE2** per datasheet §4.5.4.1, DESAT via 2× US1M to the module drain-sense pins with ADJA/ADJB set resistors (349 mA soft-off, 650 ns LEB [TBV]), per-channel +18/−5 rails (LS shared), FLT_N wired-AND into the supervisor's DRV_FAULT_IN, RDYC bus (dual-function ready/fault-clear) coupled to the supervisor reset chain through a 1 k series resistor.
- Root sheet now wires supervisor → gate_drive (6× gated PWM, fault, reset) and gate_drive → power_stage (6× gate, 6× Kelvin, 6× DESAT). VGD_* supply rails await the aux_power sheet.
- Verification: ERC 0 errors on the full hierarchy; netlist machine-checks — power_stage 49 pins/29 nets, gate_drive 244/244 channel checks; independently re-run before commit. 4 of 11 sheets now captured.

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
