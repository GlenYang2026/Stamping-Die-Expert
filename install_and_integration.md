# install_and_integration.md —— 安装与集成说明

## 一、在 WorkBuddy 中安装技能

1. 将本目录（`Stamping-Die-Expert/`）整体复制到 WorkBuddy 的技能目录：
   - 用户级：`~/.workbuddy/skills/Stamping-Die-Expert/`
   - 或项目级：`<项目>/.workbuddy/skills/Stamping-Die-Expert/`
2. 重启 / 刷新技能列表，技能由 `SKILL.md` 驱动（`skill.yaml` 仅作元数据，entrypoint 指向 SKILL.md）。
3. 无需联网、无需编译，纯文件 + Python 脚本。

## 二、Python 运行环境（可选，用于计算脚本与排样）

- **`stamping_calc.py`（核心计算）**：仅用 Python 标准库，**无需安装任何依赖**，Python 3.8+ 即可。
- **`auto_dxf_integration/nest_dxf.py`（DXF 自动排样）**：需 `ezdxf`（读取/写出 DXF），可选 `shapely`（旋转重叠检测）。
  安装（建议在虚拟环境）：
  ```bash
  python -m venv .venv && .venv\Scripts\activate      # Windows
  pip install ezdxf shapely
  ```

## 三、运行示例

```bash
# 直接算 T2 2mm 落料（周长 180mm）
python stamping_calc.py shear --material T2 --L 180 --t 2.0

# 排样利用率
python stamping_calc.py nesting --part_w 40 --part_l 60 --t 2.0 --rows 2

# DXF 自动排样（需 ezdxf）
python auto_dxf_integration/nest_dxf.py part.dxf --sheet 1000 2000 --gap 2.0
```

## 四、与 Excel 配合

- `stamping_calculator.csv` / `nesting_calculator.csv` / `quoting_template.csv` 可直接用 Excel 打开，按文件头注释里的公式按列展开批量计算。

## 五、说明

- 本包为基础工程估算工具。若需与 SolidWorks / NX 等商业 CAD 深度集成（API 驱动建模、CAM），属后续迭代方向，不在当前版本范围内。
- 材料参数以材料证书为准；文档中的 UTS / 密度 / 间隙等为典型示例值。
