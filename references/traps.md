# 已踩的坑（Pitfalls）

> 按严重度排序。每条都来自真实翻车，能省几天。

## 通道/连接

1. **桥接每次 EDA 重启才重连**：EDA 重启后桥接（`localhost:49620`）要重启 bridge server 才重连；
   CLI daemon（60832）会自动重连。判断掉线：`easyeda health` 看 `windows` 是否出现目标工程。
2. **CLI 报 "no EasyEDA connector"**：`easyeda daemon start` 后台拉起 daemon，再 `easyeda health` 确认。
3. **EDA 重启后停在 home 页**：`doc open/switch` 报 `schematic.pages.list failed: Cannot read
   properties of undefined (reading 'map')`。`openProject` / `project open` 均返回 false →
   **只能用户在 UI 双击打开工程**（程序化无法打开）。
4. **桥接 vs CLI 是两套独立通道**：`bridge`（HTTP 49620，需 EDA 重启才重连）与 `easyeda.exe`
   daemon（60832，自动重连）互不替代；跑 JS 用 bridge `/execute` 或 `easyeda debug exec`。

## 图元/几何

5. **Fill / Region / Pour 的 BETA `create` 全废**：别用它们铺艺术图形，矢量插画只走
   `pcb_PrimitiveImage`（B2/B3）。
6. **裸 source array → 僵尸图元**：直接把像素数组塞 `create` 不产生几何实体（不可见、不可 3D）。
   **必须**先 `convertImageToComplexPolygon` 得到 `cp`。
7. **`convertImageToComplexPolygon` 四零魔咒**：`(blob, w, h, 0,0,0,0, true, false)` 的后四个 0
   不能改；改了包围盒假设失效，create 拉伸错位。
8. **create 是包围盒拉伸，不是定点放置**：`create(x,y,cp,w,h)` 把 `cp` 自己 bbox 拉进
   `[x-w,x]×[y-h,y]`。X/Y 镜像、缩放已被坐标常数吸收；传自然像素 `cp` 即可。
9. **stored Y 与 bbox 相反**：回读/落点 Y 出现"取反"源于 `-sy0*10` 那项，属正常，按 B0 公式即可，别手调。
10. **reload 后 `getAllPrimitiveId` 必炸**：`reload` 后枚举全量图元会失败。改用已知 id `get()`
    读取，或 `dump` 快照，不要枚举。
11. **整板回读 IoU 0.90 是系统性外扩假象**：整板图元回读 IoU 偏低常因栅格化 even-odd 合成误差，
    不是真错位；以"真值对齐后零衰减"为准，别被 0.90 吓到。
12. **副本实验危险（坑19）**：`board copy` 出的副本里，原板 primitiveId 仍可被 `get()` 解析 →
    严禁在副本上批量删除；验证完即时 `board delete <副本>`。

## 坐标/单位

13. **PCB 单位 = mil，Schematic = 0.01inch(10mil)**：混用会放错 10×。所有 `eda.*` 几何按 mil。
14. **`silk-add` 坐标/字号是 mil**：`--x/--y/--font-size/--line-width` 全 mil；字号 <32mil 嘉立创不可读，线宽 ≥6mil。
15. **圆角半径单位是 mil**：`outline-round --radius 78.74`（2mm=78.74mil），传 mm 会爆圆角。

## 颜色/工艺

16. **黑阻焊用 `modifyLayer`，不是 `setLayerColorConfiguration`**：后者只接受整体配色预设枚举
    （`EPCB_LayerColorConfiguration`，如 ALTIUM=2），对单色无效、误导性强。
    `modifyLayer(5/6, {color:'#000000'})` 才能改单层显示色。
17. **`modifyLayer` 改的是显示色，非工艺色**：实物黑色阻焊工艺色仍要在 UI 的 Board Colors/下单选项选。
18. **沉金 = 铜层 + 阻焊开窗两份图元**：只在铜层放金色块不会"露金"，必须同形状再建一份阻焊开窗
    （同 bbox、同 `cp`）。

## 其它

19. **客编自动取不到**：半离线模式下 `eda.sys_Environment.getUserInfo().customerCode` 为空；
    工程 sqlite（attributes/system_attributes/...）与 LCEDA-Pro 的 IndexedDB / Local Storage /
    Service Worker 缓存全扫无值（仅字段名，无数据）。→ 直接问用户要（登录 jlc.com 个人中心可见）。
20. **3D 预览顶点预算**：`pcb_RayTracerEngine` 对矢量图元做三角化，6 个 `PrimitiveImage` 合计
    ~883KB/~5 万顶点即导致 3D 加载 30s 超时挂死。插画类 PCB 别指望 EDA 内置 3D；要 3D 外走
    Blender/Keyshot，或 `tolerance` 简化（代价糊）。GPU/网络/隐藏图层都不是根因。

## 通用

- 每次稳定检查点显式 `pcb save`；验证持久化用有界 `doc reload` 后再读。
- 截图/界面观察只能当只读证据，不能替代 typed readback。
- 工程级跨项目打开、原生 `.eprj2` 导出见 `easyeda-agent` 的 references。
