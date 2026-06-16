#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
나라 비교 시리즈용 '크기 비교 지도' SVG 4종 생성기.

씬:
  A) 한국이 대상국 옆에        (korea-beside)   : 한국을 대상국 동쪽 해안에 바짝 붙여 비교
  B) 한국이 대상국 안에        (korea-inside)
  C) 대상국이 동아시아 옆에     (beside-eastasia): 대상국을 한국 왼쪽에 바짝 붙여 비교
  D) 대상국이 한국 위에 포개짐   (over-eastasia)

규칙:
- 람베르트 정적방위도법(등적 투영)으로 면적 왜곡 없이 같은 축척.
- 맥락(주변국)은 단일 투영 중심으로 그려 국경이 맞물리게, 이동국은 자기 중심 투영 후 평행이동.
- 수도(★)는 '주인공 나라'만 표시. 주변국·한국은 나라 이름만(한국은 A/B에선 이름도 생략).
- 바다=연파랑(해안선 자동), 국경=흰 선, 동아시아 씬은 clipPath 창으로 크롭.
- 주인공 나라 한정으로 주요 도시·강·관광지(POI)를 A/B 씬에 표시.

외부 라이브러리 없이 표준 라이브러리만 사용. 사용: python3 scripts/make_country_maps.py brazil
"""
import json
import math
import os
import sys

R = 6371008.8
HERE = os.path.dirname(os.path.abspath(__file__))
GEODIR = os.path.join(HERE, "geodata")
OUTDIR = os.path.join(HERE, "..", "public", "images", "size")

NAMES = {
    "BRA": "브라질", "ARG": "아르헨티나", "BOL": "볼리비아", "PER": "페루",
    "COL": "콜롬비아", "VEN": "베네수엘라", "GUY": "가이아나", "SUR": "수리남",
    "PRY": "파라과이", "URY": "우루과이", "CHL": "칠레", "ECU": "에콰도르",
    "KOR": "한국", "PRK": "북한", "CHN": "중국", "JPN": "일본", "TWN": "대만",
    "RUS": "러시아", "MNG": "몽골", "VNM": "베트남", "LAO": "라오스",
    "MMR": "미얀마", "THA": "태국", "KHM": "캄보디아", "PHL": "필리핀",
}
CAPITALS = {  # ISO -> (한글명, lon, lat)
    "BRA": ("브라질리아", -47.882, -15.793),
    "COL": ("보고타", -74.072, 4.711),
    "ECU": ("키토", -78.468, -0.181),
    "PRY": ("아순시온", -57.576, -25.264),
    "KOR": ("서울", 126.978, 37.566),
}

# 동아시아 맥락: 주변국(중립)을 먼저, 한국을 마지막에 그려 위로 올림
EA_ISOS = ["RUS", "MNG", "MMR", "THA", "LAO", "VNM", "KHM", "PHL",
           "CHN", "TWN", "JPN", "PRK", "KOR"]
EA_WINDOW = (104.0, 21.0, 149.0, 47.0)
GAP_M = 20000.0  # beside 배치 간격 (20km, 바짝 붙임)

OCEAN = "#dbeafe"
LAND_NEUTRAL = "#e7e5e4"
LAND_FOCUS = "#93c5fd"
KOREA_RED = "#ef4444"
MOVE_ORANGE = "#f97316"
BORDER = "#ffffff"
INK = "#1e293b"
RIVER = "#0ea5e9"
SPOT = "#16a34a"


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


def laea(lon, lat, c):
    lon, lat, lon0, lat0 = map(math.radians, (lon, lat, c[0], c[1]))
    cosc = math.sin(lat0) * math.sin(lat) + math.cos(lat0) * math.cos(lat) * math.cos(lon - lon0)
    k = math.sqrt(max(0.0, 2.0 / (1.0 + cosc)))
    x = R * k * math.cos(lat) * math.sin(lon - lon0)
    y = R * k * (math.cos(lat0) * math.sin(lat) - math.sin(lat0) * math.cos(lat) * math.cos(lon - lon0))
    return x, y


def project(rings, c):
    return [[laea(p[0], p[1], c) for p in r] for r in rings]


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
    ch = word[-1]
    if "가" <= ch <= "힣":
        return "이" if (ord(ch) - 0xAC00) % 28 else "가"
    return "이(가)"


def eun(word):
    ch = word[-1]
    if "가" <= ch <= "힣":
        return "은" if (ord(ch) - 0xAC00) % 28 else "는"
    return "은(는)"


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


def render_scene(out_name, title, caption, anchor_isos, anchor_center, focus_iso,
                 move_iso, placement, move_fill, protagonist_iso,
                 side="right", window=None, poi=None, move_opacity=None,
                 move_label_size=13, width=940):
    anchor = {iso: project(load_polygons(iso), anchor_center) for iso in anchor_isos}
    focus_proj = anchor[focus_iso]

    if window:
        box = [[(window[0], window[1]), (window[2], window[1]),
                (window[2], window[3]), (window[0], window[3]), (window[0], window[1])]]
        ax0, ay0, ax1, ay1 = extent(project(box, anchor_center))
    else:
        ax0, ay0, ax1, ay1 = extent(sum(anchor.values(), []))
    a_cy = (ay0 + ay1) / 2

    m_rings = load_polygons(move_iso)
    m_center = bbox_center(m_rings)
    m_proj = project(m_rings, m_center)
    mx0, my0, mx1, my1 = extent(m_proj)
    m_cx, m_cy = (mx0 + mx1) / 2, (my0 + my1) / 2

    fx0, fy0, fx1, fy1 = extent(focus_proj)
    f_cy = (fy0 + fy1) / 2
    if placement == "inside":
        tx, ty = (fx0 + fx1) / 2 - m_cx, f_cy - m_cy
    elif side == "left":
        tx, ty = (fx0 - GAP_M) - mx1, f_cy - m_cy
    else:  # right
        tx, ty = (fx1 + GAP_M) - mx0, f_cy - m_cy
    m_placed = shift(m_proj, tx, ty)
    px0, py0, px1, py1 = extent(m_placed)

    tot_x0, tot_y0 = min(ax0, px0), min(ay0, py0)
    tot_x1, tot_y1 = max(ax1, px1), max(ay1, py1)
    margin, foot = 64, 58
    scale = (width - 2 * margin) / (tot_x1 - tot_x0)
    height = int((tot_y1 - tot_y0) * scale + 2 * margin + foot)
    ox = margin - tot_x0 * scale
    oy = margin + tot_y1 * scale

    def to_px(x, y):
        return ox + x * scale, oy - y * scale

    clip_px = None
    if window:
        cx0, cy0 = to_px(ax0, ay1)
        cx1, cy1 = to_px(ax1, ay0)
        clip_px = (cx0, cy0, cx1, cy1)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
         f'viewBox="0 0 {width} {height}" font-family="Pretendard, sans-serif">',
         f'<rect width="{width}" height="{height}" fill="{OCEAN}"/>']
    if clip_px:
        s.append(f'<clipPath id="win"><rect x="{clip_px[0]:.1f}" y="{clip_px[1]:.1f}" '
                 f'width="{clip_px[2]-clip_px[0]:.1f}" height="{clip_px[3]-clip_px[1]:.1f}"/></clipPath>')
    s.append(f'<text x="{width/2:.0f}" y="34" text-anchor="middle" font-size="21" '
             f'font-weight="700" fill="{INK}">{esc(title)}</text>')

    # 맥락(주변국)
    g = ' clip-path="url(#win)"' if clip_px else ''
    s.append(f'<g{g}>')
    for iso in anchor_isos:
        fill = KOREA_RED if iso == "KOR" else (LAND_FOCUS if iso == focus_iso else LAND_NEUTRAL)
        s.append(f'<path d="{path_d(anchor[iso], to_px)}" fill="{fill}" stroke="{BORDER}" stroke-width="0.8"/>')
    for iso in anchor_isos:
        if iso == "KOR" and move_iso == "KOR":
            continue  # (해당 없음)
        if iso == "KOR" and protagonist_iso != "KOR" and window is None:
            continue  # SA 씬엔 한국 없음
        lp = label_pt(anchor[iso], to_px, clip_px)
        if lp:
            col = "#7f1d1d" if iso == "KOR" else "#475569"
            fw = "700" if iso == focus_iso else "500"
            s.append(f'<text x="{lp[0]:.0f}" y="{lp[1]:.0f}" text-anchor="middle" '
                     f'font-size="12" font-weight="{fw}" fill="{col}">{NAMES.get(iso, iso)}</text>')
    s.append('</g>')

    # 이동국
    big = shoelace_area(m_proj) > shoelace_area(focus_proj)
    if move_opacity is not None:
        op = move_opacity
    else:
        op = 0.95 if placement == "beside" else (0.35 if big else 0.9)
    s.append(f'<path d="{path_d(m_placed, to_px)}" fill="{move_fill}" fill-opacity="{op}" '
             f'stroke="#9a3412" stroke-width="1.1"/>')
    if placement == "inside" and big:
        s.append(f'<path d="{path_d(focus_proj, to_px)}" fill="none" stroke="#7f1d1d" '
                 f'stroke-width="1.4" stroke-dasharray="3,2"/>')
    if move_iso != "KOR":  # 한국은 이름 라벨 생략
        mlp = label_pt(m_placed, to_px)
        if mlp:
            s.append(f'<text x="{mlp[0]:.0f}" y="{mlp[1]:.0f}" text-anchor="middle" font-size="{move_label_size}" '
                     f'font-weight="700" fill="#7c2d12">{NAMES.get(move_iso, move_iso)}</text>')

    # POI (주인공 나라 한정, 맥락 투영 사용)
    if poi:
        pc = anchor_center
        for nm, pts in poi.get("rivers", []):
            line = "M" + " L".join("%.1f,%.1f" % to_px(*laea(lo, la, pc)) for lo, la in pts)
            s.append(f'<path d="{line}" fill="none" stroke="{RIVER}" stroke-width="1.6" opacity="0.85"/>')
            mlo, mla = pts[len(pts) // 2]
            x, y = to_px(*laea(mlo, mla, pc))
            s.append(f'<text x="{x:.0f}" y="{y-3:.0f}" text-anchor="middle" font-size="10" '
                     f'font-style="italic" fill="{RIVER}">{esc(nm)}</text>')
        for nm, lo, la in poi.get("spots", []):
            x, y = to_px(*laea(lo, la, pc))
            s.append(f'<path d="M{x:.1f},{y-4:.1f} L{x+3.6:.1f},{y+2.5:.1f} L{x-3.6:.1f},{y+2.5:.1f} Z" '
                     f'fill="{SPOT}" stroke="#fff" stroke-width="0.6"/>')
            s.append(f'<text x="{x:.0f}" y="{y+15:.0f}" text-anchor="middle" font-size="10" '
                     f'font-weight="600" fill="{SPOT}">{esc(nm)}</text>')
        for nm, lo, la in poi.get("cities", []):
            x, y = to_px(*laea(lo, la, pc))
            s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="#334155" stroke="#fff" stroke-width="0.7"/>')
            s.append(f'<text x="{x+5:.0f}" y="{y+4:.0f}" font-size="10.5" fill="#334155">{esc(nm)}</text>')

    # 수도(주인공만)
    if protagonist_iso in CAPITALS:
        nm, lo, la = CAPITALS[protagonist_iso]
        if protagonist_iso == move_iso:
            mx, my = laea(lo, la, m_center)
            cx, cy = mx + tx, my + ty
        else:
            cx, cy = laea(lo, la, anchor_center)
        x, y = to_px(cx, cy)
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="#fde047" stroke="{INK}" stroke-width="1.2"/>')
        s.append(f'<text x="{x+6:.1f}" y="{y+4:.1f}" font-size="11" font-weight="700" fill="{INK}">★{esc(nm)}</text>')

    s.append(f'<text x="{width/2:.0f}" y="{height-20}" text-anchor="middle" font-size="16" '
             f'font-weight="600" fill="#334155">{esc(caption)}</text>')
    s.append('</svg>\n')

    os.makedirs(OUTDIR, exist_ok=True)
    path = os.path.join(OUTDIR, out_name)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(s))
    print(f"  {out_name}  {width}x{height}  {os.path.getsize(path)//1024}KB")


COUNTRIES = {
    "brazil": {
        "iso": "BRA",
        "neighbors": ["ARG", "BOL", "PER", "COL", "VEN", "GUY", "SUR", "PRY", "URY", "CHL", "ECU"],
        "ratio": "한국의 약 85배",
        "poi": {
            "cities": [("상파울루", -46.63, -23.55), ("리우데자네이루", -43.20, -22.91)],
            "spots": [("이구아수 폭포", -54.44, -25.69)],
            "rivers": [("아마존강", [(-72.5, -4.4), (-69, -4.2), (-65, -3.8), (-61, -3.3),
                                   (-58, -3.1), (-55, -2.4), (-52, -1.6), (-50.3, -0.6)])],
        },
    },
    "colombia": {
        "iso": "COL",
        "neighbors": ["VEN", "BRA", "PER", "ECU"],
        "ratio": "한국의 약 11배",
        "poi": {
            "cities": [("메데인", -75.581, 6.244), ("칼리", -76.532, 3.452)],
            "spots": [("카르타헤나", -75.479, 10.391)],
        },
    },
    "ecuador": {
        "iso": "ECU",
        "neighbors": ["COL", "PER"],
        "ratio": "한국의 약 2.8배",
        "poi": {
            "cities": [("과야킬", -79.889, -2.189)],
        },
    },
    "paraguay": {
        "iso": "PRY",
        "neighbors": ["ARG", "BRA", "BOL"],
        "ratio": "한국의 약 4배",
        "poi": {
            "spots": [("이타이푸 댐", -54.589, -25.408)],
        },
    },
}


def build(slug):
    cfg = COUNTRIES[slug]
    iso, kr, ratio, poi = cfg["iso"], NAMES[cfg["iso"]], cfg["ratio"], cfg.get("poi")
    sa = [iso] + cfg["neighbors"]
    sa_center = bbox_center(load_polygons(iso))
    ea_center = ((EA_WINDOW[0] + EA_WINDOW[2]) / 2, (EA_WINDOW[1] + EA_WINDOW[3]) / 2)
    print(f"[{slug}]")
    render_scene(f"{slug}-A-korea-beside.svg",
                 f"한국이 {kr} 옆에 가면 (실제 크기 비교)",
                 f"빨강이 한국 — {kr}{eun(kr)} {ratio}",
                 sa, sa_center, iso, "KOR", "beside", KOREA_RED, iso, side="right", poi=poi)
    render_scene(f"{slug}-B-korea-inside.svg",
                 f"한국이 {kr} 안에 들어가면",
                 f"빨강이 한국 — {kr} 영토에 쏙 들어간다 ({ratio})",
                 sa, sa_center, iso, "KOR", "inside", KOREA_RED, iso, poi=poi)
    render_scene(f"{slug}-C-beside-eastasia.svg",
                 f"{kr}{ga(kr)} 한국 옆에 오면 (동아시아 크기 비교)",
                 f"주황이 {kr} — 한국 바로 옆에 두고 비교",
                 EA_ISOS, ea_center, "KOR", iso, "beside", MOVE_ORANGE, iso, side="left",
                 window=EA_WINDOW, move_opacity=0.4)
    render_scene(f"{slug}-D-over-eastasia.svg",
                 f"{kr}{ga(kr)} 한국 위에 포개지면",
                 f"주황이 {kr} — 한반도를 덮고도 남는다",
                 EA_ISOS, ea_center, "KOR", iso, "inside", MOVE_ORANGE, iso,
                 window=EA_WINDOW, move_label_size=34)


if __name__ == "__main__":
    for t in (sys.argv[1:] or list(COUNTRIES)):
        build(t)
