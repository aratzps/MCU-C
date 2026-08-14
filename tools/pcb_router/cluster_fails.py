"""Cluster unconnected-edge endpoints spatially to find congestion hotspots."""
import json, sys, math, collections

drc = json.load(open(sys.argv[1], encoding="utf-8"))
pts = []
for u in drc["unconnected_items"]:
    for it in u["items"]:
        pts.append((it["pos"]["x"], it["pos"]["y"]))

# greedy clustering with 12mm linkage
clusters = []
for p in pts:
    for c in clusters:
        if any(math.hypot(p[0] - q[0], p[1] - q[1]) < 12 for q in c):
            c.append(p)
            break
    else:
        clusters.append([p])
# merge pass
merged = True
while merged:
    merged = False
    for i in range(len(clusters)):
        for j in range(i + 1, len(clusters)):
            if any(math.hypot(a[0] - b[0], a[1] - b[1]) < 12 for a in clusters[i] for b in clusters[j]):
                clusters[i] += clusters[j]
                del clusters[j]
                merged = True
                break
        if merged:
            break

clusters.sort(key=len, reverse=True)
for c in clusters[:12]:
    xs = [p[0] for p in c]
    ys = [p[1] for p in c]
    print(f"{len(c):4d} endpoints in x {min(xs):6.1f}-{max(xs):6.1f}, y {min(ys):6.1f}-{max(ys):6.1f}")
print(f"total {len(pts)} endpoints, {len(clusters)} clusters")
