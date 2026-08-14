"""Refill all zones and save the board atomically.

Usage: kicad python refill.py [board.kicad_pcb]
Default board: <repo>/mcuc_inverter/mcuc_inverter.kicad_pcb
"""
import os, sys
import pcbnew

ROOT = os.environ.get("MCUC_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BOARD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "mcuc_inverter", "mcuc_inverter.kicad_pcb")

board = pcbnew.LoadBoard(BOARD)
if board is None:
    print("FATAL: board failed to load", file=sys.stderr)
    sys.exit(2)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
tmp = BOARD + ".saving"
pcbnew.SaveBoard(tmp, board)
if os.path.getsize(tmp) < 1_000_000:
    print("FATAL: suspiciously small save, not installing", file=sys.stderr)
    sys.exit(2)
os.replace(tmp, BOARD)
print("zones refilled, board saved. zones:", len(board.Zones()))
