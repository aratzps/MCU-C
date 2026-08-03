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
