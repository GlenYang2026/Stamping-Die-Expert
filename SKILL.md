---
title: "冲压模具专家"
summary: "冲压模具设计技能——冲裁/弯曲/拉深/翻边工艺计算、排样利用率、机台吨位（含卸料/推件总力）、报价模板、缺陷诊断与DFM，含可运行 Python 计算脚本与 ezdxf 自动排样示例。覆盖铜/铝/钢/不锈钢/硅钢/高强钢等常用材料。"
author: "MoldYang"
license: "CC BY-NC-SA 4.0"
read_when:
  - 用户询问冲压模具、冲裁、排样、排料、级进模、落料、冲孔、弯曲、拉深相关问题
  - 用户需要计算冲压力/总力/吨位、材料利用率、步距、搭边
  - 用户需要冲压件报价（材料/机台/人工/模具摊销/管理费/利润税）
  - 用户提到 stamping, die design, 冲压, 刀口间隙, 搭边, 利用率, 回弹, 拉深比
  - 用户需要试模/首件检查表、缺陷诊断（毛刺/起皱/拉裂）
  - 用户需要把 DXF 自动排样(nesting)到板材
---

> 原创 WorkBuddy 技能，作者 **MoldYang（GlenYang2026）**。
> 许可证：CC BY-NC-SA 4.0（非商业使用，须署名，衍生须以相同方式共享）。
> 数据来源：材料 UTS / 屈服 / 间隙 / 最小弯曲半径等为行业典型**参考值**，正式量产以来料质保书实测为准；本技能为工程估算工具，不构成商业报价或安全结论的唯一依据。

# 冲压模具专家 (Stamping Die Expert)

> 技能包 v0.3.0，作者 GlenYang2026 / MoldYang。面向**铜、铝、钢、不锈钢、硅钢、高强钢**的冲裁 / 弯曲 / 拉深 / 翻边工艺计算、排样利用率、机台总力估算、报价，附带可运行 Python 计算脚本与 ezdxf 自动排样示例。v0.3.0 重点：弯曲力系数按材质 4 档分型、304 拉深量产 0.53 / 研发 0.50 双标准、材料库加硬度变体与质保书校正标记。

## 包含文件与用途

- `skill.yaml`：技能元数据清单（本技能由 SKILL.md 驱动）
- `materials_db.csv`：材料库（UTS / 屈服 / τ系数 / 密度 / 延伸率 / 双边间隙 / 最小弯曲半径 / 卸料推件比例 / **弯曲力系数 bending_c** / **数据源标记 data_source**；含 T2/304 硬度变体）
- `材料库校正说明.md`：如何按车间来料质保书实测值校正材料库（含填表模板与 hardness/横纹顺纹处理）
- `stamping_calculator.csv`：冲压力 / 总力 / 吨位 / 材料质量 计算模板（CSV，可导入 Excel）
- `nesting_calculator.csv`：排样利用率计算（料宽 / 步距 / 搭边 / 单件面积 / 利用率 η）
- `quoting_template.csv`：报价模板（材料 / 机台 / 人工 / 模具费 / 管理费 / 利润 / 税 / 损耗 / 良率）
- `rules_and_defaults.md`：常用规则与默认值（**双边**刀口间隙、τ系数、安全系数、机台档位、搭边、弯曲/拉深经验）
- `process_formulas.md`：工艺公式全集（冲裁含总力、弯曲、拉深、翻边）+ 算例
- `trial_die_checklist.md`：试模 / 首件检查表
- `defect_guide.md`：缺陷诊断库（原因 + 对策）
- `design_guide.md`：模具类型选择 + 冲压件 DFM 检查清单
- `glossary.md`：术语表与公式索引
- `stamping_calc.py`：可运行计算脚本（纯标准库，CLI + 函数库，输入 L/t/材料/工艺即出结果）
- `strip_layout_examples/simple_strip.svg`：排样示意图
- `strip_layout_examples/bending.svg` / `drawing.svg` / `clearance.svg`：工艺示意图
- `auto_dxf_integration/nest_dxf.py`：纯 ezdxf + shapely 贪婪排样（可运行，输出嵌套 DXF + 利用率）
- `install_and_integration.md`：安装与集成说明
- `demo_case_T2_2mm.md`：示例计算（T2 2mm）
- `demo_case_bending.md` / `demo_case_drawing.md`：弯曲 / 拉深算例

## 核心公式

### 冲裁（含总力 —— 选机台必须用总力）
- 剪切强度：`τ = tau_factor × UTS`（铜/铝 0.70，钢 0.80，不锈钢 0.70~0.75；见材料库）
- 纯冲裁力：`F_shear = L(剪切周长) × t(板厚) × τ`
- 卸料力 `F_strip = strip_pct × F_shear`；推件力 `F_eject = eject_pct × F_shear`
- **总冲压力**：`F_total = F_shear × (1 + strip_pct + eject_pct)` ← 选机台以此为准
- 换算吨位：`F_ton = F_N / 9806.65`（1 tf = 9806.65 N）
- 推荐机台吨位：`F_total_ton × 安全系数`（默认 1.25），向上取整到常用档位（5/10/20/30/50/60/80/100/160/200/250/315 t）

### 弯曲（详见 process_formulas.md）
- 弯曲力：`F_b = C × B × t² × σb / (r + t)`（90° V 形自由弯曲近似），**C 按材质分 4 档**：普通冷轧钢 1.33 / T2铜·软铝 1.15~1.20 / 软态304 1.45~1.50 / 厚料 t≥2.0 再 +0.08~0.12（见材料库 `bending_c`，正式工艺卡须分型）
- 中性层 `λ = r + k·t`；回弹随屈服↑、料厚↓而增大，硬态需过弯补偿
- 最小弯曲半径库值为**横纹(⊥纤维)**安全值；顺纹需放大 1.5~2 倍

### 拉深（详见 process_formulas.md）
- 毛坯直径（圆筒）：`D ≈ √(d² + 4dh)`（平底圆筒）
- 拉深力：`F_d ≈ 3.14 × d × t × σb × (D/d − 0.7)`（首次拉深）
- 拉深比 `m = d/D`：首次钢/不锈钢 0.50~0.55，铝/铜 0.55~0.62；超界需多次拉深
  - **304 首道量产锁死 m≥0.53**；m=0.50 仅研发试模（`drawing --rd`）可下探，禁止量产

### 刀口间隙（双边总间隙 = 凹模 − 凸模）
- 铜 T2（软）4%~8% t、（硬）6%~10% t；不锈钢 304（软）6%~10% t、（硬）8%~12% t
- 完整表见 `rules_and_defaults.md` / `materials_db.csv`

## 使用方式

1. **直接算（推荐）**：运行 `python stamping_calc.py --help`，按提示输入材料/尺寸/工艺，立即得吨位、机台档、总力、利用率、报价。无需开 Excel。
2. **Excel 批量**：用 `stamping_calculator.csv` 按列展开；排样用 `nesting_calculator.csv`；报价用 `quoting_template.csv`。
3. **自动排样**：在装了 `ezdxf`(+`shapely`) 的 Python 环境运行 `auto_dxf_integration/nest_dxf.py`，输出嵌套 DXF 与利用率（无需 FreeCAD）。

## 注意

- 本包为工程估算工具。与商业 CAD（SolidWorks / NX）深度集成需后续迭代。
- 材料参数以材料证书为准，文档与材料库中的 UTS / 屈服 / 间隙 / 弯曲半径等均为**典型参考值**（材料库 `data_source` 列已标注"参考值"）。正式量产请用车间来料质保书实测值校正——整理方法见 `材料库校正说明.md`。
- 材料库已内置 T2（软/半硬/硬）、304（2B软/1/2H硬）硬度变体，按需选用；未列的料号按校正说明补齐。
- **涉及安全风险（冲压吨位、模具吊装、氮气弹簧能量、高温材料加工）须现场确认前提条件（机台、模具、材料、环境）。**
- 间隙口径统一为**双边总间隙**，与其他资料对照时务必换算单边/双边。
