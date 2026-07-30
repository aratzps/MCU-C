# Design changelog

Append-only, newest first. One entry per committed copperhead run.

## 2026-07-30 — let's review some of this. The 35kW power figure is at 250V Nominal, please adjust the project accordingly. This should fix the current and at other voltages the power it is what it is

- Change: recalculate-power-for-250v-nominal
- Files: SPEC.md, .copperhead/constraints.json, BOM.md, docs/DECISIONS.md, docs/CHANGELOG.md, docs\DECISIONS.md
- Verification: ERC not required

## 2026-07-30 — I want to design a new MCU based on this project. It has to be VESC compatible. Specs: Voltage range 48-450V, continuous power 15kW, peak power 35kW. Let's start there

- Change: initial-spec-and-architecture
- Files: SPEC.md, BOM.md, PINOUT.md, docs/DECISIONS.md
- Verification: ERC not required


## 2026-07-30 — Recalculate power ratings for 250V nominal basis

- Change: recalculate-power-for-250v-nominal
- Files: SPEC.md, BOM.md, docs/DECISIONS.md, .copperhead/constraints.json
- Verification: ERC, check_drift
- Summary: Moved 35kW peak / 15kW continuous power ratings from 48V to 250V nominal. Peak current: 729A → 140A. Continuous current: 312A → 60A. MOSFETs: 6 parallel/switch (36 total) → 3 parallel/switch (18 total). Shunt resistor: 100W → 5W–10W. Thermal: liquid cooling no longer mandatory, forced air sufficient.
