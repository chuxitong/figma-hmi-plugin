# 本地服务 API 说明（中文版）

Base URL：`http://localhost:8000`。服务由 `local-service/app.py` 经 uvicorn 启动。所有端点均启用了 CORS，便于 Figma 插件直接调用。下文说明各端点的请求体、响应体与调用示例。

## 与任务书一致：插件里用勾选控制「可选」

**请求体：**`task_description`、`variables`、`css_hints`、以及 `/refine`·`/edit` 的 `current_code` 与 `/edit` 的 `instruction`，均由 **`ui.html`** 中对应 **Include …** 勾选框决定是否并入本次 HTTP 请求（未勾选则发送 `null`、空对象，或拦截操作并写日志）。详见 **`help/docs/figma-data-extraction.zh.md`** 中的「插件 UI 勾选框一览」。

**响应体：**服务仍返回 **`code`**、**`explanation`**、**`metadata`**、**`preview_base64`**。是否在面板中展示 **`explanation`** / **`metadata`** / 预览图，由 **Show explanation**、**Show metadata**、**Show preview image** 三个勾选框控制（关闭时仅不刷新对应 UI 区域，不改变服务端行为）。

## POST `/generate`

根据传入的画框截图像素图返回 HTML/CSS 代码。请求体为：PNG 的 base64、画框名、**可选的自然语言** `task_description`（与任务书中「任务描述/提示词」对应）、视口 `width`/`height`（默认 1280×720），以及两个可选的上下文字段 `css_hints` 与 `variables`（与「来自 Figma 的变量 / CSS 提示」对应，由插件里勾选是否发送）。画框名作为标题提示；宽高用于 Playwright 将**同一 HTML 渲成 PNG 预览**（在服务器本地或远程容器内执行，输出均为 **PNG 的 base64**）。

无论服务跑在本机还是 AutoDL 等远程 GPU，预览图均为 **PNG**（`preview_base64`），与 `/render` 一致。若需归档，可同时将 `code` 存为 `.html`，将 base64 解码为 `.png` 与 `.b64`（仓库内 `run_week3_verified` 已按此落盘，避免「生完即丢」）。

请求示例：

```json
{
  "image_base64": "<base64-PNG>",
  "frame_name": "Equipment Status Dashboard",
  "task_description": "Emphasize the alarm area and use a high-contrast header.",
  "width": 1280,
  "height": 720,
  "css_hints": {
    "StatusCard": { "width": "280px", "background": "#2a2a3e", "border-radius": "8px" }
  },
  "variables": {
    "--color-primary": "#1A73E8",
    "--spacing-md": "16px"
  }
}
```

响应字段：`code`（HTML/CSS）；`preview_base64`（**PNG** 的 base64，由无头 Chromium 生成，失败则为 `null`）；`explanation`（短说明）；`metadata`（**下一阶段**建议：如建议调用的 `POST /edit` / `POST /refine`、当前 `model_kind`、视口、是否已嵌入 PNG、各上下文是否被使用等）。

## POST `/refine`

对已有代码做迭代优化。请求包含：参考 `reference_image_base64`、当前 `current_code`（「可选的当前代码」在 refine 流中为**必填**）。可选：`rendered_image_base64`（经 `/render` 得到的 **PNG** base64）、`task_description`、视口与 `css_hints`、`variables`。

请求示例：

```json
{
  "reference_image_base64": "<base64-PNG>",
  "current_code": "<!DOCTYPE html>...",
  "rendered_image_base64": "<base64-PNG-可选>",
  "task_description": "Tighten spacing in the main grid.",
  "width": 1280,
  "height": 720,
  "css_hints": {},
  "variables": {}
}
```

响应形式与 `/generate` 相同（含 `metadata`）。

## POST `/edit`

用自然语言短指令（`instruction`，即**提示词/任务**）修改当前**已有代码** `current_code`。另含 `width`/`height` 与 `css_hints`、`variables`（勾选才发送，与第 4 周要求一致）。响应中 `metadata.context.instruction` 表示是否携带了非空文字指令（与 `task_description` 在语义上区分为「编辑类」主入口）。

请求示例：

```json
{
  "current_code": "<!DOCTYPE html>...",
  "instruction": "让报警区更醒目",
  "width": 1280,
  "height": 720,
  "css_hints": {},
  "variables": {}
}
```

响应形式与 `/generate` 相同。

## POST `/render`

工具端点。接受 HTML 与视口尺寸，**返回 PNG**（`image_base64`）。与生成/编辑/refine 中的预览使用同一无头渲染管线。响应另含 `explanation` 与 `metadata`（宽、高、格式等）。

```json
{
  "html_code": "<!DOCTYPE html>...",
  "width": 1280,
  "height": 720
}
```

响应示例（节选）：

```json
{
  "image_base64": "<base64-PNG>",
  "explanation": "Rasterised HTML to PNG in headless Chromium (same pipeline as preview fields).",
  "metadata": { "format": "png", "viewport": { "width": 1280, "height": 720 } }
}
```

## GET `/health`

健康检查。典型形式：`{ "status": "ok", "model_loaded": true, "model_kind": "ui2coden"|"rule_based"|"stub", "ui2code_n_active": true|false }`，用于判断当前是否为真实 UI2Code^N。

## curl 调用示例

生成代码：

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "iVBORw0...", "frame_name": "Equipment Status Dashboard"}'
```

按指令编辑：

```bash
curl -X POST http://localhost:8000/edit \
  -H "Content-Type: application/json" \
  -d '{"current_code": "<!DOCTYPE html>...", "instruction": "Make the card background lighter"}'
```

## 服务内部使用的模型

服务在**首次请求时**懒加载模型：先尝试从 `model_wrapper` 导入并加载真实 UI2Code^N；若失败（无权重、无 GPU、版本不兼容等），会**静默回退**到确定性备用实现 `rule_based_model.RuleBasedModel`。两套实现均提供相同的 `generate` / `refine` / `edit` 接口，故其余代码无需区分。

---

*本文件为 `api-reference.md` 的中文对照版，如有出入以仓库内 `local-service/app.py` 与俄文/英文主文档为准。*
