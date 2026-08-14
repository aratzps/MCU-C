# Adversarial review — findings and dispositions

Independent reviewers were tasked to attack this design before fabrication, with instructions to verify every claim against manufacturer datasheets rather than trust the repository, and to report nothing they could not defend with arithmetic.

**Review 1 — component stress, ratings and thermal** (2026-08-03). 17 substantive findings. Root cause of several: SPEC.md derived precharge and bleeder numbers from **400 µF**, but the selected bank is **5 × 100 µF = 500 µF**; nothing downstream was re-derived.

Status key: **FIX** = being corrected · **SPEC** = documentation/requirement correction · **ACCEPT** = accepted with rationale.

## Critical

| # | Finding | Evidence | Disposition |
|---|---|---|---|
| 1 | **RCD clamp resistors R603/R604** (390 k, 0603) see the full clamp voltage (230–360 V) in **parallel**, and dissipate 0.10–0.17 W each | 0603 thick film: max working voltage **75 V**, P70 = 0.1 W (Yageo/Vishay) | **FIX** — 3–5× overvoltage. Series string of 2512 parts, sized with the clamp respec (#3) |
| 2 | **Footprints physically impossible**: C601/C602 (0.68 µF 630 V X2, real body 10.5×16.5×26.5 mm, 22.5 mm lead pitch) assigned 0603; likewise C603 (10 nF 1 kV), C604 (10 µF 50 V), R605 | TDK B32921–928 datasheet | **FIX** — fabrication-blocking. Real footprints assigned |
| 3 | **Flyback drain overvoltage**: 25T:2T gives V_or = 194 V → steady plateau 694 V at the 500 V transient bus, **before** any leakage spike; with the as-drawn clamp the drain peaks ~811 V (450 V bus) / 861 V (500 V) | InnoSwitch3-AQ max **continuous** drain 725 V (900 V non-repetitive); PI: keep peak drain below 725 V under all normal operation | **FIX** — reduce V_or via turns ratio (transformer is custom and still [TBV]) and size the clamp properly. INN3949CQ (1700 V) remains the documented fallback |
| 4 | **DESAT cannot clear inside the module's short-circuit withstand**: 100 pF blanking → 1.24 µs ramp + 225 ns filter + 623–883 ns fault = **>1.5 µs** before turn-off begins | Module **t_SC < 1.2 µs** at −5/+18 V; 1ED3491 I_DESATC 500 µA, V_DESAT 9.18 V, internal LEB 400 ns | **FIX** — blanking capacitor 100 pF → 22 pF (272 ns); driver's own 400 ns LEB provides blanking |
| 5 | **Comparators cannot see the upper trip threshold.** LM2903 input common-mode range on a 3.3 V rail is 0 → **1.8 V**; the upper window threshold is **2.34 V**, and the upper half of the current signal swings outside CMR | LM2903 datasheet (CMR = V− to V+ − 1.5 V) | **FIX** — the hardware overcurrent trip would not function. Rail-to-rail **TLV7042** is mandatory, not the "alternate" the BOM called it |

## Major

| # | Finding | Evidence | Disposition |
|---|---|---|---|
| 6 | **5.1 V split zener at +5 % = 5.4 V exceeds the module's static V_GS(off) absolute maximum of −5 V** on every switch | Module AMR table | **FIX** — 4.7 V zener class (4.4–4.9 V) |
| 7 | **Gate-supply rail is open-loop**: worst case (5 V rail high, light-load V_F, zener low, secondary leakage peak-charging) reaches **+18.8…19.5 V** against a **+19 V** absolute maximum | Transformer 1:4.67, module AMR | **FIX** — post-regulate/clamp the +18 V leg and tighten worst-case stack-up |
| 8 | **The −5 V off-bias is undefined by design**: gate charge nets to zero at COM, so the zener runs below its knee (Z_ZK 480 Ω at 1 mA) with no bias path | BZT52 characteristics | **FIX** — add a bleed from VCC2 to GND2 (≥5 mA) per channel |
| 9 | **Passive bleeder fails its own requirement**: 74.8 kΩ × 500 µF → τ = 37.4 s, 450 → 60 V takes **75.4 s** vs the **<60 s** requirement (already marginal at the old 400 µF assumption) | SPEC §7.2 | **FIX** — 4 × 14 kΩ (56 kΩ): 60 s met, 0.90 W and 112.5 V per part, inside 2512 ratings |
| 10 | **Precharge energy understated**: ½ × 500 µF × 450² = **50.6 J** (62.5 J from a 500 V rail), and 5τ = 3.13 s, not the documented 40.5 J / 2.5 s | SPEC §7.1 | **SPEC + FIX** — resistor spec ≥65 J single-shot; precharge timeout ≥3.2 s |
| 11 | **5 V buck thermally impossible in SOT-23-6**: real load ≈1.65 A / 8.25 W → 1.13 W dissipated → ΔT_J ≈ 122 K; needs R_θJA ≤ 53 °C/W | LMR51430 R_θJA 107.8 °C/W; TI: keep T_J < 125 °C | **FIX** — move to a thermal-pad package / higher-current part |
| 12 | **3.3 V LDO marginal**: 1.7 V × 0.35 A = 0.60 W in SOT-223 → T_J ≈ 122 °C at 65 °C ambient, 142 °C at 85 °C | TLV1117 R_θJA 95.4 °C/W, T_J max 125 °C | **FIX** — replace with a buck or split the load |
| 13 | **Gate resistors over their rating**: R_on share 0.315 W and R_off share 0.266 W at 25 kHz vs a 1206's 0.25 W (0.206 W at 85 °C) | Q_g·ΔV = 27.4 µJ/cycle | **FIX** — ½ W 1206 or parallel pairs |
| 14 | **Thermal design point ~48 % low**: real module losses at 190 A rms / 250 V / 25 kHz ≈ **1039 W** (470 W conduction + 496 W switching + 73 W dead-time diode) → η 97.1 %, not 98 %; at 450 V ≈ **1436 W** | FS02MR12A8MA2B Tables 6/8 | **SPEC** — §11.4 corrected. *The module itself keeps 3–4× thermal margin* (R_th,j-f 0.121 K/W vs 0.36–0.49 required); it is the **coolant loop and heat exchanger** that must be sized for ~1.05–1.45 kW |
| 15 | **Split reference on the HV-side LDO**: U702 GND sits on the Kelvin-source net while its own output capacitor and the AMC1311 GND1 sit on DC_BUS_N; the two join only through module internals — several volts of bounce at 4 kA/µs | Module L_s,DS 8 nH | **FIX** — move U702 GND to DC_BUS_N (already flagged [TBV] in D022) |
| 16 | **DC-link carrier planes are in the main current path at 2 oz**: ~1.9 mΩ total → **37 W at the 140 A peak**, ~65 K rise over 120 s | D024 calls it "heavy copper"; 2 oz is not | **FIX/SPEC** — specify 4 oz (or document the busbar as the parallel conductor, which D021 implies but the board does not state) |
| 17 | **Contactor freewheel diode undersized**: BAS316 is 250 mA I_F(AV) / 500 mA I_FRM; a 35 kW-class contactor coil pulls 1.7–2.5 A | Coil current is specified nowhere in the design | **FIX + SPEC** — 1 A-class diode, and a coil-current budget written into §11.2 |

## Minor / accepted

- **Discharge bank can be commanded on with the bus live** (230 W into 100 W of resistors, no hardware inhibit) — **FIX**: interlock discharge against bus-live.
- **Relay coil suppression**: plain diode lengthens release time, which Hongfa warns reduces contact life — **FIX**: diode + zener.
- **Bus divider accuracy 1.11 %** before tempco vs the ±1 % requirement — **SPEC**: calibrate in firmware or specify 0.1 % parts.
- **AMC1311 saturates at 502 V**, so a 550 V excursion reads as 500 V — **ACCEPT** for rev A (OVP threshold is 490 V, well inside range); noted.
- **AMC1311 input RC corner 123 Hz** gives 1–3 ms OVP response — **FIX**: reduce filter capacitor to ~1 nF.
- **Miller-clamp FET BSS138 at 1.4 A Miller current** vs ~0.8 A I_DM — **FIX**: 2 A-class SOT-23 FET.
- **Cap current sharing on the carrier**: worst unit takes 22.2 % (25.3 A) vs 20 % ideal — **ACCEPT** with symmetrised feed noted; inside rating at ≤80 °C.
- **J501–J503 family mismatch** (BOM says JST PA, footprint is JST PH) — **FIX**: reconcile.
- **PCB stackup block absent** from the board file, so copper weight never reaches the fab files — **FIX**.
- **No internal enclosure ambient is specified anywhere** — **SPEC**: the single cheapest high-value action; findings 11, 12, 13, 16 and the cap-bank margin all resolve differently at 55 °C than at 85 °C.

## Verified correct (reviewer's explicit coverage)

DC-link bank against 114 A rms for 120 s (14.7 K rise per cap; the block's own thermal time constant is ~43 min, so the steady-state calculation is already the conservative bound — **the SPEC §14 open item on ripple duty is resolved**); module junction margin (3–4×); gate-supply power chain (0.68 W/channel, transformer at 60 % of its application point, volt-second margin 2×); DESAT blocking diodes (500 V worst case against 1000 V, unshared); bus divider stress (124.5 V, 20.7 mW per part); bleeder part stress; discharge chain energy and FET dissipation; precharge relay duty (4 orders of magnitude inside its switching capability); series X2 input capacitors needing no balancing network; all three inductors' saturation margins; every connector's current rating; **the Miller-clamp return to VEE2 being correct** (returning it to GND2 would have caused shoot-through); and the overcurrent window scaling arithmetic (the thresholds are right — only the comparator part was wrong).

---

# Review 2 — precharge / MCU / connectors / dangling sweep (2026-08-03)

Independently verified all 100 MCU pins against ST DocID022152 Table 7 (and found the *review brief's own* assumed pin list wrong while the schematic was right — VDD/VSS/VSSA correct as drawn).

**New criticals:** the **+12 V rail cannot supply a contactor coil** (same SOT-23-6 thermal impossibility as the 5 V rail but at 1.7× the load); the **three motor phase outputs are dangling** — `PHASE_U/V/W_OUT` are single-node nets and no phase terminal exists anywhere in either project, despite D021 describing M6 output studs.

**New majors:** the discharge FET's gate has **no low-impedance off-state clamp** (a 450 V dv/dt step capacitively injects ~4.4 V, above V_GS(th) min 1.8 V, against a 10 MΩ pull-down and a µA-class photovoltaic turn-off); D403's 18 V zener **clamps above the FET's V_GS maximum** and never inside its operating maximum; R427 = 100 Ω **overdrives the STM32 pin** (17–21 mA vs an 8 mA characterisation point) leaving turn-on time indeterminate; and C702's pin 1 is **unconnected** — the LDO output capacitor whose wire was never drawn.

**Verified correct:** the §7.1 precharge sequence is fully permitted by the hardware; both coil drivers are boot-safe (1 kΩ series + 10 kΩ pull-down); both freewheel diodes correctly oriented; the relay's symbol-to-footprint pad mapping is consistent and its contact polarity correct; K401 never breaks load; Q403's TO-263-7 pinout matches the netlist exactly; every MCU power pin present and correct; every peripheral pin checked against the AF table with no function assigned to a pin that lacks it; USB-C, SWD and ISO1042 wiring all correct pin-for-pin.

---

# Review 3 — circuit correctness (2026-08-03)

**Verdict: not fabrication-ready.** Seven critical findings, each anchored to a netlist fact plus a datasheet quote.

| # | Finding | Consequence |
|---|---|---|
| **CR-1** | **The gate-driver fault latch can never be cleared.** RDYC only rises when FLT_N is already high; FLT_N only clears on a rising RDYC edge. The MCU's reset is ANDed in, so it can only add another *low* — closed loop, no override | After any DESAT event, driver over-temperature, or the staggered power-up of six drivers, the bridge is dead with no recovery path. **The board very likely never enables the bridge, even once** |
| **CR-2** | **DESAT chain is ~5.8 µs** (1.84 µs blanking ramp + 1.58 µs filter + 0.33 µs offset + 2.05 µs soft-off) against the module's **t_SC < 1.2 µs** | The die fails ~5× over before the gate moves |
| **CR-3** | The AMC1311's high-side LDO returns to **VGD_LS_COM** (the module's Kelvin-source pins) while its own output caps and the AMC1311's GND1 sit on **DC_BUS_N** — joined only inside the module | Tens of volts across the LDO every switching edge; a Kelvin node used as a power node |
| **CR-4** | RCD clamp on 0603 parts: 3.6× power, 7.5× voltage, and **876 V on a 900 V device** at the 500 V rail | PI's own reference runs at 72 % of BV_DSS; this is 97 % |
| **CR-5** | **Flyback transformer saturates at the controller's current limit** — B_pk 425 mT typ / 476 mT worst case against 3C96's 440 mT at 100 °C (the transformer was copied from a DER using a lower-current-limit part) | Uncontrolled di/dt through the primary switch on every overload or hard start |
| **CR-6** | HV-rated aux capacitors on 0603 footprints, two of them **in series across the 450 V link** | A stock 0603 fitted at build fails short → the second sees 500 V → **dead short across a 500 µF bank** |
| **CR-7** | 5 V converter dissipates 1.33 W in a 107.8 °C/W SOT-23-6 → ΔT_J ≈ 143 K | Thermal shutdown; the real ceiling is ~0.45 A against a 1.64 A load |

**The most consequential major: MJ-1 — the hardware overcurrent trip never reaches TIM1_BKIN.** `OC_LATCH_N` goes only to a supervisor gate and an LED; `OC_LATCHED` goes to a plain GPIO. FAULT_BKIN carries *driver* faults only. **SPEC §9.2's central claim — "Fault → PWM disable: drives TIM1_BKIN" — is false as built for the overcurrent path**, and the trip's only effect hangs on a single resistor.

Other majors: comparators are the wrong part twice over (TLV7032 is push-pull, not open-drain; LM2903 cannot see the upper threshold) and both are ~3 µs parts against a "<1 µs" spec claim; the 300 A trip is really ±245–356 A because the thresholds ride on a ±4 % rail while the transducer is not ratiometric; the bus-sense filter has a 123 Hz pole so the 490 V OVP arrives ~363 V late; ±1 % bus accuracy is unachievable against a ±4 % reference; a current-sense harness disconnect is **not fail-safe** (silently disables one phase's protection); no VCC2↔VEE2 decoupling on any gate-supply domain; the gate-rail zeners have no guaranteed bias current; the LM5175 current limit trips at 17 A against a 7.6 A inductor; and the SinCos front end adds ~48° of electrical lag at speed.

**Verified correct** (extensive): end-to-end PWM polarity through gating, RC and driver to the module gate; overlap elimination genuinely forces both outputs low; the dead-time diode orientation on all six channels; channel-to-switch mapping; the OC latch is genuinely edge-triggered and latching; TIM1_BKIN polarity matches the STM32 reset default; boot-safe pull-downs on all six PWM lines; gate resistors match the module datasheet test condition exactly; CMTI margin 200 V/ns vs 14.6 kV/µs; comparator polarity correct in all six positions; the divider arithmetic exact; every LM5175 configuration pin; the SN6505B pinout; the flyback FB divider and bias winding; every MCU power pin and ADC channel; AD2S1205 interface-mode strapping; USB-C, SWD, CAN and NTC front ends; and whole-design sweeps finding no output contention, no driverless inputs, and no unconnected power pins.


---

# Fix pass — dispositions as implemented (2026-08-03)

Three fix agents worked with strict file ownership. Where an agent's verification contradicted the instruction it was given, the agent's finding won — twice, and both are recorded here because they are the most useful entries in this document.

## Instructions that were wrong, and were corrected by the implementer

| Item | What I directed | What was actually true | Outcome |
|---|---|---|---|
| **CR-5** (flyback core saturation) | Substitute INN3999CQ for its lower current limit, or rewind the transformer | The InnoSwitch3-AQ family has **no reduced current-limit setting** — the BPP capacitor selects between standard (0.47 µF) and increased (4.7 µF). The premise for a part swap was wrong | Capacitor changed 4.7 → **0.47 µF**: B_pk 360 mT typ / 403 mT worst, below the reference design's own 376 mT point, **and it keeps more power headroom (2.30 A vs 2.13 A) than the part swap would have.** Controller retained |
| **MJ-22** (diff-amp gain) | Set R709 = R710 = 16.2 kΩ for ~3.23 V at 500 V | At that gain the 490 V OVP threshold lands at **3.162 V against a TLV1117 rail that is 3.168 V at −4 %** — an RRIO output cannot reach it, so the overvoltage protection would have been **unreachable by construction** | Gain **1.50**: 500 V → 2.988 V, clip 3.000 V, 90.5 % of range, 168 mV headroom, 0.135 V of bus per LSB |

## Fixes implemented

**aux_power / bus_sense** — CR-4 (RCD clamp rebuilt as 6 × 39 kΩ 1206 in 3s2p; worst case 0.35 W and 117 V per part), CR-5 (above), CR-6 (every impossible footprint replaced, including the 0.68 µF X2 boxes onto a real 22.5 mm radial pattern), CR-7 (both bucks → LMR33630ADDAR in HSOIC-8 PowerPAD, 42.9 vs 107.8 °C/W, thermal pad wired as AGND), MJ-5 (bus filter 100 nF → 100 pF: OVP response 1.3 ms → 13 µs), MJ-6 (tolerance fields added), MJ-10 (LM5175 sense 10 → 30 mΩ — it was tripping at 17 A against a 7.6 A inductor saturation), MJ-14 (flyback line UV/OV enabled; brown-in 32.5–44.2 V), MJ-16 (C702's unconnected pin — the LDO output capacitor whose net was never drawn), MJ-18 (input capacitance to datasheet requirement), MJ-19 + MN-7 (aux priority made real: 0.62 V worst-case margin), MJ-22 (above), MN-13, MN-24.

**Carried into the T601 purchase specification:** the clamp analysis shows the primary switch drain reaches 731 V / 761 V / 806 V at leakage inductances of 1 / 2 / 4 µH, against a 725 V continuous limit — so **L_k ≤ 2 µH becomes a purchase requirement**, where the reference design tolerated 6.5 µH. Also flagged: D601 (US1M) sits at 80 % of its 1000 V rating where the reference design uses two in series.

## Deliberately not implemented, and why

- **CR-3** was left open by the first implementer rather than guessed at: it required a footprint for the transformer that **bridges the reinforced isolation barrier**, and inventing that geometry is precisely the failure class this review exists to prevent. Implemented separately once verified land-pattern data (rendered from the manufacturer drawing) was available.
- **MN-14** (aux input TVS and reverse-polarity element) deferred rather than fitted with unverified parameters.

---

# Layout-phase finding: netclass patterns that matched nothing (2026-08-03)

Found during PCB re-import, and the most dangerous defect of the whole project.

**What was wrong.** Seven `HV_BUS` netclass patterns in `mcuc_inverter.kicad_pro` matched **no real net**, including `/Auxiliary power/DC_BUS_N` where the actual net is `/Precharge and contactor/DC_BUS_N`. So **the board's main DC negative rail — the return for the entire high-voltage domain — was silently unclassified**, taking the 0.2 mm default clearance instead of the 2.0 mm HV rule and the 6.4 mm barrier rule. The adversarial fix pass had also created new nets at bus potential (the RCD clamp string, a new UV/OV divider, a renamed clamp node, the discharge gate, the bus-sense tap) that no pattern covered at all.

**Why nothing caught it.**

- ERC passes — the schematic is correct; this is a *board configuration* fault.
- DRC passes — the rules were not violated because they were **not being applied** to those nets.
- Nothing looks wrong on screen: the nets exist, they are named, they connect correctly.
- **A netclass pattern that matches nothing produces no warning.** It fails open, silently.

The same trap bit the first repair attempt: KiCad prefixes sheet-local net names with their sheet path, so a bare `CLAMP_NODE` pattern is inert — the working form is `*CLAMP_NODE`. That correction, too, produced no error when it matched nothing; it was caught only because the violation count moved the wrong way.

**How it was found.** Not by a checker — by an agent cross-checking the netclass configuration against the *actual exported net list* rather than assuming the configuration was current. That comparison is now a standing check: **every HV pattern must match at least one real net**, asserted programmatically.

**What it exposed.** Correct classification surfaced violations in three waves: 43 → (LV stitching removed) 37 → (placement repaired) 0 → (DC_BUS_N finally classified) 72. Each wave was real spacing that would have been fabricated. The last wave revealed a structural error the earlier passes had only worked around: **the bus-sense high-side block, including its barrier-crossing transformer, had been placed in low-voltage territory** because no pocket existed in the HV zone.

**The lesson worth keeping.** Automated checks verify that a design satisfies the rules it was given. They cannot verify that it was given the right rules. Every rule that selects by pattern — netclasses, DRC custom rules, keepout scopes — needs an explicit test that the selector actually selects something.
