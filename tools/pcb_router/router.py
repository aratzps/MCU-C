"""Collision-checked completion router for mcuc_inverter.kicad_pcb.

Reads the DRC unconnected-items list, routes each edge with exact
SHAPE::Collide checks against every nearby copper item, honouring:
  - netclass clearances (Default/GATE 0.2, HV_BUS 2.0)
  - the HV_to_LV 6.4 mm rule with HV_DOMAIN exemption
  - HV_RELAX (0.6) / HV_RELAX_PIN (0.25) relaxations
  - BARRIER_* rule areas (no tracks, no vias)
  - board edge clearance
New copper goes on F.Cu / B.Cu only; vias may tap In1 (GND) and In2
(power islands) where a same-net filled zone covers the point.
"""
import sys, os, json, math, re, heapq, fnmatch, collections, time
import pcbnew
from pcbnew import VECTOR2I, F_Cu, B_Cu, In1_Cu, In2_Cu

ROOT = os.environ.get("MCUC_ROOT") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BOARD_PATH = os.path.join(ROOT, "mcuc_inverter", "mcuc_inverter.kicad_pcb")
PRO_PATH = os.path.join(ROOT, "mcuc_inverter", "mcuc_inverter.kicad_pro")
SP = os.environ.get("MCUC_ROUTER_WORK") or os.path.join(os.environ.get("TEMP", "."), "mcuc_router")
os.makedirs(SP, exist_ok=True)

MM = 1_000_000
def mm(v): return int(round(v * MM))

def safe_save(board_obj):
    """atomic board save: write to temp, then replace Ã¢â‚¬â€ a crash mid-write
    can no longer truncate the real file"""
    tmp = BOARD_PATH + ".saving"
    pcbnew.SaveBoard(tmp, board_obj)
    if os.path.getsize(tmp) < 1_000_000:
        raise RuntimeError(f"refusing to install suspiciously small save ({os.path.getsize(tmp)} bytes)")
    os.replace(tmp, BOARD_PATH)

# ---------------- netclass model ----------------
pro = json.load(open(PRO_PATH, encoding="utf-8"))
ns = pro["net_settings"]
CLASSES = {c["name"]: c for c in ns["classes"]}
PATTERNS = [(p["pattern"], p["netclass"]) for p in ns.get("netclass_patterns", [])]

def netclass_of(netname):
    for pat, cls in PATTERNS:
        if fnmatch.fnmatchcase(netname, pat):
            return cls
    return "Default"

def class_params(cls):
    c = CLASSES.get(cls, CLASSES["Default"])
    return dict(clearance=mm(c["clearance"]), width=mm(c["track_width"]),
                via_dia=mm(c["via_diameter"]), via_drill=mm(c["via_drill"]))

# ---------------- board ----------------
board = pcbnew.LoadBoard(BOARD_PATH)
bds = board.GetDesignSettings()
EDGE_CLR = bds.m_CopperEdgeClearance
bb = board.GetBoardEdgesBoundingBox()
BX0, BY0 = bb.GetX(), bb.GetY()
BX1, BY1 = bb.GetX() + bb.GetWidth(), bb.GetY() + bb.GetHeight()

HOLE_TO_HOLE = mm(0.5)

# rule areas
BARRIERS = []      # outlines where no track/via may go
HV_DOMAIN = []     # SHAPE_POLY_SET list
HV_RELAX = []
HV_RELAX_PIN = []
for z in board.Zones():
    if not z.GetIsRuleArea():
        continue
    name = z.GetZoneName()
    outline = z.Outline()
    if name.startswith("BARRIER"):
        BARRIERS.append(outline)
    elif name == "HV_DOMAIN":
        HV_DOMAIN.append(outline)
    elif name == "HV_RELAX":
        HV_RELAX.append(outline)
    elif name == "HV_RELAX_PIN":
        HV_RELAX_PIN.append(outline)

# footprint-embedded rule areas (e.g. isolation keepout inside U608)
for fp in board.GetFootprints():
    for z in fp.Zones():
        if z.GetIsRuleArea() and (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()):
            BARRIERS.append(z.Outline())

def in_areas(areas, pts):
    """ANY pt inside any polygon of the list (matches KiCad insideArea =
    intersects semantics closely enough for our sample points)"""
    for p in pts:
        for a in areas:
            if a.Contains(p):
                return True
    return False

def pt_in_areas(areas, p):
    for a in areas:
        if a.Contains(p):
            return True
    return False

# same-net filled zones for via-to-plane taps
NET_ZONES = collections.defaultdict(list)  # netname -> [(layer, zone)]
for z in board.Zones():
    if z.GetIsRuleArea() or not z.IsFilled():
        continue
    for l in (F_Cu, In1_Cu, In2_Cu, B_Cu):
        if z.IsOnLayer(l):
            NET_ZONES[z.GetNetname()].append((l, z))

# ---------------- obstacle index ----------------
CELL = mm(4)

class Obstacle:
    __slots__ = ("shape", "bbox", "net", "cls", "layers", "hole", "holepos", "center", "fully_in_dom", "item", "zone_fill")
    def __init__(self, shape, bboxrect, net, cls, layers, hole=0, holepos=None, item=None):
        self.item = item
        self.zone_fill = False
        self.shape = shape
        self.bbox = (bboxrect.GetX(), bboxrect.GetY(),
                     bboxrect.GetX() + bboxrect.GetWidth(), bboxrect.GetY() + bboxrect.GetHeight())
        self.net = net
        self.cls = cls
        self.layers = layers
        self.hole = hole
        self.holepos = holepos
        cx = (self.bbox[0] + self.bbox[2]) // 2
        cy = (self.bbox[1] + self.bbox[3]) // 2
        self.center = VECTOR2I(cx, cy)
        corners = [VECTOR2I(self.bbox[0], self.bbox[1]), VECTOR2I(self.bbox[2], self.bbox[3]),
                   VECTOR2I(self.bbox[0], self.bbox[3]), VECTOR2I(self.bbox[2], self.bbox[1])]
        self.fully_in_dom = in_areas(HV_DOMAIN, corners) if HV_DOMAIN else False

GRID = collections.defaultdict(list)      # all obstacles
GRID_HV = collections.defaultdict(list)   # HV_BUS obstacles only

def grid_cells(x0, y0, x1, y1):
    for cx in range(x0 // CELL, x1 // CELL + 1):
        for cy in range(y0 // CELL, y1 // CELL + 1):
            yield (cx, cy)

def add_obstacle(o):
    for c in grid_cells(o.bbox[0], o.bbox[1], o.bbox[2], o.bbox[3]):
        GRID[c].append(o)
        if o.cls == "HV_BUS":
            GRID_HV[c].append(o)

def remove_obstacle(o):
    for c in grid_cells(o.bbox[0], o.bbox[1], o.bbox[2], o.bbox[3]):
        for g in (GRID, GRID_HV):
            lst = g.get(c)
            if lst is not None:
                g[c] = [x for x in lst if x is not o]

def query_grid(g, x0, y0, x1, y1, seen, out):
    for c in grid_cells(x0, y0, x1, y1):
        for o in g.get(c, ()):
            if id(o) not in seen:
                seen.add(id(o))
                out.append(o)

def query(x0, y0, x1, y1):
    seen = set()
    out = []
    query_grid(GRID, x0, y0, x1, y1, seen, out)
    return out

def query_for(my_cls, x0, y0, x1, y1):
    """obstacles that could matter for a candidate of class my_cls.
    LV candidates: all obstacles within 1mm + HV obstacles within 6.5mm.
    HV candidates: all obstacles within 6.5mm."""
    seen = set()
    out = []
    if my_cls == "HV_BUS":
        query_grid(GRID, x0 - MAXCLR, y0 - MAXCLR, x1 + MAXCLR, y1 + MAXCLR, seen, out)
    else:
        m = mm(1.0)
        query_grid(GRID, x0 - m, y0 - m, x1 + m, y1 + m, seen, out)
        query_grid(GRID_HV, x0 - MAXCLR, y0 - MAXCLR, x1 + MAXCLR, y1 + MAXCLR, seen, out)
    return out

def item_layers(it):
    ls = []
    for l in (F_Cu, In1_Cu, In2_Cu, B_Cu):
        if it.IsOnLayer(l):
            ls.append(l)
    return tuple(ls)

print("building obstacle index...", flush=True)
t0 = time.time()
NETNAME = {}
for t in board.GetTracks():
    netname = t.GetNetname()
    cls = netclass_of(netname)
    if t.GetClass() == "PCB_VIA":
        shp = t.GetEffectiveShape(F_Cu)
        add_obstacle(Obstacle(shp, t.GetBoundingBox(), netname, cls,
                              (F_Cu, In1_Cu, In2_Cu, B_Cu),
                              hole=t.GetDrillValue(), holepos=t.GetPosition(), item=t))
    else:
        add_obstacle(Obstacle(t.GetEffectiveShape(t.GetLayer()), t.GetBoundingBox(),
                              netname, cls, (t.GetLayer(),), item=t))
for fp in board.GetFootprints():
    for pad in fp.Pads():
        netname = pad.GetNetname()
        cls = netclass_of(netname) if netname else "Default"
        hole = 0
        holepos = None
        if pad.GetDrillSize().x > 0:
            hole = max(pad.GetDrillSize().x, pad.GetDrillSize().y)
            holepos = pad.GetPosition()
        add_obstacle(Obstacle(pad.GetEffectiveShape(pad.GetLayer()), pad.GetBoundingBox(),
                              netname, cls, item_layers(pad), hole=hole, holepos=holepos))
print(f"  {sum(len(v) for v in GRID.values())} entries, {time.time()-t0:.1f}s", flush=True)

# HV filled zones are obstacles too (the 6.4/2.0 rules apply against fills).
# LV zone fills on inner layers are obstacles ONLY for same-layer track
# candidates (marked zone_fill): tracks must not fragment the pours, but
# through-vias are fine â€” the pour re-flows around them.
for z in board.Zones():
    if z.GetIsRuleArea() or not z.IsFilled():
        continue
    netname = z.GetNetname()
    cls = netclass_of(netname)
    for l in (F_Cu, In1_Cu, In2_Cu, B_Cu):
        if not z.IsOnLayer(l):
            continue
        fill = z.GetFilledPolysList(l)
        if fill.OutlineCount() == 0:
            continue
        if cls == "HV_BUS":
            add_obstacle(Obstacle(fill, z.GetBoundingBox(), netname, cls, (l,)))
        elif l in (In1_Cu, In2_Cu):
            o = Obstacle(fill, z.GetBoundingBox(), netname, cls, (l,))
            o.zone_fill = True
            add_obstacle(o)

# ---------------- clearance logic ----------------
def seg_pts(a, b):
    return [a, VECTOR2I((a.x + b.x) // 2, (a.y + b.y) // 2), b]

CLS_CLR = {name: mm(c["clearance"]) for name, c in CLASSES.items()}

def required_clearance(my_net, my_cls, my_pts, obs):
    """clearance in nm between candidate copper (net/class, sample pts) and obstacle"""
    if obs.net == my_net:
        return None  # same net: no constraint
    base = max(CLS_CLR.get(my_cls, CLS_CLR["Default"]), CLS_CLR.get(obs.cls, CLS_CLR["Default"]))
    if obs.zone_fill:
        base = max(base, mm(0.35))  # inner-layer pour clearance
    hv_a = my_cls == "HV_BUS"
    hv_b = obs.cls == "HV_BUS"
    clr = base
    if hv_a and not hv_b:
        if not obs_in(obs, HV_DOMAIN):
            clr = max(clr, mm(6.4))
    elif hv_b and not hv_a:
        if not in_areas(HV_DOMAIN, my_pts):
            clr = max(clr, mm(6.4))
    if (hv_a or hv_b) and clr > mm(0.6):
        # relaxations require BOTH items inside the relax area
        if in_areas(HV_RELAX, my_pts) and obs_in(obs, HV_RELAX):
            clr = mm(0.6)
        if in_areas(HV_RELAX_PIN, my_pts) and obs_in(obs, HV_RELAX_PIN):
            clr = mm(0.25)
    return clr

_obs_area_cache = {}
def obs_in(obs, areas):
    """obstacle intersects any polygon in the list (bbox-based approximation)"""
    key = (id(obs), id(areas))
    v = _obs_area_cache.get(key)
    if v is None:
        x0, y0, x1, y1 = obs.bbox
        pts = [VECTOR2I(x0, y0), VECTOR2I(x1, y1), VECTOR2I(x0, y1), VECTOR2I(x1, y0),
               obs.center,
               VECTOR2I((x0 + x1) // 2, y0), VECTOR2I((x0 + x1) // 2, y1),
               VECTOR2I(x0, (y0 + y1) // 2), VECTOR2I(x1, (y0 + y1) // 2)]
        v = in_areas(areas, pts)
        if not v:
            # bbox edge/diagonal segments crossing the polygon
            segs = [pcbnew.SEG(VECTOR2I(x0, y0), VECTOR2I(x1, y1)),
                    pcbnew.SEG(VECTOR2I(x0, y1), VECTOR2I(x1, y0)),
                    pcbnew.SEG(VECTOR2I(x0, y0), VECTOR2I(x1, y0)),
                    pcbnew.SEG(VECTOR2I(x0, y1), VECTOR2I(x1, y1)),
                    pcbnew.SEG(VECTOR2I(x0, y0), VECTOR2I(x0, y1)),
                    pcbnew.SEG(VECTOR2I(x1, y0), VECTOR2I(x1, y1))]
            for a in areas:
                if any(a.Collide(s, 0) for s in segs):
                    v = True
                    break
        _obs_area_cache[key] = v
    return v

def bbox_dist(bbox, x0, y0, x1, y1):
    dx = max(bbox[0] - x1, x0 - bbox[2], 0)
    dy = max(bbox[1] - y1, y0 - bbox[3], 0)
    return math.hypot(dx, dy)

MAXCLR = mm(6.5)

def cand_collide(obs_shape, kind, a, b, wr, clr):
    """collide candidate (seg a-b width wr | circle at a radius wr) vs an obstacle shape"""
    if isinstance(obs_shape, pcbnew.SHAPE_POLY_SET):
        if kind == "seg":
            # Collide(SEG) alone misses segments fully inside the polygon
            if obs_shape.Collide(pcbnew.SEG(a, b), clr + wr // 2):
                return True
            mid = VECTOR2I((a.x + b.x) // 2, (a.y + b.y) // 2)
            return any(obs_shape.Contains(p) for p in (a, mid, b))
        if obs_shape.Collide(a, clr + wr):
            return True
        return obs_shape.Contains(a)
    if kind == "seg":
        return obs_shape.Collide(pcbnew.SHAPE_SEGMENT(a, b, wr), clr)
    return obs_shape.Collide(pcbnew.SHAPE_CIRCLE(a, wr), clr)

def collides(kind, a, b, wr, layers, my_net, my_cls, my_pts):
    """exact collision of candidate vs indexed obstacles.
    kind='seg': segment a-b, width wr.  kind='circle': center a, radius wr."""
    if kind == "seg":
        x0, x1 = min(a.x, b.x) - wr // 2, max(a.x, b.x) + wr // 2
        y0, y1 = min(a.y, b.y) - wr // 2, max(a.y, b.y) + wr // 2
    else:
        x0, x1 = a.x - wr, a.x + wr
        y0, y1 = a.y - wr, a.y + wr
    is_via = len(layers) > 1
    for o in query_for(my_cls, x0, y0, x1, y1):
        if not any(l in o.layers for l in layers):
            continue
        if o.zone_fill and is_via:
            continue  # pours re-flow around through-vias
        clr = required_clearance(my_net, my_cls, my_pts, o)
        if clr is None:
            continue
        if bbox_dist(o.bbox, x0, y0, x1, y1) > clr + 1000:
            continue
        if cand_collide(o.shape, kind, a, b, wr, clr):
            return True
    return False

def via_hole_ok(pos, drill):
    x, y = pos.x, pos.y
    r = mm(3)
    for o in query(x - r, y - r, x + r, y + r):
        if o.hole and o.holepos is not None:
            d = math.hypot(o.holepos.x - x, o.holepos.y - y)
            if d < (o.hole + drill) / 2 + HOLE_TO_HOLE:
                return False
    return True

def in_barrier(kind, a, b, wr):
    for bshape in BARRIERS:
        if cand_collide(bshape, kind, a, b, wr, 0):
            return True
    return False

def on_board_box(x0, y0, x1, y1):
    m = EDGE_CLR + 1000
    return x0 >= BX0 + m and y0 >= BY0 + m and x1 <= BX1 - m and y1 <= BY1 - m

# ---------------- candidate primitives ----------------
def seg_ok(a, b, layer, net, cls, width):
    if a == b:
        return True
    h = width // 2
    if not on_board_box(min(a.x, b.x) - h, min(a.y, b.y) - h, max(a.x, b.x) + h, max(a.y, b.y) + h):
        return False
    if in_barrier("seg", a, b, width):
        return False
    return not collides("seg", a, b, width, (layer,), net, cls, seg_pts(a, b))

def via_size_for(cls, w):
    cp = class_params(cls)
    if cls == "HV_BUS" and w < mm(1.0):
        return mm(0.8), mm(0.4)
    return cp["via_dia"], cp["via_drill"]

def via_ok(p, net, cls, w=None):
    dia, drill = via_size_for(cls, w if w is not None else class_params(cls)["width"])
    r = dia // 2
    if not on_board_box(p.x - r, p.y - r, p.x + r, p.y + r):
        return False
    if in_barrier("circle", p, None, r):
        return False
    if not via_hole_ok(p, drill):
        return False
    return not collides("circle", p, None, r, (F_Cu, In1_Cu, In2_Cu, B_Cu), net, cls, [p])

# ---------------- path attempt machinery ----------------
class Plan:
    def __init__(self, via_w=None):
        self.tracks = []  # (a, b, layer, width)
        self.vias = []    # (pos,)
        self.via_w = via_w  # track width context for via sizing
    def cost(self):
        c = sum(math.hypot(b.x - a.x, b.y - a.y) for a, b, _, _ in self.tracks)
        return c + len(self.vias) * mm(2)

def path_on_layer(a, b, layer, net, cls, width):
    """try direct, L, Z paths from a to b on one layer; return list of segs or None"""
    if seg_ok(a, b, layer, net, cls, width):
        return [(a, b, layer, width)]
    c1 = VECTOR2I(a.x, b.y)
    c2 = VECTOR2I(b.x, a.y)
    for c in (c1, c2):
        if seg_ok(a, c, layer, net, cls, width) and seg_ok(c, b, layer, net, cls, width):
            return [(a, c, layer, width), (c, b, layer, width)]
    # Z shapes: horizontal-first and vertical-first with intermediate fractions
    for f in (0.5, 0.25, 0.75, 0.35, 0.65):
        mx = int(a.x + (b.x - a.x) * f)
        my = int(a.y + (b.y - a.y) * f)
        p1, p2 = VECTOR2I(mx, a.y), VECTOR2I(mx, b.y)
        if (seg_ok(a, p1, layer, net, cls, width) and seg_ok(p1, p2, layer, net, cls, width)
                and seg_ok(p2, b, layer, net, cls, width)):
            return [(a, p1, layer, width), (p1, p2, layer, width), (p2, b, layer, width)]
        p1, p2 = VECTOR2I(a.x, my), VECTOR2I(b.x, my)
        if (seg_ok(a, p1, layer, net, cls, width) and seg_ok(p1, p2, layer, net, cls, width)
                and seg_ok(p2, b, layer, net, cls, width)):
            return [(a, p1, layer, width), (p1, p2, layer, width), (p2, b, layer, width)]
    return None

ESCAPE_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
ESCAPE_DIST = [0.7, 1.2, 2.0, 3.2]

def stub_exits(p, layer, net, cls, width, toward=None):
    """points reachable from p by a short straight stub on `layer`.
    Returns [(q, stub_segs)] including (p, []) if p itself is in free space."""
    out = [(p, [])]
    dirs = list(ESCAPE_DIRS)
    if toward is not None:
        dirs.sort(key=lambda d: -(d[0] * (toward.x - p.x) + d[1] * (toward.y - p.y)))
    for d in (0.6, 1.0, 1.6, 2.4):
        for dx, dy in dirs:
            f = 0.7071 if dx and dy else 1.0
            q = VECTOR2I(p.x + mm(d * dx * f), p.y + mm(d * dy * f))
            if seg_ok(p, q, layer, net, cls, width):
                out.append((q, [(p, q, layer, width)]))
        if len(out) > 8:
            break
    return out

def escape_vias(p, layer, net, cls, width):
    """candidate (via_pos, stub_segments) pairs to move from `layer` to the other side near p"""
    out = []
    if via_ok(p, net, cls):
        out.append((p, []))
    for d in ESCAPE_DIST:
        for dx, dy in ESCAPE_DIRS:
            q = VECTOR2I(p.x + mm(d * dx * 0.7071 if dx and dy else d * dx),
                         p.y + mm(d * dy * 0.7071 if dx and dy else d * dy))
            if via_ok(q, net, cls) and seg_ok(p, q, layer, net, cls, width):
                out.append((q, [(p, q, layer, width)]))
                if len(out) >= 6:
                    return out
    return out

# ---------------- A* fallback ----------------
STEP = mm(0.5)

def astar_multi(starts, goals, net, cls, width, timeout=15.0, exact_steps=False, margin_mm=18,
                layers_allowed=(F_Cu, B_Cu)):
    """grid A* from any start (pt, layer, stubs) to any goal (pt, layer, stubs), F/B only"""
    all_pts = [s[0] for s in starts] + [g[0] for g in goals]
    raw_span = math.hypot(max(p.x for p in all_pts) - min(p.x for p in all_pts),
                          max(p.y for p in all_pts) - min(p.y for p in all_pts))
    margin = mm(6) if (exact_steps and raw_span < mm(8)) else mm(margin_mm)
    x0 = max(BX0 + EDGE_CLR + width, min(p.x for p in all_pts) - margin)
    y0 = max(BY0 + EDGE_CLR + width, min(p.y for p in all_pts) - margin)
    x1 = min(BX1 - EDGE_CLR - width, max(p.x for p in all_pts) + margin)
    y1 = min(BY1 - EDGE_CLR - width, max(p.y for p in all_pts) + margin)
    span = math.hypot(x1 - x0, y1 - y0)
    if exact_steps and raw_span < mm(8):
        STEP = mm(0.1)
    else:
        STEP = mm(0.25) if span < mm(45) else mm(0.5)
    nx = (x1 - x0) // STEP
    ny = (y1 - y0) // STEP
    if nx < 2 or ny < 2:
        return None
    blocked_cache = {}
    segok_cache = {}

    def cell_pt(cx, cy):
        return VECTOR2I(x0 + cx * STEP, y0 + cy * STEP)

    def cell_of(p):
        return (max(0, min(nx, round((p.x - x0) / STEP))), max(0, min(ny, round((p.y - y0) / STEP))))

    disc_r = width // 2 if exact_steps else width // 2 + STEP // 2

    def blocked(cx, cy, layer):
        key = (cx, cy, layer)
        v = blocked_cache.get(key)
        if v is None:
            p = cell_pt(cx, cy)
            v = in_barrier("circle", p, None, disc_r) or collides("circle", p, None, disc_r, (layer,), net, cls, [p])
            blocked_cache[key] = v
        return v

    def step_ok(c1, c2, layer):
        # exact collision test of the connecting segment between two free cells
        key = (c1, c2, layer) if c1 <= c2 else (c2, c1, layer)
        v = segok_cache.get(key)
        if v is None:
            a = cell_pt(c1[0], c1[1])
            b = cell_pt(c2[0], c2[1])
            v = (not in_barrier("seg", a, b, width)) and not collides(
                "seg", a, b, width, (layer,), net, cls, seg_pts(a, b))
            segok_cache[key] = v
        return v

    goal_map = {}
    for gpt, gl, gstubs in goals:
        gc = cell_of(gpt)
        goal_map.setdefault((gc[0], gc[1], gl), (gpt, gstubs))
    gcx = sum(g[0].x for g in goals) // len(goals)
    gcy = sum(g[0].y for g in goals) // len(goals)

    t_start = time.time()
    VIA_COST = mm(3)
    openq = []
    dist = {}
    prev = {}
    start_info = {}
    for spt, sl, sstubs in starts:
        sc = cell_of(spt)
        node = (sc[0], sc[1], sl)
        if dist.get(node, 1 << 62) > 0:
            dist[node] = 0
            start_info[node] = (spt, sstubs)
            heapq.heappush(openq, (0, node))
    goal = None
    pops = 0
    NB = [(1, 0, STEP), (-1, 0, STEP), (0, 1, STEP), (0, -1, STEP),
          (1, 1, int(STEP * 1.414)), (1, -1, int(STEP * 1.414)),
          (-1, 1, int(STEP * 1.414)), (-1, -1, int(STEP * 1.414))]
    while openq:
        pops += 1
        if pops % 256 == 0 and time.time() - t_start > timeout:
            print(f"    [astar TIMEOUT pops={pops} explored={len(dist)} {time.time()-t_start:.1f}s]", flush=True)
            return None
        f, cur = heapq.heappop(openq)
        if cur in goal_map:
            goal = cur
            break
        cx, cy, cl = cur
        d = dist[cur]
        for dx, dy, c in NB:
            nx2, ny2 = cx + dx, cy + dy
            if nx2 < 0 or ny2 < 0 or nx2 > nx or ny2 > ny:
                continue
            nxt = (nx2, ny2, cl)
            ndist = d + c
            if dist.get(nxt, 1 << 62) <= ndist:
                continue
            if nxt not in goal_map:
                if blocked(nx2, ny2, cl):
                    continue
                if exact_steps and not step_ok((cx, cy), (nx2, ny2), cl):
                    continue
            dist[nxt] = ndist
            prev[nxt] = cur
            p = cell_pt(nx2, ny2)
            h = int(math.hypot(p.x - gcx, p.y - gcy))
            heapq.heappush(openq, (ndist + h, nxt))
        # layer change through any allowed layer (inner layers cost extra)
        for ol in layers_allowed:
            if ol == cl:
                continue
            nxt = (cx, cy, ol)
            ndist = d + (VIA_COST if ol in (F_Cu, B_Cu) else 2 * VIA_COST)
            if dist.get(nxt, 1 << 62) > ndist:
                p = cell_pt(cx, cy)
                if via_ok(p, net, cls):
                    dist[nxt] = ndist
                    prev[nxt] = cur
                    h = int(math.hypot(p.x - gcx, p.y - gcy))
                    heapq.heappush(openq, (ndist + h, nxt))
    if goal is None:
        print(f"    [astar EXHAUSTED pops={pops} explored={len(dist)} {time.time()-t_start:.1f}s]", flush=True)
        return None
    nodes = [goal]
    while nodes[-1] in prev:
        nodes.append(prev[nodes[-1]])
    nodes.reverse()
    start_node = nodes[0]
    spt, sstubs = start_info[start_node]
    gpt, gstubs = goal_map[goal]
    pts = [(cell_pt(n[0], n[1]), n[2]) for n in nodes]

    plan = Plan()
    plan.tracks.extend(sstubs)
    runs = []
    cur_run = [pts[0][0]]
    cur_layer = pts[0][1]
    for p, l in pts[1:]:
        if l != cur_layer:
            runs.append((cur_run, cur_layer))
            plan.vias.append(cur_run[-1])
            cur_run = [cur_run[-1]]
            cur_layer = l
        else:
            cur_run.append(p)
    runs.append((cur_run, cur_layer))
    # replace grid entry/exit cell centers with the exact endpoints: the
    # endpoint cells were exempt from blocked checks, so their centers may
    # not be legal track points ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â never route through them
    if len(runs[0][0]) > 1:
        runs[0][0][0] = spt
    else:
        runs[0][0].insert(0, spt)
    if len(runs[-1][0]) > 1:
        runs[-1][0][-1] = gpt
    else:
        runs[-1][0].append(gpt)
    # smooth each run greedily with exact checks
    for run, l in runs:
        pts2 = [p for i, p in enumerate(run) if i == 0 or p != run[i - 1]]
        if len(pts2) < 2:
            continue
        i = 0
        simplified = [pts2[0]]
        while i < len(pts2) - 1:
            j = len(pts2) - 1
            while j > i + 1:
                if seg_ok(pts2[i], pts2[j], l, net, cls, width):
                    break
                j -= 1
            simplified.append(pts2[j])
            i = j
        for k in range(len(simplified) - 1):
            if simplified[k] != simplified[k + 1]:
                plan.tracks.append((simplified[k], simplified[k + 1], l, width))
    plan.tracks.extend(gstubs)
    return plan

# ---------------- endpoint resolution ----------------
def resolve_item(uid):
    it = board.GetItem(pcbnew.KIID(uid))
    if it is None:
        return None
    return it.Cast()

def endpoint_info(it, other_pos, json_pos, trackw):
    """returns (point, set_of_reachable_copper_layers, class_name, alt_points)"""
    cname = it.GetClass()
    if cname == "PAD":
        layers = set(item_layers(it))
        if it.GetDrillSize().x > 0:
            layers |= {F_Cu, B_Cu}
        c = it.GetPosition()
        alts = [c]
        try:
            sz = it.GetSize()
            ang = it.GetOrientation().AsRadians()
            inset = trackw // 2 + mm(0.06)
            ca, sa = math.cos(ang), math.sin(ang)
            for dx, dy in ((sz.x // 2 - inset, 0), (-(sz.x // 2 - inset), 0),
                           (0, sz.y // 2 - inset), (0, -(sz.y // 2 - inset))):
                if (dx and sz.x // 2 > inset + mm(0.05)) or (dy and sz.y // 2 > inset + mm(0.05)):
                    alts.append(VECTOR2I(int(c.x + dx * ca - dy * sa), int(c.y + dx * sa + dy * ca)))
        except Exception:
            pass
        return c, layers, cname, alts
    if cname == "PCB_VIA":
        return it.GetPosition(), {F_Cu, B_Cu}, cname, [it.GetPosition()]
    if cname in ("PCB_TRACK", "PCB_ARC"):
        s, e = it.GetStart(), it.GetEnd()
        ds = math.hypot(s.x - other_pos.x, s.y - other_pos.y)
        de = math.hypot(e.x - other_pos.x, e.y - other_pos.y)
        p, q = (s, e) if ds <= de else (e, s)
        L = math.hypot(e.x - s.x, e.y - s.y)
        alts = [p]
        if L > 1000:
            for back in (0.4, 0.8, 1.5, 3.0):
                f = min(mm(back) / L, 1.0)
                alts.append(VECTOR2I(int(p.x + (q.x - p.x) * f), int(p.y + (q.y - p.y) * f)))
        return p, {it.GetLayer()}, cname, alts
    if cname == "ZONE":
        # connect at the DRC-reported anchor, which lies in the fill
        layers = set()
        for l in (F_Cu, In1_Cu, In2_Cu, B_Cu):
            if it.IsOnLayer(l):
                layers.add(l)
        return json_pos, layers, cname, [json_pos]
    return None, None, cname, []

# ---------------- commit helpers ----------------
NEW_ITEMS = []

def commit_plan(net_item, plan, cls):
    net = net_item
    for a, b, layer, width in plan.tracks:
        if a == b:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(a)
        t.SetEnd(b)
        t.SetLayer(layer)
        t.SetWidth(width)
        t.SetNet(net)
        board.Add(t)
        NEW_ITEMS.append(t)
        add_obstacle(Obstacle(t.GetEffectiveShape(layer), t.GetBoundingBox(),
                              net.GetNetname(), cls, (layer,)))
    dia, drill = via_size_for(cls, plan.via_w if plan.via_w is not None else class_params(cls)["width"])
    for p in plan.vias:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(p)
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetDrill(drill)
        v.SetWidth(dia)
        v.SetLayerPair(F_Cu, B_Cu)
        v.SetNet(net)
        board.Add(v)
        NEW_ITEMS.append(v)
        add_obstacle(Obstacle(v.GetEffectiveShape(F_Cu), v.GetBoundingBox(),
                              net.GetNetname(), cls, (F_Cu, In1_Cu, In2_Cu, B_Cu),
                              hole=drill, holepos=p))

# ---------------- routing one edge ----------------
def route_edge(net_name, ua, ub, pos_a, pos_b, log):
    ia, ib = resolve_item(ua), resolve_item(ub)
    if ia is None or ib is None:
        log.append("  item lookup failed")
        return False
    net = ia.GetNet() if hasattr(ia, "GetNet") else ib.GetNet()
    cls = netclass_of(net_name)
    cp = class_params(cls)
    width = cp["width"]
    pa, la, ca, alts_a = endpoint_info(ia, VECTOR2I(pos_b[0], pos_b[1]), VECTOR2I(pos_a[0], pos_a[1]), width)
    pb, lb, cb, alts_b = endpoint_info(ib, VECTOR2I(pos_a[0], pos_a[1]), VECTOR2I(pos_b[0], pos_b[1]), width)
    if pa is None or pb is None:
        log.append(f"  unsupported endpoint types {ca}/{cb}")
        return False

    # 0a. two islands of the same zone (anchors coincide): connect between
    # the nearest vertex pair of two different fill islands
    if ca == "ZONE" and cb == "ZONE" and pa == pb:
        zlayer = next((l for l in (F_Cu, B_Cu, In1_Cu, In2_Cu) if ia.IsOnLayer(l)), None)
        fill = ia.GetFilledPolysList(zlayer) if zlayer is not None else None
        best = None
        if fill and fill.OutlineCount() >= 2:
            isl = []
            for i in range(fill.OutlineCount()):
                ol = fill.Outline(i)
                step = max(1, ol.PointCount() // 50)
                isl.append([ol.CPoint(k) for k in range(0, ol.PointCount(), step)])
            for i in range(len(isl)):
                for j in range(i + 1, len(isl)):
                    for p in isl[i]:
                        for q in isl[j]:
                            d2 = (p.x - q.x) ** 2 + (p.y - q.y) ** 2
                            if d2 > 0 and (best is None or d2 < best[0]):
                                best = (d2, p, q)
        if best is None:
            log.append("  zone-island edge: no vertex pair found")
            return False
        pa = VECTOR2I(best[1].x, best[1].y)
        pb = VECTOR2I(best[2].x, best[2].y)
        la = lb = {zlayer}
        alts_a, alts_b = [pa], [pb]
        log.append(f"  zone islands: bridging ({pa.x/1e6:.1f},{pa.y/1e6:.1f})->({pb.x/1e6:.1f},{pb.y/1e6:.1f})")

    # 0b. same-net zone taps: drop a via where a same-net filled zone covers an
    # endpoint on another layer. Only both-ends-tapped counts as success Ã¢â‚¬â€
    # a single tap may join a cluster that already contains the plane.
    def existing_tap(p):
        r = mm(0.1)
        for o in query(p.x - r, p.y - r, p.x + r, p.y + r):
            if o.net == net_name and o.hole and o.holepos is not None:
                if abs(o.holepos.x - p.x) < r and abs(o.holepos.y - p.y) < r:
                    return True
        return False

    taps = 0
    for (p, lset) in ((pa, la), (pb, lb)):
        for zl, z in NET_ZONES.get(net_name, ()):
            if z.GetFilledPolysList(zl).OutlineCount() and z.GetFilledPolysList(zl).Contains(p):
                if zl in lset:
                    continue  # already same layer: connectivity should have it
                if existing_tap(p):
                    break  # tap already exists but the edge is still open: don't re-add, don't claim success
                if via_ok(p, net_name, cls):
                    plan = Plan()
                    plan.vias.append(p)
                    commit_plan(net, plan, cls)
                    log.append(f"  zone tap via at ({p.x/1e6:.2f},{p.y/1e6:.2f}) -> {board.GetLayerName(zl)}")
                    taps += 1
                    break
    if taps >= 2:
        return True

    # 0b. endpoints only reachable on inner layers (zone anchors): add an entry via
    entry_vias = []
    if not (la & {F_Cu, B_Cu}):
        if via_ok(pa, net_name, cls):
            entry_vias.append(pa)
            la = la | {F_Cu, B_Cu}
        else:
            # nudge nearby for a legal via spot inside the fill
            found = False
            for d in (0.6, 1.0, 1.6, 2.4, 3.2):
                for dx, dy in ESCAPE_DIRS:
                    q = VECTOR2I(pa.x + mm(d * dx), pa.y + mm(d * dy))
                    zs = [z for zl, z in NET_ZONES.get(net_name, ()) if zl in la and z.GetFilledPolysList(zl).Contains(q)]
                    if zs and via_ok(q, net_name, cls):
                        entry_vias.append(q)
                        pa = q
                        la = la | {F_Cu, B_Cu}
                        found = True
                        break
                if found:
                    break
            if not found:
                log.append("  no entry via for inner-layer endpoint A")
                return False
    if not (lb & {F_Cu, B_Cu}):
        if via_ok(pb, net_name, cls):
            entry_vias.append(pb)
            lb = lb | {F_Cu, B_Cu}
        else:
            found = False
            for d in (0.6, 1.0, 1.6, 2.4, 3.2):
                for dx, dy in ESCAPE_DIRS:
                    q = VECTOR2I(pb.x + mm(d * dx), pb.y + mm(d * dy))
                    zs = [z for zl, z in NET_ZONES.get(net_name, ()) if zl in lb and z.GetFilledPolysList(zl).Contains(q)]
                    if zs and via_ok(q, net_name, cls):
                        entry_vias.append(q)
                        pb = q
                        lb = lb | {F_Cu, B_Cu}
                        found = True
                        break
                if found:
                    break
            if not found:
                log.append("  no entry via for inner-layer endpoint B")
                return False
    if entry_vias:
        plan = Plan()
        plan.vias = list(entry_vias)
        commit_plan(net, plan, cls)

    if attempt_route(net, net_name, cls, width, pa, la, alts_a, pb, lb, alts_b, log):
        return True

    # 4. rip-up-and-reroute: remove LV tracks of other nets crossing the
    # corridor, retry; their nets re-enter the open list next DRC iteration.
    radius = width // 2 + mm(2.0)
    x0 = min(pa.x, pb.x) - radius
    y0 = min(pa.y, pb.y) - radius
    x1 = max(pa.x, pb.x) + radius
    y1 = max(pa.y, pb.y) + radius
    new_ids = {id(x) for x in NEW_ITEMS}
    ring = mm(1.8)
    victims = []
    hv_victims = []
    for o in query(x0 - ring, y0 - ring, x1 + ring, y1 + ring):
        if o.item is None or o.net == net_name:
            continue
        if id(o.item) in new_ids:
            continue  # never rip copper committed this run
        if o.net in PROTECTED:
            continue  # nets already completed in a previous run
        hit = cand_collide(o.shape, "seg", pa, pb, 2 * radius, 0)
        if not hit:
            # ring around each endpoint: pads boxed in on all sides
            hit = (cand_collide(o.shape, "circle", pa, None, ring, 0)
                   or cand_collide(o.shape, "circle", pb, None, ring, 0))
        if hit:
            (hv_victims if o.cls == "HV_BUS" else victims).append(o)
    if not victims and hv_victims:
        victims = hv_victims  # last resort: rip HV neighbours
    if not victims or len(victims) > 10:
        log.append(f"  rip-up not viable ({len(victims)} victims)")
        return False
    for o in victims:
        board.Remove(o.item)
        remove_obstacle(o)
    log.append(f"  ripped {len(victims)} items: " + ", ".join(sorted({o.net for o in victims})))
    if attempt_route(net, net_name, cls, width, pa, la, alts_a, pb, lb, alts_b, log):
        # immediately try to repair each victim net along another lane
        repaired = 0
        for o in victims:
            if o.item.GetClass() != "PCB_TRACK":
                continue
            vs, ve = o.item.GetStart(), o.item.GetEnd()
            vnet_item = board.FindNet(o.net)
            if vnet_item is None:
                continue
            vcls = netclass_of(o.net)
            vw = class_params(vcls)["width"]
            # repair must attach on the ripped track's own layer at both ends
            vlay = {o.item.GetLayer()}
            if attempt_route(vnet_item, o.net, vcls, vw, vs, vlay, [vs], ve, vlay, [ve], log):
                repaired += 1
        log.append(f"  victim repair: {repaired}/{len(victims)}")
        return True
    # restore
    for o in victims:
        board.Add(o.item)
        add_obstacle(o)
    log.append("  rip-up failed, victims restored")
    return False

def attempt_route(net, net_name, cls, width, pa, la, alts_a, pb, lb, alts_b, log):
    widths = [width]
    if cls == "HV_BUS":
        widths = [width, mm(2.0), mm(1.2), mm(0.6)]

    for w in widths:
        # 1. simple paths between connection points / stub exits on a common layer
        common = la & lb & {F_Cu, B_Cu}
        for l in common:
            ex_a = [(q, []) for q in alts_a] + stub_exits(pa, l, net_name, cls, w, toward=pb)
            ex_b = [(q, []) for q in alts_b] + stub_exits(pb, l, net_name, cls, w, toward=pa)
            pairs = [(qa, sa, qb, sb_) for qa, sa in ex_a for qb, sb_ in ex_b]
            pairs.sort(key=lambda t: math.hypot(t[0].x - t[2].x, t[0].y - t[2].y))
            for qa, sa, qb, sb_ in pairs[:24]:
                segs = path_on_layer(qa, qb, l, net_name, cls, w)
                if segs:
                    plan = Plan()
                    plan.tracks = sa + segs + sb_
                    if not any(a != b for a, b, _, _ in plan.tracks):
                        continue  # zero-length phantom: nothing would be committed
                    commit_plan(net, plan, cls)
                    log.append(f"  simple path w={w/1e6:.2f} ({len(plan.tracks)} segs)")
                    return True

        # 2. one-via plans: escape from one side, then simple path on the other layer
        for (src, sl, dst, dl) in ((pa, la, pb, lb), (pb, lb, pa, la)):
            for sl_layer in (x for x in (F_Cu, B_Cu) if x in sl):
                other = B_Cu if sl_layer == F_Cu else F_Cu
                if other not in dl:
                    continue
                for vp, stubs in escape_vias(src, sl_layer, net_name, cls, w):
                    for qd, sd in stub_exits(dst, other, net_name, cls, w, toward=vp)[:6]:
                        segs = path_on_layer(vp, qd, other, net_name, cls, w)
                        if segs:
                            plan = Plan()
                            plan.tracks = stubs + segs + sd
                            plan.vias = [vp]
                            commit_plan(net, plan, cls)
                            log.append(f"  via path w={w/1e6:.2f} ({len(plan.tracks)} segs)")
                            return True

    widths_astar = [width, mm(1.2), mm(0.6)] if cls == "HV_BUS" else widths
    for w in widths_astar:
        # 3. A* fallback, seeded from stub exits on each reachable layer
        starts = []   # (pt, layer, stub_segs)
        goals = []
        for l in (x for x in (F_Cu, B_Cu) if x in la):
            for q, s in stub_exits(pa, l, net_name, cls, w, toward=pb)[:5]:
                starts.append((q, l, s))
        for l in (x for x in (F_Cu, B_Cu) if x in lb):
            for q, s in stub_exits(pb, l, net_name, cls, w, toward=pa)[:5]:
                goals.append((q, l, s))
        if not starts or not goals:
            continue
        span = math.hypot(pa.x - pb.x, pa.y - pb.y)
        FB = (F_Cu, B_Cu)
        FBI = (F_Cu, B_Cu, In2_Cu)
        if span < mm(10):
            modes = [(False, 18, FB), (False, 45, FBI), (True, 18, FB)]
        else:
            modes = [(False, 18, FB), (False, 45, FBI)]
        for exact, mgn, lys in modes:
            plan = astar_multi(starts, goals, net_name, cls, w, timeout=12.0 if not exact else 20.0,
                               exact_steps=exact, margin_mm=mgn, layers_allowed=lys)
            if plan:
                ok = all(seg_ok(a, b, l, net_name, cls, w) or a == b for a, b, l, _ in plan.tracks)
                ok = ok and all(via_ok(p, net_name, cls, w) for p in plan.vias)
                if ok:
                    commit_plan(net, plan, cls)
                    log.append(f"  A* path w={w/1e6:.2f} exact={exact} ({len(plan.tracks)} segs, {len(plan.vias)} vias)")
                    return True
                log.append(f"  A* colliding plan rejected (w={w/1e6:.2f} exact={exact})")
            else:
                log.append(f"  A* failed/timeout (w={w/1e6:.2f} exact={exact})")
    return False

# ---------------- main ----------------
PROTECTED = set()
PROT_FILE = os.path.join(SP, "protected_nets.txt")

def main():
    drc_path = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
    with open(drc_path, encoding="utf-8") as f:
        j = json.load(f)
    net_re = re.compile(r"\[([^\]]*)\]")
    edges = []
    for u in j["unconnected_items"]:
        a, b = u["items"][0], u["items"][1]
        m = net_re.search(a["description"]) or net_re.search(b["description"])
        net = m.group(1) if m else "?"
        d = math.hypot(a["pos"]["x"] - b["pos"]["x"], a["pos"]["y"] - b["pos"]["y"])
        edges.append((d, net, a["uuid"], b["uuid"],
                      (mm(a["pos"]["x"]), mm(a["pos"]["y"])), (mm(b["pos"]["x"]), mm(b["pos"]["y"]))))
    edges.sort(key=lambda e: e[0])
    edges = edges[:limit]

    # protected nets: completed in earlier runs, minus anything still open now
    open_now = {e[1] for e in edges}
    if os.path.exists(PROT_FILE):
        for line in open(PROT_FILE, encoding="utf-8"):
            n = line.strip()
            if n and n not in open_now:
                PROTECTED.add(n)
    print(f"{len(PROTECTED)} protected nets", flush=True)

    done = failed = 0
    fails = []
    t_start = time.time()
    import gc
    for i, (d, net, ua, ub, posa, posb) in enumerate(edges):
        print(f"[{i+1}/{len(edges)}] {net} ({d:.1f}mm) ...", flush=True)
        log = []
        try:
            ok = route_edge(net, ua, ub, posa, posb, log)
        except Exception as ex:
            log.append(f"  EXC {type(ex).__name__}: {ex}")
            ok = False
        print(f"[{i+1}/{len(edges)}] {net} ({d:.1f}mm) {'OK' if ok else 'FAIL'}"
              + "".join("\n" + s for s in log), flush=True)
        if ok:
            with open(PROT_FILE, "a", encoding="utf-8") as pf:
                pf.write(net + "\n")
        if i % 25 == 24:
            safe_save(board)
            gc.collect()
            print(f"  [checkpoint saved at {i+1}]", flush=True)
        if ok:
            done += 1
        else:
            failed += 1
            fails.append((net, d))
    print(f"\nrouted {done}, failed {failed}, {time.time()-t_start:.0f}s", flush=True)
    if fails:
        print("failed edges:")
        for net, d in fails:
            print(f"  {net} ({d:.1f}mm)")
    print("saving board...", flush=True)
    safe_save(board)
    print("saved.", flush=True)

if __name__ == "__main__":
    main()
