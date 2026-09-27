# easyeda-agent CLI 速查（Cookbook）

> 本 cardPCB 项目实际用到的命令。完整动作目录：`easyeda actions`；任意命令 `--help` 看参数；
> 未知官方接口先 `easyeda api search <词>`。

## 连接与保活

```bash
easyeda health                                   # 看 daemon + windows + writeHealth
easyeda daemon start                             # 后台拉起 daemon（60832），掉线自愈
easyeda --project <name> pcb <cmd>               # 按工程路由，省去 --window
easyeda --doc <uuid|name> pcb <cmd>              # 锁定到某 PCB 再改，避免前台页错乱
```

## 板框

```bash
easyeda pcb outline-get                          # 读板框（中心线尺寸 + 渲染 bbox + nativeArcs）
easyeda pcb outline-round --radius 78.74          # 2mm 圆角（半径单位 mil！）
easyeda pcb outline-clear                        # 删板框
easyeda pcb outline-set --rect "0,0,3582.68,2362.21"   # 从多边形设板框（mil, y-up）
```

## 丝印文字（客编 / 标注）

```bash
# 底层丝印，mil 坐标；字号 78.74mil≈2mm，线宽 6mil
easyeda pcb silk-add --text "C123456" --x 2248 --y -284 --layer 4 \
                     --font-size 78.74 --line-width 6 --rotation 0
easyeda pcb silk-set  <primitiveId> --x 2248 --y -284 --font-size 78.74   # 改位置/样式
easyeda pcb silk-import-svg --file art.svg --layer 4     # 整块 SVG 当填充丝印（备选）
```

## 图层 / 显示

```bash
easyeda pcb layers                               # 列层（含当前层、铜层数）
easyeda pcb layer-visibility --hide 3,4           # 隐藏层（验证/避让）
easyeda pcb layer-visibility --show 3,4           # 显示层
# 黑阻焊（显示色，非工艺色）走 JS：
easyeda debug exec --code "return await eda.pcb_Layer.modifyLayer(6,{color:'#000000'});"
```

## 保存 / 重载 / 读取

```bash
easyeda pcb save                                 # 保存当前 PCB
easyeda doc reload                               # 有界重载（验证持久化）
easyeda pcb dump --out board.json                 # 只读几何快照（JSON）
easyeda pcb view-side bottom                     # 切到底面视图（截图用）
```

## 在 EDA 客户端跑任意 JS

```bash
# 桥接 HTTP（需 run-api-gateway.eext 扩展）：POST localhost:49620/execute {"code":"..."}
# 或经 CLI 连接器：
easyeda debug exec --code "return await eda.sys_Environment.getUserInfo();"
easyeda debug exec --code "const p=await eda.pcb_PrimitiveImage.get('ID'); \
  let c=p.complexPolygon; if(c&&c.then)c=await c; return c;"
```
> `debug exec` 是确认门控的逃生口；用它跑 JS 时务必 `return` 结果（console.log 不被捕获）。

## 复制/删除板（危险）

```bash
easyeda board                                    # 板管理（schematic↔PCB 绑定）
# ⚠ 副本里的原板 primitiveId 仍可被 get() 解析 → 严禁在副本上批量删除，用完即删副本
```
