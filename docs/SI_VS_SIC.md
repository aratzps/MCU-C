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

## Sources

- DigiKey product listings, retrieved 2026-07-31: FS200R12KT4R, FS150R12KT4, FS300R12KE3, FS02MR12A8MA2B, MSCSM120TAM11CTPAG, CCB021M12FM3T, CCB016M12GM3T, NXH022S120M3F1PTG, FS13MR12W2M1H_B70 (digikey.com)
- BNEF Battery Price Survey, Dec 2025: pack $108/kWh, cells $74/kWh (about.bnef.com)
- Retail cell pricing: 18650batterystore.com (LG M50LT ~$250/kWh, Molicel P45B ~$900/kWh); appevsystems.com EV modules ~$467/kWh
