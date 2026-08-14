# MCU-C pin map — STM32F405VGT6 (U1, LQFP100)

Fixed per DECISIONS.md **D023** ("MCU pin map fixed"). Assignments follow the
VESC `hw_100_250` conventions adapted to this board's isolated architecture;
every row was verified pin-by-pin against ST **DS8626 Rev 8** (STM32F405xx/407xx
datasheet, DocID022152): LQFP100 pin numbers and additional (ADC) functions from
**Table 7**, alternate functions from **Table 9** (AF mapping).

**This table was generated against the exported netlist after wiring** —
each net below was machine-checked in `mcuc_inverter` (kicad-cli netlist
export) to contain `U1` at exactly the stated LQFP100 pad *and* the counterpart
pin on the stated sheet. ERC: 0 errors.

5 V tol. column is the DS8626 Table 7 *I/O structure*: **FT** = 5 V tolerant,
**TTa** = 3.3 V only (ADC-capable). Per DS8626 note 4, FT pins are *not* 5 V
tolerant while configured in analog mode — all rows marked "(analog)" below
run at ADC levels regardless.

## Analog inputs

| Signal | Port pin | LQFP100 # | Function (ADC ch / AF) | 5 V tol. | Connected sheet | Source |
|---|---|---|---|---|---|---|
| I_PH_1 | PC0 | 15 | ADC123_IN10 (analog) — VESC CURR1 | FT (4) | Phase current sensing (HOYS U504) | DS8626 T7 p.48; D019/D023 |
| I_PH_2 | PC1 | 16 | ADC123_IN11 (analog) — VESC CURR2 | FT (4) | Phase current sensing (HOYS U505) | DS8626 T7 p.48; D019/D023 |
| I_PH_3 | PC2 | 17 | ADC123_IN12 (analog) — VESC CURR3 | FT (4) | Phase current sensing (HOYS U506) | DS8626 T7 p.48; D019/D023 |
| I_REF_1 | PA4 | 29 | ADC12_IN4 (analog) | TTa | Phase current sensing (U501 Vref) | DS8626 T7 p.50 |
| I_REF_2 | PA7 | 32 | ADC12_IN7 (analog) | FT (4) | Phase current sensing (U502 Vref) | DS8626 T7 p.50 |
| I_REF_3 | PB1 | 36 | ADC12_IN9 (analog) | FT (4) | Phase current sensing (U503 Vref) | DS8626 T7 p.50 |
| V_BUS | PC3 | 18 | ADC123_IN13 (analog) — VESC ADC_IND_VIN_SENS | FT (4) | Bus voltage sensing (U703 output) | DS8626 T7 p.49; D023 |
| TEMP_COLDPLATE | PA3 | 26 | ADC123_IN3 (analog) | FT (4) | Temperature sensing | DS8626 T7 p.49 |
| TEMP_BOARD | PB0 | 35 | ADC12_IN8 (analog) | FT (4) | Temperature sensing | DS8626 T7 p.50 |
| MOTOR_TEMP | PC4 | 33 | ADC12_IN14 (analog) — VESC TEMP_MOTOR | FT (4) | Position feedback (front end) + J1205 | DS8626 T7 p.50; D023 |
| SINCOS_SIN | PA5 | 30 | ADC12_IN5 (analog) — VESC ADC_IND_EXT | TTa | Position feedback (SinCos front end) | DS8626 T7 p.50; D023 |
| SINCOS_COS | PA6 | 31 | ADC12_IN6 (analog) — VESC ADC_IND_EXT2 | FT (4) | Position feedback (SinCos front end) | DS8626 T7 p.50; D023 |
| USB_VBUS_SENSE | PC5 | 34 | ADC12_IN15 (analog) | FT (4) | Communications (USB-C VBUS divider) | DS8626 T7 p.50 |

## Digital I/O

| Signal | Port pin | LQFP100 # | Function / AF | 5 V tol. | Connected sheet | Source |
|---|---|---|---|---|---|---|
| ENC_A | PC6 | 63 | TIM3_CH1 (AF2) encoder mode | FT | Position feedback (ABI conditioning) | DS8626 T7 p.54, T9; D023 |
| ENC_B | PC7 | 64 | TIM3_CH2 (AF2) encoder mode | FT | Position feedback (ABI conditioning) | DS8626 T7 p.54, T9; D023 |
| ENC_I | PC8 | 65 | TIM3_CH3 (AF2) / EXTI index | FT | Position feedback (ABI conditioning) | DS8626 T7 p.54, T9; D023 |
| HALL_1 | PD12 | 59 | TIM4_CH1 (AF2) / GPIO hall input | FT | Position feedback (hall filters) | DS8626 T7 p.53, T9; D023 |
| HALL_2 | PD13 | 60 | TIM4_CH2 (AF2) / GPIO hall input | FT | Position feedback (hall filters) | DS8626 T7 p.54, T9; D023 |
| HALL_3 | PD14 | 61 | TIM4_CH3 (AF2) / GPIO hall input | FT | Position feedback (hall filters) | DS8626 T7 p.54, T9; D023 |
| RES_SPI_SCK | PC10 | 78 | SPI3_SCK (AF6) → AD2S1205 SCLK | FT | Position feedback (U801.8) | DS8626 T7 p.56, T9; D023 |
| RES_SPI_MISO | PC11 | 79 | SPI3_MISO (AF6) ← AD2S1205 SO (5 V out) | FT | Position feedback (U801.7) | DS8626 T7 p.56, T9; D023 |
| RES_SPI_NCS | PA15 | 77 | SPI3_NSS / GPIO #CS (AF6); boot pull-up to +5 V on sheet | FT | Position feedback (U801.3 + R803) | DS8626 T7 p.56, T9; D023 |
| RES_SPI_NSAMPLE | PD0 | 81 | GPIO out → AD2S1205 #SAMPLE | FT | Position feedback (U801.4 + R804) | DS8626 T7 p.56 |
| RES_SPI_NRDVEL | PD1 | 82 | GPIO out → AD2S1205 RDVEL | FT | Position feedback (U801.5 + R805) | DS8626 T7 p.56 |
| RES_NFAULT | PD2 | 83 | GPIO in ← resolver fault AND (U804) | FT | Position feedback | DS8626 T7 p.56 |
| OC_LATCHED | PD3 | 84 | GPIO in ← latched overcurrent flip-flop | FT | Supervisor and interlocks (U904.5) | DS8626 T7 p.56 |
| FAULT_RESET | PD4 | 85 | GPIO out → fault latch reset | FT | Supervisor and interlocks (U904.6) | DS8626 T7 p.57 |
| DRV_RST_IN | PD5 | 86 | GPIO out → gate-drive reset request | FT | Supervisor and interlocks (U903.9) | DS8626 T7 p.57 |
| PRECHARGE_EN | PE2 | 1 | GPIO out (boot: input w/ no pull → off, R402 pulldown) | FT | Precharge and contactor (R402) | DS8626 T7 p.47 |
| CONTACTOR_EN | PE3 | 2 | GPIO out (boot-safe, R404 pulldown) | FT | Precharge and contactor (R404) | DS8626 T7 p.47 |
| DISCHARGE_EN | PE4 | 3 | GPIO out (boot-safe, R427 pulldown) | FT | Precharge and contactor (R427) | DS8626 T7 p.47 |
| LED_FAULT | PE0 | 97 | GPIO out → fault LED | FT | Communications (D1203) | DS8626 T7 p.58 |
| PPM | PB6 | 92 | TIM4_CH1 (AF2) input capture — VESC servo/PPM convention | FT | Communications (J1206 pin 7) | DS8626 T7 p.58, T9; D023 |

## Fixed core set (wired in the initial MCU sheet capture)

| Signal | Port pin | LQFP100 # | Function / AF | 5 V tol. | Connected sheet | Source |
|---|---|---|---|---|---|---|
| PWM_HS_1 | PA8 | 67 | TIM1_CH1 (AF1) | FT | Supervisor (PWM gating) | DS8626 T7 p.55, T9 |
| PWM_HS_2 | PA9 | 68 | TIM1_CH2 (AF1) | FT | Supervisor (PWM gating) | DS8626 T7 p.55, T9 |
| PWM_HS_3 | PA10 | 69 | TIM1_CH3 (AF1) | FT | Supervisor (PWM gating) | DS8626 T7 p.55, T9 |
| PWM_LS_1 | PB13 | 52 | TIM1_CH1N (AF1) | FT | Supervisor (PWM gating) | DS8626 T7 p.53, T9 |
| PWM_LS_2 | PB14 | 53 | TIM1_CH2N (AF1) | FT | Supervisor (PWM gating) | DS8626 T7 p.53, T9 |
| PWM_LS_3 | PB15 | 54 | TIM1_CH3N (AF1) | FT | Supervisor (PWM gating) | DS8626 T7 p.53, T9 |
| FAULT_BKIN | PB12 | 51 | TIM1_BKIN (AF1) hardware PWM kill | FT | Supervisor and interlocks | DS8626 T7 p.53, T9 |
| CAN1_RX | PB8 | 95 | CAN1_RX (AF9) | FT | Communications (ISO1042) | DS8626 T7 p.58, T9 |
| CAN1_TX | PB9 | 96 | CAN1_TX (AF9) | FT | Communications (ISO1042) | DS8626 T7 p.58, T9 |
| USB_DM | PA11 | 70 | OTG_FS_DM (AF10) | FT | Communications (USB-C) | DS8626 T7 p.55, T9 |
| USB_DP | PA12 | 71 | OTG_FS_DP (AF10) | FT | Communications (USB-C) | DS8626 T7 p.55, T9 |
| SWDIO | PA13 | 72 | JTMS/SWDIO | FT | Communications (SWD J1208) | DS8626 T7 p.55 |
| SWCLK | PA14 | 76 | JTCK/SWCLK | FT | Communications (SWD J1208) | DS8626 T7 p.56 |
| NRST | NRST | 14 | Reset (100 nF C12; SWD + comms sheet) | RST | Communications / MCU sheet | DS8626 T7 p.48 |
| BOOT0 | BOOT0 | 94 | Boot select, 10 k pulldown R1 | B | MCU sheet (local) | DS8626 T7 p.58 |
| HSE in | PH0 | 12 | OSC_IN — 8 MHz crystal Y1 | FT (osc) | MCU sheet (local) | DS8626 T7 p.48 |
| HSE out | PH1 | 13 | OSC_OUT | FT (osc) | MCU sheet (local) | DS8626 T7 p.48 |
| VCAP_1 / VCAP_2 | — | 49 / 73 | Core regulator caps, 2.2 uF each | — | MCU sheet (local) | DS8626 T7 |
| VDD ×6 + VBAT | — | 11,19,28,50,75,100 / 6 | +3.3 V rail, 100 nF each + 4.7 uF | — | MCU sheet (local) | DS8626 T7 |
| VDDA / VREF+ | — | 22 / 21 | 3V3A via ferrite bead + 1 uF/100 nF | — | MCU sheet (local) | DS8626 T7 |
| VSS ×4 + VSSA | — | 10,27,74,99 / 20 | GND | — | MCU sheet (local) | DS8626 T7 |

## Reserved pins (labelled on the MCU sheet, not wired)

| Port pin | LQFP100 # | Reserved for | Why | Source |
|---|---|---|---|---|
| PA0 | 23 | SENS1 (ADC123_IN0) | VESC phase-voltage input — not fitted in rev A; isolated control domain makes direct dividers impossible. Kept free so a future isolated phase-sense option lands on the exact VESC channels. | DS8626 T7 p.49; **D023** |
| PA1 | 24 | SENS2 (ADC123_IN1) | as above | DS8626 T7 p.49; **D023** |
| PA2 | 25 | SENS3 (ADC123_IN2) | as above | DS8626 T7 p.49; **D023** |
| PB10 | 47 | USART3_TX (AF7) / I2C2_SCL (AF4) | spare comms expansion | DS8626 T7 p.52, T9; D023 |
| PB11 | 48 | USART3_RX (AF7) / I2C2_SDA (AF4) | spare comms expansion | DS8626 T7 p.52, T9; D023 |

## Notes

- **D023**: no phase-voltage sensing in rev A — the custom `hw_mcuc.h` header
  disables VESC phase-filter/BEMF features that need SENS1/2/3. ADC vector
  mirrors `hw_100_250` minus SENS.
- **AD2S1205 3.3 V drive check**: the resolver IC runs at 5 V but its logic
  inputs specify VIH min = 2.0 V (DS "Electrical Characteristics"), so 3.3 V
  MCU drive on RES_SPI_SCK/NCS/NSAMPLE/NRDVEL is valid. Its outputs are 5 V
  (VOH min 4.0 V) — RES_SPI_MISO and RES_NFAULT land on FT (5 V-tolerant)
  pins PC11/PD2, and RES_NFAULT additionally passes through the 3.3 V
  5 V-tolerant SN74LVC1G11 AND gate on the position sheet. Noted on the
  position sheet next to U801.
- **PPM connector**: J1206 (Encoder / SinCos, 8-pos) pin 7 was the spare
  position (tied to GND alongside pin 8); it now carries PPM. GND stays on
  pin 8.
- PA4 (I_REF_1) and PA5 (SINCOS_SIN) are **TTa** — never expose them to 5 V.
  Both nets are 3.3 V-domain analog outputs of on-board dividers/references.
