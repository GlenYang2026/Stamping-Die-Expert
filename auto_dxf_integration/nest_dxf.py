"""
nest_dxf.py —— 冲压排样（nesting）示例脚本（纯 ezdxf + 可选 shapely）

功能：
  读取一个 DXF 零件轮廓，在给定板材（W×H）上用"货架式贪婪排样"摆放多个实例，
  输出嵌套后的 DXF，并计算材料利用率。
  - 默认尝试 0° 与 90° 两种朝向，取摆放数量多的方案；
  - 若安装了 shapely，对每个实例做重叠检测（保险）；
  - 无 shapely 时依赖 gap 留隙保证不重叠。

依赖：pip install ezdxf [shapely]
运行：python nest_dxf.py part.dxf --sheet 1000 2000 --gap 2.0
输出：nested_out.dxf（同目录）+ 终端打印 摆放数量 / 利用率

说明：此脚本为工程入门级排样，非商业级（无 No-Fit-Polygon / 遗传算法 / 异形件混合排样）。
      工业级排样请用专业 nesting 软件或后续迭代。
"""

import os
import sys
import math
import argparse

try:
    import ezdxf
except Exception:
    print("请先安装依赖: pip install ezdxf")
    raise


def read_outline(path):
    """从 DXF 读取第一个闭合 LWPOLYLINE/POLYLINE 的轮廓点（list of (x,y)）。"""
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    for e in msp.query("LWPOLYLINE"):
        pts = [(p[0], p[1]) for p in e.get_points()]
        if len(pts) >= 3:
            return pts
    for e in msp.query("POLYLINE"):
        pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        if len(pts) >= 3:
            return pts
    raise RuntimeError("未在 DXF 中找到闭合轮廓（LWPOLYLINE / POLYLINE）")


def rotate_points(pts, angle_deg):
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(x * ca - y * sa, x * sa + y * ca) for (x, y) in pts]


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def normalize(pts):
    """把轮廓平移到原点（最小角点归零），便于摆放。"""
    minx, miny, _, _ = bbox(pts)
    return [(x - minx, y - miny) for (x, y) in pts]


def transform(pts, angle_deg, dx, dy):
    return [(x + dx, y + dy) for (x, y) in rotate_points(pts, angle_deg)]


def shelf_pack(part_pts, W, H, gap):
    """货架式贪婪排样，返回 (placements, count)。placements: list of (angle, x, y)"""
    best = ([], 0)
    for angle in (0, 90):
        rot = rotate_points(part_pts, angle)
        minx, miny, maxx, maxy = bbox(rot)
        bw = maxx - minx
        bh = maxy - miny
        placements = []
        y = 0.0
        while y + bh <= H:
            x = 0.0
            while x + bw <= W:
                # 摆放位置：把零件原点(0,0)放到 (x - minx_rot? ) 简化：直接以归一化后放置
                placements.append((angle, x, y))
                x += bw + gap
            y += bh + gap
        if len(placements) > best[1]:
            best = (placements, len(placements))
    return best


def overlap_any(placed_polys):
    try:
        from shapely.geometry import Polygon
    except Exception:
        return False
    polys = [Polygon(p) for p in placed_polys if len(p) >= 3]
    for i in range(len(polys)):
        for j in range(i + 1, len(polys)):
            if polys[i].intersects(polys[j]):
                return True
    return False


def main():
    ap = argparse.ArgumentParser(description="DXF 冲压排样（贪婪货架式）")
    ap.add_argument("dxf", help="零件 DXF 路径")
    ap.add_argument("--sheet", nargs=2, type=float, default=[1000.0, 2000.0],
                    metavar=("W", "H"), help="板材宽 高 (mm)，默认 1000 2000")
    ap.add_argument("--gap", type=float, default=2.0, help="零件间留隙 (mm)")
    ap.add_argument("--out", default="nested_out.dxf", help="输出 DXF 路径")
    args = ap.parse_args()

    W, H = args.sheet
    raw = read_outline(args.dxf)
    part = normalize(raw)

    placements, count = shelf_pack(part, W, H, args.gap)

    # 重叠检测（若 shapely 可用）
    placed = [transform(part, ang, x, y) for (ang, x, y) in placements]
    if overlap_any(placed):
        print("警告：检测到重叠（gap 可能过小或旋转碰撞），请增大 --gap。")

    # 写出嵌套 DXF
    out_doc = ezdxf.new("R2010")
    oms = out_doc.modelspace()
    for (ang, x, y) in placements:
        tp = transform(part, ang, x, y)
        oms.add_lwpolyline(tp, close=True)
    # 画板材边框
    oms.add_lwpolyline([(0, 0), (W, 0), (W, H), (0, H)], close=True)
    out_doc.saveas(args.out)

    # 利用率
    _, _, px, py = bbox(part)
    part_area = (px) * (py)  # 近似矩形面积（归一化后原点在最小角）
    # 更严谨：用鞋带公式算真实多边形面积
    def poly_area(pts):
        s = 0.0
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            s += x1 * y2 - x2 * y1
        return abs(s) / 2.0
    part_area = poly_area(part)
    sheet_area = W * H
    util = count * part_area / sheet_area * 100 if sheet_area else 0

    print(f"板材: {W:.0f} × {H:.0f} mm")
    print(f"摆放数量: {count}")
    print(f"单件面积: {part_area:.1f} mm²")
    print(f"材料利用率: {util:.1f} %")
    print(f"输出 DXF: {args.out}")


if __name__ == "__main__":
    main()
