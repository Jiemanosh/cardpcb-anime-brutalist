# 设计语言（Anime-Brutalist 艺术卡）

> 整合自 `anime-brutalist-poster` 与本 cardPCB 项目。追求"有设计意图"，不是"漂亮"。

## 画布与出血

- 标准卡 `91×60mm`（本项目口径）；早期 85×54mm 4 层 ENIG 校园卡。
- SVG 用 **mm 单位**：`width="91mm" height="60mm" viewBox="0 0 91 60"`。
- 出血 +3mm；渲染 300dpi。resvg 渲染前正则剥离根节点 mm 物理单位（否则报 invalid size）。
- 底视图（B 面）y 向下、X 镜像；详见 `coordinate-framework.md`。

## 七层 SVG（L1–L7）

| 层 | id | 内容 | 落板映射 |
|----|----|------|----------|
| L1-bg | `L1-bg` | 纯色底（近黑 `#0B0B0D`） | 板底色 / 丝印底色 |
| L2-bg-type | `L2-bg-type` | 背景大字（Impact，深红/幽灵） | 丝印或沉金前景 |
| L3-geometry | `L3-geometry` | 几何色块/线（框、十字准星、分隔线） | 丝印 |
| L4-tech-labels | `L4-tech-labels` | 等宽技术标签/歌词/客编（Consolas） | 丝印 |
| L5-figure-real | `L5-figure-real` | 主体抠图（base64 `<image>` + clipPath） | 丝印/线稿（米白单层） |
| L6-fg-type | `L6-fg-type` | 前景大字/数字（Impact，"15"） | 沉金（铜+阻焊开窗） |
| L7-micro | `L7-micro` | 刻度带/编号（CAT.NO、PRINTED IN 2026） | 丝印 |

模板见 `assets/layer-template.svg`；B 面范例见 `assets/example-cardpcb-sideb.svg`。

## 五色系统（纯色，全程）

| 色 | 值 | 用途 |
|----|----|------|
| 近黑 | `#0B0B0D` | 底 |
| 深红 | `#D6336C` | 几何块/幽灵字 |
| 黄 | `#F5C518` | 强调/编号/金（映射沉金） |
| 深蓝 | `#14204A` | 几何块 |
| 米白 | `#EDEDE6` | 线稿/技术标签（黑底上用米白，别用黑） |

## 字体规范

- 大字/数字：Impact 或 `Arial Black`（双数字宽 ≈1.05×font-size，中缝大数字 font-size ≤ 缝宽/1.1）。
- 技术标签：**Consolas / 等宽**；所有定位标签 `text-anchor` 必须显式声明。
- **艺术汉字行**：霞鹜文楷 Medium（LXGW WenKai，开源可商用）。下载走
  `https://github.com/lxgw/LxgwWenKai/releases`，或 `https://ghproxy.net/https://github.com/...`。
  resvg 渲染必须 `font_files=[ttf绝对路径]` 显式挂载；SVG `font-family="LXGW WenKai Medium, LXGW WenKai, KaiTi, sans-serif"`。
- **禁止**雅黑/黑体等 UI 字体承担艺术汉字行。
- 繁简跟随题材（香港演出题材用繁体）。

## 通道 A：参考图主体抠出（首选）

1. `alpha = 255 - 灰度`，灰度 L>246 归零 → 白底变透明，排线深浅转透明度层次。
2. 落位：镜像/缩放，"地标落位"倒推 scale（如头部左缘目标 8mm、道具尖端出画至 93mm）。
3. 裁切设计化：底边对齐框缘/基线，禁止悬空硬切；左右硬边藏进出血区（x=0 / 91mm）。
4. 黑底线稿转米白 `#EDEDE6` **单层**（双色套印错位仅用户主动要求时）。
5. `<image>` 同时写 `href` 与 `xlink:href` 的 base64 data URI（resvg 双兼容），置 L5 + clipPath。

## 通道 B：手绘矢量符号（无参考图时）

平面设计符号：单一高饱和色填充 + 高对比描边 + ≤8 条内部细节线 + 一个记忆点手势/道具
（举掌、持麦）。禁写实渐变/照片光影。头身用**填充脖子块**连接（两根悬空线不算连接）；
颅顶收平、发丝贴颅顶走弧线（防"灯泡头"）。

## 叙事闭环（必做）

大字数字、幽灵字、CAT.NO 三段式编号三者指向同一张专辑/演唱会：
`CAT.NO <大字>-<年份>-<缩写+序号>`，如 `15-2011-KF06`（《15》/2011 红磡/Khalil Fong 出道第六年）。
禁用有歧义/谐音风险的缩写（如 SB01）。

## 强制自审清单

- [ ] 灯泡头？颅顶收平、发丝贴颅顶弧线。
- [ ] 头身断缝？画填充脖子块。
- [ ] 标签被人物吞？角标移到黑区或调层序。
- [ ] 竖字打架？只留一条。
- [ ] 品红压红？改米白或黄。
- [ ] 半透明小字发糊？改不透明或移入黑净区。
- [ ] 中文行 UI 感？换霞鹜文楷。
- [ ] CJK 豆腐块？resvg 挂载中文字体。
- [ ] 主体悬空硬切？底边对齐框缘做设计化裁口。
- [ ] 竖排被出血缘裁半？`transform="translate(x,y) rotate(90)"` 且文字 `x=0 y=0`。
- [ ] 中缝大数字失控？font-size ≤ 缝宽/1.1，`text-anchor="middle"`，渲染后查压刻度带。

## 关键禁令

普通赛博朋克 / 霓虹光 / 玻璃拟态 / 卡片式 UI / 对称构图 / 随机英文堆砌 / UI 中文字体 / 悬空硬切 /
"漂亮但无意图"——命中即返工。
