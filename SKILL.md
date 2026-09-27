---
name: cardpcb-anime-brutalist
description: "把“动漫粗野主义(anime-brutalist)艺术卡”做成嘉立创EDA(专业版)PCB 的端到端方法：七层可编辑 SVG 设计语言 + 把插画/文字转成 PCB 矢量图元的管线(丝印层/沉金铜层+阻焊开窗/黑色阻焊/圆角板框/客编丝印)。当用户要做“艺术贺卡板 / 把插画做成 PCB 丝印 / cardPCB / 动漫粗野主义 PCB / 嘉立创EDA 矢量丝印或沉金 / 在板子上铺满插画或歌词”时使用。"
license: MIT
metadata:
  author: Jiemanosh
  version: "1.0.0"
  homepage: "https://github.com/Jiemanosh/cardpcb-anime-brutalist"
  openclaw:
    requires:
      bins:
        - node
        - python
agent_created: true
---

# CardPCB · Anime-Brutalist PCB Art Card

把"动漫粗野主义编辑海报"的设计语言落到一块真实可打样的 PCB 艺术卡上：七层可编辑 SVG
驱动设计，再用嘉立创EDA 的图元 API 把插画/文字/色块转成 PCB 矢量几何（丝印层、沉金铜层、
阻焊开窗）。本 skill 是**整合版**——覆盖"从审美到可制造"的完整技法，不只是一句提示。

> 配套参考（按需读取，勿全量进上下文）：
> - `references/design-language.md` — 七层 SVG 规范、五色系统、字体、叙事闭环、自审清单
> - `references/coordinate-framework.md` — mm ↔ mil ↔ 0.1mil 局部坐标的精确换算与镜像约定
> - `references/image-primitive-pipeline.md` — `convertImageToComplexPolygon` 四零魔咒 + `create` 拉伸变换（已逐像素验证）
> - `references/cli-cookbook.md` — easyeda-agent CLI（daemon / outline-round / silk-add / save / reload / dump）
> - `references/traps.md` — 实操踩过的 20 个坑
>
> 相关 WorkBuddy 技能（可单独安装，本 skill 已涵盖核心，无需依赖）：
> `anime-brutalist-poster`（纯海报设计）、`easyeda-api`（EDA 官方 API 全集）、
> `easyeda-agent`（typed CLI 工程操作）、`jlcpcb`（打样/拼板/钢网）。

---

## 何时使用

- 用户要做一块"艺术卡 / 贺卡板 / 把插画铺满 PCB / 板子上印歌词或专辑封面风格图形"。
- 提到：动漫粗野主义、anime brutalist、编辑排版、高密度技术标签、丝印插画、沉金色块、
  嘉立创EDA 矢量丝印/沉金、cardPCB。
- 需要在 PCB 上精确放置大块插画、大字、色块，且要求"可回读验证、可持久化"。

---

## 工具链（必读）

两条在 EDA 客户端内执行 JS 的通道，二选一即可：

1. **桥接 HTTP**（本 skill 主用，已验证）：`localhost:49620/execute` POST `{code}`，
   EasyEDA 里装 `run-api-gateway.eext` 扩展自动连。适合跑任意 `eda.*` JS。
2. **easyeda-agent CLI**：`easyeda debug exec --code "..."` 在连接器上下文跑 JS；
   `easyeda health` / `pcb outline-round` / `pcb silk-add` / `pcb save` / `doc reload`
   是 typed 命令，优先用 typed 命令做"板框/丝印文字/保存"。

> 坐标单位铁律：PCB 一切 `eda.*` 几何单位都是 **mil**（1mm ≈ 39.37mil）。
> 丝印文字 `pcb silk-add` 的 `--x/--y/--font-size/--line-width` 也是 mil。

层 ID（嘉立创EDA）：`1`=顶铜 `2`=底铜 `3`=顶丝印 `4`=底丝印 `5`=顶阻焊 `6`=底阻焊。

---

## A. 设计语言（anime-brutalist 艺术卡）

极简要点（完整见 `references/design-language.md`）：

- **画布用 mm 单位**，标准卡 `91×60mm`（本项目口径）；出血 +3mm，渲染 300dpi。
- **七层 SVG**：`L1-bg`(底) / `L2-bg-type`(背景大字) / `L3-geometry`(几何色块线) /
  `L4-tech-labels`(等宽技术标签/歌词) / `L5-figure-real`(主体抠图，base64 `<image>`+clipPath) /
  `L6-fg-type`(前景大字/数字) / `L7-micro`(刻度带/编号)。
- **五色纯色**：近黑 `#0B0B0D`、深红 `#D6336C`、黄 `#F5C518`、深蓝 `#14204A`、米白 `#EDEDE6`。
- **字体**：大字 Impact/Arial Black；技术标签 Consolas/等宽；**艺术汉字行用霞鹜文楷 Medium**
  （LXGW WenKai，开源可商用），禁 UI 黑体；resvg 渲染必须 `font_files=[ttf绝对路径]` 显式挂载。
- **黑底人物线稿**转米白 `#EDEDE6` 单层（黑底上黑线会隐形）。
- **叙事闭环**：大字数字、幽灵字、CAT.NO 三段式编号必须指向同一专辑/演唱会，例如
  `15-2011-KF06`（《15》/2011 红磡/Khalil Fong 出道第六年）。
- **禁止**：霓虹/玻璃拟态/对称构图/随机英文堆砌/"漂亮但无意图"。追求"有设计意图"。

B 面（底视）参考实现：`assets/example-cardpcb-sideb.svg`；空白模板：`assets/layer-template.svg`。

---

## B. 从艺术到 PCB（核心管线）

### B0. 坐标框架

板子以**底视**呈现，X 镜像、Y 直映射。设板尺寸 `BW_mm × BH_mm`，设计稿在 **底视、y 向下**
的像素/毫米帧里定义。一个 mask 的毫米包围盒为 `(mx0,mx1,my0,my1)`（y 向下），
换算成 `pcb_PrimitiveImage.create` 所需的 mil 入参：

```
X_off = BW_mm * 3.937          # 0.1mil 单位
Y_off = BH_mm * 3.937
sx0 = X_off - mx1*3.937 ; sx1 = X_off - mx0*3.937     # 注意用 mx1 算 sx0 → X 镜像
sy0 = -Y_off + my0*3.937 ; sy1 = -Y_off + my1*3.937
X_P = sx1*10        ; W_P = (sx1-sx0)*10              # 右边缘 mil, 宽 mil
Y_P = -sy0*10       ; H_P = (sy1-sy0)*10              # 顶边缘 mil, 高 mil
```

本项目 `BW=91,BH=60` → `X_off=358.2677, Y_off=236.2205`。
`create(x=X_P, y=Y_P, cp, layer, w=W_P, h=H_P)`：引擎把复杂多边形**自身包围盒拉伸**进
`[x-w, x] × [y-h, y]`，X 镜像、Y 直映射。回读校验的逆变换见 `references/coordinate-framework.md`。

### B1. 把要落板的层栅格化成 PNG

- 细笔画/大字（如单字"15"）：**80px/mm**，再 `distance_transform_edt` 膨胀 0.25mm 当阻焊开窗。
- 整板丝印：**40px/mm**。
- alpha>128 取墨；黑底白字或白底黑字都行，只要 alpha 区分墨/空。

### B2. PNG → 复杂多边形（四零魔咒）

在 EDA 客户端里（`easyeda debug exec` 或桥接 `/execute`）：

```javascript
const bin = Uint8Array.from(atob("<BASE64>"), c => c.charCodeAt(0));
const blob = new Blob([bin], { type: "image/png" });
let cp = await eda.pcb_MathPolygon.convertImageToComplexPolygon(
    blob, W_PX, H_PX, 0, 0, 0, 0, true, false);   // ← 四个 0 是阈值/缩放参数，改了就破防
```

`cp` 是「子路径数组」，每个元素是带 `M`/`L` 标记的 SVG path 字符串（局部坐标，**像素**或
其自然单位）。**四零不能动**：它是"按 alpha 二值化 + 不缩放归一"的正确组合；改成其它值会让
包围盒假设失效，create 拉伸后严重错位。

### B3. 创建图元（create + 拉伸）

```javascript
const f = await eda.pcb_PrimitiveImage.create(X_P, Y_P, cp, LAYER, W_P, H_P);
const id = f.primitiveId || f.id;
```

- `LAYER`：丝印=3(顶)/4(底)，铜=1(顶)/2(底)，阻焊开窗=5(顶)/6(底)。
- 之后强制重绘：`setLayerInvisible(LAYER); setLayerVisible(LAYER);`（隐藏再显示，逼引擎重算）。

> 一个整板丝印图元可能 5 万+ 顶点。若图元"僵尸"（裸 source array、无几何实体），多半是
> 跳过了 B2 的 `convertImageToComplexPolygon` 直接塞了像素数据 → 必须走 B2。

### B4. 沉金（ENIG）双图元

金 = **铜层实色 + 同形状阻焊开窗**。同一图形各建一份：
- 铜：`create(..., 2, ...)`（底铜）/ `1`（顶铜）
- 阻焊开窗：`create(..., 6, ...)`（底阻焊）/ `5`（顶阻焊）
两者 bbox 与复杂多边形完全一致，叠在一起即"露铜镀金"。本项目"15"即用此法的底视图实现。

### B5. 黑色阻焊（显示色，非工艺色）

```javascript
await eda.pcb_Layer.modifyLayer(5, { color: "#000000" });  // 顶阻焊
await eda.pcb_Layer.modifyLayer(6, { color: "#000000" });  // 底阻焊
```

注意：这只改**编辑器显示色**。实物黑色阻焊工艺色仍要在 UI 的 Board Colors / 下单选项里选。
（反例：`setLayerColorConfiguration` 只接受整体配色预设枚举，对单色无效——别被它误导。）

### B6. 圆角板框（CLI，半径单位是 mil！）

```bash
easyeda pcb outline-round --radius 78.74          # 2mm = 78.74mil
```

产出 4 段线 + 4 个原生 90° ARC（locked 的 arc-polyline），中心线保持板尺寸不变。
保存后回读确认 `nativeArcs: 4` 持久化。

### B7. 自由丝印文字（客编 / 标注，CLI）

```bash
easyeda pcb silk-add --text "C123456" --x 2248 --y -284 --layer 4 \
                     --font-size 78.74 --line-width 6 --rotation 0
```

坐标 mil：本项目 B 面 `HAND & MIC` 行末端（x≈30.5mm）→ `x_mil = 3582.677 - mm_x*39.37`、
`y_mil = mm_y*39.37 - 2362.205`，落点约 `(2248, -284)`。字体太小（<32mil）嘉立创不可读，
线宽 ≥6mil。之后 `pcb silk-set` 可改位置/样式。

### B8. 校验与持久化

1. **回读 IoU**：`pcb_PrimitiveImage.get(id)` → `.complexPolygon`（可能是 Promise，需 await）
   → 用 B0 逆变换栅格化 → 与源 mask 算 IoU，要求 **>0.95**（整板）/ **>0.98**（单元素）。
2. **删旧图元**（换血时）：`pcb_PrimitiveImage.delete([oldId])`。
3. **保存**：`easyeda pcb save` → `easyeda doc reload`（有界，确认再读）→ 再次 dump/readback，
   IoU 零衰减才算落盘。

---

## C. 3D 预览陷阱（顶点预算）

嘉立创EDA 的 `pcb_RayTracerEngine` 对**矢量图元**做三角化。本项目 6 个 `pcb_PrimitiveImage`
合计 ~883KB / ~5 万顶点（L4 整板丝印 381KB≈2.1 万点、L3 301KB≈1.7 万点）直接导致 3D 加载
30s 超时挂死。结论：**插画类 PCB 别指望 EDA 内置 3D 预览**。要 3D 渲染就外走 Blender/Keyshot，
或在 EDA 里把大图元 `tolerance` 简化（代价是细节糊）。GPU、网络、隐藏图层都不是根因。

---

## D. 已踩坑（详见 `references/traps.md`）

高频雷区速记：
- 桥接每次 EDA 重启才重连；CLI daemon 掉线用 `easyeda daemon start` 后台拉起。
- `reload` 后 `getAllPrimitiveId` 可能炸 → 用已知 id `get()` 读，别枚举全量。
- 副本实验危险：副本 PCB 里原板 primitiveId 仍可解析 → 严禁在副本上批量删除，用完即删副本。
- 客编自动取不到：`getUserInfo().customerCode` 在半离线模式下为空，工程/缓存均无记录 → 问用户要。
- 坐标单位：PCB= mil；schematic=0.01inch(10mil)。混用会放错 10×。
- `convertImageToComplexPolygon` 四零魔咒；`create` 是包围盒拉伸不是定点放置。
- 黑阻焊用 `modifyLayer`，不是 `setLayerColorConfiguration`。

---

## 端到端示例（本项目 cardPCB 收尾）

目标 B 面：① 整板 sim3 黑丝印（L4，40px/mm 重建，IoU 0.90→1.0 是系统性外扩假象，真值对齐后
零衰减）；② "15" 沉金（L2 铜 + L6 阻焊开窗，80px/mm，IoU 0.9948/0.9955）；③ 黑色阻焊
(modifyLayer 5/6)；④ 2mm 圆角板框；⑤ 客编丝印接在 `FIG.02 — HAND & MIC` 行末（silk-add L4）。
完整脚本见 `assets/pipeline-example.py`（通用化重建脚本）。

---

## 相关技能

| Skill | 用途 |
|-------|------|
| `anime-brutalist-poster` | 纯动漫粗野主义海报/卡面设计（不含 PCB） |
| `easyeda-api` | 嘉立创EDA 官方 `eda.*` API 全集（120+ 类） |
| `easyeda-agent` | typed CLI 工程操作（布局/布线/DRC） |
| `jlcpcb` | JLCPCB 打样、拼板、钢网、BOM/CPL |
| `lcsc` | LCSC 器件选型 |
