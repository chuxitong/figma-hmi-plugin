# 第八周实验说明（中文对照稿）

俄文正文见 [`week-8.md`](week-8.md)。

与任务书对应：**时间、迭代次数、错误类别摘要、上下文开关**，并落实 **① refine 不能只有口头声明、② synthetic bulk 不能与 Figma 真提取混称、③ SSIM + 类目 + 文字结论**。

**跑数要点（云上）**：`hmi_week78_eval.py --week 8 --force-refine-rounds 2 --max-refines 2`（或 `FORCE_REFINE_ROUNDS=2`），保证每条分支的 **`refine_trace`** 里能对应到 `step01_refine`、`step02_refine`。`/health` 须为 **`model_kind=ui2coden`**。

**图解**：除三档配置的汇总图外，脚本还提供 **逐 mockup 折线 / 条形 / 纵排**（`figure_*per_screen*` 等），避免单均值盖住八张屏的差异；另有按 **24 格全运行** 绘制的 `figure_all_runs_indexed_*.png` 等。

**诚实表述**：Week 8 请求体里的 `variables` / `css_hints` 来自 Python **`synthetic_context`**，`metrics_full.json` 中记为 **`context_source_bulk: synthetic_script`** —— 正文应写「**模仿设计变量与设计稿式 CSS 的上下文**」，与 Week 7 **Figma 插件导出**对照区分开。

---

## 为什么跑 baseline 与 extended 两趟

两趟都在 **UI2Code^N 真推理**下完成：`GET /health` 中 `model_kind: ui2coden`，各目录 `metrics_full.json` 里 `model_backend` 也是 `ui2coden`。**不是**换权重、**也不是**两台独立服务；差别仅在于进程启动时读取的 **`UI2CODEN_PROMPT_PROFILE`**。脚本 `reports/scripts/run_week8_two_prompt_profiles.sh` 在两趟之间 **重启 `uvicorn`**，以便服务端加载与当前 profile 一致的模板。其余条件相同：8 张 mockup PNG、三种输入档位，JSON 中 `context_source_bulk: synthetic_script`（脚本生成的变量与 CSS 形状字段）。

## 两种 prompt 设定具体是什么

二者由环境变量 **`UI2CODEN_PROMPT_PROFILE`** 选择；未设置时行为同 **`baseline`**。实现见仓库 `local-service/model_wrapper.py`（`build_generate_prompt` / `build_refine_prompt` / `build_edit_prompt` 与 `_prompt_profile_extended()`）。

**`baseline`（默认）**  
在固定的主提示词后拼接上下文块（`variables` / `css_hints` 等），**不再**附加额外工程约束后缀：

- **生成**：工业 HMI 截屏 → 输出单文件自包含 HTML + 内联 CSS，复现版式/字体/配色与可点控件，语义化 HTML，无外链资源。
- **精修**：在参考图与当前渲染图（或仅参考图）对照下改进 HTML，收紧间距、排版层次、对齐与色板，补全参考中有而当前缺失的明显元素，返回完整 HTML。
- **编辑**：按用户指令修改附带的 HTML，返回完整更新后的 HTML。

**`extended`**  
在 **同一套** 主模板 + 上下文块之上，按环节 **追加** 三段英文「工程/HMI」约束：

1. **生成**：强调告警/状态与装饰性 chrome 区分、flex/grid 与面板间距一致、不遗漏主要设备或趋势区域、多按钮时区分主/次/中性样式等。
2. **精修**：强调在不大改无关卡片的前提下改善像素对齐与字体，除非参考明显要求重建。
3. **编辑**：强调局部落实指令，避免无关大段重写。

因此可概括为：**同一模型与数据管线，仅「是否在生成/精修/编辑三段流程末追加 extended 后缀」这一组 prompt 差异。**

---

## 规模

每 profile：**8 画框 × 3 档上下文 = 24 格**。每格固定 **1×`/generate` + 2×`/refine`**（`force_refine_rounds = 2`），故 `refine_iterations` 均为 2。汇总在各自的 `metrics_full.json`、`metrics.csv`，逐格产物在 `per_screen/.../`。

## 指标与图表

- **时间**：`seconds_first_generate`、`seconds_to_acceptable` 为墙钟（含请求与渲染）。图中有三档散点及 `figure_all_runs_indexed_*.png`（24 次逐格），避免只报均值抹掉离群格。
- **SSIM**：最终预览相对参考 PNG 的 `final_ssim`。图中有按 24 格索引的折线及按 8 张画叠线的 `figure_final_ssim_per_screen_lines.png`。
- **上下文边际 ΔSSIM**：按画框计算「+variables 相对 image_only」「+variables_css 相对 with_variables」，见 `figure_context_effect_ssim_delta.png`；pooled 数示例：baseline +0.01333 / −0.01850，extended +0.00637 / −0.02265（以 `metrics_full.json` 的 `effects` 为准）。
- **HTML 启发式类目**：`taxonomy_after_last_snapshot`，热力图 `figure_error_taxonomy_rates.png` 按格展示；可与 SSIM 配合肉眼判断，非唯一金标准。

## 交付路径

- Baseline：`reports/deliverables_week8_prompt_baseline/`（含 `figure*.png`、`SUMMARY.md`、`reproducibility_complete/`；trace 见该目录下 `reproducibility_logs/`，稳定入口 `WEEK8_FIXED_SERVER_TRACE_ROOT` 或会话子目录依实际导出而定）。
- Extended：`reports/deliverables_week8_prompt_extended/`（结构同上）。

`rule_based` 未混入本批数；有效 prompt 与请求体可在 `reproducibility_complete` 与 trace 中对齐。

## 实际运行顺序

本地 `USE_REAL_MODEL=1`，`/health` 确认 ui2coden → baseline（`--week8-deliver-dir …_baseline`，固定 `--trace-dir`，中断可用 `--week8-resume`）→ 重启服务 → extended 同参写入 `…_extended`。图与 `SUMMARY.md` 可用 `--replay-week8-figures` 按当前脚本从 `metrics_full.json` 重画。

张思成
