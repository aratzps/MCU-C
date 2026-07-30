# MCU-C Controller — System Specification

## 1. Overview

High-power VESC-compatible motor controller for 3-phase BLDC/PMSM motors.
Ultra-wide input voltage range (48–450V) with 15kW continuous and 35kW peak power delivery.

## 2. Electrical Requirements

### 2.1 Input / Power

| Parameter | Min | Nom | Max | Unit | Notes |
|---|---|---|---|---|---|
| Bus voltage range | 48 | — | 450 | V | Ultra-wide; derate MOSFETs to ≥650V |
| Continuous power | 15 | — | — | kW | At any voltage in range |
| Peak power | — | — | 35 | kW | 10s duty, thermal limited |
| Max continuous current @48V | — | 312 | — | A | 15kW / 48V |
| Max peak current @48V | — | 729 | — | A | 35kW / 48V |
| Max continuous current @450V | — | 33.3 | — | A | 15kW / 450V |
| Max peak current @450V | — | 77.8 | — | A | 35kW / 450V |
| Input protection | — | — | — | — | Reverse polarity, OVP, undervoltage lockout |

### 2.2 Motor Output

| Parameter | Value | Unit |
|---|---|---|
| Phases | 3 | — |
| PWM frequency | 20–100 | kHz | Configurable |
| Current sensing | Shunt-based, isolated | — | Per VESC architecture |
| Rotor position | Hall sensors (optional) + encoder (optional) | — | VESC-compatible |

## 3. MCU Requirements

| Parameter | Requirement |
|---|---|
| MCU family | STM32 (VESC firmware compatible) |
| MCU part | **STM32F405RGT6** (LQFP100) — primary reference |
| Core | ARM Cortex-M4, 168MHz, FPU |
| Flash | ≥512 KB (1 MB on F405) |
| SRAM | ≥128 KB (192 KB on F405) |
| ADC | 3× 12-bit, ≥1 MSPS (for 3-phase current sensing + bus voltage) |
| Timers | ≥6 PWM outputs (3-phase FOC + dead time) |
| CAN | CAN FD (2× CAN, CAN2 supports FD) |
| UART | ≥2 (debug, external comms) |
| VESC firmware support | Officially supported in VESC Tool / VESC firmware |

**Rationale:** STM32F405RGT6 is the official VESC reference MCU. It has the most mature firmware support, sufficient ADC performance for shunt-based sensing, CAN FD for VESC protocol, and proven thermal profile in LQFP100.

## 4. Power Stage Architecture

### 4.1 MOSFET Selection

| Parameter | Requirement |
|---|---|
| VDS rating | ≥650 V (derated from 450V max bus) |
| RDS(on) | As low as possible (milliohm class) |
| Package | TO-247 or similar for thermal dissipation |
| Configuration | 6× MOSFETs (3-phase bridge); parallel per switch as needed for current sharing |

**Candidate:** STK8H122D (1200V, 122A, TO-247-3) or equivalent SiC MOSFETs (e.g., ROHM B3M120000J) for high-voltage efficiency.

**Parallel MOSFETs at 48V:** At 729A peak, individual MOSFETs must be paralleled (minimum 4–6 per switch position depending on thermal design and RDS(on) matching).

### 4.2 Gate Drivers

| Parameter | Requirement |
|---|---|
| Type | Isolated, high-side + low-side per phase |
| Isolation voltage | ≥1500 Vrms |
| Peak current drive | ≥2A per channel |
| Dead time | Programmable or external |
| Candidate | TI ISO7721 (dual isolated digital isolator) + external gate driver stage, or integrated isolated gate driver (e.g., TI ISO6731-Q1) |

## 5. Current Sensing

| Parameter | Requirement |
|---|---|
| Type | Shunt-based with isolated amplifier (VESC standard) |
| Range | ±800 A (to cover 729A peak with margin) |
| Isolation | ≥1500 Vrms |
| Bandwidth | ≥100 kHz |
| Candidate | TI AMC1301MOM (100kHz, ±2.5V output, 2kV isolation) or Allegro ACS780 (Hall-effect, ±500A, non-isolated — use AMC1301 for isolation) |

**Note:** Shunt resistor must handle 729A peak. Power dissipation at peak: P = I²R. For R = 100µΩ: P = 729² × 0.0001 = 53W peak (pulsed). Continuous at 312A: 9.7W. Requires water cooling or large thermal mass.

## 6. Bus Voltage Sensing

| Parameter | Requirement |
|---|---|
| Range | 0–450 V |
| Method | High-voltage resistor divider + buffered differential amplifier |
| Divider ratio | e.g., 1000:1 → 0.45V max at ADC input |
| ADC input | 0–3.3V range (MCU ADC) |
| Candidate | TI TLV9062 (rail-to-rail op-amp) or similar |

## 7. Isolation Requirements

| Interface | Isolation | Voltage Rating |
|---|---|---|
| MCU ↔ Power stage | Isolated gate drivers, isolated current sense | ≥1500 Vrms |
| CAN bus | Isolated CAN transceiver | ≥2500 Vrms |
| UART/debug | Opto-isolated or magnetic isolation | ≥1000 Vrms |
| MCU ground plane | Split or isolated from power ground | — |

## 8. Thermal Budget

| Parameter | Target |
|---|---|
| System efficiency @15kW | ≥97% |
| Max power dissipation | ≤450 W |
| MOSFET junction temp @peak | ≤150°C |
| Heat sinking | Forced air or liquid cooling required |

**Rationale:** 97% efficiency at 15kW output = 450W loss. This requires active thermal management (forced air or liquid).

## 9. VESC Compatibility

| Interface | Specification |
|---|---|
| MCU firmware | VESC firmware (STM32F405RGT6 target) |
| Host protocol | VESC protocol over CAN FD or UART |
| Configuration | VESC Tool compatible .conf files |
| Motor parameters | Standard VESC motor parameter set |
| FOC algorithm | VESC FOC implementation |

## 10. Safety Requirements

| Item | Requirement |
|---|---|
| Undervoltage lockout | MCU brownout + power stage UVLO |
| Overvoltage protection | Bus OVP at ~520V (TVS/clamp) |
| Overcurrent protection | Hardware comparator trip + firmware monitoring |
| Overtemperature | NTC on MOSFETs + heatsink, firmware monitoring |
| Gate driver fault | Auto-shutdown on overtemp/overcurrent |
| ESD protection | On all I/O pins |

## 11. Power Budget (MCU Side)

| Block | Current (mA) | Notes |
|---|---|---|
| STM32F405 @168MHz | ~120 | Typical, all peripherals on |
| Gate driver ICs (×6) | ~180 | Quiescent, not switching |
| Current sense amps (×1) | ~10 | AMC1301 |
| CAN transceiver | ~20 | Isolated type |
| Voltage dividers | ~2 | Negligible |
| **Total MCU side** | **~332** | From 3.3V LDO |
| **LDO dissipation** | **~1W** | (3.3V × 0.33A) |

## 12. Pin Strapping Constraints

| Pin | Function | Strapping Requirement |
|---|---|---|
| BOOT0 | Must be pulled LOW for normal boot | BOOT0 → GND |
| NRST | External pull-up (10k to 3.3V) | Active-low reset |
| VBAT | Battery backup (RTC) | 1.8–3.6V, optional |
| PC0/PC1 (OSC32_IN/OUT) | 32.768kHz crystal | For RTC / low-power clock |
| PH0/PH1 (OSC_IN/OUT) | 8MHz HSE crystal | System clock source |

## 13. Antenna Keepout

| Zone | Requirement |
|---|---|
| RF antenna area | No ground pours, no copper, no traces within 10mm of antenna |
| CAN trace length | <15cm, terminated at 120Ω |
| PWM traces | Shortest possible, differential pairs for gate drive |

---

*Document version: 1.0*
*Last updated: initial design*
