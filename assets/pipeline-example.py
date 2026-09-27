# -*- coding: utf-8 -*-
"""
cardpcb-anime-brutalist · 通用图像图元落地脚本
============================================
把"设计稿 mask / SVG 元素"转成嘉立创EDA 的 pcb_PrimitiveImage 矢量几何，
覆盖: 丝印层 / 沉金(铜+阻焊开窗)。已逐像素回读验证 (IoU 0.95+)。

依赖: numpy, Pillow, resvg_py(仅 SVG 源需要)
运行: 嘉立创EDA 装 run-api-gateway.eext 扩展; 桥接监听 localhost:49620
      (或改用 `easyeda debug exec --code` 替换 ex())

坐标: BW_mm/BH_mm 为板尺寸(本项目 91x60)。设计稿为"底视, y 向下"毫米帧。
详细公式见 references/coordinate-framework.md 与 image-primitive-pipeline.md。
"""
import json, io, base64, urllib.request, urllib.error
import numpy as np
from PIL import Image, ImageDraw

# ---------------- 配置 ----------------
BRIDGE = "http://localhost:49620/execute"
BW_MM, BH_MM = 91.0, 60.0          # 板尺寸
X_OFF = BW_MM * 3.937              # 0.1mil
Y_OFF = BH_MM * 3.937
PXMM_DEFAULT = 40                  # 整板丝印分辨率 (px/mm)
# 20px/mm 逆变换常量 (回读栅格化用; 若设计稿分辨率不同改这里)
DESIGN_PXMM = 20


# ---------------- 桥接执行 ----------------
def ex(code, timeout=600):
    req = urllib.request.Request(BRIDGE, data=json.dumps({"code": code}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError("HTTP %s: %s" % (e.code, e.read().decode("utf-8", "replace")[:300]))


# ---------------- 坐标: mask 包围盒(mm) -> create 入参(mil) ----------------
def mm_bbox_to_place(mx0, mx1, my0, my1):
    sx0 = X_OFF - mx1 * 3.937
    sx1 = X_OFF - mx0 * 3.937
    sy0 = -Y_OFF + my0 * 3.937
    sy1 = -Y_OFF + my1 * 3.937
    X_P = sx1 * 10
    W_P = (sx1 - sx0) * 10
    Y_P = -sy0 * 10
    H_P = (sy1 - sy0) * 10
    return X_P, Y_P, W_P, H_P


# ---------------- mask -> PNG payload + mm 包围盒 ----------------
def mask_to_payload(mask, pxmm, name="payload"):
    """mask: bool (H_px, W_px), True=墨。返回 (b64, w_px, h_px, (mx0,mx1,my0,my1))"""
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    crop = mask[y0:y1 + 1, x0:x1 + 1]
    im = Image.fromarray(np.where(crop, 0, 255).astype(np.uint8)).convert("RGB")
    import os
    p = "%s.png" % name
    im.save(p)
    b64 = base64.b64encode(open(p, "rb").read()).decode()
    mm = (x0 / pxmm, (x1 + 1) / pxmm, y0 / pxmm, (y1 + 1) / pxmm)
    return b64, im.width, im.height, mm


# ---------------- 创建图元 (JS: convertImageToComplexPolygon 四零魔咒 + create) ----------------
def create_image(b64, w_px, h_px, mm, layer, x_p=None, y_p=None, w_pp=None, h_pp=None):
    X_P, Y_P, W_P, H_P = mm_bbox_to_place(*mm) if None in (x_p, y_p, w_pp, h_pp) else (x_p, y_p, w_pp, h_pp)
    code = (
        'const bin=Uint8Array.from(atob("%s"), c=>c.charCodeAt(0));'
        'var blob=new Blob([bin],{type:"image/png"});'
        'let e=null,id=null;'
        'try{ let cp=await eda.pcb_MathPolygon.convertImageToComplexPolygon(blob,%d,%d,0,0,0,0,true,false);'
        'if(!cp) e="conv undefined";'
        'else{ const f=await eda.pcb_PrimitiveImage.create(%s,%s,cp,%s,%s,%s);'
        'id=f?(f.primitiveId||f.id):null; } }'
        'catch(x){ e=String(x&&x.message||x); } return {id,e};'
        % (b64, w_px, h_px, round(X_P, 4), round(Y_P, 4), layer, round(W_P, 4), round(H_P, 4))
    )
    r = ex(code)
    res = r.get("result") or {}
    if not res.get("id"):
        raise RuntimeError("create failed: %s" % res.get("e"))
    # 强制重绘
    ex("await eda.pcb_Layer.setLayerInvisible(%d); await eda.pcb_Layer.setLayerVisible(%d);" % (layer, layer))
    return res["id"], (X_P, Y_P, W_P, H_P)


# ---------------- 回读 + IoU 校验 ----------------
def parse_path(toks):
    subs, cur, i = [], [], 0
    while i < len(toks):
        t = toks[i]
        if t == "M":
            if cur:
                subs.append(cur); cur = []
            i += 1; continue
        if t == "L":
            i += 1; continue
        cur.append((float(t), float(toks[i + 1]))); i += 2
    if cur:
        subs.append(cur)
    return subs


def raster_subs(subs, W_px=1820, H_px=1200):
    acc = np.zeros((H_px, W_px), bool)
    for s in subs:
        tmp = Image.new("1", (W_px, H_px), 0); d = ImageDraw.Draw(tmp)
        pts = [((X_OFF - x) / 3.937 * DESIGN_PXMM, (y + Y_OFF) / 3.937 * DESIGN_PXMM) for x, y in s]
        if len(pts) >= 3:
            d.polygon(pts, fill=1)
        acc ^= np.array(tmp, bool)
    return acc


def readback_iou(pid, ref_mask):
    r = ex('const p=await eda.pcb_PrimitiveImage.get("%s"); let c=p.complexPolygon;'
           'if(c&&c.then)c=await c; return c;' % pid)
    st = r["result"]
    m = raster_subs(parse_path(st[0].split()))
    inter = (m & ref_mask).sum(); union = (m | ref_mask).sum()
    return (inter / max(1, union)), len(st), sum(len(s) for s in parse_path(st[0].split()))


# ---------------- 沉金: 铜层 + 阻焊开窗 双图元 ----------------
def create_enig(mask, pxmm=80, dil_mm=0.25, copper_layer=2, mask_layer=6):
    from scipy import ndimage
    # 阻焊开窗 = 铜 mask 膨胀 dil_mm
    mk = ndimage.distance_transform_edt(~mask) <= (dil_mm * pxmm + 1e-6)
    cu_b64, cu_w, cu_h, cu_mm = mask_to_payload(mask, pxmm, "cu")
    mk_b64, mk_w, mk_h, mk_mm = mask_to_payload(mk, pxmm, "mk")
    cu_id, _ = create_image(cu_b64, cu_w, cu_h, cu_mm, copper_layer)
    mk_id, _ = create_image(mk_b64, mk_w, mk_h, mk_mm, mask_layer)
    return cu_id, mk_id


# ---------------- 演示: 从 SVG 文本元素建"15"沉金 ----------------
def demo_svg_element(svg_path, regex, pxmm=80):
    import re, resvg_py
    svg = open(svg_path, encoding="utf-8").read()
    el = re.search(regex, svg).group(0)
    s = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 91 60">\n%s\n</svg>' % el
    png = resvg_py.svg_to_bytes(svg_string=s, width=91 * pxmm, height=60 * pxmm)
    g = np.asarray(Image.open(io.BytesIO(bytes(png))).convert("RGBA"))[:, :, 3] > 128
    return g


if __name__ == "__main__":
    # 例1: 整板丝印 (来自 PNG)
    # silk = np.array(Image.open("silk_bottom_v8_new.png").convert("RGBA"))[:,:,3] > 128
    # b64, w, h, mm = mask_to_payload(silk, PXMM_DEFAULT, "silk")
    # sid, box = create_image(b64, w, h, mm, layer=4)
    # v, n, pts = readback_iou(sid, silk)
    # assert v > 0.95

    # 例2: "15" 沉金 (来自 SVG 元素)
    # g = demo_svg_element("poster-sideb-real.svg", r'<text x="70\.5" y="54"[^>]*>15</text>')
    # cu_id, mk_id = create_enig(g, pxmm=80)
    print("pipeline-example ready; uncomment demos in __main__ to run against a live EDA.")
