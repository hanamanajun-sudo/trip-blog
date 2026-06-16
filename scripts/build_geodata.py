#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Natural Earth 50m 국가 경계에서 특정 나라 폴리곤을 추출·단순화해
geodata/{ISO}.geo.json (FeatureCollection, properties.name=ISO) 으로 저장.

사용: python3 scripts/build_geodata.py USA CAN MEX
원본: ne_50m_admin_0_countries.geojson (ADM0_A3 기준 매칭)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEODIR = os.path.join(HERE, "geodata")
SRC = os.environ.get("NE_SRC", "/tmp/ne_50m.geojson")
EPS = 0.05          # Douglas-Peucker 허용오차(도)
MIN_RING = float(os.environ.get("MINRING", "0.4"))  # 이 둘레(도) 미만 작은 섬 제외
# BBOX="minlon,minlat,maxlon,maxlat" 설정 시 중심이 이 창 밖인 폴리곤은 제외
# (예: 미국 본토만 — 알래스카/하와이는 날짜변경선·원거리라 투영 왜곡)
_b = os.environ.get("BBOX")
BBOX = tuple(float(x) for x in _b.split(",")) if _b else None


def in_bbox(ring):
    if BBOX is None:
        return True
    cx = sum(p[0] for p in ring) / len(ring)
    cy = sum(p[1] for p in ring) / len(ring)
    return BBOX[0] <= cx <= BBOX[2] and BBOX[1] <= cy <= BBOX[3]


def dp(points, eps):
    """Douglas-Peucker. points: [(x,y),...] (마지막=처음, 닫힌 링)."""
    if len(points) < 4:
        return points
    # 닫힌 링: 시작/끝 고정점 기준 분할
    dmax, idx = 0.0, 0
    a, b = points[0], points[-1]
    for i in range(1, len(points) - 1):
        d = _perp(points[i], a, b)
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        left = dp(points[:idx + 1], eps)
        right = dp(points[idx:], eps)
        return left[:-1] + right
    return [a, b]


def _perp(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    cx, cy = ax + t * dx, ay + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def ring_len(ring):
    s = 0.0
    for i in range(1, len(ring)):
        s += abs(ring[i][0] - ring[i - 1][0]) + abs(ring[i][1] - ring[i - 1][1])
    return s


def simplify_polygon(poly):
    out = []
    for ring in poly:
        pts = [(round(x, 6), round(y, 6)) for x, y in ring]
        if ring_len(pts) < MIN_RING:
            continue
        s = dp(pts, EPS)
        if len(s) >= 4:
            out.append([[x, y] for x, y in s])
    return out


def extract(iso, features):
    feat = None
    for f in features:
        p = f.get("properties", {})
        if p.get("ADM0_A3") == iso or p.get("ISO_A3") == iso or p.get("SOV_A3") == iso \
                or p.get("SU_A3") == iso:
            feat = f
            break
    if feat is None:
        print(f"  !! {iso} 못 찾음")
        return False
    geom = feat["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    new = []
    for poly in polys:
        if poly and not in_bbox(poly[0]):
            continue
        sp = simplify_polygon(poly)
        if sp:
            new.append(sp)
    out = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"name": iso},
         "geometry": {"type": "MultiPolygon", "coordinates": new}}]}
    path = os.path.join(GEODIR, f"{iso}.geo.json")
    with open(path, "w") as fp:
        json.dump(out, fp, separators=(",", ":"))
    print(f"  {iso}: {len(new)} polygon, {os.path.getsize(path)//1024}KB")
    return True


if __name__ == "__main__":
    with open(SRC) as fp:
        data = json.load(fp)
    feats = data["features"]
    for iso in sys.argv[1:]:
        extract(iso, feats)
