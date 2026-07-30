# Supervisor and Hardware Interlocks — Design

**Block:** `mcuc_inverter/supervisor.kicad_sch`
**Requirement:** `SPEC.md` §9.2
**Status:** Logic design settled. Component placement and wiring not yet done.

---

## 1. Purpose

Prevent the bridge from being destroyed by conditions firmware cannot be trusted to catch in time — or at all. Every function here works with the MCU halted, mis-flashed, or executing a bad configuration.

This block is carried over in intent from `pcb_design/supervisor.sch` on the original PALTA board, which implemented the same three functions: *PWM overlap elimination*, *overcurrent latch*, and *fault/reset aggregation*.

**Design rule for this block:** no signal path may depend on firmware for correctness. Firmware may *observe* and may *reset* a latched fault, but may never *suppress* one.

---

## 2. Interface

### 2.1 Inputs

| Signal | From | Type | Purpose |
|---|---|---|---|
| `PWM_AH` `PWM_AL` | MCU TIM1_CH1/CH1N | Digital | Phase A high/low PWM |
| `PWM_BH` `PWM_BL` | MCU TIM1_CH2/CH2N | Digital | Phase B high/low PWM |
| `PWM_CH` `PWM_CL` | MCU TIM1_CH3/CH3N | Digital | Phase C high/low PWM |
| `ISENSE_A/B/C` | Current sense (§8.1) | Analog | Phase current, 1.65 V = 0 A |
| `GATE_FAULT_N` | Gate drivers (§5) | Digital, active low | Aggregated desat / driver fault |
| `OVP_N` | Bus sense (§8.2) | Digital, active low | Bus overvoltage, 490 V |
| `UVLO_N` | Bus sense (§8.2) | Digital, active low | Bus undervoltage, 45 V |
| `OTP_N` | Temperature (§8.3) | Digital, active low | Overtemperature |
| `FAULT_RESET_N` | MCU GPIO | Digital, active low | Explicit latch clear |
| `MCU_ENABLE` | MCU GPIO | Digital | Master enable |

### 2.2 Outputs

| Signal | To | Type | Purpose |
|---|---|---|---|
| `GD_AH` `GD_AL` | Gate drive (§5) | Digital | Gated phase A |
| `GD_BH` `GD_BL` | Gate drive (§5) | Digital | Gated phase B |
| `GD_CH` `GD_CL` | Gate drive (§5) | Digital | Gated phase C |
| `BKIN_N` | MCU PB12 / TIM1_BKIN | Digital, active low | Hardware PWM shutdown |
| `OCP_LATCHED` | MCU GPIO | Digital | Latched overcurrent status |
| `FAULT_N` | MCU GPIO | Digital, active low | Aggregated fault status |

### 2.3 Supply rails

| Rail | Used by | Reason |
|---|---|---|
| +5 V | LM2903 comparators | See §3.2 — input common-mode range |
| +3.3 V | Logic gates, flip-flop, pull-ups | MCU-compatible levels |
| GND | All | |

---

## 3. Block A — Overcurrent detect and latch

### 3.1 Threshold

From `SPEC.md` §3.3: sense full scale ±300 A, hardware trip at 280 A.

Current sense presents 1.65 V at 0 A with ±1.5 V full-scale swing, so:

```
V(+280 A) = 1.65 + (280/300 × 1.5) = 1.65 + 1.40 = 3.05 V
V(-280 A) = 1.65 - 1.40                            = 0.25 V
```

Six comparator channels — both polarities on three phases. Motoring and regeneration both need catching, so a single-polarity trip is not sufficient.

### 3.2 Why the comparators run from +5 V

**This is the detail that makes or breaks the block.** The LM2903's input common-mode range extends from ground to `VCC − 1.5 V`. On a 3.3 V rail that ceiling is **1.8 V** — well below the 3.05 V positive trip point, so the positive-overcurrent comparator would simply never assert.

Running the comparators from +5 V raises the ceiling to 3.5 V, which accommodates 3.05 V with margin. The LM2903 has an **open-drain output**, so its pull-up goes to +3.3 V and the logic downstream still sees clean 3.3 V levels. No level shifter is needed.

### 3.3 Wired-OR trip

All six open-drain outputs tie to a single `OC_TRIP_N` node with one pull-up to +3.3 V. Any comparator pulling low asserts the trip. This is free OR-ing and costs one resistor.

| Item | Value | Note |
|---|---|---|
| Pull-up | 4.7 kΩ to +3.3 V | Matches original board's 4.7 k family |
| Filter | 100 pF to GND | Suppresses switching-noise glitches |

The filter is deliberately small. At 4.7 kΩ it gives ~470 ns of rejection — enough for switching spikes, far below the microseconds that matter for device survival.

### 3.4 Latch

A single `74AUP1G74` D flip-flop, wired as a set-dominant latch:

| Pin | Connection | Reason |
|---|---|---|
| `D` | +3.3 V | Always latch a one |
| `CLK` | `OC_TRIP` (inverted `OC_TRIP_N`) | Rising edge on trip |
| `CLR_N` | `FAULT_RESET_N` | Explicit clear only |
| `PRE_N` | +3.3 V | Unused |
| `Q` | `OCP_LATCHED` | |

**The latch cannot be cleared by the condition going away.** It requires an explicit `FAULT_RESET_N` pulse from firmware. A momentary overcurrent therefore stops the bridge until a human or the control loop deliberately acknowledges it — the behaviour that makes an overcurrent latch worth having.

`CLR_N` also has an RC power-on reset so the latch comes up in a known cleared state rather than a random one.

---

## 4. Block B — Fault aggregation

```
FAULT_N = /OCP_LATCHED · GATE_FAULT_N · OVP_N · UVLO_N · OTP_N
```

`FAULT_N` is low when *any* source is faulted. It drives two things:

1. **`BKIN_N` → MCU pin PB12 (TIM1_BKIN).** The STM32 timer's break input tri-states all six PWM outputs **in silicon**, with no code executing. This is the single most important connection in the block: an MCU lockup, a firmware bug, or a bad timer configuration cannot leave the bridge conducting.
2. **`ENABLE_INT`** — the internal enable feeding Block C, combined with `MCU_ENABLE`:

```
ENABLE_INT = FAULT_N · MCU_ENABLE
```

Note the redundancy is intentional. `BKIN_N` stops PWM at the source; Block C stops it again downstream. Either alone is sufficient; both together mean no single gate failure defeats the shutdown.

---

## 5. Block C — PWM overlap elimination and dead time

### 5.1 Mutual exclusion

Per phase, with mutual exclusion enforced combinationally:

```
GD_AH = PWM_AH_delayed · ENABLE_INT · /PWM_AL
GD_AL = PWM_AL_delayed · ENABLE_INT · /PWM_AH
```

If firmware ever commands both high — a timer misconfiguration, a corrupted register, a bad dead-time value — **each output gates the other off**. Both go low. The bridge coasts rather than shooting through. This holds regardless of what the MCU is doing.

### 5.2 Hardware dead time

Mutual exclusion alone stops a *static* overlap but not the *transition* case, where one switch has not finished turning off as the other starts. That needs a delay on the turn-on edge only.

Classic asymmetric RC with a Schottky bypass, as on the original board:

- **Turn-on** (rising): charges through `R_dt` → delayed
- **Turn-off** (falling): discharges through the Schottky → fast, undelayed

With CMOS input thresholds at `0.5 × VCC`:

```
t_dead = R · C · ln(2) = 0.693 · R · C

R = 1.5 kΩ, C = 470 pF  →  t_dead = 0.693 × 1500 × 470e-12 = 489 ns
```

**Target: ~490 ns hardware floor.** This sits deliberately *below* the firmware dead time (the original board used 1.4 µs, set by `HW_DEAD_TIME_VALUE`), so in normal operation the hardware network does nothing at all. It only asserts if firmware commands a dead time shorter than the hardware minimum — which is precisely the failure this exists to catch.

Final value must be confirmed against the chosen power module's turn-off time once §14 item 2 is resolved. **[TBV]**

### 5.3 Logic family

**74HC** rather than the original's 74ACT.

The dead-time calculation above assumes a CMOS threshold at `0.5 × VCC`. 74ACT has *TTL* thresholds (~1.5 V on a 5 V rail), which makes the RC delay supply- and part-dependent — the delay becomes `RC · ln(VCC/(VCC−Vth))`, a different number that drifts with rail tolerance. Predictable dead time is worth more here than the ~10 ns of propagation delay 74AC would save.

At 100 kHz PWM, a 74HC gate's ~20 ns propagation delay is 4 % of the 490 ns dead time. Acceptable. If timing margin later proves tight, **74AC** (CMOS thresholds, faster) is the drop-in upgrade — **not** 74ACT.

---

## 6. Gate and part budget

| Ref | Part | Units | Used for |
|---|---|---|---|
| U1–U3 | LM2903 | 2 comparators each | 6 channels, ±280 A × 3 phases |
| U4 | 74AUP1G74 | 1 D flip-flop | OCP latch |
| U5 | 74HC00 | 4 NAND | `OC_TRIP` inversion, `/PWM_xL` and `/PWM_xH` inversion |
| U6 | 74HC08 | 4 AND | `ENABLE_INT`, fault aggregation |
| U7–U8 | 74HC08 | 4 AND each | 6 PWM gating outputs, 2 spare |

Eleven ICs. The original used a comparable count (10 AND units, 5 NAND units, 1 flip-flop) for the same three functions, which is a useful sanity check that the design has not quietly grown.

| Passive | Value | Qty | Purpose |
|---|---|---|---|
| Dead-time R | 1.5 kΩ | 6 | §5.2 |
| Dead-time C | 470 pF | 6 | §5.2 |
| Schottky | BAT54S (dual) | 3 | §5.2, one per phase |
| Pull-up | 4.7 kΩ | 8 | `OC_TRIP_N`, fault lines |
| Trip divider | TBV | 4 | 3.05 V and 0.25 V references |
| Decoupling | 100 nF | 11 | One per IC |
| POR | 10 kΩ + 100 nF | 1 | Latch `CLR_N` |
| Status LED | — | 2 | `OCP`, `FAULT` — carried from original |

---

## 7. Failure-mode review

What happens for each single fault, given firmware is assumed hostile:

| Failure | Result |
|---|---|
| MCU halts with PWM high | `BKIN_N` unaffected; but PWM is static, so Block C mutual exclusion holds only if not both high. **Watchdog required** — see §8 |
| Firmware commands H and L both high | Block C forces both low. Bridge coasts |
| Firmware sets dead time to zero | Hardware RC enforces 490 ns floor |
| Firmware ignores an overcurrent | Latch already dropped `BKIN_N`; silicon tri-states PWM |
| Firmware spams `FAULT_RESET_N` | Latch re-asserts immediately while the condition persists. Cannot be held clear |
| One AND gate fails high | `BKIN_N` path still stops PWM at the MCU. Redundancy per §4 |
| Comparator supply lost | Open-drain output floats; **pull-up makes it read as no-fault** — see §8 |
| 3.3 V lost | All logic low, gate drivers see no drive, bridge off |

## 8. Open items

| # | Item | Why it matters |
|---|---|---|
| 1 | **Watchdog is not yet in this block.** A halted MCU holding a valid static PWM pattern is not caught by anything above | A stuck duty cycle can still overheat a stalled motor |
| 2 | **Comparator supply-loss detection.** Losing +5 V makes the overcurrent trip silently read as healthy | Fail-safe requires the comparators' own supply be monitored |
| 3 | Trip divider values and tolerance, once the current-sense chain's actual scaling is fixed | §3.1 assumes 1.65 V ± 1.5 V |
| 4 | Dead-time value against the real module turn-off time | §5.2 |

Items 1 and 2 are genuine gaps in the original PALTA design as well. They should be closed before this block is considered finished.

---

## 9. Implementation state

The logic above is settled. **The KiCad sheet is still an empty placeholder** — no components, no interface pins.

The interface in §2 is encoded in `tools/gen_skeleton.py` (`IFACE`), together with the counterpart pins on the MCU, gate drive, current sense, bus sense and temperature sheets. It is held back from the schematic by the `EMIT_INTERFACE` flag.

The reason is worth recording. Emitting the interface into empty sheets was tried and produces 96 dangling-label violations — 48 sheet-boundary labels at root and 48 hierarchical labels inside sheets that contain nothing to connect to. Those are *correct* reports: an interface with no implementation behind it genuinely is unconnected. But `copperhead check` fails on warnings as well as errors, so the verification gate would sit permanently red, and a gate that is always red gets ignored — the same failure that let the earlier generated documents through unchecked.

So the interface lands in the same change as the components. Flip `EMIT_INTERFACE = True`, run `python tools/gen_skeleton.py`, and place the parts.

One piece of verification did come out of the attempt and is worth keeping: with the interface emitted, ERC reported **no `hier_label_mismatch` violations**, meaning all 24 signal names and directions agree across every sheet boundary. The interface in §2 is internally consistent.

`mcuc_inverter.kicad_pro` carries matching ERC severities: `label_dangling` and `pin_not_connected` are warnings during build-out, while `hier_label_mismatch` stays an error. Restore the first two to `error` once the blocks are populated.

### Suggested build order

1. Comparator front end (§3.1–3.3) — sets the trip references and the +5 V rail decision
2. Latch (§3.4) — depends only on the comparator output
3. Fault aggregation (§4) — needs the latch
4. PWM gating and dead time (§5) — largest gate count, depends on `ENABLE_INT` from §4

Steps 1–3 are independent of the power module choice. Step 4's dead-time RC needs the module's turn-off time, so it is the one part that should wait for `SPEC.md` §14 item 2.
