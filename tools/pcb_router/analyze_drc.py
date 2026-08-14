"""Analyze DRC unconnected items by net."""
import json, re, collections, math, sys

path = sys.argv[1] if len(sys.argv) > 1 else None
with open(path, encoding="utf-8") as f:
    j = json.load(f)

net_re = re.compile(r"\[([^\]]*)\]")
edges = []
for u in j["unconnected_items"]:
    a, b = u["items"][0], u["items"][1]
    ma, mb = net_re.search(a["description"]), net_re.search(b["description"])
    net = ma.group(1) if ma else (mb.group(1) if mb else "?")
    d = math.hypot(a["pos"]["x"] - b["pos"]["x"], a["pos"]["y"] - b["pos"]["y"])
    edges.append({"net": net, "d": d, "a": a, "b": b})

by_net = collections.defaultdict(list)
for e in edges:
    by_net[e["net"]].append(e["d"])

print(f"{len(edges)} edges across {len(by_net)} nets")
rows = sorted(by_net.items(), key=lambda kv: -len(kv[1]))
for net, ds in rows:
    print(f"{net:36s} {len(ds):4d}  {min(ds):7.2f}..{max(ds):7.2f} mm")
