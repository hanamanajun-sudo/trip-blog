#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
나라 비교 시리즈용 '크기 비교 지도' SVG 4종 생성기.

씬(scene)마다 4종을 만든다:
  A) 한국이 대상국 옆에        (korea-beside)
  B) 한국이 대상국 안에        (korea-inside)
  C) 대상국이 동아시아 옆에     (beside-eastasia)
  D) 대상국이 한국 위에 포개짐   (over-eastasia)

특징:
- 람베르트 정적방위도법(등적 투영)으로 면적 왜곡 없이 같은 축척 비교.
- 한 씬은 '맥락(주변국)'을 단일 투영 중심으로 그려 국경이 맞물리게 하고,
  멀리서 가져오는 '이동국'은 자기 중심으로 투영한 뒤 평행이동(면적 보존).
- 바다=연파랑(해안선 자동 노출), 국경=흰 선 + 주변국 이름 라벨, 수도 마커.
- 동아시아 씬은 clipPath 창으로 크롭.

외부 라이브러리 없이 표준 라이브러리만 사용한다.
사용: python3 scripts/make_country_maps.py brazil
"""
import json
import math
import os
import sys

R = 6371008.8
GEODIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geodata")
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "images", "size")

NAMES = {
    "BRA": "브라질", "ARG": "아르헨티나", "BOL": "볼리비아", "PER": "페루",
    "COL": "콜롬비아", "VEN": "베네수엘라", "GUY": "가이아나", "SUR": "수리남",
    "PRY": "파라과이", "URY": "우루과이", "CHL": "칠레", "ECU": "에콰도르",
    "KOR": "한국", "PRK": "북한", "CHN": "중국", "JPN": "일본", "TWN": "대만",
}
# 수도: ISO -> (한글명, lon, lat)
CAPITALS = {
    "BRA": ("브라질리아", -47.882, -15.793),
    "KOR": ("서울", 126.978, 37.566),
    "PRK": ("평양", 125.762, 39.039),
    "CHN": ("베이징", 116.407, 39.904),
    "JPN": ("도쿄", 139.692, 35.690),
}

EA_ISOS = ["CHN", "KOR", "PRK", "JPN", "TWN"]
EA_WINDOW = (104.0, 21.0, 149.0, 47.0)  # lon0,lat0,lon1,lat1

OCEAN = "#dbeafe"
LAND_NEUTRAL = "#e7e5e4"
LAND_FOCUS = "#93c5fd"
KOREA_RED = "#ef4444"
MOVE_ORANGE = "#f97316"
BORDER = "#ffffff"
INK = "#1e293b"


# ---------- geo ----------
def load_polygons(iso):
    with open(os.path.join(GEODIR, f"{iso}.geo.json"), encoding="utf-8") as f:
        data = json.load(f)
    rings = []
    for feat in data.get("features", [data]):
        geom = feat.get("geometry", feat)
        t = geom["type"]
        polys = [geom["coordinates"]] if t == "Polygon" else geom["coordinates"] if t == "MultiPolygon" else []
        for poly in polys:
            rings.append(poly[0])
    return rings


def bbox_center(rings):
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    return (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0


def laea(lon, lat, lon0, lat0):
    lon, lat, lon0, lat0 = map(math.radians, (lon, lat, lon0, lat0))
    cosc = math.sin(lat0) * math.sin(lat) + math.cos(lat0) * math.cos(lat) * math.cos(lon - lon0)
    k = math.sqrt(max(0.0, 2.0 / (1.0 + cosc)))
    x = R * k * math.cos(lat) * math.sin(lon - lon0)
    y = R * k * (math.cos(lat0) * math.sin(lat) - math.sin(lat0) * math.cos(lat) * math.cos(lon - lon0))
    return x, y


def project(rings, c):
    return [[laea(p[0], p[1], c[0], c[1]) for p in r] for r in rings]


def shift(proj, tx, ty):
    return [[(x + tx, y + ty) for x, y in r] for r in proj]


def extent(proj):
    xs = [p[0] for r in proj for p in r]
    ys = [p[1] for r in proj for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def shoelace_area(proj):
    a = 0.0
    for r in proj:
        s = 0.0
        for i in range(len(r) - 1):
            s += r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1]
        a += abs(s) / 2.0
    return a


# ---------- svg ----------
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def ga(word):
    """받침 여부로 주격조사 이/가 선택."""
    ch = word[-1]
    if "가" <= ch <= "힣":
        return "이" if (ord(ch) - 0xAC00) % 28 else "가"
    return "이(가)"


def path_d(proj, to_px):
    out = []
    for r in proj:
        pts = [to_px(x, y) for x, y in r]
        out.append("M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + " Z")
    return " ".join(out)


def label_pt(proj, to_px, clip=None):
    pts = [to_px(x, y) for r in proj for x, y in r]
    if clip:
        x0, y0, x1, y1 = clip
        pts = [p for p in pts if x0 <= p[0] <= x1 and y0 <= p[1] <= y1]
    if len(pts) < 3:
        return None
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def render_scene(out_name, title, caption,
                 anchor_isos, anchor_center, focus_iso,
                 move_iso, placement, move_fill,
                 window=None, width=940):
    """placement: 'beside' 또는 'inside'."""
    # 1) 맥락(주변국) 투영
    anchor = {iso: project(load_polygons(iso), anchor_center) for iso in anchor_isos}
    focus_proj = anchor[focus_iso]

    # 클립 창(동아시아) 또는 맥락 전체 범위
    if window:
        corners = [[(window[0], window[1]), (window[2], window[1]),
                    (window[2], window[3]), (window[0], window[3]), (window[0], window[1])]]
        ax0, ay0, ax1, ay1 = extent(project(corners, anchor_center))
    else:
        ax0, ay0, ax1, ay1 = extent(sum(anchor.values(), []))
    a_cx, a_cy = (ax0 + ax1) / 2, (ay0 + ay1) / 2

    # 2) 이동국 자기중심 투영
    m_rings = load_polygons(move_iso)
    m_proj = project(m_rings, bbox_center(m_rings))
    mx0, my0, mx1, my1 = extent(m_proj)
    m_cx, m_cy = (mx0 + mx1) / 2, (my0 + my1) / 2

    # 3) 배치 평행이동
    if placement == "inside":
        fx0, fy0, fx1, fy1 = extent(focus_proj)
        f_cx, f_cy = (fx0 + fx1) / 2, (fy0 + fy1) / 2
        tx, ty = f_cx - m_cx, f_cy - m_cy
    else:  # beside: 맥락 오른쪽에 배치
        gap = (ax1 - ax0) * 0.07
        tx = (ax1 + gap) - mx0
        ty = a_cy - m_cy
    m_placed = shift(m_proj, tx, ty)
    px0, py0, px1, py1 = extent(m_placed)

    # 4) 전체 범위 → 스케일
    tot_x0, tot_y0 = min(ax0, px0), min(ay0, py0)
    tot_x1, tot_y1 = max(ax1, px1), max(ay1, py1)
    margin, foot = 64, 58
    scale = (width - 2 * margin) / (tot_x1 - tot_x0)
    height = int((tot_y1 - tot_y0) * scale + 2 * margin + foot)
    ox = margin - tot_x0 * scale
    oy = margin + tot_y1 * scale  # y 반전

    def to_px(x, y):
        return ox + x * scale, oy - y * scale

    clip_px = None
    if window:
        cx0, cy0 = to_px(ax0, ay1)
        cx1, cy1 = to_px(ax1, ay0)
        clip_px = (cx0, cy0, cx1, cy1)

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}" font-family="Pretendard, sans-serif">')
    s.append(f'<rect width="{width}" height="{height}" fill="{OCEAN}"/>')
    if clip_px:
        s.append(f'<clipPath id="win"><rect x="{clip_px[0]:.1f}" y="{clip_px[1]:.1f}" '
                 f'width="{clip_px[2]-clip_px[0]:.1f}" height="{clip_px[3]-clip_px[1]:.1f}"/></clipPath>')
    s.append(f'<text x="{width/2:.0f}" y="34" text-anchor="middle" font-size="21" '
             f'font-weight="700" fill="{INK}">{esc(title)}</text>')

    # --- 맥락(주변국) 그룹 (창 클립) ---
    gattr = ' clip-path="url(#win)"' if clip_px else ''
    s.append(f'<g{gattr}>')
    for iso in anchor_isos:
        fill = KOREA_RED if iso == "KOR" else (LAND_FOCUS if iso == focus_iso else LAND_NEUTRAL)
        s.append(f'<path d="{path_d(anchor[iso], to_px)}" fill="{fill}" stroke="{BORDER}" stroke-width="0.8"/>')
    # 주변국 이름 라벨
    for iso in anchor_isos:
        lp = label_pt(anchor[iso], to_px, clip_px)
        if lp:
            col = "#7f1d1d" if iso == "KOR" else "#475569"
            fw = "700" if iso in (focus_iso, "KOR") else "500"
            s.append(f'<text x="{lp[0]:.0f}" y="{lp[1]:.0f}" text-anchor="middle" '
                     f'font-size="12" font-weight="{fw}" fill="{col}">{NAMES.get(iso, iso)}</text>')
    s.append('</g>')

    # --- 이동국 ---
    big = shoelace_area(m_proj) > shoelace_area(focus_proj)
    op = "0.55" if (placement == "inside" and big) else ("0.9" if placement == "inside" else "0.95")
    s.append(f'<path d="{path_d(m_placed, to_px)}" fill="{move_fill}" fill-opacity="{op}" '
             f'stroke="#9a3412" stroke-width="1.1"/>')
    # 포개짐 + 이동국이 더 클 때 포커스국 윤곽 다시 그려 식별
    if placement == "inside" and big:
        s.append(f'<path d="{path_d(focus_proj, to_px)}" fill="none" stroke="#7f1d1d" '
                 f'stroke-width="1.4" stroke-dasharray="3,2"/>')
    mlp = label_pt(m_placed, to_px)
    if mlp:
        s.append(f'<text x="{mlp[0]:.0f}" y="{mlp[1]:.0f}" text-anchor="middle" font-size="13" '
                 f'font-weight="700" fill="#7c2d12">{NAMES.get(move_iso, move_iso)}</text>')

    # --- 수도 마커 ---
    def capital(iso, proj, t=(0, 0)):
        if iso not in CAPITALS:
            return
        nm, lon, lat = CAPITALS[iso]
        cx, cy = laea(lon, lat, *(bbox_center(load_polygons(iso)) if iso == move_iso else anchor_center))
        cx, cy = cx + t[0], cy + t[1]
        if not (tot_x0 <= cx <= tot_x1 and tot_y0 <= cy <= tot_y1):
            return
        x, y = to_px(cx, cy)
        if clip_px and iso != move_iso and not (clip_px[0] <= x <= clip_px[2] and clip_px[1] <= y <= clip_px[3]):
            return
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="#fde047" stroke="{INK}" stroke-width="1.2"/>')
        s.append(f'<text x="{x+6:.1f}" y="{y+4:.1f}" font-size="11" font-weight="600" fill="{INK}">★{esc(nm)}</text>')

    for iso in anchor_isos:
        capital(iso, anchor[iso])
    capital(move_iso, m_placed, (tx, ty))

    # --- 캡션 ---
    s.append(f'<text x="{width/2:.0f}" y="{height-20}" text-anchor="middle" font-size="16" '
             f'font-weight="600" fill="#334155">{esc(caption)}</text>')
    s.append('</svg>\n')

    os.makedirs(OUTDIR, exist_ok=True)
    path = os.path.join(OUTDIR, out_name)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(s))
    print(f"  {out_name}  {width}x{height}")
    return path


COUNTRIES = {
    "brazil": {
        "iso": "BRA",
        "neighbors": ["ARG", "BOL", "PER", "COL", "VEN", "GUY", "SUR", "PRY", "URY", "CHL", "ECU"],
        "ratio": "한국의 약 85배",
    },
}


def build(slug):
    cfg = COUNTRIES[slug]
    iso, kr, ratio = cfg["iso"], NAMES.get(cfg["iso"]), cfg["ratio"]
    sa = [iso] + cfg["neighbors"]
    sa_center = bbox_center(load_polygons(iso))
    ea_center = ((EA_WINDOW[0] + EA_WINDOW[2]) / 2, (EA_WINDOW[1] + EA_WINDOW[3]) / 2)
    print(f"[{slug}]")
    render_scene(f"{slug}-A-korea-beside.svg",
                 f"한국이 {kr} 옆에 가면 (실제 크기 비교)",
                 f"빨강이 한국 — {kr}은(는) {ratio}",
                 sa, sa_center, iso, "KOR", "beside", KOREA_RED)
    render_scene(f"{slug}-B-korea-inside.svg",
                 f"한국이 {kr} 안에 들어가면",
                 f"빨강이 한국 — {kr} 영토에 쏙 들어간다 ({ratio})",
                 sa, sa_center, iso, "KOR", "inside", KOREA_RED)
    render_scene(f"{slug}-C-beside-eastasia.svg",
                 f"{kr}{ga(kr)} 한국(동아시아) 옆에 오면",
                 f"주황이 {kr} — 동아시아 전체와 견줘본 크기",
                 EA_ISOS, ea_center, "KOR", iso, "beside", MOVE_ORANGE, window=EA_WINDOW)
    render_scene(f"{slug}-D-over-eastasia.svg",
                 f"{kr}{ga(kr)} 한국 위에 포개지면",
                 f"주황이 {kr} — 한반도를 덮고도 남는다",
                 EA_ISOS, ea_center, "KOR", iso, "inside", MOVE_ORANGE, window=EA_WINDOW)


if __name__ == "__main__":
    targets = sys.argv[1:] or list(COUNTRIES)
    for t in targets:
        build(t)
