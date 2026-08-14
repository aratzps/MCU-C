# MCU-C control/driver board — fabrication specification

Order parameters for the main board (`mcuc_inverter`). **Gerbers are generated once routing completes; this document specifies how the board must be built and exists separately because several requirements are unusual and a fabricator's defaults will get them wrong.**

Companion: `fabrication/mcuc_dclink/README.md` (the second board — different rules, do not conflate them).

## 1. The three requirements a fabricator will get wrong by default

| # | Requirement | Default that breaks it |
|---|---|---|
| 1 | **Press-fit holes: finished diameter 1.02–1.10 mm, drill tool 1.15 mm, hole wall copper 25–50 µm, and the surface finish in those holes must be IMMERSION TIN.** | Infineon AN-G2-ASSEMBLY explicitly discourages HAL-LF, ENIG and OSP in press-fit holes. A fab quoting "ENIG" as a blanket finish produces a board the module cannot be pressed into reliably. The 30 press-fit holes are deliberately drawn at a unique 1.06 mm so they land in their own NC drill tool and cannot be silently merged with vias. |
| 2 | **Board thickness 1.6 mm ±0.16 mm (±10 %), not the usual ±10 % on a nominal that drifts.** | The module's press-fit pin retention and the EJOT screw engagement are both specified against 1.6 ±0.16 mm. |
| 3 | **The 6.4 mm HV-to-LV barrier channels must not be flooded with copper.** | Auto-flood/teardrop/copper-balancing steps offered as "manufacturability improvements" will bridge the isolation barrier. The board carries explicit keepout areas; **do not modify copper.** |

## 2. Stackup and process

| Parameter | Value | Note |
|---|---|---|
| Layers | 4 | F.Cu / GND / power islands / B.Cu |
| Board size | 200 × 132 mm | |
| Thickness | **1.6 mm ±0.16 mm** | Press-fit requirement, §1 |
| Outer copper | 1 oz base, **2 oz finished preferred** | Gate-drive and HV traces; declare in the stackup |
| Inner copper | 1 oz | |
| Material | FR-4, **TG150 minimum** | Operating ambient ≤70 °C (SPEC §11.5) plus power dissipation nearby |
| Surface finish | **Immersion tin** | Mandated by the press-fit holes (§1); applies to the whole board for process simplicity |
| Soldermask | Both sides | Must respect the barrier keepouts |
| Silkscreen | Both sides | Carries HV warnings and the barrier annotation |
| Min track / clearance | 0.2 mm / 0.2 mm (signal) | HV nets are on their own netclass at 2.0 mm |
| Min drill | 0.3 mm (vias) | Plus the dedicated 1.06 mm press-fit tool |
| Electrical test | **Required** | 460+ components, HV barrier — do not waive |

## 3. High-voltage construction requirements

The board carries **450 V DC working voltage** with a control domain that must stay isolated from it.

- **Barrier channels of ≥6.4 mm** separate the HV and LV domains everywhere, enforced in `mcuc_inverter.kicad_dru` by a custom `HV_to_LV` rule (not merely drawn — the rule was verified live by planting a violating track and confirming DRC caught it).
- **14 copper keepout areas** sit under the isolator bodies (gate drivers, flyback transformer, InSOP switcher, bus-sense amplifier, discharge opto, relay, CAN channel). No copper of either domain may enter them.
- **No panel rails, tooling holes, fiducials or copper thieving may be added inside a barrier channel.** If panelisation requires additions, they go outside the board outline or in the LV region only — query before assuming.
- V-scoring across the board is **not** permitted (it would cross the barrier); use tab-routing outside the HV zone if panelising.

## 4. Assembly notes

- **The power module is not fitted by the PCB fabricator.** It is pressed in afterwards per Infineon AN-G2-ASSEMBLY, with either 6× EJOT Delta PT WN5451 30×10 screws at 0.45–0.55 N·m **or** heat-staking — never both. Press-tool distance keepers land on the six heat-stake positions, so the top side must stay clear of Ø6 mm around them.
- **Component keepout around every press-fit hole**: ≥3 mm radius for small passives and SO/QFP packages, ≥4 mm for everything else. Already enforced in placement; do not relocate parts.
- Several components are **deliberately not on this board** (D024): the DC-link capacitors (carrier board), the precharge and discharge resistors and the current transducers (chassis-mounted, harnessed). They appear in the schematic with `exclude_from_board` set, so a schematic-parity check will report them — this is expected, not an error.
- HV interface terminals (J401–J405) and phase terminals are M4/M6 ring-lug pads, hand-assembled.

## 5. Verification status at release

Gerbers are released only when all of the following hold, and the release commit records them:

- [ ] ERC: 0 errors on the full hierarchy
- [ ] DRC: 0 violations **including the custom HV rules**, 0 unconnected items
- [ ] Netlist machine-check of the safety paths: overcurrent trip to TIM1_BKIN, DESAT chains, gate/Kelvin pairs, HV-to-LV separation (no HV net sharing a pin with any LV rail)
- [ ] All fixes from `docs/REVIEW_FINDINGS.md` dispositioned and verified

**Do not order boards against an interim gerber set.** The design has already been through three adversarial reviews that found seven critical defects; the release gate exists because passing ERC and DRC alone was demonstrably not sufficient.

## 6. BOM and placement

`docs/BOM.md` (suppliers, pricing, stock caveats), `docs/BOM_mcuc_inverter.csv` (refdes level). Position file is generated with the gerbers.

**Long-lead items to order at design commit, not at board delivery**: the SiC module (39 weeks behind current stock), AD2S1205 (20 weeks, zero distributor stock at last check), LEM HOYS transducers (5 pcs at last check), STM32F405VGT6 (dry at DigiKey/Mouser — source from Newark/Farnell), Hongfa precharge relay (non-DigiKey channel).
