# MCU-C Integrated SiC Inverter — Engineering Report

**Status: DRAFT — sections marked ⏳ await completion of BOM/PCB/review phases.**
Companion documents: `SPEC.md` (requirements), `docs/DECISIONS.md` (D001–D021), `docs/SI_VS_SIC.md` (technology trade), `docs/CHANGELOG.md`.

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

| Point | SiC (~98 %) | Si reference (~96.5 %) |
|---|---|---|
| 15 kW continuous | ~300 W | ~525 W |
| 35 kW, 120 s | **~700 W** | ~1225 W |

The cold plate is therefore sized for **700 W** with ≥25 °C junction margin at ≤65 °C coolant — not for the continuous 300 W. This doubled cooling requirement was priced into the Si/SiC decision.

## 5. DC link (D013)

Voltage-ripple bound for a two-level VSI, ΔV_pp ≤ 1.5 % of 250 V = 3.75 V:

```
C ≥ I_ph,pk/(8·f_sw·ΔV_pp) = 270/(8 × 25 000 × 3.75) = 360 µF → 400 µF selected
```

f_sw = 25 kHz baseline (SiC; inaudible; VESC-typical). The binding constraint is ripple **current**: 114 A rms for the full 120 s — quasi-DC for film-cap hotspot time constants (minutes), so the bank must be rated ≥ 80 A rms @ 70 °C with the 120 s duty verified against the manufacturer model, not hand-waved from short-pulse ratings. Bank: 5 parallel film blocks ⏳ (final P/N from BOM sweep). 800 V DC rating (450 V + transients + margin).

## 6. Protection chain — firmware-independent by construction

Ported from PALTA and netlist-verified (D018), with one honesty correction: the original never inserted hardware dead time — it only eliminates overlap. The protection stack is:

1. **TIM1 silicon dead-time generator** — configured by firmware, enforced by hardware.
2. **Overlap eliminator** (supervisor sheet): NAND detects HS∧LS high per phase; AND gates force both low. Boot pulldowns on all six PWM lines.
3. **Turn-on RC delay per driver input** (~250 ns target, gate_drive sheet): even simultaneous edges get a hardware gap; diode bypass keeps turn-off fast.
4. **300 A hardware trip** (current_sense sheet): per-phase window comparators (thresholds 2.340/0.960 V = ±300 A × 2.3 mV/A about the 1.65 V reference; 9.53k/13.7k/9.53k E96 string, error < 0.05 %), open-drain wire-OR → supervisor latch (D-flip-flop, explicit reset) → **TIM1_BKIN (PB12, netlist-verified)** — silicon tri-states the PWM without firmware.
5. **Transducer OCD backup** (~584 A) on the same wired-OR line.
6. **Per-switch DESAT** in the 1ED3491 drivers (blanking set by ADJB, current-source soft-off by ADJA) with FLT_N wired-AND into the same supervisor fault conditioning.
7. Bus OVP 490 V / UVP 45 V, module overtemp 150 °C ⏳ (bus_sense/temp_sense capture pending).

## 7. Gate drive (D017)

1ED3491MC12M ×6: reinforced per IEC 60747-17 (VIORM 1767 V pk), CMTI 200 V/ns against the module's ~14 V/ns, ±9–11 A vs the ~2 A the datasheet-condition R_G (12 Ω/3.3 Ω) actually draws, Miller-clamp pre-driver → BSS138-class FET returned to VEE2 (datasheet §4.5.4.1 — the gate rests at −5 V), DESAT via 1 kΩ + 2×US1M (2 kV standoff) into the module's drain-sense pins. RDYC is a dual-function bused ready/fault-clear line — coupled to the supervisor's push-pull reset through 1 kΩ (contention ≤3.3 mA, low-pulse 0.58 V < V_IL 0.99 V).

Isolated supplies (D020): four SN6505B push-pull stages **from the 5 V rail** (the part is 2.25–5.5 V only — verified, a 15 V feed would have been a silent design error) through Würth 750316856 (1:4.67 → 23 V) with a 5.1 V zener split → +17.9/−5.1 V. The reinforced barrier lives in the driver ICs; the transformers are functional isolation (their 2.5 kV AC is a test rating, not a reinforced working-voltage cert) — acceptable pending the compliance target, flagged in D017.

## 8. Precharge / discharge (§7, captured)

Precharge energy is independent of resistance: E = ½CV² = ½ × 400 µF × 450² = **40.5 J**. R = 1.25 kΩ → τ = 0.5 s, ~2.5 s to >99 %, 0.36 A peak — relay closes into a dead bus and opens at near-zero current. Sequencing rule (on-sheet, verbatim): precharge → verify V_bus ≥ 95 % via bus sense → main contactor → open precharge; neither contactor closes without a valid bus reading.

Passive bleeder: 75 kΩ as a **4-resistor series string** (no single part spans 450 V): τ = 30 s → <60 V in 60 s at 2.7 W continuous. Active discharge: 880 Ω (4× 220 Ω series) + C3M0350120J, opto-driven: ~0.51 A initial, <5 s to 60 V, ~230 W single-shot pulse — chassis-mounted resistors (D021).

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

## 13. ⏳ Pending sections (updated as phases complete)

- Final BOM with line-item pricing and suppliers (task #3)
- MCU pin assignment table with AF-table citations (task #2)
- PCB layout: stackup, HV zones, clearance verification, DRC record (task #4)
- Fabrication package contents and PCBWay ordering parameters (task #5)
- Adversarial review findings and dispositions (task #7)
- Bring-up plan and open risks

*Draft maintained under version control; see git history for provenance of every change.*
