# MCU-C — Design Decisions

## D001: Selected STM32F405RGT6 as primary MCU
- **Why:** Official VESC reference MCU with mature firmware support, 168MHz Cortex-M4 with FPU, CAN FD, and sufficient ADC/timer resources for FOC at 15kW.
- **Affects:** U1 (MCU), all PWM/ADC/CAN pin assignments, firmware target

## D002: Power stage uses STK8H122D (1200V, 122A) MOSFETs with parallel devices
- **Why:** 1200V rating provides sufficient derating for 450V max bus; 6 parallel MOSFETs per switch position (36 total) needed for 729A peak current at 48V.
- **Affects:** Q1–Q6, Q1a–Q6a, thermal design

## D003: Current sensing uses shunt resistor + AMC1301 isolated amplifier
- **Why:** VESC standard architecture; AMC1301 provides 2kV isolation, ±2.5V output, 100kHz bandwidth sufficient for FOC at 20–100kHz PWM.
- **Affects:** R_SHUNT, U8, current sense circuit

## D004: Gate drivers use TI ISO7762QRQ1 isolated digital isolators + external gate driver stage
- **Why:** Provides 5kV isolation between MCU and power stage; external gate driver stage handles high-current switching of MOSFET gates.
- **Affects:** U2–U4, gate drive circuit

## D005: Bus voltage sensing uses 1MΩ/1kΩ resistor divider + TLV9062 buffer op-amp
- **Why:** 1000:1 divider reduces 450V max to 0.45V; rail-to-rail op-amp buffers to 0–3.3V range for MCU ADC1_IN3.
- **Affects:** R_DIV1, R_DIV2, U9, bus voltage sense circuit

---
