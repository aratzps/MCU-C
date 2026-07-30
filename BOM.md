# MCU-C — Bill of Materials

## 1. MCU & Core

| RefDes | Part | Package | Qty | Notes |
|---|---|---|---|---|
| U1 | STM32F405RGT6 | LQFP100 | 1 | VESC-compatible MCU, 168MHz |
| Y1 | HCSP-1210-8.0M00 | 0805 | 1 | 8MHz HSE crystal (PH0/PH1) |
| Y2 | HCRT-1210-32.768 | 0805 | 1 | 32.768kHz RTC crystal (PC0/PC1) |
| C_MCU_3V3 | 10µF 6.3V X5R | 0603 | 3 | MCU core decoupling |
| C_MCU_1V8 | 10µF 6.3V X5R | 0603 | 2 | Core/voltage domain decoupling |

## 2. Power Stage — MOSFETs

| RefDes | Part | Package | Qty | Notes |
|---|---|---|---|---|
| Q1–Q6 | STK8H122D (1200V, 122A) | TO-247-3 | 6 | Primary MOSFET per leg |
| Q1a–Q6a | STK8H122D | TO-247-3 | 6 | Parallel per switch for current sharing at 250V nominal |
| Q1b–Q6b | STK8H122D | TO-247-3 | 6 | Third parallel per switch (3 total per position) |
| Rg1–Rg18 | 10Ω / 0.5W | 1206 | 18 | Gate resistor per MOSFET (3 per switch) |
| R1–R18 | 100kΩ / 0.25W | 1206 | 18 | Pull-down per MOSFET gate (3 per switch) |

**Rationale:** STK8H122D provides 1200V rating (well above 650V requirement) and 122A continuous. For 140A peak at 250V nominal, 3 parallel MOSFETs per switch position (18 total) provides current sharing (47A per device at peak, well within 122A rating). Thermal design must ensure junction temp ≤150°C at peak.

## 3. Gate Drivers

| RefDes | Part | Package | Qty | Notes |
|---|---|---|---|---|
| U2–U4 | TI ISO7762QRQ1 (dual) | SOIC-8 | 3 | Dual isolated digital isolator ×2 channels |
| U5–U7 | TI DRV8301 (or similar) | HTSSOP-28 | 3 | Integrated 3-phase gate driver |

**Alternative:** Use TI ISO6731-Q1 (triple isolated gate driver) per phase — reduces component count.

## 4. Current Sensing

| RefDes | Part | Package | Qty | Notes |
|---|---|---|---|---|
| R_SHUNT | 100µΩ, 5W–10W, 4-wire | Custom shunt | 1 | Bus-level shunt resistor (140A peak = 1.96W peak, 60A continuous = 0.36W) |
| U8 | TI AMC1301MOM | SOIC-16 | 1 | Isolated amplifier, ±2.5V out, 2kV isolation |
| R_CS1–R_CS2 | 10kΩ / 0.125W | 0603 | 2 | AMC1301 gain resistors |

## 5. Bus Voltage Sensing

| RefDes | Part | Package | Qty | Notes |
|---|---|---|---|---|
| R_DIV1 | 1MΩ / 1W | 1206 | 1 | High-side divider top |
| R_DIV2 | 1kΩ / 0.125W | 0603 | 1 | Low-side divider bottom |
| U9 | TLV9062IPWR | SOT-23-5 | 1 | Buffer op-amp (single channel) |
| C_DIV | 1nF | 0603 | 1 | Divider low-pass filter |

## 6. Isolation & Communication

| RefDes | Part | Package | Qty | Notes |
|---|---|---|---|---|
| U10 | TI ISO1042 | SOIC-8 | 1 | Isolated CAN transceiver, ±5kV |
| J_CAN | DB9 or XH2.54-4P | 1 | CAN connector |
| U11 | 74LVC1G125 | SOT-23-5 | 2 | Level shifters for UART |
| J_UART | XH2.54-4P | 1 | UART debug connector |

## 7. Power Supply

| RefDes | Part | Package | Qty | Notes |
|---|---|---|---|---|
| U12 | LM7805 or similar | TO-220 | 1 | 48V→5V pre-regulator (for gate driver supply) |
| U13 | TPS7A4733 | SOT-23-5 | 1 | 5V→3.3V LDO, 100mA, low-noise |
| C_PS1 | 100µF 63V | Radial | 2 | Input bulk capacitance |
| C_PS2 | 100nF 50V X7R | 1206 | 4 | Decoupling |

**Rationale:** TPS7A4733 LDO provides low-noise 3.3V for MCU. Dissipation ≈1W — requires thermal pad or small heatsink.

## 8. Protection & Passive

| RefDes | Part | Package | Qty | Notes |
|---|---|---|---|---|
| TVS1 | SMAJ45CA or similar | SMA | 1 | Bus overvoltage protection |
| F1 | 100A fuse or PTC | — | 1 | Input overcurrent protection |
| NTC1–NTC3 | 100kΩ NTC | SMD | 3 | MOSFET heatsink temperature monitoring |
| C_BYPASS | 100nF 100V X7R | 1206 | 3 | Snubber capacitors per phase |

## 9. Connectors

| RefDes | Part | Package | Qty | Notes |
|---|---|---|---|---|
| J_PWR | XT90-60 or similar | — | 1 | Main power input (48–450V) |
| J_MOTOR | XT90-120 or similar | — | 3 | Motor phase outputs (U, V, W) |
| J_USB | Micro-USB or USB-C | — | 1 | Programming/debug |
| J_PROG | SWD 2×5 | — | 1 | ST-LINK programming |

---

*Note: This BOM is preliminary. Final part numbers and quantities will be refined during schematic capture and layout.*
