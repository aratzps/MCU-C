"""Probe: why does a specific candidate segment collide? Prints every collider."""
import router as R
from router import mm, VECTOR2I, F_Cu, B_Cu, seg_pts, required_clearance, query_for, cand_collide, bbox_dist, in_barrier

def explain_seg(ax, ay, bx, by, net, cls, w_mm, layer=F_Cu):
    a, b = VECTOR2I(mm(ax), mm(ay)), VECTOR2I(mm(bx), mm(by))
    w = mm(w_mm)
    print(f"--- seg ({ax},{ay})->({bx},{by}) w={w_mm} net={net} cls={cls} layer={'F' if layer==F_Cu else 'B'}")
    if in_barrier("seg", a, b, w):
        print("  BLOCKED BY BARRIER")
    pts = seg_pts(a, b)
    x0, x1 = min(a.x, b.x) - w // 2, max(a.x, b.x) + w // 2
    y0, y1 = min(a.y, b.y) - w // 2, max(a.y, b.y) + w // 2
    hits = 0
    for o in query_for(cls, x0, y0, x1, y1):
        if layer not in o.layers:
            continue
        clr = required_clearance(net, cls, pts, o)
        if clr is None:
            continue
        if bbox_dist(o.bbox, x0, y0, x1, y1) > clr + 1000:
            continue
        if cand_collide(o.shape, "seg", a, b, w, clr):
            hits += 1
            print(f"  HIT {o.net} [{o.cls}] clr={clr/1e6:.2f} bbox=({o.bbox[0]/1e6:.1f},{o.bbox[1]/1e6:.1f})-({o.bbox[2]/1e6:.1f},{o.bbox[3]/1e6:.1f})")
            if hits > 12:
                print("  ...")
                return
    if hits == 0:
        print("  CLEAN")

NET = "/Precharge and contactor/DC_BUS_N"
for w in (3.0, 1.2, 0.6):
    explain_seg(35.3, 48.1, 38.8, 48.1, NET, "HV_BUS", w)
# also a tiny stub east from C702 pad2
for w in (1.2, 0.6):
    explain_seg(35.3, 48.1, 36.0, 48.1, NET, "HV_BUS", w)
# and the U901 fine-pitch case on Default class
explain_seg(150.863, 15.35, 149.137, 11.30, "Net-(U901-Pad6)", "Default", 0.2)
explain_seg(150.863, 15.35, 151.8, 15.35, "Net-(U901-Pad6)", "Default", 0.2)
