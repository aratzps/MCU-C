"""Generate the supervisor overcurrent comparator front end (docs/supervisor.md 3).

Places the threshold divider, six LM2903 comparator channels and the wired-OR
trip node into mcuc_inverter/supervisor.kicad_sch, with symbol definitions
embedded from the stock KiCad 9 libraries.

Connections are made with a short stub wire off each pin, terminated either by
a local label (signals) or a power symbol (rails). No routed wires - net
formation is by label name, which is unambiguous and survives re-layout.

    python tools/gen_supervisor_frontend.py
"""
import os
import re
import uuid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCH = os.path.join(REPO, "mcuc_inverter", "supervisor.kicad_sch")
ROOT_SCH = os.path.join(REPO, "mcuc_inverter", "mcuc_inverter.kicad_sch")
LIB = r"C:\Program Files\KiCad\9.0\share\kicad\symbols"

VERSION, GEN_VER, PROJECT = 20250114, "9.0", "mcuc_inverter"
G, STUB = 1.27, 2.54

# lib_id -> (library file, symbol name)
SYMS = {
    "Comparator:LM2903": ("Comparator", "LM2903"),
    "Device:R":          ("Device", "R"),
    "Device:C":          ("Device", "C"),
    "power:+3V3":        ("power", "+3V3"),
    "power:+5V":         ("power", "+5V"),
    "power:GND":         ("power", "GND"),
    "power:PWR_FLAG":    ("power", "PWR_FLAG"),
}

# lib_id -> unit -> pin number -> (dx, dy, stub direction)
PINS = {
    "Comparator:LM2903": {
        1: {"3": (-7.62, 2.54, "L"), "2": (-7.62, -2.54, "L"), "1": (7.62, 0, "R")},
        2: {"5": (-7.62, 2.54, "L"), "6": (-7.62, -2.54, "L"), "7": (7.62, 0, "R")},
        3: {"8": (-2.54, 7.62, "U"), "4": (-2.54, -7.62, "D")},
    },
    "Device:R": {1: {"1": (0, 3.81, "U"), "2": (0, -3.81, "D")}},
    "Device:C": {1: {"1": (0, 3.81, "U"), "2": (0, -3.81, "D")}},
    "power:+3V3":     {1: {"1": (0, 0, "N")}},
    "power:+5V":      {1: {"1": (0, 0, "N")}},
    "power:GND":      {1: {"1": (0, 0, "N")}},
    "power:PWR_FLAG": {1: {"1": (0, 0, "N")}},
}

DELTA = {"L": (-STUB, 0), "R": (STUB, 0), "U": (0, -STUB), "D": (0, STUB)}


def uid():
    return str(uuid.uuid4())


def snap(v):
    return round(round(v / G) * G, 4)


def extract(libfile, name, lib_id):
    """Pull one top-level symbol block out of a .kicad_sym by brace matching.

    Inside a .kicad_sch the lib_symbols entry must be keyed by the full lib_id
    ("Device:R"), while its child units keep the bare name ("R_0_1"). Renaming
    only the outer symbol is what makes placed lib_id references resolve.
    """
    d = open(os.path.join(LIB, libfile + ".kicad_sym"), encoding="utf-8").read()
    i = d.index('(symbol "%s"' % name)
    depth = 0
    for j in range(i, len(d)):
        if d[j] == "(":
            depth += 1
        elif d[j] == ")":
            depth -= 1
            if depth == 0:
                break
    blk = d[i:j + 1]
    return blk.replace('(symbol "%s"' % name, '(symbol "%s"' % lib_id, 1)


def pin_abs(lib_id, unit, num, x, y):
    dx, dy, _ = PINS[lib_id][unit][num]
    return snap(x + dx), snap(y - dy)


# ---------------------------------------------------------------- layout ----
# ref, lib_id, value, unit, x, y, {pin: net}
COMPS = []

# Threshold divider: 3V3 - 1k - 11k - 1k - GND
# tap A = 3.3 * 12/13 = 3.046 V (+280 A)
# tap B = 3.3 *  1/13 = 0.254 V (-280 A)
COMPS += [
    ("R1", "Device:R", "1k",  1, 40.64, 38.10, {"1": "+3V3", "2": "V_TH_POS"}),
    ("R2", "Device:R", "11k", 1, 40.64, 53.34, {"1": "V_TH_POS", "2": "V_TH_NEG"}),
    ("R3", "Device:R", "1k",  1, 40.64, 68.58, {"1": "V_TH_NEG", "2": "GND"}),
    ("C1", "Device:C", "100nF", 1, 55.88, 45.72, {"1": "V_TH_POS", "2": "GND"}),
    ("C2", "Device:C", "100nF", 1, 55.88, 60.96, {"1": "V_TH_NEG", "2": "GND"}),
]

# Six comparator channels.
#   positive trip: IN+ = V_TH_POS, IN- = ISENSE_x  -> out low when ISENSE > threshold
#   negative trip: IN+ = ISENSE_x, IN- = V_TH_NEG  -> out low when ISENSE < threshold
CH = [("A", "U1", 111.76), ("B", "U2", 154.94), ("C", "U3", 198.12)]
for ph, ref, x in CH:
    COMPS.append((ref, "Comparator:LM2903", "LM2903", 1, x, 45.72,
                  {"3": "V_TH_POS", "2": "ISENSE_%s" % ph, "1": "OC_TRIP_N"}))
    COMPS.append((ref, "Comparator:LM2903", "LM2903", 2, x, 76.20,
                  {"5": "ISENSE_%s" % ph, "6": "V_TH_NEG", "7": "OC_TRIP_N"}))
    COMPS.append((ref, "Comparator:LM2903", "LM2903", 3, x, 106.68,
                  {"8": "+5V", "4": "GND"}))
    # one decoupling cap per package
    n = {"A": "C4", "B": "C5", "C": "C6"}[ph]
    COMPS.append((n, "Device:C", "100nF", 1, x + 20.32, 106.68, {"1": "+5V", "2": "GND"}))

# Wired-OR trip node: pull-up to 3V3 and a small filter to ground.
COMPS += [
    ("R4", "Device:R", "4.7k",  1, 236.22, 38.10, {"1": "+3V3", "2": "OC_TRIP_N"}),
    ("C3", "Device:C", "100pF", 1, 236.22, 53.34, {"1": "OC_TRIP_N", "2": "GND"}),
]

# PWR_FLAG so ERC sees the rails as driven; this sheet has no regulators.
FLAGS = [("+3V3", 20.32, 22.86), ("+5V", 35.56, 22.86), ("GND", 50.80, 22.86)]

HIER_IN = ["ISENSE_A", "ISENSE_B", "ISENSE_C"]

POWER_NETS = {"+3V3": "power:+3V3", "+5V": "power:+5V", "GND": "power:GND"}


# ----------------------------------------------------------------- emit ----
def prop(name, value, x, y, hide=False, size=1.27):
    h = "\n\t\t\t\t(hide yes)" if hide else ""
    return (f'\t\t(property "{name}" "{value}"\n\t\t\t(at {x} {y} 0)\n\t\t\t(effects\n'
            f'\t\t\t\t(font\n\t\t\t\t\t(size {size} {size})\n\t\t\t\t){h}\n\t\t\t)\n\t\t)\n')


def symbol(lib_id, ref, value, unit, x, y, sheet_path, show_fields=True):
    pins = "".join(f'\t\t(pin "{n}"\n\t\t\t(uuid "{uid()}")\n\t\t)\n'
                   for n in PINS[lib_id][unit])
    hide_ref = not show_fields
    s = [f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {x} {y} 0)\n\t\t(unit {unit})\n',
         '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n',
         '\t\t(fields_autoplaced yes)\n', f'\t\t(uuid "{uid()}")\n',
         prop("Reference", ref, x + 5.08, y - 2.54, hide_ref),
         prop("Value", value, x + 5.08, y + 2.54, hide_ref),
         prop("Footprint", "", x, y, True),
         prop("Datasheet", "", x, y, True),
         prop("Description", "", x, y, True),
         pins,
         f'\t\t(instances\n\t\t\t(project "{PROJECT}"\n\t\t\t\t(path "{sheet_path}"\n'
         f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit {unit})\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n']
    return "".join(s)


def wire(x1, y1, x2, y2):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {x1} {y1}) (xy {x2} {y2})\n\t\t)\n'
            f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(uuid "{uid()}")\n\t)\n')


def label(name, x, y, angle=0):
    return (f'\t(label "{name}"\n\t\t(at {x} {y} {angle})\n\t\t(fields_autoplaced yes)\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            f'\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{uid()}")\n\t)\n')


def hier_label(name, x, y, angle=180):
    return (f'\t(hierarchical_label "{name}"\n\t\t(shape input)\n\t\t(at {x} {y} {angle})\n'
            f'\t\t(fields_autoplaced yes)\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify right)\n\t\t)\n'
            f'\t\t(uuid "{uid()}")\n\t)\n')


def text(t, x, y, size=1.27):
    return (f'\t(text "{t}"\n\t\t(exclude_from_sim no)\n\t\t(at {x} {y} 0)\n\t\t(effects\n'
            f'\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t)\n\t\t\t(justify left bottom)\n'
            f'\t\t)\n\t\t(uuid "{uid()}")\n\t)\n')


import itertools
PWRSEQ = ("#PWR%02d" % i for i in itertools.count(1))
FLGSEQ = ("#FLG%02d" % i for i in itertools.count(1))


def build():
    # the sheet's instance path must match the root's uuid + this sheet's uuid
    root = open(ROOT_SCH, encoding="utf-8").read()
    root_uuid = re.search(r'\(uuid "([0-9a-f-]+)"\)', root).group(1)
    m = re.search(r'\(sheet\b.*?\(uuid "([0-9a-f-]+)"\).*?"Sheetfile" "supervisor\.kicad_sch"',
                  root, re.S)
    sheet_uuid = m.group(1)
    path = f"/{root_uuid}/{sheet_uuid}"

    out = ["(kicad_sch", f"\t(version {VERSION})", '\t(generator "eeschema")',
           f'\t(generator_version "{GEN_VER}")', f'\t(uuid "{uid()}")', '\t(paper "A3")',
           '\t(title_block\n\t\t(title "MCU-C Integrated Inverter")\n\t\t(date "2026-07-30")\n'
           '\t\t(rev "0.1")\n\t\t(company "MCU-C")\n'
           '\t\t(comment 1 "Supervisor and interlocks")\n\t)\n']

    # embedded symbol definitions
    libs = "".join("\t\t" + extract(f, n, lid).replace("\n", "\n\t\t") + "\n"
                   for lid, (f, n) in SYMS.items())
    out.append("\t(lib_symbols\n" + libs + "\t)\n")

    out.append(text("Overcurrent comparator front end  -  docs/supervisor.md section 3", 20.32, 15.24, 2.54))
    out.append(text("Trip at +/-280 A. Divider taps 3.046 V and 0.254 V from 3V3.", 20.32, 20.32))
    out.append(text("Comparators on +5V: LM2903 common-mode ceiling is VCC-1.5V,", 20.32, 24.13))
    out.append(text("so 3.3V would put the 3.046 V trip out of range.", 20.32, 27.94))
    out.append(text("Latch, fault aggregation and PWM gating not yet placed.", 20.32, 130.0))

    body = []
    for ref, lib_id, value, unit, x, y, nets in COMPS:
        body.append(symbol(lib_id, ref, value, unit, x, y, path, show_fields=(unit == 1)))
        for num, net in nets.items():
            px, py = pin_abs(lib_id, unit, num, x, y)
            d = PINS[lib_id][unit][num][2]
            ddx, ddy = DELTA[d]
            ex, ey = snap(px + ddx), snap(py + ddy)
            body.append(wire(px, py, ex, ey))
            if net in POWER_NETS:
                body.append(symbol(POWER_NETS[net], next(PWRSEQ), net, 1, ex, ey, path, False))
            else:
                body.append(label(net, ex, ey))

    # power flags
    for net, x, y in FLAGS:
        body.append(symbol("power:PWR_FLAG", next(FLGSEQ), "PWR_FLAG", 1, x, y, path, False))
        body.append(wire(x, y, x, snap(y + STUB)))
        body.append(symbol(POWER_NETS[net], next(PWRSEQ), net, 1, x, snap(y + STUB), path, False))

    # sheet-boundary inputs
    for i, n in enumerate(HIER_IN):
        y = snap(150.0 + STUB * i)
        body.append(hier_label(n, 30.48, y))
        body.append(wire(30.48, y, snap(30.48 + STUB), y))
        body.append(label(n, snap(30.48 + STUB), y))

    out.extend(body)
    out.append(f'\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)')
    out.append("\t(embedded_fonts no)")
    out.append(")")
    open(SCH, "w", encoding="utf-8").write("\n".join(out) + "\n")
    n_sym = len([c for c in COMPS if c[3] == 1])
    print(f"supervisor.kicad_sch: {len(COMPS)} symbol units, {n_sym} components placed")


build()
