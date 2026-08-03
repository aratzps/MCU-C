# MCU-C Integrated SiC Inverter — Engineering Report

**Status: post-review revision, schematic complete.** Control-board routing and its fabrication package are the remaining work; §21 states this plainly. Sections 1–16 describe the design; **§17 records what three adversarial reviews changed** and §18 the validation gates. Where an earlier figure was corrected by review, this document carries the corrected one and §17 shows the original alongside it.
Companion documents: `SPEC.md` (requirements), `docs/DECISIONS.md` (D001–D026), `docs/REVIEW_FINDINGS.md` (review record), `docs/SI_VS_SIC.md` (technology trade), `docs/BOM.md` (sourcing), `docs/PINOUT.md`, `docs/CHANGELOG.md`.

Every number in this report is either derived here or verified against a manufacturer datasheet / live distributor listing on the date noted in the corresponding decision record. No part entered the design unverified.

---

## 1. System definition

A fully integrated 3-phase inverter: 48–450 V DC bus, 15 kW continuous / 35 kW peak at the 250 V nominal point, VESC-compatible (STM32F405VGT6, mainline `bldc` firmware target). Target motor: EMRAX 188, HV winding (D011). The board enforces **current** limits; power scales with bus voltage (D005).

## 2. Current sizing — from the motor, not from guesswork

Phase current at the rated point (full modulation, SVPWM, η = 0.97, cos φ = 0.95):

```
V_ll = V_dc/√2 = 176.8 V rms at 250 V bus
I_ph,cont = 15 000×0.97/(√3×176.8×0.95) =  50.0 A rms
I_ph,peak = 35 000×0.97/(√3×176.8×0.95) = 116.7 A rms
```

These are *high-speed* values. At low speed the same torque needs the same current at low voltage, so the stage is sized to the motor's own ratings (EMRAX 188 HV, datasheet v1.6):

| Quantity | Value | Origin |
|---|---|---|
| Continuous phase current | 100 A rms | motor continuous rating |
| Peak phase current, 120 s | 190 A rms | motor S2 rating; t_peak matched to it (D012) |
| Instantaneous peak | 270 A | 190×√2 |
| Sense full scale | ±325 A | 270 + 20 % |
| Hardware trip | 300 A | between legitimate 270 A and sense saturation |

Cross-checks: full peak torque 100 Nm needs 100/0.54 = 185 A rms < 190 A ✓; motor envelope at 250 V bus: Kv_load × 250 V ≈ 3 400 rpm × 100 Nm ≈ 35.6 kW ≈ the 35 kW rating point (the HV winding lands on our spec almost exactly — D011).

DC-side: I_dc = P/V_nom → 60 A cont / 140 A peak. Worst-case DC-link RMS ripple ≈ 0.6×I_ph → **60 A cont / 114 A for 120 s**.

## 3. Technology: SiC, and what it cost

1200 V class is forced by the 450 V bus plus overshoot/regeneration margin (650 V excluded outright; 750–900 V leaves no first-design margin). Six-pack module for one thermal interface, vendor-controlled stray inductance, and no paralleling problem (D004).

Si vs SiC was decided on measured market data, not folklore (full analysis `SI_VS_SIC.md`): at our current class the stocked premium is ≈ $635 (FS200R12KT4R $132 vs FS02MR12A8MA2B $767), battery compensation for Si's efficiency deficit is +1.59 % pack capacity (= 1/0.965 − 1/0.98), and after DC-link/cooling offsets the net SiC premium is ≈ $280 at 20 kWh — shrinking to $70–200/unit at 10 k/yr. SiC selected (D016) for inaudible 25 kHz switching, half the peak-condition heat, mass, and 450 V headroom. GaN was evaluated and ruled out on shipping-product evidence (D015): no ≥900 V device above 34 A ever shipped (now obsolete), no avalanche rating in lateral GaN, no benefit at 25 kHz.

**Module: Infineon FS02MR12A8MA2B** (HybridPACK Drive G2, CoolSiC, 1.9 mΩ @ 18 V, 390 A class). Key verified facts that shaped the design: R_DS,on 1.90 mΩ @ V_GS 18 V vs 2.40 mΩ @ 15 V (+26 % conduction loss → gate levels +18/−5 V, D017); Q_G 1.19 µC; dv/dt ≈ 14 V/ns; per-phase temp-sense **diodes** (not NTCs); PressFIT signal pins requiring the AN-G2-ASSEMBLY board pattern; screw power terminals (→ busbar architecture, D021).

## 4. The 120 s peak and its thermal consequence (D012)

t_peak was matched to the motor's S2 2 min rating by owner directive. Because module baseplate, cold plate and coolant loop have thermal time constants of tens of seconds, **a 120 s peak is thermally steady-state for the cooling system**. Loss estimates:

**These figures were corrected by review — see §17.2 for the derivation.** Computed from the module's own loss tables at V_GS = +15 V (D026), not from a technology-class efficiency estimate:

| Point | Dissipation | Note |
|---|---|---|
| 15 kW continuous | **~420 W** | η ≈ 97.3 % |
| 35 kW, 120 s @ 250 V | **~1144 W** | η = 96.8 % |
| 35 kW, 120 s @ 450 V | **~1541 W** | switching scales with bus voltage |

**The module is not the constraint — the loop is.** The G2 is direct-cooled at R_th,j-f = 0.121 K/W max per switch, so at 191 W per switch the junction sits ≈ 88 °C with 65 °C coolant against a 150 °C limit: a 3–4× margin. What must be sized for ~1.15–1.55 kW is the external heat exchanger, pump and coolant loop. There is no separate cold plate to design — the requirement is a coolant jacket per AN-G2-ASSEMBLY at ≥10 dm³/min, ≤65 °C.

## 5. DC link (D013)

Voltage-ripple bound for a two-level VSI, ΔV_pp ≤ 1.5 % of 250 V = 3.75 V:

```
C ≥ I_ph,pk/(8·f_sw·ΔV_pp) = 270/(8 × 25 000 × 3.75) = 360 µF → 400 µF selected
```

f_sw = 25 kHz baseline (SiC; inaudible; VESC-typical). The binding constraint is ripple **current**, not capacitance: 114 A rms for the full 120 s.

**Bank as built: 5 × Vishay MKP1848C71010JY5, 100 µF / 1000 V ⇒ 500 µF, ≥125 A rms.** The 120 s duty was verified against Vishay's own thermal model rather than inferred from short-pulse ratings: ΔT = P/G with G = 152 mW/°C gives **14.7 K rise per capacitor** at 22.8 A each, and the block's own thermal time constant is **~43 minutes**, so a 120 s pulse reaches under 5 % of steady state and adds ~0.7 K. The steady-state case therefore bounds the pulse case — which is what **closed SPEC open item 5**. Valid for a capacitor ambient ≤ 80 °C, which is why §11.5's ambient requirement exists.

Note the bank is 500 µF, not the 400 µF the ripple-voltage bound required. That gap is where a family of stale derivations hid — see §17.2.

## 6. Protection chain — firmware-independent by construction

Ported from PALTA and netlist-verified (D018), with one honesty correction: the original never inserted hardware dead time — it only eliminates overlap. The protection stack is:

1. **TIM1 silicon dead-time generator** — configured by firmware, enforced by hardware.
2. **Overlap eliminator** (supervisor sheet): NAND detects HS∧LS high per phase; AND gates force both low. Boot pulldowns on all six PWM lines.
3. **Turn-on RC delay per driver input** (~250 ns target, gate_drive sheet): even simultaneous edges get a hardware gap; diode bypass keeps turn-off fast.
4. **300 A ±8 A hardware trip** (current_sense sheet): per-phase window comparators, open-drain wire-OR → supervisor latch (D-flip-flop, explicit reset) → **TIM1_BKIN (PB12)** — silicon tri-states the PWM without firmware.
   Two review findings landed here. The comparator was wrong twice over (TLV7032 is push-pull, so six of them wire-ORed was direct contention; LM2903's input common-mode range stops at 1.8 V, *below* the 2.34 V upper threshold, so the over-current half could never trip) — now **TLV7022**, true open-drain, rail-to-rail, 260 ns. And the thresholds rode the ±4 % 3.3 V rail while the transducer's reference is absolute, making the real trip **245–356 A**; each phase's window is now servo'd off *its own* transducer reference through an OPA376 buffer, giving **300 A ±8 A**.
   **The trip did not reach TIM1_BKIN at all until review** — it terminated at a supervisor gate and a status GPIO, so this specification's central safety claim was false as built. A wire-OR diode now carries it (0.31 V against a 0.95 V threshold), and it reverse-biases on driver-only faults so the two fault paths stay independent.
5. **Transducer OCD backup** (~584 A) on the same wired-OR line.
6. **Per-switch DESAT** in the 1ED3491 drivers (blanking set by ADJB, current-source soft-off by ADJA) with FLT_N wired-AND into the same supervisor fault conditioning.
7. Bus OVP 490 V / UVP 45 V, module overtemp 150 °C ⏳ (bus_sense/temp_sense capture pending).

## 7. Gate drive (D017)

1ED3491MC12M ×6: reinforced per IEC 60747-17 (VIORM 1767 V pk), CMTI 200 V/ns against the module's ~14 V/ns, ±9–11 A vs the ~2 A the datasheet-condition R_G (12 Ω/3.3 Ω) actually draws, Miller-clamp pre-driver → BSS138-class FET returned to VEE2 (datasheet §4.5.4.1 — the gate rests at −5 V), DESAT via 1 kΩ + 2×US1M (2 kV standoff) into the module's drain-sense pins. RDYC is a dual-function bused ready/fault-clear line — coupled to the supervisor's push-pull reset through 1 kΩ (contention ≤3.3 mA, low-pulse 0.58 V < V_IL 0.99 V).

**Gate levels are +15 V / −5 V (D026), not the +18 V originally selected** — the derate is what makes the module's 2 µs short-circuit withstand reachable; see §17.3.

**The rails are post-regulated, which they were not originally.** An open-loop secondary peak-charges to ~24.9 V at light load, putting V_GS(on) at 20.3 V against the module's **+19 V absolute maximum** — a continuous overstress on every switch. Each of the four isolated domains now carries a 15 V reference plus an emitter follower: **V_GS(on) 14.2–16.2 V over 0–70 °C, 2.8 V under the limit**. The off-rail needed two fixes: a ±2 % 4.7 V zener (the original ±5 % 5.1 V part exceeded the −5 V static maximum), and a preload, because gate charge nets to zero at COM so the zener otherwise sat in its knee with the off-voltage undefined. It now sits at **4.84 V**. Residual, recorded: the zener tempco reaches 5.06 V at −40 °C and §11.5 sets no cold minimum, so −40 °C operation would need a 4.3 V part.

Isolated supplies (D020): four SN6505B push-pull stages **from the 5 V rail** (the part is 2.25–5.5 V only — verified, a 15 V feed would have been a silent design error) through Würth 750316856 (1:4.67) with a zener split. The reinforced barrier lives in the driver ICs; these transformers carry only supplementary/functional insulation at 600 V rms working (their 2.5 kV AC is a hipot test rating, not a reinforced working-voltage certification) — an open risk against SPEC §10 pending the compliance target, carried in §18.

## 8. Precharge / discharge (§7, captured)

Precharge energy is independent of resistance: E = ½CV² = ½ × **500 µF** × 450² = **50.6 J** (62.5 J from a 500 V rail; the 400 µF-based 40.5 J in the original draft was a stale derivation — §17.2). R = 1.25 kΩ → τ = 0.625 s, **~3.13 s** to >99 % (firmware timeout ≥3.2 s), 0.36 A peak — relay closes into a dead bus and opens at near-zero current. Sequencing rule (on-sheet, verbatim): precharge → verify V_bus ≥ 95 % via bus sense → main contactor → open precharge; neither contactor closes without a valid bus reading.

Passive bleeder: **56 kΩ** as a 4-resistor series string of 14 kΩ (no single part spans 450 V): τ = 28 s → **56.4 s** to 60 V, 3.6 W continuous. *The original 75 kΩ failed the <60 s requirement at 75.4 s against the real 500 µF bank — §17.2.* Active discharge: 880 Ω (4× 220 Ω series) + C3M0350120J, opto-driven: ~0.51 A initial, <5 s to 60 V, ~230 W single-shot pulse — chassis-mounted resistors (D021).

## 9. Sensing

- **Phase current (D019):** 3× LEM HOYS 200-S/SP33 — the shunt route died on physics (0.75 mΩ → 27 W at peak) and on silicon (F405 has no DFSDM; ΔΣ readout impossible without eating the CPU; analog AMC1302 unstocked). HOYS: ±500 A, 2.3 mV/A about 1.65 V on 3.3 V, reinforced IEC 61800-5-1, 180 kHz/3 µs — requirements re-derived for 25 kHz switching (≥150 kHz, <5 µs).
- **Bus voltage:** series divider string (≥4 resistors, no part spans 450 V) into an isolated amplifier ⏳ (AMC1311B verification pending), scaled 500 V → near-full ADC range.
- **Temperature:** module TS diodes ⏳ (readout domain under verification — likely HV-referenced; architecture decision pending research); coldplate + board NTCs; motor KTY 81/210 input (EMRAX standard) with a front end that accommodates PT1000/NTC by resistor choice.
- **Position (D003):** all four interfaces — Halls, ABI, resolver via AD2S1205 (its A/B/NM emulation makes VESC support free — no firmware work), SinCos ⏳ (capture in progress, ported from PALTA).

## 10. Auxiliary power (D014, D020)

The 9.4:1 input range (48–450 V) is the hard requirement; InnoSwitch3-AQ INN3990CQ is the only verified family with a datasheet-guaranteed 30 V DC start (competitors fail on: 90 V min line, 4.4:1 UV/OV pin ratio, 11 W ceilings, 700–800 V switches, 95 V brown-in). Captured per the DER-948Q 15 V pattern with computed FB divider 143k/13.2k → 14.97 V. Aux input 12–24 V via LM5175 4-switch buck-boost (a plain boost cannot regulate 24 V→15 V — verified trap) set to 15.02 V so the external supply deliberately wins the diode-OR when present. Rails: 5 V (LMR51430, carries the ~8 W gate-supply load), 12 V (relay/contactor coils), 3.3 V (TLV1117 — the rail's PWR_FLAG source), isolated CAN 5 V (Murata NXE2S0505MC, 3 kV).

## 11. Isolation architecture (§10)

Working voltage 450 V DC, IEC 60664-1 basis (PD2, OVC II, material IIIa) ⏳ final compliance target open. Reinforced barriers (≥3 kV rms): gate drivers (1ED3491 VIORM 1767 Vpk ✓), current sense (HOYS IEC 61800-5-1 ✓), bus sense ⏳, CAN (ISO105x/NXE2S ✓), aux transformer ≥4 kV [TBV at transformer build]. USB is user-accessible → reinforced, no exceptions. HV/LV net separation is asserted mechanically in every netlist check (no HV net shares a pin with GND/+3.3 V/+12 V — verified at every sheet commit).

## 12. Verification record

Every schematic sheet gated on: kicad-cli ERC **0 errors** on the full hierarchy, per-block netlist machine-assertions (supervisor 24/24 against the legacy PALTA netlist; power_stage 49 pins/29 nets; gate_drive 244/244; precharge 40/40 incl. HV/LV separation; current_sense 69/69 incl. 11-node OC_TRIP membership; aux_power full block set incl. all 12 VGD rails spanning source→load), and independent re-verification by a second netlist export before each commit. PDF export of the hierarchy succeeds at every step.

## 13. MCU pin assignment

Complete table with per-pin citations in `docs/PINOUT.md`, generated against the post-wiring netlist. Highlights: the three phase-current ADC inputs sit on **PC0/PC1/PC2 = ADC123_IN10/11/12**, the exact channels VESC's `hw_100_250` converts at rank 1 of ADC1/ADC2/ADC3 in triple-regular-simultaneous mode — so the custom `hw_mcuc.h` can copy that ADC vector nearly verbatim. Encoder on TIM3 (PC6/7/8), PPM on PB6 (TIM4_CH1, VESC convention), resolver on SPI3 with PA15 as chip select (its reset-state pull-up holds CS deasserted through boot; costs full JTAG, which this board never uses). PA4/PA5 are the only non-5 V-tolerant pins used and carry analog only.

**D023 — no phase-voltage sensing:** VESC's SENS1/2/3 assume a controller floating at battery potential with direct phase dividers. This control domain is isolated, so those dividers are impossible; isolated phase sensing would cost three more AMC1311 channels plus per-phase HV supplies for features (phase filters, BEMF startup assist) that FOC with three current sensors and four position interfaces does not need. PA0/PA1/PA2 stay reserved.

## 14. Physical realisation

**Two boards plus a busbar assembly (D021, D024).** Power current never flows through the control PCB:

| Item | Form |
|---|---|
| Control/driver board | 200 × 132 mm, 4-layer (F.Cu / GND / power islands / B.Cu), 1.6 mm ±0.16 (PressFIT requirement), mounted on the module via its PressFIT signal pins and the AN-G2-ASSEMBLY screw/heat-stake pattern |
| DC-link carrier | 320 × 100 mm, 2-layer 2 oz, solid DC+ front / DC− back zones, SOLID pad connections (no thermal reliefs), M6 lugs to module and busbar. **Complete: ERC 0/0, DRC 0 violations** |
| Laminated busbar | Mechanical part (drawing, not gerbers): battery → carrier → module screw terminals; phase bars pass through the HOYS transducer apertures to M6 studs |
| Chassis-mounted | Precharge resistor (50 W), discharge bank (4 × 25 W), coldplate NTC — all connectorised |

**Isolation is enforced, not documented.** `mcuc_inverter.kicad_dru` carries a custom `HV_to_LV` rule at 6.4 mm (SPEC §10 basic insulation at 450 V working) with narrow relax rules for intra-string segments that legitimately sit at ~124 V, plus 14 copper keepout areas under every isolator body. The rule was proven live: a probe track planted 4.68 mm from an HV pin produced exactly one violation and its removal returned the board to zero. Placement passes DRC with **0 clearance and 0 courtyard violations**.

Known geometry exceptions, recorded rather than hidden: the VOM1271's SOP-4 package creepage (~5 mm) is below the 6.4 mm board target — a package limit, flagged for the review pass; and the precharge relay's coil-to-contact spacing rides the relay's own certified barrier.

## 15. Bill of materials

`docs/BOM.md` carries every part with its verified supplier, price at qty 1/100 and stock caveats; `docs/BOM_*.csv` are the refdes-level exports (165 line items / 474 parts on the control board, 13 of them deliberately off-board; 11 items on the carrier). Rough qty-1 cost ≈ **$1.4 k**, of which the SiC module is 55 % — consistent with the §3 economics.

The sourcing sweeps caught several parts that would have failed at purchase or fabrication: a fictitious "REDCUBE THR M6" terminal (M6 exists only in the press-fit family), a Würth inductor P/N that returns 404, an obsolete AO3400 (the A suffix is the live part), the EOL'd KTY 81/210, an NFND board NTC, unstocked Nexperia small-signal parts, an SS310 package mismatch, and a Vishay capacitor P/N whose "C61010" code decodes to 10 µF rather than the intended 100 µF. **Order-early list** (long leads behind current stock): the module (39 wk), AD2S1205 (20 wk), HOYS transducers (5 pcs at check), the STM32 (dry at DigiKey/Mouser; Newark holds it), and the Hongfa relay (non-DigiKey channel).

---

## 17. What the adversarial review changed

Three independent reviewers attacked the design with instructions to verify every claim against manufacturer datasheets rather than trust this repository, and to report nothing they could not defend with arithmetic. Full findings and dispositions: `docs/REVIEW_FINDINGS.md`. The verdict of the third review was **"not fabrication-ready"**, and it was right. This section records what that cost and what it bought, because a design report that shows only the final state hides the most useful information in the project.

### 17.1 Defects that ERC, DRC and inspection could never have caught

Every one of these passed electrical-rules checking, passed design-rules checking, and looks correct on the page:

| Defect | Why it survived every automated check |
|---|---|
| **The gate-driver fault latch could never be cleared.** RDYC only rises when FLT_N is already high; FLT_N only clears on a rising RDYC edge; the MCU reset was ANDed in so it could only add another *low* | A closed logical loop across two ICs, legal at every net. Consequence: the bridge very likely never enables, even once |
| **The hardware overcurrent trip never reached TIM1_BKIN** — it terminated at a supervisor gate and a status GPIO | Every net was connected and driven. SPEC §9.2's central safety claim was simply false as built |
| **The comparators could not see the upper trip threshold.** LM2903's input common-mode range on 3.3 V ends at 1.8 V; the threshold is 2.34 V | A part-parameter fact, invisible to connectivity checking. The overcurrent protection would silently not function |
| **DESAT took ~5.8 µs against a 1.2 µs short-circuit withstand** | Timing emerges from four datasheet parameters across two devices; no tool sums them |
| **HV-rated capacitors on 0603 footprints, two of them in series across the 450 V link** | Footprint assignment is not rule-checked against part ratings. A stock 0603 fitted at build fails short, the second sees 500 V, and the result is a dead short across a 500 µF bank |
| **The flyback transformer saturated at the controller's current limit** (B_pk 425 mT typ against 3C96's 440 mT) — because it was copied from a reference design using a *lower*-current-limit controller | Requires cross-reading two datasheets and a reference-design report |
| **The 5 V converter could not dissipate its own loss** (1.33 W in a 107.8 °C/W SOT-23-6 → ΔT_J ≈ 143 K) | Thermal capability appears nowhere in the netlist |
| **Three motor phase outputs were dangling** — no terminal existed anywhere in either project | Reported only as benign "dangling label" warnings among 200 others |

The through-line: **automated checks verify that a design is internally consistent, not that it works.** Every defect above lived in the gap between "the netlist is correct" and "the physics is correct."

### 17.2 Arithmetic that was simply wrong

**Stale derivations.** The DC-link bank was selected as 5 × 100 µF = 500 µF, but the specification still carried numbers derived from an earlier 400 µF assumption, and nothing recomputed them:

```
Precharge energy    ½ × 400 µF × 450² = 40.5 J  →  ½ × 500 µF × 450² = 50.6 J  (62.5 J from a 500 V rail)
Precharge duration  5τ = 2.5 s                   →  5τ = 3.13 s
Bleeder             74.8 kΩ × 400 µF → 60.3 s    →  74.8 kΩ × 500 µF → 75.4 s
```

That last line is the important one: **the passive bleeder failed its own <60 s safety requirement by 26 %**, and had been marginal (60.3 s) even against the assumption it was designed to. Fixed at 4 × 14 kΩ = 56 kΩ → 56.4 s.

**An efficiency estimate used as a design input.** The thermal design point came from a technology-class figure (~98 % for SiC) rather than the module's own loss data. Computed properly at 190 A rms, 25 kHz:

```
Conduction (+15 V):    3 × 190² × (4.67 mΩ @150 °C + 0.64 mΩ)          =  575 W
Switching @250 V:      3 × 25 kHz × 115.4 µJ/A × (250/750) × (2×270/π)  =  496 W
Dead-time body diode:  3 × 171.9 A × 4.04 V × 0.035                     =   73 W
                                                                          ────────
                                                                          1144 W    (η = 96.8 %)
```

against a documented 700 W — **63 % low**. The module absorbs it (junction ≈ 88 °C at 65 °C coolant against a 150 °C limit, a 3–4× margin), so the error lands entirely on the **coolant loop and heat exchanger**, which must reject ~1.15 kW at 250 V and ~1.55 kW at 450 V. A cooling system built to the original figure would have been roughly half the size required.

### 17.3 The trade that had to be made

The DESAT finding forced a genuine engineering decision rather than a value change (D026). The module's short-circuit withstand is **t_SC < 1.2 µs at V_GS = +18 V but < 2 µs at +15 V**, and the driver chain, optimally configured, reaches ~2.0 µs:

- At +18 V the requirement was **unreachable** — the die fails roughly five times over before the gate moves.
- At +15 V it becomes **attainable**, at the cost of R_DS,on rising 1.90 → 2.40 mΩ (+26 % conduction loss, +105 W at peak) — paid out of junction margin, not out of the cooling budget's critical path.
- Reopening the driver selection (D017) was considered and rejected: the dominant delays are the *configurable* blanking filter (1575 ns) and soft-off current, not the 9.18 V threshold, so a six-channel respin buys little.

**The residual risk is stated rather than buried: ~2.0 µs sits at the 2 µs rating with no margin.** A double-pulse short-circuit validation is therefore a gate on production release, and if it fails the fallback is a driver change, not a value tweak.

### 17.4 What the reviews confirmed

Coverage matters as much as findings, so reviewers were required to list what they checked and found correct. Among it: end-to-end PWM polarity from TIM1 through the interlock and RC network to the module gate; the overlap eliminator genuinely forcing both outputs low; dead-time diode orientation on all six channels; TIM1_BKIN polarity matching the STM32 reset default; every one of the 100 MCU pins against ST's tables (one reviewer found *the review brief's own* assumed pin list wrong while the schematic was right); every ADC channel assignment; the Miller-clamp return to VEE2 being correct where returning it to GND2 would have caused shoot-through; the DC-link bank's 114 A / 120 s ripple duty — which **closed SPEC open item 5** with 14.7 K of rise per capacitor against a ~43 min thermal time constant, so the 120 s pulse adds ~0.7 K; the precharge sequence being fully permitted by the hardware; and both coil drivers being boot-safe.

## 18. Validation plan and open risks

**Gates on production release** — each must pass before the design is considered qualified:

| # | Validation | Why |
|---|---|---|
| 1 | **Double-pulse short-circuit test** at +15 V gate | D026's residual risk — the DESAT chain sits at the 2 µs limit with no margin |
| 2 | **Transformer leakage-inductance measurement** on the first wound T601 sample | The RCD clamp assumes ~1.9 µH; at 4 µH the primary switch drain reaches 946 V, past its absolute maximum |
| 3 | **Internal enclosure ambient measurement** | §11.5 sets ≤70 °C by requirement, not by measurement; regulator junction temperatures, resistor derating and cap-bank margin all depend on it |
| 4 | **Gate-rail worst-case verification** on hardware | The rails are open-loop and the module's V_GS absolute maxima are +19 V / −5 V static |
| 5 | **48 V full-load flyback test** | The InnoSwitch reference warns regulation can fail below 80 V at high load; §11.1 requires 48 V |
| 6 | **Overcurrent trip end-to-end** — inject a fault, confirm PWM tri-states in silicon with the MCU held in reset | Verifies the trip-to-BKIN fix at the level the specification claims |
| 7 | **Precharge/discharge sequence** including the new hardware interlock | Confirms discharge cannot be commanded into a live bus |

**Open risks carried into rev A**, documented rather than silently accepted:

- **Compliance target undefined** (§14 item 4). The gate-drive supply transformers carry only supplementary/functional insulation at 600 V rms working, so the reinforced barrier rests entirely on the driver ICs. Defensible under a functional-safety argument, not under a strict reinforced-insulation requirement.
- **Aux input has no load-dump protection.** The fitted TVS handles fast transients but not an ISO 7637-2 5a/5b load dump (tens of joules against ~1 J of capability). Only binding if an automotive target is adopted.
- **Module TS diodes unread** (D022) — thermal protection derives from a coldplate NTC with DESAT as the fast backstop; junction excursions during the 120 s peak rely on the margin computed in §4.
- **Bus-voltage accuracy** is limited by the 3.3 V reference, not the divider — ±1 % needs a REF3033 or per-board firmware calibration.
- **AD2S1205 is a 20-week lead part** with zero distributor stock at last check; the stocked AD2S1210 alternative is a package and interface redesign.

---

## 19. Decision index — every engineering choice, with its reason

The full record is `docs/DECISIONS.md`; this is the index, so the report can be read alone.

| # | Decision | The reason it went this way |
|---|---|---|
| D001 | Fully integrated inverter, not a control board | Owner's choice, made with the trade-off explicit: DC-link, precharge, creepage and thermal become this design's problems rather than a power-stage vendor's |
| D002 | STM32F405VGT6, LQFP100 | Same die as the VESC reference so mainline firmware applies; 100 pins fit all four position interfaces plus CAN, USB and the supervisor. No CAN FD exists on any F405 — a hard constraint, not a preference |
| D003 | All four position interfaces | Owner requirement. The AD2S1205's encoder emulation makes VESC resolver support free, so it costs pins rather than firmware |
| D004 | 1200 V six-pack module | 450 V bus plus overshoot and regeneration rules out 650 V. A module gives one thermal interface and removes current-sharing entirely |
| D005 | Current limits fixed, power scales with bus | Physically correct: the hardware limits are thermal and current. 15/35 kW are defined at 250 V only |
| D006→D011 | Phase current sized from the motor, not a guess | The 1.5× placeholder was replaced once the EMRAX 188 was fixed: 100 A rms continuous, 190 A peak. The HV winding's envelope at 250 V lands on the 35 kW rating point almost exactly |
| D012 | Peak duration 120 s, matched to the motor's S2 rating | Owner directive. Consequence: 120 s is *thermally steady-state* for the cooling loop, so cooling is sized for peak losses, not continuous |
| D013 | DC-link 500 µF, ripple-current limited | Voltage ripple needs 360 µF at 25 kHz; ripple *current* (114 A rms for 120 s) sets the real bank |
| D014 | InnoSwitch3-AQ aux flyback | The only family with a datasheet-guaranteed 30 V start across the 9.4:1 input range. Every alternative failed on a hard number |
| D015 | GaN ruled out | No ≥900 V GaN above 34 A ever shipped and that line is obsolete; lateral GaN has no avalanche capability; and a 25 kHz drive gains nothing from GaN's speed while its dv/dt harms motor insulation |
| D016 | SiC power stage | ~$635 module premium, ~$280 net after battery/DC-link/cooling offsets, falling to $70–200/unit at 10 k/yr. Buys inaudible switching, half the peak heat, mass and 450 V headroom |
| D017 | 1ED3491 gate drivers | Reinforced, 200 V/ns against the module's 14 V/ns, adjustable DESAT and soft-off, stocked. Infineon's own automotive pairing has zero distribution stock |
| D018 | Dead time from TIM1 + RC delay, not from the PALTA logic | The ported circuit *only* eliminates overlap — it never inserted dead time, despite the record claiming so |
| D019 | LEM HOYS transducers, not shunts | A 0.75 mΩ shunt dissipates 27 W at peak; the low-loss ΔΣ alternative is blocked because the F405 has no DFSDM peripheral to decode the bitstream |
| D020 | Aux rail tree | Verified two traps: the push-pull driver is 5 V-only, and a plain boost cannot regulate a 24 V input down to 15 V |
| D021 | One PressFIT board on the module; power on busbars | The module's terminals are screw lugs. Putting 190 A on PCB copper is absurd; Infineon's own architecture separates power from signal |
| D022 | TS diodes provision-only; PT1000-selectable motor sense; AMC1311 bus sense | The module's TS pins carry no isolation rating and the only documented readout is inside a zero-stock driver. KTY 81/210 is obsolete |
| D023 | No phase-voltage sensing | Stock VESC boards float at battery potential; this control domain is isolated, so those dividers are impossible and isolated equivalents aren't justified |
| D024 | Two boards: control + DC-link carrier | The film caps are PCB-pin parts but their 114 A rms cannot ride control-board copper |
| D025 | Post-review spec corrections | Thermal design point was 63 % low; every 400 µF-era derivation was stale, leaving the bleeder failing its own safety requirement |
| D026 | Gate drive derated to +15 V | At +18 V the module's short-circuit withstand is 1.2 µs and the driver chain cannot meet it. At +15 V the withstand is 2 µs and the chain reaches 1.9 µs typical — attainable, not comfortable |

## 20. Summary of derived quantities

Every figure below is derived in the section named, from a [REQ] input or a datasheet value.

| Quantity | Value | Where |
|---|---|---|
| Phase current, continuous / peak | 100 / 190 A rms | §2 — motor ratings |
| Instantaneous phase peak | 270 A | §2 — 190 × √2 |
| DC bus current, continuous / peak | 60 / 140 A | §2 — P/V_nom |
| DC-link ripple current | 60 A rms / 114 A rms for 120 s | §2 — 0.6 × I_ph |
| DC-link capacitance, voltage bound | ≥360 µF at 25 kHz | §5 — I_pk/(8·f·ΔV) |
| DC-link bank as built | 500 µF, ≥125 A rms | §5 |
| Capacitor rise at peak duty | 14.7 K, τ ≈ 43 min | §5 |
| Module losses, continuous | ~420 W (η 97.3 %) | §4 |
| Module losses, 120 s peak @250 V | ~1144 W (η 96.8 %) | §4 |
| Module losses, 120 s peak @450 V | ~1541 W | §4 |
| Junction temperature at peak | ≈88 °C at 65 °C coolant | §4 — 0.121 K/W × 191 W |
| Heat-exchanger requirement | 1.15–1.55 kW | §4 |
| Precharge energy | 50.6 J (62.5 J from 500 V) | §8 — ½CV² |
| Precharge time constant / duration | 0.60 s / 3.0 s | §8 |
| Passive bleeder time to 60 V | 56.4 s (requirement <60 s) | §8 |
| Active discharge time to 60 V | 0.89 s (requirement <5 s) | §8 |
| Overcurrent trip | 300 A ±8 A | §6 |
| DESAT detect-to-gate-off | 1.9 µs typ / 2.6 µs worst | §17.3 |
| Gate drive V_GS(on) worst case | 14.2–16.2 V (AMR +19 V) | §7 |
| Gate drive V_GS(off) worst case | 4.84 V (AMR −5 V static) | §7 |
| Bus sense scaling | 500 V → 2.988 V, 0.135 V/LSB | §9 |
| Gate-drive power per channel | 0.684 W (Q_G·ΔV·f_sw) | §7 |

## 21. Closing assessment

**What this design is.** A 48–450 V, 15 kW continuous / 35 kW peak SiC inverter matched to an EMRAX 188, VESC-compatible, built as two boards plus a busbar assembly. Eleven schematic sheets, ~460 components on the control board, every part verified against a manufacturer datasheet *and* a live distributor listing before it entered the BOM.

**What is genuinely finished.** Schematic capture and verification (ERC 0 errors, netlist machine-checks on every safety path). Component selection with prices, suppliers and stock caveats. The DC-link carrier board — designed, DRC-clean, and released as a fabrication package. Three independent adversarial reviews and the refinement they forced.

**What is not.** The control board's routing and its fabrication package. The design is at the threshold: netlist current, placement legal, DRC clean, isolation geometry enforced by custom rules — but the tracks are not laid, and until they are there is no gerber set for board 1.

**What would worry me if I were reviewing this cold.** Three things, all recorded rather than buried:

1. **The DESAT margin.** 1.9 µs typical against a 2 µs withstand, 2.6 µs on worst-case silicon. Typical parts pass; worst-case parts do not. The mitigating physics is real (t_SC is specified at 750 V and this bus is ≤450 V) but unquantified. This is why the double-pulse test is a release gate rather than a nice-to-have.
2. **Single-source, long-lead parts on the critical path.** The precharge relay is at zero stock with a 26-week lead; the module 39 weeks; the resolver-to-digital converter 20 weeks with zero stock. The design is buildable but not quickly.
3. **The compliance target is still undefined**, and it changes real things — most concretely whether the gate-supply transformers' supplementary insulation is acceptable with the reinforced barrier resting on the driver ICs.

**What the process demonstrated.** Eight defects passed ERC, DRC and visual inspection, including one that would have prevented the bridge from ever enabling and one that made the central safety claim false as built. They were found by reviewers instructed to verify against datasheets rather than trust the repository — and twice, the implementer's verification overruled an instruction I had given. Automated checks prove a design is internally consistent. They do not prove it works.
