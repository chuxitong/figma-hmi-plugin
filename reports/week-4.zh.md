# 第 4 周——本地 HTTP 封装

这一周把模型调用收敛到 `local-service/app.py`，端点对齐任务书：**`/generate`、`/refine`、`/edit`、`/render`、`/health`**。从导师提醒出发，周报里强调的不再是「手写 prompts.json」，而是 **`reproducibility_complete/` 里逐条 gzip POST** + 服务端 **`effective_prompt.txt`**，`X-Experiment-Trace-Dir` 已固定随 Week 7/8 全流程发送。
