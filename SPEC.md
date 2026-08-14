# MCU-C — Integrated 3-Phase Inverter, System Specification

**Revision:** 0.2 (target motor fixed; currents re-derived from EMRAX 188 HV)
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

> **Pack architecture: 88S1P dual-chemistry (D027).** Two SKUs share one fixture and one inverter —
> LFP 22 Ah "Life" (281.6 V nominal, 220–321 V, 6.2 kWh) and NMC 32 Ah "Range" (325.6 V nominal,
> 264–370 V, 10.4 kWh), both Desten 10135170 pouches, both 6C-charge rated. The operating window is
> therefore **220–370 V**. The original 48–450 V envelope is retained below as *hardware capability*:
> every part selected against it (D014 aux supply, D016 1200 V module, §8.2 divider, HV creepage)
> keeps its margin unchanged, so this decision re-selects nothing.

| Parameter | Symbol | Value | Unit | Tag |
|---|---|---|---|---|
| Minimum bus voltage (operating) | V_min | 220 — LFP SKU empty; 176 absolute at 2.0 V/cell | V DC | **[REQ]** D027 |
| Nominal bus voltage | V_nom | 281.6 (LFP SKU) / 325.6 (NMC SKU) | V DC | **[REQ]** D027 |
| Maximum bus voltage (operating) | V_max | 370 — NMC SKU full charge, 369.6 | V DC | **[REQ]** D027 |
| Hardware-capable envelope | — | 48–450 | V DC | **[SEL]** retained as design margin |
| Continuous power @ 250 V rated point | P_cont | 15 | kW | **[REQ]** |
| Peak power @ 250 V rated point | P_peak | 35 | kW | **[REQ]** |
| Peak duration | t_peak | 120 | s | **[REQ]** — matched to the motor's S2 2 min peak rating (§2.2) |

**Thermal consequence of the 120 s peak:** the power module baseplate, cold plate and coolant loop have thermal time constants of tens of seconds, so a 120 s peak is **quasi-steady-state** for them. The cooling system must be sized for peak-condition losses (§11.4), not continuous-rated losses. Only the silicon junction itself (τ ~ ms–s) sees the peak as a transient.

### 2.1 Power at other bus voltages

The power figures are defined **at 250 V nominal only**. The board enforces *current* limits, not power limits, so deliverable power scales with bus voltage:

| Bus voltage | Continuous | Peak | Note |
|---|---|---|---|
| 48 V | 2.9 kW | 6.7 kW | Current-limited |
| 250 V | **15 kW** | **35 kW** | Rated point |
| 450 V | 27 kW | 49 kW | Current-limited; **thermally constrained, see §11** |

At 450 V the current limits alone would permit 49 kW peak. The board is **not** rated to deliver this — switching losses scale with bus voltage, and the thermal design in §11 is sized for the 250 V rated point. Operation above 250 V must be derated. Quantifying that derating requires the loss model in §11.4 and is an open item.

**Where the D027 operating window sits:** both SKU nominals, 281.6 V and 325.6 V, fall between the 250 V rated point and 450 V, so the rows above bracket them. Deliverable power at those nominals is correspondingly above the 15/35 kW rated figures at the same current limits — and correspondingly subject to the derating this section leaves open. The rated point stays at 250 V because §3's currents, not the bus voltage, are what the board enforces.

### 2.2 Target motor **[REQ]**

**EMRAX 188, High Voltage winding, or similar.** Figures below are from the EMRAX 188 datasheet v1.6 (verified 2026-07-31, emrax.com):

| Parameter | Value | Note |
|---|---|---|
| Type | Axial flux PMSM, 10 pole pairs, star | 188 × 79 mm, 7.1–7.9 kg |
| Peak power | 60 kW, S2 2 min | At 6500 rpm; requires 660 V DC (HV winding) |
| Continuous power | 27 / 34 / 37 kW | Air / liquid / combined cooling |
| Peak torque | 100 Nm | = 190 A rms × Kt |
| Continuous torque | 40 / 52 / 56 Nm | Air / liquid / combined cooling |
| Max speed | 8000 rpm | 1333 Hz electrical at 10 pole pairs |
| **Peak motor current (HV)** | **190 A rms** | S2 2 min |
| **Continuous motor current (HV)** | **100 A rms** | |
| Kt (HV) | 0.54 Nm/A rms | |
| Kv at nominal load (HV) | 13.61 rpm/V DC | 17.73 no-load, 9.81 at peak load |
| Phase resistance (HV, 25 °C) | 14.37 mΩ | |
| Ld, one phase (HV) | 188.5 µH | |
| Winding temperature sensor | **KTY 81/210** | Board must provide an input — see §8.3 |
| Position sensor options | Resolver / encoder | Matches §8.4; AD2S1205 carry-over applies |
| Max test voltage | 833 V | All variants |

**Why the HV winding [SEL]:** at 250 V nominal bus the HV winding reaches ≈ 3400 rpm under load (13.61 × 250), and 100 Nm at 3400 rpm ≈ 35.6 kW — the motor's envelope at our bus lands almost exactly on the 35 kW peak rating point of §2. At 450 V it reaches ≈ 6100 rpm. The MV winding would need 310 A rms peak and the LV variants 390–900 A rms — all far beyond a sensible power stage for this power level. The full 60 kW / 6500 rpm motor capability requires 660 V and is not reachable on this 450 V bus; this is accepted.

**Against the D027 pack (checked 2026-08-14):** the HV winding still fits. At the LFP SKU's 281.6 V it reaches ≈ 3830 rpm under load (13.61 × 281.6) and at the NMC SKU's 325.6 V ≈ 4430 rpm — both above the 3400 rpm the 250 V rated point gives, so the operating window strictly improves the speed envelope. §3's currents are derived from the motor's own ratings (D011/D012), not from bus voltage, so nothing in §3 moves. What binds first at those nominals is the board's current limit and the §11 thermal derating, not the winding.

**Winding variant must be confirmed at motor order time.** If a different variant or motor is chosen, §3.3 must be re-derived.

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

### 3.3 Design current capability **[DER]** — from the EMRAX 188 HV ratings

The earlier 1.5× guess (75/175 A rms) is superseded. With the target motor known (§2.2), the power stage is sized to the motor's own current ratings, making the system motor-limited rather than inverter-limited:

| Parameter | Value | Basis |
|---|---|---|
| Continuous phase current | 100 A rms | Motor continuous current, HV winding |
| Peak phase current (120 s) | 190 A rms | Motor peak current, S2 2 min; board peak duration matched to the motor (§2) |
| Instantaneous phase peak | 270 A | 190 × √2, rounded |
| Current sense full scale | ±325 A | Instantaneous peak + 20 % headroom |
| Hardware overcurrent trip | 300 A, adjustable | Above legitimate 270 A peak, below sense saturation |

Full 100 Nm peak torque needs 100 / 0.54 = 185 A rms — inside the 190 A peak limit. Full continuous torque (56 Nm, combined-cooled motor) needs 104 A rms; at the 100 A board limit, continuous torque is 54 Nm — accepted, the difference is within the motor's cooling-configuration spread.

**[TBV]** Confirmed only for the HV winding. Re-derive if the winding variant changes at order time.

### 3.4 DC-link ripple current **[DER]**

Worst-case DC-link RMS ripple in a 3-phase inverter approaches `0.6 × I_ph,rms`:

```
Continuous: 0.6 × 100 =  60 A rms
Peak:       0.6 × 190 = 114 A rms
```

This is the dominant constraint on DC-link capacitor selection — see §6.

---

## 4. Power stage

### 4.1 Switch voltage class **[SEL]**

Bus maximum is 450 V. With switching overshoot, stray inductance and regenerative transients, **1200 V class** devices are required. 650 V is not acceptable at a 450 V bus; 750–900 V parts exist but leave little margin for a first design.

### 4.2 Topology **[SEL]**

Three-phase two-level bridge, six switch positions. Baseline is a **single 1200 V SiC MOSFET module** (technology decided — D016) rather than discretes:

- One thermal interface instead of 18+
- Manufacturer-controlled internal layout and stray inductance
- Integrated NTC
- Removes the paralleling/current-sharing problem entirely

**Candidates — verified stocked parts, DigiKey 2026-07-31 (full analysis in `docs/SI_VS_SIC.md`):**

**Technology: SiC (D016).** Module candidates, verified stocked (DigiKey 2026-07-31, analysis in `docs/SI_VS_SIC.md`):

| Rank | Part | Rating | Price qty 1 | Note |
|---|---|---|---|---|
| 1 | **Infineon FS02MR12A8MA2B**, HybridPACK Drive G2, CoolSiC | 1.9 mΩ, 390 A class | $767.12 (51 pcs, 39-wk lead after stock) | Stocked today; automotive pin-fin direct-cooled base — the cold plate becomes a coolant jacket sealing against the module's pin-fin baseplate, not a flat plate. **Buy at design commit, not at layout completion** |
| 2 | Microchip MSCSM120TAM11CTPAG, SP6-P | 10.4 mΩ, 251 A | $769.08 | Right-sized, flat base, but zero stock — orderable, lead unknown |

At 10 k/yr scale, RFQ custom right-sized six-packs from Infineon / Semikron-Danfoss / onsemi instead of catalog parts.

Every part number must be verified against a live datasheet and stocked distributor part before entering a BOM. **No part enters the BOM on the strength of a plausible-looking part number.**

### 4.3 Selection criteria

| Parameter | Requirement |
|---|---|
| V_CES / V_DS | ≥ 1200 V |
| I_C continuous @ T_c = 80 °C | ≥ 200 A |
| Sustained 190 A rms for 120 s | Required — quasi-steady-state thermally, see §2 and §11.4 |
| Repetitive peak | ≥ 270 A instantaneous |
| Integrated temperature sensor | Required — the selected G2 module provides a **sense diode per phase** (TS1–TS3 pin pairs), not an NTC |
| Isolated baseplate | Required |
| Configuration | Six-pack (3 half-bridges) |

---

## 5. Gate drive

| Parameter | Requirement | Tag |
|---|---|---|
| Topology | Isolated, per switch position | **[SEL]** |
| Isolation | ≥ 3 kV rms, reinforced | **[DER]** from §10 |
| Drive voltage | **+18 V on / −5 V off** — the module datasheet's switching condition. (+15 V on is permitted but costs +26 % conduction loss: R_DS,on 2.40 mΩ vs 1.90 mΩ) | **[DER]** — FS02MR12A8MA2B datasheet |
| CMTI | ≥ 100 V/ns (module's actual dv/dt ≈ 14 V/ns — margin is comfortable) | **[SEL]** |
| Peak gate current | ≥ 8 A available | **[SEL]** — Q_G = 1.19 µC; datasheet-matched switching (R_G,on 12 Ω, R_G,int 0.66 Ω) draws only ~2 A peak, so 8 A is margin for faster external R_G, not a hard need |
| Desaturation detection | Required, per switch | **[SEL]** |
| Active Miller clamp | Required | **[SEL]** |
| Soft turn-off on fault | Required | **[SEL]** |
| Fault reporting | Per-channel, aggregated to supervisor | **[SEL]** |
| Dead time | Hardware-enforced, see §9.2 | **[REQ]** |

**Module gate-interface facts (FS02MR12A8MA2B datasheet, verified 2026-07-31):** Q_G 1.19 µC; R_G,int 0.66 Ω; per-switch gate, dual Kelvin-source and drain-sense pins (PressFIT — the PCB needs the AN-G2-ASSEMBLY drill/heat-stake pattern); the drain-sense pins are the DESAT connection. Module isolation 4.2 kV rms.

**Driver candidates — datasheet- and stock-verified 2026-07-31:**

| Rank | Part | Key figures | Price / stock |
|---|---|---|---|
| 1 | **Infineon 1ED3491MC12M** (EiceDRIVER X3 Analog) | Reinforced 1767 V pk VIORM (IEC 60747-17) / 5.7 kV rms; **200 V/ns**; ±9–11 A; adjustable DESAT blanking; CLAMPDRV Miller clamp; 16-step current-source soft-off; FLT_N + RDYC per channel; +15/−5 explicitly supported | $6.31 / **2,670 in stock** |
| 2 | TI UCC21755-Q1 | Reinforced 2121 V pk; 150 V/ns; ±10 A; **5.0 V SiC-optimised DESAT threshold**; internal 4 A clamp; soft-off; AEC-Q100 grade 1 | $8.61 / 1,510 |
| 3 | TI UCC21750 | Same family, 9.15 V DESAT, industrial | $4.69 / 8,996 |
| 4 | ST STGAP3SXS | Reinforced VDE 0884-17 (VIORM 1200 V pk, 5.7 kV rms UL); **200 V/ns min**; 10 A; SiC 6 V DESAT; adjustable soft-off; DIAG+RDY. Cheapest qualifier | $4.85 / 1,508 |
| 5 | onsemi NCD57000 | 5 kV rms UL, VDE 0884-11 VIORM 1200 V pk; 100 V/ns min; 7.8 A; 9 V DESAT; clamp; soft-off | $6.84 / 1,438 |
| — | Infineon 1EDI3035AS (the automotive part on Infineon's own EV GB HPD2 SIC driver board for this exact module) | Reinforced 8 kV pk; 150 V/ns; 20 A; DESAT+BIST, ASC, ASIL-B SEooC | $4.06 / **0 stock** — the reference design to copy, not the purchasable part today |

Ruled out on verified datasheet grounds: Skyworks Si828x (no VDE 0884 VIORM — reinforced only per IEC 62368 at 600 V working; effectively out of stock), ADI ADuM4136 (VIORM 849 V pk **basic**, no Miller clamp), Broadcom ACPL-355JC (0 stock, 25 wk, not automotive), ST STGAP1AS (obsolete; 2.5 kV rms and 50 V/ns — fails twice), onsemi NCP51705 (not isolated).

**Isolated gate supplies [TBV]:** each channel needs +18/−5 V class isolated DC/DC. Murata MGJ2-series is purpose-built (+15/−5 variant $8.96) but carries two problems: **0 stock / 19-wk lead**, and its reinforced certification (UL 60950) covers only **150 V rms working voltage** — the 5.2 kV figure is a test voltage, continuous barrier rating 2.4 kV DC *functional*. At a 450 V bus the reinforced barrier must therefore be provided by the driver IC, with the supply transformer treated as functional isolation — acceptable only if the compliance target (§14 item 4) permits it, else the discrete transformer must itself be certified. Baseline: discrete push-pull (TI SN6505B + gate-drive transformer wound/certified to the required barrier), with Infineon's eval-board approach (boost + self-oscillating half-bridge + transformers) as the volume alternative. Supply span must match the final gate levels.

The 2SP0115T2A SCALE-2 driver characterised in `adaptor boards/power_integrations_2SP0115T2A/` is IGBT-oriented; its measured dead-time/propagation data remains useful reference only.

---

## 6. DC link

| Parameter | Value | Tag |
|---|---|---|
| Capacitance | ≥ 400 µF — SiC selected (D016), f_sw baseline 25 kHz | **[DER]** — see §6.1 |
| Voltage rating | ≥ 800 V DC | **[DER]** — 450 V + transients + margin |
| Ripple current rating | ≥ 80 A rms @ 70 °C (bank) | **[DER]** — see §6.1 |
| Technology | Metallised polypropylene film, parallel bank | **[SEL]** |
| ESL | As low as achievable; laminated busbar to module | **[SEL]** |

Film rather than electrolytic: the 60–114 A rms ripple from §3.4 is impractical for electrolytics at this voltage without a large parallel bank, and film gives far better lifetime at temperature.

### 6.1 Sizing derivation **[DER]**

**Voltage ripple sets capacitance.** Worst-case bound for a two-level VSI, with permitted peak-to-peak bus ripple ΔV_pp = 1.5 % of V_nom = 3.75 V:

```
C ≥ I_ph,pk / (8 × f_sw × ΔV_pp)

f_sw = 25 kHz:  C ≥ 270 / (8 × 25 000 × 3.75) = 360 µF  →  400 µF OK
f_sw = 20 kHz:  C ≥ 450 µF                              →  400 µF gives 1.7 %
f_sw = 12 kHz:  C ≥ 750 µF                              →  400 µF gives 2.8 %
```

So **400 µF is confirmed for f_sw ≥ ~23 kHz**, which a SiC module supports comfortably (VESC default zones are 20–30 kHz). A 1200 V Si IGBT module realistically switches at 10–15 kHz at these currents, which roughly doubles the required capacitance — a cost/volume input to the Si-vs-SiC decision (§14 item 2).

At 48 V bus the same absolute ripple is ~8 % of bus. Deliverable power there is ≤ 2.9 kW and VESC samples bus voltage every cycle, so this is acceptable, but it is a real limit on control margin at minimum voltage — flagged, not hidden.

**Ripple current sets the bank, and is the binding constraint.** 60 A rms continuous plus 114 A rms held for the full 120 s peak (§3.4). Film capacitor hotspot time constants are minutes, so a 120 s peak at ~2× rating is *not* automatically safe. Bank rating ≥ 80 A rms @ 70 °C, with the 114 A / 120 s repetitive duty verified against the manufacturer's thermal model **[TBV]**. Practically: 4–6 parallel 80–120 µF / 900 V film blocks at 20–30 A rms each, which lands at ≥ 400 µF anyway.

---

## 7. Precharge and discharge

Mandatory at 450 V. Omitting this destroys contactors and capacitors on first connection.

### 7.1 Precharge **[DER]**

Energy dissipated in the precharge resistor is independent of its value:

```
E = ½ C V²  =  0.5 × 400e-6 × 450²  =  40.5 J
```

(If the Si path is taken and capacitance rises to 750 µF per §6.1, this becomes 76 J and the resistor pulse rating below scales with it. **[TBV]**)

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
| Range | ±325 A instantaneous |
| Isolation | Reinforced, ≥ 3 kV rms |
| Bandwidth | ≥ 150 kHz | 
| Latency | < 5 µs to ADC-ready |

Bandwidth/latency re-derived for the actual 25 kHz switching (D016): 5× f_sw = 125 kHz; the original ≥ 500 kHz / < 2 µs figures assumed 100 kHz PWM. VESC samples currents synchronised to the PWM midpoint, so 3 µs transducer response at a 40 µs period is comfortable. **[DER]**

**Three phase measurements, not one bus measurement.** VESC FOC reconstructs the current vector from per-phase samples; a single DC-link shunt cannot provide this.

**Selection (D019, candidate level — verified 2026-07-31):** **LEM HOYS 200-S/SP33** ×3 — Ipn 200 A rms, range ±500 A, 2.3 mV/A from a 1.65 V reference on a single 3.3 V supply (natively ADC-mapped, ratiometric), 180 kHz, 3 µs response, reinforced per IEC 61800-5-1 (tested 5.4 kV rms), $37.11 qty 1, stocked. Its built-in OCD pin trips at 2.92 × Ipn ≈ 584 A — too high for the 300 A hardware trip — so **the §9.1 trip comes from an external window comparator per phase** on the analog output (±0.69 V about V_ref at 300 A), open-drain wire-OR onto the supervisor's OC_TRIP, restoring the original PALTA three-comparator structure.

**Shunt route — evaluated and rejected [DER]:** at ±250 mV full scale the required 0.75 mΩ dissipates 27 W at 190 A rms (not a PCB part). A 0.1 mΩ busbar shunt (1 W cont / 3.6 W peak) works electrically, but the clean readout is a ΔΣ modulator (AMC1306M05) and **the STM32F405 has no DFSDM peripheral** — it cannot filter a ΔΣ bitstream without consuming the CPU (confirmed against ST AN4821). The analog fallback (AMC1302, 280 kHz, 1.6–2.5 µs) had zero stock / 16-week lead at check. Precedent agrees: Tesla's shunt+ΔΣ phase sensing rides on a C2000 with hardware SDFM; the VESC-based Axiom (100 kW, 400 V) uses LEM aperture transducers; Infineon's own G2 eval uses coreless TLE4973 modules that are not purchasable at distribution (MOQ 5000 / Tier-1 only).

### 8.2 Bus voltage

| Parameter | Requirement |
|---|---|
| Range | 0–500 V |
| Accuracy | ±1 % over range |
| Isolation | Reinforced |
| Divider construction | **Series string**, ≥ 4 resistors |

A single chip resistor must not span 450 V — typical 1206 parts are rated ~200 V working. A series string is required for voltage rating *and* for creepage across the part.

**Implementation (D022, parts verified 2026-08-02):** series string 4× 750 kΩ (124.5 V and 20.7 mW per part at 500 V — inside 1206 ratings) + 12.0 kΩ bottom → 1.992 V at 500 V into a **TI AMC1311BDWV** isolated amplifier (0–2 V input, reinforced, V_IOWM 2120 V DC, BW ≥220 kHz, $10.02 stocked in tubes; reel and AEC-Q variants exist). Total divider drain 83 mW. The AMC1311's differential output (±2 V about 1.44 V) needs one diff-to-single-ended op-amp stage to the 0–3.3 V ADC — the gain of that stage sets final scaling. HV-side 3.3 V supply: LDO from the VGD_LS rail referenced to the low-side Kelvin/DC_BUS_N region **[TBV — noise review]**; TI's alternative pattern is a dedicated SN6501-class isolated supply.

### 8.3 Temperature

| Sensor | Location | Purpose |
|---|---|---|
| Module TS diodes ×3 | Inside power module | **Provision only in rev A (D022).** The TS pins carry no isolation rating and the only Infineon-documented readout is the HV-side ADC of the (zero-stock) 1EDI3035AS driver — no control-GND-referenced readout is supportable. Pads routed to the HV zone, unpopulated |
| **Coldplate NTC (module baseplate)** | Bolted at the module mounting | Primary module thermal protection: TDK B57861S0103F040 (10 k 1 %, B 3988 K, AEC-Q200, glass bead). Read as VESC "MOSFET temp" |
| Board NTC | Near control electronics | Murata NCU18XH103F6SRB (successor — NCP18 is NFND) |
| **Motor winding** | Inside motor stator (§2.2) | Motor thermal protection; input via motor connector |

**Motor sensor reality check (D022):** the KTY 81/210 that EMRAX historically fitted is **obsolete** (NXP EOL 2020, residual stock only). VESC firmware supports NTC 10k, KTY83, KTY84-130, PT1000 and PTC 1k natively. The front end is therefore a resistor-selectable bias network covering PT1000 / KTY8x / NTC 10k, and the motor should be ordered with a **PT1000** option where available. **[SEL]**

**Overtemperature protection consequence:** with TS diodes unread in rev A, the §9.1 overtemp function derives from the coldplate NTC with a conservative threshold plus the drivers' DESAT as the fast backstop; junction excursions during the 120 s peak must be covered by the thermal design margin (§11.4), verified at bring-up with a calibrated load step. **[DER]**

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
| Overcurrent (hardware) | 300 A instantaneous | Latched shutdown, < 1 µs |
| Desaturation | Per gate driver | Soft turn-off + latch |
| Bus overvoltage | 400 V (D027; was 490 V for the 48–450 V envelope) | Latched shutdown |
| Bus undervoltage | 200 V (D027; was 45 V) | Inhibit switching |
| Overtemperature | Module 150 °C (SiC, D016) | Derate, then shutdown |
| Gate supply UVLO | Per driver | Inhibit |
| Watchdog timeout | — | Latched shutdown |

Bus OVP is set at **400 V** (D027): above the NMC SKU's 369.6 V full-charge voltage with regen margin, below the retained 450 V envelope, and far below the 1200 V device rating. One threshold covers both SKUs. The margin exists to catch regenerative overvoltage before the devices see it. UVLO at **200 V** sits below the LFP SKU's 220 V empty point.

**Both thresholds are evaluated in firmware**, not by a comparator: §8.2's bus sense is an analog measurement path (divider → AMC1311B → ADC) with no on-board OVP/UVLO comparator, so D027 changes numbers in firmware and in this document, and no schematic part. The 0–500 V sense range covers both thresholds as built; rescaling the divider to 0–400 V would buy resolution and is optional, not required.

### 9.2 Hardware interlocks — carry over from PALTA

The most valuable feature of the existing board in this repository is that overcurrent and shoot-through protection live in **discrete logic, independent of firmware** (`pcb_design/supervisor.sch`). Firmware cannot override them. This must be carried forward:

| Interlock | Implementation |
|---|---|
| PWM overlap / shoot-through elimination | Combinational logic gating complementary pairs — **ported, verified** (supervisor sheet) |
| Hardware dead-time insertion | **Corrected (D018):** the PALTA circuit never inserted dead time — it only eliminates overlap. Dead time is generated by TIM1's silicon dead-time generator (firmware-configured, hardware-enforced); the firmware-independent backstop is the overlap eliminator plus a **turn-on RC delay network per gate-drive input** in the gate_drive sheet, ~250 ns initial value **[TBV]** against switching characterisation |
| Overcurrent latch | Comparator + flip-flop, requires explicit reset — **ported, verified** |
| Fault → PWM disable | Drives **TIM1_BKIN** (PB12, netlist-verified); silicon tri-states PWM without firmware involvement |

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
| Input range | 48–450 V DC (9.4:1), tolerant to 500 V |
| Input range actually seen (D027) | 220–370 V DC (1.7:1) |
| Topology | Isolated flyback **[SEL]** |
| Primary switch rating | ≥ 900 V **[DER]** |

**D027 does not reopen this section.** The 9.4:1 requirement above is what forced the D014 selection, and the INN3990CQ that won it covers 220–370 V with a great deal of room to spare. The narrower operating window is recorded as margin, not as a licence to re-select a 1.7:1 part: the 48–450 V capability is retained deliberately (§2), and the aux supply is the one block where losing it would be felt first — on a bench supply, on a partially charged pack, or on any future pack decision.

### 11.2 Outputs

| Rail | Voltage | Isolation | Load |
|---|---|---|---|
| Gate drive, high side ×3 | +18 / −5 V (see §5) | Independent, reinforced | Per-channel |
| Gate drive, low side | +18 / −5 V (see §5) | Common (shared source) | 3 channels |
| Control logic | +5 V, +3.3 V | Secondary | MCU, sensing |
| Isolated CAN | +5 V | Independent | Transceiver |
| Contactor / fan | +12 V | Secondary | External loads |

**Candidates — verified against datasheets and DigiKey stock, 2026-07-31:**

| Rank | Part | Why | Caveat |
|---|---|---|---|
| 1 | **PI InnoSwitch3-AQ INN3990CQ** (900 V PowiGaN, integrated) | Only family with a datasheet-guaranteed **30 V DC start** and "30 V to >1200 V DC" input; ~32 W available at 48 V (interpolated from the 30/60 V power-table columns), 100 W at 400 V; AEC-Q100; reinforced isolation per IEC 60747-17; $8.93, ~1.5 k in stock | Max recommended DC rail 650 V (covers our 500 V transient); 48 V power figure is interpolated, not a datasheet point — confirm in design **[TBV]**; primary inductance < 500 µH and Kp ≈ 0.9 at V_min per design guide |
| 2 | INN3999CQ (same family) | ~24 W at 48 V, $7.79, ~1.9 k in stock | Less power headroom at minimum line |
| 3 | Discrete: TI UCC28C42 (or UCC28700) + 1200 V SiC FET (Wolfspeed C3M0350120J $6.39 / Infineon IMW120R350M1H $6.36, both stocked) | Fully flexible, automotive -Q1 variants exist, 94–96 % max duty handles 9.4:1 | Needs HV startup current source (a 48 V-sized startup resistor burns ~90× more at 450 V), aux bias winding clamped across the line swing, opto + TL431 |

**Ruled out with reasons:** InnoSwitch3-EP (datasheet minimum DC input 90 V; UV/OV pin ratio 4.4:1 cannot span 9.4:1), LinkSwitch-XT2 (11 W ceiling), InnoSwitch4 (750 V max, no 900 V part exists), ST VIPerPlus (800 V max), onsemi NCP107x (700 V), MPS HFC0500 (hard brown-in at ≥ 95 V — never starts at 48 V). The 1700 V SiC InnoSwitch3-AQ (INN3949CQ, $15.11, stocked) is a valid oversized fallback if the 650 V rail recommendation of the 900 V parts becomes a concern.

### 11.2b Secondary architecture (D020 — parts verified 2026-07-31)

```
HV bus 48–450 V ──INN3990CQ flyback (RCD clamp, Schottky rectifier,
                  FB divider @1.265 V ref, Lp<500 µH, DER-948Q pattern)──► 15 V main rail
                                                                              │
12–24 V aux ──LM5175 4-switch buck-boost → 15 V ──ideal-diode OR (LM74610-Q1)─┤
                                                                              │
        15 V ──LMR51430 buck──► 5 V (3 A)                                     │
        15 V ──LMR51430 buck──► 12 V (contactor/fan) [TBV]  ◄─────────────────┘
        5 V ──TLV1117-33──► 3.3 V logic
        5 V ──4× SN6505B + Würth 750316856 (1:4.67 → 23 V, AEC-Q200,
              zener-split at centre tap)──► +18 / −5 V gate rails (3× HS + 1× LS)
        5 V ──Murata NXE2S0505MC (2 W, 3 kV)──► isolated CAN 5 V
```

Key verified constraints: SN6505B accepts **5 V only** (2.25–5.5 V) — gate supplies run from the 5 V rail, which therefore carries ~8 W of gate-drive load (LMR51430's 3 A covers it, noted); a plain boost for the aux input is **invalid** (cannot regulate with 24 V in > 15 V out) — hence the buck-boost; the gate-supply transformer's 2.5 kV AC test rating is functional isolation, with the reinforced barrier in the driver ICs per §5. All parts stocked at DigiKey at check; the 12 V rail buck is the one unverified block **[TBV]**.

### 11.3 Auxiliary input

A **12–24 V external auxiliary input [SEL]** is required in addition to the HV-derived supply. Control electronics must be able to power up before the DC bus is live, to sequence precharge and to permit safe bench work and diagnostics on a de-energised bus. Implementation per §11.2b: LM5175 buck-boost into the 15 V rail through an ideal-diode OR.

### 11.4 Thermal

| Case | Efficiency | Loss @ 15 kW cont | Loss @ 35 kW, 120 s peak |
|---|---|---|---|
| Si IGBT (not selected, reference) | ~96.5 % | ~525 W | ~1225 W |
| **SiC MOSFET (selected, D016)** | ~98 % | **~300 W** | **~700 W** |

**Design point (SiC): 300 W continuous, 700 W for 120 s** — and per §2 the 120 s figure sizes the cold plate.

**The 120 s peak (§2) is quasi-steady-state for the cooling system**, so the cold plate, pump and coolant loop must be sized to hold junction temperature at the *peak-condition* losses — 700 W (SiC) to 1225 W (Si) — with the junction-temperature margin below, not merely at the continuous figures. This roughly doubles the cooling requirement relative to a short-transient peak and is a significant cost/mass factor in the Si vs SiC comparison (§14 item 2).

**Liquid cooling is required in all cases.** A cold plate is the baseline. Forced air is viable only at a substantially reduced continuous rating, which would need to be characterised and stated. The previous draft's claim that forced air suffices rested on a fabricated 5 mΩ figure for a 1200 V device; real 1200 V devices are 25–80 mΩ, an order of magnitude higher.

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
| 1 | ~~Target motor~~ **Resolved: EMRAX 188 HV (§2.2).** Remaining: confirm winding variant and cooling configuration at motor order; duty cycle still unstated | §3.3 finalisation |
| 2 | ~~Si vs SiC~~ **Resolved: SiC (D016).** Remaining: final module part commitment (FS02MR12A8MA2B baseline) and gate driver selection | Gate drive, cold plate concept |
| 3 | Derating curve for 250–450 V operation | Safe operating area at high bus |
| 4 | Compliance target (industrial / automotive / none) | §10 creepage, certification |
| 5 | ~~DC-link capacitance vs f_sw~~ **Resolved conditionally (§6.1):** 400 µF @ ≥ 25 kHz (SiC) or ≥ 750 µF @ 12 kHz (Si). Remaining: 114 A / 120 s ripple duty vs manufacturer thermal model | Capacitor part selection |
| 6 | Cooling: cold plate design and coolant availability | §11.4 |
| 7 | ~~Aux supply controller~~ **Resolved at candidate level (§11.2):** InnoSwitch3-AQ INN3990CQ, verified 30 V start and stock. Remaining: transformer design and 48 V full-load confirmation | §11.1 |
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
