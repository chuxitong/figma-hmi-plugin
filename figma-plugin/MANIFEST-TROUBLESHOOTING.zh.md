# Figma 仍报 `networkAccess` / localhost / reasoning？

## 1. 先确认：Figma 读到的**是不是你刚改的那份** `manifest.json`

- 在 **Windows 资源管理器**里打开**你点「Import from manifest…」时选中的那个** `manifest.json`，用**记事本**打开。  
- 看里面是否已有 **`"reasoning"`**、**`"devAllowedDomains"`** 与 **`"documentAccess": "dynamic-page"`**（与仓库中最新 `figma-plugin/manifest.json` 一致）。  
- 若你本地还是只有 `"allowedDomains": ["http://localhost:8000"]` 而**没有** `reasoning`，说明 **Figma 用的是旧文件** 或你改的是**另一份克隆副本**；红色报错会一直出现，与仓库里是否已修无关。

## 2. 强制 Figma 重新读 manifest

1. **Plugins → Development →** 在列表里对本插件点 **Remove**（或从列表移除开发插件）。  
2. 完全**退出** Figma 桌面版再打开（清掉部分缓存）。  
3. **再次** **Import plugin from manifest…**，指向**上一步用记事本确认过**的 `figma-plugin\manifest.json`。

## 3. 常见原因

| 情况 | 说明 |
|------|------|
| 仓库在 **WSL / 云主机**，Figma 在 **Windows** | 必须在 **Windows 盘**上有一份**最新**的仓库（拉取/解压），并用**那份路径**去 Import。 |
| 用 **历史 zip 解压** 打开老工程 | 解压目录里的 `manifest` 没更新，需从 Git 再拉。 |
| 只改了 Cursor 里文件，**没保存** 或没同步到 Figma 指向的目录 | 保存后重试 Import。 |

## 4. 当前仓库里的合法写法（供对照）

- **`allowedDomains`**: `["*"]` + **`reasoning`（非空）** 满足「允许任意你填的 Service URL」；  
- **`devAllowedDomains`**: 显式包含 `http://127.0.0.1:8000`、`http://localhost:8000` 等，满足官方「本机请放 dev 列表」的推荐；  
- **`documentAccess`**: `"dynamic-page"` 为 Figma 当前文档中推荐项。

若按上表仍报**同一句**红字，多为 **Figma 仍加载旧 manifest**；请用记事本对 **Import 所用路径** 做一次核对。
