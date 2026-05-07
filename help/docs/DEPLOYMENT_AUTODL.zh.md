# 在 AutoDL 等云 GPU 上部署（全精度 bf16，不量化）

本文与仓库内 `local-service/model_wrapper.py`、`DEPLOYMENT.zh.md` 一致：**论文与正式指标应以 `UI2CODEN_QUANT=none`（bf16）为准**；量化仅作小显存妥协。

## 一、GPU 与显存建议

- **UI2Code^N** 约 9B 参数，bf16 权重约 **18 GB** 量级；再加上推理时的激活与缓存，**单卡建议 ≥ 24 GB**（如 RTX 3090/4090、A10、L20、A100 等）。
- **NVIDIA Blackwell 消费级卡（如 RTX 5090，sm_120）**：请安装 **PyTorch cu128** 轮子，**勿用本文下面示例中的 cu124**（否则 GPU 算子不可用）。详见仓库内 **`help/远程服务器-上传后补装依赖.md`** 中「PyTorch / CUDA」小节。
- **不要量化**时：不要设置 `UI2CODEN_QUANT`，或显式设为 `none`。
- 若租用 **双卡**（例如 2×16 GB），可在加载失败或需切分时将 **`UI2CODEN_DEVICE_MAP=auto`**，由 `accelerate` 自动分卡（见 `model_wrapper.py`）。

## 二、AutoDL 控制台侧

1. 选择带 **NVIDIA 驱动** 的镜像（通常已预装 CUDA / PyTorch；以实例说明为准）。
2. 确认数据盘空间 **≥ 25 GB**（模型约 18 GB + 依赖与缓存）。
3. 如需从本机用 Figma 插件连到云端，有两种常见方式（二选一即可）：
   - **SSH 端口转发（推荐）**：本机浏览器与 Figma 仍用 `http://localhost:8000`，插件 UI 的 **Service URL** 也保持本机地址即可。
   - **公网 / 平台映射 URL**：在 AutoDL「自定义服务」或文档提供的 **https 反代地址** 上暴露 8000 端口；插件 UI 里将 **Service URL** 填成该地址（见 `figma-plugin/src/ui.html`）。

> 当前仓库的 `figma-plugin/manifest.json` 已采用 `networkAccess.allowedDomains: ["*"]` + `reasoning` + `devAllowedDomains`，以兼容 Figma 对 localhost / development servers 的 manifest 校验；通常**不必**再逐条手改白名单。若你要改回严格白名单发布策略，再按平台地址逐条列出域名。

## 三、实例内：环境变量（全精度）

在 `local-service` 目录下激活 venv 后，启动前导出（路径请按你的数据盘修改）：

```bash
export USE_REAL_MODEL=1
export UI2CODEN_QUANT=none
export UI2CODEN_DEVICE_MAP=single
# 权重目录（snapshot_download 的目标路径，或 Hub 缓存路径）
export UI2CODEN_MODEL_ID=/root/autodl-tmp/UI2Code_N
# 可选：限制生成长度，避免单次请求过久
# export UI2CODEN_MAX_NEW_TOKENS=4096
```

- 双卡需要自动切分时：`export UI2CODEN_DEVICE_MAP=auto`。
- 国内拉取 Hugging Face 较慢时，可使用镜像（示例）：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

## 四、依赖与权重

```bash
cd /root/autodl-tmp/figma-hmi-plugin/local-service
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
pip install transformers==4.57.1 accelerate bitsandbytes huggingface_hub
playwright install chromium
playwright install-deps  # 若 headless 缺系统库时按报错执行
```

下载权重（示例目录与上面 `UI2CODEN_MODEL_ID` 一致）：

```bash
python -c "from huggingface_hub import snapshot_download; snapshot_download('zai-org/UI2Code_N', local_dir='/root/autodl-tmp/UI2Code_N', max_workers=4)"
```

快速检查环境（不写死 Windows 盘符，使用 `UI2CODEN_MODEL_ID`）：

```bash
export UI2CODEN_MODEL_ID=/root/autodl-tmp/UI2Code_N
python verify_model_install.py
```

## 五、启动服务（必须监听所有网卡）

远程或端口映射时，需绑定 **`0.0.0.0`**，否则仅本机 `127.0.0.1` 可访问：

```bash
cd /root/autodl-tmp/figma-hmi-plugin/local-service
source .venv/bin/activate
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

确认健康检查（启动后有一段时间在**预热**真模型，`ui2code_n_active` 才会变为 `true`；也可用 `UI2CODEN_SKIP_WARMUP=1` 延后到首次 `/generate`，见下文）：

```bash
curl -s http://127.0.0.1:8000/health | python -m json.tool
```

云上推荐一键拉起（内置 `USE_REAL_MODEL` / 量化与设备映射默认值，并把日志写到 `/tmp/uvicorn-figma-hmi.log`）：

```bash
bash /root/autodl-tmp/figma-hmi-plugin/local-service/start_cloud_service.sh
```

**从你自己电脑的浏览器访问云上的 Swagger**：本机开一个 **SSH 本地转发**。完整步骤见 **`help/本地浏览器访问云端8000-SSH隧道.zh.md`**。

## 六、从本机连接 Figma（SSH 转发，可复制执行）

在你的 **Windows / Mac** 终端保持下面这条一直连着（断开则本机 8000 不再指向云上服务）：

```bash
ssh -p 10029 -L 8000:127.0.0.1:8000 root@connect.westd.seetacloud.com -N
```

仅登录远端、不要做端口转发时用：

```bash
ssh -p 10029 root@connect.westd.seetacloud.com
```

然后本机打开 `http://127.0.0.1:8000/docs`；插件 **Service URL** 填 `http://localhost:8000` 或 `http://127.0.0.1:8000` 即可。

## 七、在服务器上跑第三周验收脚本

与 Windows 上 `reports/run_week3_verified.ps1` 等价，仓库提供 **`reports/run_week3_verified.py`**（在仓库**根目录**执行，可设置 `API_BASE` 指向本机或反代）：

```bash
cd /root/autodl-tmp/figma-hmi-plugin
export API_BASE=http://127.0.0.1:8000
export USE_REAL_MODEL=1
export UI2CODEN_QUANT=none
# 另开终端或先后台启动 uvicorn 后再跑：
local-service/.venv/bin/python reports/run_week3_verified.py
```

仅捕 Swagger/health 证据时：

```bash
export API_BASE=http://127.0.0.1:8000
/root/autodl-tmp/figma-hmi-plugin/local-service/.venv/bin/python local-service/capture_week3_evidence.py --base "$API_BASE" --out-dir /root/autodl-tmp/figma-hmi-plugin/reports/screenshots
```

## 八、注意事项

- **单 worker**：长时 `generate`/`refine` 会阻塞同进程内其他请求；等待期间不要杀 `uvicorn`。
- **CORS 与 PNA（与「uvicorn 在哪台机」要分开说）**：
  - **`uvicorn` 跑在云服务器上**、你在本机用 **`ssh -p 10029 -L 8000:127.0.0.1:8000 root@connect.westd.seetacloud.com -N`** 时：Figma 与浏览器仍应访问 **`http://127.0.0.1:8000` / `http://localhost:8000`**（填在插件 **Service URL**），因为请求先到**你电脑上的**隧道入口，再转到**服务器上的** 8000 端口。这与「在本机也跑一个 uvicorn」是两种不同部署，**插件里填 127.0.0.1 在这类转发下仍是正确做法**（见上「§六」）。
  - 普通浏览器开 `/docs` 能通，**不代表** Figma 插件里 `fetch` 一定通：插件 UI 会触发 **Private Network Access** 预检，服务器必须在 CORS 里允许 **`Access-Control-Allow-Private-Network`**。仓库的 `app.py` 已设置 **`allow_private_network=True`**；修改后需在**跑 `uvicorn` 的那台机器**（即你的远程实例，不是 Figma 所在电脑）上**部署该 `app.py` 并重启** `uvicorn`。
  - Figma 侧可访问的域名仍受 **`manifest.json` 的 `networkAccess`** 约束（与上面服务配置独立）。
- **不量化**时不需要为推理安装 `bitsandbytes`，但 `pip` 列表里保留也不影响；仅当 `UI2CODEN_QUANT=4bit|8bit` 时才依赖 bnb。
- **预览与截图格式**：`POST /generate` 等返回的 `preview_base64`、以及 `POST /render` 的 `image_base64`，在**本机或远程**均为 **PNG**（Playwright 无头 Chromium），与部署位置无关；需在实例上安装好 `playwright install chromium`（及依赖），否则预览为 `null` 但 HTML 代码仍返回。

## 九、释放实例 / 换一台新服务器时

释放云实例前建议 `git push`、记下环境变量与连接方式；换机后从 clone 到拉起 `uvicorn` 的**最短清单**见 **`help/断联与换机重连.md`**（与本文 §二～§五 互补，侧重「断联准备 + 新机器一套展开」）。
