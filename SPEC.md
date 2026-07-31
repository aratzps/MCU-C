# MCU-C — Integrated 3-Phase Inverter, System Specification

**Revision:** 0.1 (architecture baseline)
**Status:** Requirements and architecture fixed. Component selection is candidate-level and flagged where verification is outstanding.

---

## 0. How to read this document

Every value is tagged:

| Tag | Meaning |
|---|---|
| **[REQ]** | Requirement given by the project owner. Not negotiable without a spec change. |
| **[DER]** | Derived by calculation from a [REQ]. The derivation is shown. |
| **[SEL]** | Engineering selection. Defensible, but a design choice that could go another way. |
| **[TBV]** | To be verified. A candidate part or number that must be checked against a datasheet or supplier before it enters a BOM. |

Nothing in this document has been validated by ERC, DRC or simulation. No schematic exists yet.

---

## 1. Scope

A **fully integrated 3-phase inverter**: control electronics, isolated gate drive, DC link, precharge and power stage on one assembly.

This is deliberately different from the existing `pcb_design/` board in this repository, which is a control board only ("brain") that drives an external power stage through an adaptor board. That split existed for good reason at high voltage. Integrating it means DC-link design, precharge, creepage/clearance and thermal management become primary constraints on this design rather than someone else's.

**In scope:** power stage, gate drive, DC link, precharge/discharge, auxiliary supplies, sensing, protection, MCU, communications, thermal interface.

**Out of scope:** motor, battery/supply, main contactor (commanded by this board, not housed on it), enclosure, external cooling loop.

---

## 2. Top-level ratings

> **Revision 2026-07-30 — pack architecture decided: 88S1P dual-chemistry.** Two SKUs share one fixture and one inverter: LFP 22 Ah "Life" (281.6 V nom, 220–321 V, 6.2 kWh) and NMC 32 Ah "Range" (325.6 V nom, 264–370 V, 10.4 kWh), Desten 10135170 pouches, both 6C-charge rated. Evidence: OrekaVault `01-knowledge/engineering/ARCHITECTURE-2026-07-30-dual-sku.md` and the bus-voltage A/B study. The original 48–450 V / 250 V-nominal envelope below is retained as hardware capability; operating numbers supersede it. Derived-current sections (§3) were computed at 250 V and remain conservative for both SKUs (at 281.6–325.6 V the same power draws less current); they will be re-derived when the motor winding is fixed.

| Parameter | Symbol | Value | Unit | Tag |
|---|---|---|---|---|
| Minimum bus voltage (operating) | V_min | 220 (LFP SKU empty; 176 abs at 2.0 V/cell) | V DC | **[REQ]** rev 2026-07-30 |
| Nominal bus voltage | V_nom | 281.6 (LFP SKU) / 325.6 (NMC SKU) | V DC | **[REQ]** rev 2026-07-30 |
| Maximum bus voltage | V_max | 370 (NMC SKU full charge 369.6) | V DC | **[REQ]** rev 2026-07-30 |
| Hardware-capable envelope | — | 48–450 | V DC | **[SEL]** design retains original envelope as margin |
| Continuous power @ V_nom | P_cont | 15 | kW | **[REQ]** |
| Peak power @ V_nom | P_peak | 35 | kW | **[REQ]** |
| Peak duration | t_peak | 10 | s | **[SEL]** |

### 2.1 Power at other bus voltages

The power figures are defined **at 250 V nominal only**. The board enforces *current* limits, not power limits, so deliverable power scales with bus voltage:

| Bus voltage | Continuous | Peak | Note |
|---|---|---|---|
| 48 V | 2.9 kW | 6.7 kW | Current-limited |
| 250 V | **15 kW** | **35 kW** | Rated point |
| 450 V | 27 kW | 49 kW | Current-limited; **thermally constrained, see §11** |

At 450 V the current limits alone would permit 49 kW peak. The board is **not** rated to deliver this — switching losses scale with bus voltage, and the thermal design in §11 is sized for the 250 V rated point. Operation above 250 V must be derated. Quantifying that derating requires the loss model in §11.4 and is an open item.

---

## 3. Current ratings — DC bus vs phase

This distinction was the largest single error in the previous draft and deserves to be explicit.

### 3.1 DC bus current **[DER]**

```
I_dc,cont = P_cont / V_nom = 15 000 / 250 =  60 A
I_dc,peak = P_peak / V_nom = 35 000 / 250 = 140 A
```

### 3.2 Phase current **[DER]**

With space-vector PWM at full modulation, the maximum line-to-line RMS output is `V_ll = V_dc / √2 = 176.8 V` at 250 V bus. Taking inverter efficiency η = 0.97 and motor power factor cos φ = 0.95:

```
I_ph = (P × η) / (√3 × V_ll × cos φ)

I_ph,cont = (15 000 × 0.97) / (1.732 × 176.8 × 0.95) =  50.0 A rms
I_ph,peak = (35 000 × 0.97) / (1.732 × 176.8 × 0.95) = 116.7 A rms
```

**These are the values at full modulation, i.e. at high speed.** They are *not* the design maximum. At low speed the motor needs the same current for the same torque while the output voltage is small, so phase current — not power — is the binding constraint. The power stage must therefore be sized above the figures above to deliver full torque at low speed.

### 3.3 Design current capability **[SEL]**

| Parameter | Value | Basis |
|---|---|---|
| Continuous phase current | 75 A rms | 1.5 × I_ph,cont — full torque at low speed |
| Peak phase current (10 s) | 175 A rms | 1.5 × I_ph,peak |
| Instantaneous phase peak | 250 A | 175 × √2, rounded |
| Current sense full scale | ±300 A | Instantaneous peak + 20 % headroom |
| Hardware overcurrent trip | 280 A, adjustable | Below sense saturation, above legitimate peak |

The 1.5× factor is a judgement call. If the target motor and duty cycle are known, this should be revisited — it directly sets device count and cost.

### 3.4 DC-link ripple current **[DER]**

Worst-case DC-link RMS ripple in a 3-phase inverter approaches `0.6 × I_ph,rms`:

```
Continuous: 0.6 × 75  =  45 A rms
Peak:       0.6 × 175 = 105 A rms
```

This is the dominant constraint on DC-link capacitor selection — see §6.

---

## 4. Power stage

### 4.1 Switch voltage class **[SEL]**

Bus maximum is 450 V. With switching overshoot, stray inductance and regenerative transients, **1200 V class** devices are required. 650 V is not acceptable at a 450 V bus; 750–900 V parts exist but leave little margin for a first design.

### 4.2 Topology **[SEL]**

Three-phase two-level bridge, six switch positions. Baseline is a **single 1200 V six-pack power module** rather than discretes:

- One thermal interface instead of 18+
- Manufacturer-controlled internal layout and stray inductance
- Integrated NTC
- Removes the paralleling/current-sharing problem entirely

**Candidates [TBV]:**

| Technology | Example class | Trade-off |
|---|---|---|
| Si IGBT six-pack, 1200 V / ~200 A | Infineon EconoPACK / Semikron MiniSKiiP | Lower cost, ~96.5 % efficiency, more heat |
| SiC MOSFET six-pack, 1200 V | onsemi / Microchip / Wolfspeed modules | ~98 % efficiency, higher switching frequency, higher cost |

Every part number must be verified against a live datasheet and stocked distributor part before entering a BOM. **No part enters the BOM on the strength of a plausible-looking part number.**

### 4.3 Selection criteria

| Parameter | Requirement |
|---|---|
| V_CES / V_DS | ≥ 1200 V |
| I_C continuous @ T_c = 80 °C | ≥ 100 A |
| I_C peak, 10 s | ≥ 250 A |
| Integrated NTC | Required |
| Isolated baseplate | Required |
| Configuration | Six-pack (3 half-bridges) |

---

## 5. Gate drive

| Parameter | Requirement | Tag |
|---|---|---|
| Topology | Isolated, per switch position | **[SEL]** |
| Isolation | ≥ 3 kV rms, reinforced | **[DER]** from §10 |
| Drive voltage | +15 V / −8 V (IGBT) or +18 V / −4 V (SiC) | **[SEL]** |
| Peak gate current | ≥ 8 A | **[SEL]** |
| Desaturation detection | Required, per switch | **[SEL]** |
| Active Miller clamp | Required | **[SEL]** |
| Soft turn-off on fault | Required | **[SEL]** |
| Fault reporting | Per-channel, aggregated to supervisor | **[SEL]** |
| Dead time | Hardware-enforced, see §9.2 | **[REQ]** |

**Candidates [TBV]:** discrete isolated gate drivers with integrated desat (Infineon 1EDI/2ED-series, Broadcom ACPL-339J class), or a SCALE-2 driver core such as the 2SP0115T2A already characterised in `adaptor boards/power_integrations_2SP0115T2A/` in this repo. The existing scope captures at 80 A with 1.4 µs dead time are real measured data on that driver — worth reusing rather than rediscovering.

---

## 6. DC link

| Parameter | Value | Tag |
|---|---|---|
| Capacitance | ≥ 400 µF | **[SEL]** |
| Voltage rating | ≥ 800 V DC | **[DER]** — 450 V + transients + margin |
| Ripple current rating | ≥ 50 A rms @ 70 °C | **[DER]** from §3.4 |
| Technology | Metallised polypropylene film | **[SEL]** |
| ESL | As low as achievable; laminated busbar to module | **[SEL]** |

Film rather than electrolytic: the 45–105 A rms ripple from §3.4 is impractical for electrolytics at this voltage without a large parallel bank, and film gives far better lifetime at temperature.

400 µF is a starting point from the ~10–20 µF/kW rule of thumb. It must be confirmed against the actual switching frequency and the permitted bus voltage ripple. **[TBV]**

---

## 7. Precharge and discharge

Mandatory at 450 V. Omitting this destroys contactors and capacitors on first connection.

### 7.1 Precharge **[DER]**

Energy dissipated in the precharge resistor is independent of its value:

```
E = ½ C V²  =  0.5 × 400e-6 × 450²  =  40.5 J
```

| Parameter | Value | Derivation |
|---|---|---|
| Precharge resistor | 1.25 kΩ | τ = RC = 0.5 s |
| Peak inrush | 0.36 A | 450 V / 1250 Ω |
| Precharge duration | ~2.5 s | 5τ, to >99 % of bus |
| Resistor pulse energy | ≥ 40.5 J | Above; use ≥ 50 W wirewound or pulse-rated |

Sequence: precharge relay closes → bus monitored via §8.2 → main contactor commanded closed only when V_bus ≥ 95 % of supply → precharge relay opens. **The MCU commands both; neither may close without a valid bus voltage reading.**

### 7.2 Discharge **[DER]**

| Mechanism | Requirement | Implementation |
|---|---|---|
| Passive bleeder | < 60 V within 60 s | 75 kΩ across bus → τ = 30 s; 2.7 W at 450 V |
| Active discharge | < 60 V within 5 s, commanded | Switched resistor, thermally rated for single-shot |

Passive bleeding alone at 5 s would dissipate >30 W continuously — unacceptable. Hence the split.

---

## 8. Sensing

### 8.1 Phase current

| Parameter | Requirement |
|---|---|
| Channels | 3 (one per phase) |
| Range | ±300 A instantaneous |
| Isolation | Reinforced, ≥ 3 kV rms |
| Bandwidth | ≥ 500 kHz (≥ 5× max PWM frequency) |
| Latency | < 2 µs to ADC-ready |

**Three phase measurements, not one bus measurement.** VESC FOC reconstructs the current vector from per-phase samples; a single DC-link shunt cannot provide this.

**Candidates [TBV]:** isolated shunt amplifier (AMC1301/AMC1311 class) with a ~0.5 mΩ shunt, or closed-loop Hall/fluxgate transducers (LEM class). If shunts are used, the shunt value must be chosen so full-scale current maps to most of the amplifier's input range — at ±300 A into a ±250 mV input, that is ~0.8 mΩ, not the 100 µΩ that would waste 94 % of the range.

### 8.2 Bus voltage

| Parameter | Requirement |
|---|---|
| Range | 0–500 V |
| Accuracy | ±1 % over range |
| Isolation | Reinforced |
| Divider construction | **Series string**, ≥ 4 resistors |

A single chip resistor must not span 450 V — typical 1206 parts are rated ~200 V working. A series string is required for voltage rating *and* for creepage across the part.

The divider must map 500 V to most of the 0–3.3 V ADC range (i.e. ~150:1, giving 3.0 V at 450 V), not to a fraction of it. If a unity-gain buffer follows the divider, the divider ratio alone sets the scaling — there is no gain stage to recover range later.

### 8.3 Temperature

| Sensor | Location | Purpose |
|---|---|---|
| Module NTC | Inside power module | Junction proxy, fastest response |
| Heatsink/coldplate NTC | Thermal path | Cooling system health |
| Board NTC | Near control electronics | Ambient/enclosure |

### 8.4 Rotor position

All four interfaces are required.

| Interface | Implementation | Note |
|---|---|---|
| Hall sensors | 3 digital inputs, filtered | VESC standard, startup |
| ABI / quadrature encoder | Timer in encoder mode + index | VESC standard |
| Resolver | AD2S1205 resolver-to-digital | See below |
| SinCos / SSI | 2 ADC channels + SPI | VESC supports SinCos natively |

**On the resolver:** mainline VESC firmware has no resolver driver. The AD2S1205 solves this — it provides **incremental encoder emulation outputs (A, B, NM)**, so the resolver presents to the MCU as a standard ABI encoder that VESC already supports. This is very likely why the original PALTA board used that part. Its SPI/parallel absolute output can additionally be read for absolute position at startup. Carrying over `pcb_design/resolver.sch` is a strong starting point.

---

## 9. Protection

### 9.1 Protection summary

| Function | Threshold | Response |
|---|---|---|
| Overcurrent (hardware) | 280 A instantaneous | Latched shutdown, < 1 µs |
| Desaturation | Per gate driver | Soft turn-off + latch |
| Bus overvoltage | 400 V (rev 2026-07-30; was 490 V for the 450 V envelope) | Latched shutdown |
| Bus undervoltage | 200 V (rev 2026-07-30; below LFP SKU empty, above chargers' floor region) | Inhibit switching |
| Overtemperature | Module 125 °C (IGBT) / 150 °C (SiC) | Derate, then shutdown |
| Gate supply UVLO | Per driver | Inhibit |
| Watchdog timeout | — | Latched shutdown |

Bus OVP is set at **400 V** (rev 2026-07-30): above the NMC SKU's 369.6 V full-charge voltage plus regen margin, and far below the 1200 V device rating. One threshold covers both SKUs. The margin exists to catch regenerative overvoltage before the devices see it.

### 9.2 Hardware interlocks — carry over from PALTA

The most valuable feature of the existing board in this repository is that overcurrent and shoot-through protection live in **discrete logic, independent of firmware** (`pcb_design/supervisor.sch`). Firmware cannot override them. This must be carried forward:

| Interlock | Implementation |
|---|---|
| PWM overlap / shoot-through elimination | Combinational logic gating complementary pairs |
| Hardware dead-time insertion | Independent of MCU timer configuration |
| Overcurrent latch | Comparator + flip-flop, requires explicit reset |
| Fault → PWM disable | Drives **TIM1_BKIN**; silicon tri-states PWM without firmware involvement |

Routing the aggregated fault to TIM1's break input means an MCU lockup, a firmware bug or a bad configuration cannot leave the bridge conducting.

---

## 10. Isolation, creepage and clearance

Working voltage 450 V DC. Basis: IEC 60664-1, pollution degree 2, material group IIIa, overvoltage category II. **[TBV]** — final values must be confirmed against the target compliance standard once the end application is known.

| Barrier | Clearance | Creepage | Insulation |
|---|---|---|---|
| Phase-to-phase, phase-to-DC | ≥ 2.0 mm | ≥ 3.2 mm | Functional |
| Power stage → control | ≥ 3.2 mm | ≥ 6.4 mm | Basic |
| Power stage → user-accessible (USB, CAN, encoder) | ≥ 5.5 mm | ≥ 8.0 mm | Reinforced |

| Isolated component | Rating |
|---|---|
| Gate drivers | ≥ 3 kV rms reinforced |
| Current sense | ≥ 3 kV rms reinforced |
| Bus voltage sense | ≥ 3 kV rms reinforced |
| CAN transceiver | ≥ 3 kV rms reinforced |
| Auxiliary supply transformer | ≥ 4 kV rms |

USB is user-accessible and directly connected to a laptop. It sits behind reinforced insulation, with no exception.

---

## 11. Auxiliary power

The previous draft had no viable path from a 48–450 V bus to control power. This is a genuinely hard part of the design.

### 11.1 Requirement

| Parameter | Value |
|---|---|
| Input range | 220–370 V DC (1.7:1), tolerant to 450 V (rev 2026-07-30 — was 48–450 V / 9.4:1) |
| Topology | Isolated flyback **[SEL]** |
| Primary switch rating | ≥ 900 V **[DER]** |

### 11.2 Outputs

| Rail | Voltage | Isolation | Load |
|---|---|---|---|
| Gate drive, high side ×3 | +15 / −8 V | Independent, reinforced | Per-channel |
| Gate drive, low side | +15 / −8 V | Common (shared emitter) | 3 channels |
| Control logic | +5 V, +3.3 V | Secondary | MCU, sensing |
| Isolated CAN | +5 V | Independent | Transceiver |
| Contactor / fan | +12 V | Secondary | External loads |

**Candidates [TBV]:** Power Integrations InnoSwitch3-EP or LinkSwitch families with 900 V integrated FETs, or a discrete flyback with a 1000 V MOSFET. Wide-range input at 9.4:1 is the difficult requirement — verify the chosen controller supports it at full load.

### 11.3 Auxiliary input

A **12–24 V external auxiliary input [SEL]** is required in addition to the HV-derived supply. Control electronics must be able to power up before the DC bus is live, to sequence precharge and to permit safe bench work and diagnostics on a de-energised bus.

### 11.4 Thermal

| Case | Efficiency | Loss @ 15 kW |
|---|---|---|
| Si IGBT | ~96.5 % | ~525 W |
| SiC MOSFET | ~98 % | ~300 W |

**300–525 W of continuous dissipation requires liquid cooling.** A cold plate is the baseline. Forced air is viable only at a substantially reduced continuous rating, which would need to be characterised and stated. The previous draft's claim that forced air suffices rested on a fabricated 5 mΩ figure for a 1200 V device; real 1200 V devices are 25–80 mΩ, an order of magnitude higher.

| Parameter | Target |
|---|---|
| Coolant | Water/glycol, ≤ 65 °C inlet |
| Junction temperature | ≤ 125 °C (IGBT) / ≤ 150 °C (SiC) |
| Design margin | ≥ 25 °C at rated continuous |

---

## 12. MCU and VESC compatibility

### 12.1 Selection **[REQ]**

**STM32F405VGT6, LQFP100.**

Same die and firmware target as the VESC reference design, so mainline `bldc` firmware applies, with 100 pins instead of the 64 on the `RGT6` used by the original PALTA board — enough IO for all four position-feedback interfaces plus CAN, USB and the supervisor without pin conflicts.

| Resource | Figure |
|---|---|
| Core | Cortex-M4F, 168 MHz |
| Flash / SRAM | 1 MB / 192 KB |
| ADC | 3 × 12-bit, 2.4 MSPS |
| Advanced timer | TIM1 (complementary PWM + dead time + break) |
| CAN | **2 × bxCAN 2.0B** |
| USB | OTG FS |

**The STM32F405 has no CAN FD.** It has classic bxCAN 2.0B. This is a hard constraint of the part and is what VESC's CAN protocol uses. Any requirement for CAN FD would mean leaving the F4 family and porting the firmware.

### 12.2 Anchor pin assignments **[SEL]**

Only assignments verified against the STM32F405 alternate-function table are listed. **A complete pinout is deliberately not included in this document** — it belongs in schematic capture, against the datasheet, and it is exactly where the previous attempt produced 96 fabricated power pins and assigned every GPIO on top of them.

| Function | Pins | AF |
|---|---|---|
| PWM high side | PA8, PA9, PA10 | TIM1_CH1/2/3 |
| PWM low side | PB13, PB14, PB15 | TIM1_CH1N/2N/3N |
| **Fault → PWM disable** | PB12 | **TIM1_BKIN** |
| CAN1 | PB8 / PB9 | CAN1_RX / TX |
| USB | PA11, PA12 | OTG_FS_DM / DP |
| SWD | PA13, PA14 | SWDIO / SWCLK |

Note `TIM1_CH1N/2N/3N` are `PB13/14/15` (or `PE8/10/12`) — **not** `PE13/14/15`, which are `CH3`, `CH4` and `BKIN` respectively.

### 12.3 Firmware

A new hardware target in the VESC `bldc` firmware, following the pattern of `HW_VERSION_PALTA` in this repo's README — `hw_mcuc.h` / `hw_mcuc.c` defining pin mapping, current-sense scaling, voltage divider ratio and dead time. Configuration through VESC Tool over USB or CAN.

---

## 13. Connectors and mechanical

| Interface | Requirement |
|---|---|
| DC input | Busbar / M6 studs, or HV-rated connector (Amphenol PowerLok class) **[TBV]** |
| Motor phases | Busbar / M6 studs, 3× |
| CAN | Isolated, 120 Ω terminated |
| USB | USB-C, reinforced isolation |
| Encoder / resolver | Shielded, sealed |
| Contactor control | 2 outputs (main, precharge), flyback-protected |

**XT90 connectors are not acceptable** at 450 V. They are LiPo battery connectors with insufficient voltage rating and creepage for this bus.

---

## 14. Open items

Ordered by how much they would change the design.

| # | Item | Blocks |
|---|---|---|
| 1 | Target motor and duty cycle — sets the §3.3 1.5× current factor | Device count, cost, thermal |
| 2 | Power module selection: Si IGBT vs SiC | Efficiency, cooling, gate drive, cost |
| 3 | Derating curve for 250–450 V operation | Safe operating area at high bus |
| 4 | Compliance target (industrial / automotive / none) | §10 creepage, certification |
| 5 | DC-link capacitance vs switching frequency and bus ripple | §6 |
| 6 | Cooling: cold plate design and coolant availability | §11.4 |
| 7 | Isolated aux supply controller supporting 9.4:1 input range | §11.1 |
| 8 | Whether the DC-link and power module are on this PCB or a busbar sub-assembly | Whole mechanical concept |

---

## 15. Deliberately carried over from the existing design

| From | What | Why |
|---|---|---|
| `pcb_design/supervisor.sch` | Firmware-independent overcurrent latch and shoot-through interlock | The single most valuable feature of the original board |
| `pcb_design/resolver.sch` | AD2S1205 resolver front end | Proven, and its ABI emulation makes VESC support free |
| `adaptor boards/power_integrations_2SP0115T2A/` | Gate drive approach and measured dead-time data | Real scope captures at 80 A, 1.4 µs dead time |
| `pcb_design/CAN.sch` | Isolated CAN topology | Proven |

---

*Prepared as the architecture baseline for MCU-C. No part number in this document should be ordered before datasheet verification.*
