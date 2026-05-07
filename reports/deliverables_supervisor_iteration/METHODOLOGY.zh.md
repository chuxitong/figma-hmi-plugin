# 实验方法与交付诚实标注（中文摘要）

本页与俄文 [`METHODOLOGY.md`](./METHODOLOGY.md) 平行，概括导师评审关切点与仓库中的**可核实**实现；操作细则仍以 `help/毕业论文实验-Git与Figma真实上下文.zh.md` 为准（help 不要求俄译）。

## 模型后端

批量脚本 `reports/scripts/hmi_week78_eval.py` 在启动前校验 `GET /health`：`ui2code_n_active=true` 且 **`model_kind` 必须为 `ui2coden`**，否则退出。不得在论文中把 **UI2Code^N** 与 **rule_based**（规则占位）混称为同一「真实 baseline」。

## 上下文来源（variables / CSS hints）

| 产物 | `context_source` / 说明 |
|------|-------------------------|
| mockup PNG + Python `synthetic_context()` | **`synthetic_script`**（Week 8 全批量默认） |
| Figma 插件导出 `*.payload.json` 对与图 | **`figma_plugin`**（Week 7 `--context-mode from-json`） |

Week 7 的 **四条 `/edit` 链路**仍为 mockup + 合成上下文；与「context 对照」段来源可能不一致——见 `reports/deliverables_week7/WEEK7_MANIFEST.json` 内的 `sequential_edits_context_source` 与中文字段说明。

Week 8 `metrics_full.json` 含 `context_source_bulk: synthetic_script`。

**用词（对接 Davydov）**：大批量 Week 8 评估中的 variables/CSS 正文表述须写为「**模拟设计变量与设计稿式 CSS hints 的额外上下文**」，不能与 Week 7 `figma_plugin` 真提取声称同一证据层级；二者的 `context_source*` 字段在 MANIFEST / `metrics_full.json` 已区分。

## SSIM、refine、定性维度

- **SSIM**：仅像素相似度度量，必须与人工观察并列；不得在结论中写成唯一成败标准。
- **自适应 refine**：首帧预览 SSIM ≥ `--ssim-accept`（或环境 `SSIM_ACCEPT`）则不再调用 `/refine`；否则在 `--max-refines` 上限内迭代直至达标或穷尽。
- **强制 refine**：`--force-refine-rounds` 或环境 `FORCE_REFINE_ROUNDS` 可与 SSIM 脱钩，固定执行若干轮 `/refine`，用于对比「从不 refine」的叙事；受 `--max-refines` 上界约束（`force > max` 时脚本拒绝运行）。
- **轨迹**：每个 Week 8 组合在 `per_screen/<slug>/<config>/refine_trace/` 落盘 HTML、预览 PNG、逐步 SSIM JSON。
- **定性脚手架**：`metrics_full.json` 与各 `metrics.json` 通过 `qualitative_dimensions_template` / 字段提示与 SSIM 并列记录类别化笔记（对齐、层级、缺件、图表、编辑副作用等）。

## Week 7 报告插图（上下文对照）

**Week 7 答辩插图**：`context_compare/figma_native_context/`（`from-json`）下 **`figma_plugin_THESIS_slide_image_only_context.png`** 与 **`figma_plugin_THESIS_slide_full_figma_context.png`** — 各自为 **两张独立**「参考帧 | 生成预览」（避免旧版三栏 triptych 投影字号过小）。同目录复制 **`figma_plugin_input_*.payload.json`**，manifest 字段 `png_for_report_thesis_slide_*_relative` 与 **`reproducibility_complete/`** 全文 gzip 对齐，满足「可追溯完整请求体 / effective_prompt」。**synthetic_script** 子目录仅保留作工程消融，不作为 ВКР 与 **figma_plugin** 混谈的 baseline。

## 可复现记录（全自动）

- **客户端完整请求**：`reports/deliverables_week7|8/reproducibility_complete/http_request_bodies/*.full.json.gz`（与脚本当次 `POST /generate|/refine|/edit` 的 JSON **逐字节一致**，含完整 base64）+ `INDEX.json` + 自动生成的 **`README_REPRODUCIBILITY.zh.md`**（含导师要求的边界说明与 `prompts.json` 反例，**无需人工再写**）。  
- **服务端审计（固定执行）**：每次 `--week 7` 或 `--week 8` 主流程都会向服务发送 `X-Experiment-Trace-Dir`（默认 `reports/deliverables_weekN/reproducibility_logs/<时间戳>/`；可用 **`--trace-dir`** 覆盖根路径，须落在仓库根或 `/tmp`）→ 成功处理的 `POST /generate|/refine|/edit` 下会有 `effective_prompt.txt` + `request_meta.json`/`request.json`（内容相同；大 base64 为摘要）。  
- **`POST /render`** 不写入 gzip（非模型输入，见 README）。

## Prompt 配置

环境变量 `UI2CODEN_PROMPT_PROFILE=baseline|extended` 控制 `local-service/model_wrapper.py` 是否在工业 HMI 英文约束块上附加扩展说明；与上述 trace 路径中的 `prompt_profile_env` 字段一致。
