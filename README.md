# cardpcb-anime-brutalist

把 **动漫粗野主义（anime-brutalist）艺术卡** 做成 **嘉立创EDA（专业版）PCB** 的端到端方法。

> 作者：**Jiemanosh** · License：MIT · 主页：<https://github.com/Jiemanosh/cardpcb-anime-brutalist>

把"插画 / 大字 / 歌词 / 专辑封面风格图形"做成一块真实可打样的 PCB 艺术卡：七层可编辑 SVG
驱动设计，再用嘉立创EDA 的图元 API 把插画/文字/色块转成 PCB 矢量几何（丝印层、沉金铜层 +
阻焊开窗、黑色阻焊、圆角板框、客编丝印）。

本项目实战卡：`91×60mm` B 面艺术卡 —— 整板 sim3 黑丝印 + "15" 沉金 + 黑色阻焊 + 2mm 圆角板框
+ 嘉立创客编丝印，审美取自 Khalil Fong（方大同）《15 / Soul Boy 2006》专辑美学。

---

## 这个 skill 解决什么

- **设计语言**：动漫粗野主义编辑海报的七层 SVG 规范（五色、字体、叙事闭环、自审清单）。
- **PCB 落地管线（核心）**：把任意 PNG/插画转成 `pcb_PrimitiveImage` 矢量几何——
  `convertImageToComplexPolygon` 的"四零魔咒" + `create` 的"包围盒拉伸" + 精确 mm↔mil 坐标框架。
- **工艺技法**：沉金（铜+阻焊开窗双图元）、黑色阻焊（`modifyLayer`）、圆角板框（CLI）、客编丝印（CLI）。
- **避坑**：20 个真实踩过的坑（桥接/daemon、僵尸图元、3D 顶点预算、客编取不到……）。

---

## 目录结构

```
cardpcb-anime-brutalist/
├── SKILL.md                        # 技能主体（WorkBuddy 读取）
├── README.md
├── LICENSE
├── .gitignore
├── references/
│   ├── design-language.md          # 七层 SVG 规范 / 五色 / 字体 / 叙事闭环 / 自审
│   ├── coordinate-framework.md     # mm ↔ mil ↔ 0.1mil 精确换算与镜像约定
│   ├── image-primitive-pipeline.md # 图像图元管线（四零魔咒 + create 拉伸 + 回读 IoU）
│   ├── cli-cookbook.md             # easyeda-agent CLI 速查
│   └── traps.md                    # 20 个坑
├── assets/
│   ├── layer-template.svg          # 七层可编辑 SVG 模板
│   ├── example-cardpcb-sideb.svg   # B 面实战范例（含主体抠图）
│   └── pipeline-example.py         # 通用化落地脚本（丝印/沉金 + 回读校验）
```

---

## 作为 WorkBuddy 技能安装

把整个目录复制到用户技能目录即可被 WorkBuddy 自动加载：

```bash
# Windows (PowerShell)
Copy-Item -Recurse cardpcb-anime-brutalist "$env:USERPROFILE\.workbuddy\skills\cardpcb-anime-brutalist"
```

重启 WorkBuddy 后，当你提到"艺术贺卡板 / 把插画做成 PCB 丝印 / cardPCB / 动漫粗野主义 PCB /
嘉立创EDA 矢量丝印或沉金"时，技能会被自动触发。

---

## 独立使用（不依赖 WorkBuddy）

1. 设计：照 `references/design-language.md` + `assets/layer-template.svg` 画七层 SVG。
2. 渲染：`resvg_py` 把 SVG 渲成 PNG（中文需挂载霞鹜文楷 ttf）。
3. 栅格化取墨：`alpha>128` 得 mask；细笔画 80px/mm、整板 40px/mm。
4. 落地：`assets/pipeline-example.py` 的 `create_image()` / `create_enig()` 连嘉立创EDA
   桥接（`localhost:49620`，需装 `run-api-gateway.eext`）或 `easyeda debug exec` 执行 JS。
5. 校验：回读 `complexPolygon` → 逆变换栅格化 → 与源 mask 算 IoU（整板 ≥0.95、单元素 ≥0.98）。
6. 持久化：`pcb save` → `doc reload` → 再读一遍确认零衰减。

坐标换算、CLI 命令、踩坑细节见 `references/`。

---

## 依赖

- Python：`numpy`, `Pillow`, `resvg_py`（SVG 源需要）, `scipy`（沉金开窗膨胀需要）
- 嘉立创EDA 专业版 + `run-api-gateway.eext` 扩展（桥接）或 `easyeda-agent` CLI（daemon）

---

## License

MIT —— 见 [LICENSE](LICENSE)。
