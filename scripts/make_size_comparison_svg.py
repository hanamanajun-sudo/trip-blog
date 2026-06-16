#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
나라 비교 시리즈용 '한국 지도 겹친 크기 비교' SVG 생성기.

실제 국경 좌표(GeoJSON)에 람베르트 정적방위도법(Lambert Azimuthal Equal-Area)을
적용해 면적이 왜곡되지 않게 투영한 뒤, 대상국 위에 한국을 같은 축척으로 겹쳐 그린다.
외부 라이브러리 없이 표준 라이브러리만 사용한다.

사용 예:
  python3 scripts/make_size_comparison_svg.py \
      --country /tmp/BRA.geo.json --country-name "브라질" \
      --ratio "한국의 약 85배" \
      --out public/images/brazil-vs-korea-size.svg
"""
import argparse
import json
import math

R = 6371008.8  # 지구 평균 반지름 (m)


def load_polygons(path):
    """GeoJSON에서 (lon, lat) 외곽 링 목록을 추출 (Polygon/MultiPolygon 지원)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rings = []
    feats = data.get("features", [data])
    for feat in feats:
        geom = feat.get("geometry", feat)
        gtype = geom["type"]
        coords = geom["coordinates"]
        if gtype == "Polygon":
            polys = [coords]
        elif gtype == "MultiPolygon":
            polys = coords
        else:
            continue
        for poly in polys:
            rings.append(poly[0])  # 외곽 링만 (구멍 무시 → 실루엣)
    return rings


def bbox_center(rings):
    xs = [p[0] for ring in rings for p in ring]
    ys = [p[1] for ring in rings for p in ring]
    return (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0


def laea(lon, lat, lon0, lat0):
    """람베르트 정적방위도법: (경도,위도)도 → (x,y) 미터. 면적 보존."""
    lon, lat = math.radians(lon), math.radians(lat)
    lon0, lat0 = math.radians(lon0), math.radians(lat0)
    cosc = (math.sin(lat0) * math.sin(lat)
            + math.cos(lat0) * math.cos(lat) * math.cos(lon - lon0))
    k = math.sqrt(max(0.0, 2.0 / (1.0 + cosc)))
    x = R * k * math.cos(lat) * math.sin(lon - lon0)
    y = R * k * (math.cos(lat0) * math.sin(lat)
                 - math.sin(lat0) * math.cos(lat) * math.cos(lon - lon0))
    return x, y


def project(rings, lon0, lat0):
    return [[laea(p[0], p[1], lon0, lat0) for p in ring] for ring in rings]


def extent(proj_rings):
    xs = [p[0] for ring in proj_rings for p in ring]
    ys = [p[1] for ring in proj_rings for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def rings_to_path(proj_rings, to_px):
    """투영 좌표(m) → SVG path 문자열. to_px(x,y)->(px,py)."""
    parts = []
    for ring in proj_rings:
        pts = [to_px(x, y) for x, y in ring]
        d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + " Z"
        parts.append(d)
    return " ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", required=True, help="대상국 GeoJSON 경로")
    ap.add_argument("--country-name", required=True, help="대상국 한글명")
    ap.add_argument("--ratio", required=True, help="비율 캡션 (예: '한국의 약 85배')")
    ap.add_argument("--korea", default="/tmp/KOR.geo.json", help="한국 GeoJSON 경로")
    ap.add_argument("--out", required=True, help="출력 SVG 경로")
    ap.add_argument("--width", type=int, default=900)
    args = ap.parse_args()

    # 각 나라를 '자기 중심'으로 등적 투영 → 둘 다 면적 보존, 동일 축척
    c_rings = load_polygons(args.country)
    k_rings = load_polygons(args.korea)
    c_lon0, c_lat0 = bbox_center(c_rings)
    k_lon0, k_lat0 = bbox_center(k_rings)
    c_proj = project(c_rings, c_lon0, c_lat0)
    k_proj = project(k_rings, k_lon0, k_lat0)

    # 대상국 범위를 기준으로 캔버스 스케일 결정
    cx0, cy0, cx1, cy1 = extent(c_proj)
    margin = 70
    W = args.width
    scale = (W - 2 * margin) / (cx1 - cx0)
    H = int((cy1 - cy0) * scale + 2 * margin + 60)  # 하단 캡션 공간

    cxc = (cx0 + cx1) / 2.0
    cyc = (cy0 + cy1) / 2.0
    cv_cx, cv_cy = W / 2.0, (H - 60) / 2.0

    def to_px(x, y):
        return cv_cx + (x - cxc) * scale, cv_cy - (y - cyc) * scale

    country_path = rings_to_path(c_proj, to_px)
    korea_path = rings_to_path(k_proj, to_px)  # 한국도 원점 중심 → 대상국 중앙에 겹침

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Pretendard, sans-serif">
  <rect width="{W}" height="{H}" fill="#f8fafc"/>
  <text x="{W/2:.0f}" y="34" text-anchor="middle" font-size="22" font-weight="700" fill="#1e293b">{args.country_name} vs 한국 실제 크기 비교</text>
  <path d="{country_path}" fill="#cbd5e1" stroke="#94a3b8" stroke-width="1"/>
  <path d="{korea_path}" fill="#ef4444" fill-opacity="0.85" stroke="#b91c1c" stroke-width="1.2"/>
  <text x="{cv_cx:.0f}" y="{cv_cy:.0f}" text-anchor="middle" font-size="13" font-weight="700" fill="#7f1d1d">한국</text>
  <text x="{W/2:.0f}" y="{H-22}" text-anchor="middle" font-size="17" font-weight="600" fill="#334155">빨간색이 한국 — {args.country_name}은(는) {args.ratio}</text>
</svg>
'''
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {args.out} ({W}x{H})")


if __name__ == "__main__":
    main()
