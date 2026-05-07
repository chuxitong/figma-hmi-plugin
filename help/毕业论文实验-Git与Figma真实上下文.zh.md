# 毕业论文实验：SSH、真模型仓库与「Figma 真实上下文」存放约定（中文版）

仅供你自己查阅；不向导师强制提供俄文版。与 [`help/docs/DEPLOYMENT_AUTODL.zh.md`](docs/DEPLOYMENT_AUTODL.zh.md) 配套。

## 概念区分（写给答辩前的自己）

| 数据来源 | 含义 |
|----------|------|
| **脚本合成上下文** (`synthetic`) | [`reports/scripts/hmi_week78_eval.py`](../reports/scripts/hmi_week78_eval.py) 里 `synthetic_context()`：**Python 手写**的假 variables / css_hints，仅用于大批量、与 `mockups/png` 对齐的消融；**不等于**你在 Figma 里点 Inspect 拿到的真数据。 |
| **插件真实上下文** (`figma_plugin`) | [`figma-plugin/src/code.ts`](../figma-plugin/src/code.ts)：勾选后从**当前导出根 Frame 及其子树**收集已绑定的 **Variables**（含 **Libraries** 里引用、用在 Fill/Stroke/effect/文本段等处），经 `getVariableByIdAsync` / `resolveForConsumer` 解析；`css_hints` 仍来自 `getCSSAsync()`（Frame 与部分子图层）。详见 [`help/docs/figma-data-extraction.zh.md`](docs/figma-data-extraction.zh.md)。 |

批量周报告里以前若只跑脚本而未说明，容易被质疑「合成」——应用本仓库 ** `--context-mode`** 与本页路径约定区分开。

---

## 1. 云服务器启动真模型

```bash
cd /root/autodl-tmp/figma-hmi-plugin/local-service
bash start_cloud_service.sh
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

需满足：`model_kind` 为 `ui2coden`、`ui2code_n_active` 为 `true`。

---

## 2. 本机 SSH 隧道（浏览器与插件都连本机 8000）

在云控制台看你的 **SSH 端口**（示例里常为 `10029`），在本机终端**保持不关**：

```bash
ssh -p <SSH端口> -L 8000:127.0.0.1:8000 root@<平台域名> -N
```

随后在**本机**打开：

- Swagger：`http://127.0.0.1:8000/docs`
- Figma 插件 **Service URL**：`http://127.0.0.1:8000`

---

## 3. Figma 中采集「真实」variables / CSS hints（用于替换合成对比）

1. 用 **Figma Desktop** 打开你的工业稿件；在 **Layers** 里点选顶层 **Frame**（不要只选在 Frame 里的小图层，否则导出可能跑偏）。
2. 运行开发版插件：`Plugins → Development → Import plugin from manifest` → `figma-plugin/manifest.json`。
3. **Include design variables** 勾选后：插件递归当前 **Frame 子树**，从节点的 **`boundVariables`、每层 Fill/Stroke/effect、文本段的变量绑定**等处收集别名，并用 **`getVariableByIdAsync` + `resolveForConsumer`** 解析取值——**Libraries 拖到 Fill 上的颜色变量也会被导出**（键名形如 `--Color-6`）。若整棵子树内**无任何变量绑定**，`variables` 才是 `{}`。论文里可对「绑定覆盖范围」有一句诚实说明。
4. **第一次**：取消勾选「Include design variables」「Include CSS hints」，点 **Generate**。
5. **第二次**：勾选两者，再次 **Generate**（同一 Frame）。
6. 插件面板底部的 **Generated Code** 区域：  
   - **推荐**：点击 **Copy last API request (JSON, base64 truncated)**。本仓库先尝试系统的 **Clipboard API**，不可用时改用 **`execCommand('copy')` 兜底**；成功后 **Log** 会以 *Last API request JSON copied (…; base64 truncated)* 形式写明所用路径（如 `Clipboard API` 或 `execCommand …`）；若两种方式均失败，**Log** 会提示你改用下方的 **Last API request snapshot** 文本框（点击框内 → **Ctrl+A** → **Ctrl+C**）粘贴到本地文件。每次 **Generate / Refine / Edit** 后快照框内容与 Copy 按钮目标一致。
   - 请将 **同一 Frame** 下「仅截图」与「含 variables + CSS hints」两次 **Generate** 各导出一份，保存为两个文件（见下文文件名）；或改从插件 Log / 开发者工具自行抓取 **`POST /generate`** 的 JSON body。

建议使用下列文件名放进仓库（可自行建目录）：

```text
reports/deliverables_week7/figma_native/
  05-production-overview.image_only.payload.json
  05-production-overview.with_variables_css.payload.json
```

每份 payload 应为服务可识别的字段（至少）：

`image_base64`, `frame_name`, `width`, `height`，以及第二份中的 `variables`, `css_hints`。

---

## 4. 从 Figma 导出的 JSON 跑上下文对比（**非脚本合成上下文**），**并生成可直接插报告的 PNG**

在云或本机（能访问 `API_BASE`，且 **`/health` 已确认为 UI2Code^N**）：

```bash
export API_BASE=http://127.0.0.1:8000
python reports/scripts/hmi_week78_eval.py --week 7 \
  --context-mode from-json \
  --figma-context-dir reports/deliverables_week7/figma_native
```

脚本会：

1. **读取** `*.image_only.payload.json` 与 `*.with_variables_css.payload.json`，各调用一次 **`POST /generate`**。  
2. **复制**两份输入 payload 到 `context_compare/figma_native_context/`，文件名带 `figma_plugin_input_*.payload.json`，与你的截图、manifest 一齐打包即为「可追溯输入」。  
3. **写出对比 PNG（报告用，ВКР 口径）**：脚本生成**两张独立**投影片（各为「参考帧 | 模型预览」两栏，避免三栏合成一张导致投影字号过小）：  
   - **`figma_plugin_THESIS_slide_image_only_context.png`** — 仅截图上下文的一次 `/generate`；  
   - **`figma_plugin_THESIS_slide_full_figma_context.png`** — 含插件采集的 `variables` + `css_hints` 的一次 `/generate`。  
   另保留技术向单帧预览 `figma_plugin_preview_*.png` 与省略 `preview_base64` 后的 `*_generate_*.response.json`。  
4. **`WEEK7_MANIFEST.json`** 中：`context_source: figma_plugin`，并含 `png_for_report_thesis_slide_*_relative`、`input_payload_snapshots_relative`、`experiment_api_trace_dir_relative`（每次跑数**自动写入**）。

> **说明（与任务书周次对齐）**：任务书 **第 7 周**要求「至少 1 个小对比：仅图像 vs 图像+变量和 CSS」——**§3–§4 + 上述两张 `THESIS_slide_*` 已满足**。「第 5 周」在任务书中指**渲染模块 + 插件外壳**，**不是**本仓库里曾写的「脚本合成大批量消融」；**毕业论文正文不必再跑 `--context-mode synthetic` 的 Week 7/8 合成流水线作为证据**（见 §5 说明）。

---

## 5. （内部工程选项，不与 ВКР 主证据混用）

以下命令仍可在**打通管道、对比延迟**时使用，但 `context_source: synthetic_script` **不得**在论文中与 **UI2Code^N + Figma 真提取**写进同一组「baseline」结论：

```bash
export API_BASE=http://127.0.0.1:8000
python reports/scripts/hmi_week78_eval.py --week 7 --context-mode synthetic   # engineers only
python reports/scripts/hmi_week78_eval.py --week 8 --context-mode synthetic
```

周线评估（Week 8）若需单独展示 **refine**，请参见 **§6** 使用 **`--force-refine-rounds`**，否则低 SSIM 阈值会导致 `refine_iterations=0`、无法支撑「迭代优化」这一条故事线。**服务端可追溯 gzip + trace**仍随每次主流程自动生成。

---

## 6. 强制 Refine 轮次（满足导师「即使 SSIM 已够也要跑两轮」）

周 8 批量：

```bash
export FORCE_REFINE_ROUNDS=2
python reports/scripts/hmi_week78_eval.py --week 8 --context-mode synthetic
```

或：

```bash
python reports/scripts/hmi_week78_eval.py --week 8 --force-refine-rounds 2 --ssim-accept 0.45
```

`per_screen/*/refine_trace/` 下会保存每一步 HTML、SSIM、中间预览说明。同一次实验的 **API 文本审计**（`effective_prompt.txt` / `request.json`，含脱敏摘要）由脚本**固定**发往服务的 `X-Experiment-Trace-Dir` 根目录写入，详见 §7（仅 **`--replay-week8-figures`** 重画图时不访问 API，故无服务端 trace）。

## 7. 可复现实验日志（全自动落盘：**无需你再抓包/写说明**）

### 7.1 两处互补材料（导师 Roman Davydov 要求拆开理解，脚本都会生成）

每次跑 `python reports/scripts/hmi_week78_eval.py --week 7` 或 `--week 8`，脚本都会在交付物目录下**覆盖写入**：

- **`reports/deliverables_week7/reproducibility_complete/`** 或 **`reports/deliverables_week8/reproducibility_complete/`**  
  - `http_request_bodies/*.full.json.gz`：**与当次客户端 `POST /generate|/refine|/edit` 完全相同的 JSON UTF-8 字节**（含完整 `image_base64` 等），可用于逐字节重放 HTTP 请求。  
  - 逐条 **`.sha256`**：针对**解压后的** JSON 字节，**不是** gzip 文件本身。  
  - `HEALTH_at_run_start.json`：本番跑数前 `GET /health` 快照（证明 `model_kind` 等）。  
  - `RUN_META.json`、`INDEX.json`  
  - **`README_REPRODUCIBILITY.zh.md`**：由脚本自动生成，写明多模态局限、`prompts.json` 反例、与下方「服务审计副本」的差别等——**你不必再手写注意事项**。

此外，脚本**固定**向服务发送 **`X-Experiment-Trace-Dir`**（默认新建 `reports/deliverables_week7|8/reproducibility_logs/<时间戳>/.../`，内含 `README_API_TRACES.zh.txt` 并指向同级上一层的 **`../reproducibility_complete/`**）。若要把追溯根目录改到固定路径，使用 **`--trace-dir`**（须解析到**仓库根**或 **`/tmp`** 之下）。服务在每次成功的 `POST /generate|/refine|/edit` 下落盘：

| 文件 | 含义 |
|------|------|
| **`effective_prompt.txt`** | **代入后的英文 prompt 文本**；多模态时图像仍以张量进模型——**≠**全文「模型输入」的单独 Serializable 形态。 |
| **`request_meta.json` 与 `request.json`** | **二者内容相同**；服务端收到的字段**审计摘要**，大块 `*_base64` → **长度 + sha256 前缀**。用于 git 友好的对照；**不可替代** `reproducibility_complete` 里 gzip 的 **完整** body。 |

**反例（禁止）**：单独放一个只描述实验剧情的 `prompts.json`，却声称它是「完整模型输入」——与事实不符时导师会质疑；**以 `INDEX.json` + `http_request_bodies/*.full.json.gz` 为准**。

### 7.2 服务侧追溯目录（与 7.1 并列，**每次 `--week 7|8` 主流程默认开启**）

已移除 **`--capture-repro`**：`X-Experiment-Trace-Dir` **总是**设置在完整跑数时。仅在希望**自定义根目录**时追加 **`--trace-dir`**：

```bash
python reports/scripts/hmi_week78_eval.py --week 7 --context-mode from-json \
  --figma-context-dir reports/deliverables_week7/figma_native \
  --trace-dir /tmp/my_hmi_trace_root
```

### 7.3 Figma 插件「Copy last API request」与快照框（可选）

用于快速导出**脱敏预览用** JSON（字段名中带 `base64` 的长串会被截断为 `<<truncated N chars>>`）。实现上：**先尝试写入系统剪贴板**，不可用则 **`execCommand('copy')` 兜底**；仍失败时在面板 **`Last API request snapshot`** 中保留同一文本，请 **Ctrl+A / Ctrl+C** 手动粘贴到文件。**论文级完整 body**仍以评估脚本落地的 `reproducibility_complete/http_request_bodies/*.full.json.gz` 为准；`--figma-context-dir` 下的 `*.payload.json` 可与上述材料交叉校验。

若点击 Copy 仍「完全没反应」，请同步最新 **`figma-plugin/src/ui.html`** 并重新 **Import** 插件，见 `help/插件报错全面排查与本次修复说明.md` **§9.6**，Build 行为 **2026-05-07** 起应在 Log 中看到复制成功或兜底提示。

---

## 8. 用你本机跑出的 PNG/JSON「覆盖仓库里的旧对比图」

1. 你保留 Figma / 插件真机流程产出的：`*.png`、`*.payload.json`、`WEEK7_MANIFEST` 增补段。
2. 直接替换 `reports/deliverables_week7/` 与 `reports/deliverables_week8/` 中对应文件，或新开 `figma_native/` 子目录并在俄/中文周报里引用新路径。
3. **`git commit` 前**核对：不要把含隐私的整块 base64 图误提交进公开副本（可先运行脚本自带的 omit 或使用 `response.json` 中已省略预览字段的版本）。

Prompt 配置文件（中英扩展对比）可选环境变量：**`UI2CODEN_PROMPT_PROFILE=baseline|extended`**（见 `local-service/model_wrapper.py`）。

---

## 参阅

- [本地浏览器访问云端8000-SSH隧道.zh.md](本地浏览器访问云端8000-SSH隧道.zh.md)
- [断联与换机重连.md](断联与换机重连.md)
