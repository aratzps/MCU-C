# Proposal: initial-spec-and-architecture

> Marker: AUTO (autonomous mode; auto-approved, reviewable after the fact)

## Why

Greenfield project — no existing schematic or design docs. Need to establish the foundation for a 15kW–35kW, 48–450V VESC-compatible motor controller before any schematic work.

## What Changes

- Create SPEC.md with full electrical requirements, power budget, thermal targets, and VESC compatibility constraints
- Create BOM.md with initial MCU selection (STM32F405RGT6) and placeholder sections for power stage, gate drivers, current sensing, and isolation components
- Create PINOUT.md mapping STM32F405RGT6 pins to VESC-compatible functions (ADC channels, PWM outputs, CAN, UART, etc.)
- Create initial schematic (.kicad_sch) with MCU, power stage topology, and critical interconnections
- Establish the project's KiCad project files (.kicad_pro)
