# Proposal: recalculate-power-for-250v-nominal

> Marker: AUTO (autonomous mode; auto-approved, reviewable after the fact)

## Why

The 35kW peak and 15kW continuous power ratings are specified at 250V nominal, not at 48V. This reduces the design current from 729A/312A to 140A/60A, dramatically reducing MOSFET parallel count, shunt power rating, and thermal requirements. Power at other voltages = V_bus × I_limit.

## What Changes

- SPEC.md §2.1: Update power table — 35kW peak @ 250V, 15kW continuous @ 250V; update current figures (140A peak, 60A continuous @ 250V); add note that power at other voltages = V × I_limit
- SPEC.md §4.1: Update MOSFET parallel count from 6 to 3 per switch position (18 total) since 140A peak / 122A per device = 1.15, 3 for margin
- SPEC.md §5: Update shunt resistor power rating from 100W to ~5W peak (140² × 100µΩ = 1.96W peak, 60² × 100µΩ = 0.36W continuous)
- SPEC.md §8: Update thermal budget — dissipation drops significantly with lower current
- constraints.json: Replace `power.continuous_current_48V` with `power.continuous_current_nominal` (60A @ 250V); replace `power.peak_current_48V` with `power.peak_current_nominal` (140A @ 250V)
- BOM.md: Reduce MOSFET parallel quantities — Q1a–Q6a + Q1b–Q6b (2 additional parallels per switch = 18 total MOSFETs); reduce shunt resistor power rating
- docs/DECISIONS.md: Add D006 noting 250V nominal power rating basis
- docs/CHANGELOG.md: Append entry for this change
