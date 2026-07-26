#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stamping_calc.py —— 冲压工艺可运行计算脚本（纯标准库，无需安装任何依赖）

子命令：
  shear    冲裁力 / 总力 / 吨位 / 机台档（含卸料+推件）
  bending  弯曲力 / 最小半径校核 / 中性层系数
  drawing  拉深毛坯直径 / 拉深比校核 / 拉深力 / 压边力
  nesting  排样料宽 / 步距 / 利用率
  quote    单件报价（材料/机台/人工/模具/管理/利润/税）

用法示例：
  python stamping_calc.py shear --material T2 --L 180 --t 2.0
  python stamping_calc.py bending --material SPCC --B 50 --t 1.5 --r 2
  python stamping_calc.py drawing --material 304 --d 40 --h 30 --t 1.0
  python stamping_calc.py nesting --part_w 40 --part_l 60 --t 2 --a 3 --a1 3 --rows 2
  python stamping_calc.py quote --mass_kg 0.00644 --machine_h 0.01 --labor_h 0.01

说明：材料性能从同目录 materials_db.csv 读取。所有值为工程估算，正式设计以材料证书/试模为准。
"""

import os
import sys
import csv
import math
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "materials_db.csv")
TIERS = [5, 10, 20, 30, 50, 60, 80, 100, 160, 200, 250, 315]
N_PER_TON = 9806.65


def load_materials():
    mats = {}
    with open(DB_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            mats[row["material"].strip().upper()] = row
    return mats


def get_mat(mats, name):
    key = name.strip().upper()
    if key in mats:
        return mats[key]
    # 模糊匹配（如 "304" 或 "stainless"）
    for k, v in mats.items():
        if key in k or key in v["grade"].upper():
            return v
    raise SystemExit(f"未知材料: {name}（库中有: {', '.join(sorted(mats))}）")


def f2(x, n=2):
    return f"{x:.{n}f}"


def pick_tier(ton):
    for t in TIERS:
        if ton <= t:
            return t
    return math.ceil(ton / 50) * 50  # 超 315 取就近 50 倍数


# ---------------- 冲裁 ----------------
def cmd_shear(args, mats):
    m = get_mat(mats, args.material)
    UTS = float(m["UTS_MPa"])
    tau_factor = args.tau_factor or float(m["tau_factor"])
    strip = args.strip_pct if args.strip_pct is not None else float(m["strip_pct"])
    eject = args.eject_pct if args.eject_pct is not None else float(m["eject_pct"])
    sf = args.sf
    tau = UTS * tau_factor
    F_s = args.L * args.t * tau
    F_total = F_s * (1 + strip + eject)
    ton_s = F_s / N_PER_TON
    ton_total = F_total / N_PER_TON
    tier = pick_tier(ton_total * sf)
    print("=== 冲裁力 / 总力 / 机台选型 ===")
    print(f"材料          : {m['material']} ({m['grade']})")
    print(f"UTS={f2(UTS)} MPa, τ系数={tau_factor}, τ={f2(tau)} MPa")
    print(f"剪切周长 L    : {f2(args.L)} mm, 板厚 t={f2(args.t)} mm")
    print(f"纯冲裁力      : {f2(F_s)} N = {f2(F_s/1000)} kN = {f2(ton_s)} t")
    print(f"卸料力({f2(strip*100)}%)+推件力({f2(eject*100)}%)")
    print(f"总冲压力      : {f2(F_total)} N = {f2(ton_total)} t   ← 选机台以此为准")
    print(f"×安全系数{sf}  : {f2(ton_total*sf)} t")
    print(f"建议机台档位  : {tier} t")


# ---------------- 弯曲 ----------------
K_TABLE = [(0.1,0.23),(0.2,0.27),(0.3,0.30),(0.4,0.33),(0.5,0.35),(0.8,0.39),
           (1.0,0.41),(1.5,0.44),(2.0,0.45),(3.0,0.47),(4.0,0.48),(5.0,0.50)]

def k_from_rt(rt):
    if rt >= 5:
        return 0.50
    # 线性插值，避免阶梯跳变
    pts = K_TABLE
    if rt <= pts[0][0]:
        return pts[0][1]
    for i in range(len(pts) - 1):
        r0, k0 = pts[i]
        r1, k1 = pts[i + 1]
        if r0 <= rt <= r1:
            return k0 + (k1 - k0) * (rt - r0) / (r1 - r0)
    return pts[-1][1]

def cmd_bending(args, mats):
    m = get_mat(mats, args.material)
    sigma = args.sigma or float(m["UTS_MPa"])
    rt = args.r / args.t
    # 4 档弯曲力系数（见 materials_db.csv bending_c 列；正式工艺卡须分型）
    c = float(m["bending_c"])
    thick_adj = ""
    if args.t >= 2.0:               # 厚料所有材料系数上浮 0.10
        c += 0.10
        thick_adj = " (t≥2.0mm, +0.10)"
    F_b = c * args.B * args.t**2 * sigma / (args.r + args.t)
    Rmin = float(m["min_bend_radius_t"]) * args.t
    k = k_from_rt(rt)
    print("=== 弯曲力 / 回弹校核 ===")
    print(f"材料          : {m['material']}  屈服={m['yield_MPa']} MPa")
    print(f"弯宽 B={f2(args.B)} mm, 料厚 t={f2(args.t)} mm, 内圆角 r={f2(args.r)} mm")
    print(f"r/t = {f2(rt)}")
    print(f"弯曲系数 C    : {f2(c)}{thick_adj}  (4档分型，见 materials_db)")
    print(f"弯曲力 F_b    : {f2(F_b)} N = {f2(F_b/1000)} kN")
    print(f"中性层系数 k  : {k}  → 中性层半径 ρ=r+k·t={f2(args.r + k*args.t)} mm")
    print(f"最小弯曲半径  : {f2(Rmin)} mm (库值 {m['min_bend_radius_t']}t，横纹⊥纤维)")
    print("   ※ 顺纹∥纤维折弯易裂，R_min 需放大 1.5~2 倍或改横纹排样")
    if args.r < Rmin:
        print("⚠️ 当前 r < R_min，弯曲会开裂！需放大圆角或换软料/退火。")
    else:
        print("✅ r ≥ R_min，弯曲可行。硬态料仍需注意回弹补偿。")


# ---------------- 拉深 ----------------
DRAW_LIMITS = {
    "SPCC":0.52,"SECC":0.52,"304":0.53,"301":0.53,"1050":0.58,"3003":0.58,
    "5052":0.57,"6061":0.56,"T2":0.58,"TU2":0.58,"H62":0.55,"C5191":0.55,
    "Silicon":0.55,"DP590":0.52,
}
def cmd_drawing(args, mats):
    m = get_mat(mats, args.material)
    sigma = float(m["UTS_MPa"])
    D = math.sqrt(args.d**2 + 4*args.d*args.h)
    mn = args.d / D
    F_d = math.pi * args.d * args.t * sigma * (D/args.d - 0.7)
    limit = DRAW_LIMITS.get(m["material"].upper(), 0.55)
    if args.rd:
        # 研发试模模式：量产门槛临时下探至 0.50，仅限试模，禁止批量量产
        print("⚠️【研发试模模式】量产门槛已临时放宽至 m≥0.50；此配置仅限试模，")
        print("   禁止批量量产！须配套退火/改善润滑/加大压边/放大凹模圆角。")
        limit = 0.50
    print("=== 拉深力 / 拉深比校核 ===")
    print(f"材料          : {m['material']}  UTS={f2(sigma)} MPa")
    print(f"直径 d={f2(args.d)} mm, 直壁高 h={f2(args.h)} mm, 料厚 t={f2(args.t)} mm")
    print(f"毛坯直径 D    : {f2(D)} mm")
    print(f"拉深比 m=d/D  : {f2(mn)}  (量产极限≈{DRAW_LIMITS.get(m['material'].upper(),0.55)}{' / 研发试模0.50' if args.rd else ''})")
    print(f"拉深力 F_d    : {f2(F_d)} N = {f2(F_d/1000)} kN = {f2(F_d/N_PER_TON)} t")
    print(f"压边力(估)    : {(0.02*F_d):.0f}~{(0.05*F_d):.0f} N 或按 q=1.5~3 MPa×法兰面积")
    if mn < limit:
        print(f"⚠️ m={f2(mn)} < 极限 {limit}，一次拉深会破裂！需多次拉深/加大圆角/退火。")
    else:
        print("✅ 拉深比在安全范围，可一次拉深（仍需压边+润滑）。")


# ---------------- 排样 ----------------
def cmd_nesting(args, mats):
    rows = args.rows
    B = args.part_w * rows + (rows + 1) * args.a
    P = args.part_l + args.a1
    part_area = args.part_w * args.part_l
    strip = B * P
    util = rows * part_area / strip * 100
    print("=== 排样利用率 ===")
    print(f"零件 {f2(args.part_w)}×{f2(args.part_l)} mm, 板厚 {f2(args.t)} mm")
    print(f"搭边 a={f2(args.a)} mm, 步距搭边 a1={f2(args.a1)} mm, 并排数 rows={rows}")
    print(f"料宽 B        : {f2(B)} mm")
    print(f"步距 P        : {f2(P)} mm")
    print(f"单件面积      : {f2(part_area)} mm²")
    print(f"材料利用率 η  : {f2(util)} %")
    if rows == 1:
        print("（提示：双排/斜排通常可再提升利用率，用 --rows 2 或改排样方式比对）")


# ---------------- 报价 ----------------
def cmd_quote(args, mats):
    # 直接成本
    material = args.mass_kg * args.material_price * (1 + args.scrap) / args.yield_rate
    machine = args.machine_h * args.machine_rate
    labor = args.labor_h * args.labor_rate
    mold = args.mold_amort
    surface = args.surface
    direct = material + machine + labor + mold + surface
    overhead = direct * args.overhead
    profit = (direct + overhead) * args.profit
    tax = (direct + overhead + profit) * args.tax
    unit = direct + overhead + profit + tax
    print("=== 单件报价（元）===")
    print(f"材料费  : {f2(material)}  (质量{args.mass_kg}kg × 单价{args.material_price} ×(1+损耗{args.scrap})/良率{args.yield_rate})")
    print(f"机台费  : {f2(machine)}  ({args.machine_h}h × {args.machine_rate}元/h)")
    print(f"人工费  : {f2(labor)}  ({args.labor_h}h × {args.labor_rate}元/h)")
    print(f"模具摊销: {f2(mold)}")
    print(f"表面处理: {f2(surface)}")
    print(f"直接成本: {f2(direct)}")
    print(f"管理费  : {f2(overhead)}  ({args.overhead*100}%)")
    print(f"利润    : {f2(profit)}  ({args.profit*100}%)")
    print(f"税      : {f2(tax)}  ({args.tax*100}%)")
    print(f"零件单价: {f2(unit)} 元/件")


def build_parser(mats):
    p = argparse.ArgumentParser(description="冲压工艺计算（纯标准库）")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("shear", help="冲裁力/吨位")
    s.add_argument("--material", required=True)
    s.add_argument("--L", type=float, required=True, help="剪切周长 mm")
    s.add_argument("--t", type=float, required=True, help="板厚 mm")
    s.add_argument("--tau_factor", type=float, default=None)
    s.add_argument("--strip_pct", type=float, default=None, help="卸料力比例")
    s.add_argument("--eject_pct", type=float, default=None, help="推件力比例")
    s.add_argument("--sf", type=float, default=1.25, help="安全系数")
    s.set_defaults(func=cmd_shear)

    b = sub.add_parser("bending", help="弯曲力")
    b.add_argument("--material", required=True)
    b.add_argument("--B", type=float, required=True, help="弯宽 mm")
    b.add_argument("--t", type=float, required=True, help="料厚 mm")
    b.add_argument("--r", type=float, required=True, help="内圆角 mm")
    b.add_argument("--sigma", type=float, default=None, help="抗拉强度，默认取库 UTS")
    b.set_defaults(func=cmd_bending)

    d = sub.add_parser("drawing", help="拉深")
    d.add_argument("--material", required=True)
    d.add_argument("--d", type=float, required=True, help="拉深远径 mm")
    d.add_argument("--h", type=float, required=True, help="直壁高 mm")
    d.add_argument("--t", type=float, required=True, help="料厚 mm")
    d.add_argument("--rd", action="store_true", help="研发试模模式：允许 m≥0.50（仅限试模，禁止量产）")
    d.set_defaults(func=cmd_drawing)

    n = sub.add_parser("nesting", help="排样利用率")
    n.add_argument("--part_w", type=float, required=True)
    n.add_argument("--part_l", type=float, required=True)
    n.add_argument("--t", type=float, required=True)
    n.add_argument("--a", type=float, default=3.0, help="侧搭边 mm")
    n.add_argument("--a1", type=float, default=3.0, help="步距搭边 mm")
    n.add_argument("--rows", type=int, default=1)
    n.set_defaults(func=cmd_nesting)

    q = sub.add_parser("quote", help="报价")
    q.add_argument("--mass_kg", type=float, required=True)
    q.add_argument("--material_price", type=float, default=30)
    q.add_argument("--scrap", type=float, default=0.05)
    q.add_argument("--yield_rate", type=float, default=0.95)
    q.add_argument("--machine_h", type=float, default=0.01)
    q.add_argument("--machine_rate", type=float, default=60)
    q.add_argument("--labor_h", type=float, default=0.01)
    q.add_argument("--labor_rate", type=float, default=35)
    q.add_argument("--mold_amort", type=float, default=2)
    q.add_argument("--surface", type=float, default=0)
    q.add_argument("--overhead", type=float, default=0.08)
    q.add_argument("--profit", type=float, default=0.10)
    q.add_argument("--tax", type=float, default=0.13)
    q.set_defaults(func=cmd_quote)
    return p


def main():
    mats = load_materials()
    parser = build_parser(mats)
    args = parser.parse_args()
    args.func(args, mats)


if __name__ == "__main__":
    main()
