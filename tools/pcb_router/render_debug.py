"""Render a crop of the board to PNG for debugging congestion.
Usage: render_debug.py out.png x0 y0 x1 y1 [drc.json]
Colors: F.Cu red, B.Cu blue, vias magenta, pads dark, open-net items green,
unconnected endpoints yellow crosses, barriers black outline.
"""
import sys, json, math, re
import wx
import pcbnew
from pcbnew import F_Cu, B_Cu

import os
BOARD = os.environ.get("MCUC_BOARD") or os.path.join(os.environ.get("MCUC_ROOT") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")), "mcuc_inverter", "mcuc_inverter.kicad_pcb")

out, x0, y0, x1, y1 = sys.argv[1], *map(float, sys.argv[2:6])
drcp = sys.argv[6] if len(sys.argv) > 6 else None
SCALE = 40  # px per mm
W, H = int((x1 - x0) * SCALE), int((y1 - y0) * SCALE)

open_nets = set()
marks = []
if drcp:
    drc = json.load(open(drcp, encoding="utf-8"))
    net_re = re.compile(r"\[([^\]]*)\]")
    for u in drc["unconnected_items"]:
        for it in u["items"]:
            m = net_re.search(it["description"])
            if m:
                open_nets.add(m.group(1))
            marks.append((it["pos"]["x"], it["pos"]["y"]))

board = pcbnew.LoadBoard(BOARD)
app = wx.App()
bmp = wx.Bitmap(W, H)
dc = wx.MemoryDC(bmp)
dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255)))
dc.Clear()

def px(x): return int((x / 1e6 - x0) * SCALE)
def py(y): return int((y / 1e6 - y0) * SCALE)

def track_color(t, layer):
    if t.GetNetname() in open_nets:
        return wx.Colour(0, 170, 0)
    return wx.Colour(220, 60, 60) if layer == F_Cu else wx.Colour(60, 90, 220)

# tracks
for t in board.GetTracks():
    b = t.GetBoundingBox()
    if b.GetX() / 1e6 > x1 or (b.GetX() + b.GetWidth()) / 1e6 < x0:
        continue
    if b.GetY() / 1e6 > y1 or (b.GetY() + b.GetHeight()) / 1e6 < y0:
        continue
    if t.GetClass() == "PCB_VIA":
        dc.SetPen(wx.Pen(wx.Colour(200, 0, 200), 1))
        dc.SetBrush(wx.Brush(wx.Colour(200, 0, 200, 120)))
        r = max(2, int(t.GetWidth(F_Cu) / 2e6 * SCALE))
        dc.DrawCircle(px(t.GetPosition().x), py(t.GetPosition().y), r)
    else:
        lw = max(1, int(t.GetWidth() / 1e6 * SCALE))
        dc.SetPen(wx.Pen(track_color(t, t.GetLayer()), lw))
        if t.GetLayer() in (F_Cu, B_Cu):
            dc.DrawLine(px(t.GetStart().x), py(t.GetStart().y), px(t.GetEnd().x), py(t.GetEnd().y))

# pads
for fp in board.GetFootprints():
    for pad in fp.Pads():
        p = pad.GetPosition()
        if not (x0 <= p.x / 1e6 <= x1 and y0 <= p.y / 1e6 <= y1):
            continue
        sz = pad.GetSize()
        c = wx.Colour(0, 130, 0) if pad.GetNetname() in open_nets else wx.Colour(80, 80, 80)
        dc.SetPen(wx.Pen(c, 1))
        dc.SetBrush(wx.Brush(c) if pad.GetNetname() in open_nets else wx.TRANSPARENT_BRUSH)
        w = max(2, int(sz.x / 1e6 * SCALE))
        h = max(2, int(sz.y / 1e6 * SCALE))
        ang = pad.GetOrientation().AsDegrees() % 180
        if 45 < ang < 135:
            w, h = h, w
        dc.DrawRectangle(px(p.x) - w // 2, py(p.y) - h // 2, w, h)

# footprint refs
dc.SetTextForeground(wx.Colour(0, 0, 0))
dc.SetFont(wx.Font(7, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
for fp in board.GetFootprints():
    p = fp.GetPosition()
    if x0 <= p.x / 1e6 <= x1 and y0 <= p.y / 1e6 <= y1:
        dc.DrawText(fp.GetReference(), px(p.x) + 2, py(p.y) + 2)

# rule areas
for z in board.Zones():
    if not z.GetIsRuleArea():
        continue
    o = z.Outline()
    name = z.GetZoneName()
    col = wx.Colour(0, 0, 0) if name.startswith("BARRIER") else wx.Colour(255, 165, 0)
    dc.SetPen(wx.Pen(col, 2, wx.PENSTYLE_LONG_DASH if not name.startswith("BARRIER") else wx.PENSTYLE_SOLID))
    dc.SetBrush(wx.TRANSPARENT_BRUSH)
    for i in range(o.OutlineCount()):
        ol = o.Outline(i)
        pts = [wx.Point(px(ol.CPoint(k).x), py(ol.CPoint(k).y)) for k in range(ol.PointCount())]
        dc.DrawPolygon(pts)

# unconnected endpoint marks
dc.SetPen(wx.Pen(wx.Colour(230, 180, 0), 2))
for mx, my in marks:
    if x0 <= mx <= x1 and y0 <= my <= y1:
        X, Y = int((mx - x0) * SCALE), int((my - y0) * SCALE)
        dc.DrawLine(X - 6, Y - 6, X + 6, Y + 6)
        dc.DrawLine(X - 6, Y + 6, X + 6, Y - 6)

dc.SelectObject(wx.NullBitmap)
bmp.SaveFile(out, wx.BITMAP_TYPE_PNG)
print("wrote", out, f"{W}x{H}")
