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

## D011: Target motor — EMRAX 188, High Voltage winding

- **Decision:** EMRAX 188 (or similar class), HV winding assumed. Figures verified against EMRAX 188 datasheet v1.6 (2026-07-31): peak 190 A rms / 100 Nm (S2 2 min), continuous 100 A rms, Kt 0.54 Nm/A, Kv 13.61 rpm/V at nominal load, 10 pole pairs, 8000 rpm max, KTY 81/210 stator temperature sensor, resolver/encoder feedback.
- **Why:** Owner's choice of motor. HV winding is the engineering recommendation: at 250 V nominal the HV envelope (100 Nm at ≈ 3400 rpm ≈ 35.6 kW) lands on the board's 35 kW rated point, and its 190/100 A rms currents match a sensible power stage. MV needs 310 A rms peak, LV 390–900 A — both oversize the inverter. The motor's full 60 kW at 6500 rpm needs 660 V and is unreachable on a 450 V bus; accepted.
- **Consequence:** §3.3 re-derived from motor ratings, superseding the 1.5× guess (D006): 100 A rms continuous, 190 A rms peak (10 s), 270 A instantaneous, ±325 A sense, 300 A hardware trip. Module criteria rise to ≥ 150 A continuous / ≥ 270 A peak. DC-link ripple rises to 60/114 A rms. A motor temperature input (KTY 81/210) is added to §8.3.
- **Open:** Winding variant must be confirmed at motor order time; if it changes, §3.3 is re-derived. Duty cycle still unstated — 10 s board peak vs motor's 2 min S2 rating noted in §3.3.
- **Affects:** SPEC.md §2.2, §3.3, §3.4, §4.3, §6, §8.1, §8.3, §9.1, module selection, thermal.

## D012: Peak duration 120 s, matched to the motor's S2 rating

- **Decision:** t_peak = 120 s (was 10 s [SEL]). Owner directive: match the inverter peak time to the motor's S2 2 min rating.
- **Why:** The motor sustains 190 A rms / 100 Nm for 2 min; a 10 s board limit would waste that capability.
- **Consequence:** 120 s is quasi-steady-state for the module baseplate, cold plate and coolant loop (thermal τ of tens of seconds). Cooling must therefore be sized for peak-condition losses — ~700 W (SiC) to ~1225 W (Si) at 35 kW — not the 300–525 W continuous figures. Module continuous-class criterion raised to ≥ 200 A. DC-link ripple duty (114 A rms) must be held for the full 120 s, which drives the capacitor bank rating.
- **Affects:** SPEC.md §2, §3.3, §4.3, §6, §11.4. Strengthens the SiC side of open item 2.

## D013: DC-link capacitance confirmed conditionally on switching frequency

- **Decision:** 400 µF stands **if** f_sw ≥ ~23 kHz (SiC path, 25 kHz baseline). If Si IGBT at ~12 kHz, capacitance must rise to ≥ 750 µF for the same 1.5 % bus ripple.
- **Why:** Derivation in SPEC.md §6.1 — C ≥ I_ph,pk/(8·f_sw·ΔV_pp) with 270 A instantaneous peak and 3.75 V pp permitted at 250 V.
- **Consequence:** Capacitor voltage-ripple sizing is settled; the binding constraint is ripple *current* — a bank rated ≥ 80 A rms @ 70 °C with the 114 A / 120 s repetitive duty verified against the manufacturer's thermal model. Si path also carries a capacitor cost/volume penalty, which enters the Si-vs-SiC comparison.
- **Affects:** SPEC.md §6, §7.1 (precharge energy scales with C), open item 2.

## D014: Auxiliary supply controller — InnoSwitch3-AQ (candidate level)

- **Decision:** Power Integrations InnoSwitch3-AQ INN3990CQ (900 V PowiGaN, integrated FET) as primary candidate; INN3999CQ as alternate; discrete UCC28C42 + 1200 V SiC FET as fallback.
- **Why:** Only family found with a datasheet-guaranteed 30 V DC start covering the full 48–450 V (9.4:1) range at 20–30 W. Every other candidate fails on hard numbers: InnoSwitch3-EP min DC input 90 V and UV/OV pin ratio 4.4:1; LinkSwitch-XT2 11 W ceiling; InnoSwitch4 tops at 750 V; ST VIPer 800 V; onsemi NCP107x 700 V; MPS HFC0500 brown-in ≥ 95 V. Verified in stock (DigiKey, 2026-07-31).
- **Open:** Transformer design; 48 V full-load power is interpolated from the 30/60 V datasheet columns and must be confirmed; 650 V max recommended rail vs our 500 V transient is fine but noted.
- **Affects:** SPEC.md §11.2, §14 item 7, aux_power schematic sheet.

## D015: GaN ruled out for the power stage

- **Decision:** No GaN in the main power stage. GaN stays where it already is: the aux flyback's 900 V PowiGaN InnoSwitch3-AQ (D014).
- **Why:** Verified against shipping products (2026-07-31): no GaN device ≥ 900 V at ≥ 50 A exists in distribution (Transphorm's 900 V line is obsolete, was 34 A max); no GaN six-pack/half-bridge module suits a 450 V bus at 190 A rms; lateral GaN has no avalanche capability, which matters for regen transients; and a 25 kHz FOC drive gains nothing from GaN's switching speed while its dv/dt stresses motor insulation and bearings. The only >400 V-bus GaN path (650 V devices, 3-level topology) doubles switch count for no benefit here.
- **Re-evaluate if:** avalanche-rated vertical GaN or ≥ 900 V / ≥ 200 A-class GaN modules reach distribution.
- **Affects:** SPEC.md §4 (unchanged — Si vs SiC remains the open choice), docs/SI_VS_SIC.md §6.

## D016: SiC power stage

- **Decision:** SiC MOSFET module. Baseline part: Infineon FS02MR12A8MA2B (HybridPACK Drive G2, CoolSiC, 1.9 mΩ, 390 A class, $767 stocked). Right-sized alternative if stock appears: Microchip MSCSM120TAM11CTPAG.
- **Why:** Owner decision, informed by `docs/SI_VS_SIC.md`: at qty 1 SiC costs ~$635 more (~$280 net after DC-link/cooling/battery offsets); at 10 k/yr the net premium falls to ~$70–200/unit. SiC buys inaudible 25 kHz switching, ~½ the peak-condition heat (700 W vs 1225 W for the 120 s peak, which sizes the cold plate per D012), less mass, and better 450 V-bus behaviour.
- **Consequence:** f_sw baseline 25 kHz → DC-link stays 400 µF (D013). Gate drive becomes SiC-class: +15 V / 0…−5 V (per module datasheet, TBV), CMTI ≥ 100 V/ns, SiC-tuned desat. Module overtemp threshold 150 °C. Thermal design point: 300 W continuous / 700 W for 120 s. The HybridPACK G2's pin-fin baseplate means the "cold plate" is a coolant jacket sealing against the module, not a flat plate — this shapes the whole mechanical concept (§14 item 8). The 2SP0115T2A IGBT driver data stays as reference only.
- **Sourcing note:** 51 pcs stocked, 39-week factory lead behind them — buy prototype modules at design commit, not at layout completion.
- **Affects:** SPEC.md §4, §5, §6, §9.1, §11.2, §11.4; gate_drive and power_stage sheets; cold plate concept.

## D017: Gate driver — Infineon 1ED3491MC12M (candidate level); gate levels +18/−5 V

- **Decision:** 1ED3491MC12M (EiceDRIVER X3 Analog) as primary gate driver, six channels. Alternates: TI UCC21755-Q1 (SiC-tuned DESAT, AEC-Q) and UCC21750. Gate levels +18 V / −5 V. Isolated per-channel supplies: discrete push-pull (SN6505B + transformer) baseline, Murata MGJ2 preferred if lead time allows.
- **Why:** Verified against the FS02MR12A8MA2B datasheet: recommended VGS(on) 15–18 V with R_DS,on 1.90 mΩ at 18 V vs 2.40 mΩ at 15 V (+26 % conduction loss — hence +18 V), VGS(off) −5…0 V, Q_G 1.19 µC. The 1ED3491 is reinforced per IEC 60747-17, 200 V/ns CMTI (module dv/dt ≈ 14 V/ns), adjustable DESAT, Miller clamp pre-driver, current-source soft-off, per-channel fault, $6.31 with 2,670 in stock. Infineon's own automotive pairing (1EDI3035AS, used on their EV GB HPD2 SIC board for this exact module) has zero distribution stock — kept as the reference design to copy.
- **Ruled out on verified grounds:** Skyworks Si828x (no VDE 0884 VIORM), ADuM4136 (VIORM 849 V pk basic, no Miller clamp), ACPL-355JC (no stock, not automotive), STGAP1AS (obsolete, 2.5 kV rms, 50 V/ns), NCP51705 (not isolated).
- **Amended same day after full datasheet verification:** ST STGAP3SXS *qualifies* (reinforced VDE 0884-17, 200 V/ns, 10 A, SiC 6 V DESAT, $4.85 — cheapest qualifier) and onsemi NCD57000 qualifies (VIORM 1200 V pk, 100 V/ns min) — both added as alternates 4/5; 1ED3491MC12M remains primary. Murata MGJ2 caveat found: reinforced cert covers only 150 V rms working voltage (5.2 kV is a test voltage) — at 450 V bus the driver IC must be the reinforced barrier and the supply transformer is functional isolation, pending the compliance target (§14 item 4).
- **Also learned from the module datasheet:** temp sensing is a **diode per phase** (TS1–TS3), not an NTC — §8.3 corrected, needs current-source bias; no integrated current sense (external phase sensors stay per §8.1); PressFIT PCB requires the AN-G2-ASSEMBLY mating pattern — a hard mechanical constraint on the power PCB.
- **Affects:** SPEC.md §5, §8.3, §11.2, gate_drive sheet, power PCB mechanical.

## D018: Supervisor ported; dead-time claim in D008 corrected

- **What happened:** The PALTA supervisor was ported into `mcuc_inverter/supervisor.kicad_sch` (ERC 0 errors; 24/24 gate-by-gate netlist checks against the legacy `VESC-controller.net`). During the port, the reconstruction showed the original circuit performs **overlap elimination only** — NAND detects both inputs high, AND gates force both outputs low. It inserts **no dead time**: there is no deliberate turn-on delay anywhere in the discrete logic. D008's "hardware dead-time insertion" claim was wrong about the original board.
- **Resolution:** Dead time is generated by TIM1's silicon dead-time generator (configured by firmware, enforced by hardware, cannot be violated by compare-register values). The firmware-independent protection is (a) the ported overlap eliminator and (b) a turn-on RC delay network per gate-drive input, to be placed in the gate_drive sheet (~250 ns initial, TBV against switching characterisation). Together these mean even a totally misconfigured timer cannot command overlap, and simultaneous edges get a hardware-guaranteed gap.
- **Port deviations (recorded on-sheet):** all-3.3 V logic (the original BOM quietly fitted 5 V SN74ACT08 despite the schematic saying ALVC08 — revisit only if the chosen gate driver needs 5 V inputs; the 1ED3491 does not); single OC_TRIP open-drain input replacing the three wired-OR comparators (comparator lives with current sensing); added boot pullups on FAULT_RESET / DRV_RST_IN.
- **Affects:** SPEC.md §9.2, gate_drive sheet (RC delay network), D008 (corrected, not superseded — the latch and BKIN routing claims were accurate and are now netlist-verified).

## D019: Phase current sensing — LEM HOYS 200-S/SP33 aperture transducers

- **Decision:** Three LEM HOYS 200-S/SP33 (±500 A range, 3.3 V ratiometric, 1.65 V ref) on the phase outputs; 300 A hardware trip via an external window comparator per phase, open-drain wire-OR onto the supervisor's OC_TRIP. Spec bandwidth/latency re-derived for 25 kHz switching: ≥ 150 kHz / < 5 µs.
- **Why:** The shunt path died twice over: 0.75 mΩ (sized for ±250 mV amps) dissipates 27 W at the 120 s peak, and the low-dissipation 0.1 mΩ + ΔΣ route is blocked because the STM32F405 has no DFSDM peripheral (verified, ST AN4821) — the analog AMC1302 fallback was unstocked with 16-week lead. HOYS is the only verified in-stock transducer meeting range + reinforced isolation (IEC 61800-5-1, 5.4 kV rms tested) + native 3.3 V ADC mapping. Precedent: the VESC-based Axiom 100 kW inverter uses LEM aperture transducers for the same reasons.
- **Trade-offs accepted:** 180 kHz / 3 µs (fine at 25 kHz FOC); ±1.25 % @ 25 °C growing to ±4.55 % @ 105 °C (FOC uses relative phase balance; absolute accuracy affects torque calibration, acceptable for this application); the built-in OCD (584 A) is unusable for the 300 A trip — external comparators restore the PALTA per-phase comparator structure.
- **Sourcing note:** only 5 pcs at DigiKey at check — order with the module and drivers at design commit.
- **Affects:** SPEC.md §8.1, §9.1 trip implementation, current_sense sheet, motor phase routing (aperture transducers — busbars pass through), BOM.

---

## Superseded

The documents generated on 2026-07-30 by an autonomous copperhead run (`SPEC.md`, `BOM.md`, `PINOUT.md`, and the first `DECISIONS.md`/`CHANGELOG.md`) were removed rather than corrected. They contained fabricated part numbers, a non-existent MOSFET as the central BOM item, an unusable pinout, and several component selections that would have destroyed hardware on power-up. Verification never ran on them because no schematic existed, so copperhead's ERC/DRC gate was inert. Recorded here so the reasoning is not rediscovered later.
