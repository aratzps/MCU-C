"""Regenerate the MCU-C KiCad 9 schematic skeleton.

Emits the root sheet plus one hierarchical sub-sheet per functional block in
SPEC.md. IFACE below records the supervisor boundary (docs/supervisor.md
section 2) and its counterpart pins on the MCU, gate drive, current sense,
bus sense and temperature sheets.

    python tools/gen_skeleton.py

Regenerates the sheets from scratch, so do not hand-edit the generated files
while this script still drives them. Once real components are placed in
KiCad, retire the script rather than re-running it.
"""
import os
import uuid

# repo-relative: tools/ -> <repo>/mcuc_inverter
ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcuc_inverter"
)
PROJECT = "mcuc_inverter"
VERSION = 20250114
GEN_VER = "9.0"
TITLE = "MCU-C Integrated Inverter"
REV = "0.1"
DATE = "2026-07-30"
COMPANY = "MCU-C"
P = 2.54
STUB = 5.08

# Emit the block interfaces into the schematic?
#
# False until the blocks contain components. A hierarchical label inside an
# empty sheet is legitimately unconnected, so emitting the interface early
# produces ~96 unavoidable dangling-label warnings. copperhead's check fails
# on warnings as well as errors, which would leave the verification gate
# permanently red and therefore ignored.
#
# The interface itself is specified in docs/supervisor.md section 2, which is
# the authoritative source. Flip this to True in the same change that places
# the components, so the labels have something to connect to.
EMIT_INTERFACE = False

PWM = ["PWM_AH", "PWM_AL", "PWM_BH", "PWM_BL", "PWM_CH", "PWM_CL"]
GD = ["GD_AH", "GD_AL", "GD_BH", "GD_BL", "GD_CH", "GD_CL"]
ISENSE = ["ISENSE_A", "ISENSE_B", "ISENSE_C"]

# stem -> (inputs, outputs). Directions are from that sheet's point of view.
IFACE = {
    "supervisor": (
        PWM + ISENSE + ["GATE_FAULT_N", "OVP_N", "UVLO_N", "OTP_N",
                        "FAULT_RESET_N", "MCU_ENABLE"],
        GD + ["BKIN_N", "OCP_LATCHED", "FAULT_N"],
    ),
    "mcu": (
        ["BKIN_N", "OCP_LATCHED", "FAULT_N"],
        PWM + ["FAULT_RESET_N", "MCU_ENABLE"],
    ),
    "gate_drive":    (GD, ["GATE_FAULT_N"]),
    "current_sense": ([], ISENSE),
    "bus_sense":     ([], ["OVP_N", "UVLO_N"]),
    "temp_sense":    ([], ["OTP_N"]),
}

G = 1.27  # KiCad schematic grid; every emitted coordinate must land on it


def snap(v):
    return round(round(v / G) * G, 4)


# name, stem, spec ref, x, y, w, h  -- all snapped to the 1.27 mm grid
LAYOUT = [
    ("Power stage and DC link",   "power_stage",   "SPEC 4, 6",    20.32,  40.64, 60.96, 20.32),
    ("Gate drive",                "gate_drive",    "SPEC 5",       20.32,  72.39, 60.96, 22.86),
    ("Precharge and contactor",   "precharge",     "SPEC 7",       20.32, 106.68, 60.96, 20.32),
    ("Phase current sensing",     "current_sense", "SPEC 8.1",     20.32, 138.43, 60.96, 20.32),
    ("Bus voltage sensing",       "bus_sense",     "SPEC 8.2",     20.32, 170.18, 60.96, 20.32),
    ("Temperature sensing",       "temp_sense",    "SPEC 8.3",     20.32, 201.93, 60.96, 20.32),
    ("Position feedback",         "position",      "SPEC 8.4",     20.32, 233.68, 60.96, 20.32),
    ("MCU",                       "mcu",           "SPEC 12",     120.65,  40.64, 60.96, 30.48),
    ("Communications",            "comms",         "SPEC 12, 13", 120.65,  80.01, 60.96, 20.32),
    ("Auxiliary power",           "aux_power",     "SPEC 11",     120.65, 111.76, 60.96, 20.32),
    ("Supervisor and interlocks", "supervisor",    "SPEC 9.2",    229.87,  40.64, 76.20, 48.26),
]


def uid():
    return str(uuid.uuid4())


def title_block(n):
    return (f'\t(title_block\n\t\t(title "{TITLE}")\n\t\t(date "{DATE}")\n'
            f'\t\t(rev "{REV}")\n\t\t(company "{COMPANY}")\n\t\t(comment 1 "{n}")\n\t)\n')


def note(t, x, y, s=1.27):
    return (f'\t(text "{t}"\n\t\t(exclude_from_sim no)\n\t\t(at {x} {y} 0)\n\t\t(effects\n'
            f'\t\t\t(font\n\t\t\t\t(size {s} {s})\n\t\t\t)\n\t\t\t(justify left bottom)\n'
            f'\t\t)\n\t\t(uuid "{uid()}")\n\t)\n')


def wire(x1, y1, x2, y2):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {x1} {y1}) (xy {x2} {y2})\n\t\t)\n'
            f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(uuid "{uid()}")\n\t)\n')


def label(name, x, y, angle, justify):
    return (f'\t(label "{name}"\n\t\t(at {x} {y} {angle})\n\t\t(fields_autoplaced yes)\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            f'\t\t\t(justify {justify} bottom)\n\t\t)\n\t\t(uuid "{uid()}")\n\t)\n')


def sheet_pin(name, kind, x, y, angle, justify):
    return (f'\t\t(pin "{name}" {kind}\n\t\t\t(at {x} {y} {angle})\n\t\t\t(effects\n'
            f'\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
            f'\t\t\t\t(justify {justify})\n\t\t\t)\n\t\t\t(uuid "{uid()}")\n\t\t)\n')


def hier_label(name, shape, x, y, angle, justify):
    return (f'\t(hierarchical_label "{name}"\n\t\t(shape {shape})\n\t\t(at {x} {y} {angle})\n'
            f'\t\t(fields_autoplaced yes)\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {justify})\n\t\t)\n'
            f'\t\t(uuid "{uid()}")\n\t)\n')


def build_root():
    root_uuid = uid()
    out = ["(kicad_sch", f"\t(version {VERSION})", '\t(generator "eeschema")',
           f'\t(generator_version "{GEN_VER}")', f'\t(uuid "{root_uuid}")',
           '\t(paper "A3")', title_block("Root"), "\t(lib_symbols)"]
    out.append(note("MCU-C  -  48-450V DC, 250V nominal, 15kW cont / 35kW peak", 20, 18, 2.54))
    out.append(note("Supervisor interface per docs/supervisor.md. Other blocks are placeholders.", 20, 24))

    extras, page = [], 2
    for name, stem, ref, x, y, w, h in LAYOUT:
        pins_in, pins_out = IFACE.get(stem, ([], [])) if EMIT_INTERFACE else ([], [])
        body = [f'\t(sheet\n\t\t(at {x} {y})\n\t\t(size {w} {h})\n',
                '\t\t(fields_autoplaced yes)\n',
                '\t\t(stroke\n\t\t\t(width 0.1524)\n\t\t\t(type solid)\n\t\t)\n',
                '\t\t(fill\n\t\t\t(color 0 0 0 0.0000)\n\t\t)\n',
                f'\t\t(uuid "{uid()}")\n',
                f'\t\t(property "Sheetname" "{name}"\n\t\t\t(at {x} {y - 0.7116} 0)\n'
                '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
                '\t\t\t\t(justify left bottom)\n\t\t\t)\n\t\t)\n',
                f'\t\t(property "Sheetfile" "{stem}.kicad_sch"\n\t\t\t(at {x} {y + h + 0.5846} 0)\n'
                '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
                '\t\t\t\t(justify left top)\n\t\t\t)\n\t\t)\n']

        for i, n in enumerate(pins_in):
            py = y + P * (i + 1)
            body.append(sheet_pin(n, "input", x, py, 180, "right"))
            extras.append(wire(x, py, x - STUB, py))
            extras.append(label(n, x - STUB, py, 180, "right"))
        for i, n in enumerate(pins_out):
            py = y + P * (i + 1)
            body.append(sheet_pin(n, "output", x + w, py, 0, "left"))
            extras.append(wire(x + w, py, x + w + STUB, py))
            extras.append(label(n, x + w + STUB, py, 0, "left"))

        body.append(f'\t\t(instances\n\t\t\t(project "{PROJECT}"\n\t\t\t\t(path "/{root_uuid}"\n'
                    f'\t\t\t\t\t(page "{page}")\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
        out.append("".join(body))
        out.append(note(ref, x, y + h + 4.0, 1.0))
        page += 1

    out.extend(extras)
    out.append('\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)')
    out.append("\t(embedded_fonts no)")
    out.append(")")
    with open(os.path.join(ROOT, f"{PROJECT}.kicad_sch"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def build_subsheet(name, stem, ref):
    li, lo = IFACE.get(stem, ([], [])) if EMIT_INTERFACE else ([], [])
    out = ["(kicad_sch", f"\t(version {VERSION})", '\t(generator "eeschema")',
           f'\t(generator_version "{GEN_VER}")', f'\t(uuid "{uid()}")',
           '\t(paper "A3")', title_block(name), "\t(lib_symbols)",
           note(name, 20, 20, 2.54)]
    if li or lo:
        if stem == "supervisor":
            out.append(note("Interface defined. Components not yet placed - see docs/supervisor.md", 20, 27))
        else:
            out.append(note("Interface defined for the supervisor boundary. Block not yet designed.", 20, 27))
        if li:
            out.append(note("INPUTS", 30.48, 40.64, 1.8))
            for i, n in enumerate(li):
                out.append(hier_label(n, "input", 30.48, snap(45.72 + P * i), 180, "right"))
        if lo:
            out.append(note("OUTPUTS", 149.86, 40.64, 1.8))
            for i, n in enumerate(lo):
                out.append(hier_label(n, "output", 149.86, snap(45.72 + P * i), 0, "left"))
    else:
        out.append(note(f"Placeholder. Requirements: {ref}", 20, 27))
    out.append("\t(embedded_fonts no)")
    out.append(")")
    with open(os.path.join(ROOT, f"{stem}.kicad_sch"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


build_root()
for name, stem, ref, *_ in LAYOUT:
    build_subsheet(name, stem, ref)

n_sig = sum(len(a) + len(b) for a, b in IFACE.values())
if EMIT_INTERFACE:
    print(f"root + {len(LAYOUT)} sheets; {n_sig} sheet pins across {len(IFACE)} interfaced blocks")
else:
    print(f"root + {len(LAYOUT)} sheets; interfaces NOT emitted (EMIT_INTERFACE=False)")
    print(f"  {n_sig} pins across {len(IFACE)} blocks are defined but held back - see the note above")
