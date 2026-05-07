# 在本地部署 UI2Code^N（中文版）

本文说明在本项目中如何启动真实的视觉—语言模型 UI2Code^N、遇到过哪些问题，以及在不同硬件下可采取的做法。

在 **AutoDL 等云 GPU、全精度 bf16、不量化** 时，以 **`docs/DEPLOYMENT_AUTODL.zh.md`** 为逐步操作说明（与本文互补）。

## 硬件要求

UI2Code^N 在 GLM-4.1V-9B-Base 之上约 **90 亿参数**；bf16 权重约 **18 GB**。要较顺畅地运行，建议使用 **24 GB 显存** 的服务器级显卡（如 RTX 3090/4090、A5000 及以上），或 **两块 12 GB** 卡并行。笔记本 **6 GB 显存** 则需要折中方案，见下文。

作者在测试中使用：RTX 3060 笔记本版（6 GB）、64 GB DDR5 内存、磁盘剩余 140+ GB；CUDA 12.3 驱动，经 PyTorch 使用 CUDA 12.4 运行时。

## 环境安装

在 `local-service/.venv` 中创建独立虚拟环境。关键依赖包括：PyTorch 2.4.1+cu124（通过 `https://download.pytorch.org/whl/cu124` 安装）、`transformers==4.57.1`（验证时与 UI2Code^N 配套）、`accelerate`、`bitsandbytes`、`huggingface_hub`，以及 `fastapi`、`uvicorn`、`pillow`、`playwright`。

安装 `playwright` 后**必须**再执行：

```bash
playwright install chromium
```

否则无头浏览器无法启动，渲染会失败。

## 下载权重

模型托管在 Hugging Face：`zai-org/UI2Code_N`。四份 safetensors 分片加 tokenizer 与配置，合计约 **18 GB**。作者使用 `huggingface_hub.snapshot_download` 下载。若从俄罗斯或中国大陆直连 Hugging Face 很慢，可通过环境变量使用镜像（例如 `hf-mirror.com`）。

作者在 Windows 上使用的下载命令示例：

```bash
set HF_ENDPOINT=https://hf-mirror.com
python -c "from huggingface_hub import snapshot_download; snapshot_download('zai-org/UI2Code_N', local_dir='d:/hf_models/UI2Code_N', max_workers=4)"
```

在 Linux 或 macOS 上请将 `set` 改为 `export` 等对应写法，并调整 `local_dir` 路径。

## 加载模型

项目中的薄封装 `local-service/model_wrapper.py` 负责加载逻辑。环境变量 `UI2CODEN_MODEL_ID`（默认 `zai-org/UI2Code_N`）指定模型；内部使用 `apply_chat_template` 组装多模态消息，解码并清理 \`\`\`html 等标记。接口与确定性备用 `rule_based_model.py` 一致，因此服务与脚本不依赖具体模型实现细节。

作者采用的两种方式之一，是通过 **bitsandbytes 做 4 bit 量化**（NF4、双量化、计算 dtype 为 bf16）。若整模无法完全放入 GPU，`accelerate` 会把部分层卸到 CPU 内存。在作者的 **6 GB GPU** 上，该配置曾受 **bitsandbytes + accelerate** 在元张量、量化层 state_dict 上的已知问题影响，表现不稳定。因此更稳妥的做法是：在 6 GB 上改用 **纯 CPU 上以 bf16 推理**——稳定但极慢，首包可能因 mmap 分页等待数分钟。

若使用 **24 GB 显存** 的 GPU，通常可直接 bf16 + `device_map="auto"`，**不做量化、不做 CPU offload**，生成速度可达每秒数十个 token 量级。

## 将真实模型接到服务

`local-service/app.py` 中的 `get_model` 在首次请求时检查环境变量 **`USE_REAL_MODEL`**。若为 `1`，则尝试从 `model_wrapper` 加载真实 UI2Code^N；若失败（无权重、内存不足、版本不兼容等），会**回退到确定性备用模型**并写入日志。这样整条流水线不会因模型问题完全卡死，始终可用备用模型做端到端验证。

启用真实模型（Windows cmd 示例）：

```bash
set USE_REAL_MODEL=1
cd local-service
.venv\Scripts\python.exe -m uvicorn app:app --port 8000
```

（PowerShell 使用 `$env:USE_REAL_MODEL = "1"`。）

要恢复为备用模型，取消该环境变量后重启服务即可。

## 作者实测情况

在 RTX 3060 笔记本 6 GB + 64 GB 内存 上，使用当前 `model_wrapper.py` 时，模型可完成下载与加载（`Loading checkpoint shards: 100%`），首包可开始生成，但在 **CPU bf16** 下约 **0.2–0.4 token/秒**，整页数千 token 需**数分钟**。对手头八个 mockup 做可复现实验时，作者改用 **`rule_based_model.py`**，秒级完成，便于验证插件、服务、渲染、后处理与指标，而不依赖 GPU。在 **24 GB VRAM** 的机器上，同一套脚本可在合理时间内以真实模型跑完并给出反映 UI2Code^N 真实性能的计时表。

## 简短检查清单

1. 安装 Python 3.12，在 `local-service/.venv` 创建 venv。  
2. 安装与 CUDA 匹配的 PyTorch（例如 `pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cu124`）。  
3. `pip install -r local-service/requirements.txt`，并安装 `transformers==4.57.1`、`accelerate`、`bitsandbytes`、`huggingface_hub` 等。  
4. `playwright install chromium`。  
5. 通过 `snapshot_download`（必要时配合镜像）下载权重。  
6. 在 `figma-plugin/` 中执行 `npm run build`（或 `npx tsc`）构建插件。  
7. 需要时设置 `USE_REAL_MODEL=1`，再启动服务与实验脚本。

另见环境变量 **`UI2CODEN_QUANT`**：`none`（默认，bf16/论文用）、`8bit`、`4bit`，详见 `model_wrapper.py` 文件头说明。

**小显存 4bit 在本仓库中的推荐设置（与 `model_wrapper` 实现一致）**

- **`UI2CODEN_QUANT=4bit`**：权重量化。  
- **默认**使用 **`UI2CODEN_DEVICE_MAP=single`（可省略）**：整模放在单块 GPU（`device_map={"":0}`），避免 `device_map=auto` 把部分 4bit 层卸到 CPU 时在 Windows 上触发的 `bitsandbytes` + `meta tensor` 错误。需显卡 **显存能装下整模 4bit 权重**（约 6–8+ GB 量级，以实测为准；不足则 OOM 而非误报成「能跑」）。  
- 若需旧版「半在 CPU」行为，可设 **`UI2CODEN_DEVICE_MAP=auto`** 并视情况开 **`UI2CODEN_BNB_CPU_OFFLOAD=1`**（仍可能因驱动/环境失败）。  
- 笔记本上单次生成可能极慢，可设 **`UI2CODEN_MAX_NEW_TOKENS=2048`**（或更低）以缩短每轮生成长度、避免 `/edit` 堵塞整个服务过长时间。论文正式指标仍建议大显存 + 非截断全长度。

**与 FastAPI 的关系**  
Uvicorn 默认同进程单 worker 时，**长推理会阻塞**其它 HTTP 请求（如 `/health` 暂时无响应），属正常现象。

---

*本文件为 `DEPLOYMENT.md` 的中文对照版，技术细节以仓库内最新代码为准。*
