# 从 Figma 提取哪些数据

本文描述仓库 **`figma-hmi-plugin`** 的**当前实现**。以代码为准：**`figma-plugin/src/code.ts`**（沙盒）、**`figma-plugin/src/ui.html`**（插件 UI）与 **`local-service/app.py`**（HTTP 服务）。

---

## 与《任务计划》第 4 周：服务应接受 vs 服务应返回（请先读）

以下表述与 **`help/张思成-任务计划（中文翻译）.md`** 第 4 周一致。**「可选」**在任务书中的含义是：**协议与实现必须支持**；**某一次 HTTP 请求里**可以不带该字段（由场景决定，例如首次生成没有「当前代码」）。

### 服务应接受

| # | 任务书表述 | 后端字段（示意） | 数据从哪来 |
|---|------------|------------------|------------|
| 1 | 界面的 PNG 图片 | `image_base64`（及 `frame_name`、`width`、`height`） | Figma `exportAsync` |
| 2 | 任务描述或提示词（prompt） | `task_description`；编辑流中为 `instruction` | UI 文本框；**仅当勾选 Include task description** 时才在 `/generate` 发送（否则 `null`）。编辑流另受 **Include edit instruction** 控制 |
| 3 | （可选）当前代码 | `current_code` | 插件内存 **`currentCode`**；**仅当勾选 Include current HTML in Refine / Edit** 时才向 `/refine`、`/edit` 发送（未勾选则操作被阻止） |
| 4 | （可选）来自 Figma 的变量 | `variables` | Figma API + 勾选 **Include design variables** |
| 5 | （可选）CSS 提示 | `css_hints` | Figma + 勾选 **Include CSS hints** |

### 服务应返回

| # | 任务书表述 | 后端字段 | 在插件里如何看到 |
|---|------------|----------|------------------|
| 1 | 生成或更新的 HTML/CSS | `code` | **Generated Code** 文本框 |
| 2 | （可选）简短说明 | `explanation` | **Show explanation in panel** 勾选时写入 Explanation 框；未勾选则占位提示（服务端仍返回） |
| 3 | （可选）下一阶段的元数据 | `metadata` | **Show metadata (JSON)** 勾选时写入；未勾选则占位提示 |

工程上还有 **`preview_base64`**；**Show preview image from service** 勾选时用其更新 **Preview** 区，未勾选则不更新预览图。

## 插件 UI 勾选框一览（`figma-plugin/src/ui.html`）

任务书里的「可选」在界面上**一律对应明确勾选**（或明确不勾选即不发送 / 不展示）：

**请求是否携带（点击按钮瞬间的状态生效）：**

| 勾选框 | 作用 |
|--------|------|
| Include task description | 开：`/generate` 发送文本框内容（可空→`null`）。关：始终 `task_description: null`。 |
| Include design variables | 开：**遍历当前导出 Frame 子树**上的变量绑定（含 **Libraries → Fill** 等），再合并文件内多余的本地变量定义→ 写入 `variables`。关：空对象。 |
| Include CSS hints | 开：沙盒收集 CSS 并入 `css_hints`。关：空对象。 |
| Include current HTML in Refine / Edit | 开：允许 `/refine`、`/edit` 并发送 `current_code`。关：两按钮拦截并日志提示。 |
| Include edit instruction | 开：允许 `POST /edit` 发送 `instruction`。关：拦截 Apply Edit。 |

**返回是否在面板展示（服务端仍返回 JSON；仅影响 UI 是否刷新该区域）：**

| 勾选框 | 作用 |
|--------|------|
| Show explanation in panel | 开：填充 `explanation`。关：占位「Show explanation is off」。 |
| Show metadata (JSON) in panel | 开：格式化 `metadata`。关：占位「Show metadata is off」。 |
| Show preview image from service | 开：用 `preview_base64` 更新预览。关：不更新预览区（有图时可能显示 hidden 提示）。 |

说明：**Generate** 仍始终导出并发送 PNG（当前流程下无「不发送图」勾选）。

**本文档以下章节**主要说明：**「服务应接受」里与 Figma 相关的项如何采集**。「返回」字段由 `CodeResponse` 定义；是否在面板显示由上表勾选控制。

---

## 划分说明（下文读法）

- **必需（Figma → 首次生成链路）**：PNG、画框元数据、沙盒↔UI 消息。  
- **仅从 Figma 勾选附加**：**variables**、**css_hints**。  
- **当前代码**：见上表；详述见「当前代码（插件状态）」。

## 必需数据

1. **选中节点的栅格导出**  
   - 仅当选中 **`FRAME`、`COMPONENT` 或 `INSTANCE`** 时有效（见 `getSelectedFrame()`），否则会提示先选对类型。  
   - 调用 `node.exportAsync({ format: 'PNG', constraint: { type: 'SCALE', value: 2 } })` 得到 `Uint8Array`，再 `figma.base64Encode(pngBytes)`。  
   - **2 倍缩放**用于提高小字与细部在模型输入中的可读性。

2. **节点元数据（注意：不包含 Figma 画框背景字段）**  
   导出完成后发往 UI、并在 Generate 时一并 POST 的包括：  
   - `frameName` ← `node.name`  
   - `width`、`height` ← 取整后的 `node.width`、`node.height`  
   当前实现**没有把 `node.backgrounds` 序列化进 payload**；若要把页面背景作为模型输入，需要改代码单独加入。

3. **沙盒 ↔ UI 消息通道**  
   - 沙盒 → UI：`figma.ui.postMessage(...)`  
   - UI → 沙盒：`parent.postMessage({ pluginMessage: ... }, '*')`  
   没有这条链路，UI 无法拿到文档里的 PNG 与上下文，也就无法 `fetch` 本地服务。

## 当前代码（插件状态，非 Figma 导出）

- 任务书中的「当前代码」在协议里对应字段 **`current_code`**（以及 Refine 里与服务约定的 `html_code` 用于 `/render` 等）。  
- **`ui.html`** 用变量 **`currentCode`** 保存最近一次模型返回的 HTML/CSS：在 **`/generate`**、**`/refine`**、**`/edit`** 的响应解析后赋值（见 `currentCode = result.code || ...`）。  
- **`POST /generate`** 不需要上一版代码（首次从图生成）。**`/refine`** 与 **`/edit`** 必须把 **`currentCode`** 作为 **`current_code`** 发给服务，否则流程无意义；这与任务书「可选」的含义一致——**能力必须实现**，**首次生成请求可以不携带**，迭代请求则携带。  
- 服务端：`RefineRequest`、`EditRequest` 在 **`local-service/app.py`** 中均包含 **`current_code`**，并把 **`css_hints` / `variables`** 一并传给模型包装层（与任务书一致）。

## 从 Figma 附加的可选数据（仅 variables 与 CSS，由 UI 勾选）

在 **`ui.html`** 中有两项：**Include design variables**、**Include CSS hints**。  
它们作用于 **Generate、Refine、Edit**：只有在**点击对应按钮时勾选开启**，经沙盒收集后，请求里才会带上**有内容的** `variables` / `css_hints`（Refine/Edit 通过 **`request-context`** 按当下勾选重新拉取，见下文）。

### 设计变量（`includeVariables`）

实现：`figma-plugin/src/code.ts` 中 `collectVariables`（build **2026-05-07-r5-vars-bound-tree** 及之后）。

1. **子树绑定（主要）**  
   从当前导出根 **Frame / Component / Instance** 起 **DFS** 遍历子节点（有节点数与深度上限），收集：  
   - 各节点 `boundVariables`（含 `fills` / `strokes` 等处的 `VariableAlias`）；  
   - 每条 **Paint**（含 **gradient stop**）上的 `boundVariables`；  
   - **Effect**、**Layout grid** 上的绑定；  
   - **Text** 各段 `getStyledTextSegments(['boundVariables'])`（需 `loadFontAsync` 成功）。  
   去重后最多 **200** 个变量 ID；对每个 ID **`getVariableByIdAsync`**（可解析**已启用库**里绑到稿面的变量），优先 **`variable.resolveForConsumer(根节点)`**；失败则回退该集合 **`modes[0]`** 的 `valuesByMode`。

2. **本地定义（补充）**  
   **`getLocalVariablesAsync()`** 中尚未出现在上一步结果里的键，最多再补 **80** 个（避免「仅文件内定义、子树未绑」的变量完全丢失）。

3. **键与取值**  
   `--` + 变量名，`/` → `-`；颜色格式化为 `rgba(...)` / `#RRGGBB`。  
   **更正**：旧实现**仅**枚举 `getLocalVariablesAsync()`，**漏掉**「Libraries → Fill」等**仅产生绑定、文件内无同名本地定义」**的变量，导致 `variables: {}`；当前以子树绑定为主。

4. **异常**  
   try/catch 保留已收集部分或得到空对象。

### CSS 提示（`includeCssHints`）

- 对选中节点调用 `getCSSAsync()`。  
- 对**最多 10 个直接子节点**（`children.slice(0, 10)`），若支持 `getCSSAsync` 则同样取 CSS，结果合并进一个字典，键为 **`child.name`**（若子节点重名可能互相覆盖）。  
- 失败或 API 不存在时可能得到空字典。

### 仅 Generate 使用的额外字段

UI 中有可选的 **task description** 文本框：调用 **`POST /generate`** 时作为 **`task_description`** 发送；留空则发 `null`。

## 独立流程：不重新导出 PNG 的上下文

消息 **`request-context`**（UI → 沙盒）只根据当前勾选状态收集 `cssHints` 与 `variables`，**不再**执行 `exportAsync`。  
用于 **Refine** 和 **Edit**，保证模型看到的变量/CSS 与**当前按钮按下时**的勾选一致，而不是第一次 Generate 时的状态。

沙盒回复：**`context-ready`**，带 `requestId` 与 `data: { cssHints, variables }`。

## 发往 HTTP 服务的字段（按端点）

UI 里可配置 **Service URL**（默认 `http://localhost:8000`），保存在 `localStorage`。**`manifest.json`** 的 **`networkAccess`** 须符合 Figma 当前校验（本仓库使用 **`allowedDomains: ["*"]` + `reasoning`**，避免仅写 `localhost` 时出现 Manifest error；实际请求仍只发往用户在面板中填写的 **Service URL**）。

| 端点 | 数据来源 |
|------|----------|
| **`POST /generate`** | 在 `frame-exported` 之后：`image_base64` 等；`task_description` / `css_hints` / `variables` 是否非空由对应 **Include …** 勾选与文本/沙盒数据决定 |
| **`POST /refine`** | 参考图：Generate 时缓存的 PNG；当前代码；代码截图：先 **`POST /render`**（`html_code` 与尺寸）；`css_hints` / `variables` 来自最新的 `request-context` |
| **`POST /edit`** | `current_code`、`instruction`、尺寸；`css_hints` / `variables` 来自 `request-context` |
| **`POST /render`** | 仅 UI：`html_code`、`width`、`height`（供 Refine 对比「设计稿 vs 当前 HTML 渲染」） |

线上 JSON 字段名与 **`local-service/app.py`** 中 `GenerateRequest`、`RefineRequest` 等模型一致。

## 数据流示意图

```
┌────────────────────────── Figma Desktop ──────────────────────────┐
│                                                                   │
│   code.ts (沙盒)              postMessage              ui.html     │
│   export-frame / request-context  ◄────────────►   pluginMessage   │
│   frame-exported / context-ready                     fetch /generate │
│                                                      /refine /edit   │
│                                                      /render         │
└────────────────────────────────────┬──────────────────────────────┘
                                     │ HTTP（基址由 UI 配置）
                                     ▼
                         本地服务（例如 localhost:8000）
```

## 当前代码中未实现的内容

- **完整轻量节点树**（仅几何/层级、不含变量语义）——**未采集**；但 **variables** 已按子树 **变量绑定** 做专门 DFS。  
- **将画框 `backgrounds` 发往服务**——**未实现**。

## 小结

**服务应接受：** 5 类输入在协议与后端均已实现；插件侧**每一项可选是否随请求发送**由 **`ui.html`** 勾选框控制（见上文「插件 UI 勾选框一览」）。首次 **Generate** 仍始终带 PNG。  

**服务应返回：** `CodeResponse` 含 `code`、`explanation`、`metadata`、`preview_base64`；**是否在面板展示**后三项由 **Show …** 勾选控制。  

**Refine/Edit：** 通过 `request-context` 刷新变量/CSS；Refine 会额外调用 `/render` 得到当前 HTML 的截图。

*若本文与代码不一致，以 **`figma-plugin/src/code.ts`**、**`figma-plugin/src/ui.html`** 与 **`local-service/app.py`** 为准。*
