# 图像图元管线（Image Primitive Pipeline）

把任意 PNG/插画转成嘉立创EDA 的 `pcb_PrimitiveImage` 矢量几何。整套流程已逐像素回读验证
（整板丝印 IoU 0.95+、单元素 0.98+）。

## 0. 前置：栅格化

- 细笔画/大字（如单字"15"）：**80px/mm**；整板丝印：**40px/mm**。
- `alpha > 128` 取墨；源图黑底白字或白底黑字都行。
- 阻焊开窗：对铜层 mask 做 `distance_transform_edt(~mask) <= 0.25*PX+1e-6` 膨胀 0.25mm。
- 裁掉外围空白，得到 mask 的毫米包围盒 `(mx0,mx1,my0,my1)`（mm，y 向下）。

## 1. 生成 PNG payload（Python 侧）

```python
import base64
from PIL import Image
import numpy as np

# mask: 布尔数组(H_px, W_px)，True=墨
ys, xs = np.nonzero(mask)
x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
crop = mask[y0:y1+1, x0:x1+1]
im = Image.fromarray(np.where(crop, 0, 255).astype(np.uint8)).convert("RGB")
im.save("payload.png")
b64 = base64.b64encode(open("payload.png","rb").read()).decode()
w_px, h_px = im.width, im.height
mx0, mx1, my0, my1 = x0/PX, (x1+1)/PX, y0/PX, (y1+1)/PX   # PX = 渲染分辨率
```

## 2. B64 → 复杂多边形（EDA 客户端，四零魔咒）

通过桥接 `POST localhost:49620/execute {code}` 或 `easyeda debug exec --code "..."` 运行：

```javascript
const code = `const bin=Uint8Array.from(atob("${b64}"), c=>c.charCodeAt(0));
var blob=new Blob([bin],{type:"image/png"});
let e=null,id=null;
try{
  let cp=await eda.pcb_MathPolygon.convertImageToComplexPolygon(blob, ${w_px}, ${h_px}, 0, 0, 0, 0, true, false);
  if(!cp) e="conv undefined";
  else { const f=await eda.pcb_PrimitiveImage.create(${X_P}, ${Y_P}, cp, ${LAYER}, ${W_P}, ${H_P});
         id=f?(f.primitiveId||f.id):null; }
} catch(x){ e=String(x&&x.message||x); }
return {id,e};`;
```

`convertImageToComplexPolygon(blob, w, h, 0,0,0,0, true, false)`：
- 后四个 `0,0,0,0` 是阈值/缩放/偏移参数；**保持全 0**，它们是"按 alpha 二值化 + 不归一缩放"
  的正确组合。改成其它值会让后续 `create` 的包围盒假设失效，结果严重错位。
- `true`=填充，`false`=不合并相邻多边形。
- 返回 `cp`：`[子路径0, 子路径1, ...]`，每个是 `"M x0 y0 L x1 y1 L ... "` 字符串（像素单位）。

## 3. create 的拉伸语义（关键）

`pcb_PrimitiveImage.create(x, y, cp, layerId, w, h)`：引擎取 `cp` **自身的包围盒**，线性拉伸到
`[x-w, x] × [y-h, y]` 后再按层放置。即"给一个目标矩形，图元自动填满"——**不是**"顶点定点摆放"。
因此 X/Y 镜像、缩放都已被 B0 的常数吸收，传入的 `cp` 用自然像素坐标即可。

`(X_P, Y_P, W_P, H_P)` 由 B0 公式得到（右/顶边缘 + 宽/高，全部 mil）。

## 4. 强制重绘

```javascript
await eda.pcb_Layer.setLayerInvisible(${LAYER});
await eda.pcb_Layer.setLayerVisible(${LAYER});
```
隐藏再显示，逼引擎重算几何（否则新图元可能不立即显示/不进 3D）。

## 5. 回读验证

```javascript
const p = await eda.pcb_PrimitiveImage.get("${id}");
let c = p.complexPolygon; if (c && c.then) c = await c;   // 可能是 Promise
return c;   // [子路径字符串...]
```
把 `c` 用 B0 逆变换栅格化（见 coordinate-framework.md），与源 mask 算 IoU：
- 整板丝印 ≥ 0.95；单元素（如"15"）≥ 0.98 才算合格。
- 若 IoU 偏低：多半是 `X_P/Y_P/W_P/H_P` 算错，或 `cp` 没走 `convertImageToComplexPolygon`
  （裸 source array → "僵尸图元"）。

## 6. 删旧 / 换血

```javascript
await eda.pcb_PrimitiveImage.delete(["oldId1","oldId2"]);
```
换血顺序：**先建新图元并回读验证 → 再删旧**。绝不在副本 PCB 上批量删除（见 traps.md 坑19）。

## 完整可运行脚本

见仓库 `assets/pipeline-example.py`（把 rebuild_l4.py / replace15b.py 通用化）。
