# Si IGBT vs SiC — cost analysis including battery compensation

**Date:** 2026-07-31. All prices verified live on DigiKey US; battery prices from BNEF Dec 2025 survey and retail checks. Supports SPEC.md §14 open item 2. This document analyses; the decision is the owner's.

---

## 1. The actual parts and the actual premium

Requirement (SPEC §4.3): 1200 V six-pack, ≥ 200 A continuous class, sustains 190 A rms for 120 s, isolated base, NTC.

| | Si IGBT | SiC MOSFET |
|---|---|---|
| Part | **Infineon FS200R12KT4R**, EconoPACK 3, 200 A @ Tc 80 °C | **Infineon FS02MR12A8MA2B**, HybridPACK Drive G2, 1.9 mΩ, 390 A class (or Microchip MSCSM120TAM11CTPAG, 251 A, $769, out of stock) |
| Price, qty 1 | **$131.88** (18 in stock) | **$767.12** (51 in stock) |
| **Module premium** | — | **≈ $635** |

The frequently-assumed "$300–500 SiC premium" does not exist at this current class: every *stocked* SiC six-pack below $300 (Wolfspeed CCB, Infineon Easy 2B, onsemi F1) is a 48–90 A-class part, far below our 190 A/120 s requirement. At our size, SiC six-packs live in automotive traction packages at automotive prices.

Runner-up Si parts: FS150R12KT4 ($118) is below the 200 A criterion; FS300R12KE3 ($407, NRND) buys margin but erodes the price case. The HybridPACK SiC part is a pin-fin direct-cooled automotive form factor — mechanically different from an EconoPACK on a flat cold plate; that changes the cold-plate design, in SiC's favour thermally but with a less conventional mounting.

## 2. Battery compensation math

Efficiency (SPEC §11.4): Si ≈ 96.5 %, SiC ≈ 98 %. For the same *delivered* energy, the pack must supply:

```
ΔE / E_delivered = 1/0.965 − 1/0.98 = 1.0363 − 1.0204 = 0.0159  →  +1.59 % pack capacity
```

Extra battery cost = 0.0159 × pack size [kWh] × battery price [$/kWh]:

| Battery price basis ($/kWh) | 10 kWh pack | 20 kWh | 30 kWh | Break-even pack size vs $635 |
|---|---|---|---|---|
| OEM pack level, $108 (BNEF 2025) | $17 | $34 | $52 | ≈ 370 kWh |
| DIY energy cells (LG M50LT), ~$250 | $40 | $79 | $119 | ≈ 160 kWh |
| EV-conversion modules w/ BMS, ~$467 | $74 | $148 | $223 | ≈ 86 kWh |
| High-power cells (Molicel P45B), ~$900 | $143 | $286 | $429 | ≈ 44 kWh |

**On pure module-vs-battery capex, Si wins for any realistic pack behind an EMRAX 188** (motorcycle / light EV / VTOL, ~5–30 kWh). Even with expensive high-power cells at 30 kWh, the extra battery ($429) is cheaper than the SiC premium ($635).

## 3. Offsets the naive comparison misses

The Si path carries system costs beyond battery:

| Item | Si penalty | Basis |
|---|---|---|
| DC link | ≈ +350 µF of 900 V film ≈ **+$70–140** | §6.1: Si at ~12 kHz needs ≥ 750 µF vs 400 µF |
| Cooling | ≈ **+$50–150**, +~1 kg | §11.4: 1225 W vs 700 W peak-condition heat for 120 s |
| Acoustic | Si at 10–15 kHz switches **inside the audible band** — the drive will whine. SiC at 25 kHz is silent | Not monetisable, real for a vehicle |
| 450 V derating | IGBT switching losses grow faster with bus voltage; high-bus derating (§2.1, open item 3) will be harsher | Open item 3 |
| Mass | +1.59 % pack ≈ +0.3–0.5 kWh ≈ **+2–3 kg** at 20 kWh, plus cooling mass | Matters greatly for VTOL/aviation, mildly for ground |

Adjusted Si-vs-SiC gap for a representative 20 kWh conversion-module pack:

```
SiC premium:            +$635
Battery compensation:   −$148
DC-link delta:          −$105 (midpoint)
Cooling delta:          −$100 (midpoint)
Net SiC premium:        ≈ +$280, buying: silence, ~3-4 kg, easier cooling,
                        better 450 V behaviour, ~1.5 % more range per charge
```

## 4. Assessment

- **Cost-driven ground vehicle at ~250 V nominal:** Si (FS200R12KT4R) is the rational choice; net saving ≈ $280–500 depending on pack. Accept the audible switching and beefier cooling.
- **Aviation/VTOL, or if 450 V operation is a primary mode, or if acoustic matters:** SiC; the $280 net premium is small against airframe-level $/kg.
- Both candidate parts are in stock today; stock at qty ~20–50 means either should be *purchased at design commit*, not at layout completion.

Numbers to re-verify at commit time: FS200R12KT4R 190 A/120 s junction excursion against the datasheet transient thermal curve and a real cold-plate model; HybridPACK G2 mounting/cooling concept if SiC.

---

## 5. At scale: 10,000 units/year

**What is public:** distributors publish almost no volume breaks for modules of this class — Si FS200R12KT4R shows $131.88 @ 1 / $107.22 @ 10 (DigiKey) and $119.62 @ 1 / $114.94 @ 30 (LCSC); the SiC HybridPACK G2 shows a single $767.12 break, quote-only beyond (MOQ 12/tray at Rutronik, "price on request"). 10 k/yr pricing is negotiated directly with Infineon/franchise everywhere. So the volume numbers below are **estimates from analyst data, clearly labelled as such**, not quotes.

**What the industry data says:** the SiC-to-Si ratio at volume is consistently ~3× at the die/device level (PGC Consultancy 2021 measurement, Wolfspeed's own "up to 3×" statement, McKinsey via secondary, and our own qty-1 per-amp cross-check: Si ≈ $0.55–0.66/A vs SiC ≈ $1.97/A ≈ 3.0–3.6×). Finished-module premiums in adjacent markets (solar) run +20–40 %. Analyst parity window: SiC reaching 2–2.5× Si around 2027–2029 with the 200 mm wafer transition; full parity not expected.

**Estimated per-unit picture at 10 k/yr** (module negotiated at typical 30–50 % off distribution; battery at OEM pack pricing $100–150/kWh instead of retail; caps/cooling at volume −40 %):

```
Si module          ~$70–90        SiC (right-sized ~250 A class,
                                  negotiated/custom)  ~$300–450
SiC premium:                      ≈ $225–350
Battery compensation (20 kWh):    −$32–48
DC-link delta:                    −$40–80
Cooling delta:                    −$30–80
Net SiC premium at 10 k/yr:       ≈ $70–200/unit  →  $0.7–2 M/yr program cost
```

The gap *narrows* at scale (battery compensation shrinks to OEM pricing, but the module premium shrinks faster in absolute terms), and it keeps narrowing over a program's life given the SiC price trajectory. At 10 k/yr the decision drivers shift from BOM to strategic:

- **Supply chain:** Si EconoPACK lead time 16 wk vs SiC HybridPACK 39 wk (DigiKey listed); at 10 k/yr both need allocation contracts, but the SiC channel is tighter. The Microchip 251 A SiC part is zero-stock; FS300R12KE3 is NRND — do not baseline either for a program.
- **Product-level:** audible 10–15 kHz switching on the Si path is a per-unit product characteristic, not a one-off annoyance — at 10 k units it becomes a market-perception/warranty question money can't directly fix.
- **Custom module option opens:** at 10 k/yr Semikron-Danfoss, onsemi and Infineon will all quote application-specific six-packs (including right-sized SiC around 250 A, avoiding paying for the G2's 390 A) — the $300–450 SiC estimate reflects that, and a serious program should RFQ all three.
- **Benchmark sanity check:** Tesla's entire Model Y SiC inverter was ~$522 at true OEM megavolume (Munro teardown, 2020) — confirming that at sufficient scale the whole SiC power stage lands below today's single-module distribution price.

**Bottom line at 10 k/yr:** net SiC premium ≈ $70–200/unit and falling year-on-year. For a program at this scale the efficiency, acoustics, mass and 450 V headroom almost certainly justify it; the qty-1 hobbyist math (where Si wins) inverts somewhere around the hundreds-of-units mark.

## 6. GaN — evaluated and ruled out for the power stage (2026)

Checked against shipping products, not headlines (all verified 2026-07-31):

| Requirement | GaN reality |
|---|---|
| ≥ 900 V switch class (450 V bus + margin, §4.1) | The only ≥ 900 V GaN discretes ever distributed (Transphorm 900 V SuperGaN) are **marked Obsolete at DigiKey**; best was 34 A anyway. Infineon CoolGaN tops at 700 V; Navitas/Nexperia/VisIC/CGD are 650 V; PI's 900–1700 V PowiGaN exists **only inside ≤100 W flyback ICs**, no discrete sold |
| 190 A rms phase current | Largest stocked 650 V GaN: Navitas NV6514C, 90 A TOLL. Nothing at 900 V above 34 A (obsolete). No GaN six-pack exists in distribution; GaN Systems' 650 V/300 A three-phase module was an eval kit only |
| Overvoltage ruggedness (regen transients) | Lateral GaN HEMTs have **no avalanche capability** — vendors specify transient-survival ratings (e.g. 800 V on 650 V parts) via energy absorption into C_oss, not a clamping mechanism. Avalanche-capable vertical GaN is research-stage only |
| Would GaN's speed even help? | No — a 25 kHz FOC drive gains nothing from 100 kHz+ capability, while GaN's fast dv/dt edges stress motor winding insulation and bearings (drives deliberately *slow* edges) |

The one credible >400 V-bus GaN path (VisIC's 650 V devices in a 3-level topology, 800 V bus) means doubling the switch count and a far more complex inverter — not sensible for this design. **Verdict: GaN is not viable for this power stage in 2026.** Re-evaluate only if avalanche-rated vertical GaN or ≥900 V GaN modules at ≥200 A class reach distribution. GaN *is* used where it fits: the aux flyback's InnoSwitch3-AQ is a 900 V PowiGaN part (D014).

### Additional sources (§5–6)

- DigiKey price breaks: FS200R12KT4RBOSA1, FS150R12KT4BOSA1, FS02MR12A8MA2BBPSA1, FS03MR12A6MA1BBPSA1, MSCSM120TAM11CTPAG; LCSC C535453; rutronik24.com (MOQ/quote-only)
- PGC Consultancy SiC cost roadmap (pgcconsultancy.com); surgepv.com SiC-vs-IGBT 2026 analysis w/ Applied Materials wafer data; Wolfspeed knowledge-center 3× statement; Munro teardowns via chargedevs.com
- GaN: DigiKey obsolete listings TP90H050WS/TP90H180PS; power.com PowiGaN releases; Navitas NV6514C DigiKey listing; VisIC 100 kW 3-level reference (visic-tech.com); ST AN6418 on p-GaN drain overvoltage robustness; Infineon CoolGaN/EasyPACK GaN announcements (semiconductor-today.com)

## Sources

- DigiKey product listings, retrieved 2026-07-31: FS200R12KT4R, FS150R12KT4, FS300R12KE3, FS02MR12A8MA2B, MSCSM120TAM11CTPAG, CCB021M12FM3T, CCB016M12GM3T, NXH022S120M3F1PTG, FS13MR12W2M1H_B70 (digikey.com)
- BNEF Battery Price Survey, Dec 2025: pack $108/kWh, cells $74/kWh (about.bnef.com)
- Retail cell pricing: 18650batterystore.com (LG M50LT ~$250/kWh, Molicel P45B ~$900/kWh); appevsystems.com EV modules ~$467/kWh
