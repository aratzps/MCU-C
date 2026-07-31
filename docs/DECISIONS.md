# MCU-C — Design Decisions

Newest last. Each entry records what was decided, why, and what it constrains.

---

## D001: Fully integrated inverter, not a control board

- **Decision:** Control, gate drive, DC link, precharge and power stage on one assembly.
- **Why:** Project owner's choice, made with the trade-off stated explicitly.
- **Consequence:** DC-link sizing, precharge/discharge, creepage/clearance and thermal become primary constraints on this design rather than the power stage vendor's. This is the harder path — the original project split brain and power stage deliberately.
- **Affects:** Everything. See SPEC.md §1.

## D002: STM32F405VGT6 (LQFP100)

- **Decision:** STM32F405VGT6 in LQFP100.
- **Why:** Same die and firmware target as the VESC reference, so mainline `bldc` firmware applies. 100 pins instead of the 64 on the `RGT6` used by the original PALTA board gives room for all four position-feedback interfaces plus CAN, USB and the supervisor without pin conflicts.
- **Consequence:** No CAN FD is available on any STM32F405 — it has classic bxCAN 2.0B only. VESC's CAN protocol uses classic CAN, so this is not a limitation in practice, but CAN FD must not be specified anywhere.
- **Affects:** SPEC.md §12, firmware target, CAN transceiver selection.

## D003: All four rotor position interfaces supported

- **Decision:** Hall, ABI/quadrature encoder, resolver (AD2S1205) and SinCos/SSI.
- **Why:** Project owner's requirement. Resolver is appropriate at this power level and carries over from the original board.
- **Consequence:** Drives the pin budget and is a main reason for choosing LQFP100 over LQFP64.
- **Note:** Mainline VESC has no resolver driver. The AD2S1205's incremental-encoder emulation outputs (A, B, NM) let the resolver present as a standard ABI encoder that VESC already supports — so no firmware work is needed for basic operation.
- **Affects:** SPEC.md §8.4, MCU package choice, `pcb_design/resolver.sch` reuse.

## D004: 1200 V switch class, six-pack module

- **Decision:** 1200 V devices, in a single six-pack power module rather than discretes.
- **Why:** 450 V bus with switching overshoot and regenerative transients rules out 650 V. A module gives one thermal interface, vendor-controlled stray inductance, an integrated NTC, and removes the paralleling/current-sharing problem entirely.
- **Open:** Si IGBT vs SiC not yet decided — see SPEC.md §14 item 2.
- **Affects:** Gate drive, thermal design, cost, efficiency.

## D005: Current limits are fixed; power scales with bus voltage

- **Decision:** The board enforces current limits, not power limits. 15 kW / 35 kW are defined at 250 V nominal only.
- **Why:** Project owner's clarification. Physically correct — the hardware limits are thermal and current, not power.
- **Consequence:** 2.9 kW / 6.7 kW at 48 V; 27 kW / 49 kW at 450 V by current limit alone. **The board is not rated for 49 kW** — switching losses scale with bus voltage and the thermal design is sized at 250 V. Derating above 250 V is an open item.
- **Affects:** SPEC.md §2.1, §3, thermal design.

## D006: Phase current sized 1.5× above the value at rated power

- **Decision:** 75 A rms continuous, 175 A rms peak, ±300 A sense range.
- **Why:** Phase current at rated power (50 A / 117 A rms) occurs at full modulation, i.e. high speed. At low speed the motor draws the same current for the same torque at much lower voltage, so phase current rather than power is binding. 1.5× allows full torque at low speed.
- **Caveat:** The 1.5× factor is a judgement call made without knowledge of the target motor or duty cycle. It directly sets device count and cost and should be revisited once those are known.
- **Affects:** SPEC.md §3.3, module selection, current sensing, thermal.

## D007: Three isolated phase-current measurements

- **Decision:** Per-phase current sensing, not a single DC-link shunt.
- **Why:** VESC FOC reconstructs the current vector from per-phase samples. A single bus-level shunt cannot provide this.
- **Affects:** SPEC.md §8.1, ADC allocation, isolation count.

## D008: Firmware-independent hardware interlocks, carried over from PALTA

- **Decision:** Overcurrent latch and shoot-through/PWM-overlap elimination in discrete logic, with the aggregated fault driving TIM1_BKIN.
- **Why:** The most valuable feature of the original board (`pcb_design/supervisor.sch`). Routing the fault to the timer break input means an MCU lockup, firmware bug or bad configuration cannot leave the bridge conducting.
- **Affects:** SPEC.md §9.2, pin assignment (PB12), supervisor schematic reuse.

## D009: HV-derived auxiliary supply plus external 12–24 V input

- **Decision:** Isolated flyback from the 48–450 V bus (≥ 900 V primary switch), and a separate 12–24 V auxiliary input.
- **Why:** Control electronics must power up before the DC bus is live in order to sequence precharge, and to permit safe bench work on a de-energised bus. The 9.4:1 input range is the hard part of the flyback design.
- **Affects:** SPEC.md §11, precharge sequencing, bench bring-up.

## D010: Liquid cooling as baseline

- **Decision:** Cold plate. Forced air only at a reduced, characterised continuous rating.
- **Why:** 300–525 W continuous dissipation at 15 kW depending on Si vs SiC. This is a physical consequence of realistic device losses, not a preference.
- **Affects:** SPEC.md §11.4, mechanical concept, enclosure.


## D011: 88S1P dual-chemistry pack; operating window 220–370 V

- **Decision:** Pack is 88S1P Desten 10135170 pouch, in two chemistry SKUs sharing one fixture: LFP 22 Ah "Life" (281.6 V nominal, 220–321 V, 6.2 kWh) and NMC 32 Ah "Range" (325.6 V nominal, 264–370 V, 10.4 kWh). Both 6C-charge rated per datasheet. OVP moves 490 → 400 V; UVLO 45 → 200 V; aux-supply input range collapses to 220–370 V (1.7:1).
- **Why:** DCFC compatibility decided the bus class (CCS floors 150/200 V; every production DCFC motorcycle ≥300 V; sub-window packs cannot charge). 88S clears both defects of 80S (peak C-rate inside the 132 A cell rating; 220 V empty clears the legacy 200 V floor) and saves ~137 mm of stack vs 100S. Both SKUs bracket one ~280–320 V motor winding class (EMRAX LV+100% as COTS reference).
- **Caveats:** LFP SKU peak ≈ 33–34 kW through the shared winding (−4%), tapering below ~20% SoC; rapid charge window 15–45 °C makes pack pre-heating a launch requirement; LFP datasheet's 160 Wh/kg headline unreconciled (use 142).
- **Affects:** SPEC §2, §9.1, §11.1; current-sense scaling (§8.1) now unblockable; charge-port section to be added (§13).

---

## Superseded

The documents generated on 2026-07-30 by an autonomous copperhead run (`SPEC.md`, `BOM.md`, `PINOUT.md`, and the first `DECISIONS.md`/`CHANGELOG.md`) were removed rather than corrected. They contained fabricated part numbers, a non-existent MOSFET as the central BOM item, an unusable pinout, and several component selections that would have destroyed hardware on power-up. Verification never ran on them because no schematic existed, so copperhead's ERC/DRC gate was inert. Recorded here so the reasoning is not rediscovered later.
