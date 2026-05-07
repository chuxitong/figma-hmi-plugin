# 本地工具 `figma-bootstrap` 使用与 `localhost:8765` 报错说明

这份说明专门讲仓库里的工具插件：

- `_localtools/figma-bootstrap`

它和主插件 **`figma-plugin`** 不是一回事。

---

## 一、它是干什么的

`figma-bootstrap` 的作用不是调大模型，也不是调用 `/generate`、`/refine`、`/edit`。  
它做的是：

1. 从一个 **SVG 素材 HTTP 服务**
2. 拉取：
   - `symbols/*.svg`
   - `screens/*.svg`
3. 再把这些 SVG 导入 Figma，整理成页面/组件/variants

也就是说，它依赖的是**素材静态服务**，不是模型服务。

---

## 二、为什么以前会报 `localhost:8765 ... ERR_CONNECTION_REFUSED`

因为旧版 `figma-bootstrap` 的 UI 里把地址写死成了：

- `http://localhost:8765`

只要你本机没有启动一个监听 **8765** 端口的 HTTP 服务，它就一定会报：

- `ERR_CONNECTION_REFUSED`
- `[bootstrap] UI fetch failed`

这不是“远程模型服务坏了”，也不是主插件 `figma-plugin` 坏了；只是这只工具插件在找**素材服务**时，地址写得太死。

---

## 三、我这次改了什么

### 1. `figma-bootstrap` 现在支持**自定义 SVG 服务器 URL**

我修改了：

- `_localtools/figma-bootstrap/ui.html`

现在它有：

- 一个 **Base URL 输入框**
- 一个 **Save SVG server URL** 按钮
- 默认值仍然是 `http://localhost:8765`
- 但你现在可以改成：
  - 本机地址
  - SSH 端口转发地址
  - 云端公网 / 隧道地址

也就是说，它不再被强制绑死在本机 `8765`。

### 2. manifest 允许本机或远程地址

我修改了：

- `_localtools/figma-bootstrap/manifest.json`

现在它使用：

- `allowedDomains: ["*"]`
- `reasoning`
- `devAllowedDomains`

这样就不会因为只认 localhost 而被 Figma 的联网策略卡住。

### 3. 错误提示更清楚

如果它拉素材失败，现在会在 UI 日志里多给一条 hint，大意是：

- 先确认 SVG server 是否已启动
- 当前机器是否能访问
- 服务是否真的提供 `/symbols` 和 `/screens`
- 是否带了 CORS

---

## 四、这是不是“远程服务端问题”

要分情况。

### 情况 A：你把 Base URL 写成 `http://localhost:8765`

那它就是**当前运行 Figma 的这台机器本地**的问题：

- 本机没开素材服务
- 或端口不对
- 或服务没监听到你填的地址

### 情况 B：你把 Base URL 写成远程地址

例如：

- `https://你的域名`
- `http://某台服务器:8765`

那就变成**远程素材服务**的问题，可能是：

- 远程没启动
- 端口没开放
- 反代没配置
- 没带 CORS
- 路径不是 `/symbols/...` 与 `/screens/...`

所以，**它是不是远程问题，取决于你在工具插件里填的 URL 是本机还是远程。**

---

## 五、我推荐你怎么用

### 方案 1：在本机跑素材服务

如果你的素材文件已经在本机有一份仓库：

```bash
python _localtools/serve_layered_svg.py
```

然后在 `figma-bootstrap` 里填：

```text
http://localhost:8765
```

这是最简单的用法。

### 方案 2：在云端跑素材服务

如果仓库主要在云端，且你不想再把 `mockups/layered-svg` 同步到本机：

1. 在云端启动：

```bash
python _localtools/serve_layered_svg.py
```

2. 用以下任一方式让本机可访问：
   - SSH 端口转发
   - 公网 / 内网映射
   - 反向代理

3. 在 `figma-bootstrap` 的 URL 输入框里填：
   - 转发后的本机地址
   - 或云端可直连地址

例如：

```text
http://localhost:8765
```

（若你做了 SSH 转发）

或：

```text
https://your-svg-host.example.com
```

（若你做了公网反代）

---

## 六、如何判断服务是不是正确

你在**能访问该 URL 的浏览器**里打开下面任意一个地址：

```text
http://localhost:8765/symbols/pump.svg
```

```text
http://localhost:8765/screens/07-energy-dashboard.svg
```

如果浏览器能直接看到 SVG 内容，说明素材服务是通的。  
如果浏览器都打不开，`figma-bootstrap` 自然也会失败。

---

## 七、和主插件 `figma-plugin` 的关系

再次强调：

- `figma-bootstrap`：导入 SVG 素材/样板用
- `figma-plugin`：调用本地/远程 HMI HTTP API（`/generate`、`/refine`、`/edit`、`/render`）

这两者不要混为一谈。

如果你看到的是：

- `localhost:8765`
- `[bootstrap] UI fetch failed`

那优先看的是这份文档，而不是主插件的模型服务。

---

## 八、相关文件

| 文件 | 用途 |
|------|------|
| `_localtools/figma-bootstrap/ui.html` | bootstrap 工具 UI（现已支持自定义 URL） |
| `_localtools/figma-bootstrap/manifest.json` | bootstrap 工具 manifest |
| `_localtools/serve_layered_svg.py` | SVG 素材静态服务 |
| `help/插件报错全面排查与本次修复说明.md` | 总排查说明（含这次日志分类） |

