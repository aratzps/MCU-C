# MCU-C Sourcing BOM — verified parts, prices and suppliers

**Basis:** every line verified against a manufacturer datasheet AND a live distributor listing on 2026-07-31…08-02 (dates in DECISIONS.md D011–D022). Prices USD. Quantity-per-board in the Qty column; refdes ranges follow the schematic page series. A refdes-level CSV export follows PCB completion.

**Sourcing watch-list (order at design commit — long leads behind current stock):**

| Part | Why | Stock at check |
|---|---|---|
| FS02MR12A8MA2B (module) | 39-wk factory lead behind stock | 51 @ DigiKey |
| AD2S1205WSTZ | 0 stock / 20-wk (TME residual) | 0 @ DigiKey |
| LEM HOYS 200-S/SP33 | thin stock | 5 @ DigiKey |
| STM32F405VGT6 | DigiKey/Mouser dry; Newark holds | 20,334 @ Newark ($7.36) |
| Hongfa HFE80V relay | non-DigiKey channel (Rutronik/RS) | 80 @ Rutronik |
| C3M0350120J | adequate, not deep | 386 @ DigiKey |

## 1. Power stage & DC link

| Qty | Part | Function | Unit $ (1/100) | Supplier | Notes |
|---|---|---|---|---|---|
| 1 | Infineon **FS02MR12A8MA2B** | SiC six-pack module | 767.12 / quote | DigiKey | D016; pin-fin coolant jacket |
| 5 | Vishay **MKP1848C71010JY5** | DC-link film 100 µF/1000 V, 25 A rms | 28.85 / 20.55 | DigiKey | Bank: 500 µF / ≥125 A rms; P/N decode verified (C61010 = 10 µF trap) |
| 2 | Amphenol **SLPRBTPSR / SLPRBTPSB** | HV DC input connectors (+/−) | 13.13 / 9.49 ea | DigiKey | 200 A / 1 kV, panel, sealed |
| 3+ | Würth **7461097** (WP-BUFU M6 press-fit, 180 A) | Busbar/stud terminations | 3.22 / 2.47 | DigiKey | "REDCUBE THR M6" does not exist — press-fit family only |

## 2. Gate drive

| Qty | Part | Function | Unit $ (1/100) | Supplier | Notes |
|---|---|---|---|---|---|
| 6 | Infineon **1ED3491MC12M** | Isolated SiC driver | 6.31 / 4.07 | DigiKey | D017; reinforced, 200 V/ns |
| 6 | Infineon **BSS138**-class SOT-23 | Miller-clamp FET | ~0.15 | DigiKey | returns to VEE2 |
| 12 | SMC **US1M** | DESAT blocking (2× per ch) | 0.13 / 0.05 | DigiKey | 1000 V, 2 kV series standoff |
| 4 | TI **SN6505BDBVR** | Push-pull driver (5 V rail) | 2.23 / ~1.35 | DigiKey | 5 V-only — verified constraint |
| 4 | Würth **750316856** | Gate supply transformer 1:4.67 | 4.49 / 3.45 | DigiKey | 23 V raw → +18/−5 split; AEC-Q200 |
| 8 | TSC **SS310** (SMC pkg) or MCC **SL310A-TP** (SMA) | Gate-supply rectifiers | 0.65 / 0.26 | DigiKey | package flag: SS310 is SMC |
| 4 | MCC **BZT52C5V1S-TP** | 5.1 V split zener | ~0.14 | DigiKey | BZX384-C5V1 unstocked everywhere |

## 3. Control & sensing

| Qty | Part | Function | Unit $ (1/100) | Supplier | Notes |
|---|---|---|---|---|---|
| 1 | ST **STM32F405VGT6** | MCU | 7.36 (Newark) | **Newark/Farnell** | DigiKey 0-stock/52-wk |
| 3 | LEM **HOYS 200-S/SP33** | Phase current transducers | 37.11 | DigiKey | D019; ±500 A, reinforced |
| 3 | TI **LM2903DR** | 300 A window comparators | 0.24 / 0.125 | DigiKey | open-collector confirmed; TLV7042DGKR alternate |
| 1 | TI **AMC1311BDWV** | Bus-voltage isolated amp | 10.02 (tube) | DigiKey | D022; V_IOWM 2120 V DC |
| 4 | Yageo/Vishay 750 kΩ 1206 1 % | Bus divider string | ~0.02 | DigiKey | 124.5 V, 20.7 mW per part |
| 1 | ADI **AD2S1205WSTZ** | Resolver-to-digital | 29.87 | DigiKey/TME | **order early**; AD2S1210 fallback = redesign |
| 1 | ADI **AD8397ARDZ** | Resolver exciter buffer | ~7 | DigiKey | PALTA carry-over |
| 1 | Abracon **ABM3B-8.000MHZ-B2-T** | MCU HSE crystal (18 pF) | 0.69 / 0.45 | DigiKey | 75 k stock |
| 1 | 8.192 MHz crystal [final P/N at BOM export] | AD2S1205 clock | ~0.7 | DigiKey | datasheet nominal |
| 1 | TDK **B57861S0103F040** | Coldplate NTC (chassis) | 1.97 / 1.44 | DigiKey | AEC-Q200 glass bead |
| 1 | Murata **NCU18XH103F6SRB** | Board NTC | ~0.12 | DigiKey | NCP18 successor (NFND) |
| 1 | Diodes **APX809-46** | 5 V supervisor (resolver) | ~0.35 | DigiKey | PALTA carry-over |

## 4. Auxiliary power

| Qty | Part | Function | Unit $ (1/100) | Supplier | Notes |
|---|---|---|---|---|---|
| 1 | PI **INN3990CQ-TL** | HV flyback (30 V start) | 8.93 / 5.89 | DigiKey | D014/D020; only 9.4:1-capable family |
| 1 | Custom flyback transformer | Lp<500 µH, ≥4 kV | quote (Würth/ICE custom) | — | DER-948Q pattern; **[TBV — the one custom magnetic]** |
| 2 | TDK **B32923C3684M000** | HV input films 0.68 µF/630 V X2 | 0.79 / 0.35 | DigiKey | series pair |
| 1 | TI **LM5175RHFR** | 12–24 V buck-boost | 8.25 / 5.41 | DigiKey | boost-only topology fails at 24 V — verified |
| 5 | TI **CSD18543Q3A**-class | Buck-boost + ideal-diode FETs | ~1.10 | DigiKey | 4 + 1 |
| 1 | TI **LM74610QDGKRQ1** | Ideal-diode controller | 2.59 / 1.58 | DigiKey | AEC-Q100 |
| 2 | TI **LMR51430XDDCR** | 5 V / 12 V bucks | 1.84 / ~1.10 | DigiKey | 36 V in, 3 A |
| 1 | TI **TLV1117-33CDCYR** | 3.3 V LDO | 0.46 / 0.25 | DigiKey | rail source |
| 1 | Murata **NXE2S0505MC-R7** | Isolated CAN 5 V, 3 kV | 4.55 / 4.02 | DigiKey | Mornsun alt is NRND |
| 1 | Diodes **B540C-13-F** | Flyback OR Schottky | 0.96 / 0.39 | DigiKey | "SS54" is marketplace-only |

## 5. Precharge / discharge / protection

| Qty | Part | Function | Unit $ (1/100) | Supplier | Notes |
|---|---|---|---|---|---|
| 1 | Hongfa **HFE80V-20C/450-12-HTPAJ** | Precharge relay, 450 V DC | 18.92 | **Rutronik/RS** | purpose-built EV precharge; DigiKey fallback: TE LEV100A4ANG $145 |
| 1 | Vishay **VOM1271T** | Discharge FET photovoltaic driver | 2.08 / 1.25 | DigiKey | eliminates floating supply (refinement queued) |
| 1 | Wolfspeed **C3M0350120J** | Active discharge FET | 6.39 / 3.08 | DigiKey | ~0.3–0.5 W at 8 V gate, current-limited duty OK |
| 1 | 1.25 kΩ ≥50 W pulse wirewound (chassis) | Precharge resistor ≥41 J | ~8–15 | DigiKey (final P/N at BOM export) | chassis-mount |
| 4 | 220 Ω 25 W (chassis) | Discharge bank | ~4 ea | DigiKey (final P/N at export) | 230 W / <5 s single-shot |
| 4 | 18.7 kΩ 3 W thick film | Bleeder string | ~0.5 | DigiKey | series, 0.68 W each |
| 1 | onsemi **MM3Z18VT1G** | Discharge gate zener 18 V | 0.16 | DigiKey | BZX384-C18 unstocked |
| 6+ | MCC **BAS316-TP** | Small signal (flyback/clamps) | 0.13 / 0.05 | DigiKey | Nexperia BAS316 0-stock |
| 3+ | AOS **AO3400A** | Relay/LED drivers | 0.52 / 0.20 | DigiKey | plain AO3400 obsolete |

## 6. Comms & connectors

| Qty | Part | Function | Unit $ (1/100) | Supplier | Notes |
|---|---|---|---|---|---|
| 1 | TI **ISO1042DWR** | Isolated CAN, 5 kV | 5.28 / 3.37 | DigiKey | replaces legacy ISO1050 |
| 1 | GCT **USB4085-GF-A** | USB-C receptacle | 0.91 / 0.66 | DigiKey | check cutout vs drawing |
| 1 | ST **USBLC6-2SC6** | USB ESD | 0.57 / 0.22 | DigiKey | |
| 1 | Samtec **FTSH-105-01-L-DV-K** | SWD 10-pin keyed | 1.37 / 0.97 | DigiKey | keyed = cheaper + deeper stock |
| 3 | JST **B05B-PASK-1** + PAP-05V-S | HOYS harness | 0.34 + 0.13 | DigiKey | |
| 2 | JST **SM08B-SRSS-TB** | Hall/temp + enc/SinCos | 0.80 / 0.58 | DigiKey | |
| 1 | Molex Micro-Fit 3.0 8-pos (vertical variant TBD at layout) | CAN/aux/contactor I/O | ~1.9 | DigiKey | 43045-0800 is right-angle — pick orientation at layout |

## Rough cost roll-up (qty 1, majors only)

```
Module               767      Gate drive (6 ch + supplies)   ~95
DC-link bank         144      Current sensing (3× HOYS+cmp)  ~113
MCU + control        ~55      Aux power                      ~35
Precharge/discharge  ~45      Resolver chain                 ~40
Connectors/misc      ~40      PCB (4-layer, est.)            ~60–120
                              ─────────────────────────────────────
                              ≈ $1,330–1,450 + custom transformer
                                + busbar fabrication + cold plate
```

The module is 55 % of BOM cost at qty 1 — consistent with the D016 analysis; at 10 k/yr the module premium compresses first.
