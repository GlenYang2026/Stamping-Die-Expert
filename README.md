# Stamping Die Expert —— 冲压模具专家技能包

冲压模具设计技能（**冲裁 / 弯曲 / 拉深 / 翻边**工艺计算、排样利用率、机台总力估算、报价、缺陷诊断与 DFM）。
覆盖铜、铝、钢、不锈钢、硅钢、高强钢等 14 种常用材料。v0.2.0。

## 结构说明

| 文件 | 用途 |
|---|---|
| `SKILL.md` | 技能入口与总说明（由它驱动） |
| `skill.yaml` | 元数据清单 |
| `materials_db.csv` | 材料库（UTS/屈服/τ系数/密度/延伸率/双边间隙/最小弯曲半径/卸料推件比例） |
| `stamping_calculator.csv` | 冲压力/总力/吨位/材料质量 计算模板（可导入 Excel） |
| `nesting_calculator.csv` | 排样利用率计算（料宽/步距/搭边/单件面积/利用率η） |
| `quoting_template.csv` | 报价模板（材料/机台/人工/模具/管理费/利润/税/损耗/良率） |
| `rules_and_defaults.md` | 常用规则与默认值（**双边**刀口间隙、τ系数、安全系数、机台档位、搭边、弯曲/拉深经验） |
| `process_formulas.md` | 工艺公式全集（冲裁含总力、弯曲、拉深、翻边）+ 算例 |
| `trial_die_checklist.md` | 试模/首件检查表 |
| `defect_guide.md` | 缺陷诊断库（毛刺/翘曲/起皱/拉裂/叠料… 原因+对策） |
| `design_guide.md` | 模具类型选择 + 冲压件 DFM 检查清单 |
| `glossary.md` | 术语表与公式索引 |
| `stamping_calc.py` | 可运行计算脚本（纯标准库，CLI + 函数库） |
| `strip_layout_examples/*.svg` | 排样/弯曲/拉深/间隙 示意图 |
| `auto_dxf_integration/nest_dxf.py` | 纯 ezdxf + shapely 贪婪排样（可运行，输出 DXF + 利用率） |
| `install_and_integration.md` | 安装与集成说明 |
| `demo_case_T2_2mm.md` | 冲裁算例（T2 2mm） |
| `demo_case_bending.md` | 弯曲算例（SPCC） |
| `demo_case_drawing.md` | 拉深算例（304 杯） |

## 快速上手

```bash
# 直接算（无需 Excel）
python stamping_calc.py shear --material T2 --L 180 --t 2.0
python stamping_calc.py bending --material SPCC --B 50 --t 1.5 --r 2
python stamping_calc.py drawing --material 304 --d 40 --h 30 --t 1.0
python stamping_calc.py nesting --part_w 40 --part_l 60 --t 2 --a 3 --a1 3 --rows 2

# DXF 自动排样（需 pip install ezdxf [shapely]）
python auto_dxf_integration/nest_dxf.py part.dxf --sheet 1000 2000 --gap 2.0
```

## 注意

- 本包为工程估算工具。材料参数以材料证书为准，文档中 UTS/密度/间隙等为典型示例值。
- 涉及安全风险（冲压吨位、模具吊装、氮气弹簧能量、高温材料加工）须现场确认前提条件。
- 间隙口径统一为**双边总间隙**（= 凹模 − 凸模），与其他资料对照时务必换算单边/双边。
