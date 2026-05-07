# 可复现材料说明（全部由脚本自动生成，请勿手改本文）

本目录（相对仓库根）：`reports/deliverables_week7/reproducibility_complete`
对应周次：**Week 7**
元数据：`RUN_META.json`、`HEALTH_at_run_start.json`、`INDEX.json`

---

## 1. 本目录承诺提供什么（与导师要求对齐）

| 内容 | 说明 |
|------|------|
| `http_request_bodies/*.full.json.gz` | 评估脚本 `POST` 时使用的 **完整 JSON UTF-8 字节序列**（与 `urllib` 所用 `json.dumps(..., ensure_ascii=False).encode('utf-8')` 一致），**含完整 `*_base64` 图像**。解压后即为当次请求的 HTTP JSON body。 |
| （**不写入本包**）`POST /render` | 无头渲染预览用，不改变模型 multimodal 输入；为控制体量未 gzip 存档。 |
| `*.full.json.gz.sha256` | 对 **解压后 UTF-8 JSON 原始字节** 的 SHA-256；**不是** `.gz` 文件的哈希。 |
| `HEALTH_at_run_start.json` | 交付物流水线开始后、首次发包前快照的 `GET /health`，用于佐证 **`model_kind` / `ui2code_n_active`**。 |
| `INDEX.json` | 每条 POST 的路径、gzip 相对路径、哈希、字节数。 |

- **服务端追溯目录（每次 Week 7/8 主流程自动发送 `X-Experiment-Trace-Dir`；可用 `--trace-dir` 改根路径）**：仓库内相对路径 `reports/deliverables_week7/reproducibility_logs/week7_from-json_20260507_072807`。

- **`X-Experiment-Trace-Dir`（完整 Week 7/8 默认总有）**：服务在追溯根目录下按请求建子文件夹，内含 `effective_prompt.txt`（**代入后的英文文本**；多模态时**图像仍以张量进模型**，**不能**单凭此文件声明已包含「模型全部输入」）以及 **`request_meta.json` 与 `request.json`（内容相同）**：为服务端审计副本，**大块 base64 被替换为「长度 + sha256 前缀」**，用于 git 友好与对照；它们**不可替代**本目录 gzip 中的 **完整** 客户端请求体。**两者并存**：**gzip（本目录） = 发包原文**；**trace = prompt 明文 + 脱敏字段审计**（与 gzip 互补，非可选项）。

---

## 2. 诚实边界（避免误导）

1. **输出不唯一**：相同 POST body 在不同驱动 / 随机种子 / cudnn / 权重文件版本 / 服务端环境变量下，模型输出的 HTML 或预览 PNG **可能有差异**。此处固定的是 **输入侧证据链**，而非对输出做全域唯一锁定。  
2. **勿用剧本式 JSON 顶替真实输入**：导师要求的反例——**单独**放一个只描写实验场景的 `prompts.json` 却声称等价于完整模型调用——仍为**禁止**。若引用本仓库，应向导师指明 **`INDEX.json` + `http_request_bodies/*.full.json.gz` +（若存在）服务端 `effective_prompt.txt`**。

---

## 3. POST 数量

仅 **`/generate`、 `/refine`、 `/edit`** 计入本节（明细见 `INDEX.json`）。

本条流水共记录 **7** 条。

---

## 4. 解压校验示例

```bash
gzip -dc http_request_bodies/001_POST_generate.full.json.gz | sha256sum
# 与对应 .sha256 文件中的前缀一致（对解压后的字节流）。
```

---
*自动生成 / auto-generated*
